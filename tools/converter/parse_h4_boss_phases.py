"""Hero4 Round 91 — multi-phase boss encounter stat 정량 (R80 후속).

ESDAT outlier 4 종 (1+ phase + final) 의 phase 별 stat 추출 + scaling 계산:

    좀비:        213B = 2 × 73 + 67 (2 phase + final)
    소환된 좀비:  140B = 1 × 73 + 67 (1 phase + final)
    오토마톤:    432B = 5 × 73 + 67 (5 phase + final)
    기갑병:      140B = 1 × 73 + 67 (1 phase + final, but R80 anomaly)
    죽음의 구:    72B  = 0 × 73 + 72 (special, layout 다름 — skip)

각 phase = 73B = 67B base stat (R78 layout) + 6B inter-phase link (R80).
final block = 67B (link 없음).

Stat field (R78):
    pos[0]      = enemy class byte (animation sheet ID)
    pos[2-3]    = EXP base LE16
    pos[23-24]  = HP_max LE16 (가설)
    pos[29-30]  = HP_current / pair LE16
    pos[35-40]  = ATK/DEF triple LE16
    pos[57-58]  = gold reward LE16
    pos[59-60]  = EXP reward LE16
"""
from __future__ import annotations
import json
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ESDAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

OUTLIERS = [
    ('_ESDAT_0', 0x1362, '좀비',         213),
    ('_ESDAT_0', 0x1a8e, '소환된 좀비',   140),
    ('_ESDAT_0', 0x2bef, '오토마톤',     432),
    ('_ESDAT_0', 0x2f80, '기갑병',       140),
]


def le16(b: bytes, p: int) -> int:
    return b[p] | (b[p+1] << 8)


def signed16(b: bytes, p: int) -> int:
    v = le16(b, p)
    return v - 0x10000 if v >= 0x8000 else v


def extract_body(fn: str, off: int, body_size: int) -> bytes:
    data = (ESDAT_DIR / fn).read_bytes()
    nlen = data[off + 3]
    header_len = 4 + nlen
    return data[off + header_len: off + header_len + body_size]


def decode_phase(block: bytes) -> dict:
    """67B base stat + optional 6B link (= 73B for phases, 67B for final)."""
    assert len(block) >= 67
    info = {
        'enemy_class': block[0],
        'exp_base_p2': le16(block, 2),
        'hp_max_p23': le16(block, 23),
        'pair_p29': le16(block, 29),
        'pair_p31': le16(block, 31),
        'atk_p35': le16(block, 35),
        'def_p37': le16(block, 37),
        'misc_p39': le16(block, 39),
        'gold_p57': le16(block, 57),
        'exp_p59': le16(block, 59),
        'section_marker_p42_43': f'{block[42]:02x}{block[43]:02x}',
        'sub_marker_p56': f'{block[56]:02x}',
    }
    if len(block) >= 73:
        info['link'] = {
            'sig': f'{block[67]:02x}{block[68]:02x}',
            'phase_id_le16': le16(block, 69),
            'transition_le16': le16(block, 71),
            'transition_hex': f'{block[71]:02x}{block[72]:02x}',
        }
    return info


def split_phases(body: bytes) -> tuple[list[bytes], bytes]:
    """N × 73 + 67 split."""
    n_phase = (len(body) - 67) // 73
    assert n_phase * 73 + 67 == len(body), f'unexpected size {len(body)}'
    phases = [body[i*73:(i+1)*73] for i in range(n_phase)]
    final = body[n_phase*73:]
    return phases, final


def compute_scaling(phases: list[dict], final: dict) -> dict:
    """Stat scaling: phase 0 → final 비율 + monotonicity."""
    seq = phases + [final]
    fields = ['hp_max_p23', 'atk_p35', 'def_p37', 'exp_p59', 'gold_p57']
    out = {}
    for f in fields:
        vals = [s[f] for s in seq]
        monotonic_inc = all(vals[i] <= vals[i+1] for i in range(len(vals)-1))
        out[f] = {
            'sequence': vals,
            'phase0_to_final_ratio': round(vals[-1] / vals[0], 3) if vals[0] else None,
            'monotonic_inc': monotonic_inc,
            'min_phase_idx': vals.index(min(vals)),
            'max_phase_idx': vals.index(max(vals)),
        }
    return out


def main() -> int:
    results = []
    for fn, off, name, body_size in OUTLIERS:
        body = extract_body(fn, off, body_size)
        phases, final = split_phases(body)
        phase_info = [decode_phase(p) for p in phases]
        final_info = decode_phase(final)
        scaling = compute_scaling(phase_info, final_info)
        # enemy_class transitions
        class_seq = [p['enemy_class'] for p in phase_info] + [final_info['enemy_class']]
        results.append({
            'file': fn,
            'offset': f'0x{off:x}',
            'name': name,
            'body_size': body_size,
            'phase_count': len(phases),
            'phases': phase_info,
            'final': final_info,
            'scaling': scaling,
            'enemy_class_sequence': class_seq,
            'class_changes': sum(1 for i in range(len(class_seq)-1) if class_seq[i] != class_seq[i+1]),
        })

    out = {
        'round': 91,
        'outlier_count': len(results),
        'r78_field_layout': {
            'enemy_class': 'pos[0]',
            'exp_base': 'pos[2-3] LE16',
            'hp_max': 'pos[23-24] LE16',
            'pair_a': 'pos[29-30] LE16',
            'pair_b': 'pos[31-32] LE16',
            'atk': 'pos[35-36] LE16',
            'def': 'pos[37-38] LE16',
            'misc': 'pos[39-40] LE16',
            'gold_reward': 'pos[57-58] LE16',
            'exp_reward': 'pos[59-60] LE16',
        },
        'r80_link_layout': {
            'signature': 'pos[67-68] = 0x47 0x00',
            'phase_id': 'pos[69-70] LE16 sequential',
            'transition': 'pos[71-72] = 0xbcb1 (final 진입) or 0xfabf (continue)',
        },
        'outliers': results,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_boss_phases.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] {len(results)} multi-phase boss encounters')
    for r in results:
        print(f'\n=== {r["name"]} ({r["body_size"]}B, {r["phase_count"]} phase + final) ===')
        print(f'  enemy_class seq: {r["enemy_class_sequence"]} (changes: {r["class_changes"]})')
        for fname, sc in r['scaling'].items():
            print(f'  {fname:14s} seq={sc["sequence"]} ratio_p0_to_final={sc["phase0_to_final_ratio"]} '
                  f'mono_inc={sc["monotonic_inc"]} min@ph{sc["min_phase_idx"]} max@ph{sc["max_phase_idx"]}')

    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
