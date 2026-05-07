"""
Hero5 .scn (scene/map) 헤더 파서.

근거: `EventProc::Scene_Init @ 000823a8` 디컴파일 (work/h5/analysis/scn_loader.c).
case 0 분기에서 .scn 파일을 로드하고 sequential cursor 로 헤더 11바이트를 파싱한다.

헤더 (11 bytes from offset 0):
  u8 flag1            ; this[0x75] — 시작 플래그
  u8 flag2            ; this[0x74] — 시작 플래그 (특수값 'mmonUiC1Ev' 대응 시 commonUI 모드)
  u8 state            ; this[0x76] — 초기 state (0=normal, 1=commonUI)
  u8 mapID            ; this[0x7c] — Map::LoadData/LoadImage 가 사용하는 인덱스
  u8 dialogID         ; this[0x7e] — Interpreter::Strings::getString 인덱스
  u8 byte_05          ; this[0x7f]
  u8 startX           ; this[0x80] — 플레이어 시작 X
  u8 startY           ; this[0x81] — 플레이어 시작 Y
  u8 startDir         ; this[0x82] — 플레이어 시작 방향
  u8 byte_09          ; this[0x83]
  u8 byte_0a          ; this[0x84]

  ※ flag2 (offset 1) 가 특정 값일 때 case branch — 'mmonUiC1Ev' 매직 비교가 있어
     해당 시 4번째 바이트가 추가 플래그가 되고 cursor가 한 칸 더 진행한다.

이후 11(or 12)바이트부터 끝까지: Interpreter 바이트코드 (이벤트/대사 스크립트).
opcode 정의는 별도 분석 (Interpreter::execute / Token::* 함수 추적 필요).

타일/이미지: .scn 본체엔 없음. mapID 로 `c/map/{face,obj,fgi,tile,seaani}_NN.gbm`
파일이 별도 로드됨 (`Map::LoadData`, `Map::LoadImage`).

산출:
  work/h5/analysis/scn_headers.tsv  — 모든 .scn 파일 헤더 dump
  work/h5/analysis/scn_summary.txt
"""
from __future__ import annotations
import pathlib, csv, struct, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT_TSV = ROOT / 'work' / 'h5' / 'analysis' / 'scn_headers.tsv'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'scn_summary.txt'


def main() -> int:
    # find all assets that are .scn
    scn_entries = []
    with open(NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['recovered_name'].endswith('.scn'):
                scn_entries.append(row)

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    map_id_dist = collections.Counter()
    state_dist = collections.Counter()
    flag2_dist = collections.Counter()
    body_size_dist = collections.Counter()

    for e in scn_entries:
        idx = int(e['index']); h = int(e['hash'], 16)
        p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
        if not p.exists():
            continue
        d = p.read_bytes()
        if len(d) < 11:
            continue

        flag1, flag2, state, mapID, dlgID, b5, sx, sy, sdir, b9, b10 = d[:11]
        body_len = len(d) - 11
        rows.append({
            'index': idx,
            'name': e['recovered_name'],
            'size': len(d),
            'flag1': flag1, 'flag2': flag2, 'state': state,
            'mapID': mapID, 'dialogID': dlgID, 'b5': b5,
            'startX': sx, 'startY': sy, 'startDir': sdir,
            'b9': b9, 'b10': b10,
            'body_len': body_len,
            'body_head_hex': d[11:11+24].hex(),
        })
        map_id_dist[mapID] += 1
        state_dist[state] += 1
        flag2_dist[flag2] += 1
        body_size_dist[body_len // 100 * 100] += 1

    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t')
            w.writeheader()
            for r in rows: w.writerow(r)

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'.scn files parsed: {len(rows)} / {len(scn_entries)}\n\n')
        f.write(f'mapID distribution (top 30):\n')
        for k, v in map_id_dist.most_common(30):
            f.write(f'  {k:3d}  ×{v}\n')
        f.write(f'\nstate (offset 2) distribution:\n')
        for k, v in state_dist.most_common():
            f.write(f'  0x{k:02x}  ×{v}\n')
        f.write(f'\nflag2 (offset 1) top values:\n')
        for k, v in flag2_dist.most_common(20):
            f.write(f'  0x{k:02x}  ×{v}\n')
        f.write(f'\nbody (post-header script) size buckets:\n')
        for k, v in sorted(body_size_dist.items()):
            f.write(f'  {k:6}-{k+99:>6}B  ×{v}\n')

    print(f'parsed {len(rows)} / {len(scn_entries)} .scn files')
    print(f'unique mapIDs: {len(map_id_dist)}, top: {map_id_dist.most_common(10)}')
    print(f'unique states: {len(state_dist)}, top: {state_dist.most_common(5)}')
    print(f'\nfirst 10 entries:')
    for r in rows[:10]:
        print(f'  idx={r["index"]:>5} {r["name"]:>30}  '
              f'mapID={r["mapID"]:3d} st={r["state"]} '
              f'pos=({r["startX"]:3d},{r["startY"]:3d},dir={r["startDir"]}) '
              f'body={r["body_len"]:>5}B')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
