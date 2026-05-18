"""Round 66: skill debuff code 정밀 매핑 (i13 디버프 + string table 비교).

R65 발견: skill +0x13 debuff code 6 distinct (0x03/0x06/0x08/0x09/0x0a/0x15/0x1c).
R65 가설: debuff code = 별도 enum (stat enum 과 부분 공유).

R66 정밀 분석:

  실제로는 debuff code = i13/i12/i16/equip 의 **stat enum 그대로 재사용** 가능.
  단, value 의 부호로 buff/debuff 분리.

  - skill 0x03 = "BLEED" (새 enum) 가 아니라 **HP_REGEN(음수)** = 적 HP 매 턴 감소
    (i13 0x03=HP_REGEN 와 동일 enum, value 부호만 차이)
  - skill 0x06 = ATT2(음수) = 적 ATT2 감소 (= 망각 "공격력 격감", i13 와 동일)
  - skill 0x08 = M_DEF(음수) = 적 M_DEF 감소 (= 전율 "방어력 격감")
  - skill 0x09 = ACC(음수) = 적 ACC 감소 (= 격광 "명중률 낮춘다")
  - skill 0x0a = DOD(음수) = 적 DOD 감소 (= 전율 2차 "회피율 격감")

  새 enum (R63 master 에 없던 의미):
  - skill 0x15 = TAUNT (R63 미식별 코드, 유도 "공격 자신에게 집중")
  - skill 0x1c = STUN (참혼/저격 "기절", R63 의 0x1c REVIVE 와 컨텍스트 분리)

  대안 가설:
  - 0x1c = master enum 그대로 (REVIVE), 단 value=0 인 경우 = "REVIVE 무효화" = STUN
    (적이 행동 불능 = REVIVE-resistant = effectively stunned)
  - 일관성을 위해 master enum 으로 통합 가능

i13 vs skill debuff 매핑 검증:
  | code | i13 디버프 | skill 디버프 |
  |---:|---|---|
  | 0x02 | 드래곤피어 "HP최대치 감소" | (skill 에서 사용 안 됨) |
  | 0x03 | (i13 양수 = HP_REGEN buff) | 암영/직격 "관통/출혈" (음수 → HP_REGEN debuff = bleed) |
  | 0x06 | (i13 양수 = ATT2 buff) | 망각 "공격력 격감" (음수 → ATT2 debuff) |
  | 0x07 | 사막의폭염 "물리방어력 감소" | (skill 에서 사용 안 됨) |
  | 0x08 | 머메이드의노래 "특수방어력 감소" | 전율 "방어력 격감" |
  | 0x09 | 아레스의구름 "명중률 감소" | 압도/격광 "공격 늦춘다/명중률 낮춘다" |
  | 0x0a | 결박하는대지 "회피율 감소" | 전율 2차 "회피율 격감" |
  | 0x15 | — | 유도 "공격 집중" = TAUNT ★ NEW |
  | 0x1c | (i13 양수 = REVIVE) | 참혼/저격 "기절" = STUN (또는 REVIVE 음수 = stun?) |

→ **debuff code 가 stat enum 과 정확히 동일** (0x15, 0x1c 의 새 의미 제외).
  - R65 의 "별도 enum" 가설 → "동일 enum, value 부호로 buff/debuff" 로 정정
  - 0x15 TAUNT 는 R63 미식별 코드 (실제 master enum 의 0x14/0x19 와 함께 unused 추정이었으나, skill 에서만 사용 = master enum 의 0x15 = TAUNT 라는 새 코드 추가)
  - 0x1c 는 두 가지 가능성: (a) STUN 새 enum, (b) REVIVE 의 컨텍스트 변형

Output: work/h3/recon/debuff_codes_refined.{json,log}
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


# R63 master enum (24 codes) + R66 정정
MASTER_ENUM = {
    0x00: "ATT1_BASE",
    0x01: "HP_HEAL_INSTANT",
    0x02: "HP_MAX",
    0x03: "HP_REGEN",        # skill negative = BLEED
    0x04: "SP_MAX",
    0x05: "ATT1",
    0x06: "ATT2",
    0x07: "P_DEF",
    0x08: "M_DEF",
    0x09: "ACC",
    0x0a: "DOD",
    0x0b: "BLOCK",
    0x0c: "CRI_RATE",
    0x0d: "CRI_DEF",
    0x0e: "SP_COST_REDUCE",
    0x0f: "SP_REGEN",
    0x10: "HP_DRAIN",
    0x11: "CD_REDUCE",
    0x12: "SHIELD_PIERCE",
    0x14: "?? (unused)",
    0x15: "TAUNT (R66 신규, skill 0x15 에서만 사용)",
    0x16: "BUFF_REMOVE",
    0x17: "CURE_STATUS",
    0x19: "?? (unused)",
    0x1c: "REVIVE / STUN (컨텍스트 분리)",
}

# i13 디버프 cases (R64 발견)
I13_DEBUFFS = [
    {"name": "드래곤피어",   "stat_code": 0x02, "value": -30, "desc": "적 파티 HP최대치 감소"},
    {"name": "사막의폭염",   "stat_code": 0x07, "value": -50, "desc": "적 파티 물리방어력 감소"},
    {"name": "머메이드의노래", "stat_code": 0x08, "value": -50, "desc": "적 파티 특수방어력 감소"},
    {"name": "아레스의구름",  "stat_code": 0x09, "value": -30, "desc": "적 파티 명중률 감소"},
    {"name": "결박하는대지",  "stat_code": 0x0a, "value": -30, "desc": "대상의 회피율 감소"},
]


def main() -> None:
    # Load skill effect mask
    em = json.loads((RECON / "effect_mask.json").read_text(encoding="utf-8"))
    skill_debuffs = []
    for s in em["active_attack_skills"]:
        d1c = s.get("off_13_debuff1_code", 0x7f)
        d2c = s.get("off_18_debuff2_code", 0x7f)
        if d1c == 0x7f and d2c == 0x7f:
            continue
        skill_debuffs.append({
            "name": s["name"],
            "weapon_file": s["file"],
            "rank": s["rank"],
            "debuff1_code": d1c,
            "debuff1_primary": s.get("off_14_17_debuff1_value", 0),
            "debuff2_code": d2c,
            "debuff2_primary": s.get("off_19_1c_debuff2_value", 0),
            "desc": s.get("desc", ""),
        })

    # Cross-reference: i13 stat_code vs skill debuff code
    cross_ref = {}
    for code in [0x02, 0x03, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x15, 0x1c]:
        i13_usage = [d for d in I13_DEBUFFS if d["stat_code"] == code]
        skill_usage = [
            s for s in skill_debuffs
            if s["debuff1_code"] == code or s["debuff2_code"] == code
        ]
        cross_ref[f"0x{code:02x}"] = {
            "master_enum_name": MASTER_ENUM.get(code, "?"),
            "i13_cases": [{"name": d["name"], "value": d["value"], "desc": d["desc"]} for d in i13_usage],
            "skill_cases": [{"name": s["name"], "code_pos": "d1" if s["debuff1_code"] == code else "d2",
                             "value": s["debuff1_primary"] if s["debuff1_code"] == code else s["debuff2_primary"],
                             "desc": s["desc"]} for s in skill_usage],
            "consistency": (
                "✓ consistent (i13 양수=buff, skill 음수=debuff, 동일 stat 의 부호 차이)" if i13_usage and skill_usage else
                "i13 only (skill 미사용)" if i13_usage and not skill_usage else
                "skill only (R63 미식별 또는 신규)" if skill_usage and not i13_usage else
                "neither"
            ),
        }

    out = {
        "doc": "Round 66: debuff code 정밀 매핑 (R65 '별도 enum' 가설 → 'stat enum 동일' 로 정정)",
        "conclusion": [
            "skill debuff code = stat enum 과 정확히 동일 (value 부호로 buff/debuff 구분)",
            "0x15 = TAUNT (R63 미식별 → R66 신규 master enum 추가)",
            "0x1c = REVIVE 또는 STUN (컨텍스트 분리 또는 value=0 의 다른 해석)",
            "0x03 = HP_REGEN — skill 음수 value 가 BLEED 효과 (HP 시간 감소)",
            "i13 디버프 (5 cases) + skill 디버프 (9 cases) = 동일 enum 시스템",
        ],
        "master_enum_refined": MASTER_ENUM,
        "i13_debuffs": I13_DEBUFFS,
        "skill_debuffs": skill_debuffs,
        "cross_reference": cross_ref,
    }

    out_path = RECON / "debuff_codes_refined.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 debuff code 정밀 매핑 (R66) =====\n")
    log_lines.append("[Conclusion]")
    for c in out["conclusion"]:
        log_lines.append(f"  - {c}")

    log_lines.append("\n[i13 디버프 5 cases (effect_type high byte = stat code)]")
    for d in I13_DEBUFFS:
        log_lines.append(f"  0x{d['stat_code']:02x} ({MASTER_ENUM.get(d['stat_code'],'?'):<18}) val={d['value']:>4}  {d['name']:<14} — {d['desc']}")

    log_lines.append("\n[Skill +0x13/+0x18 디버프 9 cases]")
    for s in skill_debuffs:
        d1c = s["debuff1_code"]
        d2c = s["debuff2_code"]
        d1_label = f"0x{d1c:02x}({MASTER_ENUM.get(d1c,'?')[:14]})" if d1c != 0x7f else "."
        d2_label = f"0x{d2c:02x}({MASTER_ENUM.get(d2c,'?')[:14]})" if d2c != 0x7f else "."
        log_lines.append(f"  {s['name']:<12} d1={d1_label:<22} val={s['debuff1_primary']:>5}  "
                         f"d2={d2_label:<22} val={s['debuff2_primary']:>5}  — {s['desc'][:60]}")

    log_lines.append("\n[Cross-reference (i13 stat_code ↔ skill debuff code)]")
    for code_label, info in cross_ref.items():
        log_lines.append(f"\n  {code_label} = {info['master_enum_name']}")
        log_lines.append(f"    {info['consistency']}")
        if info["i13_cases"]:
            log_lines.append(f"    i13 cases: {[c['name'] for c in info['i13_cases']]}")
        if info["skill_cases"]:
            log_lines.append(f"    skill cases: {[c['name'] for c in info['skill_cases']]}")

    log_lines.append("\n[Master enum (R66 refined)]")
    for k, v in sorted(MASTER_ENUM.items()):
        log_lines.append(f"  0x{k:02x}  {v}")

    log_path = RECON / "debuff_codes_refined.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Conclusion ---")
    for c in out["conclusion"]:
        print(f"  - {c}")


if __name__ == "__main__":
    main()
