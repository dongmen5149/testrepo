"""Round 65: boss_dat 6B 가변 trailer 디코드.

R58 발견: boss = enemy 의 superset. enemy trailer = 2B 고정 `01 1e`, boss trailer = 6B 가변.

R65 분석:

  boss trailer = 6 bytes:
    [0] level-related metric (combat rating?)
    [1] boss model/sprite index (group ID): 리츠=0, 케이=1, 멜=2, 큐=3, 시즈=0, 아르=1, 오르=2, 홀=4
    [2..5] 4 boss-specific skill IDs (각 byte = skill slot ID):
           - 리츠1/2/케이1/2: 단순 ID (1-3 range)
           - 리츠3/케이3: tier 3 boss 강한 skill (0x13/0x14)
           - 멜페토/큐: paired 4 unique IDs
           - 미사일/타이탄 등 일반 boss = 0xFF 0xFF 0xFF 0xFF (no special skill)

추가 발견:
  - boss trailer[1] = sprite/model index, char_dat 의 character 와 매핑 안 됨 (boss-only)
  - 일반 boss (벨루스/시즈/아르보르/오르도/홀리가디언) 가 0xFF trailer = "no scripted ability"
  - 스토리 보스 (리츠/케이/멜페토/큐) 만 special skill slot 사용

Output: work/h3/recon/boss_trailer.{json,log}
"""
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


def main() -> None:
    d = json.loads((ROOT / "work/h3/game_balance.json").read_text(encoding="utf-8"))

    rows: list[dict] = []
    for difficulty in ("normal", "hard"):
        bosses = d["bosses"].get(difficulty, [])
        for b in bosses:
            tr = b["trailer_hex"]
            try:
                bytes_ = bytes.fromhex(tr.replace(" ", ""))
            except ValueError:
                continue
            if len(bytes_) < 6:
                bytes_ = bytes_ + bytes(6 - len(bytes_))
            row = {
                "difficulty": difficulty,
                "name": b["name"],
                "level": b["stats"].get("lvl"),
                "hp_max": b["stats"].get("hp_max"),
                "trailer_hex": tr,
                "t0_combat_rating": bytes_[0],
                "t1_sprite_idx":    bytes_[1],
                "t2_skill1":        bytes_[2],
                "t3_skill2":        bytes_[3],
                "t4_skill3":        bytes_[4],
                "t5_skill4":        bytes_[5],
                "is_misc_boss":     all(b == 0xFF for b in bytes_[2:6]),
            }
            rows.append(row)

    # group by name family (boss family)
    by_family: dict = {}
    for r in rows:
        family = r["name"]
        by_family.setdefault(family, []).append(r)

    # sprite index per family
    family_sprite: dict = {}
    for fam, items in by_family.items():
        sprites = set(r["t1_sprite_idx"] for r in items)
        family_sprite[fam] = sorted(sprites)

    # skill ID distribution
    skill_ids = Counter()
    for r in rows:
        if r["is_misc_boss"]:
            continue
        for k in ("t2_skill1", "t3_skill2", "t4_skill3", "t5_skill4"):
            skill_ids[r[k]] += 1

    out = {
        "doc": "Round 65: boss_dat 6B 가변 trailer 디코드",
        "schema": {
            "[0]": "combat rating? (lvl 과 비례하지 않는 boss-only metric)",
            "[1]": "sprite/model index (boss family ID)",
            "[2..5]": "4 boss-specific skill slot IDs (0xFF = unused)",
        },
        "family_sprite_index": family_sprite,
        "boss_entries": rows,
        "skill_id_freq_in_story_bosses": dict(skill_ids.most_common()),
        "misc_bosses_count": sum(1 for r in rows if r["is_misc_boss"]),
        "story_bosses_count": sum(1 for r in rows if not r["is_misc_boss"]),
    }

    out_path = RECON / "boss_trailer.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 boss_dat 6B trailer 디코드 (R65) =====\n")
    log_lines.append("[Schema]")
    for k, v in out["schema"].items():
        log_lines.append(f"  {k:<6} {v}")

    log_lines.append("\n[Family → sprite index mapping]")
    for fam, sprites in family_sprite.items():
        log_lines.append(f"  {fam:<12} sprite_idx = {sprites}")

    log_lines.append(f"\n[Boss entries — full dump]")
    log_lines.append(f"  {'diff':<6} {'name':<12} {'lvl':>3} {'hp':>6} t0={'rating':>4} t1={'spr':>3} t2={'sk1':>3} t3={'sk2':>3} t4={'sk3':>3} t5={'sk4':>3} {'kind':<6}")
    for r in rows:
        kind = "misc" if r["is_misc_boss"] else "story"
        log_lines.append(f"  {r['difficulty']:<6} {r['name']:<12} {r['level']:>3} {r['hp_max']:>6}     "
                         f"{r['t0_combat_rating']:>4}      {r['t1_sprite_idx']:>3}      "
                         f"{r['t2_skill1']:>3}      {r['t3_skill2']:>3}      {r['t4_skill3']:>3}      {r['t5_skill4']:>3} {kind}")

    log_lines.append(f"\n[Skill ID freq (story boss only)]")
    log_lines.append(f"  Total skill slot occurrences: {sum(skill_ids.values())}")
    for k, v in skill_ids.most_common():
        log_lines.append(f"  0x{k:02x} ({k:>3}): {v}")

    log_lines.append(f"\n[Counts]")
    log_lines.append(f"  Story bosses (with skill slots):  {out['story_bosses_count']}")
    log_lines.append(f"  Misc bosses (no skills, 0xFF×4): {out['misc_bosses_count']}")

    log_lines.append("\n[Key observations]")
    log_lines.append("  - Story bosses (리츠/케이/멜페토/큐) 만 skill slot 사용")
    log_lines.append("  - Misc bosses (벨루스/시즈타이탄/아르보르/오르도/홀리가디언) trailer[2..5] 전부 0xFF")
    log_lines.append("  - boss family 별 sprite_idx 고유: 리츠=0, 케이=1, 멜페토=2, 큐=3, 시즈=0, 아르=1, 오르=2, 홀=4")
    log_lines.append("  - tier 3 boss (리츠3/케이3) 는 더 강한 skill ID (0x13/0x14) 보유")
    log_lines.append("  - 멜페토/큐 (tier 4) 는 unique skill (각 4 slot 모두 사용)")

    log_path = RECON / "boss_trailer.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print(f"\n--- Summary ---")
    print(f"  Story bosses (with skill slots):  {out['story_bosses_count']}")
    print(f"  Misc bosses (no skills):          {out['misc_bosses_count']}")
    print(f"  Skill IDs observed: {sorted(skill_ids.keys())}")


if __name__ == "__main__":
    main()
