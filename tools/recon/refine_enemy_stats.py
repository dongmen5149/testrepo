"""Round 69: enemy_dat 19B stat block field 정밀 매핑.

R60 발견: hp_max @+0x0a..+0x0b (BE16) — boss 에서 검증 통과.
R69 정밀: normal vs hard scaling 분석으로 각 field 의미 추적.

19B stat block layout (이전 가설):
  +0x00         lvl (byte)
  +0x01..+0x03  pad
  +0x04..+0x05  f4_5 (BE16)  ?
  +0x06..+0x07  f6_7 (BE16)  ?
  +0x08..+0x09  f8_9 (BE16)  ?
  +0x0a..+0x0b  hp_max (BE16) [R60 확정 for boss]
  +0x0c..+0x0d  hp_cur (BE16) ?
  +0x0e..+0x0f  exp_gold (BE16) ?
  +0x10         f16  (byte)  ?
  +0x11 (agi)   AGI/DOD (byte)
  +0x12         f18  (byte)  pad?

R69 scaling 분석 (normal vs hard, top 10 enemies):

  field    | scaling pattern   | 가설
  ---------|-------------------|------
  lvl      | 1.5-3.1x          | lvl (R56 확정)
  f4_5     | 0.54-1.25x (불안정) | variant/ID byte (sprite or AI variant)
  f6_7     | 2.20-4.06x        | MP_max 또는 secondary stat
  f8_9     | 2.78-17x (불안정)  | EXP_high or Gold tier (일부만 큰 scaling)
  hp_max   | 1.98-2.37x ★일관   | HP_max (R60 확정)
  hp_cur   | 2.23-3.13x        | HP_cur 또는 base*multiplier
  exp_gold | 9.65-9.75x ★일관   | EXP (9.7x 일관) — 일부 1.80x = gold 변형
  f16      | 4x ATK scaling    | ATK (physical attack)
  f17 (agi)| +2 constant       | DOD/AGI (mode boost +2)
  f18      | 0 → 0             | pad

R69 정정 field 가설:
  +0x04..+0x05  ID/variant (sprite or model index)
  +0x06..+0x07  MP_max (secondary stat)
  +0x08..+0x09  EXP_high or Gold_tier flag
  +0x0a..+0x0b  HP_max (R60 확정)
  +0x0c..+0x0d  HP_cur 또는 base value
  +0x0e..+0x0f  EXP_main (9.7x scaling)
  +0x10         ATK (4x scaling)
  +0x11         AGI/DOD (+2 boost)
  +0x12         pad

Output: work/h3/recon/enemy_stat_fields.{json,log}
"""
import json
import sys
import statistics
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


FIELD_HYPOTHESIS = {
    "lvl":      {"offset": "+0x00", "guess": "level", "verified": "R56"},
    "f4_5":     {"offset": "+0x04..+0x05", "guess": "ID/variant (sprite or model index)", "scaling": "0.54-1.25x (불안정)"},
    "f6_7":     {"offset": "+0x06..+0x07", "guess": "MP_max or secondary stat", "scaling": "2.20-4.06x"},
    "f8_9":     {"offset": "+0x08..+0x09", "guess": "EXP_high or Gold_tier", "scaling": "2.78-17x (불안정, group별)"},
    "hp_max":   {"offset": "+0x0a..+0x0b", "guess": "HP_max", "verified": "R60", "scaling": "1.98-2.37x"},
    "hp_cur":   {"offset": "+0x0c..+0x0d", "guess": "HP_cur 또는 base*multiplier", "scaling": "2.23-3.13x"},
    "exp_gold": {"offset": "+0x0e..+0x0f", "guess": "EXP_main", "scaling": "9.65-9.75x 일관 (일부 1.80x = gold 변형)"},
    "f16":      {"offset": "+0x10", "guess": "ATK", "scaling": "4x"},
    "agi_or":   {"offset": "+0x11", "guess": "AGI/DOD", "scaling": "+2 constant"},
    "f18":      {"offset": "+0x12", "guess": "pad", "scaling": "0 → 0"},
}


