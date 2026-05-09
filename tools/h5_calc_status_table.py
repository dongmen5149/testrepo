"""HERO::CalcStatusComputation 의 calc 호출 → cache offset 매핑 자동 추출.

패턴 1 (calc_sk 호출 + cache):
  mov   r1, #0x7f0
  add   r1, r1, #N        ; r1 = formula_id (calc_sk 0x7f0+N)
  ...
  bl    Formula::calc      ; → r0 = 결과
  mov   r3, #<offset>     ; cache offset
  (add  r3, r3, #<delta>)
  strh  r0, [r4, r3]       ; HERO+<offset> = 결과

추출:
  → (formula_id, cache_offset, sequence_idx)

산출: work/h5/analysis/calc_status_cache_map.tsv
"""
from __future__ import annotations
import pathlib

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/calc_status_cache_map.tsv"

CALC_SYM = "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase"
TARGET_SYMS = [
    "_ZN4HERO21CalcStatusComputationEh",
]


REG_ALIAS = {"ip": "r12", "sp": "r13", "lr": "r14", "pc": "r15", "fp": "r11", "sl": "r10", "sb": "r9"}
REG_NAMES = {f"r{i}" for i in range(16)}


def norm(r: str) -> str | None:
    r = r.strip().lower()
    if r in REG_ALIAS:
        r = REG_ALIAS[r]
    return r if r in REG_NAMES else None


