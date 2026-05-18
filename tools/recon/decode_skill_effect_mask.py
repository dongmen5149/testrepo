"""Round 65: skill +0x10..+0x1d 의 effect mask 디코드.

R64 발견: ultimate skill 의 +0x14..+0x1c 영역이 0, normal active 는 0xff/0xfe 다수.

R65 정밀 분석 결과:

  +0x10..+0x11   LE16  primary damage scale  (저격 0x14=20 highest)
  +0x12          byte  pad (00)
  +0x13          byte  1차 debuff code (0x7f sentinel = "no debuff")
  +0x14..+0x17   LE32 signed  1차 debuff value (음수면 디버프, 0 = no effect)
  +0x18          byte  2차 debuff code (0x7f = no second debuff)
  +0x19..+0x1c   LE32 signed  2차 debuff value
  +0x1d          byte  rank / power class (R63)

핵심:
  - ultimate skill 은 primary debuff만 사용 (1차/2차 = 0x7f sentinel)
  - normal active 중 일부 (압도/유도/저격/참혼/암영/망각/전율/위협/격광/직격) 는 debuff 보유
  - 디버프 value 는 signed int32 LE (음수 = 적 stat 감소)

debuff_code 매핑 (관찰):
  0x03 = ?? (압도 "공격을 늦춘다", value=-10,-3)
  0x06 = ATT2_debuff (망각, 0x06 = ATT2 코드)
  0x08 = M_DEF_debuff (전율, 0x08 = M_DEF)
  0x09 = ACC_debuff (격광, 0x09 = ACC)
  0x0a = DOD_debuff (전율 2차)
  0x15 = ?? (유도 "공격 집중시킨다" = taunt, value=21)
  0x1c = REVIVE 가설은 잘못 — 실제 = stun? (참혼 "기절시킨다" + 저격, value=28)
  0x0d = ?? (위협)

스크립트 출력: work/h3/recon/effect_mask.{json,log}
"""
import json
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"

STAT_NAME = {
    0x00: "ATT1_BASE", 0x01: "HP_HEAL_INSTANT", 0x02: "HP_MAX", 0x03: "HP_REGEN",
    0x04: "SP_MAX", 0x05: "ATT1", 0x06: "ATT2", 0x07: "P_DEF", 0x08: "M_DEF",
    0x09: "ACC", 0x0a: "DOD", 0x0b: "BLOCK", 0x0c: "CRI_RATE", 0x0d: "CRI_DEF",
    0x0e: "SP_COST_REDUCE", 0x0f: "SP_REGEN", 0x10: "HP_DRAIN", 0x11: "CD_REDUCE",
    0x12: "SHIELD_PIERCE", 0x15: "TAUNT (R65 신규 가설)", 0x16: "BUFF_REMOVE",
    0x17: "CURE_STATUS", 0x1c: "STUN_TRIGGER (R65 정정, R63 REVIVE 아님)",
    0x7f: "(sentinel, no debuff)",
}


def decode_tail(tail_hex: str) -> dict:
    b = [int(x, 16) for x in tail_hex.split()]
    if len(b) < 30:
        return {"raw": tail_hex}
    raw = bytes(b)
    return {
        "off_10_11_primary_dmg":     struct.unpack_from("<H", raw, 0x10)[0],
        "off_12_pad":                b[0x12],
        "off_13_debuff1_code":       b[0x13],
        "off_14_17_debuff1_value":   struct.unpack_from("<i", raw, 0x14)[0],
        "off_18_debuff2_code":       b[0x18],
        "off_19_1c_debuff2_value":   struct.unpack_from("<i", raw, 0x19)[0],
        "off_1d_rank":               b[0x1d],
    }


