"""_scn 244 파일의 byte-code 통계 분석 — Ghidra 없이 가능한 opcode 후보 추출.

가설: _scn 은 인터프리터형 byte-code. 텍스트 외 영역(EUC-KR 한국어 sequences) 의
바이트들 중 자주 나타나는 단일 byte / 2-byte 시퀀스가 opcode 후보일 가능성.

출력:
  - work/scn_opcode_freq.json — 가장 자주 등장하는 byte / 2-byte
  - stdout: 텍스트 영역 / opcode 영역 비율 추정

사용:
    python analyze_scn_opcodes.py
"""
from __future__ import annotations
import collections, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'
OUT  = ROOT / 'work' / 'scn_opcode_freq.json'


def is_korean_byte_pair(b0: int, b1: int) -> bool:
    """EUC-KR 한국어 영역 (KSC5601) 첫 byte 0xa1-0xfe + 두 번째 byte 0xa1-0xfe."""
    return 0xa1 <= b0 <= 0xfe and 0xa1 <= b1 <= 0xfe


def main():
    if not SCN.exists():
        print(f'  ERROR: {SCN} not found')
        return 1
    files = sorted(SCN.glob('e*_scn'))
    print(f'scn files: {len(files)}')

    byte_freq = collections.Counter()       # opcode 영역만
    pair_freq = collections.Counter()       # opcode 영역 2-byte
    total_bytes = 0
    text_bytes  = 0
    sizes = []

    for f in files:
        data = f.read_bytes()
        sizes.append(len(data))
        total_bytes += len(data)
        # 한국어 byte pair 영역을 텍스트로 분류
        i = 0
        while i < len(data):
            if i + 1 < len(data) and is_korean_byte_pair(data[i], data[i+1]):
                text_bytes += 2
                i += 2
            else:
                byte_freq[data[i]] += 1
                if i + 1 < len(data):
                    pair_freq[(data[i], data[i+1])] += 1
                i += 1

    text_pct = text_bytes / max(1, total_bytes) * 100
    print(f'total: {total_bytes:,} bytes  text(EUC-KR pair): {text_bytes:,} ({text_pct:.1f}%)')
    print(f'avg size: {sum(sizes) // max(1, len(sizes))} bytes')

    print('\nTop 20 single bytes (non-text region):')
    for b, c in byte_freq.most_common(20):
        ascii_ = chr(b) if 32 <= b < 127 else '.'
        print(f'  {b:#04x} ({ascii_})  count={c:,}')

    print('\nTop 20 byte pairs (non-text region):')
    for (a, b), c in pair_freq.most_common(20):
        print(f'  {a:#04x} {b:#04x}  count={c:,}')

    OUT.write_text(json.dumps({
        'files': len(files),
        'total_bytes': total_bytes,
        'text_bytes': text_bytes,
        'text_pct': round(text_pct, 2),
        'top_bytes': [(b, c) for b, c in byte_freq.most_common(64)],
        'top_pairs': [(f'{a:#04x}', f'{b:#04x}', c) for (a, b), c in pair_freq.most_common(64)],
    }, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
