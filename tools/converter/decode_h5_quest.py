"""quest_*.dat (Hero5 main story quest 3 difficulty × 151 quests) 디코더.

Round 39 (Quest 시스템 식별) + Round 40 (record byte → struct 정밀 매핑).

데이터 소스: VFS index 55/56/57 (`c/csv/quest_0.dat`, `quest_1.dat`,
`quest_2.dat`, 각 22367B). 3 파일 동일 layout, 다른 값 (difficulty scaling) —
같은 quest 의 condition target 과 reward 값이 q0 < q1 < q2 로 증가하는
패턴이 `enemy_*.dat` 와 동일 (Round 34).

`_ZN8QuestMgr13LoadQuestDataEaa` (0x000d40e8, 1188B) 디스어셈블 결과:

파일 layout:
  u16 count (151)
  records[count]:
    u16 body_size (Quest_GetOffset 가 사용)
    body[body_size]:
      u8 h0                  → struct[+5]    (용도 미상)
      u8 h1 = obj_count      → struct[+6]    (variable sub-loop 카운터, signed)
      u8 h2                  → struct[+7]    (용도 미상, 255=metadata 추정)
      u8 strlen0; bytes[strlen0]              → struct[+8] (name, max 28B)
      u8 strlen1; bytes[strlen1]              → struct[+0x24] (desc, max 200B)
      u8 strlen2; bytes[strlen2]              → struct[+0xec] (cat, max 28B)
      phase1: 3 × 6B objective entries
        u8 cond_type; u8 cond_sub; u32 target_value
        → struct[+0x114..+0x119, +0x11c..+0x128]
      phase2: 3 × 6B reward entries (same layout)
        17 = money, 18 = EXP, 255 = unused
        → struct[+0x140..+0x145, +0x148..+0x154]
      trailer: u8 byte0, u8 byte1 → struct[+0x16c, +0x16d]
      (obj_count > 0 인 경우 variable sub-loop 이 실행되지만 일반 데이터에서는
       obj_count=0 이 대부분 — 151 중 1 record (#117) 만 obj_count=2)

총 body size = 44 + strlen0 + strlen1 + strlen2 (정확 검증, 151/151 records EOF 도달).

산출:
  apps/hero5-godot/assets/gamedata/quests.json
  - difficulty 별 quest 배열 + 3 difficulty 비교 view
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'quests.json'


# reward type code (phase2 byte 0)
REWARD_TYPE = {
    17: 'money',
    18: 'exp',
    255: 'unused',
}

# condition type code (phase1 byte 0) — empirical; 255 = unused slot
COND_TYPE = {
    17: 'cond_17',
    18: 'cond_18',
    255: 'unused',
}


def find(target: str) -> pathlib.Path:
    for r in csv.DictReader(open(NAMES, encoding='utf-8'), delimiter='\t'):
        if r['recovered_name'] == target:
            return ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"], 16):08x}.bin'
    raise FileNotFoundError(target)


def parse_entry(buf: bytes, base: int) -> dict:
    b0, b1 = buf[base], buf[base + 1]
    val = struct.unpack_from('<I', buf, base + 2)[0]
    return {'type': b0, 'sub': b1, 'value': val}


def parse_quest_file(data: bytes) -> list[dict]:
    count = struct.unpack_from('<H', data, 0)[0]
    pos = 2
    out = []
    for i in range(count):
        if pos + 2 > len(data):
            raise ValueError(f'EOF before record {i} (pos={pos})')
        size = struct.unpack_from('<H', data, pos)[0]
        body_start = pos + 2
        body_end = body_start + size
        if body_end > len(data):
            raise ValueError(f'record {i} body OOB (pos={pos}, size={size})')
        body = data[body_start:body_end]

        h0, h1, h2 = body[0], body[1], body[2]
        p = 3
        s0 = body[p]; p += 1
        name = body[p:p + s0].decode('euc-kr', errors='replace'); p += s0
        s1 = body[p]; p += 1
        desc = body[p:p + s1].decode('euc-kr', errors='replace'); p += s1
        s2 = body[p]; p += 1
        category = body[p:p + s2].decode('euc-kr', errors='replace'); p += s2

        # 3 × 6B objective entries
        objectives = [parse_entry(body, p + k * 6) for k in range(3)]
        p += 18
        # 3 × 6B reward entries
        rewards = [parse_entry(body, p + k * 6) for k in range(3)]
        p += 18
        # 2-byte trailer
        trailer = (body[p], body[p + 1])
        p += 2

        # remaining bytes (typically 0 — obj_count > 0 path inspects neighboring
        # bytes but does not actually grow body size)
        remainder = body[p:]

        labeled_rewards = []
        for r in rewards:
            r_label = dict(r)
            r_label['kind'] = REWARD_TYPE.get(r['type'], f'type_{r["type"]}')
            labeled_rewards.append(r_label)

        labeled_objs = []
        for o in objectives:
            o_label = dict(o)
            o_label['kind'] = COND_TYPE.get(o['type'], f'type_{o["type"]}')
            labeled_objs.append(o_label)

        out.append({
            'idx': i,
            'size': size,
            'h0': h0,
            'obj_count': h1,
            'h2': h2,
            'name': name,
            'description': desc,
            'category': category,
            'objectives': labeled_objs,
            'rewards': labeled_rewards,
            'trailer': list(trailer),
            'extra_hex': remainder.hex() if remainder else '',
        })
        pos = body_end
    if pos != len(data):
        raise ValueError(f'trailing data: pos={pos} vs size={len(data)}')
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sources = ['c/csv/quest_0.dat', 'c/csv/quest_1.dat', 'c/csv/quest_2.dat']
    by_diff = {}
    for diff, src in enumerate(sources):
        data = find(src).read_bytes()
        recs = parse_quest_file(data)
        by_diff[f'q{diff}'] = recs

    compare = []
    for i in range(151):
        q0, q1, q2 = by_diff['q0'][i], by_diff['q1'][i], by_diff['q2'][i]
        compare.append({
            'idx': i,
            'name': q0['name'],
            'category': q0['category'],
            'name_match': q0['name'] == q1['name'] == q2['name'],
            'rewards_q0': [(r['kind'], r['value']) for r in q0['rewards'] if r['type'] != 255],
            'rewards_q1': [(r['kind'], r['value']) for r in q1['rewards'] if r['type'] != 255],
            'rewards_q2': [(r['kind'], r['value']) for r in q2['rewards'] if r['type'] != 255],
        })

    OUT.write_text(json.dumps({
        'note': '3 difficulty levels (q0/q1/q2). 151 quests/each. Same layout, scaled values.',
        'reward_type_table': REWARD_TYPE,
        'cond_type_table': COND_TYPE,
        'by_difficulty': by_diff,
        'compare': compare,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    q0 = by_diff['q0']
    print(f'parsed 3 × {len(q0)} quests → {OUT}')
    print('\nfirst 10 quests (q0=easy):')
    for r in q0[:10]:
        rew = ', '.join(f'{x["kind"]}={x["value"]}' for x in r['rewards'] if x['type'] != 255)
        print(f'  #{r["idx"]:3d}  {r["name"][:22]:22}  [{r["category"]}]  rewards: {rew}')

    from collections import Counter
    h2_dist = Counter(r['h2'] for r in q0)
    print(f'\nh2 distribution top 10: {dict(h2_dist.most_common(10))}')

    print('\ndifficulty scaling sample (#0):')
    for d in ('q0', 'q1', 'q2'):
        r = by_diff[d][0]
        rewards = [(x['kind'], x['value']) for x in r['rewards'] if x['type'] != 255]
        objs = [(x['kind'], x['value']) for x in r['objectives'] if x['type'] != 255]
        print(f'  {d}: obj={objs}  rewards={rewards}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
