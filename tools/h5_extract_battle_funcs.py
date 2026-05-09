"""BATTLER / Monster / HERO 의 데미지 관련 함수들을 capstone 으로 disasm.

목표: 정확한 ATK/DEF/Critical 공식과 HP 감소/증가 흐름의 Ground Truth 확보.
산출:
  work/h5/analysis/battle_damage_funcs.txt  — 함수별 ARM 디스어셈블 dump
  work/h5/analysis/battle_damage_summary.tsv — 함수 → size, callee 카운트, str ref
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT_DUMP = ROOT / "work/h5/analysis/battle_damage_funcs.txt"
OUT_TSV = ROOT / "work/h5/analysis/battle_damage_summary.tsv"

# 우선 분석 대상 (mangled name → 표시명).
TARGETS = [
    ("_ZN7BATTLER10IncreaseHPEi",                "BATTLER::IncreaseHP(int)"),
    ("_ZN7BATTLER14ApplyAddEffectEasP13HeroSkillInfo", "BATTLER::ApplyAddEffect(short, HeroSkillInfo*)"),
    ("_ZN7BATTLER21InitStatusComputationEv",     "BATTLER::InitStatusComputation()"),
    ("_ZN7BATTLER18ApplyBuildupEffectEai",       "BATTLER::ApplyBuildupEffect(short, int)"),
    ("_ZN7Monster15AddEffectDamageEs",           "Monster::AddEffectDamage(short)"),
    ("_ZN7Monster9HitedProcEPiS0_",              "Monster::HitedProc(int*, int*)"),
    ("_ZN9EventProc18Event_PlayerDamageEa",      "EventProc::Event_PlayerDamage(char)"),
    ("_ZN4HERO9HitedProcEv",                     "HERO::HitedProc()"),
    ("_ZN4HERO20HeroSkillAtkHardCodeEP13HeroSkillInfoP7BATTLER", "HERO::HeroSkillAtkHardCode(...)"),
    ("_ZN12TargetEffect12NewHitEffectEP13HeroSkillInfoP7BATTLER", "TargetEffect::NewHitEffect(...)"),
    ("_ZN4HERO12NewHitEffectEP13HeroSkillInfoP7BATTLER", "HERO::NewHitEffect(...)"),
]


def main() -> int:
    try:
        import lief, capstone
    except ImportError:
        print("pip install lief capstone", file=sys.stderr)
        return 1

    if not SO.exists():
        print(f"missing {SO} — apk unzip 먼저", file=sys.stderr)
        return 1

    so = lief.parse(str(SO))
    blob = bytes(so.get_content_from_virtual_address(0, 0))  # not reliable

    # 정확히 메모리 매핑 — 각 PT_LOAD 세그먼트를 읽어 dict 로 재구성.
    seg_data: list[tuple[int, int, bytes]] = []  # (vstart, vend, bytes)
    for s in so.segments:
        if s.type != lief.ELF.Segment.TYPE.LOAD:
            continue
        seg_data.append((s.virtual_address,
                         s.virtual_address + s.virtual_size,
                         bytes(s.content)))

    def read(va: int, size: int) -> bytes | None:
        for v0, v1, data in seg_data:
            if v0 <= va < v1:
                off = va - v0
                return bytes(data[off:off+size])
        return None

    # symbol 검색 (이름 → (addr, size))
    sym_index: dict[str, tuple[int, int, bool]] = {}  # (addr, size, thumb)
    for sym in so.symbols:
        n = sym.name or ""
        if n and sym.value and sym.size:
            thumb = bool(sym.value & 1)
            sym_index.setdefault(n, (sym.value & ~1, sym.size, thumb))

    # 모든 심볼을 va 기준으로 정렬 → callee 추정.
    addr_to_name: dict[int, str] = {}
    for n, (a, _sz, _th) in sym_index.items():
        addr_to_name.setdefault(a, n)

    # 심볼 LSB == 1 → Thumb. armeabi 의 경우 대부분 ARM(LSB=0). 동적 선택.
    md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md_arm.detail = True
    md_thumb.detail = True

    OUT_DUMP.parent.mkdir(parents=True, exist_ok=True)
    out = OUT_DUMP.open("w", encoding="utf-8")
    summary_rows: list[tuple[str, str, int, int, int]] = []  # (mangled, pretty, addr, size, callee_count)

    for mangled, pretty in TARGETS:
        info = sym_index.get(mangled)
        if not info:
            out.write(f"\n=== {pretty} ===\n  (symbol not found)\n")
            continue
        addr, size, thumb = info
        data = read(addr, size)
        if data is None:
            out.write(f"\n=== {pretty} ===\n  (no segment data @ 0x{addr:08x})\n")
            continue

        mode = "THUMB" if thumb else "ARM"
        out.write(f"\n=== {pretty}  @ 0x{addr:08x}  size={size}  mode={mode}  ===\n")
        callees = 0
        md = md_thumb if thumb else md_arm
        for ins in md.disasm(data, addr):
            comment = ""
            # branch target 분석 (bl/blx imm, b/bx imm)
            if ins.mnemonic.startswith(("bl", "b")) and ins.op_str.startswith("#"):
                try:
                    tgt = int(ins.op_str[1:], 0) & ~1
                    target_name = addr_to_name.get(tgt)
                    if target_name:
                        # demangle 간단화
                        comment = f"  ; -> {target_name[:80]}"
                        if ins.mnemonic.startswith("bl"):
                            callees += 1
                except ValueError:
                    pass
            out.write(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{comment}\n")

        summary_rows.append((mangled, pretty, addr, size, callees))

    out.close()

    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("addr\tsize\tcallees\tpretty\tmangled\n")
        for mn, pr, a, sz, cc in summary_rows:
            f.write(f"0x{a:08x}\t{sz}\t{cc}\t{pr}\t{mn}\n")

    print(f"functions analyzed: {len(summary_rows)}")
    print(f"dump  -> {OUT_DUMP.relative_to(ROOT)}")
    print(f"summary -> {OUT_TSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
