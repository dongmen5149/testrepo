"""Hero5 Monster AI 정의 (/c/mon/<id>_ai) 디코더.

Round 44 (Monster AI VM 식별) + Round 45 (AI_def 데이터원 식별).

EnemyAI::LoadData (0x6a62c, 700B) 정밀 disasm 결과:

파일 layout (모두 little-endian):
  byte 0              : trigger_count (n_t)
  bytes 1..n_t        : trigger code list (n_t bytes) — IsTriggerEqual 의 trigger ids
  bytes n_t+1..2n_t   : handler size list (n_t bytes) — 각 trigger 의 trigger_data_block 내 size
                        (handler_offsets 는 누적합으로 _계산_ 되며 파일에서 안 읽음)
  next sum(handlers) bytes : trigger_data_block
  u16 (LE)            : action_count (n_a, 사실은 u8 — 상위 바이트 무시)
  3 × n_a bytes       : 3개 lookup table (action_data_1/2/3)
  n_a * 2 bytes       : action_data_4 (각 action 의 u16 metadata)
  u16 (LE)            : trigger_stream_size (n_ts, 사실은 u8 — 상위 바이트 무시)
  n_ts bytes          : **trigger byte stream** (Tokenizer 1 = Monster+0x28c, trigger eval)
  byte                : action_list_count (n_l)
  3 × n_l bytes       : 3개 lookup table (action_list_data_1/2/3)
                        - action_list_data_2 = AI_setActionList 가 사용하는 offset_table
  u16 (LE)            : action_stream_size (n_as, s16)
  n_as bytes          : **action byte stream** (Tokenizer 2 = Monster+0x290, opcode interpreter)

산출:
  apps/hero5-godot/assets/gamedata/monster_ai.json
"""
from __future__ import annotations
import pathlib, csv, struct, json, re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'monster_ai.json'


# Round 44 의 13 opcode 별 operand size
OPCODE_OPERAND = {
    0: 2, 1: 2, 2: 1, 3: 1, 4: 3, 5: 4, 6: 2, 7: 3, 8: 2, 9: 2, 10: 1,
    11: -1,  # variable
    12: 1,
}

OPCODE_NAME = {
    0: 'WALK',
    1: 'CHANCE_WALK',
    2: 'SET_SUB',
    3: 'SET_STATE_FIRST',
    4: 'SKILL_SET',
    5: 'SKILL_PARAM',
    6: 'SET_303',
    7: 'SET_305',
    8: 'SET_308',
    9: 'NEXT_SKILL',
    10: 'SKIP',
    11: 'VAR_DATA',
    12: 'ANIM_OVERRIDE',
}

# Round 46 — IsTriggerEqual 13 trigger 의 operand size (IsTriggerEqual 본체가
# 데이터를 읽는 바이트 수). ActionOfTrigger 가 매 entry 의 끝에 action_id 1 byte
# 추가로 읽어 Monster+0x294 에 set. 따라서 entry stride = 1 (code) + operand + 1 (action_id).
TRIGGER_OPERAND = {
    0: 0,   # +0x29f one-shot SET
    1: 1,   # IRect visibility check (operand = IRect index 0-3, mul by 40)
    2: 0,   # +0x2bc one-shot consume
    3: 0,   # all-monsters-dead check
    4: 0,   # this-monster isDie check
    5: 0,   # special: skip IsTriggerEqual, immediate action_id read
    6: 1,   # tutorial flag check (operand vs gv+0x130/0x131/0x132)
    7: 0,   # +0x2bf one-shot consume
    8: 0,   # +0x2b9 one-shot consume
    9: 0,   # +0x2bd one-shot consume
    10: 0,  # +0x2be one-shot consume
    11: 0,  # +0x2b7 one-shot consume
    12: 0,  # +0x2b6 one-shot consume
}

TRIGGER_NAME = {
    0: 'SET_29F',
    1: 'VISIBILITY_RECT',
    2: 'CONSUME_2BC',
    3: 'ALL_MONSTERS_DEAD',
    4: 'SELF_DEAD',
    5: 'ALWAYS_GOTO',
    6: 'TUTORIAL_FLAG',
    7: 'CONSUME_2BF',
    8: 'CONSUME_2B9',
    9: 'CONSUME_2BD',
    10: 'CONSUME_2BE',
    11: 'CONSUME_2B7',
    12: 'CONSUME_2B6',
}


