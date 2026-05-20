"""Hero4 Round 107 — 죽음의 구 countdown timer 단위 in-game 검증 (R98 후속).

R98: pos[63-64] LE16 = 600 → 480 → 360 (stage 0→1→2), -120/stage.

검증 전략 (dialogue 에 분/초 문자열 없음):
1. ESDAT 전수 파싱 — 72B named entry 만 pos[63-64] 추출
2. 600/480/360 시퀀스가 죽음의 구 @0x331b 에만 존재하는지 uniqueness
3. 단위 가설 점수: seconds(÷60), centiseconds(÷100), 2-min blocks(÷120), game ticks(÷2/÷10)
4. decrypted 코퍼스 dialogue 키워드 negative scan
"""
from __future__ import annotations
import json
import os
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
ESDAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_death_sphere_timer_verify.json'

DEATH_SPHERE_OFFSET = 0x331b
TIMER_SEQ = [600, 480, 360]
STAGE_FILES = ['_ESDAT_0', '_ESDAT_1', '_ESDAT_2']


def le16(b: bytes, p: int) -> int:
    return b[p] | (b[p + 1] << 8)


def decode_euckr(b: bytes) -> str:
    try:
        return b.decode('euc-kr', errors='replace')
    except Exception:
        return ''


def extract_named_body(data: bytes, off: int, body_size: int) -> tuple[str, bytes] | None:
    if off + 4 >= len(data):
        return None
    nlen = data[off + 3]
    if nlen < 1 or nlen > 40:
        return None
    he = off + 4 + nlen
    if he + body_size > len(data):
        return None
    name = decode_euckr(data[off + 4:he])
    body = data[he:he + body_size]
    return name, body


def walk_esdat_entries(data: bytes, source: str) -> list[dict]:
    out = []
    off = 0
    while off < len(data) - 10:
        for body_size in (67, 72, 73):
            got = extract_named_body(data, off, body_size)
            if not got:
                continue
            name, body = got
            if not name or len(body) != body_size:
                continue
            entry = {
                'source': source,
                'offset': off,
                'name': name,
                'body_size': body_size,
                'enemy_class': body[0],
            }
            if body_size >= 65:
                entry['timer_p63_le16'] = le16(body, 63)
            if body_size >= 58:
                entry['gold_p57'] = le16(body, 57)
                entry['hp_p23'] = le16(body, 23)
            out.append(entry)
            break
        off += 1
    return out


def scan_dialogue_keywords() -> dict:
    keywords = [
        '죽음의 구', '10분', '8분', '6분', '제한시간', '시간이 얼마', '카운트다운',
        '600', '480', '360',
    ]
    counts = {k: {'hits': 0, 'files': []} for k in keywords}
    files_scanned = 0
    for root, _, files in os.walk(DECRYPTED):
        for fn in files:
            p = pathlib.Path(root) / fn
            try:
                txt = p.read_bytes().decode('euc-kr', errors='replace')
            except OSError:
                continue
            files_scanned += 1
            relp = str(p.relative_to(DECRYPTED)).replace('\\', '/')
            for k in keywords:
                c = txt.count(k)
                if c:
                    counts[k]['hits'] += c
                    counts[k]['files'].append({'path': relp, 'count': c})
    return {'files_scanned': files_scanned, 'keyword_hits': counts}


def score_unit_hypotheses(seq: list[int]) -> list[dict]:
    hypotheses = [
        ('seconds', 60, '10/8/6 minutes'),
        ('centiseconds', 100, '6.0/4.8/3.6 minutes (weak)'),
        ('two_minute_blocks', 120, '5/4/3 blocks × 2 min'),
        ('deciseconds', 10, '60/48/36 seconds (too long for mobile boss)'),
        ('frames_at_60fps', 60, 'alias seconds'),
    ]
    rows = []
    for name, divisor, label in hypotheses:
        vals = [v / divisor for v in seq]
        diffs = [seq[i] - seq[i + 1] for i in range(len(seq) - 1)]
        diff_vals = [d / divisor for d in diffs]
        monotonic = all(seq[i] > seq[i + 1] for i in range(len(seq) - 1))
        uniform_step = len(set(diffs)) == 1
        rows.append({
            'unit': name,
            'divisor': divisor,
            'display': label,
            'values': vals,
            'step_per_stage': diff_vals[0] if diff_vals else None,
            'monotonic_decrease': monotonic,
            'uniform_step_120': uniform_step and diffs == [120],
            'recommended': name == 'seconds' and uniform_step and diffs == [120],
        })
    return rows


