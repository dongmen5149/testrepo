"""Formula::calc(formula_id, ...) 호출자 추적 — formula_id 별 caller 함수 식별.

목적: V[112..116] 5 secondary stat 라벨 식별을 위해 calc_pl id=25..29 의
실제 사용처 (HERO::GetHit / GetAvoid / GetCritical 같은 wrapper 또는
CommonUi::DrawSkillBookDiscription 의 stat fetch 자리) 추적.

방법:
  1. Formula::calc 심볼 (`_ZN7Formula4calcEi*`) 주소 확정.
  2. .so .text 의 모든 함수를 disasm 하면서 register state 추적:
       - r0..r12 의 immediate 값을 dict 로 보관
       - mov rD, rS  → state[rD] = state[rS]
       - mov/movw/movs/mvn rD, #imm → state[rD] = imm
       - ldr rD, [pc, #N] → state[rD] = *(literal pool)
       - 그 외 명령은 dst register state invalidate
       - branch / call / 함수 끝 → state reset (basic block 단위)
  3. BL/BLX <Formula::calc> 직전 r0 값을 caller_func 와 함께 record.
  4. Caller 함수 mangled name (간단 demangle) 매핑 + (id, caller, addr) TSV.

산출: work/h5/analysis/formula_callers.tsv
"""
from __future__ import annotations
import pathlib
import struct
import sys

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/formula_callers.tsv"
SUMMARY = ROOT / "work/h5/analysis/formula_callers_summary.txt"

CALC_SYM = "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase"


def simple_demangle(mangled: str) -> str:
    """Itanium ABI mangled name → 'Class::Method' (인수 무시)."""
    if not mangled.startswith("_ZN"):
        return mangled
    s = mangled[3:]
    parts = []
    while s and s[0].isdigit():
        n = 0
        while s and s[0].isdigit():
            n = n * 10 + int(s[0])
            s = s[1:]
        if len(s) < n:
            break
        parts.append(s[:n])
        s = s[n:]
        if s.startswith("E"):
            break
    return "::".join(parts) if parts else mangled


