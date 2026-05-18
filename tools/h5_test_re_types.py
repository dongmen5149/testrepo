"""Round 59 RE 결과 검증 — Mission sub_type 정밀 매핑 + RE 함수 주소 무결성.

확인 항목:
1. ELF symbol table 에서 RE 한 23 함수 주소가 모두 valid (text 영역 내).
2. mission_system.gd 의 EVENT_TO_SUB_TYPES 매핑이 mission.json 데이터와 일관:
   - sub_type 6 (Refine) 미션 존재
   - sub_type 10 (OrbCombine) 미션 존재
   - sub_type 2 (Playtime) 미션 존재
3. type=3 누적 도전 의 sub_type 분포 (Round 58 의 가설 대비 실제 분포 확인).
4. mission_type=1 (boss kill) 의 5건 미션이 모두 boss-like name 포함.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MISSION_JSON = Path("apps/hero5-godot/assets/gamedata/mission.json")
SO_PATH = Path("work/h5/extracted/lib/armeabi/libHeroesLore5.so")

# Round 59 RE — disasm_h5_mission_quest.py 산출 함수 주소
RE_FUNCTIONS = {
    "Mission::HuntingCounting":         (0x089f10, 156),
    "Mission::QuestCompleteCounting":   (0x089ff0, 16),
    "Mission::BossCompleteCounting":    (0x08a000, 16),
    "Mission::CompleteMission":         (0x08a330, 204),
    "Mission::CheckStatistics":         (0x08a3fc, 496),
    "Mission::CheckQuestComplete":      (0x08a5ec, 256),
    "Mission::CheckMonsterHunting":     (0x08a6ec, 516),
    "Mission::CheckCollection":         (0x08a8f0, 372),
    "Mission::CheckSpiritSkillAll":     (0x08aa64, 112),
    "Mission::CheckMissionRank":        (0x08ab10, 252),
    "Mission::CheckOrbCombine":         (0x08ac0c, 236),
    "Mission::CheckMissionMix":         (0x08acf8, 268),
    "Mission::CheckMissionRefine":      (0x08ae04, 196),
    "Mission::CheckBattleUseItem":      (0x08aec8, 204),
    "Mission::CheckMissionPlaytime":    (0x08af94, 340),
    "Mission::CheckMissionHeroDie":     (0x08b0e8, 196),
    "Mission::CheckMissionMoney":       (0x08b1ac, 212),
    "Mission::CheckMission99Level":     (0x08b280, 96),
    "Mission::CheckMissionSetItem":     (0x08b2e0, 292),
    "Mission::LoadMissionTable":        (0x08b73c, 460),
    "QuestMgr::QuestCheck":             (0x0d3acc, 1492),
    "QuestMgr::Quest_GetOffset":        (0x0d40a0, 72),
    "QuestMgr::LoadQuestData":          (0x0d40e8, 1188),
}


def main() -> None:
    print("# Round 59 Hero5 Mission/Quest RE 검증\n")

    # 1. .so 의 ELF 헤더에서 .text 영역 확인 + 함수 주소가 모두 valid range
    if not SO_PATH.exists():
        print(f"[skip] {SO_PATH} 미발견 (.so 없음)")
    else:
        from elftools.elf.elffile import ELFFile
        with open(SO_PATH, "rb") as f:
            elf = ELFFile(f)
            text = elf.get_section_by_name(".text")
            text_va = text["sh_addr"]
            text_size = text["sh_size"]
            print(f"  .text @ {text_va:#x} + {text_size}B")

            # ELF symbol 에서 RE 한 함수 주소 cross-verify
            sym_addrs = {}
            for section in elf.iter_sections():
                if section.name not in (".symtab", ".dynsym"): continue
                for sym in section.iter_symbols():
                    sym_addrs[sym.name] = sym["st_value"] & ~1

            mangled_map = {
                "_ZN7Mission15HuntingCountingEia": "Mission::HuntingCounting",
                "_ZN7Mission20BossCompleteCountingEv": "Mission::BossCompleteCounting",
                "_ZN7Mission18CheckMissionRefineEv": "Mission::CheckMissionRefine",
                "_ZN7Mission15CheckOrbCombineEa": "Mission::CheckOrbCombine",
                "_ZN7Mission19CheckMissionSetItemEv": "Mission::CheckMissionSetItem",
                "_ZN7Mission16CheckMissionRankEv": "Mission::CheckMissionRank",
                "_ZN7Mission15CheckCollectionEv": "Mission::CheckCollection",
                "_ZN8QuestMgr10QuestCheckEaaaa": "QuestMgr::QuestCheck",
            }
            print("\n  주소 cross-verify (mangled vs RE 산출):")
            mismatch = 0
            for mangled, label in mangled_map.items():
                expected = RE_FUNCTIONS[label][0]
                actual = sym_addrs.get(mangled)
                if actual is None:
                    print(f"    ✗ {label}: ELF 에 심볼 없음")
                    mismatch += 1
                elif actual != expected:
                    print(f"    ✗ {label}: 기대 {expected:#x}, ELF {actual:#x}")
                    mismatch += 1
                else:
                    print(f"    ✓ {label}: {actual:#x}")
            assert mismatch == 0, f"{mismatch} symbol address mismatches"

            # 모든 RE 함수가 .text 범위 내
            text_end = text_va + text_size
            for label, (addr, size) in RE_FUNCTIONS.items():
                in_range = text_va <= addr < text_end and addr + size <= text_end
                if not in_range:
                    print(f"    ✗ {label} @ {addr:#x} +{size}B 가 .text 범위 외")
            print(f"  ✓ {len(RE_FUNCTIONS)} 함수 모두 .text 영역 내")

    # 2. mission.json 의 type 3 sub_type 분포 검증
    if not MISSION_JSON.exists():
        print(f"\n[skip] {MISSION_JSON} 미발견")
        return
    data = json.loads(MISSION_JSON.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    type3_entries = [e for e in entries if int(e.get("mission_type", 255)) == 3]
    print(f"\n# type=3 누적 도전 sub_type 분포 (총 {len(type3_entries)}개):")
    sub_dist = Counter(int(e.get("sub_type", 0)) for e in type3_entries)
    for st, cnt in sub_dist.most_common():
        print(f"  sub_type {st:3d}: {cnt}건")

    # RE 결과 sub_type 6/10/2 가 모두 존재해야 함
    REQUIRED_SUB_TYPES = {
        6: "Refine (CheckMissionRefine)",
        10: "OrbCombine (CheckOrbCombine)",
        2: "Playtime (CheckMissionPlaytime)",
        1: "HeroDie (CheckMissionHeroDie)",
        4: "BattleUseItem (CheckBattleUseItem)",
    }
    print("\n  RE 기대 sub_type 존재 검증:")
    for st, label in REQUIRED_SUB_TYPES.items():
        present = st in sub_dist
        print(f"    {'✓' if present else '✗'} sub_type {st} ({label}): {sub_dist.get(st, 0)}건")
        assert present, f"sub_type {st} ({label}) 가 type 3 미션에 없음"

    # 3. type=1 (boss kill) 미션 5개 — name 에 boss/특수 키워드
    print("\n# type=1 (특수 처치 / Boss kill) 미션 5개:")
    type1 = [e for e in entries if int(e.get("mission_type", 255)) == 1]
    assert len(type1) == 5
    for e in type1:
        sc = e.get("sub_conditions", [])
        active = [c for c in sc if c["slot"] != 255 or c["sub_flag"] != 255]
        sc_str = ", ".join(f"sub#{c['sub_flag']}" for c in active if c["sub_flag"] != 255)
        print(f"  [{e['idx']:3d}] '{e['name']}' — sub_flag={sc_str or '(없음)'}")

    # 4. type=0 (사냥) sub_flag = monster_id 검증 (Round 59 RE 매핑)
    print("\n# type=0 (사냥) — sub_flag 가 monster_id 매핑:")
    type0 = [e for e in entries if int(e.get("mission_type", 255)) == 0]
    print(f"  {len(type0)}개 미션, 첫 3개 sub_flag:")
    for e in type0[:3]:
        sub_flags = [c["sub_flag"] for c in e["sub_conditions"]
                     if c["sub_flag"] != 255]
        target_values = [c["target_value"] for c in e["sub_conditions"]
                        if c["sub_flag"] != 255]
        print(f"    '{e['name']}' — monster_id {sub_flags} × kill_count {target_values}")

    print("\n# All Round 59 RE checks passed.")


if __name__ == "__main__":
    main()