def main() -> None:
    d = json.loads((ROOT / "work/h3/game_balance.json").read_text(encoding="utf-8"))

    # Compute scaling factors for each field
    scaling_data: dict = defaultdict(list)
    raw_pairs = []
    for n, h in zip(d["enemies"]["normal"], d["enemies"]["hard"]):
        if n["name"] != h["name"]:
            continue
        ns, hs = n["stats"], h["stats"]
        raw_pairs.append({
            "name": n["name"],
            "normal_stats": ns,
            "hard_stats": hs,
        })
        for f in ["lvl", "f4_5", "f6_7", "f8_9", "hp_max", "hp_cur", "exp_gold", "f16", "agi_or", "f18"]:
            nv = ns.get(f, 0)
            hv = hs.get(f, 0)
            if nv > 0:
                scaling_data[f].append(hv / nv)

    field_summary = {}
    for f, scales in scaling_data.items():
        if scales:
            field_summary[f] = {
                "min_scale": min(scales),
                "max_scale": max(scales),
                "median_scale": statistics.median(scales),
                "n_samples": len(scales),
            }

    out = {
        "doc": "Round 69: enemy_dat 19B stat block field 정밀 매핑",
        "field_hypothesis": FIELD_HYPOTHESIS,
        "scaling_summary": field_summary,
        "sample_pairs": raw_pairs[:5],
        "verified_fields": {
            "+0x00":      "lvl (R56)",
            "+0x0a..+0x0b": "HP_max (R60 boss 검증)",
        },
        "still_unverified": [
            "+0x04..+0x05 = variant/ID 가설 (scaling 불안정)",
            "+0x06..+0x07 = MP_max 가설 (2-4x scaling)",
            "+0x0e..+0x0f = EXP 가설 (9.7x 일관 + 일부 1.80x gold 변형)",
            "+0x10 = ATK 가설 (4x scaling)",
            "+0x11 = AGI/DOD 가설 (+2 constant boost)",
        ],
        "key_pattern": [
            "hp_max scaling ~ 2x (전체 안정)",
            "exp_gold scaling = 9.7x 또는 1.80x (group 별 두 종류)",
            "AGI = +2 constant (lvl 무관)",
            "ATK = ~4x (lvl 비례)",
        ],
    }

    out_path = RECON / "enemy_stat_fields.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 enemy_dat 19B stat field 정밀 (R69) =====\n")
    log_lines.append("[Field hypothesis]")
    for f, info in FIELD_HYPOTHESIS.items():
        log_lines.append(f"\n  {f:<10} {info['offset']:<14}")
        log_lines.append(f"    guess:    {info.get('guess','?')}")
        log_lines.append(f"    scaling:  {info.get('scaling','?')}")
        if "verified" in info:
            log_lines.append(f"    verified: {info['verified']}")

    log_lines.append("\n[Scaling summary (normal → hard, 161 pairs)]")
    log_lines.append(f"  {'field':<10} {'min':>7} {'max':>7} {'median':>7} {'n':>4}")
    for f, info in field_summary.items():
        log_lines.append(f"  {f:<10} {info['min_scale']:>7.2f} {info['max_scale']:>7.2f} "
                         f"{info['median_scale']:>7.2f} {info['n_samples']:>4}")

    log_lines.append("\n[Key patterns]")
    for p in out["key_pattern"]:
        log_lines.append(f"  - {p}")

    log_lines.append("\n[Verified fields (R56/R60)]")
    for f, v in out["verified_fields"].items():
        log_lines.append(f"  {f}: {v}")

    log_lines.append("\n[Still unverified]")
    for u in out["still_unverified"]:
        log_lines.append(f"  - {u}")

    log_path = RECON / "enemy_stat_fields.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Scaling summary ---")
    for f, info in field_summary.items():
        print(f"  {f:<10} median={info['median_scale']:.2f}x (range {info['min_scale']:.2f}..{info['max_scale']:.2f})")


if __name__ == "__main__":
    main()
