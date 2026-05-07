"""
skill_NN.dat 분석. 가변사이즈 record 의 첫 부분 stat 추출 + Korean 설명 분리.

확인된 record 구조 (변동):
  u16 type/category   (3=basic, 4=charge, 7=down, ...)
  u16 unk1
  u16 unk2
  u16 flags (= 0x0868 모든 skill 공통, 아이콘 카테고리?)
  u16 unk4
  u16 mp_cost? (가변)
  u16 anim/icon (= 0x5d 공통)
  ... 추가 stat
  EUC-KR 한글 설명 (마지막 부분)

산출:
  apps/hero5-godot/assets/gamedata/skills.json — 각 클래스의 skill 통합
"""
from __future__ import annotations
import json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GAMEDATA = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata'
OUT = GAMEDATA / 'skills.json'


def split_stats_desc(b: bytes) -> tuple[list[int], str]:
    """첫 u16 들 (stat) + 끝 EUC-KR 한글 설명 분리."""
    # 한글 시작 위치 = 첫 EUC-KR 한글 byte (high byte 0xb0..0xc8)
    desc_start = -1
    for i in range(len(b) - 1):
        hi = b[i]
        lo = b[i + 1]
        if 0xb0 <= hi <= 0xc8 and 0xa1 <= lo <= 0xfe:
            # check that next 3 chars are also EUC-KR Hangul
            ok = True
            for j in range(2, 8, 2):
                if i + j + 1 >= len(b): break
                if not (0xb0 <= b[i+j] <= 0xc8 and 0xa1 <= b[i+j+1] <= 0xfe):
                    if b[i+j] not in (0x20, 0x3b, 0x7b, 0x7c, 0x7d, 0x23):
                        ok = False
                        break
            if ok:
                desc_start = i
                break
    if desc_start < 0:
        desc_start = len(b)
    stats_bytes = b[:desc_start]
    desc_bytes = b[desc_start:]
    n_u16 = len(stats_bytes) // 2
    stats = list(struct.unpack(f'<{n_u16}H', stats_bytes[:n_u16*2])) if n_u16 else []
    try:
        desc = desc_bytes.decode('euc-kr', errors='replace')
    except Exception:
        desc = ''
    return stats, desc


def main() -> int:
    out = {}
    for class_id in range(5):
        src = GAMEDATA / f'c_csv_skill_{class_id:02d}.json'
        if not src.exists(): continue
        data = json.loads(src.read_text(encoding='utf-8'))
        skills = []
        for r in data['records']:
            b = bytes.fromhex(r['extra_hex'])
            stats, desc = split_stats_desc(b)
            skills.append({
                'name': r['name'],
                'type': stats[0] if stats else 0,
                'stats_u16': stats[:8],
                'desc': desc.strip(),
            })
        out[f'class_{class_id}'] = skills

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT}')
    for cls, skills in out.items():
        print(f'\n{cls}: {len(skills)} skills')
        for s in skills[:5]:
            short_desc = s['desc'][:40].replace('\n', ' ').replace(';', '|')
            print(f'  type={s["type"]:>3}  {s["name"]:10}  {short_desc}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
