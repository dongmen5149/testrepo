"""HERO::ApplyBuildupEffect / BATTLER::ApplyBuildupEffect 자동 entry table 추출.

ARM jumptable 패턴:
  cmp r3, #N           ; r3 = type-1 (effect 타입 0..N)
  addls pc, pc, r3, lsl #2  ; 점프 분기
  b <default>          ; idx 0 fallthrough
  b <case_1>           ; idx 1
  ...
  b <case_N>           ; idx N

각 case_K 위치의 시작에서:
  - mov r3, #<offset>; (add r3, r3, #<delta>;) ldrh/strh r2, [r0, r3]; add r5,r5,r2; strh r5,[r0,r3]
    → V[?] += arg (s16 add)
  - mov r3, #<offset>; strb r3, [r0, #<offset>]; mov r3, #<icon>; strb r2, [r4, #0x296]; ...
    → buff descriptor (effect_type/icon/strength)
  - bl <함수명>
    → 외부 함수 호출 (SP heal, Spirit, etc)
  - 등

산출: work/h5/analysis/applybuildup_table.tsv  (entry_type, target_offset, store_kind, note)
"""
from __future__ import annotations
import pathlib
import re

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/applybuildup_table.tsv"

TARGETS = [
    "_ZN4HERO18ApplyBuildupEffectEai",
    "_ZN7BATTLER18ApplyBuildupEffectEai",
]


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
    addr_to_name = {}
    fn_targets = []
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        n = s.name or ""
        addr_to_name.setdefault(a, n)
        if n in TARGETS:
            fn_targets.append((a, s.size, n))

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def get_data(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0: va - v0 + sz])
        return None

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    rows = []  # (fn, type_idx, target_va, kind, note)
    for fn_addr, fn_sz, fn_name in fn_targets:
        data = get_data(fn_addr, fn_sz)
        if not data:
            continue
        ins_list = list(md.disasm(data, fn_addr))
        # jumptable scan: find `addls pc, pc, r3, lsl #2` (or similar)
        jt_idx = None
        for i, ins in enumerate(ins_list):
            if ins.mnemonic.startswith("add") and "pc, pc" in ins.op_str and "lsl" in ins.op_str:
                jt_idx = i
                break
        if jt_idx is None:
            print(f"[!] {fn_name}: jumptable 패턴 없음")
            continue

        # 다음부터 연속된 b #imm 들을 jumptable entry 로 수집
        entries = []
        for ins in ins_list[jt_idx + 1:]:
            if ins.mnemonic == "b" and ins.op_str.startswith("#"):
                try:
                    target = int(ins.op_str[1:], 0) & ~1
                except ValueError:
                    break
                entries.append((ins.address, target))
            else:
                break
        # 첫 entry 가 default/idx=0 (보통 type=1 fallthrough)

        # case 코드 분석: 각 target 에서 store offset / 외부 호출 식별
        # target 별 시작점에서 ~10 명령 disasm 후 패턴 매칭
        # ins_addr → ins index map
        ins_by_addr = {ins.address: idx for idx, ins in enumerate(ins_list)}

        for entry_idx, (b_va, target_va) in enumerate(entries):
            # type = entry_idx + 1 (jumptable idx 0 = type 1)
            etype = entry_idx + 1
            # 타겟이 함수 내인 경우만 분석
            if target_va not in ins_by_addr:
                # 다른 함수로 분기 (default fallthrough → BATTLER::ApplyBuildupEffect)
                tn = addr_to_name.get(target_va, "")
                rows.append((fn_name, etype, b_va, target_va, "branch_extern",
                             simple_demangle(tn) if tn else f"0x{target_va:08x}"))
                continue
            seq = ins_list[ins_by_addr[target_va]: ins_by_addr[target_va] + 12]
            note, kind = analyze_case(seq)
            rows.append((fn_name, etype, b_va, target_va, kind, note))

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("function\tentry_type\tjt_va\ttarget_va\tkind\tnote\n")
        for fn, etype, b_va, t_va, kind, note in rows:
            f.write(f"{simple_demangle(fn)}\t{etype}\t0x{b_va:08x}\t0x{t_va:08x}\t{kind}\t{note}\n")

    print(f"[+] {OUT}")

    # 요약: HERO 의 entry → V slot
    print()
    print("== HERO::ApplyBuildupEffect entry table ==")
    print(f"{'type':>4}  {'kind':<14}  {'note'}")
    for fn, etype, b_va, t_va, kind, note in rows:
        if "HERO" in fn:
            print(f"{etype:>4}  {kind:<14}  {note}")

    return 0


def analyze_case(seq) -> tuple[str, str]:
    """case 시작 시퀀스 (~12 ins) 에서 store target 식별."""
    if not seq:
        return ("(empty)", "unknown")

    # mov r3, #<imm> ; (add r3, r3, #<delta>) ; ldrh r2, [r0, r3] ; add r5, r5, r2 ; strh r5, [r0, r3]
    # → V add at offset
    base = None
    delta = 0
    has_ldrh = False
    has_strh = False
    has_strb = False
    strb_target = None
    bl_target = None
    bl_name = None
    misc = []

    for ins in seq:
        m = ins.mnemonic
        op = ins.op_str
        if m in ("mov", "movs") and op.startswith("r3, #"):
            try:
                base = int(op.split("#")[1], 0)
            except ValueError:
                base = None
        elif m == "add" and op.startswith("r3, r3, #") and base is not None:
            try:
                delta += int(op.split("#")[1], 0)
            except ValueError:
                pass
        elif m == "ldrh" and "[r0, r3]" in op:
            has_ldrh = True
        elif m == "strh" and "[r0, r3]" in op:
            has_strh = True
        elif m == "strb":
            # strb r3, [r0, #N]  / strb r2, [r4, #N]
            mret = re.search(r"\[(\w+),\s*#(0x[0-9a-fA-F]+|\d+)\]", op)
            if mret:
                strb_target = int(mret.group(2), 0)
                misc.append((m, op))
        elif m == "bl" and op.startswith("#"):
            try:
                bl_target = int(op[1:], 0) & ~1
            except ValueError:
                pass
        elif m == "b" and op.startswith("#"):
            break

    if has_ldrh and has_strh and base is not None:
        offset = (base + delta) & 0xFFFF
        return (f"V_at_0x{offset:03x}_add", "v_add_s16")
    if strb_target is not None:
        return (f"strb_at_0x{strb_target:03x}", "strb_const_or_arg")
    if bl_target is not None:
        return (f"bl 0x{bl_target:08x}", "extern_call")
    return ("complex/other", "complex")


if __name__ == "__main__":
    raise SystemExit(main())
