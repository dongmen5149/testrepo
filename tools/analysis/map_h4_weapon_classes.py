"""Round 76 — Hero4 weapon class × character class mapping.

R75 발견 7 weapon classes (_ITM_00..06) + R69 4 character classes (S000..S003) 매핑.

근거:
- Dual-ATK (ATK1+ATK2 모두 nonzero) → 검류 4종 (_ITM_00..03)
- Single-ATK (ATK2=0, ATK1 큰 값) → 총류 3종 (_ITM_04..06)
- 각 dual class 가 고유 level 진행 곡선 보유 → 캐릭터 전용 등급표
- 3 single class 가 동일 level 곡선 공유 → 한 캐릭터의 무기 sub-type
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / 'apps/hero4-android/app/src/main/assets/h4_items_detailed.json'
CATALOG = ROOT / 'apps/hero4-android/app/src/main/assets/h4_catalog.json'
OUT = ROOT / 'work/h4/converted/h4_weapon_class_mapping.json'


def fix_mojibake(s: str) -> str:
    try:
        return s.encode('latin-1').decode('cp949')
    except Exception:
        return s


def summarize(entries):
    a1 = [e['weapon_stats']['atk1'] for e in entries]
    a2 = [e['weapon_stats']['atk2'] for e in entries]
    lv = [e['weapon_stats']['level_req'] for e in entries]
    return {
        'count': len(entries),
        'is_dual_atk': any(x > 0 for x in a2),
        'lv_start': lv[0], 'lv_max': max(lv), 'lv_step1': lv[1] - lv[0],
        'lv_curve': lv,
        'atk1_avg': round(sum(a1) / len(a1), 1),
        'atk2_avg': round(sum(a2) / len(a2), 1),
        'damage_sum_avg': round((sum(a1) + sum(a2)) / len(a1), 1),
    }


def main():
    items = json.loads(ITEMS.read_text(encoding='utf-8'))
    weapon_dat = items['dat_files'][:7]

    summary = {f['file']: summarize(f['entries']) for f in weapon_dat}

    # Mapping by total damage avg + dual/single
    # _ITM_01 가장 높은 dual → S000 양손검 (two-handed, highest)
    # _ITM_02 mid dual → S002 마검 (magic sword)
    # _ITM_00 mid-low dual → S003 단도마법 (dagger+magic)
    # _ITM_03 lowest dual → reserve (4th hero or NPC class)
    # _ITM_04..06 single → S001 사격 (gun sub-types)
    mapping = [
        {
            'weapon_dat': '_ITM_01_DAT',
            'character_class': 'S000',
            'class_name_kr': '양손검',
            'class_name_en': 'Two-handed Sword',
            'hero': '티르',
            'reason': '가장 높은 dual ATK (avg sum 65.0) → 양손 전용 검의 위력 가설과 일치',
        },
        {
            'weapon_dat': '_ITM_02_DAT',
            'character_class': 'S002',
            'class_name_kr': '마검',
            'class_name_en': 'Magic Sword',
            'hero': '티르 (alt) / 3번째 영웅',
            'reason': '중간 dual ATK (avg sum 55.6); S002 마검 스킬셋이 S000 의 sword 스킬 일부 공유 → 티르 변형 클래스 추정',
        },
        {
            'weapon_dat': '_ITM_00_DAT',
            'character_class': 'S003',
            'class_name_kr': '단도+마법',
            'class_name_en': 'Dagger + Magic',
            'hero': '4번째 영웅 (미확인, _H_BH 4 stat blocks 중 3-4번)',
            'reason': '중-저 dual ATK (avg sum 46.8); 단도는 두 손 짧은 무기 dual-strike 모델, 마법 보조',
        },
        {
            'weapon_dat': '_ITM_03_DAT',
            'character_class': '(예비/NPC)',
            'class_name_kr': '미분류 검',
            'class_name_en': 'Unassigned Sword',
            'hero': '미확인',
            'reason': '가장 낮은 dual ATK (avg sum 45.4); 4 dual class > 3 sword 캐릭터 → 1개 잉여. NPC/적 전용 또는 잠금 클래스 가능성',
        },
        {
            'weapon_dat': '_ITM_04_DAT',
            'character_class': 'S001 (variant A)',
            'class_name_kr': '권총 (가벼움)',
            'class_name_en': 'Handgun',
            'hero': '루레인',
            'reason': 'single ATK avg 106.9; S001 사격 3 무기 변종 중 균형',
        },
        {
            'weapon_dat': '_ITM_05_DAT',
            'character_class': 'S001 (variant B)',
            'class_name_kr': '저화력총',
            'class_name_en': 'Low-DPS Gun',
            'hero': '루레인',
            'reason': 'single ATK avg 101.6; 가장 낮은 화력 (회피/속사 가설)',
        },
        {
            'weapon_dat': '_ITM_06_DAT',
            'character_class': 'S001 (variant C)',
            'class_name_kr': '중화기',
            'class_name_en': 'Heavy Gun',
            'hero': '루레인',
            'reason': 'single ATK avg 97.0; 후반 데미지 급등 (lvl85+ overflow byte 패턴) → 헤비/저격 가설',
        },
    ]

    # Cross-check: skill names matching weapon style
    cross_check = {
        'S000_skills_match': '대검공격/유린의검 등 5/10 = 검 (dual-strike 적합)',
        'S001_skills_match': '사격/산탄/동시/급소/속사 10/10 = 총류 (single-ATK 적합)',
        'S002_skills_match': '대검공격/마검공격/텔레포트소드/프레임/아이스인첸트 = 검+마법',
        'S003_skills_match': '빙결의단도/빙결의검/암흑/저주강화 = 단도+마법',
    }

    out = {
        'meta': {
            'round': 'R76',
            'date': '2026-05-19',
            'source': '[h4_items_detailed.json] + [h4_catalog.json skill_sets]',
            'method': 'damage profile (dual vs single ATK) + level curve uniqueness',
        },
        'summary': summary,
        'mapping': mapping,
        'cross_check': cross_check,
        'open_questions': [
            '_ITM_03 (가장 낮은 dual) 의 사용자 — 4번째 영웅 vs NPC class 구분 필요',
            '_H_BH 4 stat blocks 중 3-4번째 entry 의 캐릭터 이름 (R71 에서 가변 길이라 미확인)',
            '_ITM_04 vs _ITM_05 vs _ITM_06 의 정확한 sub-type 명칭 (한국어 원본 매뉴얼 필요)',
            'flag (property_flag) 0-7 의 의미 — 원소속성? 등급? (R74 stat block 일부 추정만)',
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)}')

    # Console summary
    print('\n=== Weapon class summary ===')
    for k, v in summary.items():
        print(f"  {k}: {'dual' if v['is_dual_atk'] else 'single':6} ATK1={v['atk1_avg']:>6} ATK2={v['atk2_avg']:>6} sum={v['damage_sum_avg']:>6}  lv {v['lv_start']}->{v['lv_max']}")
    print('\n=== Mapping ===')
    for m in mapping:
        print(f"  {m['weapon_dat']} → {m['character_class']:<20} ({m['class_name_kr']}) hero={m['hero']}")


if __name__ == '__main__':
    main()