def main() -> int:
    so = lief.parse(str(SO))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    addr_to_name = {}
    calc_addr = None
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        addr_to_name.setdefault(a, (s.name or "", s.size))
        if s.name == CALC_SYM:
            calc_addr = a
    if calc_addr is None:
        print("[!] Formula::calc 심볼 없음")
        return 1

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def get_data(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0: va - v0 + sz])
        return None

    rows = []  # (fn, formula_id, cache_offset, call_va, sequence_idx)

    for sym_name in TARGET_SYMS:
        info = None
        for a, (n, sz) in addr_to_name.items():
            if n == sym_name:
                info = (a, sz); break
        if not info:
            print(f"[!] {sym_name} 없음")
            continue
        fn_addr, fn_sz = info
        data = get_data(fn_addr, fn_sz)
        if not data:
            continue

        ins_list = list(md.disasm(data, fn_addr))
        # state: register → known imm
        state: dict[str, int | None] = {}
        last_call_idx = None  # bl Formula::calc 위치

        seq_idx = 0
        for i, ins in enumerate(ins_list):
            m = ins.mnemonic
            op = ins.op_str.replace(" ", "")

            # BL
            if m == "bl" and op.startswith("#"):
                try:
                    target = int(op[1:], 0) & ~1
                except ValueError:
                    target = None
                if target == calc_addr:
                    fid = state.get("r1")
                    # 이후 명령에서 strh r0, [r4, r3] + r3 cache offset 확인
                    cache_offset = None
                    # r3 추적 — 호출 직후 r3 가 cache offset 으로 set 되는 패턴
                    sub_state: dict[str, int | None] = {}
                    for j in range(i + 1, min(i + 16, len(ins_list))):
                        sins = ins_list[j]
                        sm = sins.mnemonic
                        sop = sins.op_str.replace(" ", "")
                        # mov r3, #imm
                        if sm in ("mov", "movs") and sop.startswith("r3,#"):
                            try:
                                sub_state["r3"] = int(sop.split("#")[1], 0)
                            except ValueError:
                                sub_state["r3"] = None
                        elif sm == "add" and sop.startswith("r3,r3,#") and sub_state.get("r3") is not None:
                            try:
                                sub_state["r3"] += int(sop.split("#")[2 - sop.count(",")], 0)
                            except (ValueError, IndexError):
                                # parsing edge case
                                pieces = sop.split(",")
                                if len(pieces) >= 3 and pieces[2].startswith("#"):
                                    try:
                                        sub_state["r3"] += int(pieces[2][1:], 0)
                                    except ValueError:
                                        pass
                        elif sm == "strh" and "[r4," in sop:
                            # strh r0, [r4, r3] 또는 strh r0, [r4, #N]
                            if "r3]" in sop and sub_state.get("r3") is not None:
                                cache_offset = sub_state["r3"]
                            elif "#" in sop:
                                # strh r0, [r4, #N]
                                try:
                                    cache_offset = int(sop.split("#")[-1].rstrip("]"), 0)
                                except ValueError:
                                    pass
                            break
                        # 다른 BL 만나면 중단
                        if sm == "bl":
                            break
                    rows.append((sym_name, fid, cache_offset, ins.address, seq_idx))
                    seq_idx += 1
                # caller-saved invalidate
                for r in ("r0", "r1", "r2", "r3", "r12", "r14"):
                    state[r] = None
                continue

            # 분기 — basic block 끝
            if m == "blx":
                for r in ("r0", "r1", "r2", "r3", "r12", "r14"):
                    state[r] = None
                continue
            if m.startswith("b") and m not in ("bic", "bfc", "bfi", "bl") and op.startswith("#"):
                state.clear()
                continue
            if m == "bx":
                state.clear()
                continue

            # 명령 별 reg update
            parts = ins.op_str.split(",")
            dst = norm(parts[0].strip()) if parts else None

            if m in ("mov", "movs") and dst:
                if len(parts) >= 2:
                    rhs = parts[1].strip()
                    if rhs.startswith("#"):
                        try:
                            state[dst] = int(rhs[1:], 0)
                        except ValueError:
                            state[dst] = None
                    else:
                        src = norm(rhs)
                        state[dst] = state.get(src) if src else None
            elif m == "movw" and dst and len(parts) >= 2 and parts[1].strip().startswith("#"):
                try:
                    state[dst] = int(parts[1].strip()[1:], 0) & 0xFFFF
                except ValueError:
                    state[dst] = None
            elif m == "movt" and dst and len(parts) >= 2 and parts[1].strip().startswith("#"):
                try:
                    hi = int(parts[1].strip()[1:], 0) & 0xFFFF
                    cur = state.get(dst) or 0
                    state[dst] = (cur & 0xFFFF) | (hi << 16)
                except ValueError:
                    state[dst] = None
            elif m == "add" and dst and len(parts) >= 3:
                src = norm(parts[1].strip())
                rhs = parts[2].strip()
                src_val = state.get(src) if src else None
                if rhs.startswith("#") and src_val is not None:
                    try:
                        state[dst] = (src_val + int(rhs[1:], 0)) & 0xFFFFFFFF
                    except ValueError:
                        state[dst] = None
                else:
                    state[dst] = None
            elif dst and m not in ("cmp", "cmn", "tst", "teq", "str", "strb", "strh", "stm", "stmdb", "stmia", "push", "pop"):
                state[dst] = None
            if m == "pop" and "pc" in ins.op_str:
                state.clear()

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("function\tseq_idx\tformula_id\tcache_offset\tcall_va\n")
        for fn, fid, off, call_va, sidx in rows:
            fid_s = f"0x{fid:x}" if fid is not None else "?"
            off_s = f"0x{off:x}" if off is not None else "?"
            f.write(f"{fn}\t{sidx}\t{fid_s}\t{off_s}\t0x{call_va:08x}\n")

    print(f"[+] {OUT} ({len(rows)} 호출)")
    print()
    print(f"== HERO::CalcStatusComputation 의 calc 호출 → cache 매핑 ==")
    print(f"{'seq':>3}  {'formula_id':>12s}  {'cache_off':>10s}  {'note'}")
    for fn, fid, off, call_va, sidx in rows:
        fid_s = f"0x{fid:x}" if fid is not None else "?"
        off_s = f"0x{off:x}" if off is not None else "?"
        # formula_id 가 0x7f0+ = calc_sk
        note = ""
        if fid is not None:
            if 0x7f0 <= fid < 0x800:
                note = f"calc_sk[{fid - 0x7f0}]"
            elif 0 <= fid < 39:
                note = f"calc_pl[{fid}]"
            elif 1000 <= fid < 1019:
                note = f"calc_en[{fid - 1000}]"
        print(f"{sidx:>3}  {fid_s:>12s}  {off_s:>10s}  {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
