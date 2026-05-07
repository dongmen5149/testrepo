"""
Hero5 c/map/(md)NN 맵 데이터 파일 파서.

근거: `Map::LoadData @ 0x000c5f14` (work/h5/analysis/map_init.c) +
header u16 dump (idx 184 = (md)00).

파일 구조:
  헤더 96 bytes (0x60):
    u16  size_marker        ; offset 0x00 (e.g. 15428)
    u16  param0..param4     ; offset 0x02..0x0a (5개 메타 필드, mapW/H/layers 추정)
    u16  case1[4]           ; offset 0x0c..0x12 → enemy/event records 갯수
    u16  case2[4]           ; offset 0x14..0x1a → npc/object records 갯수
    u32  section_offsets[]  ; offset 0x1c.. — 파일 내 섹션 시작 위치 표

  바디: 섹션 데이터 (offsets[i]..offsets[i+1] = 섹션 i 의 바이트 범위).

산출:
  work/h5/analysis/mapdata_index.tsv — 파일별 섹션 분포
  work/h5/analysis/mapdata_summary.txt
"""
from __future__ import annotations
import pathlib, struct, csv, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT_TSV = ROOT / 'work' / 'h5' / 'analysis' / 'mapdata_index.tsv'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'mapdata_summary.txt'


def parse(d: bytes) -> dict | None:
    if len(d) < 96: return None
    h_u16 = struct.unpack_from('<6H', d, 0)
    case1 = struct.unpack_from('<4H', d, 0x0c)
    case2 = struct.unpack_from('<4H', d, 0x14)
    # section offsets: u32 from 0x1c to 0x60
    n_off = (0x60 - 0x1c) // 4
    offs = list(struct.unpack_from(f'<{n_off}I', d, 0x1c))
    # filter: keep only valid (monotonic, in-bounds) section offsets
    valid = [o for o in offs if 96 <= o <= len(d)]
    valid_sorted = sorted(set(valid))
    sections = []
    for i, start in enumerate(valid_sorted):
        end = valid_sorted[i+1] if i+1 < len(valid_sorted) else len(d)
        sections.append((start, end, end - start))
    return {
        'size': len(d),
        'header_meta': h_u16,
        'case1': case1, 'case2': case2,
        'raw_offsets': offs,
        'sections': sections,
    }


def main() -> int:
    md_files = []
    with open(NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if '(md)' in row['recovered_name']:
                md_files.append(row)
    print(f'(md)NN files: {len(md_files)}')

    parsed = []
    section_counts = collections.Counter()
    section_sizes = collections.Counter()
    for r in md_files:
        idx = int(r['index']); h = int(r['hash'], 16)
        p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
        if not p.exists(): continue
        info = parse(p.read_bytes())
        if not info: continue
        info['name'] = r['recovered_name']; info['index'] = idx
        parsed.append(info)
        section_counts[len(info['sections'])] += 1
        for s in info['sections']:
            sb = s[2] // 1000 * 1000
            section_sizes[sb] += 1

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        f.write('index\tname\tsize\thdr_meta\tcase1_sum\tcase2_sum\tn_sections\tlargest_section\n')
        for i in parsed:
            largest = max((s[2] for s in i['sections']), default=0)
            f.write(f'{i["index"]}\t{i["name"]}\t{i["size"]}\t'
                    f'{",".join(str(x) for x in i["header_meta"])}\t'
                    f'{sum(i["case1"])}\t{sum(i["case2"])}\t'
                    f'{len(i["sections"])}\t{largest}\n')

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'(md) map files: {len(parsed)}\n\n')
        f.write(f'sections per file distribution:\n')
        for k, v in sorted(section_counts.items()):
            f.write(f'  {k} sections  ×{v}\n')
        f.write(f'\nsection size distribution (1KB buckets):\n')
        for k, v in sorted(section_sizes.items()):
            f.write(f'  {k:>6}-{k+999:>6}B  ×{v}\n')
        f.write(f'\nfirst 5 files breakdown:\n')
        for i in parsed[:5]:
            f.write(f'\n  {i["name"]} (size {i["size"]}):\n')
            f.write(f'    header_meta: {i["header_meta"]}\n')
            f.write(f'    case1 sum={sum(i["case1"])} case2 sum={sum(i["case2"])}\n')
            f.write(f'    sections ({len(i["sections"])}):\n')
            for j, (a, b, sz) in enumerate(i['sections']):
                f.write(f'      [{j}] {a}..{b} ({sz}B)\n')

    print(f'parsed {len(parsed)} files')
    print(f'sections per file: {dict(sorted(section_counts.items()))}')
    print(f'wrote {OUT_TSV}')
    print(f'wrote {OUT_SUM}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
