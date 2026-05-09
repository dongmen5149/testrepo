"""text/*.json (VFS 추출 한글 텍스트) 에서 stat 라벨의 file/offset 검색.

Hero5 의 한글 stat 라벨은 .so 가 아닌 `vfs_entries/000NN.txt` 에 저장.
status UI 함수가 ingame_text(string_idx) 같은 패턴으로 라벨을 fetch.

이 도구는:
  1. work/h5/converted/text/*.json 파일에서 stat 라벨 string 위치 검색.
  2. 각 라벨이 어느 text-table file 의 어느 offset 에 있는지 출력.

산출: work/h5/analysis/kr_stat_text_locations.tsv
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_DIR = ROOT / "work/h5/converted/text"
OUT = ROOT / "work/h5/analysis/kr_stat_text_locations.tsv"

# 정확한 stat 라벨 (corpus 빈도 분석에서 추출 — 자주 등장하는 라벨)
LABELS = [
    "적중", "회피", "크리티컬", "블록", "속도",
    "공격력", "방어력", "근접공격력", "장거리공격력",
    "마법공격력", "마법방어력", "물리방어력", "마법적중",
    "회복", "정확도", "관통", "반사", "민첩", "회복속도",
    "이동속도", "공격속도",
    "치명타", "치명상", "긴급회피", "액티브블록",
    "정신력", "물리회피", "회피율", "회피능력",
    "근접공격", "장거리공격", "마법공격", "물리방어", "마법방어",
]


def main() -> int:
    if not TEXT_DIR.exists():
        print(f"[!] {TEXT_DIR} 없음")
        return 1

    out_rows = []  # (label, file, offset, full_text)
    summary: dict[str, list[tuple[str, int, str]]] = {l: [] for l in LABELS}

    for json_file in sorted(TEXT_DIR.glob("*.json")):
        if json_file.name == "_corpus.txt":
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            text = entry.get("text", "")
            offset = entry.get("offset", -1)
            if not text:
                continue
            # 정확 매치 (작은 unit, 라벨만 단독)
            for label in LABELS:
                if text == label or text.startswith(label):
                    summary[label].append((json_file.stem, offset, text))
                    out_rows.append((label, json_file.stem, offset, text))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("label\tfile\toffset\tfull_text\n")
        for lbl, fn, off, t in out_rows:
            f.write(f"{lbl}\t{fn}\t{off}\t{t}\n")

    print(f"[+] {OUT}")
    print()
    print("== 라벨별 발견 위치 ==")
    for label in LABELS:
        hits = summary[label]
        if not hits:
            continue
        print(f"\n  {label} ({len(hits)} 건)")
        for fn, off, t in hits[:5]:
            print(f"    file={fn}  offset={off}  text='{t}'")
        if len(hits) > 5:
            print(f"    ... +{len(hits)-5} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
