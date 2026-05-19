"""Round 78 — ESDAT 67B encounter body layout.

R76 Track B 의 "0x3f opcode 274회" 의 실체는 ESDAT 67B body 의 **섹션 경계 marker** (pos[41-42] = 0xff 0x3f).

150 aligned 67B entries × 3 stages 분석:
- pos[0-40]: base stat 섹션 (이름 ref + HP/MP/ATK)
- pos[41-42] = 0xff 0x3f (section boundary)
- pos[43-66]: reward/drop 섹션

산출: work/h4/converted/h4_esdat_encounter_layout.json
"""
from __future__ import annotations
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
E_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_esdat_encounter_layout.json'


def is_esdat(d, i):
    if i+7 > len(d) or d[i+1] != 0: return False
    nl = d[i+3]
    if not 3 <= nl <= 30: return False
    if i+4+nl > len(d): return False
    f = d[i+4:i+4+min(6,nl)]
    return any(0xa1<=f[k]<=0xfe and k+1<len(f) and 0xa1<=f[k+1]<=0xfe for k in range(len(f)-1))


def extract(data):
    out = []
    i = 0
    while i < len(data) - 6:
        if not is_esdat(data, i):
            i += 1
            continue
        seq = data[i+2]
        nl = data[i+3]
        name = data[i+4:i+4+nl].decode('euc-kr', errors='replace')
        bs = i + 4 + nl
        nxt = bs
        while nxt < len(data) - 6:
            if is_esdat(data, nxt):
                break
            nxt += 1
        else:
            nxt = len(data)
        out.append((seq, name, data[bs:nxt]))
        i = nxt
    return out


def main():
    files = {fn: extract((E_DIR/fn).read_bytes()) for fn in ['_ESDAT_0','_ESDAT_1','_ESDAT_2']}
    n = min(len(f) for f in files.values())
    triples = []
    for k in range(n):
        s0,n0,b0 = files['_ESDAT_0'][k]
        s1,n1,b1 = files['_ESDAT_1'][k]
        s2,n2,b2 = files['_ESDAT_2'][k]
        if n0==n1==n2 and len(b0)==67==len(b1)==len(b2):
            triples.append((n0, b0, b1, b2))

    const_cnt = [0]*67
    le16_mono = [0]*67
    pair_dup = [0]*67
    section_marker_pos = []
    for nm, b0, b1, b2 in triples:
        for p in range(67):
            if b0[p]==b1[p]==b2[p]: const_cnt[p] += 1
            if p < 66:
                v0 = b0[p] | (b0[p+1]<<8)
                v1 = b1[p] | (b1[p+1]<<8)
                v2 = b2[p] | (b2[p+1]<<8)
                if 0 < v0 < v1 < v2 < 60000: le16_mono[p] += 1
            if p < 64:
                va  = b0[p] | (b0[p+1]<<8); vb  = b0[p+2] | (b0[p+3]<<8)
                va1 = b1[p] | (b1[p+1]<<8); vb1 = b1[p+2] | (b1[p+3]<<8)
                if va == vb and va1 == vb1 and va > 0: pair_dup[p] += 1
        if b0[42]==0xff and b0[43]==0x3f: section_marker_pos.append(nm)

    N = len(triples)
    thr = N * 0.6
    const_pos = [p for p,c in enumerate(const_cnt) if c >= thr]
    le16_pos = [p for p,c in enumerate(le16_mono) if c >= thr]
    pair_pos = [p for p,c in enumerate(pair_dup) if c >= thr]

    # Sample 3 encounters
    samples = []
    for nm, b0, b1, b2 in triples[:3]:
        samples.append({
            'name': nm,
            'stage_0_hex': b0.hex(),
            'stage_1_hex': b1.hex(),
            'stage_2_hex': b2.hex(),
            'section_a_hex': b0[:42].hex(),
            'section_marker_pos42_43': f'{b0[42]:02x} {b0[43]:02x}',
            'section_b_hex': b0[44:56].hex(),
            'sub_boundary_pos56': f'{b0[56]:02x}' if len(b0) > 56 else '?',
            'section_c_hex': b0[57:].hex(),
        })

    out = {
        'meta': {
            'round': 'R78', 'date': '2026-05-19',
            'source': str(E_DIR.relative_to(ROOT)),
            'aligned_triples': N,
            'key_finding': 'ESDAT 67B body = 2-section encounter record (base stat + reward), boundary at pos[41-42] = 0xff 0x3f',
        },
        'layout': {
            'section_a_offsets': '0-41 (base stat + name/sprite ref)',
            'section_boundary_offset': '42-43 (0xff 0x3f marker, 127/150 entries)',
            'section_b_offsets': '44-55 (drop item ids?)',
            'sub_boundary_offset': '56 (0xff)',
            'section_c_offsets': '57-66 (reward/trailer)',
        },
        'constants': const_pos,
        'le16_monotonic_stat_positions': le16_pos,
        'max_current_pair_positions': pair_pos,
        'section_marker_hit_count': len(section_marker_pos),
        'samples': samples,
        'role_hypotheses': {
            'pos[0]': 'enemy class byte (오토마톤=0x0d, 사수=0x0e, 기갑병=0x09)',
            'pos[2-3]': 'stage-variant LE16 (EXP reward?)',
            'pos[7-9]': 'class sprite/animation ref (constants 0x33 0x6f etc)',
            'pos[23-25]': 'HP_max LE16 + variants',
            'pos[27-29]': 'MP/secondary',
            'pos[29-31]': 'paired stat (max/current)',
            'pos[35-40]': 'ATK/DEF stat block',
            'pos[41-42]': '★ section boundary (0xff 0x3f)',
            'pos[43-50]': 'drop item ids (slot-pairs?)',
            'pos[51-60]': 'gold/EXP reward',
            'pos[61-66]': 'trailer constants',
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"=== ESDAT 67B encounter analysis ({N} aligned triples) ===")
    print(f"section marker (0xff 0x3f at pos[41-42]) hits: {len(section_marker_pos)} / {N}")
    print(f"constants (>{int(thr)} of {N}): {const_pos}")
    print(f"LE16 monotonic stat: {le16_pos}")
    print(f"max/current pair: {pair_pos}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
