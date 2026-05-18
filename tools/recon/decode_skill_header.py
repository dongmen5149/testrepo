"""Round 67: skill header (+0x00..+0x0d) 정밀 디코드.

R66 schema v2 에서 effect chain (+0x0e..+0x1d) 만 디코드. header 의 의미는 부분 파악.

R67 정밀 분석 결과:

  +0x00..+0x01  LE16  SP cost (100~800 range)
  +0x02..+0x03  pad (00 00)
  +0x04         byte  primary damage base (40/80/120 = 무기 damage scale)
  +0x05         byte  secondary damage base (대부분 0, 일부 70/80/120 = combo)
  +0x06         pad (00)
  +0x07         byte  utility marker: 0x14 (=20) for utility skill (압도, 위협)
  +0x08         pad (00)
  +0x09..+0x0a  byte pair  animation timing or sprite frames
                  - 0x55 0x55 (85,85) = utility/debuff
                  - 0x29 0x29 (41,41) = 단검 1체
                  - 0x66 0x66 (102)   = 섬광
                  - 그 외 = weapon-specific animation timing
  +0x0b         byte  range/AoE radius
                  - 0   = no range (gun cross-fire)
                  - 20  = melee 단검
                  - 30  = melee 창
                  - 40  = melee 검/라이플/마법
                  - 80  = sniper 저격
                  - 100 = utility (압도/유도/위협/망각/전율)
  +0x0c         byte  weapon class flag
                  - 1  = 일반 attack
                  - 0  = utility / no damage
                  - 31 (0x1f) = gun-specific marker (s7 전용, 5 skills)
  +0x0d         byte  hit flag
                  - 1 = HIT_PHYSICAL
                  - 0 = no hit
                  - flag = utility

Output: work/h3/recon/skill_header.{json,log}
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


def decode_header(tail: bytes) -> dict:
    if len(tail) < 30:
        return {}
    return {
        "sp_cost":               struct.unpack_from("<H", tail, 0)[0],
        "primary_damage_base":   tail[4],
        "secondary_damage_base": tail[5],
        "byte_06":               tail[6],
        "byte_07_utility":       tail[7],
        "byte_08":               tail[8],
        "anim_byte_09":          tail[9],
        "anim_byte_0a":          tail[10],
        "range_aoe":             tail[11],
        "weapon_flag_0c":        tail[12],
        "hit_flag_0d":           tail[13],
    }


def classify_range(rng: int) -> str:
    if rng == 0: return "no_range (gun cross-fire)"
    if rng == 20: return "melee_short (단검)"
    if rng == 30: return "melee_med (창)"
    if rng == 40: return "melee_long (검/마법)"
    if rng == 80: return "sniper"
    if rng == 100: return "utility/debuff"
    return f"?{rng}"


def main() -> None:
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    headers: list[dict] = []
    range_dist: Counter = Counter()
    flag_0c_dist: Counter = Counter()
    sp_per_weapon: defaultdict = defaultdict(list)

    for fn, skills in d.items():
        for s in skills:
            if s.get("category_name") != "active_attack":
                continue
            tail = bytes(int(x, 16) for x in s["tail_hex"].split())
            if len(tail) < 30:
                continue
            hdr = decode_header(tail)
            entry = {
                "file": fn,
                "name": s["name"],
                "rank": s.get("rank_or_level", 0),
                "desc": (s.get("desc", "") or "")[:50],
                **hdr,
                "range_kind": classify_range(hdr["range_aoe"]),
            }
            headers.append(entry)
            range_dist[hdr["range_aoe"]] += 1
            flag_0c_dist[hdr["weapon_flag_0c"]] += 1
            sp_per_weapon[fn].append(hdr["sp_cost"])

    out = {
        "doc": "Round 67: skill header (+0x00..+0x0d) 정밀 디코드",
        "schema": {
            "+0x00..+0x01":  "LE16 SP cost",
            "+0x02..+0x03":  "pad",
            "+0x04":         "primary damage base (40/80/120)",
            "+0x05":         "secondary damage base (combo)",
            "+0x06":         "pad",
            "+0x07":         "utility marker (0x14 for utility)",
            "+0x08":         "pad",
            "+0x09..+0x0a":  "byte pair (animation timing, sprite frames)",
            "+0x0b":         "range / AoE radius",
            "+0x0c":         "weapon class flag (1=attack, 31=gun marker)",
            "+0x0d":         "hit flag (1=HIT_PHYSICAL)",
        },
        "range_distribution": {f"{k}": v for k, v in range_dist.most_common()},
        "weapon_flag_0c_distribution": {f"0x{k:02x}": v for k, v in flag_0c_dist.most_common()},
        "sp_per_weapon": {fn: {"min": min(v), "max": max(v), "values": v} for fn, v in sp_per_weapon.items()},
        "headers": headers,
    }

    out_path = RECON / "skill_header.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 skill header decode (R67) =====\n")
    log_lines.append("[Schema]")
    for k, v in out["schema"].items():
        log_lines.append(f"  {k:<14} {v}")

    log_lines.append("\n[Range distribution]")
    for k, v in range_dist.most_common():
        log_lines.append(f"  {k:>4} ({classify_range(k):<30}): {v}")

    log_lines.append("\n[Weapon flag 0c distribution]")
    for k, v in flag_0c_dist.most_common():
        kind = "gun_marker (s7)" if k == 31 else "attack" if k == 1 else "utility" if k == 0 else f"?{k}"
        log_lines.append(f"  0x{k:02x} ({kind:<20}): {v}")

    log_lines.append("\n[SP per weapon class]")
    for fn, v in sp_per_weapon.items():
        log_lines.append(f"  {fn}: SP={min(v)}..{max(v)} (n={len(v)})")

    log_lines.append("\n[All 24 active_attack headers]")
    log_lines.append(f"  {'file':<8} {'name':<14} {'rk':>2} {'sp':>4} {'pdmg':>4} {'sdmg':>4} {'util':>4} "
                     f"{'a09':>4} {'a0a':>4} {'rng':>4} {'flag':>5} {'hit':>3}  range_kind")
    for h in headers:
        log_lines.append(f"  {h['file']:<8} {h['name']:<14} {h['rank']:>2} "
                         f"{h['sp_cost']:>4} "
                         f"{h['primary_damage_base']:>4} {h['secondary_damage_base']:>4} "
                         f"{h['byte_07_utility']:>4} "
                         f"{h['anim_byte_09']:>4} {h['anim_byte_0a']:>4} "
                         f"{h['range_aoe']:>4} "
                         f"{h['weapon_flag_0c']:>5} {h['hit_flag_0d']:>3}  {h['range_kind']}")

    log_lines.append("\n[Key findings]")
    log_lines.append("  - +0x0c = 31 (0x1f) gun marker = s7_dat 의 5 skills 전용 (연사/난사/곡예/저격)")
    log_lines.append("  - +0x0b range = weapon-class specific (단검 20, 창 30, 검/마법 40, 라이플 80)")
    log_lines.append("  - utility skills (압도/유도/위협/망각/전율) 공통: +0x09..+0x0a = (85,85) + range=100")
    log_lines.append("  - +0x04..+0x05 = (120, 70/80/120) = combo damage (메인 + 보조)")

    log_path = RECON / "skill_header.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"  Range distribution: {dict(range_dist)}")
    print(f"  Flag 0c distribution: {dict(flag_0c_dist)}")
    print(f"  Gun marker (0x1f at +0x0c) skills: {sum(1 for h in headers if h['weapon_flag_0c']==31)}")


if __name__ == "__main__":
    main()
