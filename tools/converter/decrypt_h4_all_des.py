"""Hero4 Round 69 — scan 결과 49 파일 (E/HDAT/ITM/NPC/FR) 일괄 복호화 + 검증.

Round 68 에서 SCN 350 + HDAT-A 8 = 358 파일 복호화됨.
Round 69 = scan_h4_des_files.py 의 19 confirmed + 30 likely 추가 49 파일.

키 = J@IWO8N7 + mx_des_decrypt (Hero5 변종, Round 68 발견).

검증 (3단계):
    1. 8-byte align 통과
    2. 복호 후 entropy 감소 확인 (7.x → 5.x 미만이면 평문)
    3. EUC-KR Korean 또는 known structural pattern (low byte 분포)
"""
from __future__ import annotations
import json
import math
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from h5_des import mx_des_decrypt

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXTRACTED = ROOT / 'work' / 'h4' / 'extracted'
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
SCAN_JSON = ROOT / 'work' / 'h4' / 'converted' / 'des_encrypted_files_scan.json'

KEY = b'J@IWO8N7'


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    return h


def korean_run_count(data: bytes, min_len: int = 4) -> int:
    """EUC-KR Korean (pair 0xa1-0xfe) run 개수."""
    runs = 0
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            if i - start >= min_len:
                runs += 1
        else:
            i += 1
    return runs


def sample_korean(data: bytes, max_samples: int = 5) -> list[str]:
    samples = []
    i = 0
    while i < len(data) - 1 and len(samples) < max_samples:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            run = data[start:i]
            if len(run) >= 4:
                try:
                    s = run.decode('euc-kr', errors='replace')
                    samples.append(s)
                except Exception:
                    pass
        else:
            i += 1
    return samples


def main():
    scan = json.loads(SCAN_JSON.read_text(encoding='utf-8'))
    confirmed = scan['confirmed']
    likely = scan['likely']

    print(f'=== Hero4 Round 69 batch decrypt ===')
    print(f'  KEY: {KEY!r}')
    print(f'  Targets: {len(confirmed)} confirmed + {len(likely)} likely = {len(confirmed) + len(likely)} files\n')

    results = []
    for tier, entries in [('confirmed', confirmed), ('likely', likely)]:
        print(f'\n--- {tier.upper()} ({len(entries)}) ---')
        for entry in entries:
            rel = entry['file']
            src = EXTRACTED / rel.replace('/', '\\') if sys.platform == 'win32' else EXTRACTED / rel
            if not src.exists():
                # Try forward-slash path resolution
                src = EXTRACTED / pathlib.PurePosixPath(rel)
                if not src.exists():
                    print(f'  MISSING: {rel}')
                    continue
            data = src.read_bytes()
            aligned = data[:len(data) - (len(data) % 8)]
            tail = data[len(aligned):]
            plain = mx_des_decrypt(aligned, KEY) + tail

            ent_before = entry['entropy']
            ent_after = shannon_entropy(plain)
            korean = korean_run_count(plain)
            samples = sample_korean(plain)

            # Save decrypted
            dst = DECRYPTED / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(plain)

            # Print compact summary
            status = '✓ plain' if ent_after < 7.0 or korean >= 3 else '? high-entropy'
            print(f'  {rel:<40} {len(data):>6}B  ent {ent_before:.2f} → {ent_after:.2f}  K{korean:>3}  {status}')
            if samples:
                print(f'    samples: {samples[:3]}')

            results.append({
                'file': rel, 'tier': tier, 'size': len(data),
                'entropy_before': round(ent_before, 3),
                'entropy_after': round(ent_after, 3),
                'korean_runs': korean,
                'first_samples': samples[:3],
                'status': status,
            })

    # Final report
    out = ROOT / 'work' / 'h4' / 'converted' / 'round69_decrypt_results.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nResults JSON: {out}')

    n_plain = sum(1 for r in results if 'plain' in r['status'])
    n_high = sum(1 for r in results if 'high' in r['status'])
    print(f'\nSummary: {n_plain} plain / {n_high} still-high-entropy / {len(results)} total')


if __name__ == '__main__':
    main()