def main() -> int:
    so = lief.parse(str(SO))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    addr_to_sym: dict[int, tuple[str, int]] = {}
    calc_addr = None
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        addr_to_sym.setdefault(a, (s.name or "", s.size))
        if s.name == CALC_SYM:
            calc_addr = a
    if calc_addr is None:
        print(f"[!] {CALC_SYM} 심볼 없음", file=sys.stderr)
        return 1
    print(f"[+] Formula::calc @ 0x{calc_addr:08x}")

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def read_u32(va: int) -> int | None:
        for v0, v1, d in seg:
            if v0 <= va < v1 - 3:
                return struct.unpack_from("<I", d, va - v0)[0]
        return None

    text_secs = [(sec.virtual_address, bytes(sec.content)) for sec in so.sections if sec.name == ".text"]
    if not text_secs:
        print("[!] .text 섹션 없음", file=sys.stderr)
        return 1

    callers: list[tuple[int, int | None, str, int]] = []

    REG_NAMES = {f"r{i}" for i in range(13)} | {"sp", "lr", "pc", "ip", "fp", "sl", "sb"}
    # ARM 레지스터 alias
    REG_ALIAS = {"ip": "r12", "sp": "r13", "lr": "r14", "pc": "r15", "fp": "r11", "sl": "r10", "sb": "r9"}

    def norm_reg(r: str) -> str | None:
        r = r.strip().lower()
        if r in REG_ALIAS:
            r = REG_ALIAS[r]
        return r if r in REG_NAMES else None

    for sec_va, sec_data in text_secs:
        for fn_addr, (fn_name, fn_size) in sorted(addr_to_sym.items()):
            if fn_addr < sec_va or fn_addr + fn_size > sec_va + len(sec_data):
                continue
            offset = fn_addr - sec_va
            data = sec_data[offset:offset + fn_size]
            state: dict[str, int | None] = {}  # reg → known imm value
            for ins in md.disasm(data, fn_addr):
                m = ins.mnemonic
                op = ins.op_str.replace(" ", "")

                # BL / BLX <imm> 호출 검사 — 호출 직전 state[r0]
                if m in ("bl", "blx") and op.startswith("#"):
                    try:
                        target = int(op[1:], 0) & ~1
                    except ValueError:
                        target = None
                    if target == calc_addr:
                        callers.append((ins.address, state.get("r0"), fn_name, fn_addr))
                    # 함수 호출은 r0..r3 (return + caller-saved) 상태 invalidate
                    for r in ("r0", "r1", "r2", "r3", "r12", "r14"):
                        state[r] = None
                    continue

                # 분기 명령 (B / BX / BNE 등) — basic block 끝, state reset
                if m == "b" or m.startswith("b") and len(m) <= 3 and m not in ("bic", "bfc", "bfi"):
                    # b, bne, beq, bx, blx (이미 위에서 처리한 bl 제외)
                    if m in ("bl",):
                        pass  # already handled
                    elif m.startswith("b"):
                        state.clear()
                        continue

                # 명령별 register update
                # operand 파싱: capstone op_str 를 콤마로 분리
                parts = ins.op_str.split(",")
                if not parts:
                    continue
                dst = norm_reg(parts[0].strip())

                if m in ("mov", "movs"):
                    if dst and len(parts) >= 2:
                        rhs = parts[1].strip()
                        if rhs.startswith("#"):
                            try:
                                state[dst] = int(rhs[1:], 0)
                            except ValueError:
                                state[dst] = None
                        else:
                            src = norm_reg(rhs)
                            state[dst] = state.get(src) if src else None
                elif m == "movw":
                    if dst and len(parts) >= 2:
                        rhs = parts[1].strip()
                        if rhs.startswith("#"):
                            try:
                                state[dst] = int(rhs[1:], 0) & 0xFFFF
                            except ValueError:
                                state[dst] = None
                        else:
                            state[dst] = None
                elif m == "movt":
                    # movt rD, #imm — 상위 16비트 set
                    if dst and len(parts) >= 2 and parts[1].strip().startswith("#"):
                        try:
                            hi = int(parts[1].strip()[1:], 0) & 0xFFFF
                            cur = state.get(dst) or 0
                            state[dst] = (cur & 0xFFFF) | (hi << 16)
                        except ValueError:
                            state[dst] = None
                elif m == "mvn":
                    if dst and len(parts) >= 2 and parts[1].strip().startswith("#"):
                        try:
                            state[dst] = (~int(parts[1].strip()[1:], 0)) & 0xFFFFFFFF
                        except ValueError:
                            state[dst] = None
                    elif dst:
                        state[dst] = None
                elif m == "ldr":
                    # ldr rD, [pc, #N]  → literal pool
                    if dst and "[pc," in ins.op_str:
                        try:
                            off = int(ins.op_str.rsplit(",", 1)[-1].strip(" []#"), 0)
                            literal_va = (ins.address + 8 + off) & ~3
                            state[dst] = read_u32(literal_va)
                        except (ValueError, IndexError):
                            state[dst] = None
                    elif dst:
                        state[dst] = None
                else:
                    # 기타 명령: dst register invalidate (대부분 ARM 명령은 첫 op 가 dst)
                    if dst and m not in ("cmp", "cmn", "tst", "teq", "str", "strb", "strh", "stm", "stmdb", "stmia", "push", "pop"):
                        # str/stm/push 류는 dst 없음. cmp 류는 set 안 함.
                        state[dst] = None
                    # pop {rN, ..., pc} 가 함수 끝 — state 무효화
                    if m in ("pop",) and "pc" in ins.op_str:
                        state.clear()

    print(f"[+] Formula::calc 호출 {len(callers)} 건")
    known = sum(1 for c in callers if c[1] is not None)
    print(f"    formula_id 추정 가능: {known} / {len(callers)}")

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows_demangled = []
    for call_va, fid, caller_n, caller_a in callers:
        d = simple_demangle(caller_n)
        rows_demangled.append((call_va, fid, caller_n, caller_a, d))

    with OUT.open("w", encoding="utf-8") as f:
        f.write("call_va\tformula_id\tcaller_addr\tcaller_demangled\tcaller_mangled\n")
        for call_va, fid, caller_n, caller_a, d in sorted(rows_demangled, key=lambda r: (r[1] if r[1] is not None else 99999, r[0])):
            fid_s = str(fid) if fid is not None else "?"
            f.write(f"0x{call_va:08x}\t{fid_s}\t0x{caller_a:08x}\t{d}\t{caller_n}\n")

    # id 별 unique caller 요약
    by_id: dict[int, set[str]] = {}
    for call_va, fid, _, _, d in rows_demangled:
        if fid is None:
            continue
        by_id.setdefault(fid, set()).add(d)

    with SUMMARY.open("w", encoding="utf-8") as f:
        f.write("# formula_id → unique callers (calc_pl 0..38, calc_en 1000..1018, calc_sk 2000..)\n\n")
        for fid in sorted(by_id):
            f.write(f"## id={fid}  ({len(by_id[fid])} caller{'s' if len(by_id[fid])>1 else ''})\n")
            for d in sorted(by_id[fid]):
                f.write(f"  {d}\n")
            f.write("\n")

    print(f"[+] {OUT}")
    print(f"[+] {SUMMARY}")
    print()
    print("== id=24..29 callers (V[112..116] 라벨 식별 핵심) ==")
    for fid in (24, 25, 26, 27, 28, 29):
        callers_set = by_id.get(fid, set())
        print(f"  id={fid}: {len(callers_set)} caller(s)")
        for d in sorted(callers_set):
            print(f"    {d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
