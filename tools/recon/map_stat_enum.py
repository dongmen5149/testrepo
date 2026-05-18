"""Round 63: stat enum 통합 매핑 — i13 effect_type → i12 ring / equip trailer 매칭.

R62 에서 trailer 8개 미식별 type code 발견 (0x01/0x03/0x04/0x08/0x09/0x0b/0x10/0x11).
R63 발견: **i13 effect_type 의 high byte = master stat enum** (low byte = target).

i13 의 desc 텍스트를 통해 high_byte 의미가 직접 확인됨:

  0x01 = 즉시 HP 회복 (자비의손길)
  0x02 = HP 최대치 (오우거의의지 / 드래곤피어[적])
  0x03 = HP 회복량 (regen 속도, 승리의염원)
  0x04 = SP 회복/최대치 (잠재의식)
  0x05 = 물리공격력 (끓어오르는피)
  0x06 = 특수공격력 (악마의속삼임 = 마법/총기)
  0x07 = 물리방어력 (철벽의가드 / 사막의폭염[적])
  0x08 = 특수방어력 (오로라의장벽 / 머메이드의노래[적])  ← R62 ?08 = M.DEF ★
  0x09 = 명중률 (사냥꾼의눈 / 아레스의구름[적])  ← R62 ?09 = ACC ★
  0x0a = 회피율 (시간의지배자 / 결박하는대지[적])
  0x0b = 방패방어율 (용자의가호)  ← R62 ?0b = BLOCK ★
  0x10 = HP 흡수 (i16 흡혈의)  ← R62 ?10 = HP_DRAIN ★
  0x11 = 쿨타임 감소 (질풍노도)  ← R62 ?11 = CD_REDUCE ★
  0x16 = 능력치증가 해제 (망각의향)
  0x17 = 상태이상 회복 (혼의외침)
  0x1c = 전투불능 회복 (피닉스의숨결)

**R61 의 ring bonus_type 매핑 재해석**: 0x05=STR/0x06=INT/0x07=VIT/0x0a=AGI 는
UI 라벨이고 실제 의미는 ATT1/ATT2/PDEF/DOD (i13 와 같은 enum 사용).
링 이름의 "힘/정신/체력/민첩" 은 player-facing 명칭, internal stat 은 derived.

**여전히 미확정 (i13 에 등장 안 함)**:
  0x01 trailer 에 2회 (희귀, EXP/LV bonus 가설)
  0x0c, 0x0d (R61 가설 = P.DEF/M.DEF 였으나 i13 는 0x07/0x08 사용 → 재해석 필요)
  0x0e, 0x0f (R61 가설 = HIT/EVA 였으나 i13 는 0x09/0x0a 사용 → 재해석 필요)
  0x12 (R61 = ATK, i12 ring "맹공/공작깃털/샤프니스" = ATT1 flat bonus 추정)
  0x14, 0x19 (드물게 등장, 가설 검증 필요)

**가설** (i13 미커버 코드들 — InGame_txt 의 CRI/RES + STR/INT/VIT/AGI primary 추정):
  0x0c = CRI (크리티컬 발생율)
  0x0d = RES (저항)
  0x0e = STR primary (UI 표시 "힘" 직접)
  0x0f = INT primary (UI 표시 "정신" 직접)
  0x12 = ATT1 flat (i13 0x05 = ratio, ring 0x12 = flat)
  0x14, 0x19 = ?

출력: work/h3/recon/stat_enum.{json,log}
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# Master stat enum (R63 최종 — i16 enchant 가 같은 enum 사용 확정으로 모든 코드 매핑 완료)
STAT_ENUM = {
    0x00: {"name": "ATT1_BASE",        "from": "i16 뇌제의 = 무기 공격력 강화", "desc": "기본 ATT1 (i16 enchant 만 사용)"},
    0x01: {"name": "HP_HEAL_INSTANT",  "from": "i13 자비의손길", "desc": "사용자 HP 즉시 회복"},
    0x02: {"name": "HP_MAX",           "from": "i13/i12/i16 + trailer", "desc": "HP 최대치"},
    0x03: {"name": "HP_REGEN",         "from": "i13 승리의염원 + i16 공명의 + ring 회복의반지", "desc": "HP 자동 회복 (regen per turn)"},
    0x04: {"name": "SP_MAX",           "from": "i13 잠재의식 + ring 데몬의뿔", "desc": "SP 최대치/회복"},
    0x05: {"name": "ATT1",             "from": "i13 끓어오르는피 + ring 힘의반지", "desc": "물리공격력 (UI 라벨: 힘)"},
    0x06: {"name": "ATT2",             "from": "i13 악마의속삼임 + ring 정신의반지", "desc": "특수공격력 마법/총기 (UI: 정신)"},
    0x07: {"name": "P_DEF",            "from": "i13 철벽의가드 + i16 금강의 + ring 체력의반지", "desc": "물리방어력 (UI: 체력)"},
    0x08: {"name": "M_DEF",            "from": "i13 오로라의장벽 + i16 정령의 + ring 히드라/배리어", "desc": "특수방어력 (마법/총기)"},
    0x09: {"name": "ACC",              "from": "i13 사냥꾼의눈 + i16 사신의 + ring 콘돌/백발백중", "desc": "명중률"},
    0x0a: {"name": "DOD",              "from": "i13 시간의지배자 + i16 영제의 + ring 민첩의반지", "desc": "회피율 (UI 라벨: 민첩)"},
    0x0b: {"name": "BLOCK",            "from": "i13 용자의가호 + i16 철벽의 + ring 기사/프로텍트", "desc": "방패방어율"},
    0x0c: {"name": "CRI_RATE",         "from": "i16 속박의 = 크리티컬 발생 확률 증가", "desc": "크리티컬 발생율 (R61 P.DEF 가설 폐기)"},
    0x0d: {"name": "CRI_DEF",          "from": "i16 결의의 = 크리티컬 공격 맞을 확률 감소", "desc": "크리피해 감소 (R61 M.DEF 가설 폐기)"},
    0x0e: {"name": "SP_COST_REDUCE",   "from": "i16 현자의 = 스킬사용 SP 감소 + ring 총명의반지", "desc": "스킬 SP 소모 감소 (R61 HIT 가설 폐기)"},
    0x0f: {"name": "SP_REGEN",         "from": "i16 마도의 = SP 회복속도 증가 + ring 지혜의반지", "desc": "SP 회복속도 (R61 EVA 가설 폐기)"},
    0x10: {"name": "HP_DRAIN",         "from": "i16 흡혈의 + ring 카오스/데몬", "desc": "공격시 HP 흡수"},
    0x11: {"name": "CD_REDUCE",        "from": "i13 질풍노도 + i16 폭풍의 + ring 헤이스트/자칼", "desc": "스킬 쿨타임 감소"},
    0x12: {"name": "SHIELD_PIERCE",    "from": "i16 직격의 = 방패 무시 확률 증가 + ring 맹공/샤프니스", "desc": "방패 무시 (R61 ATK 가설 정정)"},
    0x14: {"name": "?",                "from": "(rare)", "desc": "미식별 (0회 출현 in 검색)"},
    0x16: {"name": "BUFF_REMOVE",      "from": "i13 망각의향", "desc": "능력치 증가 해제"},
    0x17: {"name": "CURE_STATUS",      "from": "i13 혼의외침", "desc": "상태이상 회복"},
    0x19: {"name": "?",                "from": "(rare)", "desc": "미식별"},
    0x1c: {"name": "REVIVE",           "from": "i13 피닉스의숨결", "desc": "전투불능 회복"},
}


def main() -> None:
    item_json = Path("work/h3/recon/item_decoded.json")
    out_dir = Path("work/h3/recon")
    d = json.loads(item_json.read_text(encoding="utf-8"))

    print("=" * 78)
    print("Round 63 — Master stat enum 통합 매핑")
    print("=" * 78)

    # i13 effect_type high byte ↔ desc 검증
    print("\n--- i13 effect_type → master stat enum (검증) ---")
    i13 = d.get("i13_dat", {}).get("items", [])
    by_high = defaultdict(list)
    for it in i13:
        et = it.get("effect_type", "0x0000")
        if et.startswith("0x"):
            v = int(et, 16)
            high = (v >> 8) & 0xff
            low = v & 0xff
            by_high[high].append({
                "name": it["name"], "low": low,
                "value": it.get("effect_value", 0),
                "desc": it.get("desc", "")[:60],
            })

    for high in sorted(by_high):
        items = by_high[high]
        info = STAT_ENUM.get(high, {"name": "?", "desc": "(not mapped)"})
        print(f"\n  0x{high:02x} = {info['name']:<14} | {info['desc']}")
        for it in items[:3]:
            tag = "[적]" if it["low"] == 0x01 else "[사용자]" if it["low"] == 0x02 else f"[low=0x{it['low']:02x}]"
            print(f"     {tag:<10} {it['name']:<20} val={it['value']:>5}  {it['desc']!r}")
        if len(items) > 3:
            print(f"     ... ({len(items)-3} more)")

    # i12 ring bonus_type → master enum verification
    print("\n\n--- i12 ring bonus_type → master stat enum (cross-check) ---")
    i12 = d.get("i12_dat", {}).get("items", [])
    ring_by_type = defaultdict(list)
    for it in i12:
        bt = it.get("bonus_type", -1)
        if bt >= 0:
            ring_by_type[bt].append((it["name"], it.get("bonus_value", 0)))
    for bt in sorted(ring_by_type):
        info = STAT_ENUM.get(bt, {"name": "?", "desc": "(unmapped)"})
        names = [f"{n}+{v}" for n, v in ring_by_type[bt][:4]]
        print(f"  0x{bt:02x} → {info['name']:<14} | {names}")

    # equip trailer bonus_type distribution
    print("\n\n--- equip trailer bonus_type → master stat enum (R62 cross-check) ---")
    iv = json.loads((out_dir / "item_variants.json").read_text(encoding="utf-8"))
    cats = iv.get("categories", {})
    trailer_count = Counter()
    trailer_examples = defaultdict(list)
    for fn, cat in cats.items():
        for it in cat.get("items_with_bonus", []):
            tr = it.get("trailer", {})
            for k in ("b1", "b2"):
                if k in tr:
                    bt = tr[k]["type"]
                    trailer_count[bt] += 1
                    if len(trailer_examples[bt]) < 4:
                        trailer_examples[bt].append(f"{it['name']}+{tr[k]['value']}")
    for bt in sorted(trailer_count):
        info = STAT_ENUM.get(bt, {"name": "?", "desc": "(unmapped)"})
        print(f"  0x{bt:02x} → {info['name']:<14} ({trailer_count[bt]:>3}x) | {trailer_examples[bt]}")

    # i16 enchant uses a DIFFERENT enum — list separately
    print("\n\n--- i16 enchant tail[0] (★ 별도 enum, 0x00-0x12 sequential) ---")
    i16 = d.get("i16_dat", {}).get("items", [])
    for it in i16:
        tail_hex = it.get("tail", "")
        if not tail_hex:
            continue
        tb = int(tail_hex.split()[0], 16) if tail_hex else 0
        desc = it.get("desc", "")[:55]
        print(f"  0x{tb:02x} {it['name']:<10} | {desc}")

    # SAVE
    out = {
        "stat_enum_master": {f"0x{k:02x}": v for k, v in STAT_ENUM.items()},
        "i13_effect_high_byte_distribution": {f"0x{k:02x}": [
            {"name": it["name"], "desc": it["desc"]} for it in v
        ] for k, v in by_high.items()},
        "i12_ring_bonus_type_distribution": {f"0x{k:02x}": v for k, v in ring_by_type.items()},
        "equip_trailer_bonus_type_count": {f"0x{k:02x}": c for k, c in trailer_count.items()},
    }
    (out_dir / "stat_enum.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n\nDumped: {out_dir / 'stat_enum.json'}")


if __name__ == "__main__":
    main()
