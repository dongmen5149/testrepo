"""
Spirit (class_5) skill description EUC-KR 디코더 (R88 후처리).

`convert_h5_csv.py` 산출 `c_csv_skill_05.json` 의 각 record 에 `desc_text`
필드를 추가한다 (in-place 갱신). 다른 c_csv_skill_*.json 은 별도 변환 도구
(`decode_h5_skill.py`) 가 `skills.json` 에 desc 를 채우므로 처리 대상 아님.

R77 LoadResSkillInfo file layout:
  per-record = stats_area(48B) + desc_string(desc_len B)
  desc_len   = bytes[0x2f]  (sub-rel offset 0x2f)
  desc_bytes = bytes[48 .. 48+desc_len]  (EUC-KR encoded)

R88 검증 결과 (16 spirits): 모두 한국어 desc 추출 가능. 예시:
  spirit #0 암흑탄:  "거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다.;..."
  spirit #2 영혼의회복: "버프 스킬.;사용 즉시;대량의 HP를 회복하고;..."
  spirit #7 정신감응:  "패시브 스킬.;전투시 정령 게이지가;충전되는 양이;}1.5배| 증가한다."

`;` 는 줄바꿈, `}#NN%|` 는 stat placeholder (R75 resolve_skill_desc 가 stats_u16
값으로 치환). spirit 의 stats_u16 layout 은 다른 클래스와 다르므로 placeholder
resolution 은 R89+ 정밀화 대상.

산출:
  apps/hero5-godot/assets/gamedata/c_csv_skill_05.json 의 records 각각에
  "desc_text" 필드 추가 (기존 name/extra_hex 보존).
"""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TARGET = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'c_csv_skill_05.json'

STATS_AREA_SIZE = 48
DESC_LEN_OFFSET = 0x2f


def decode_record(rec: dict) -> str:
    hex_str = rec.get('extra_hex', '')
    if not hex_str:
        return ''
    try:
        b = bytes.fromhex(hex_str)
    except ValueError:
        return ''
    if len(b) <= DESC_LEN_OFFSET:
        return ''
    desc_len = b[DESC_LEN_OFFSET]
    if desc_len == 0:
        return ''
    end = STATS_AREA_SIZE + desc_len
    if end > len(b):
        end = len(b)
    desc_bytes = b[STATS_AREA_SIZE:end]
    try:
        return desc_bytes.decode('euc-kr', errors='replace')
    except Exception:
        return ''


def main(argv: list[str]) -> int:
    if not TARGET.exists():
        print(f'[error] target not found: {TARGET}', file=sys.stderr)
        return 1
    data = json.loads(TARGET.read_text(encoding='utf-8'))
    records = data.get('records', [])
    n_added = 0
    n_empty = 0
    for rec in records:
        desc = decode_record(rec)
        rec['desc_text'] = desc
        if desc:
            n_added += 1
        else:
            n_empty += 1
    TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f'decoded {n_added}/{len(records)} spirit desc → {TARGET.name}'
          f' (empty: {n_empty})')
    # sample 출력
    for i in (0, 7, 15):
        if i < len(records):
            d = records[i].get('desc_text', '')
            d_preview = d[:60].replace('\n', ' ')
            print(f'  #{i:2d} {records[i].get("name", "")}: {d_preview!r}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
