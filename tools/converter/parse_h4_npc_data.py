"""Hero4 NPC/E 디렉토리의 plaintext 게임 데이터 테이블 파서.

분석된 파일:

1. NPC/_NPCG_DAT (960B, 60 records × 16B):
   각 record = [0e 00 NPC_ID(1) ... 0xff padding]
   NPC general data table. 39 unique NPC ID (range 0..114).

2. NPC/_NPCG_DAT_ (688B, 43 records × 16B):
   유사 layout, NPCG_DAT 변형 버전 (다른 mode? 또는 다른 zone?).

3. E/_BGDAT (589B):
   첫 byte = 29 (= 0x1d). variable-length records, 0xff separator block.
   "Background Game Data" 추정 (terrain/tile properties?).

4. E/_EGDAT (5344B, 334 records × 16B):
   짝수 record (167): [1e 00 STAT1 STAT2 00 ATK DEF S1 S2 S3 S4 ff×5]
                      → enemy stats (HP/HP_max/atk/def/...)
   홀수 record (167): [ff 00 ff ff ff S5 S6 S7 S8 ff×6 INDEX(2)]
                      → enemy 보조 데이터 (drop? script?)
   "Enemy Game Data" — 167 enemy entry × 32B (paired 16B + 16B).

5. E/AI000~042 (43 files, 21~185B):
   AI script bytecode. 첫 byte = 0x01 (script start marker).
   본문 = 작은 byte values (0x00..0x30 주). enemy AI behavior 정의.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NPC_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'NPC'
E_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'E'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def parse_fixed_stride(data: bytes, stride: int, terminator: int = 0xff) -> list[dict]:
    records = []
    n = len(data) // stride
    for i in range(n):
        rec = data[i*stride:(i+1)*stride]
        pad_start = len(rec)
        for j in range(len(rec)):
            if rec[j] == terminator and all(b == terminator for b in rec[j:j+3] if j+3 <= len(rec)):
                pad_start = j
                break
        records.append({
            'idx': i,
            'body_size': pad_start,
            'body': list(rec[:pad_start]),
            'full_hex': rec.hex(),
        })
    return records


def parse_egdat(data: bytes) -> dict:
    """E/_EGDAT 167 enemy entries × 32B (paired 16B + 16B)."""
    entries = []
    n_pairs = len(data) // 32
    for i in range(n_pairs):
        stat = data[i*32:i*32+16]
        extra = data[i*32+16:(i+1)*32]
        # Parse stat record
        if stat[0] == 0x1e and stat[1] == 0x00:
            entries.append({
                'idx': i,
                'type_byte': stat[0],
                'stat1_hp': stat[2],
                'stat2_hp_max': stat[3],
                'pad4': stat[4],
                'atk': stat[5],
                'def': stat[6],
                'stat3': stat[7],
                'stat4': stat[8],
                'stat5': stat[9],
                'stat6': stat[10],
                'extra_byte_14_15': [extra[14], extra[15]],
                'extra_hex': extra.hex(),
                'extra_byte5': extra[5],  # secondary value
            })
        else:
            entries.append({'idx': i, 'malformed': True, 'stat_hex': stat.hex(), 'extra_hex': extra.hex()})
    return {
        'enemy_count': n_pairs,
        'entries': entries,
    }


def parse_ai_script(data: bytes) -> dict:
    """E/AI bytecode 추정 분석 (정확한 opcode 의미는 Ghidra 후)."""
    return {
        'size': len(data),
        'first_byte': data[0] if data else None,
        'starts_with_01': data[:1] == b'\x01',
        'byte_dist_top10': Counter(data).most_common(10),
        'hex_preview': data[:48].hex(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    args = ap.parse_args()

    out = {}

    # _NPCG_DAT
    f = NPC_DIR / '_NPCG_DAT'
    if f.exists():
        d = f.read_bytes()
        recs = parse_fixed_stride(d, 16)
        npc_ids = [r['body'][2] for r in recs if len(r['body']) > 2]
        out['NPCG_DAT'] = {
            'size': len(d),
            'records': len(recs),
            'stride': 16,
            'unique_npc_ids': len(set(npc_ids)),
            'npc_id_range': [min(npc_ids), max(npc_ids)] if npc_ids else None,
            'sample_first_10': recs[:10],
        }

    # _NPCG_DAT_
    f = NPC_DIR / '_NPCG_DAT_'
    if f.exists():
        d = f.read_bytes()
        recs = parse_fixed_stride(d, 16)
        out['NPCG_DAT_'] = {
            'size': len(d),
            'records': len(recs),
            'stride': 16,
            'sample_first_5': recs[:5],
        }

    # _EGDAT — enemy data
    f = E_DIR / '_EGDAT'
    if f.exists():
        d = f.read_bytes()
        out['EGDAT'] = parse_egdat(d)
        out['EGDAT']['size'] = len(d)

    # _BGDAT
    f = E_DIR / '_BGDAT'
    if f.exists():
        d = f.read_bytes()
        out['BGDAT'] = {
            'size': len(d),
            'first_byte': d[0],
            'hex_preview': d[:64].hex(),
            'note': 'variable-length records, 0xff separator',
        }

    # AI scripts
    ai_files = sorted(E_DIR.glob('AI*'))
    out['AI_scripts'] = {
        'count': len(ai_files),
        'size_range': [min(f.stat().st_size for f in ai_files),
                       max(f.stat().st_size for f in ai_files)] if ai_files else None,
        'samples': [
            {'file': f.name, **parse_ai_script(f.read_bytes())}
            for f in ai_files[:5]
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'npc_e_data_parsed.json'
    with open(out_path, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    # Summary print
    print(f'-> {out_path}')
    print(f'\n=== _NPCG_DAT ({out["NPCG_DAT"]["records"]} records × 16B) ===')
    print(f'  Unique NPC IDs: {out["NPCG_DAT"]["unique_npc_ids"]}, range {out["NPCG_DAT"]["npc_id_range"]}')
    print(f'\n=== _EGDAT ({out["EGDAT"]["enemy_count"]} enemy entries × 32B) ===')
    well_formed = sum(1 for e in out['EGDAT']['entries'] if not e.get('malformed'))
    print(f'  Well-formed (type=0x1e header): {well_formed} / {out["EGDAT"]["enemy_count"]}')
    if well_formed > 0:
        first = next(e for e in out['EGDAT']['entries'] if not e.get('malformed'))
        print(f'  First enemy entry: hp={first["stat1_hp"]}/{first["stat2_hp_max"]}, '
              f'atk={first["atk"]}, def={first["def"]}, stats={[first[f"stat{i}"] for i in range(3,7)]}')
    print(f'\n=== AI scripts: {out["AI_scripts"]["count"]} files, size {out["AI_scripts"]["size_range"]} ===')

    return 0


if __name__ == '__main__':
    sys.exit(main())
