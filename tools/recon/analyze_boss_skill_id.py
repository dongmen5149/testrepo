"""Round 67: boss skill slot ID → actual skill 매핑 가설 정리.

R65 발견: story boss (리츠/케이/멜페토/큐) 의 trailer[2..5] = 4 byte = skill slot IDs.

R67 분석:

  Distinct IDs observed: {1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 19, 20}
  Range: 1..20

  보스별 skill set:
    리츠 tier 1/2 (lvl 14, 24):  (3, 2, 1, 2)
    리츠 tier 3   (lvl 32, 60):  (19, 13, 9, 9)
    케이 tier 1/2 (lvl 14, 24):  (2, 2, 1, 1)
    케이 tier 3   (lvl 32, 60):  (20, 14, 10, 8)
    멜페토 (lvl 44, 66):        (9, 3, 3, 7)
    큐    (lvl 44, 66):         (7, 8, 5, 9)

  가설들:
    H1) ID = active_attack 글로벌 1-base index (24 actives 매핑)
        - 리츠 t1 (3,2,1,2) = 섬광, 격광, 파동, 격광 → 잘 안 맞음
    H2) ID = weapon-class internal active 1-base index
        - 리츠 = 검 (s5) active = 선풍/양단/질풍 = 3개. ID 1-3 매핑 가능하지만 19/13/9 는 매핑 안 됨
    H3) ID = weapon-class 15-skill 1-base index (모든 skill)
        - 리츠 t1 (3,2,1,2) = s5_dat[2,1,0,1] = 검술3, 검술2, 검술, 검술2
        - 리츠 t3 (19,13,9,9) = 15 max 초과
    H4) ID = 별도 boss_skill_dat (binary 내 별도 table)
        - skill_dat 와 분리된 보스 전용 능력 ID

  결론: H1~H3 모두 일관되지 않음. **H4 (별도 boss skill table) 가 가장 가능성 높음**.

  binary literal grep 또는 DES 복호화된 일부 dat 파일이 boss skill mapping 을 보유 가능.
  R68+ 로 미룸.

Output: work/h3/recon/boss_skill_id_analysis.{json,log}
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
    boss_trailer = json.loads((RECON / "boss_trailer.json").read_text(encoding="utf-8"))
    skill_doc = json.loads((RECON / "skill_decoded.json").read_text(encoding="utf-8"))

    # Build global active_attack index
    global_active = []
    for fn in sorted(skill_doc.keys()):
        for i, s in enumerate(skill_doc[fn]):
            if s.get("category_name") == "active_attack":
                global_active.append({"file": fn, "local_idx": i, "name": s["name"], "rank": s.get("rank_or_level", 0)})

    # Collect distinct IDs from boss skill slots
    distinct_ids: Counter = Counter()
    boss_skill_sets = []
    for b in boss_trailer["boss_entries"]:
        if b["is_misc_boss"]:
            continue
        ids = (b["t2_skill1"], b["t3_skill2"], b["t4_skill3"], b["t5_skill4"])
        boss_skill_sets.append({
            "name": b["name"], "difficulty": b["difficulty"], "lvl": b["level"],
            "skill_ids": list(ids),
        })
        for x in ids:
            distinct_ids[x] += 1

    # Hypothesis H1: global active_attack 1-base
    h1_map = {}
    for idx, entry in enumerate(global_active, start=1):
        h1_map[idx] = entry

    # Hypothesis H3: per-weapon skill_dat 1-base (assume 리츠 = s5, 케이 = s5 too?)
    # 실제 char_dat 의 클래스별 weapon 매핑
    # 리츠 어쌀트워리어 = 검 → s5_dat
    # 케이 버서커 = 양손검? → s5_dat 도 가능, 또는 별도 클래스

    out = {
        "doc": "Round 67: boss skill slot ID 매핑 가설 분석",
        "distinct_boss_ids": dict(distinct_ids.most_common()),
        "boss_skill_sets": boss_skill_sets,
        "h1_global_active_attack_1base": {
            "doc": "ID = active_attack 글로벌 1-base index",
            "mapping": {f"id={k}": v for k, v in h1_map.items()},
            "리츠_t1_가설": "(3,2,1,2) = 섬광, 격광, 파동, 격광 — 잘 안 맞음 (서로 다른 weapon class)",
            "verdict": "rejected — boss class 와 active skill weapon 이 일치하지 않음",
        },
        "h2_weapon_internal_active_1base": {
            "doc": "ID = weapon-class internal active_attack 1-base",
            "verdict": "rejected — 리츠 t3 의 (19,13,9,9) 가 3-skill 범위 초과",
        },
        "h3_weapon_15skill_1base": {
            "doc": "ID = weapon-class 15 skill 1-base (passive + active 모두 포함)",
            "리츠_t1_가설": "(3,2,1,2) = s5_dat[2,1,0,1] = 검술3, 검술2, 검술, 검술2 — 4 passive skills",
            "verdict": "partial — 리츠 t1/t2 일치, 리츠 t3 (19) 가 15 max 초과",
        },
        "h4_separate_boss_skill_table": {
            "doc": "ID = 별도 boss_skill_dat (binary 내 별도 table)",
            "evidence": "기존 skill_dat 와 별개로 boss 전용 ability 매핑 존재 가능",
            "next_step": "binary literal grep + DES 복호화 후 확인",
            "verdict": "most_likely — R68+ 검증 필요",
        },
        "conclusion": [
            "H1~H3 매핑 시도 모두 일관되지 않음",
            "H4 (별도 boss skill table) 가 가장 가능성 높음",
            "binary 내 boss skill mapping table 또는 DES 복호화 파일 분석 필요",
            "R68 후속 작업 — FUN_4f358 또는 DES 복호화 후 진행",
        ],
    }

    out_path = RECON / "boss_skill_id_analysis.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 boss skill slot ID 매핑 가설 분석 (R67) =====\n")
    log_lines.append(f"[Distinct boss skill IDs (n={len(distinct_ids)}): {sorted(distinct_ids.keys())}]")
    log_lines.append(f"[ID range: {min(distinct_ids.keys())}..{max(distinct_ids.keys())}]")

    log_lines.append("\n[Boss skill sets (story boss only)]")
    for b in boss_skill_sets:
        log_lines.append(f"  {b['name']:<10} ({b['difficulty']:<6}) lvl={b['lvl']:>2}  skill_ids={b['skill_ids']}")

    log_lines.append("\n[Global active_attack 1-base index (H1 mapping)]")
    for k, v in h1_map.items():
        log_lines.append(f"  id={k:>3}: {v['file']:<8} [{v['local_idx']:>2}] {v['name']:<14} rank={v['rank']}")

    log_lines.append("\n[Hypothesis verdicts]")
    for h in ["h1_global_active_attack_1base", "h2_weapon_internal_active_1base",
              "h3_weapon_15skill_1base", "h4_separate_boss_skill_table"]:
        info = out[h]
        log_lines.append(f"\n  {h}:")
        log_lines.append(f"    doc: {info['doc']}")
        log_lines.append(f"    verdict: {info['verdict']}")
        if "리츠_t1_가설" in info:
            log_lines.append(f"    리츠_t1: {info['리츠_t1_가설']}")

    log_lines.append("\n[Conclusion]")
    for c in out["conclusion"]:
        log_lines.append(f"  - {c}")

    log_path = RECON / "boss_skill_id_analysis.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"  Distinct IDs: {sorted(distinct_ids.keys())}")
    print(f"  Range: {min(distinct_ids.keys())}..{max(distinct_ids.keys())}")
    print(f"  Verdict: H4 (별도 boss skill table) 가장 가능성 — R68+ binary 분석 필요")


if __name__ == "__main__":
    main()
