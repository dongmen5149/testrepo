"""
Hero5 TINY_META (5–48B residual) 파서.

구조 (PROGRESS 6.2 [P2] 가설 검증 결과):
  u16 total_record_count   (LE)  ; 헤더 1 + body N = total
  u16 record_kind          (LE)  ; 보통 0x0005
  u8  0x05                       ; prefix marker
  u8  body_count                 ; = total_record_count - 1
  u8[3] prefix_payload           ; 보통 ff ff ff
  body_count × {
      u8  0x05                   ; row marker
      u8  0x00                   ; row sub-type
      u8[5] payload              ; 0xff = empty slot, 0x2a-0x2d = field markers
  }

표본 검증:
  00075_575679e3.bin (30B) — header (4 0x0005), prefix(5B), 3×7B = 30 ✓
  00077_577aaae5.bin (44B) — header (6 0x0005), prefix(5B), 5×7B = 44 ✓
  00078_578cc366.bin (30B) — header (4 0x0005), prefix(5B), 3×7B = 30 ✓

용도 추정:
  payload 의 5 슬롯이 "프레임 i 의 hitbox/offset/anim_index" 같은 정형 필드 5개.
  0xff 는 미사용, 0x2a-0x2d 는 field-id 인덱스 (anim 시스템 enum 추정).
  → 각 row = 1 frame 의 메타. body_count = frame 수.

산출:
  work/h5/analysis/tiny_meta.tsv
  work/h5/analysis/tiny_meta_summary.txt
"""
from __future__ import annotations
import pathlib, struct, csv, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT_TSV = ROOT / 'work' / 'h5' / 'analysis' / 'tiny_meta.tsv'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'tiny_meta_summary.txt'


def parse(data: bytes):
    """
    Layout:
      u16 total_count
      u16 kind                                    ; row payload width
      prefix row: <kind> bytes
        [0]=kind, [1]=body_count, [2:]=prefix_payload (kind-2 bytes)
      body_count rows × (kind+2) bytes each
        [0]=kind, [1]=subtype (usually 0x00), [2:]=payload (kind bytes)
    Total file size: 4 + kind + body_count * (kind+2)
    """
    if len(data) < 8: return None
    total, kind = struct.unpack_from('<HH', data, 0)
    if total < 2 or total > 50: return None
    if kind < 3 or kind > 16: return None
    if 4 + kind > len(data): return None
    if data[4] != kind: return None
    body_count = data[5]
    if body_count != total - 1: return None
    prefix_payload = bytes(data[6:4 + kind])
    body_off = 4 + kind
    row_size = kind + 2
    expected = body_off + body_count * row_size
    if len(data) != expected: return None
    rows = []
    for i in range(body_count):
        r = data[body_off + i*row_size : body_off + (i+1)*row_size]
        if r[0] != kind: return None
        rows.append(r)
    return {
        'total': total, 'kind': kind,
        'body_count': body_count, 'prefix': prefix_payload,
        'rows': rows,
    }


def fmt_row(r: bytes) -> str:
    return ' '.join(f'{b:02x}' for b in r)


def main() -> int:
    # Load catalog to know which residual files are TINY_META candidates (size <= 50, type=bin)
    candidates: list[pathlib.Path] = []
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['type'] != 'bin': continue
            length = int(row['length'])
            if not (5 <= length <= 50): continue
            idx = int(row['index'])
            h = int(row['hash'], 16)
            p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
            if p.exists(): candidates.append(p)

    parsed = []
    failed = 0
    field_counter = collections.Counter()
    body_count_dist = collections.Counter()
    kind_dist = collections.Counter()

    for p in candidates:
        d = p.read_bytes()
        r = parse(d)
        if r is None:
            failed += 1; continue
        parsed.append((p, r))
        body_count_dist[r['body_count']] += 1
        kind_dist[r['kind']] += 1
        for row in r['rows']:
            for b in row[2:]:
                field_counter[b] += 1

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        f.write('file\ttotal\tkind\tbody_count\tprefix_payload\trow_idx\trow_payload\n')
        for p, r in parsed:
            for i, row in enumerate(r['rows']):
                f.write(f'{p.name}\t{r["total"]}\t0x{r["kind"]:04x}\t'
                        f'{r["body_count"]}\t{r["prefix"].hex()}\t'
                        f'{i}\t{row[2:].hex()}\n')

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'TINY_META parser results\n')
        f.write(f'================================\n')
        f.write(f'candidates (5–50B bin):     {len(candidates)}\n')
        f.write(f'parsed successfully:        {len(parsed)} ({100*len(parsed)/max(1,len(candidates)):.1f}%)\n')
        f.write(f'failed structural checks:   {failed}\n\n')
        f.write(f'body_count distribution (frames per record):\n')
        for k, v in sorted(body_count_dist.items()):
            f.write(f'  {k:3d} frames  ×  {v} files\n')
        f.write(f'\nkind word distribution:\n')
        for k, v in kind_dist.most_common():
            f.write(f'  0x{k:04x}  ×  {v}\n')
        f.write(f'\npayload byte frequency (top 30):\n')
        for b, v in field_counter.most_common(30):
            f.write(f'  0x{b:02x}  ×  {v}\n')

    print(f'parsed {len(parsed)}/{len(candidates)} TINY_META files '
          f'({100*len(parsed)/max(1,len(candidates)):.1f}%)')
    print(f'failed: {failed}')
    print(f'body_count distribution: {dict(sorted(body_count_dist.items()))}')
    print(f'kind distribution: {dict(kind_dist.most_common(5))}')
    print(f'\ntop payload bytes:')
    for b, v in field_counter.most_common(15):
        print(f'  0x{b:02x}  x{v}')
    print(f'\nwrote {OUT_TSV}')
    print(f'wrote {OUT_SUM}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