def find_ai_files() -> list[tuple[int, pathlib.Path]]:
    """asset_names.tsv 에서 c/mon/<id>_ai 패턴 추출."""
    out = []
    pat = re.compile(r'c/mon/(\d+)_ai')
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            m = pat.search(r['recovered_name'])
            if m:
                idx = int(r['index'])
                h = int(r['hash'], 16)
                path = ENTRIES / f'{idx:05d}_{h:08x}.bin'
                out.append((int(m.group(1)), path))
    out.sort()
    return out


def disasm_tokens(stream: bytes, kind: str = 'action') -> list[dict]:
    """byte stream 을 opcode + operand 로 디스어셈블.

    kind='action': Ai_onAction 의 13 opcode 사용 (Monster+0x290 stream).
    kind='trigger': IsTriggerEqual 의 13 trigger 사용 (Monster+0x28c stream).
        operand 길이는 trigger 별 다름 — 정확한 매핑은 Round 44 의 IsTriggerEqual
        13 handler 정밀 분석 필요 (현재는 raw hex 만 dump).
    """
    if kind == 'trigger':
        # Round 46: trigger stream layout = [code][operand][action_id] per entry
        out = []
        pos = 0
        while pos < len(stream):
            code = stream[pos]
            if code not in TRIGGER_OPERAND:
                out.append({'pc': pos, 'code': code, 'name': f'unk_{code:#x}',
                            'note': 'unknown trigger — stop'})
                break
            opn = TRIGGER_OPERAND[code]
            opname = TRIGGER_NAME.get(code, '?')
            if pos + 1 + opn + 1 > len(stream):
                # trailing — last entry might have no action_id (end marker)
                operand = stream[pos + 1:pos + 1 + opn]
                out.append({'pc': pos, 'code': code, 'name': opname,
                            'operand_hex': operand.hex(),
                            'note': 'incomplete entry (no action_id)'})
                break
            operand = stream[pos + 1:pos + 1 + opn]
            action_id = stream[pos + 1 + opn]
            out.append({'pc': pos, 'code': code, 'name': opname,
                        'operand_hex': operand.hex(),
                        'action_id': action_id})
            pos += 2 + opn
        return out

    out = []
    pos = 0
    while pos < len(stream):
        op = stream[pos]
        opname = OPCODE_NAME.get(op, f'unk_{op:#x}')
        if op == 11:
            if pos + 1 >= len(stream): break
            n = stream[pos + 1]
            if pos + 2 + n > len(stream): break
            operand = stream[pos + 2:pos + 2 + n]
            out.append({'pc': pos, 'op': op, 'name': opname, 'n': n,
                        'operand_hex': operand.hex()})
            pos += 2 + n
        elif op in OPCODE_OPERAND:
            n = OPCODE_OPERAND[op]
            if pos + 1 + n > len(stream): break
            operand = stream[pos + 1:pos + 1 + n]
            out.append({'pc': pos, 'op': op, 'name': opname,
                        'operand_hex': operand.hex()})
            pos += 1 + n
        else:
            # unknown opcode — default handler 가 0 반환 (continue)
            # 1 byte 만 소비하고 진행
            out.append({'pc': pos, 'op': op, 'name': opname, 'note': 'unknown — default handler returns 0 (no-op)'})
            pos += 1
    return out


