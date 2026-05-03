"""_scn v2 변환 — 화자 태그 + 대사 시작 opcode 인식하여 (speaker, mode, text) 트리플 추출.

2026-05-04 분석 결과:
  [name]   — 0x5b ... 0x5d 화자 태그
  0x00 [mode]  — 직전 sentence-end 다음에 오는 "다음 대사 시작" opcode
                 mode ∈ {0x7c, 0x27, 0x24, 0x7b}

이 v2 는 텍스트뿐만 아니라 화자/모드 분리까지 추출.

사용:
    python convert_scn_v2.py <input_dir> <output_dir>
"""
from __future__ import annotations
import json, pathlib, sys, re


def is_kr_lead(b: int) -> bool: return 0xa1 <= b <= 0xfe


def parse_scn(data: bytes) -> dict:
    """화자/모드/대사 트리플 + 미분류 opcode 영역 보존."""
    entries = []
    i = 0
    n = len(data)
    current_speaker = None
    while i < n:
        # 화자 태그
        if data[i] == 0x5b:
            end = data.find(b']', i + 1)
            if end > 0 and end - i < 32:
                try:
                    spk = data[i+1:end].decode('euc-kr')
                    current_speaker = spk
                except UnicodeDecodeError:
                    pass
                i = end + 1
                continue
        # 한국어 텍스트 런
        if i + 1 < n and is_kr_lead(data[i]) and is_kr_lead(data[i+1]):
            start = i
            while i + 1 < n and is_kr_lead(data[i]) and is_kr_lead(data[i+1]):
                i += 2
            try:
                text = data[start:i].decode('euc-kr')
            except UnicodeDecodeError:
                continue
            mode = None
            # offset start-2: 0x00 [mode]
            if start >= 2 and data[start-2] == 0x00:
                mode = data[start-1]
            entries.append({
                'offset': hex(start),
                'speaker': current_speaker,
                'mode_byte': f'{mode:#04x}' if mode is not None else None,
                'text': text,
            })
            continue
        i += 1
    return {'entries': entries, 'count': len(entries)}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src = pathlib.Path(argv[1])
    dst = pathlib.Path(argv[2])
    files = sorted(src.glob('e*_scn'))
    if not files:
        print(f'  no scn files in {src}'); return 1
    dst.mkdir(parents=True, exist_ok=True)
    total_entries = 0
    speaker_dist: dict[str, int] = {}
    mode_dist: dict[str, int] = {}
    for f in files:
        out = dst / f'{f.stem}.json'
        info = parse_scn(f.read_bytes())
        out.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
        total_entries += info['count']
        for e in info['entries']:
            s = e.get('speaker') or '(none)'
            speaker_dist[s] = speaker_dist.get(s, 0) + 1
            m = e.get('mode_byte') or '(none)'
            mode_dist[m] = mode_dist.get(m, 0) + 1

    summary = {
        'files': len(files),
        'total_entries': total_entries,
        'top_speakers': sorted(speaker_dist.items(), key=lambda x: -x[1])[:30],
        'mode_distribution': dict(sorted(mode_dist.items(), key=lambda x: -x[1])),
    }
    (dst / '_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                       encoding='utf-8')
    print(f'wrote {len(files)} files + summary to {dst}')
    print(f'total entries: {total_entries}')
    print(f'top speakers:')
    for s, c in summary['top_speakers'][:15]:
        print(f'  {c:5d}  {s}')
    print(f'\nmode distribution:')
    for m, c in summary['mode_distribution'].items():
        print(f'  {m}: {c}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
