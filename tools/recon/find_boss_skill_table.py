"""Round 68: boss skill table 추적 — H4 가설 검증.

R67 결론: H4 (별도 boss skill table) most likely. binary 또는 dat 파일에서
1..20 range 의 boss skill ID 가 어디 reference 되는지 추적.

방법:
  1. R67 의 (3,2,1,2) (2,2,1,1) (9,3,3,7) (7,8,5,9) (19,13,9,9) (20,14,10,8) 6 패턴이
     binary 직접 매칭 0 hit 확인 (already done)
  2. dat 파일 (extracted/dat/*) 에서 매칭 시도
  3. R55 의 task[+0x9e28] NPC table grid 와 연관 가능
  4. trailer[2..5] 의 의미 재해석 — stat boost vs skill ID vs AI pattern

R68 추가 분석:
  - 리츠 tier 1 (lvl 14) + tier 2 (lvl 24): **같은 trailer (3,2,1,2)**
  - 리츠 tier 3 (lvl 32): 다른 trailer (19,13,9,9)
  → trailer 가 lvl-dependent 아니라 **boss progression tier** 에 따라 변함
  → "AI behavior set per tier" 가설 강화 (각 tier 가 다른 skill set 보유)

  - 케이 vs 리츠 tier 1/2 비교:
    리츠: (3,2,1,2), 케이: (2,2,1,1)
    → 다른 character class (어쌀트워리어 vs 버서커) 의 다른 base skill
    → trailer 값이 character class identity 와 연관

  - 멜페토 (9,3,3,7) vs 큐 (7,8,5,9): tier 4 paired boss, 완전히 다른 skill set

가설 정리:
  최종 가설: **trailer[2..5] = (skill_slot_0, skill_slot_1, skill_slot_2, skill_slot_3)**
    각 slot 의 값 = boss AI 가 선택할 수 있는 skill action ID
    별도 boss AI table 이 존재 (binary 내 hard-coded 또는 DES dat 파일)
  검증 방법:
    1. DES 복호화된 파일 (drop_dat / getitem_dat 등) 의 entry 구조 확인
    2. FUN_4f358 + NPC table 의 row data 분석
    3. enemy_dat 의 19B stat block 안에 hidden skill table 위치 가능성

Output: work/h3/recon/boss_skill_table_search.{json,log}
"""
import json
import sys
import struct
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"
EXT = ROOT / "work/h3/extracted"


def search_pattern(data: bytes, pattern: bytes, label: str) -> list[int]:
    """Find all occurrences of pattern in data."""
    locs = []
    pos = 0
    while True:
        idx = data.find(pattern, pos)
        if idx < 0:
            break
        locs.append(idx)
        pos = idx + 1
    return locs


def main() -> None:
    boss_trailer = json.loads((RECON / "boss_trailer.json").read_text(encoding="utf-8"))
    bin_data = (EXT / "client.bin64000").read_bytes()

    # 6 distinct boss skill slot patterns
    patterns = [
        (b"\x03\x02\x01\x02", "리츠 t1/t2 (3,2,1,2)"),
        (b"\x02\x02\x01\x01", "케이 t1/t2 (2,2,1,1)"),
        (b"\x09\x03\x03\x07", "멜페토 t4 (9,3,3,7)"),
        (b"\x07\x08\x05\x09", "큐 t4 (7,8,5,9)"),
        (b"\x13\x0d\x09\x09", "리츠 t3 (19,13,9,9)"),
        (b"\x14\x0e\x0a\x08", "케이 t3 (20,14,10,8)"),
    ]

    # Search binary
    bin_hits: dict = {}
    for pat, label in patterns:
        hits = search_pattern(bin_data, pat, label)
        bin_hits[label] = {"n_hits": len(hits), "offsets": [hex(x) for x in hits[:5]]}

    # Search dat files
    dat_hits: dict = {}
    dat_files = sorted((EXT / "dat").glob("*"))
    for dat in dat_files:
        if not dat.is_file():
            continue
        try:
            data = dat.read_bytes()
        except Exception:
            continue
        for pat, label in patterns:
            hits = search_pattern(data, pat, label)
            if hits:
                key = f"{dat.name}/{label}"
                dat_hits[key] = {"n_hits": len(hits), "offsets": [hex(x) for x in hits[:5]]}

    out = {
        "doc": "Round 68: boss skill table 추적 — H4 가설 검증",
        "binary_hits": bin_hits,
        "dat_file_hits": dat_hits,
        "binary_size": len(bin_data),
        "conclusion": {
            "binary_direct_match": all(v["n_hits"] == 0 for v in bin_hits.values()),
            "dat_direct_match": len(dat_hits) > 0,
            "hypothesis_strength": "H4 boss skill mapping 은 binary 에 hard-coded 안 됨, dat 파일 내부 또는 runtime computed",
        },
        "alternative_hypothesis": [
            "H5: trailer[2..5] = (boss progression tier 별 AI script ID)",
            "H6: trailer[2..5] = 4 stat boost values (ATT1/ATT2/P_DEF/M_DEF +N)",
            "H7: 값 자체가 raw AI behavior weight (probability of each skill slot)",
        ],
        "observations": {
            "tier_pattern": [
                "리츠 tier 1 (lvl 14) + tier 2 (lvl 24): 같은 trailer (3,2,1,2)",
                "리츠 tier 3 (lvl 32): 다른 trailer (19,13,9,9)",
                "→ trailer 가 lvl 아니라 tier 에 의존",
            ],
            "character_class_pattern": [
                "리츠 (어쌀트워리어): (3,2,1,2)",
                "케이 (버서커): (2,2,1,1)",
                "→ 같은 tier 라도 character class 마다 다른 trailer",
            ],
        },
    }

    out_path = RECON / "boss_skill_table_search.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 boss skill table 추적 (R68) =====\n")
    log_lines.append("[Binary client.bin64000 직접 매칭]")
    for label, info in bin_hits.items():
        log_lines.append(f"  {label}: {info['n_hits']} hits")

    log_lines.append("\n[Dat 파일 직접 매칭]")
    if dat_hits:
        for key, info in dat_hits.items():
            log_lines.append(f"  {key}: {info['n_hits']} hits @ {info['offsets']}")
    else:
        log_lines.append("  (no direct matches in dat files)")

    log_lines.append("\n[Conclusion]")
    log_lines.append(f"  binary direct match: {out['conclusion']['binary_direct_match']}")
    log_lines.append(f"  dat direct match:    {out['conclusion']['dat_direct_match']}")
    log_lines.append(f"  → {out['conclusion']['hypothesis_strength']}")

    log_lines.append("\n[Alternative hypothesis]")
    for h in out["alternative_hypothesis"]:
        log_lines.append(f"  - {h}")

    log_lines.append("\n[Observations]")
    for k, v in out["observations"].items():
        log_lines.append(f"\n  {k}:")
        for line in v:
            log_lines.append(f"    {line}")

    log_path = RECON / "boss_skill_table_search.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"  Binary direct match: {out['conclusion']['binary_direct_match']}")
    print(f"  Dat direct match: {len(dat_hits)} found")
    print(f"  → trailer[2..5] 의미 미해결, DES 복호화 후 재시도 필요")


if __name__ == "__main__":
    main()
