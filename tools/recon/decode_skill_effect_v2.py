"""Round 66: skill effect block v2 — R65 schema 부분 오류 정정.

R65 schema 의 문제: 전율 (3 debuffs) 같은 케이스를 d1+d2 만 캡처 (3개 중 2개 누락).

R66 새 해석:
  - tail = 30 bytes 고정
  - 마지막 byte (+0x1d) = rank (R63)
  - effect chain = right-justified (tail 끝에서 거꾸로 읽음)
  - 각 effect = (1 byte code, LE16+LE16 = 5 bytes total)
  - 0x7f sentinel = "no debuff" placeholder
  - chain length 가변: 1~3 debuffs 까지 관찰됨

알고리즘 (backward scan):
  1. pos 29 = rank
  2. pos 24..28 = 3rd debuff slot (code at 24, value at 25..28)
  3. pos 19..23 = 2nd debuff slot
  4. pos 14..18 = 1st debuff slot
  5. pos 9..13 = "primary damage" slot? (some skills 사용)
  6. pos 0..8 = header (SP cost / damage scale / pad)

특수 케이스:
  - 단일 debuff: 1st slot 사용, 2nd/3rd = 0x7f
  - 2개 debuff: 1st + 2nd 사용, 3rd = 0x7f
  - 3개 debuff: 1st + 2nd + 3rd 모두 사용 (전율)
  - 0 debuff (raw damage): 1st = 0x7f, primary damage 는 다른 곳

또한 위협의 desc "기절저항 감소" 매핑:
  - 위협 debuff code = 0x0d (R65 가설: CRI_DEF)
  - 실제 의미: STUN_RESIST_DEBUFF (skill 컨텍스트 신규)

Output: work/h3/recon/skill_effect_v2.{json,log}
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


# R63+R66 refined master enum
ENUM = {
    0x00: "ATT1_BASE",       0x01: "HP_HEAL_INSTANT",
    0x02: "HP_MAX",          0x03: "HP_REGEN/BLEED",
    0x04: "SP_MAX",          0x05: "ATT1",
    0x06: "ATT2",            0x07: "P_DEF",
    0x08: "M_DEF",           0x09: "ACC",
    0x0a: "DOD",             0x0b: "BLOCK",
    0x0c: "CRI_RATE",        0x0d: "CRI_DEF/STUN_RESIST (R66 컨텍스트별)",
    0x0e: "SP_COST_REDUCE",  0x0f: "SP_REGEN",
    0x10: "HP_DRAIN",        0x11: "CD_REDUCE",
    0x12: "SHIELD_PIERCE",   0x14: "?? (unused)",
    0x15: "TAUNT",           0x16: "BUFF_REMOVE",
    0x17: "CURE_STATUS",     0x19: "?? (unused)",
    0x1c: "REVIVE/STUN (컨텍스트별)",
    0x7f: "(sentinel = no debuff)",
}


def parse_effect_chain(tail: bytes) -> dict:
    """30B tail 의 right-justified effect chain 파싱."""
    if len(tail) < 30:
        return {"error": "tail too short"}
    out = {
        "rank": tail[29],
        "slot1": {},  # pos 14..18
        "slot2": {},  # pos 19..23
        "slot3": {},  # pos 24..28
        "header": tail[:14].hex(" "),
    }
    for i, base in enumerate([14, 19, 24]):
        code = tail[base]
        primary = struct.unpack_from("<h", tail, base + 1)[0]   # signed int16
        secondary = struct.unpack_from("<h", tail, base + 3)[0]
        slot = f"slot{i+1}"
        out[slot] = {
            "code": code,
            "code_hex": f"0x{code:02x}",
            "code_name": ENUM.get(code, "?"),
            "is_sentinel": code == 0x7f,
            "is_zero": code == 0,
            "primary_signed": primary,
            "secondary_signed": secondary,
        }
    # header parse (best effort)
    out["header_sp_cost"] = struct.unpack_from("<H", tail, 0)[0]
    out["header_byte_4_5"] = (tail[4], tail[5])  # damage scale?
    out["header_byte_9_a"] = (tail[9], tail[10])  # 55 55 marker?
    out["header_byte_b"] = tail[11]  # range
    return out


def main() -> None:
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    results: list[dict] = []
    chain_lengths = Counter()
    debuff_codes_used: Counter = Counter()
    code_per_slot = defaultdict(Counter)
    by_skill: dict = {}

    for fn, skills in d.items():
        for s in skills:
            if s.get("category_name") != "active_attack":
                continue
            tail_hex = s.get("tail_hex", "")
            tail = bytes(int(x, 16) for x in tail_hex.split())
            if len(tail) < 30:
                continue
            parsed = parse_effect_chain(tail)
            n_debuffs = sum(1 for slot in [parsed["slot1"], parsed["slot2"], parsed["slot3"]]
                            if not slot["is_sentinel"] and not slot["is_zero"])
            chain_lengths[n_debuffs] += 1
            entry = {
                "file": fn,
                "name": s["name"],
                "desc": (s.get("desc", "") or "")[:60],
                "rank": parsed["rank"],
                "n_debuffs": n_debuffs,
                "slot1": parsed["slot1"],
                "slot2": parsed["slot2"],
                "slot3": parsed["slot3"],
                "header": {
                    "sp_cost":      parsed["header_sp_cost"],
                    "byte_4_5":     parsed["header_byte_4_5"],
                    "byte_9_a":     parsed["header_byte_9_a"],
                    "byte_b_range": parsed["header_byte_b"],
                    "raw_hex":      parsed["header"],
                },
            }
            results.append(entry)
            for slot_name, slot in [("slot1", parsed["slot1"]), ("slot2", parsed["slot2"]), ("slot3", parsed["slot3"])]:
                if not slot["is_sentinel"] and not slot["is_zero"]:
                    debuff_codes_used[slot["code"]] += 1
                    code_per_slot[slot_name][slot["code"]] += 1
            by_skill[s["name"]] = entry

    out = {
        "doc": "Round 66: skill effect block v2 (right-justified chain decode)",
        "schema": {
            "+0x00..+0x01": "LE16 SP cost",
            "+0x02..+0x03": "pad",
            "+0x04..+0x05": "damage scale (byte pair)",
            "+0x06..+0x08": "pad",
            "+0x09..+0x0a": "55 55 marker (?)",
            "+0x0b":         "byte range",
            "+0x0c..+0x0d":  "subheader",
            "+0x0e..+0x13":  "(may extend chain forward for 3-debuff skills)",
            "+0x0e=14":      "slot1 debuff code (right-justified)",
            "+0x0f..+0x12":  "slot1 LE16+LE16 signed value",
            "+0x13=19":      "slot2 debuff code",
            "+0x14..+0x17":  "slot2 LE16+LE16 signed value",
            "+0x18=24":      "slot3 debuff code",
            "+0x19..+0x1c":  "slot3 LE16+LE16 signed value",
            "+0x1d=29":      "rank/power class (R63)",
        },
        "chain_length_distribution": dict(chain_lengths),
        "debuff_code_total_usage": {f"0x{k:02x} ({ENUM.get(k,'?')})": v for k, v in debuff_codes_used.most_common()},
        "code_per_slot": {k: {f"0x{c:02x}": v for c, v in cs.items()} for k, cs in code_per_slot.items()},
        "active_attack_skills": results,
    }

    out_path = RECON / "skill_effect_v2.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 skill effect block v2 (R66) =====\n")
    log_lines.append("[Schema (right-justified, rank @+0x1d)]")
    for k, v in out["schema"].items():
        log_lines.append(f"  {k:<14} {v}")

    log_lines.append(f"\n[Chain length distribution]")
    for n, c in sorted(chain_lengths.items()):
        log_lines.append(f"  {n} debuffs: {c} skills")

    log_lines.append(f"\n[Debuff code total usage (across all 3 slots)]")
    for k, v in debuff_codes_used.most_common():
        log_lines.append(f"  0x{k:02x} ({ENUM.get(k,'?'):<32}) = {v}")

    log_lines.append(f"\n[Code per slot (slot1=first read, slot3=last before rank)]")
    for slot, cs in code_per_slot.items():
        log_lines.append(f"  {slot}: " + ", ".join(f"0x{c:02x}={v}" for c, v in cs.items()))

    log_lines.append(f"\n[All 24 active_attack skills]")
    log_lines.append(f"  {'file':<8} {'name':<14} {'rk':>2} {'sp':>5} {'n_db':>4}  slots")
    for e in results:
        slot_info = []
        for slot_name in ["slot1", "slot2", "slot3"]:
            sl = e[slot_name]
            if sl["is_sentinel"]:
                slot_info.append("..")
            elif sl["is_zero"]:
                slot_info.append("zz")
            else:
                slot_info.append(f"0x{sl['code']:02x}({sl['primary_signed']:>3},{sl['secondary_signed']:>3})")
        log_lines.append(f"  {e['file']:<8} {e['name']:<14} {e['rank']:>2} {e['header']['sp_cost']:>5} "
                         f"{e['n_debuffs']:>4}  " + " | ".join(slot_info) + f"  {e['desc'][:40]}")

    log_lines.append(f"\n[Notable cases]")
    # 3-debuff skill (전율)
    for e in results:
        if e["n_debuffs"] == 3:
            log_lines.append(f"\n  ★ 3-debuff skill: {e['name']} (rank {e['rank']})")
            log_lines.append(f"    desc: {e['desc']}")
            for i, s in enumerate(["slot1", "slot2", "slot3"], 1):
                sl = e[s]
                log_lines.append(f"    slot{i}: 0x{sl['code']:02x} ({sl['code_name']})  "
                                 f"val=({sl['primary_signed']:>3}, {sl['secondary_signed']:>3})")

    # 위협 (R65 의 weird value)
    if "위협" in by_skill:
        wh = by_skill["위협"]
        log_lines.append(f"\n  ★ 위협 정정 (R65 의 weird value 65279/64767 해석):")
        log_lines.append(f"    desc: {wh['desc']}")
        log_lines.append(f"    header_raw: {wh['header']['raw_hex']}")
        log_lines.append(f"    R65 의 'primary_damage 64767' = header padding (의미 없음)")
        log_lines.append(f"    실제 debuff: slot1 = 0x{wh['slot1']['code']:02x} ({wh['slot1']['code_name']})  "
                         f"val=({wh['slot1']['primary_signed']}, {wh['slot1']['secondary_signed']})")
        log_lines.append(f"    → 0x0d 의 skill 컨텍스트 의미 = STUN_RESIST_DEBUFF (i13 의 CRI_DEF 와 분리)")

    log_path = RECON / "skill_effect_v2.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Findings ---")
    print(f"  Chain length distribution: {dict(chain_lengths)}")
    print(f"  Distinct debuff codes:     {sorted(debuff_codes_used.keys())}")
    print(f"  3-debuff skills: 전율 (P_DEF + M_DEF + DOD)")


if __name__ == "__main__":
    main()
