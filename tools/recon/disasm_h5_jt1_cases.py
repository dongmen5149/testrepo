"""ProcHeroSkill Jumptable 1 의 5 case + class 2 GUNNER entry 정밀 disasm (Round 72).

R70 발견: JT1 @ 0x9a398 — dispatch key = skill_info[+0x28] (0..4).
  case 0 → 0x99978 (NO_HIT — also matches "rand failed" path)
  case 1, 2 → 0x9ac68 (effect_type 1·2)
  case 3, 5 → 0x9abfc (effect_type 3·5)
  case 4 → 0x9ab98 (effect_type 4)
R70 발견: class 2 (GUNNER) 별도 path @ 0x9a564

본 도구는 각 case target 의 ~60 instr 와 class 2 path entry ~80 instr 를 zoom
출력 + bl 호출 그래프 + HeroSkillInfo field access 패턴 통계.
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

# zoom 영역: (시작 주소, 길이 byte, 라벨)
ZOOMS = [
    (0x99978, 0x80, "JT1 case 0 = NO_HIT (also rand-fail path)"),
    (0x9ac68, 0x100, "JT1 case 1+2 = effect_type 1·2 (physical?)"),
    (0x9abfc, 0x100, "JT1 case 3+5 = effect_type 3·5 (magic?)"),
    (0x9ab98, 0x100, "JT1 case 4 = effect_type 4 (heal+buff?)"),
    (0x9a564, 0x100, "class 2 GUNNER entry"),
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

    for zoom_start, zoom_size, label in ZOOMS:
        zoom_end = zoom_start + zoom_size
        zoom_instrs = [ins for ins in all_instrs
                       if zoom_start <= ins.address < zoom_end]
        print("=" * 78)
        print(f"# {label}")
        print(f"# range {zoom_start:#x}..{zoom_end:#x}  ({len(zoom_instrs)} instr)")
        print("=" * 78)

        cmp_imms = Counter()
        bl_calls = []  # (addr, target, symbol)
        r6_fields = defaultdict(int)
        r4_fields = defaultdict(int)
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
            if m == "cmp" and "#" in op:
                parts = op.split(", ")
                if len(parts) == 2 and parts[1].startswith("#"):
                    try:
                        imm = int(parts[1][1:], 0)
                        cmp_imms[(parts[0], imm)] += 1
                    except ValueError:
                        pass
            if m in ("ldrb", "ldr", "ldrsb", "ldrh", "ldrsh") and "[" in op and "#" in op:
                try:
                    _, rest = op.split(", [", 1)
                    rest = rest.rstrip("]")
                    parts = rest.split(", #")
                    if len(parts) == 2:
                        rb = parts[0]
                        off = int(parts[1], 0)
                        if rb == "r6":
                            r6_fields[(m, off)] += 1
                        elif rb == "r4":
                            r4_fields[(m, off)] += 1
                except (ValueError, IndexError):
                    pass

            print(f"  {ins.address:08x}: {m:8} {op}{sym}")

        print(f"\n# --- 패턴 요약 ---")
        print(f"  cmp imm (top 10): {[(f'{r} #{i}', c) for (r, i), c in cmp_imms.most_common(10)]}")
        print(f"  bl calls: {len(bl_calls)}")
        for addr, tgt, sym_name in bl_calls[:15]:
            print(f"    @{addr:#x} → {tgt:#x}  {sym_name}")
        print(f"  HeroSkillInfo (r6) fields: {sorted(r6_fields.items(), key=lambda x: x[0][1])}")
        print(f"  HERO this (r4) fields: {sorted(r4_fields.items(), key=lambda x: x[0][1])}")
        print()


if __name__ == "__main__":
    main()
