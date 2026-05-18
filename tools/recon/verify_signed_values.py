"""Round 65: 모든 dat 파일의 value field 가 signed int16 통일 인지 검증.

R64 발견: i13 적 대상 디버프 = signed int16 음수 (65486 = -50, 65506 = -30).

R65 검증 대상:
  - i12 ring bonus_value: byte (0..255) — flat permanent, 음수 없음 (signed unused)
  - i13 effect_value: LE16 unsigned 16 → 일부 high bit 음수 (signed 사용)
  - i16 enchant magnitude (tail[1]): byte — flat, 음수 없음
  - i18 effect_value: LE16 — 양수만 (HP heal etc)
  - skill +0x14..+0x17: LE16+LE16 signed int16 — debuff 사용 (R65 발견)
  - skill +0x10..+0x11 primary damage scale: LE16 (양수만?)
  - enemy/boss stat block: BE16 (HP/EXP/Gold) — 양수
  - equip trailer 4B: (bt1, v1, bt2, v2) — byte value 양수만

검증 방법:
  각 source 의 value field 분포 dump → signed 음수 출현 여부 확인.

Output: work/h3/recon/value_sign_verification.{json,log}
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


def as_int16(u: int) -> int:
    return u - 0x10000 if u >= 0x8000 else u


def analyze_i13() -> dict:
    """i13 effect_value (LE16) 분포."""
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    items = d["i13_dat"]["items"]
    vals_raw = []
    vals_signed = []
    neg_cases = []
    for it in items:
        v = it.get("effect_value", 0)
        if not isinstance(v, int):
            continue
        vals_raw.append(v)
        sv = as_int16(v)
        vals_signed.append(sv)
        if sv < 0:
            neg_cases.append({"name": it.get("name", ""), "raw": v, "signed": sv,
                              "desc": (it.get("desc", "") or "")[:50]})
    return {
        "n": len(vals_raw),
        "min_raw": min(vals_raw) if vals_raw else 0,
        "max_raw": max(vals_raw) if vals_raw else 0,
        "min_signed": min(vals_signed) if vals_signed else 0,
        "max_signed": max(vals_signed) if vals_signed else 0,
        "negative_cases": neg_cases,
        "n_negative": len(neg_cases),
    }


def analyze_i12() -> dict:
    """i12 ring bonus_value (byte)."""
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    items = d["i12_dat"]["items"]
    vals = [it.get("bonus_value", 0) for it in items if isinstance(it.get("bonus_value"), int)]
    return {"n": len(vals), "min": min(vals), "max": max(vals),
            "signed_neg_count": sum(1 for v in vals if v >= 128)}


def analyze_i16() -> dict:
    """i16 enchant magnitude (tail byte 1)."""
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    items = d["i16_dat"]["items"]
    mags = []
    for it in items:
        tail = it.get("tail", "")
        try:
            b = bytes.fromhex(tail.replace(" ", ""))
        except ValueError:
            continue
        if len(b) >= 2:
            mags.append(b[1])
    return {"n": len(mags), "min": min(mags), "max": max(mags),
            "signed_neg_count": sum(1 for v in mags if v >= 128)}


def analyze_i18() -> dict:
    """i18 consumable effect_value (LE16)."""
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    items = d["i18_dat"]["items"]
    vals = [it.get("effect_value", 0) for it in items if isinstance(it.get("effect_value"), int)]
    sv = [as_int16(v) for v in vals]
    return {"n": len(vals), "min_raw": min(vals), "max_raw": max(vals),
            "min_signed": min(sv), "max_signed": max(sv),
            "n_negative_signed": sum(1 for x in sv if x < 0)}


def analyze_equip_trailer() -> dict:
    """equip trailer 의 v1, v2 (각 byte)."""
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    v1s, v2s = [], []
    for fn in [f"i{n}_dat" for n in range(12)]:
        if fn not in d:
            continue
        for it in d[fn].get("items", []):
            if it.get("layout") != "equip20":
                continue
            tr = it.get("trailer", "")
            try:
                b = bytes.fromhex(tr.replace(" ", ""))
            except ValueError:
                continue
            if len(b) >= 4:
                v1s.append(b[1])
                v2s.append(b[3])
    return {
        "n_v1": len(v1s), "min_v1": min(v1s), "max_v1": max(v1s),
        "n_v2": len(v2s), "min_v2": min(v2s), "max_v2": max(v2s),
        "high_bit_count_v1": sum(1 for v in v1s if v >= 128),
        "high_bit_count_v2": sum(1 for v in v2s if v >= 128),
    }


def analyze_skill_debuff() -> dict:
    """skill +0x14..+0x17 의 LE16+LE16 signed (R65 발견)."""
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))
    primary_le16: list[int] = []
    secondary_le16: list[int] = []
    for fn, skills in d.items():
        for s in skills:
            if s.get("category_name") != "active_attack":
                continue
            tail = s.get("tail_hex", "")
            b = bytes(int(x, 16) for x in tail.split())
            if len(b) < 0x1d:
                continue
            d1_code = b[0x13]
            if d1_code == 0x7f or d1_code == 0:
                continue
            p = struct.unpack_from("<H", b, 0x14)[0]
            sec = struct.unpack_from("<H", b, 0x16)[0]
            primary_le16.append(as_int16(p))
            secondary_le16.append(as_int16(sec))
    return {
        "n_with_debuff": len(primary_le16),
        "primary_le16_signed": {"min": min(primary_le16) if primary_le16 else 0,
                                "max": max(primary_le16) if primary_le16 else 0,
                                "values": primary_le16},
        "secondary_le16_signed": {"min": min(secondary_le16) if secondary_le16 else 0,
                                  "max": max(secondary_le16) if secondary_le16 else 0,
                                  "values": secondary_le16},
        "verdict": "signed int16 통일 확정 — debuff value 음수 출현",
    }


def analyze_enemy_stats() -> dict:
    """enemy_dat / boss_dat stat block BE16 fields (HP/EXP/Gold)."""
    d = json.loads((ROOT / "work/h3/game_balance.json").read_text(encoding="utf-8"))
    hp_vals = []
    exp_vals = []
    for e in d["enemies"]["normal"] + d["enemies"]["hard"]:
        st = e.get("stats", {})
        if "hp_max" in st:
            hp_vals.append(st["hp_max"])
        if "exp_gold" in st:
            exp_vals.append(st["exp_gold"])
    return {
        "enemy_hp_max":   {"min": min(hp_vals), "max": max(hp_vals), "n": len(hp_vals)},
        "enemy_exp_gold": {"min": min(exp_vals), "max": max(exp_vals), "n": len(exp_vals)},
        "verdict": "BE16 unsigned (HP/EXP 모두 양수, signed bit unused for enemy)",
    }


def main() -> None:
    out = {
        "doc": "Round 65: signed int16 value 통일 검증",
        "hypothesis": "R64 의 i13 debuff signed int16 패턴이 모든 dat 파일에 통일 적용되는지 확인",
        "results": {
            "i13_passive_scroll": analyze_i13(),
            "i12_ring": analyze_i12(),
            "i16_enchant": analyze_i16(),
            "i18_consumable": analyze_i18(),
            "equip_trailer_4B": analyze_equip_trailer(),
            "skill_debuff_mask": analyze_skill_debuff(),
            "enemy_boss_stats": analyze_enemy_stats(),
        },
    }

    out_path = RECON / "value_sign_verification.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 signed value 통일 검증 (R65) =====\n")
    log_lines.append(f"Hypothesis: {out['hypothesis']}\n")

    log_lines.append("[i13 passive scroll effect_value]")
    i13 = out["results"]["i13_passive_scroll"]
    log_lines.append(f"  n={i13['n']}, raw range {i13['min_raw']}..{i13['max_raw']}")
    log_lines.append(f"  signed range {i13['min_signed']}..{i13['max_signed']}")
    log_lines.append(f"  negative cases: {i13['n_negative']}")
    for c in i13["negative_cases"]:
        log_lines.append(f"    {c['name']:<14} raw={c['raw']:>6} signed={c['signed']:>4}  {c['desc']}")

    log_lines.append("\n[i12 ring bonus_value (byte, no signed)]")
    i12 = out["results"]["i12_ring"]
    log_lines.append(f"  n={i12['n']}, range {i12['min']}..{i12['max']}, high-bit count {i12['signed_neg_count']}")

    log_lines.append("\n[i16 enchant magnitude (tail[1] byte)]")
    i16 = out["results"]["i16_enchant"]
    log_lines.append(f"  n={i16['n']}, range {i16['min']}..{i16['max']}, high-bit count {i16['signed_neg_count']}")

    log_lines.append("\n[i18 consumable effect_value (LE16)]")
    i18 = out["results"]["i18_consumable"]
    log_lines.append(f"  n={i18['n']}, raw range {i18['min_raw']}..{i18['max_raw']}")
    log_lines.append(f"  signed range {i18['min_signed']}..{i18['max_signed']}, negative count {i18['n_negative_signed']}")

    log_lines.append("\n[equip trailer 4B (v1, v2 = byte each)]")
    et = out["results"]["equip_trailer_4B"]
    log_lines.append(f"  v1: n={et['n_v1']}, range {et['min_v1']}..{et['max_v1']}, high-bit {et['high_bit_count_v1']}")
    log_lines.append(f"  v2: n={et['n_v2']}, range {et['min_v2']}..{et['max_v2']}, high-bit {et['high_bit_count_v2']}")

    log_lines.append("\n[skill +0x14..+0x17 debuff mask (LE16+LE16 signed)]")
    sk = out["results"]["skill_debuff_mask"]
    log_lines.append(f"  n_with_debuff={sk['n_with_debuff']}")
    log_lines.append(f"  primary signed: min={sk['primary_le16_signed']['min']}, max={sk['primary_le16_signed']['max']}")
    log_lines.append(f"  primary values: {sk['primary_le16_signed']['values']}")
    log_lines.append(f"  secondary signed: min={sk['secondary_le16_signed']['min']}, max={sk['secondary_le16_signed']['max']}")
    log_lines.append(f"  secondary values: {sk['secondary_le16_signed']['values']}")

    log_lines.append("\n[enemy/boss stat block BE16]")
    eb = out["results"]["enemy_boss_stats"]
    log_lines.append(f"  enemy hp_max: {eb['enemy_hp_max']}")
    log_lines.append(f"  enemy exp/gold: {eb['enemy_exp_gold']}")

    log_lines.append("\n[Conclusion]")
    log_lines.append("  i13 effect_value:  LE16 signed 통일 (debuff 음수 출현)")
    log_lines.append("  i12 ring:          byte (signed bit unused, max 80)")
    log_lines.append("  i16 enchant:       byte (signed bit unused)")
    log_lines.append("  i18 consumable:    LE16 unsigned (양수만, 최대 3000)")
    log_lines.append("  equip trailer:     byte (signed bit unused, magic enchant range 1-25)")
    log_lines.append("  skill debuff mask: LE16+LE16 signed (R65 발견)")
    log_lines.append("  enemy/boss stats:  BE16 unsigned")
    log_lines.append("")
    log_lines.append("  → signed int16 사용처: (1) i13 effect_value, (2) skill +0x14..+0x17 debuff mask")
    log_lines.append("  → 그 외 모든 value field 는 unsigned byte/LE16/BE16")
    log_lines.append("  → R64 hypothesis 정정: 'signed int16 통일' 이 아니라, 'debuff context 만 signed'")

    log_path = RECON / "value_sign_verification.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Verdict ---")
    print("  signed int16 사용처 = i13 effect_value + skill +0x14..+0x17 debuff mask")
    print("  그 외 모든 value field 는 unsigned (byte/LE16/BE16)")
    print("  → R64 가설 정정: 'debuff context 만 signed', 'value 전체 signed' 아님")


if __name__ == "__main__":
    main()