def main() -> None:
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    results: list[dict] = []
    debuff1_codes: Counter = Counter()
    debuff2_codes: Counter = Counter()

    for fn, skills in d.items():
        for s in skills:
            if s.get("category_name") != "active_attack":
                continue
            decoded = decode_tail(s.get("tail_hex", ""))
            entry = {
                "file": fn,
                "name": s["name"],
                "rank": s.get("rank_or_level", 0),
                "desc": (s.get("desc", "") or "")[:60],
                **decoded,
            }
            results.append(entry)
            d1 = decoded.get("off_13_debuff1_code", 0)
            d2 = decoded.get("off_18_debuff2_code", 0)
            if d1 != 0x7f:
                debuff1_codes[d1] += 1
            if d2 != 0x7f:
                debuff2_codes[d2] += 1

    out = {
        "doc": "Round 65: skill +0x10..+0x1d effect mask 디코드",
        "schema": {
            "+0x10..+0x11": "LE16 primary damage scale",
            "+0x12":         "pad (00)",
            "+0x13":         "1차 debuff code (0x7f = sentinel = no debuff)",
            "+0x14..+0x17":  "LE32 signed 1차 debuff value (음수 = 적 stat 감소)",
            "+0x18":         "2차 debuff code",
            "+0x19..+0x1c":  "LE32 signed 2차 debuff value",
            "+0x1d":         "rank / power class (R63)",
        },
        "active_attack_skills": results,
        "debuff1_code_freq": {f"0x{k:02x} ({STAT_NAME.get(k,'?')})": v for k, v in debuff1_codes.most_common()},
        "debuff2_code_freq": {f"0x{k:02x} ({STAT_NAME.get(k,'?')})": v for k, v in debuff2_codes.most_common()},
    }

    out_path = RECON / "effect_mask.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 skill +0x10..+0x1d effect mask (R65) =====\n")
    log_lines.append("[Schema]")
    for k, v in out["schema"].items():
        log_lines.append(f"  {k:<14} {v}")

    log_lines.append(f"\n[All active_attack skills ({len(results)})]")
    log_lines.append(f"  {'file':<8} {'name':<14} r {'pri_dmg':>8} d1   d1_val   d2   d2_val")
    for e in results:
        d1c = e["off_13_debuff1_code"]
        d2c = e["off_18_debuff2_code"]
        d1_label = f"0x{d1c:02x}" if d1c != 0x7f else "  ."
        d2_label = f"0x{d2c:02x}" if d2c != 0x7f else "  ."
        log_lines.append(f"  {e['file']:<8} {e['name']:<14} {e['rank']:>2} "
                         f"{e['off_10_11_primary_dmg']:>8} "
                         f"{d1_label:>5} {e['off_14_17_debuff1_value']:>8} "
                         f"{d2_label:>5} {e['off_19_1c_debuff2_value']:>8}   "
                         f"{e['desc'][:30]}")

    log_lines.append(f"\n[1차 debuff code freq (excluding 0x7f sentinel)]")
    for k, v in debuff1_codes.most_common():
        log_lines.append(f"  0x{k:02x} ({STAT_NAME.get(k,'?'):<20}) = {v}")

    log_lines.append(f"\n[2차 debuff code freq (excluding 0x7f sentinel)]")
    for k, v in debuff2_codes.most_common():
        log_lines.append(f"  0x{k:02x} ({STAT_NAME.get(k,'?'):<20}) = {v}")

    # Skill-specific mapping (debuff_code → korean desc keyword)
    log_lines.append(f"\n[★ Skill debuff_code → desc mapping]")
    seen = set()
    for e in results:
        d1 = e["off_13_debuff1_code"]
        if d1 == 0x7f or d1 == 0:
            continue
        key = (d1, e["name"])
        if key in seen:
            continue
        seen.add(key)
        log_lines.append(f"  0x{d1:02x} (val={e['off_14_17_debuff1_value']:>5})  '{e['name']}' — {e['desc']}")

    log_path = RECON / "effect_mask.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print(f"\n--- Findings ---")
    print(f"  Active_attack skills: {len(results)}")
    print(f"  Debuff1 codes used:   {list(f'0x{k:02x}' for k in debuff1_codes)}")
    print(f"  Debuff2 codes used:   {list(f'0x{k:02x}' for k in debuff2_codes)}")


if __name__ == "__main__":
    main()
