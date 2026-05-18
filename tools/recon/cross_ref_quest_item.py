"""Round 62: i17_dat (퀘스트 아이템 21개) ↔ quest_*_dat (44+ quests) cross-reference.

방법:
  1. i17_dat 21 quest items 추출 (item_decoded.json)
  2. quest_00/01/10/11_dat 의 korean_strings 에서 item name substring grep
  3. 매칭된 quest 의 컨텍스트 (앞뒤 5 strings) 표시
  4. unmatched items 별도 표시 (퀘스트에서 직접 언급되지 않거나 다른 이름으로 등장)

출력 : work/h3/recon/quest_item_xref.{json,log}
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> None:
    item_json = Path("work/h3/recon/item_decoded.json")
    quest_dir = Path("work/h3/converted/dat")
    out_dir = Path("work/h3/recon")

    items_data = json.loads(item_json.read_text(encoding="utf-8"))
    i17 = items_data.get("i17_dat", {}).get("items", [])
    quest_items = [it["name"].strip() for it in i17]

    quest_files = [f for f in sorted(quest_dir.glob("quest_*_dat.json"))]
    quests: dict[str, list[dict]] = {}
    for qf in quest_files:
        quests[qf.stem] = json.loads(qf.read_text(encoding="utf-8")).get("korean_strings", [])

    print("=" * 78)
    print("Round 62 — i17 quest item ↔ quest_*_dat cross-reference")
    print("=" * 78)
    print(f"i17 items   : {len(quest_items)}")
    print(f"quest files : {list(quests)}")

    # Per-item: search all quest files for substring match
    results: dict[str, dict] = {}
    n_matched = 0
    for item_name in quest_items:
        if not item_name or item_name.startswith("'") or item_name.startswith("|"):
            clean = item_name.lstrip("|'$@{}#\"")
        else:
            clean = item_name

        item_result = {
            "clean_name": clean,
            "matches": [],
        }
        for qf, strings in quests.items():
            for i, s in enumerate(strings):
                text = s.get("text", "")
                # match by substring OR by 70%+ char overlap (Korean compounds)
                if clean in text or text in clean and len(text) >= 3:
                    # context = 2 strings before/after
                    ctx_start = max(0, i - 3)
                    ctx_end = min(len(strings), i + 4)
                    ctx = [strings[j].get("text", "") for j in range(ctx_start, ctx_end)]
                    item_result["matches"].append({
                        "file": qf,
                        "offset": s.get("offset"),
                        "text": text,
                        "context": ctx,
                    })
        if item_result["matches"]:
            n_matched += 1
        results[item_name] = item_result

    # Print summary table
    print(f"\nMatched: {n_matched}/{len(quest_items)}")
    print("\n" + "-" * 78)
    for nm, r in results.items():
        ms = r["matches"]
        if not ms:
            print(f"\n[--] {nm:<20} → unmatched (퀘스트 텍스트에서 직접 검색 안됨)")
            continue
        # collapse by file
        by_file: dict[str, list] = {}
        for m in ms:
            by_file.setdefault(m["file"], []).append(m)
        print(f"\n[OK] {nm:<20} → {len(ms)} hit(s) in {len(by_file)} file(s)")
        for qf, mms in by_file.items():
            print(f"   {qf}: {len(mms)} match(es)")
            for m in mms[:2]:  # first 2 contexts
                print(f"     off={m['offset']:>5}  context: {' / '.join(m['context'])}")

    out_path = out_dir / "quest_item_xref.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")

    # second pass: also find "유물/엽서/방패" generic terms in quest files
    print("\n" + "=" * 78)
    print("GENERIC term scan (퀘스트 내 'OO 가져오기' / 'OO 찾기' 패턴)")
    print("=" * 78)
    GENERIC_TERMS = ["가져와", "구해와", "찾아와", "전해줘", "보여줘", "획득"]
    for qf, strings in quests.items():
        hits = []
        for i, s in enumerate(strings):
            text = s.get("text", "")
            for term in GENERIC_TERMS:
                if term in text:
                    ctx_start = max(0, i - 4)
                    ctx_end = min(len(strings), i + 2)
                    ctx = [strings[j].get("text", "") for j in range(ctx_start, ctx_end)]
                    hits.append((s.get("offset"), term, " / ".join(ctx)))
                    break
        if hits:
            print(f"\n{qf}: {len(hits)} fetch/find pattern hit(s)")
            for off, term, ctx in hits[:8]:
                print(f"  off={off:>5}  [{term}] {ctx}")


if __name__ == "__main__":
    main()
