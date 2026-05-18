"""Round 69: dialogue corpus 9,741 unique 대사 LLM 번역 준비 정렬.

R57 발견: H3 dialogue 가 EUC-KR plaintext SCN 350 파일 안. 9,741 unique 텍스트.

R69 작업: LLM 번역 준비 — 우선순위/카테고리 정렬, 빈도+context grouping.

전략:
  1. 빈도 기준 정렬 (top 200 = 게임 핵심 어휘)
  2. 문자수 기준 그룹 (1-2 char = 이름/짧은 단어, 3-10 = 일반, 11+ = 긴 대사)
  3. event 별 그룹 (각 e000X SCN 파일 별 dialogue chunk)
  4. char_count >= 5 unique 만 추출 = 의미있는 대사 (~3,000 entries 추정)
  5. 영어/숫자/특수기호 only 제외

목적: 9,741 → 영어 번역할 ~3,000 entries 우선순위 큐 만들기.

Output: work/h3/translation_queue.{json,log}
"""
import json
import sys
import re
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]


def is_meaningful_korean(text: str) -> bool:
    """Korean dialogue 가 번역할 가치가 있는지 검사."""
    if not text or len(text) < 1:
        return False
    # 한글 character 비율 > 50%
    korean_chars = sum(1 for c in text if 0xac00 <= ord(c) <= 0xd7a3)
    if korean_chars / len(text) < 0.3:
        return False
    return True


def categorize_length(n: int) -> str:
    if n <= 2:
        return "name_or_short"  # 이름/짧은 단어
    if n <= 5:
        return "short_phrase"    # 짧은 구
    if n <= 15:
        return "sentence"        # 일반 문장
    return "long_dialogue"       # 긴 대사


def main() -> None:
    corpus = json.loads((ROOT / "work/h3/converted/dialogue_corpus.json").read_text(encoding="utf-8"))

    # 1. unique text + 빈도
    counter: Counter = Counter()
    text_events: dict = defaultdict(set)
    text_offsets: dict = defaultdict(list)
    for line in corpus["lines"]:
        t = line.get("text", "").strip()
        if not t:
            continue
        counter[t] += 1
        text_events[t].add(line.get("event", ""))
        text_offsets[t].append((line.get("event", ""), line.get("offset", 0)))

    # 2. filter meaningful
    meaningful: list[dict] = []
    for text, count in counter.most_common():
        if not is_meaningful_korean(text):
            continue
        meaningful.append({
            "text": text,
            "count": count,
            "char_count": len(text),
            "n_events": len(text_events[text]),
            "events": sorted(text_events[text])[:5],
            "length_category": categorize_length(len(text)),
        })

    # 3. group by length category
    by_category: dict = defaultdict(list)
    for entry in meaningful:
        by_category[entry["length_category"]].append(entry)

    # 4. event-by-event grouping (각 SCN 파일 별 대사)
    by_event: dict = defaultdict(list)
    for line in corpus["lines"]:
        t = line.get("text", "").strip()
        if not is_meaningful_korean(t):
            continue
        by_event[line.get("event", "")].append({
            "offset": line.get("offset", 0),
            "text": t,
            "char_count": len(t),
        })

    # 5. translation priority queue
    priority_queue = sorted(
        [e for e in meaningful if e["char_count"] >= 2],
        key=lambda x: (-x["count"], -x["char_count"])
    )

    out = {
        "doc": "Round 69: Hero3 dialogue corpus translation queue",
        "stats": {
            "total_lines": corpus["total_lines"],
            "unique_texts": corpus["unique_texts"],
            "meaningful_unique": len(meaningful),
            "filtered_out": corpus["unique_texts"] - len(meaningful),
        },
        "categorization": {
            cat: {"count": len(items), "total_chars": sum(e["char_count"] for e in items)}
            for cat, items in by_category.items()
        },
        "event_count": len(by_event),
        "priority_queue_top_50": priority_queue[:50],
        "priority_queue_total": len(priority_queue),
        "estimated_translation_cost": {
            "char_count_total": sum(e["char_count"] for e in priority_queue),
            "estimated_tokens_korean": sum(e["char_count"] for e in priority_queue) * 2,
            "estimated_tokens_english": sum(e["char_count"] for e in priority_queue) * 2,
            "rough_cost_usd_at_0_03_per_1k": (sum(e["char_count"] for e in priority_queue) * 4 / 1000) * 0.03,
            "note": "Claude Sonnet 4.6 가격 기준 추정",
        },
    }

    out_path = ROOT / "work/h3/translation_queue.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 dialogue translation queue (R69) =====\n")
    log_lines.append(f"Stats:")
    for k, v in out["stats"].items():
        log_lines.append(f"  {k}: {v:,}")

    log_lines.append(f"\nLength categorization:")
    for cat, info in by_category.items():
        log_lines.append(f"  {cat:<20} {len(info):>6} entries, {sum(e['char_count'] for e in info):>10,} total chars")

    log_lines.append(f"\nEvent count: {len(by_event)} unique SCN files")

    log_lines.append(f"\nPriority queue: top 30 (most frequent meaningful Korean)")
    for i, e in enumerate(priority_queue[:30], 1):
        log_lines.append(f"  {i:>3}. {e['text']:<25} count={e['count']:>4} chars={e['char_count']:>3} events={len(e['events'])}")

    log_lines.append(f"\nEstimated translation cost:")
    for k, v in out["estimated_translation_cost"].items():
        if isinstance(v, (int, float)):
            log_lines.append(f"  {k}: {v:,.2f}" if isinstance(v, float) else f"  {k}: {v:,}")
        else:
            log_lines.append(f"  {k}: {v}")

    log_path = ROOT / "work/h3/translation_queue.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"  Meaningful Korean unique: {len(meaningful):,} / {corpus['unique_texts']:,}")
    print(f"  Priority queue:           {len(priority_queue):,}")
    print(f"  Total chars to translate: {sum(e['char_count'] for e in priority_queue):,}")
    print(f"  Estimated cost: ${out['estimated_translation_cost']['rough_cost_usd_at_0_03_per_1k']:.2f} (Claude Sonnet 4.6)")


if __name__ == "__main__":
    main()
