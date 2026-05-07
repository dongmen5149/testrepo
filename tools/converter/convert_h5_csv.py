"""
Hero5 c/csv/*.dat 게임 데이터 테이블 파서.

확정된 포맷 (클래스/스킬/아이템/이름/대사 등 모든 .dat 공통):
  u16 record_count
  records[count]:
    u16 record_size   ; (strlen byte + string bytes + extra data) 의 총 크기
    u8  strlen        ; EUC-KR 문자열 바이트 수
    bytes[strlen]     ; EUC-KR 인코딩 문자열 (이름/설명)
    bytes[record_size - 1 - strlen]  ; 통계/플래그 등 binary data

검증 (name.dat 569B): 63 records of mostly small (5-9 byte) entries with
캐릭터 이름 (없음/슈르츠/렌/티아나/...).
검증 (common_text.dat 6228B): 355 records with UI 라벨 (캐릭터/가방/장비/...).

산출:
  apps/hero5-godot/assets/text/<filename>.json — JSON {records: [{name, extra_hex}]}
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT_DIR = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata'


def parse_dat(d: bytes) -> list[dict]:
    if len(d) < 2: return []
    count = struct.unpack_from('<H', d, 0)[0]
    pos = 2
    records = []
    for _ in range(count):
        if pos + 3 > len(d): break
        rec_size = struct.unpack_from('<H', d, pos)[0]
        pos += 2
        if pos + rec_size > len(d): break
        body_start = pos
        strlen = d[pos]
        pos += 1
        if strlen > rec_size - 1:
            # malformed
            pos = body_start + rec_size
            records.append({'name': '', 'extra_hex': ''})
            continue
        try:
            name = d[pos:pos + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        pos += strlen
        extra_len = rec_size - 1 - strlen
        extra = d[pos:pos + extra_len]
        pos += extra_len
        records.append({
            'name': name,
            'extra_hex': extra.hex(),
        })
    return records


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = []
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            n = r['recovered_name']
            if (n.startswith('c/csv/') or n.startswith('c/csv2/')) and n.endswith('.dat'):
                targets.append(r)

    summary = []
    for r in targets:
        p = ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"], 16):08x}.bin'
        if not p.exists(): continue
        recs = parse_dat(p.read_bytes())
        # output filename: replace / with _
        out_name = r['recovered_name'].replace('/', '_').replace('.dat', '.json')
        (OUT_DIR / out_name).write_text(
            json.dumps({'count': len(recs), 'records': recs}, ensure_ascii=False, indent=2),
            encoding='utf-8')
        summary.append((r['recovered_name'], len(recs)))

    # write index
    (OUT_DIR / '_index.json').write_text(
        json.dumps({'tables': summary}, ensure_ascii=False, indent=2),
        encoding='utf-8')

    print(f'parsed {len(summary)} csv .dat tables → {OUT_DIR}')
    print(f'top by record count:')
    for name, n in sorted(summary, key=lambda x: -x[1])[:10]:
        print(f'  {n:5d}  {name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