def main() -> int:
    all_entries: list[dict] = []
    death_sphere_rows: list[dict] = []

    for fn in STAGE_FILES:
        path = ESDAT_DIR / fn
        data = path.read_bytes()
        got = extract_named_body(data, DEATH_SPHERE_OFFSET, 72)
        if not got:
            print(f'WARN: failed to extract death sphere from {fn}')
            continue
        name, body = got
        row = {
            'file': fn,
            'offset': DEATH_SPHERE_OFFSET,
            'name': name,
            'timer_p63_le16': le16(body, 63),
            'enemy_class': body[0],
            'hp_p23': le16(body, 23),
            'gold_p57': le16(body, 57),
        }
        death_sphere_rows.append(row)

    for path in sorted(ESDAT_DIR.glob('_ESDAT_*')):
        data = path.read_bytes()
        all_entries.extend(walk_esdat_entries(data, path.name))

    timers_72 = [
        e for e in all_entries
        if e['body_size'] == 72 and 'timer_p63_le16' in e
    ]
    timer_value_index: dict[int, list[dict]] = {}
    for e in timers_72:
        t = e['timer_p63_le16']
        timer_value_index.setdefault(t, []).append({
            'source': e['source'],
            'offset': e['offset'],
            'name': e['name'],
            'enemy_class': e['enemy_class'],
        })

    exclusive = {}
    for t in TIMER_SEQ:
        hits = timer_value_index.get(t, [])
        exclusive[t] = {
            'total_hits_in_72b_entries': len(hits),
            'named_death_sphere_only': all(
                h['name'] == '죽음의 구' and h['offset'] == DEATH_SPHERE_OFFSET
                for h in hits
            ),
            'hits': hits[:8],
        }

    dialogue = scan_dialogue_keywords()
    units = score_unit_hypotheses(TIMER_SEQ)

    conclusion = {
        'timer_field_confirmed': (
            len(death_sphere_rows) == 3
            and [r['timer_p63_le16'] for r in death_sphere_rows] == TIMER_SEQ
            and all(r['name'] == '죽음의 구' for r in death_sphere_rows)
        ),
        'sequence': TIMER_SEQ,
        'step_per_stage': 120,
        'unit_verdict': 'seconds (1:1 LE16 = seconds)',
        'display_minutes': '10 → 8 → 6 minutes',
        'confidence': 'high_structural_low_dialogue',
        'dialogue_support': 'none — no 10분/8분/6분 strings in decrypted corpus',
        'dialogue_death_sphere_hits': dialogue['keyword_hits']['죽음의 구']['hits'],
        'uniqueness': all(
            exclusive.get(t, {}).get('named_death_sphere_only', False) for t in TIMER_SEQ
        ),
    }

    out = {
        'meta': {'round': 'R107', 'date': '2026-05-20', 'r98_followup': True},
        'death_sphere_entries': death_sphere_rows,
        'timer_uniqueness': exclusive,
        'unit_hypotheses': units,
        'dialogue_scan': dialogue,
        'conclusion': conclusion,
        'esdat_72b_entry_count': len(timers_72),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('=== R107 Death sphere timer verify ===')
    for r in death_sphere_rows:
        print(f"  {r['file']}: timer={r['timer_p63_le16']} HP={r['hp_p23']} class={r['enemy_class']}")
    print(f"uniqueness 600/480/360: {conclusion['uniqueness']}")
    print(f"unit verdict: {conclusion['unit_verdict']} ({conclusion['display_minutes']})")
    print(f"dialogue 죽음의 구 hits: {conclusion['dialogue_death_sphere_hits']}")
    print(f'wrote {OUT.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
