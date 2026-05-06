"""
Hero5 VFS .bin 포맷 호환성 프로브.

work/h5/vfs_entries/*.bin 각 파일에 대해:
  1) 첫 4바이트 매직 / 크기 통계 수집
  2) Hero3/4 파서들(_txt, _pa, _mp, _bm, _cif)을 try-except 로 적용
  3) 매트릭스 TSV + 요약 리포트 출력

산출:
  work/h5/analysis/bin_probe_matrix.tsv
  work/h5/analysis/bin_probe_summary.txt
"""
from __future__ import annotations
import sys, struct, pathlib, traceback, collections, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'converter'))

from convert_text import parse_text_table  # noqa
from convert_palette import parse_palette  # noqa
from convert_mp import parse_mp  # noqa
from convert_cif import parse_cif  # noqa
from convert_bm_v2 import find_frame_markers  # noqa


VFS_DIR = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT_DIR = ROOT / 'work' / 'h5' / 'analysis'


def try_txt(data: bytes) -> tuple[bool, str]:
    if len(data) < 4:
        return False, 'too short'
    declared = struct.unpack_from('<H', data, 0)[0]
    count = struct.unpack_from('<H', data, 2)[0]
    if declared != len(data):
        return False, f'size mismatch {declared}!={len(data)}'
    if count == 0 or 4 + count * 2 > len(data):
        return False, 'count out of range'
    try:
        ss = parse_text_table(data)
        # at least one non-empty string
        if any(s.strip() for s in ss):
            return True, f'{count} strings'
        return False, 'all-empty'
    except Exception as e:
        return False, str(e)[:40]


def try_pa(data: bytes) -> tuple[bool, str]:
    if len(data) < 5:
        return False, 'too short'
    count = data[0]
    if count == 0 or count > 64:
        return False, f'count {count}'
    if len(data) != count * 4 + 1:
        return False, f'size {len(data)} != {count*4+1}'
    return True, f'{count} colors'


def try_mp(data: bytes) -> tuple[bool, str]:
    if len(data) < 10:
        return False, 'too short'
    if data[0] not in (0x02, 0x03):
        return False, f'ver {data[0]:#x}'
    try:
        m = parse_mp(data)
        return True, f"v{data[0]} {m['width']}x{m['height']} '{m['name']}'"
    except Exception as e:
        return False, str(e)[:40]


def try_bm(data: bytes) -> tuple[bool, str]:
    markers = find_frame_markers(data)
    if not markers:
        return False, 'no 1f f8 markers'
    return True, f'{len(markers)} frames'


def try_cif(data: bytes) -> tuple[bool, str]:
    # weak signature: slot_count<=8 and has 19 19 marker
    if len(data) < 4:
        return False, 'too short'
    slot_count = data[0]
    if slot_count > 8:
        return False, f'slots {slot_count}'
    has_1919 = b'\x19\x19' in data
    if has_1919 and slot_count <= 8:
        return True, f'slots={slot_count} has 19 19'
    return False, 'no 19 19 marker'


def try_ogg(data: bytes) -> tuple[bool, str]:
    if data[:4] == b'OggS':
        return True, 'OggS'
    return False, ''


def try_smaf(data: bytes) -> tuple[bool, str]:
    if data[:4] == b'MMMD':
        return True, 'MMMD (SMAF)'
    return False, ''


PROBES = [
    ('ogg', try_ogg),
    ('smaf', try_smaf),
    ('txt', try_txt),
    ('pa', try_pa),
    ('mp', try_mp),
    ('bm', try_bm),
    ('cif', try_cif),
]


def main() -> int:
    files = sorted(VFS_DIR.glob('*.bin'))
    if not files:
        print('no .bin files found', file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = OUT_DIR / 'bin_probe_matrix.tsv'
    summary_path = OUT_DIR / 'bin_probe_summary.txt'

    magic_counter: collections.Counter = collections.Counter()
    fmt_hits: dict[str, int] = {n: 0 for n, _ in PROBES}
    fmt_examples: dict[str, list[str]] = {n: [] for n, _ in PROBES}
    unmatched = 0
    multi_match = 0

    with open(matrix_path, 'w', encoding='utf-8', newline='') as fmat:
        fmat.write('file\tsize\tmagic4_hex\t' + '\t'.join(n for n, _ in PROBES) + '\tdetails\n')
        for path in files:
            data = path.read_bytes()
            magic = data[:4].hex() if len(data) >= 4 else data.hex()
            magic_counter[magic] += 1

            results: list[str] = []
            details: list[str] = []
            hits = 0
            for name, fn in PROBES:
                ok, msg = fn(data)
                results.append('1' if ok else '0')
                if ok:
                    hits += 1
                    fmt_hits[name] += 1
                    if len(fmt_examples[name]) < 5:
                        fmt_examples[name].append(f'{path.name}: {msg}')
                    details.append(f'{name}={msg}')
            if hits == 0:
                unmatched += 1
            elif hits > 1:
                multi_match += 1

            fmat.write(f'{path.name}\t{len(data)}\t{magic}\t' + '\t'.join(results) + '\t' + '; '.join(details) + '\n')

    with open(summary_path, 'w', encoding='utf-8') as fs:
        fs.write(f'total bin files: {len(files)}\n')
        fs.write(f'unmatched: {unmatched}\n')
        fs.write(f'multi-match: {multi_match}\n\n')
        fs.write('format hit counts:\n')
        for name, cnt in fmt_hits.items():
            pct = 100.0 * cnt / len(files)
            fs.write(f'  {name:6s} {cnt:6d}  ({pct:5.1f}%)\n')
        fs.write('\ntop 30 magic4 prefixes:\n')
        for magic, cnt in magic_counter.most_common(30):
            fs.write(f'  {magic}  {cnt:6d}\n')
        fs.write('\nsample matches per format:\n')
        for name, examples in fmt_examples.items():
            fs.write(f'  [{name}]\n')
            for ex in examples:
                fs.write(f'    {ex}\n')

    print(f'wrote {matrix_path}')
    print(f'wrote {summary_path}')
    print()
    print(open(summary_path, encoding='utf-8').read())
    return 0


if __name__ == '__main__':
    sys.exit(main())
