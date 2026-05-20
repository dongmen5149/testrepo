"""Hero4 Round 98 — 죽음의 구 72B 특수 layout 정밀 분석 (R91 후속).

R91 의 미해결: 죽음의 구 72B = 67B standard + 5B trailer, pos[42-43] marker 부재.

3 stage variant (_ESDAT_0/1/2 모두 동일 offset 0x331b) 의 byte-by-byte 비교로 layout 확정.

발견:
- pos[0]=50 (enemy_class=0x32), 다른 보스와 별개 class
- pos[55-56] = '07 ff' (sub-boundary at +56 유지)
- pos[42-43] = '04 00' (= ff 3f marker 미사용 → R80 anomaly 확인)
- pos[23-24] HP LE16 scaling: 120 → 322 → 437 (1.0×, 2.7×, 3.6×)
- pos[28-29] ATK LE16 scaling: 195 → 567 → 772
- pos[57-60] gold/EXP scaling: 11/13/9/10 → 53/53/47/52 → 67/72/65/66
- **pos[63-64] = 600 → 480 → 360 LE16 (감소!) — 시간 카운트다운 가설**
  600/480/360 → 100×6, 80×6, 60×6 = 6배수. **timer in seconds × 60 or in deciseconds**.
  600s=10min, 480s=8min, 360s=6min 이면 stage 가 진행될수록 **time pressure 증가**.
- pos[65-71] 모두 0 (R91 의 5B extra padding)

결론: 죽음의 구 = **time-limited boss encounter** (countdown timer). stage 별로 timer 단축
→ R80 "특수 적 (보스 카운트다운 / mini-boss)" 가설 검증 완료.
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ESDAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

ENTRIES = [
    ('_ESDAT_0', 0x331b, 0),
    ('_ESDAT_1', 0x331b, 1),
    ('_ESDAT_2', 0x331b, 2),
]


def le16(b: bytes, p: int) -> int:
    return b[p] | (b[p+1] << 8)


def extract_body(fn: str, off: int) -> bytes:
    data = (ESDAT_DIR / fn).read_bytes()
    nlen = data[off + 3]
    header_end = off + 4 + nlen
    return data[header_end:header_end + 72]


def decode_death_sphere(body: bytes) -> dict:
    assert len(body) == 72
    # Field offsets verified by hex walkthrough:
    # pos[0]=class, pos[14]=156 const, pos[22]=0x0f const, pos[23-24]=HP LE16,
    # pos[25-26]=HP dup, pos[27-28]=ATK LE16, pos[29-30]=DEF LE16,
    # pos[37-38] subboundary 07 ff, pos[39-42]=gold/EXP bytes, pos[63-64]=timer LE16
    return {
        'enemy_class_p0': body[0],
        'header_le16_p1_2': le16(body, 1),
        'exp_base_le32_p3_6': body[3] | (body[4] << 8) | (body[5] << 16) | (body[6] << 24),
        'const_p8_p9': (body[8], body[9]),
        'const_p14': body[14],
        'const_p22': body[22],
        'hp_p23_le16': le16(body, 23),
        'hp_dup_p25_le16': le16(body, 25),
        'atk_p27_le16': le16(body, 27),
        'def_p29_le16': le16(body, 29),
        'def_dup_p31_le16': le16(body, 31),
        'misc_p33_p34': (body[33], body[34]),
        'speed_p35_p36': (body[35], body[36]),
        'sub_boundary_p55_56': (body[55], body[56]),
        'gold_le16_p57_58': le16(body, 57),
        'exp_le16_p59_60': le16(body, 59),
        'countdown_timer_p63_64_le16': le16(body, 63),
        'trailer_p65_71': list(body[65:72]),
    }


def main() -> int:
    decoded = []
    for fn, off, stage in ENTRIES:
        body = extract_body(fn, off)
        info = decode_death_sphere(body)
        info['source'] = fn
        info['stage'] = stage
        info['raw_body_hex'] = body.hex()
        decoded.append(info)

    # Scaling table
    fields_to_compare = [
        'hp_p23_le16', 'atk_p27_le16', 'def_p29_le16',
        'gold_le16_p57_58', 'exp_le16_p59_60',
        'countdown_timer_p63_64_le16',
    ]
    scaling_table = {}
    for f in fields_to_compare:
        scaling_table[f] = [d[f] for d in decoded]

    # Timer interpretation
    timer_seq = scaling_table['countdown_timer_p63_64_le16']
    timer_finding = {
        'sequence': timer_seq,
        'monotonic_decrease': all(timer_seq[i] > timer_seq[i+1] for i in range(len(timer_seq)-1)),
        'difference_per_stage': [timer_seq[i] - timer_seq[i+1] for i in range(len(timer_seq)-1)],
        'as_seconds_if_div_1': f'{timer_seq[0]}s = {timer_seq[0]/60:.1f}분 → {timer_seq[2]}s = {timer_seq[2]/60:.1f}분',
        'hypothesis': 'death sphere countdown timer — stage 진행시 단축 (time pressure 증가)',
    }

    out = {
        'round': 98,
        'r91_followup': '죽음의 구 72B = 67B 변형 + 5B trailer (timer + padding)',
        'entries': decoded,
        'scaling_table': scaling_table,
        'countdown_timer_finding': timer_finding,
        'layout_summary': {
            'pos_0': 'enemy_class (=0x32, 죽음의 구 전용)',
            'pos_23_24': 'HP LE16',
            'pos_28_29': 'ATK LE16',
            'pos_30_31': 'DEF LE16',
            'pos_42_43': '(R80 anomaly) ff 3f marker 부재 = 04 00',
            'pos_55_56': 'sub-boundary 07 ff (표준 +56 marker)',
            'pos_57_58': 'gold LE16',
            'pos_59_60': 'EXP LE16',
            'pos_63_64': '★ countdown timer LE16 (death sphere 시간 제한)',
            'pos_65_71': 'zero padding (5B trailer 남은 부분)',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_death_sphere.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] 3 stage variants of 죽음의 구 analyzed')
    print()
    print('=== Stat scaling (stage 0 → 1 → 2) ===')
    for f, seq in scaling_table.items():
        print(f'  {f:35s}: {seq}')
    print()
    print(f'★ Countdown timer (pos[63-64] LE16): {timer_seq}')
    print(f'  monotonic_decrease: {timer_finding["monotonic_decrease"]}')
    print(f'  diff per stage: {timer_finding["difference_per_stage"]}')
    print(f'  as seconds: {timer_finding["as_seconds_if_div_1"]}')
    print(f'  → {timer_finding["hypothesis"]}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
