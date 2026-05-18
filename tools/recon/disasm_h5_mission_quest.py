"""Hero5 Mission::CheckMission* + QuestMgr::QuestCheck 함수 동시 디스어셈블 (Round 59).

목적:
  - 13 Mission::Check* 함수 + QuestMgr::QuestCheck 의 ARM/Thumb 디스어셈블
  - cond_type 14/13/17 (Quest) 와 mission_type 0-5 (Mission) 의 의미 추론
  - 각 함수가 어떤 sub_flag/slot 을 어떻게 사용하는지 패턴 분석

전략:
  1. ELF symbol table 에서 _ZN7Mission..., _ZN8QuestMgr... 추출 → 주소 매핑
  2. 각 함수 첫 ~300B 디스어셈블 (capstone Thumb)
  3. 핵심 instruction (cmp #N / ldrb / bne) 으로 type 매핑 추론
  4. 결과 출력 → docs/h5/RE/mission_quest_types.md 와 추후 통합
"""
from __future__ import annotations
import pathlib
import sys
import re
from collections import OrderedDict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM


# 관심 함수 mangled name → label (출력용)
TARGETS = OrderedDict([
    ("_ZN7Mission15HuntingCountingEia",   "Mission::HuntingCounting(monster_id, type)"),
    ("_ZN7Mission19CheckMonsterHuntingEv", "Mission::CheckMonsterHunting"),
    ("_ZN7Mission20BossCompleteCountingEv", "Mission::BossCompleteCounting"),
    ("_ZN7Mission18CheckMissionRefineEv",  "Mission::CheckMissionRefine"),
    ("_ZN7Mission15CheckOrbCombineEa",     "Mission::CheckOrbCombine(arg)"),
    ("_ZN7Mission15CheckMissionMixEaa",    "Mission::CheckMissionMix(a, b)"),
    ("_ZN7Mission19CheckMissionSetItemEv", "Mission::CheckMissionSetItem"),
    ("_ZN7Mission16CheckMissionRankEv",    "Mission::CheckMissionRank"),
    ("_ZN7Mission17CheckMissionMoneyEv",   "Mission::CheckMissionMoney"),
    ("_ZN7Mission20CheckMissionPlaytimeEv","Mission::CheckMissionPlaytime"),
    ("_ZN7Mission18CheckQuestCompleteEv",  "Mission::CheckQuestComplete"),
    ("_ZN7Mission15CheckCollectionEv",     "Mission::CheckCollection"),
    ("_ZN7Mission19CheckMission99LevelEv", "Mission::CheckMission99Level"),
    ("_ZN7Mission19CheckMissionHeroDieEv", "Mission::CheckMissionHeroDie"),
    ("_ZN7Mission18CheckBattleUseItemEa",  "Mission::CheckBattleUseItem(a)"),
    ("_ZN7Mission21QuestCompleteCountingEh","Mission::QuestCompleteCounting(qid)"),
    ("_ZN7Mission19CheckSpiritSkillAllEv", "Mission::CheckSpiritSkillAll"),
    ("_ZN7Mission15CheckStatisticsEv",     "Mission::CheckStatistics"),
    ("_ZN7Mission15CompleteMissionEs",     "Mission::CompleteMission(mid)"),
    ("_ZN7Mission16LoadMissionTableEv",    "Mission::LoadMissionTable"),
    ("_ZN8QuestMgr10QuestCheckEaaaa",      "QuestMgr::QuestCheck(a,b,c,d)"),
    ("_ZN8QuestMgr15Quest_GetOffsetEjs",   "QuestMgr::Quest_GetOffset"),
    ("_ZN8QuestMgr13LoadQuestDataEaa",     "QuestMgr::LoadQuestData"),
])


def collect_symbols(elf: ELFFile) -> dict:
    """name → (addr, size) for target functions only."""
    out = {}
    for section in elf.iter_sections():
        if section.name not in (".symtab", ".dynsym"): continue
        for sym in section.iter_symbols():
            if sym.name in TARGETS:
                # ARM Thumb addresses have bit 0 = 1 — strip
                addr = sym["st_value"] & ~1
                size = sym["st_size"]
                out[sym.name] = (addr, size, bool(sym["st_value"] & 1))
    return out


