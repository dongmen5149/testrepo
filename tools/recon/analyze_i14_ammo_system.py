"""Round 69: i14 조합 재료의 권총/라이플 ammo 시스템 연관 분석.

R68 발견: s7 (피스톨) 만 unique flag pair (0x14 weapon_passive + 0x1f active_attack).
R69 검증: i14 (조합 재료) 의 "탄성제" = "권총/라이플의 조합에 사용" — 동일 카테고리.

결론:
  R68 가설 ("s7 별도 ammo 시스템") 부분 수정 필요:
    - 탄성제 = 권총 (s7) + 라이플 (s8) 공통 재료
    - ammo 시스템 자체는 두 무기 공유
    - 0x1f marker (s7 active) vs 0x01 (s8 active) = 사거리/조준 모드 차이 표시
      → 단발 권총 = 빠른 사격 / 다중 타겟 (난사)
      → 연발 라이플 = 정확 사격 / 관통 (직격/연쇄/위협)

i14 조합 재료 7 카테고리:
  1. 공통 용액 (3): 붉은/푸른/투명
  2. 공정 재료 (5): 제련석/연마가루/정령석/탄성제/강화제
  3. 무기-class 별 재료 (i4-i10 매핑):
     - 연마가루 → s4 (창), s5 (대검), s6 (단검)
     - 정령석   → s9 (다크석), s10 (홀리석)
     - 탄성제   → s7 (피스톨), s8 (라이플) ★ 공통
     - 질긴섬유 → 방어구 (i0-i3, i11)
     - 강화제   → 방어구 보강
  4. 원소 속성 (4): 바람피리/만년설/혈목/흑암석
  5. 몬스터 드롭 (12): 쥐가죽/박쥐날개 등
  6. 고대 재료 3 tier × 4 type (12):
     - 투구/갑옷: 에스텔시아/카메루시아/헤게네시아 (금속)
     - 장갑/신발: 그리톤/시르톤/아케톤 (가죽)
     - 물리무기/방패: 아르세네스/뮤제게네스/바스테네스 (제련석)
     - 스톤/총기: 데비그린/오헨그린/큐브그린 (정령석) ★ 마법석+총기 공유
  7. 클래스 강화 문장 (5):
     - 아벨=전사, 시몬=총기, 포프=마법, 부폰=방어, 하피=회피

신규 통찰:
  - "스톤/총기" (고대 정령석) = 다크석/홀리석 + 권총/라이플 = 4 weapon class 공유
  - 시몬의문장 = 총기 전용 강화 문장 (s7 + s8 모두)
  - R62 boss drop 의 ATT2 분포와 일치 (시몬 = 총기 = ATT2 특공)

Output: work/h3/recon/i14_ammo_system.{json,log}
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


# i14 분류 (R69)
I14_CATEGORIES = {
    "공통_용액": ["붉은용액", "푸른용액", "투명용액"],
    "공정_재료": ["제련석", "연마가루", "정령석", "탄성제", "강화제", "질긴섬유"],
    "원소_속성": ["바람피리", "만년설", "혈목", "흑암석"],
    "몬스터_드롭": ["뼛조각", "잔나뭇가지", "홀리파우더", "쥐가죽", "그을린가죽",
                     "분홍잔털", "쥐발톱", "박쥐의날개", "라이칸의이빨", "솔티안의 문장",
                     "데몬의뿔", "코르버스의문장", "라이칸의칼날", "라이트닝파우더",
                     "에인션트하니"],
    "고대_재료_t1": ["에스텔시아", "그리톤", "아르세네스", "데비그린"],
    "고대_재료_t2": ["카메루시아", "시르톤", "뮤제게네스", "오헨그린"],
    "고대_재료_t3": ["헤게네시아", "아케톤", "바스테네스", "큐브그린"],
    "클래스_문장": ["아벨의문장", "시몬의문장", "포프의문장", "부폰의문장", "하피의문장"],
}

# 무기-class → 조합재료 매핑
WEAPON_CRAFTING = {
    "창 (s4)":      ["연마가루", "아르세네스/뮤제게네스/바스테네스", "아벨의문장"],
    "대검 (s5)":    ["연마가루", "아르세네스/뮤제게네스/바스테네스", "아벨의문장"],
    "단검 (s6)":    ["연마가루", "아르세네스/뮤제게네스/바스테네스", "아벨의문장"],
    "권총 (s7)":    ["탄성제",   "데비그린/오헨그린/큐브그린",         "시몬의문장"],
    "라이플 (s8)":  ["탄성제",   "데비그린/오헨그린/큐브그린",         "시몬의문장"],
    "다크석 (s9)":  ["정령석",   "데비그린/오헨그린/큐브그린",         "포프의문장"],
    "홀리석 (s10)": ["정령석",   "데비그린/오헨그린/큐브그린",         "포프의문장"],
}


def main() -> None:
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))

    i14_items = [it.get("name", "") for it in d["i14_dat"]["items"]]

    # categorize observed i14 items
    categorized: dict = defaultdict(list)
    uncategorized: list = []
    for nm in i14_items:
        found = False
        for cat, names in I14_CATEGORIES.items():
            if nm in names:
                categorized[cat].append(nm)
                found = True
                break
        if not found:
            uncategorized.append(nm)

    out = {
        "doc": "Round 69: i14 조합 재료 권총/라이플 ammo 시스템 연관 분석",
        "i14_total_count": len(i14_items),
        "categorization": dict(categorized),
        "uncategorized": uncategorized,
        "weapon_crafting_map": WEAPON_CRAFTING,
        "key_insights": [
            "탄성제 = 권총 (s7) + 라이플 (s8) 공통 재료 → ammo 시스템 동일",
            "0x1f marker (s7) vs 0x01 (s8) = 사거리/조준 모드 차이 표시",
            "  - 단발 권총: 빠른 사격 / 다중 타겟 (난사)",
            "  - 연발 라이플: 정확 사격 / 관통 (직격/연쇄/위협)",
            "스톤/총기 고대 정령석 = 다크석/홀리석 + 권총/라이플 4 class 공유",
            "시몬의문장 = 총기 전용 강화 (s7+s8 모두)",
            "R62 boss drop ATT2 분포와 일치 — 시몬 = 총기 = ATT2 (특공)",
        ],
        "r68_hypothesis_revision": {
            "original": "s7 = 별도 hit/ammo 시스템",
            "revised":  "s7+s8 공통 ammo 시스템, 0x1f marker = 사거리/조준 모드 차이만",
            "evidence": "i14 탄성제 = '권총/라이플의 조합에 사용' (동일 카테고리)",
        },
    }

    out_path = RECON / "i14_ammo_system.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 i14 조합 재료 ammo 시스템 분석 (R69) =====\n")
    log_lines.append(f"i14 total: {len(i14_items)} items\n")

    log_lines.append("[Categorization]")
    for cat, items in categorized.items():
        log_lines.append(f"\n  {cat} ({len(items)}):")
        for nm in items:
            log_lines.append(f"    - {nm}")

    if uncategorized:
        log_lines.append(f"\n[Uncategorized ({len(uncategorized)})]")
        for nm in uncategorized:
            log_lines.append(f"  - {nm}")

    log_lines.append("\n[Weapon-class crafting map]")
    for wc, mats in WEAPON_CRAFTING.items():
        log_lines.append(f"  {wc}: {mats}")

    log_lines.append("\n[Key insights]")
    for ins in out["key_insights"]:
        log_lines.append(f"  - {ins}")

    log_lines.append("\n[R68 Hypothesis Revision]")
    rev = out["r68_hypothesis_revision"]
    log_lines.append(f"  Original: {rev['original']}")
    log_lines.append(f"  Revised:  {rev['revised']}")
    log_lines.append(f"  Evidence: {rev['evidence']}")

    log_path = RECON / "i14_ammo_system.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Key insights ---")
    for ins in out["key_insights"]:
        print(f"  - {ins}")


if __name__ == "__main__":
    main()