def parse_ai_file(data: bytes) -> dict:
    p = 0
    n_t = data[p]; p += 1
    trigger_codes = list(data[p:p + n_t]); p += n_t
    handler_bytes = list(data[p:p + n_t]); p += n_t
    # handler_offsets 는 파일에서 안 읽고 누적합으로 계산 (LoadData 가 EnemyAI+0x39 에 cumulative store)
    handler_offsets = []
    acc = 0
    for hb in handler_bytes:
        handler_offsets.append(acc)
        acc = (acc + hb) & 0xff
    total_trigger_data = acc  # 마지막 누적합 = total
    trigger_data_block = data[p:p + total_trigger_data]; p += total_trigger_data

    n_a = struct.unpack_from('<H', data, p)[0] & 0xff; p += 2
    # 3 lookup tables: 2 × u8 array + 1 × u16 array
    action_data_1 = list(data[p:p + n_a]); p += n_a
    action_data_2 = list(data[p:p + n_a]); p += n_a
    action_data_3_raw = data[p:p + n_a * 2]; p += n_a * 2
    action_data_3 = [struct.unpack_from('<H', action_data_3_raw, i * 2)[0] for i in range(n_a)]

    n_ts = struct.unpack_from('<H', data, p)[0] & 0xff; p += 2
    trigger_stream = data[p:p + n_ts]; p += n_ts

    n_l = data[p]; p += 1
    action_list_data_1 = list(data[p:p + n_l]); p += n_l
    action_list_offset_table = list(data[p:p + n_l]); p += n_l
    action_list_data_3 = list(data[p:p + n_l]); p += n_l

    n_as = struct.unpack_from('<H', data, p)[0]; p += 2
    action_stream = data[p:p + n_as]; p += n_as

    # 디스어셈블 action_stream (Ai_onAction 13 opcode)
    action_tokens = disasm_tokens(action_stream, kind='action')
    # trigger_stream 은 IsTriggerEqual 의 trigger code (별도 의미) — raw 만
    trigger_tokens = disasm_tokens(trigger_stream, kind='trigger')

    return {
        'file_size': len(data),
        'consumed': p,
        'trigger_count': n_t,
        'trigger_codes': trigger_codes,
        'handler_bytes': handler_bytes,
        'handler_offsets': handler_offsets,
        'trigger_data_hex': trigger_data_block.hex(),
        'action_count': n_a,
        'action_data_1': action_data_1,
        'action_data_2': action_data_2,
        'action_data_3_u16': action_data_3,
        'trigger_stream_size': n_ts,
        'trigger_stream_hex': trigger_stream.hex(),
        'trigger_tokens': trigger_tokens,
        'action_list_count': n_l,
        'action_list_data_1': action_list_data_1,
        'action_list_offset_table': action_list_offset_table,
        'action_list_data_3': action_list_data_3,
        'action_stream_size': n_as,
        'action_stream_hex': action_stream.hex(),
        'action_tokens': action_tokens,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files = find_ai_files()
    all_ai = {}
    errors = []
    for ai_id, path in files:
        try:
            data = path.read_bytes()
            parsed = parse_ai_file(data)
            parsed['ai_id'] = ai_id
            all_ai[ai_id] = parsed
            if parsed['consumed'] != parsed['file_size']:
                errors.append((ai_id, f'consumed={parsed["consumed"]} vs file_size={parsed["file_size"]}'))
        except Exception as e:
            errors.append((ai_id, f'parse error: {e}'))

    OUT.write_text(json.dumps({
        'note': '/c/mon/<id>_ai parsed. Action stream disasm uses Round 44 opcode table.',
        'opcode_table': {k: f'{v}: {OPCODE_NAME[k]} ({"variable" if v == -1 else str(v) + " operand bytes"})' for k, v in OPCODE_OPERAND.items()},
        'by_id': all_ai,
        'parse_errors': errors,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'parsed {len(all_ai)} AI files → {OUT}')
    if errors:
        print(f'\n{len(errors)} parse error(s) (first 10):')
        for e in errors[:10]:
            print(f'  AI {e[0]}: {e[1]}')

    # 첫 3 sample 요약
    print('\nSample AI definitions (first 3):')
    for ai_id in sorted(all_ai.keys())[:3]:
        a = all_ai[ai_id]
        print(f'  AI {ai_id}: {a["file_size"]}B, triggers={a["trigger_count"]} '
              f'(codes={a["trigger_codes"]}), action_count={a["action_count"]}, '
              f'action_list_count={a["action_list_count"]}, '
              f'action_stream={a["action_stream_size"]}B ({len(a["action_tokens"])} ops)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