def disasm_fn(data: bytes, base_va: int, addr: int, size: int, thumb: bool, max_lines: int = 60):
    """Disassemble function starting at addr (ELF virtual). Print up to max_lines."""
    file_off = addr - base_va
    if file_off < 0 or file_off + size > len(data):
        print(f"  ! out of range: file_off={file_off:#x} size={size}")
        return
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.detail = False
    show_size = min(size, max_lines * 4 + 8)
    buf = data[file_off:file_off + show_size]
    count = 0
    for ins in md.disasm(buf, addr):
        print(f"    {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
        count += 1
        if count >= max_lines: break


def find_text_base(elf: ELFFile) -> int:
    """Linear file offset = 0 의 VA (보통 0 또는 LOAD segment 의 base)."""
    for seg in elf.iter_segments():
        if seg["p_type"] == "PT_LOAD" and seg["p_offset"] == 0:
            return seg["p_vaddr"]
    return 0


def extract_cmp_immediates(data: bytes, base_va: int, addr: int, size: int, thumb: bool) -> list:
    """CMP #imm 명령의 imm 추출 (type-byte switch 의 case key 추론)."""
    file_off = addr - base_va
    if file_off < 0 or file_off + size > len(data):
        return []
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    out = []
    for ins in md.disasm(data[file_off:file_off + size], addr):
        if ins.mnemonic == "cmp" and "#" in ins.op_str:
            m = re.search(r"#(0x[0-9a-f]+|-?\d+)", ins.op_str)
            if m:
                v = m.group(1)
                imm = int(v, 16) if v.startswith("0x") else int(v)
                # 0..255 범위만 (type-byte 후보)
                if -16 <= imm <= 255:
                    out.append((ins.address, imm, ins.op_str))
    return out


def main() -> None:
    g = select("h5")
    bin_path = g.binary_path
    print(f"# Round 59 Hero5 Mission/Quest RE")
    print(f"binary: {bin_path}")
    if not bin_path.exists():
        print(f"!! {bin_path} 미발견")
        sys.exit(1)

    with open(bin_path, "rb") as f:
        elf = ELFFile(f)
        base_va = find_text_base(elf)
        symbols = collect_symbols(elf)
        f.seek(0)
        data = f.read()

    print(f"base_va: {base_va:#x}")
    print(f"resolved symbols: {len(symbols)} / {len(TARGETS)}")
    missing = [n for n in TARGETS if n not in symbols]
    if missing:
        print("missing:")
        for m in missing:
            print(f"  - {m} ({TARGETS[m]})")

    print("\n=== Function summary ===")
    for name, label in TARGETS.items():
        if name not in symbols: continue
        addr, size, thumb = symbols[name]
        mode = "T" if thumb else "A"
        print(f"  {addr:08x} +{size:4d}B {mode}  {label}")

    print("\n\n=== CMP #imm extraction (type-byte case 추론) ===\n")
    for name, label in TARGETS.items():
        if name not in symbols: continue
        addr, size, thumb = symbols[name]
        cmps = extract_cmp_immediates(data, base_va, addr, size, thumb)
        if not cmps:
            print(f"{label}:  (no CMP #imm)")
            continue
        # 중복 제거 + 0..63 범위 위주
        seen = set()
        uniq = []
        for a, imm, ops in cmps:
            if imm in seen: continue
            seen.add(imm)
            uniq.append((a, imm))
        print(f"{label}:")
        print(f"  size={size}B, CMP imms: {[hex(i) if i > 9 else str(i) for _, i in uniq[:20]]}")

    # 핵심 5개 함수 disasm
    PRIORITY = [
        "_ZN7Mission15HuntingCountingEia",
        "_ZN7Mission19CheckMonsterHuntingEv",
        "_ZN7Mission19CheckMissionSetItemEv",
        "_ZN7Mission18CheckMissionRefineEv",
        "_ZN8QuestMgr10QuestCheckEaaaa",
    ]
    print("\n\n=== Priority function disassembly (first 40 lines) ===\n")
    for name in PRIORITY:
        if name not in symbols: continue
        addr, size, thumb = symbols[name]
        print(f"--- {TARGETS[name]}  @{addr:#x} +{size}B ---")
        disasm_fn(data, base_va, addr, size, thumb, max_lines=40)
        print()


if __name__ == "__main__":
    main()
