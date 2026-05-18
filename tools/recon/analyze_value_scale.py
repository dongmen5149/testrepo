"""Round 64: i13/i12/i16/i18 effect_value scale 분석 (flat vs ratio).

R63 에서 stat enum 은 100% 매핑 완료. 미해결: value 의 의미 (% ratio 또는 flat).

핵심 가설 (desc 텍스트 + value range 로 검증):

  source | code | example | desc | scale
  -------|------|---------|------|------
  i12 ring 힘의반지 | 0x05 | value=8 | "(equip stat bonus)" | **flat** (+8 ATT1)
  i13 끓어오르는피  | 0x0502 | value=40 | "물리공격력이 일정시간 증가" | **ratio** (+40%)
  i13 혼신의일격   | 0x0502 | value=80 | "물리공격력이 순간 극대화" | **ratio** (+80%)
  i18 포션         | 0x0112 | value=200 | "HP를 200 회복" | **flat** (HP +200)
  i18 과일쥬스     | 0x0416 | value=200 | "SP를 20% 회복" | **ratio×10** (SP +20% = value/10)
  i18 포도주       | 0x0417 | value=500 | "SP를 50% 회복" | **ratio×10**
  i18 요정수       | 0x0418 | value=1000 | "SP를 완전 회복" | flat 1000 = "max"
  i16 투신의       | tail=02 05 ... | "HP 최대치 증가" | tail[1]=5 = **flat** (HP +5)

low byte (target) 매핑:
  0x?02 = 사용자 (self, single, temporary)
  0x?03 = 대상 (target, instant)
  0x?04 = 파티 전체 (party-wide, temporary)
  0x?12..15 = HP heal tier 1..4 (flat)
  0x?16..18 = SP heal tier (ratio×10 or full)
  0x?19..1c = boolean/special (revive, return, expand)

i13 specifically: high byte = stat code, low byte = target+duration
  → value scale 은 stat code 에 의해 결정:
    - HP/SP heal codes (0x01, 0x04) = flat (value = HP/SP delta)
    - stat buff codes (0x02~0x12) = **ratio %** (value = bonus %)
    - special codes (0x16, 0x17, 0x1c) = value=0 (effect only)

i12 ring: target single, duration permanent → **flat 통일**.
i16 enchant: tail[1] = small int (2-15) → flat or "level" enum.
equip trailer: bonus_type + value → flat (R62).

Output:
  work/h3/recon/value_scale.json
  work/h3/recon/value_scale.log
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


# (target low byte → label)
LOW_BYTE = {
    0x02: "self_temp",     0x03: "target_inst",   0x04: "party_temp",
    0x12: "heal_t1",       0x13: "heal_t2",       0x14: "heal_t3",       0x15: "heal_t4",
    0x16: "sp_t1",         0x17: "sp_t2",         0x18: "sp_t3",
    0x19: "revive",        0x1a: "town_return",   0x1b: "town_warp",     0x1c: "special",
    0x00: "passive",       0x01: "expand",        0x05: "boss_drop",
}


def classify_i13(items: list) -> dict:
    """i13 = 패시브/스크롤 (35) — temporary buff items."""
    by_stat: dict = defaultdict(list)
    for it in items:
        et_str = it.get("effect_type", "")
        if not et_str:
            continue
        et = int(et_str.replace("0x", ""), 16) if isinstance(et_str, str) else et_str
        high = (et >> 8) & 0xFF
        low = et & 0xFF
        val = it.get("effect_value", 0)
        desc = it.get("desc", "")
        scale = "?"
        if high == 0x01 and low in (0x02, 0x03, 0x04):
            scale = "flat (HP delta)"
        elif high == 0x04 and low in (0x02, 0x03, 0x04):
            scale = "flat (SP delta)"
        elif high in (0x02, 0x03) and low in (0x02, 0x03, 0x04):
            scale = "flat (HP regen/max)"
        elif high >= 0x05 and high <= 0x12 and low in (0x02, 0x03, 0x04):
            scale = "ratio % (stat buff)"
        elif high in (0x16, 0x17, 0x1c):
            scale = "boolean (value=0)"
        # description 으로 추가 검증
        if "회복한다" in desc and "%" not in desc:
            scale_hint = "desc:flat"
        elif "%" in desc:
            scale_hint = "desc:ratio"
        elif "일정시간 증가" in desc or "순간 극대화" in desc or "순간 증가" in desc:
            scale_hint = "desc:ratio"
        else:
            scale_hint = "desc:?"
        by_stat[f"0x{high:02x}"].append({
            "name": it.get("name", ""),
            "effect_type": et_str,
            "low_byte": f"0x{low:02x} ({LOW_BYTE.get(low,'?')})",
            "value": val,
            "scale": scale,
            "scale_hint": scale_hint,
            "desc": desc[:40],
        })
    return dict(by_stat)


def classify_i12(items: list) -> dict:
    """i12 = ring (40) — permanent equip, flat bonus."""
    by_stat: dict = defaultdict(list)
    for it in items:
        bt = it.get("bonus_type", 0)
        bv = it.get("bonus_value", 0)
        by_stat[f"0x{bt:02x}"].append({
            "name": it.get("name", ""),
            "bonus_value": bv,
            "scale": "flat (permanent equip)",
        })
    return dict(by_stat)


def classify_i16(items: list) -> dict:
    """i16 = enchant (15) — tail = (stat_code, magnitude, sub_a, sub_b)."""
    by_stat: dict = defaultdict(list)
    for it in items:
        tail_hex = it.get("tail", "")
        bytes_ = bytes.fromhex(tail_hex.replace(" ", "")) if tail_hex else b""
        if len(bytes_) < 2:
            continue
        stat = bytes_[0]
        mag = bytes_[1]
        sub_a = bytes_[2] if len(bytes_) >= 3 else 0
        sub_b = bytes_[3] if len(bytes_) >= 4 else 0
        by_stat[f"0x{stat:02x}"].append({
            "name": it.get("name", ""),
            "magnitude": mag,
            "sub_a": sub_a,
            "sub_b": sub_b,
            "scale": "flat (enchant permanent)",
            "desc": (it.get("desc","") or "")[:40],
        })
    return dict(by_stat)


def classify_i18(items: list) -> dict:
    """i18 = consumables (26) — instant use, scale depends on desc."""
    by_kind: dict = defaultdict(list)
    for it in items:
        et_str = it.get("effect_type", "")
        et = int(et_str.replace("0x", ""), 16) if isinstance(et_str, str) and et_str else 0
        high = (et >> 8) & 0xFF
        low = et & 0xFF
        val = it.get("effect_value", 0)
        desc = it.get("desc", "")
        kind = "?"
        scale = "?"
        if low in (0x12, 0x13, 0x14, 0x15) and high == 0x01:
            kind, scale = "HP_heal_tier", "flat (HP delta)"
        elif low in (0x16, 0x17, 0x18) and high == 0x04:
            kind, scale = "SP_heal_tier", "ratio×10 (value/10 = % SP recovery)"
        elif low in (0x19, 0x1a, 0x1b, 0x1c):
            kind, scale = "boolean", "value=0 (boolean effect)"
        elif low == 0x11:
            kind, scale = "expand_bag", "value=0 (boolean expand)"
        by_kind[kind].append({
            "name": it.get("name", ""),
            "effect_type": et_str,
            "value": val,
            "scale": scale,
            "desc": desc[:50],
        })
    return dict(by_kind)


def main() -> None:
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))

    out = {
        "doc": "Round 64: value scale 분석 (flat vs ratio)",
        "summary": {
            "i12_ring":  "permanent equip → all flat",
            "i13_scroll": "temp buff/heal → HP/SP heal flat, stat buff ratio%",
            "i16_enchant": "permanent equip → tail[1] = flat magnitude",
            "i17_quest": "quest item only → no stat effect (value=0)",
            "i18_consumable": "instant use → HP heal flat, SP heal ratio×10, special boolean",
            "equip_trailer": "permanent equip → (bonus_type, value) all flat (R62)",
        },
        "low_byte_table": {f"0x{k:02x}": v for k, v in LOW_BYTE.items()},
        "i12_ring":      classify_i12(d.get("i12_dat", {}).get("items", [])),
        "i13_scroll":    classify_i13(d.get("i13_dat", {}).get("items", [])),
        "i16_enchant":   classify_i16(d.get("i16_dat", {}).get("items", [])),
        "i18_consumable":classify_i18(d.get("i18_dat", {}).get("items", [])),
    }

    out_path = RECON / "value_scale.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 value scale analysis (R64) =====\n")
    log_lines.append("[Summary]")
    for k, v in out["summary"].items():
        log_lines.append(f"  {k:<20} → {v}")

    log_lines.append("\n[i13_scroll — by stat code (high byte)]")
    for stat, items in sorted(out["i13_scroll"].items()):
        log_lines.append(f"\n  {stat}:")
        for it in items:
            log_lines.append(f"    {it['name']:<14} val={it['value']:>4}  scale={it['scale']:<22} hint={it['scale_hint']}  {it.get('desc','')}")

    log_lines.append("\n[i12_ring — by stat code (bonus_type)]")
    for stat, items in sorted(out["i12_ring"].items()):
        log_lines.append(f"\n  {stat}:")
        for it in items:
            log_lines.append(f"    {it['name']:<14} val={it['bonus_value']:>4}  scale={it['scale']}")

    log_lines.append("\n[i16_enchant — by stat code (tail[0])]")
    for stat, items in sorted(out["i16_enchant"].items()):
        log_lines.append(f"\n  {stat}:")
        for it in items:
            log_lines.append(f"    {it['name']:<10} mag={it['magnitude']:>3}  sub=({it['sub_a']:>3},{it['sub_b']:>3}) {it.get('desc','')}")

    log_lines.append("\n[i18_consumable — by effect kind]")
    for kind, items in out["i18_consumable"].items():
        log_lines.append(f"\n  {kind}:")
        for it in items:
            log_lines.append(f"    {it['name']:<15} type={it['effect_type']} val={it['value']:>5}  scale={it['scale']}  {it['desc']}")

    log_path = RECON / "value_scale.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")

    # Print key summary to console
    print("\n--- Key findings ---")
    for k, v in out["summary"].items():
        print(f"  {k:<20} → {v}")


if __name__ == "__main__":
    main()
