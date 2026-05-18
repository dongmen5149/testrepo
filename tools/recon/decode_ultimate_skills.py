"""Round 64: ultimate skill byte-by-byte comparison.

R63 발견: skill rank @ +0x1d 가 "skill power class":
  - 단검 (s6) 난무 r15 = strongest ultimate
  - 건 (s7) 난사 r10
  - 라이플 (s8) 연쇄 r5
  - 다크석 (s9) 나락 r5

이들 active_attack 카테고리의 ultimate skill 30B tail 을
같은 무기의 일반 active skill 과 비교 → ultimate-only field 식별.

방법:
  1. 각 무기 ultimate 의 tail 30B
  2. 같은 무기 normal active 의 tail 30B (rank 1-4) 평균/대표값
  3. column-by-column diff
  4. cross-weapon ultimate 비교 (rank diff 외 공통 패턴)

출력: work/h3/recon/ultimate_skills.{json,log}
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


WEAPON_NAMES = {
    "s4_dat": "창",   "s5_dat": "대검", "s6_dat": "단검",
    "s7_dat": "건",   "s8_dat": "라이플",
    "s9_dat": "다크석", "s10_dat": "홀리석",
}


def hex_to_bytes(hex_str: str) -> list[int]:
    return [int(x, 16) for x in hex_str.split()]


def main() -> None:
    d = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    ultimates_by_weapon: dict = {}
    normals_by_weapon: dict = {}

    for fn, skills in d.items():
        ult: list = []
        norm: list = []
        for s in skills:
            if s.get("category_name") != "active_attack":
                continue
            rank = s.get("rank_or_level", 0)
            row = {
                "name": s["name"],
                "rank": rank,
                "tail_hex": s["tail_hex"],
                "tail_bytes": hex_to_bytes(s["tail_hex"]),
                "desc": (s.get("desc", "") or "")[:50],
            }
            if rank >= 5:
                ult.append(row)
            else:
                norm.append(row)
        if ult:
            ultimates_by_weapon[fn] = ult
            normals_by_weapon[fn] = norm

    out = {
        "doc": "Round 64: ultimate vs normal active_attack skill byte diff",
        "ultimates_summary": [],
        "per_weapon_diff": {},
        "cross_weapon_ultimate_diff": {},
    }

    log_lines: list[str] = []
    log_lines.append("===== Hero3 ultimate skill byte diff (R64) =====")

    log_lines.append("\n[Ultimate skills identified]")
    for fn, ults in ultimates_by_weapon.items():
        for u in ults:
            label = WEAPON_NAMES.get(fn, fn)
            entry = {
                "weapon_file": fn,
                "weapon": label,
                "name": u["name"],
                "rank": u["rank"],
                "tail_len": len(u["tail_bytes"]),
                "desc": u["desc"],
            }
            out["ultimates_summary"].append(entry)
            log_lines.append(f"  {fn:<8} ({label:<7}) {u['name']:<10} rank={u['rank']:<3} desc={u['desc']}")

    # Per-weapon diff: ultimate vs each normal
    log_lines.append("\n[Per-weapon byte diff (ultimate vs normals, 30B tail)]")
    for fn, ults in ultimates_by_weapon.items():
        ult = ults[0]  # one ultimate per weapon
        norms = normals_by_weapon.get(fn, [])
        if not norms:
            continue
        ult_bytes = ult["tail_bytes"]
        diff_cols_per_norm = {}
        for n in norms:
            n_bytes = n["tail_bytes"]
            diffs = []
            for c in range(min(len(ult_bytes), len(n_bytes))):
                if ult_bytes[c] != n_bytes[c]:
                    diffs.append({"col": c, "col_hex": f"+{c:02x}",
                                  "ult_val": ult_bytes[c], "norm_val": n_bytes[c]})
            diff_cols_per_norm[n["name"]] = {
                "norm_rank": n["rank"],
                "diff_count": len(diffs),
                "diffs": diffs,
            }
        out["per_weapon_diff"][fn] = {
            "weapon": WEAPON_NAMES.get(fn, fn),
            "ultimate_name": ult["name"],
            "ultimate_rank": ult["rank"],
            "ultimate_tail": " ".join(f"{b:02x}" for b in ult_bytes),
            "vs_normals": diff_cols_per_norm,
        }
        log_lines.append(f"\n  {fn} ({WEAPON_NAMES.get(fn,fn)}) — ultimate '{ult['name']}' rank={ult['rank']}")
        log_lines.append(f"    ult tail: {' '.join(f'{b:02x}' for b in ult_bytes)}")
        for n_name, info in diff_cols_per_norm.items():
            log_lines.append(f"    vs '{n_name}' (rank={info['norm_rank']}): {info['diff_count']} byte diffs")
            for d in info["diffs"]:
                log_lines.append(f"      +0x{d['col']:02x}: ult={d['ult_val']:>3} ({d['ult_val']:#04x}) "
                                 f"norm={d['norm_val']:>3} ({d['norm_val']:#04x})")

    # Cross-weapon ultimate diff (4 ultimates compared each other column-by-column)
    log_lines.append("\n[Cross-weapon ultimate diff (4 ultimates compared)]")
    ult_list = []
    for fn, ults in ultimates_by_weapon.items():
        ult_list.append((fn, WEAPON_NAMES.get(fn, fn), ults[0]))
    if len(ult_list) >= 2:
        # find columns that vary across ultimates
        col_count = min(len(u[2]["tail_bytes"]) for u in ult_list)
        varying_cols = []
        col_values: dict = defaultdict(list)
        for c in range(col_count):
            vals = [u[2]["tail_bytes"][c] for u in ult_list]
            if len(set(vals)) > 1:
                varying_cols.append(c)
                for u, v in zip(ult_list, vals):
                    col_values[c].append({"weapon_file": u[0], "weapon": u[1], "name": u[2]["name"], "val": v})

        out["cross_weapon_ultimate_diff"] = {
            "ultimates": [
                {"file": u[0], "weapon": u[1], "name": u[2]["name"], "rank": u[2]["rank"],
                 "tail": " ".join(f"{b:02x}" for b in u[2]["tail_bytes"])}
                for u in ult_list
            ],
            "varying_cols": [f"+{c:02x}" for c in varying_cols],
            "col_values": {f"+{c:02x}": v for c, v in col_values.items()},
        }
        log_lines.append(f"\n  varying cols across {len(ult_list)} ultimates: {[f'+{c:02x}' for c in varying_cols]}")
        for c in varying_cols:
            vals_str = ", ".join(f"{u[0]}={u[2]['tail_bytes'][c]:3}({u[2]['tail_bytes'][c]:#04x})" for u in ult_list)
            log_lines.append(f"    +0x{c:02x}: {vals_str}")

    out_path = RECON / "ultimate_skills.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log_path = RECON / "ultimate_skills.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    for line in log_lines[:30]:
        print(line)


if __name__ == "__main__":
    main()
