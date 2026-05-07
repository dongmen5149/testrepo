"""
class.dat stat 필드 디코더.

class.dat 의 5 records (워리어/로그/...) extra 59B 분석으로 추정:
  u16 STR
  u16 DEX
  u16 INT
  u16 CON
  u16 padding[4]    (모두 0)
  u16 base_hp_? = 5 / 50 / 0 / ...  (offset 16 ~)
  u16 base_mp_?
  u16 max_level    = 60
  u16 ?
  u16 starting_gold = 1000 (e803)
  u16 spr_idx?
  ...

  (정확한 매핑은 hero_char.c 의 BATTLER::Init 함수 추가 분석 필요)

산출:
  apps/hero5-godot/assets/gamedata/class_stats.json
"""
from __future__ import annotations
import pathlib, json, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'c_csv_class.json'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'class_stats.json'

FIELD_NAMES = [
    'STR', 'DEX', 'INT', 'CON',
    'pad0', 'pad1', 'pad2', 'pad3',
    'base_hp', 'base_mp', 'max_lvl', 'spr_id',
    'starting_gold', 'init_skill_id',
    'unk0', 'unk1', 'unk2', 'unk3',
    'unk4', 'unk5', 'unk6', 'unk7',
    'unk8', 'unk9', 'unk10', 'unk11',
    'unk12', 'unk13', 'unk14',
]


def main() -> int:
    src = json.loads(SRC.read_text(encoding='utf-8'))
    out = []
    for r in src['records']:
        b = bytes.fromhex(r['extra_hex'])
        # 59 bytes — pad to 60 for 30 u16
        if len(b) % 2 == 1:
            b += b'\x00'
        u16 = list(struct.unpack(f'<{len(b)//2}H', b))
        rec = {'name': r['name']}
        for i, val in enumerate(u16):
            field = FIELD_NAMES[i] if i < len(FIELD_NAMES) else f'u{i}'
            rec[field] = val
        out.append(rec)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'decoded {len(out)} class records → {OUT}')
    for r in out:
        print(f'  {r["name"]:6}  STR={r["STR"]:3} DEX={r["DEX"]:3} INT={r["INT"]:3} CON={r["CON"]:3}'
              f'  HP={r["base_hp"]:3} MP={r["base_mp"]:3} gold={r["starting_gold"]:5}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
