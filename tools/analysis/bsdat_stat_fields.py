"""Round 77 — BSDAT stat field mapping (49B 일반 + 105B 메인 보스).

R76 Track B 에서 3 BSDAT = 동일 보스 난이도 3단계 확인. 이번엔 LE16 stat field 의미 추정.

방법:
1. 각 entry 의 3-stage 값을 LE16 으로 추출
2. byte 위치별로 (a) 상수 (모든 stage 동일), (b) 선형 증가 (stat), (c) 중복 페어 (max/current) 식별
3. 49B 보스 (브리안 등) 와 105B 보스 (루칸 등) 의 stat layout 분리

산출: work/h4/converted/h4_bsdat_stat_fields.json
"""
from __future__ import annotations
import json
import pathlib
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
E_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_bsdat_stat_fields.json'


def is_bsdat(d, i):
    if i+6>len(d) or d[i+1]!=0: return False
    nl=d[i+2]
    if not 3<=nl<=30: return False
    if i+3+nl>len(d): return False
    f=d[i+3:i+3+min(6,nl)]
    return any(0xa1<=f[k]<=0xfe and k+1<len(f) and 0xa1<=f[k+1]<=0xfe for k in range(len(f)-1))


def extract(data):
    out=[]; i=0
    while i<len(data)-6:
        if not is_bsdat(data,i): i+=1; continue
        nl=data[i+2]; name=data[i+3:i+3+nl].decode('euc-kr', errors='replace')
        bs=i+3+nl; nxt=bs
        while nxt<len(data)-6:
            if is_bsdat(data,nxt): break
            nxt+=1
        else: nxt=len(data)
        out.append((name, data[bs:nxt])); i=nxt
    return out


def analyze_layout(triples, body_len):
    """For all entries with this body_len, find per-position role across 3 stages."""
    if not triples: return None
    n_entries = len(triples)
    pos_roles = []
    for p in range(body_len - 1):
        vals0 = [t[0][p] for t in triples]
        vals1 = [t[1][p] for t in triples]
        vals2 = [t[2][p] for t in triples]
        # Constants (same value in all 3 stages, all entries)
        constant_across_stages = sum(1 for tr in triples if tr[0][p]==tr[1][p]==tr[2][p])
        # Monotonic increase per entry?
        mono_count = sum(1 for k in range(n_entries) if triples[k][0][p] < triples[k][1][p] < triples[k][2][p])
        # LE16 view
        le16_mono = 0
        if p + 1 < body_len:
            for k in range(n_entries):
                v0 = triples[k][0][p] | (triples[k][0][p+1]<<8)
                v1 = triples[k][1][p] | (triples[k][1][p+1]<<8)
                v2 = triples[k][2][p] | (triples[k][2][p+1]<<8)
                if 0 < v0 < v1 < v2 < 60000:
                    le16_mono += 1
        # Pair-duplicate detection: LE16(p) == LE16(p+2) consistently?
        pair_dup = 0
        if p + 3 < body_len:
            for k in range(n_entries):
                v_a = triples[k][0][p] | (triples[k][0][p+1]<<8)
                v_b = triples[k][0][p+2] | (triples[k][0][p+3]<<8)
                v_a1 = triples[k][1][p] | (triples[k][1][p+1]<<8)
                v_b1 = triples[k][1][p+2] | (triples[k][1][p+3]<<8)
                if v_a == v_b and v_a1 == v_b1 and v_a > 0:
                    pair_dup += 1
        pos_roles.append({
            'pos': p,
            'constant_3stage': constant_across_stages,
            'byte_mono_increase': mono_count,
            'le16_mono_increase': le16_mono,
            'pair_duplicate_with_p+2': pair_dup,
        })
    return pos_roles


def main():
    files = {fn: extract((E_DIR/fn).read_bytes()) for fn in ['_BSDAT_0','_BSDAT_1','_BSDAT_2']}
    # group by body_len
    by_len = defaultdict(list)
    n = min(len(files['_BSDAT_0']), len(files['_BSDAT_1']), len(files['_BSDAT_2']))
    for k in range(n):
        n0, b0 = files['_BSDAT_0'][k]
        n1, b1 = files['_BSDAT_1'][k]
        n2, b2 = files['_BSDAT_2'][k]
        if n0 == n1 == n2 and len(b0)==len(b1)==len(b2):
            by_len[len(b0)].append((b0, b1, b2, n0))

    out = {'meta': {'round': 'R77', 'date': '2026-05-19',
                    'method': 'per-position role detection across 3 stages × entries'},
           'body_lens': {}}
    for L, triples in by_len.items():
        roles = analyze_layout([(t[0],t[1],t[2]) for t in triples], L)
        # filter strong stat candidates
        strong_le16 = [r for r in roles if r['le16_mono_increase'] >= max(3, len(triples)//2)]
        strong_dup = [r for r in roles if r['pair_duplicate_with_p+2'] >= max(3, len(triples)//2)]
        strong_const = [r for r in roles if r['constant_3stage'] == len(triples)]
        out['body_lens'][str(L)] = {
            'entry_count': len(triples),
            'sample_names': [t[3] for t in triples[:5]],
            'strong_le16_stat_positions': [r['pos'] for r in strong_le16],
            'max_current_pair_positions': [r['pos'] for r in strong_dup],
            'constant_positions_count': len(strong_const),
            'constant_positions': [r['pos'] for r in strong_const][:30],
            'all_roles': roles,
        }
        print(f"\n=== body_len={L} ({len(triples)} entries) ===")
        print(f"  samples: {[t[3] for t in triples[:5]]}")
        print(f"  constants (all 3 stages same): {len(strong_const)} positions: {[r['pos'] for r in strong_const]}")
        print(f"  LE16 monotonic stat positions: {[r['pos'] for r in strong_le16]}")
        print(f"  max/current pair (LE16(p)==LE16(p+2)) positions: {[r['pos'] for r in strong_dup]}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
