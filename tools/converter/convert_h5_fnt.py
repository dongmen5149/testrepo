"""
Hero5 .fnt (HNF) 폰트 분석.

eng.fnt (1051B) / kor.fnt (12813B):
  magic 'HNF\0' 또는 'HNF\1'
  width, height (각 1B)
  ... (헤더 상세 미확정)
  비트맵 데이터 (각 글리프 = ceil(width/8) × height bytes)

table.dat (4700B):
  EUC-KR 코드포인트(2B BE) → 글리프 인덱스 매핑 추정.
  처음 30+ 항목이 0x8861 (EUC-KR 한글 시작 영역) 부근.

산출 (분석만, 변환은 후속):
  work/h5/analysis/fnt_summary.txt
"""
from __future__ import annotations
import pathlib, struct, csv

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'fnt_summary.txt'


def parse_hnf(data: bytes) -> dict | None:
    if data[:3] != b'HNF':
        return None
    return {
        'magic': data[:3].decode(),
        'version': data[3],
        'width': data[4],
        'height': data[5],
        'header_rest': data[6:32].hex(),
        'glyph_bytes_8bit_aligned': ((data[4] + 7) // 8) * data[5],
        'total_size': len(data),
    }


def main() -> int:
    targets = ['c/font/eng.fnt', 'c/font/kor.fnt', 'c/font/table.dat', 'c/font/type.dat']
    files = {}
    with open(NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['recovered_name'] in targets:
                idx = int(row['index']); h = int(row['hash'], 16)
                files[row['recovered_name']] = ENTRIES / f'{idx:05d}_{h:08x}.bin'

    out = []
    for name, path in files.items():
        d = path.read_bytes()
        out.append(f'\n== {name}  ({len(d)} bytes) ==')
        out.append(f'  first 32B: {d[:32].hex()}')
        if name.endswith('.fnt'):
            info = parse_hnf(d)
            if info:
                gbytes = info['glyph_bytes_8bit_aligned']
                payload = len(d) - 32
                est_chars_32hdr = payload // gbytes if gbytes else 0
                out.append(f'  HNF v{info["version"]}  {info["width"]}×{info["height"]}')
                out.append(f'  glyph_bytes (8-bit aligned): {gbytes}')
                out.append(f'  payload (32B header assumed): {payload} → ~{est_chars_32hdr} chars')

    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out))
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
