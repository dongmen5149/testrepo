#!/usr/bin/env python3
"""R110: class_0..3 skill desc placeholder + stats_u16 매핑 검증.

R109 시점 class_0..3 의 cooldown 미해결 — spirit 만 explicit field 보유,
class_0..3 는 stats_u16 fallback 의존. 실 값이 의미 있는 범위인지 검증.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apps/hero5-godot/assets/gamedata/skills.json"

PLACEHOLDER_LABELS = {4: "효과", 5: "공격", 6: "마법", 7: "MP", 8: "지속", 9: "쿨", 12: "수치"}
THRESHOLD = 500

# R108 PLACEHOLDER_STAT_SOURCE — class_0..3 는 skill_info 의 추정 매핑 사용
INFO_INDEX = {
    "effect_type": 14, "dynamic_formula_id": 18, "special_dispatch": 21,
    "formula_id_1": 22, "formula_id_2": 23,
}


def main():
    data = json.loads(SKILLS.read_text(encoding="utf-8"))
    summary = {}
    for cls_key in ("class_0", "class_1", "class_2", "class_3"):
        skills = data.get(cls_key, [])
        cls_stats = {"total": len(skills), "with_ph": 0, "ph_dist": {}, "samples": []}
        for sidx, sk in enumerate(skills):
            desc = sk.get("desc", "")
            stats = sk.get("stats_u16", [])
            phs = re.findall(r"#(\d{2})", desc)
            if not phs:
                continue
            cls_stats["with_ph"] += 1
            resolved = {}
            for nn_s in set(phs):
                nn = int(nn_s)
                cls_stats["ph_dist"][nn] = cls_stats["ph_dist"].get(nn, 0) + 1
                raw = int(stats[nn]) if nn < len(stats) else -1
                if 0 <= raw <= THRESHOLD:
                    resolved[nn] = str(raw)
                else:
                    lbl = PLACEHOLDER_LABELS.get(nn, "?")
                    resolved[nn] = f"?({lbl})" if nn in PLACEHOLDER_LABELS else "?"
            if len(cls_stats["samples"]) < 3:
                cls_stats["samples"].append(
                    {"idx": sidx, "name": sk.get("name"), "desc_head": desc[:50],
                     "stats_u16": stats[:13], "resolved": resolved}
                )
        summary[cls_key] = cls_stats

    print(f"{'class':<10} {'total':>5} {'w/ph':>5}  ph_dist (NN: count)")
    print("-" * 70)
    for cls, s in summary.items():
        dist_str = " ".join(f"#{nn:02d}:{c}" for nn, c in sorted(s["ph_dist"].items()))
        print(f"{cls:<10} {s['total']:>5} {s['with_ph']:>5}  {dist_str}")

    print()
    for cls, s in summary.items():
        if not s["samples"]:
            continue
        print(f"\n=== {cls} samples ===")
        for sm in s["samples"]:
            print(f"  [{sm['idx']:>2}] {sm['name']}")
            print(f"       desc: {sm['desc_head']!r}")
            print(f"       stats_u16[0..12]: {sm['stats_u16']}")
            print(f"       resolved: {sm['resolved']}")


if __name__ == "__main__":
    main()
