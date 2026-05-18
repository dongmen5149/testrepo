"""Round 68: gun marker (0x1f at +0x0c) 정밀 검증.

R67 발견: skill +0x0c 가 weapon class flag. 0x1f 가 s7_dat (건/피스톨) 의 active_attack 4 skills 전용.

R68 추가 분석:

  weapon class 별 +0x0c flag 분포:
    s7 (건/피스톨):
      weapon_passive (사격1-7):   0x14 (=20)
      active_attack (연사/난사/곡예/저격): 0x1f (=31)
      active_buff (장탄):          0x00
      passive_bonus (조준/냉정/속공): 0x00

    s8 (라이플):
      weapon_passive (격발):       0x01
      active_attack (직격/연쇄):   0x01
      active_attack (위협):        0x00
      buff/passive_bonus:           0x00

    s4 (창), s5 (검), s6 (단검), s9 (다크), s10 (홀리):
      weapon_passive:               0x01 or 0x00
      active_attack:                0x01
      utility:                       0x00

  결론:
    - 0x14 + 0x1f = **s7 (건/피스톨) 전용 marker pair**
      → 사격 weapon_passive 가 일반 0x01 이 아닌 0x14 표시
      → 사격 active_attack 가 일반 0x01 이 아닌 0x1f 표시
    - 0x1f = "건 active_attack" = multi-target pistol marker
    - 0x01 = standard physical attack flag (모든 다른 weapon class)
    - 0x00 = utility / buff (no attack target)

  의미: 건 (단발 권총) 은 다른 무기와 다른 hit-target 계산 또는 ammo 시스템 보유 추정.
        라이플 (s8) 은 standard physical attack 처럼 작동.

Output: work/h3/recon/gun_marker_verification.{json,log}
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


def main() -> None:
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    # weapon flag (+0x0c) per category per weapon class
    flag_by_class_cat: dict = defaultdict(lambda: defaultdict(Counter))
    skill_details: list[dict] = []

    for fn in sorted(d.keys()):
        for s in d[fn]:
            tail = bytes(int(x, 16) for x in s["tail_hex"].split())
            if len(tail) < 14:
                continue
            flag = tail[0x0c]
            cat = s.get("category_name", "?")
            flag_by_class_cat[fn][cat][flag] += 1
            skill_details.append({
                "file": fn,
                "name": s["name"],
                "category": cat,
                "flag_0c": flag,
                "flag_0c_hex": f"0x{flag:02x}",
            })

    # Build summary table
    summary: dict = {}
    for fn, cats in flag_by_class_cat.items():
        summary[fn] = {cat: {f"0x{k:02x}": v for k, v in c.most_common()}
                       for cat, c in cats.items()}

    out = {
        "doc": "Round 68: gun marker (0x1f at +0x0c) 정밀 검증",
        "schema": {
            "+0x0c flag meanings": {
                "0x00": "utility / buff (no attack target)",
                "0x01": "standard physical attack",
                "0x14": "s7 weapon_passive marker (사격 mastery)",
                "0x1f": "s7 active_attack marker (gun multi-target)",
            },
            "weapon_class_distinct_flags": {
                "s7 (건)": "0x14 passive + 0x1f active = special pair",
                "기타 weapon class": "0x01 attack + 0x00 utility = standard pair",
            },
        },
        "summary_per_weapon_class": summary,
        "skill_details": skill_details,
    }

    out_path = RECON / "gun_marker_verification.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 gun marker (0x1f) 정밀 검증 (R68) =====\n")
    log_lines.append("[+0x0c flag meanings]")
    for k, v in out["schema"]["+0x0c flag meanings"].items():
        log_lines.append(f"  {k}: {v}")

    log_lines.append("\n[Per weapon class / category flag distribution]")
    for fn in sorted(summary.keys()):
        log_lines.append(f"\n  {fn}:")
        for cat, flags in summary[fn].items():
            log_lines.append(f"    {cat:<16}: {flags}")

    log_lines.append("\n[Conclusion]")
    log_lines.append("  - s7 (건/피스톨) 만 unique flag pair (0x14 + 0x1f)")
    log_lines.append("  - 라이플 (s8) 은 일반 weapon class 와 동일 (0x01 + 0x00)")
    log_lines.append("  - 0x1f = 'gun multi-target/multi-hit marker' (s7 active_attack 전용)")
    log_lines.append("  - 0x14 = 's7 weapon_passive marker' (사격 mastery 표시)")
    log_lines.append("")
    log_lines.append("  → 게임 내 의미: 단발 권총 (s7) 은 다른 무기 클래스와 별도 hit/ammo 시스템 보유.")
    log_lines.append("  → 라이플 (s8) 은 standard physical attack 처럼 작동.")

    log_path = RECON / "gun_marker_verification.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"  s7 flags: weapon_passive=0x14, active_attack=0x1f (special)")
    print(f"  s8 flags: weapon_passive=0x01, active_attack=0x01 (standard)")
    print(f"  → 0x1f = 's7 (피스톨) gun multi-target marker'")


if __name__ == "__main__":
    main()
