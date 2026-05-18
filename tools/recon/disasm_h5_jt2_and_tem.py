"""ProcHeroSkill JT2 4 case zoom + TargetEffectMgr::NewTargetEffect 호출 11회 분석 (Round 73).

R70 발견: JT2 @ 0x9a8d8 — dispatch key = HERO::GetCurActSkillIdx() (0..6).
  case 0, 2, 4, 6 → 0x99904 (기본 공격 alias)
  case 1, 7      → 0x9ad78 (skill A / default)
  case 3         → 0x9acf8 (skill B)
  case 5         → 0x9aa18 (skill C)

PASS 1: JT2 case 4 영역 zoom + dispatch key 검증
PASS 2: TargetEffectMgr::NewTargetEffect (@0x62d40) 호출 11회 위치 + 인자 셋업 패턴

TEM signature (mangled): NewTargetEffect(a, i, P13HeroSkillInfo, P6SPRITE, a, a, a, a, s, i, i)
  → (char, int, HeroSkillInfo*, SPRITE*, char, char, char, char, short, int, int)
"""
from __future__ import annotations
import pathlib, sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


PROC_HERO_SKILL = 0x99278
PROC_HERO_SKILL_SIZE = 7972
TEM_ADDR = 0x62d40

ZOOMS = [
    (0x99904, 0x80, "JT2 case 0/2/4/6 = 기본 공격 alias (entry)"),
    (0x9ad78, 0x100, "JT2 case 1/7 = skill A (default)"),
    (0x9acf8, 0x80, "JT2 case 3 = skill B"),
    (0x9aa18, 0x100, "JT2 case 5 = skill C"),
]


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    by_addr = {}
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            by_addr.setdefault(v, []).append(s.name)

    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= PROC_HERO_SKILL < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (PROC_HERO_SKILL - seg.virtual_address)
            break
    chunk = data[file_offset:file_offset + PROC_HERO_SKILL_SIZE]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    all_instrs = list(md.disasm(chunk, PROC_HERO_SKILL))

    # === PASS 1: JT2 4 case zoom ===
    for zoom_start, zoom_size, label in ZOOMS:
        zoom_end = zoom_start + zoom_size
        zoom_instrs = [ins for ins in all_instrs
                       if zoom_start <= ins.address < zoom_end]
        print("=" * 78)
        print(f"# {label}")
        print(f"# range {zoom_start:#x}..{zoom_end:#x}  ({len(zoom_instrs)} instr)")
        print("=" * 78)

        bl_calls = []
        for ins in zoom_instrs:
            sym = ""
            m, op = ins.mnemonic, ins.op_str
            if m in ("bl", "blx") and op.startswith("#"):
                try:
                    tgt = int(op[1:], 0)
                    names = by_addr.get(tgt & ~1, [])
                    if names:
                        sym = f"  ; {names[0]}"
                    bl_calls.append((ins.address, tgt, names[0] if names else "?"))
                except ValueError:
                    pass
            print(f"  {ins.address:08x}: {m:8} {op}{sym}")
        print(f"\n  # bl calls: {len(bl_calls)}")
        for addr, tgt, sym_name in bl_calls:
            print(f"    @{addr:#x} → {tgt:#x}  {sym_name}")
        print()

    # === PASS 2: TargetEffectMgr::NewTargetEffect 호출 11회 + 인자 추적 ===
    print("=" * 78)
    print(f"# PASS 2: TargetEffectMgr::NewTargetEffect (@{TEM_ADDR:#x}) 호출 11회 + 직전 12 instr context")
    print("=" * 78)

    tem_calls = [ins for ins in all_instrs
                 if ins.mnemonic in ("bl", "blx") and ins.op_str == f"#{TEM_ADDR:#x}"]
    print(f"\n# {len(tem_calls)} TEM 호출\n")
    for i, call_ins in enumerate(tem_calls):
        # 직전 12 instr 추출 (arg setup 추적)
        idx = all_instrs.index(call_ins)
        ctx = all_instrs[max(0, idx-12):idx+1]
        print(f"## TEM call #{i+1} @ {call_ins.address:#x}")
        for ins in ctx:
            marker = "  <-- TEM call" if ins.address == call_ins.address else ""
            print(f"   {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        print()


if __name__ == "__main__":
    main()
