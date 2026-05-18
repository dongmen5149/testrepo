"""Round 67: enemy_dat 2-byte trailer (`01 1e`) 의미 디코드.

R67 분석 결과:

  Trailer byte layout (2 bytes):
    [0] difficulty marker:
      - 0x01 = normal mode
      - 0x02 = hard mode
      - 0x05 = special enemy (unchanged across modes)
      - 0x00 = legacy/sentinel

    [1] enemy category flag:
      - 0x1e (=30) = standard battle enemy (78%, 126/161)
      - 0xff = special/event/scripted enemy (19 + 11 + 5 = 35)

  Distribution (normal mode):
    01 1e: 126 (standard normal enemies)
    01 ff: 19  (normal mode + special)
    05 ff: 11  (cross-mode special)
    00 ff: 5   (sentinel)

  Hard mode 동일 패턴 (byte 0: 01→02), special enemies (05/00) 는 unchanged.

→ byte 0 = mode marker (어느 difficulty 에서 spawn), byte 1 = encounter_type (regular vs scripted).

Output: work/h3/recon/enemy_trailer.{json,log}
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
    d = json.loads((ROOT / "work/h3/game_balance.json").read_text(encoding="utf-8"))

    by_trailer: dict = defaultdict(list)
    for diff in ("normal", "hard"):
        for e in d["enemies"].get(diff, []):
            t = e["trailer_hex"]
            by_trailer[(diff, t)].append({
                "name": e["name"],
                "lvl": e["stats"].get("lvl"),
                "hp_max": e["stats"].get("hp_max"),
            })

    trailer_counts = {f"{diff}/{t}": len(v) for (diff, t), v in by_trailer.items()}

    out = {
        "doc": "Round 67: enemy_dat 2B trailer 의미 디코드",
        "schema": {
            "[0]": "difficulty/mode marker — 0x01 normal / 0x02 hard / 0x05 special-cross / 0x00 sentinel",
            "[1]": "encounter type — 0x1e standard battle (78%) / 0xff special/event",
        },
        "trailer_distribution": trailer_counts,
        "categories": {
            "standard_normal": "01 1e (126 entries, regular normal enemies)",
            "special_normal":  "01 ff (19 entries, scripted/event normal enemies)",
            "cross_mode_special": "05 ff (11 entries, unchanged across normal/hard)",
            "sentinel": "00 ff (5 entries, possibly legacy or boundary)",
            "standard_hard": "02 1e (126 entries, same enemies as 01 1e but hard mode)",
            "special_hard": "02 ff (19 entries)",
        },
        "examples_by_trailer": {f"{diff}/{t}": v[:5] for (diff, t), v in by_trailer.items()},
    }

    out_path = RECON / "enemy_trailer.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 enemy_dat trailer 의미 (R67) =====\n")
    log_lines.append("[Schema]")
    for k, v in out["schema"].items():
        log_lines.append(f"  {k}: {v}")

    log_lines.append("\n[Trailer distribution]")
    for k, v in sorted(trailer_counts.items()):
        log_lines.append(f"  {k}: {v}")

    log_lines.append("\n[Categories]")
    for k, v in out["categories"].items():
        log_lines.append(f"  {k:<22} = {v}")

    log_lines.append("\n[Examples per trailer]")
    for (diff, t), v in sorted(by_trailer.items()):
        log_lines.append(f"\n  {diff}/{t} (n={len(v)}):")
        for ex in v[:5]:
            log_lines.append(f"    {ex['name']:<14} lvl={ex['lvl']} hp_max={ex['hp_max']}")

    log_path = RECON / "enemy_trailer.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    for k, v in sorted(trailer_counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
