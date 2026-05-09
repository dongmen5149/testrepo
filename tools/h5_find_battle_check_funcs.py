"""전투 판정 함수에서 calc_pl id 직접 호출 추적.

BATTLER / TargetEffect / Damage 관련 함수를 disasm 하면서
mov r1, #N (N=25..29) 후 BL Formula::calc 패턴을 찾는다.

이 패턴이 발견되면 N 이 어느 stat 인지 caller 함수 이름으로 식별.
"""
from __future__ import annotations
import pathlib
import re

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

CALC_SYM = "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase"


def simple_demangle(mangled: str) -> str:
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

    syms_by_addr = {}
    calc_addr = None
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        syms_by_addr.setdefault(a, (s.name or "", s.size))
        if s.name == CALC_SYM:
            calc_addr = a

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def get_data(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0: va - v0 + sz])
        return None

    # BATTLER / TargetEffect / Hit / Avoid / Crit / Damage / Attack 관련 함수만 분석
    targets = []
    for addr, (name, sz) in syms_by_addr.items():
        if not name.startswith("_ZN"):
            continue
        d = simple_demangle(name)
        # 전투 핵심 클래스 관련
        if any(kw in d for kw in (
            "BATTLER::", "TargetEffect::", "HERO::Calc",
            "Hit", "Avoid", "Crit", "Damage", "Demage",
            "ProcSkill", "ProcAttack", "Block", "Speed",
            "AttackProc", "MoveProc", "HiperCount",
        )):
            targets.append((addr, sz, name, d))

    print(f"[+] 전투 관련 함수 {len(targets)}개 분석")

    findings = []  # (formula_id, caller_demangled, caller_addr, call_va)

    REG_ALIAS = {"ip": "r12", "sp": "r13", "lr": "r14", "pc": "r15", "fp": "r11", "sl": "r10", "sb": "r9"}
    def norm(r: str) -> str | None:
        r = r.strip().lower()
        if r in REG_ALIAS:
            r = REG_ALIAS[r]
        return r if r in {f"r{i}" for i in range(13)} else None

    # 분기/branch mnemonic (b, bx, bcond... 단, bl, blx 는 호출이라 별도)
    BRANCH_RE = re.compile(r"^b(eq|ne|cs|hs|cc|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al|x)?$")

    for fn_addr, fn_sz, mangled, demangled in targets:
        data = get_data(fn_addr, fn_sz)
        if not data:
            continue
        # register state — basic block 단위
        state: dict[str, int | None] = {}
        for ins in md.disasm(data, fn_addr):
            m = ins.mnemonic
            op = ins.op_str.replace(" ", "")

            # BL 호출
            if m == "bl" and op.startswith("#"):
                try:
                    target = int(op[1:], 0) & ~1
                except ValueError:
                    target = None
                if target == calc_addr:
                    fid = state.get("r1")
                    findings.append((fid, demangled, fn_addr, ins.address))
                # caller-saved 무효화
                for r in ("r0", "r1", "r2", "r3", "r12", "r14"):
                    state[r] = None
                continue
            if m == "blx":
                for r in ("r0", "r1", "r2", "r3", "r12", "r14"):
                    state[r] = None
                continue

            # branch — basic block 끝
            if BRANCH_RE.match(m) or m == "b":
                state.clear()
                continue

            parts = ins.op_str.split(",")
            dst = norm(parts[0].strip()) if parts else None

            if m in ("mov", "movs"):
                if dst and len(parts) >= 2:
                    rhs = parts[1].strip()
                    if rhs.startswith("#"):
                        try:
                            state[dst] = int(rhs[1:], 0)
                        except ValueError:
                            state[dst] = None
                    else:
                        src = norm(rhs)
                        state[dst] = state.get(src) if src else None
            elif m in ("movw", "movt"):
                if dst and len(parts) >= 2 and parts[1].strip().startswith("#"):
                    try:
                        v = int(parts[1].strip()[1:], 0) & 0xFFFF
                    except ValueError:
                        v = None
                    if v is None:
                        state[dst] = None
                    elif m == "movw":
                        state[dst] = v
                    else:  # movt
                        cur = state.get(dst) or 0
                        state[dst] = (cur & 0xFFFF) | (v << 16)
                elif dst:
                    state[dst] = None
            elif m == "add":
                # add rD, rS, #imm — 자주 보이는 패턴 (mov r1, #0x7f0; add r1, r1, #N)
                if dst and len(parts) >= 3:
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
                elif dst:
                    state[dst] = None
            elif m in ("ldr", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldm", "ldmia"):
                if dst:
                    state[dst] = None
            elif m in ("str", "strb", "strh", "stm", "stmdb", "stmia", "push", "pop", "cmp", "cmn", "tst", "teq"):
                if m == "pop" and "pc" in ins.op_str:
                    state.clear()
                # set 안 함
            else:
                if dst:
                    state[dst] = None

    print(f"[+] {len(findings)} 호출 분석")

    # by_id 요약
    by_id: dict[int, list[tuple[str, int]]] = {}
    unknown = 0
    for fid, dem, addr, call_va in findings:
        if fid is None:
            unknown += 1
            continue
        by_id.setdefault(fid, []).append((dem, addr))
    print(f"    formula_id 추정 가능: {len(findings) - unknown} / {len(findings)}")

    # 정렬 출력 — 25..29 핵심
    print()
    print("== id별 caller (전투 함수 한정) ==")
    for fid in sorted(by_id):
        callers = by_id[fid]
        unique = sorted({(d, a) for d, a in callers})
        print(f"  id={fid:>4}  ({len(unique)} unique caller)")
        for d, a in unique[:10]:
            print(f"      0x{a:08x}  {d}")
        if len(unique) > 10:
            print(f"      ... +{len(unique)-10} more")

    # TSV 저장
    out = ROOT / "work/h5/analysis/battle_formula_callers.tsv"
    with out.open("w", encoding="utf-8") as f:
        f.write("formula_id\tcaller_addr\tcall_va\tcaller_demangled\n")
        for fid, dem, addr, call_va in sorted(findings, key=lambda r: (r[0] or 99999, r[3])):
            fid_s = str(fid) if fid is not None else "?"
            f.write(f"{fid_s}\t0x{addr:08x}\t0x{call_va:08x}\t{dem}\n")
    print(f"\n[+] {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
