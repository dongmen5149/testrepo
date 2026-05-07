"""
_scn 의 텍스트/태그 사이 'opcode 세그먼트' 만 떼어내 통계 (2026-05-07).

기존 analyze_scn_opcodes.py 는 모든 비-한국어 byte 를 합친 빈도라 dialogue markup 잡음이 큼.
이 도구는 텍스트 런과 [...] 태그를 명확히 잘라낸 '진짜 opcode 세그먼트' 만 분석한다.

산출:
  work/h3/scn_segment_stats.json
"""
from __future__ import annotations
import json, pathlib
from collections import Counter

SCN_DIR = pathlib.Path('work/extracted/event')


def is_kr_lead(b: int) -> bool:
    return 0xa1 <= b <= 0xfe


def split_segments(data: bytes) -> tuple[list[bytes], list[tuple[int, str]]]:
    """텍스트/태그 영역 사이의 opcode bytes 모음. (segments, run_log[(start,kind)])"""
    segs: list[bytes] = []
    runs: list[tuple[int, str]] = []
    i, n = 0, len(data)
    seg_start = 0
    while i < n:
        if data[i] == 0x5b:
            end = data.find(b']', i + 1)
            if 0 < end - i < 32:
                if seg_start < i:
                    segs.append(data[seg_start:i])
                runs.append((i, 'tag'))
                i = end + 1
                seg_start = i
                continue
        if i + 1 < n and is_kr_lead(data[i]) and is_kr_lead(data[i + 1]):
            if seg_start < i:
                segs.append(data[seg_start:i])
            start = i
            while i + 1 < n and is_kr_lead(data[i]) and is_kr_lead(data[i + 1]):
                i += 2
            runs.append((start, 'text'))
            seg_start = i
            continue
        i += 1
    if seg_start < n:
        segs.append(data[seg_start:])
    return segs, runs


def main() -> int:
    files = sorted(SCN_DIR.glob('*_scn'))
    byte_freq: Counter = Counter()
    pair_freq: Counter = Counter()
    tri_freq: Counter = Counter()
    seg_len_dist: Counter = Counter()
    sentence_modes: Counter = Counter()  # 0x00 [mode] just before text

    total_seg_bytes = 0
    for path in files:
        data = path.read_bytes()
        segs, runs = split_segments(data)
        for seg in segs:
            total_seg_bytes += len(seg)
            byte_freq.update(seg)
            seg_len_dist[len(seg)] += 1
            for k in range(len(seg) - 1):
                pair_freq[(seg[k], seg[k + 1])] += 1
            for k in range(len(seg) - 2):
                tri_freq[(seg[k], seg[k + 1], seg[k + 2])] += 1
        for (start, kind) in runs:
            if kind == 'text' and start >= 2 and data[start - 2] == 0x00:
                sentence_modes[data[start - 1]] += 1

    out = {
        'files_analyzed': len(files),
        'total_segment_bytes': total_seg_bytes,
        'top_bytes': [{'b': f'0x{b:02x}', 'n': c} for b, c in byte_freq.most_common(30)],
        'top_bigrams': [{'b': f'{a:02x} {b:02x}', 'n': c} for (a, b), c in pair_freq.most_common(30)],
        'top_trigrams': [{'b': f'{a:02x} {b:02x} {c:02x}', 'n': n} for (a, b, c), n in tri_freq.most_common(30)],
        'sentence_end_modes': [{'mode': f'0x{b:02x}', 'n': c} for b, c in sentence_modes.most_common()],
        'segment_length_dist_top': [{'len': l, 'n': c} for l, c in seg_len_dist.most_common(20)],
    }
    out_path = pathlib.Path('work/h3/scn_segment_stats.json')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f'analyzed {len(files)} files; total opcode-segment bytes={total_seg_bytes:,}')
    print(f'top 12 opcode bytes: {[(o["b"], o["n"]) for o in out["top_bytes"][:12]]}')
    print(f'top 8 bigrams: {[(o["b"], o["n"]) for o in out["top_bigrams"][:8]]}')
    print(f'top 8 trigrams: {[(o["b"], o["n"]) for o in out["top_trigrams"][:8]]}')
    print(f'sentence_end_modes: {[(o["mode"], o["n"]) for o in out["sentence_end_modes"][:8]]}')
    print(f'segment len top: {[(o["len"], o["n"]) for o in out["segment_length_dist_top"][:10]]}')
    print(f'wrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
