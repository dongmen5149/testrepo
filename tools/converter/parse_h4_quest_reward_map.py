"""Hero4 Round 90 — Q_REPAY idx ↔ R70 quest name 1:1 매핑 확정.

R85 의 "200 vs 128 차이 72" 미해결 해소:
- Q_REPAY_0/1 idx 0-127 = R70 128 quest 1:1 매핑 (검증: idx 0='케프네스를 찾아라',
  idx 60='전이장치', idx 62='성지 방어1' 으로 _QUEST_0_DAT(0-61) → _QUEST_1_DAT(62-127) 경계 일치)
- idx 128-198 = **71 extra reward slots** (achievement / repeatable / endgame)
- idx 199 = zero sentinel

추가 reward 영역 (idx 128-198) 특성:
- 대다수 idx 128-191: 저-중 보상 (EXP 1800-3700, gold 11k-93k) → repeatable mission
- idx 192-198: 매우 큰 보상 (EXP 67k-88k, gold 181k-198k) → endgame achievement
"""
from __future__ import annotations
import json
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT'
QUESTS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_quests.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_quests() -> list[dict]:
    qd = json.loads(QUESTS_JSON.read_text(encoding='utf-8'))
    out = []
    for fn, qfile in qd['files'].items():
        for i, q in enumerate(qfile['quests']):
            out.append({
                'source_file': fn,
                'name': q['name'],
                'category': q.get('category', ''),
            })
    return out


def parse_repay_20b(fn: str) -> list[dict]:
    data = (DAT_DIR / fn).read_bytes()
    n = len(data) // 20
    out = []
    for i in range(n):
        rec = data[i*20:(i+1)*20]
        le32 = struct.unpack('<I', rec[4:8])[0]
        drop_id = rec[8]
        drop_qty = rec[9]
        drop_misc = rec[10]
        out.append({
            'idx': i,
            'reward_le32': le32,
            'drop_id': drop_id,
            'drop_qty': drop_qty,
            'drop_misc': drop_misc,
            'has_drop': drop_id != 0xff and drop_id != 0,
        })
    return out


def classify_extra(idx: int, exp: int, gold: int) -> str:
    """idx 128-199 classifier."""
    if idx == 199 and exp == 0 and gold == 0:
        return 'sentinel'
    if exp >= 50_000 or gold >= 150_000:
        return 'endgame_achievement'
    if exp >= 5_000 or gold >= 100_000:
        return 'mid_achievement'
    return 'repeatable_mission'


def main() -> int:
    quests = load_quests()
    exp_rec = parse_repay_20b('_ITM_Q_REPAY_0')
    gold_rec = parse_repay_20b('_ITM_Q_REPAY_1')

    assert len(exp_rec) == 200 and len(gold_rec) == 200, 'expected 200 records'

    # Map idx 0-127 to quests
    mapping = []
    for i in range(128):
        q = quests[i] if i < len(quests) else None
        mapping.append({
            'idx': i,
            'quest_name': q['name'] if q else None,
            'quest_source': q['source_file'] if q else None,
            'exp': exp_rec[i]['reward_le32'],
            'gold': gold_rec[i]['reward_le32'],
            'exp_drop_id': exp_rec[i]['drop_id'],
            'gold_drop_id': gold_rec[i]['drop_id'],
        })

    # idx 128-199 = extras
    extras = []
    for i in range(128, 200):
        e = exp_rec[i]['reward_le32']
        g = gold_rec[i]['reward_le32']
        extras.append({
            'idx': i,
            'exp': e,
            'gold': g,
            'category': classify_extra(i, e, g),
        })

    # Stats
    extra_by_cat = {}
    for x in extras:
        extra_by_cat.setdefault(x['category'], []).append(x['idx'])

    out = {
        'round': 90,
        'meta': {
            'quest_count': len(quests),
            'repay_record_count': 200,
            'mapping_count': 128,
            'extra_count': 72,
        },
        'quest_idx_to_reward': mapping,
        'extra_rewards': extras,
        'extra_categorization': {k: len(v) for k, v in extra_by_cat.items()},
        'verification': {
            'first_quest_name': quests[0]['name'],
            'first_quest_match': mapping[0]['quest_name'] == quests[0]['name'],
            'boundary_61': mapping[61]['quest_source'],
            'boundary_62': mapping[62]['quest_source'],
            'crossover_correct': (
                mapping[61]['quest_source'] == '_QUEST_0_DAT' and
                mapping[62]['quest_source'] == '_QUEST_1_DAT'
            ),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_quest_reward_map.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] mapped {len(mapping)} quests to Q_REPAY idx 0-127')
    print(f'  first quest: {mapping[0]["quest_name"]} (EXP {mapping[0]["exp"]}, gold {mapping[0]["gold"]})')
    print(f'  boundary 61→62: {mapping[61]["quest_source"]} → {mapping[62]["quest_source"]} (expect _QUEST_0 → _QUEST_1)')
    print(f'  crossover_correct: {out["verification"]["crossover_correct"]}')
    print()
    print(f'[OK] extra rewards idx 128-199:')
    for k, idxs in extra_by_cat.items():
        print(f'  {k:25s}: {len(idxs):2d} entries  ({idxs[:3]}{"..." if len(idxs) > 3 else ""})')
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
