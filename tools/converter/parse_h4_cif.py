"""Hero4 _H_NNN_CIF 캐릭터 정보 파일 파서.

Hero3 의 `convert_cif.py:parse_cif` 와 동일한 헤더 schema:
    byte 0           : slot_count (sprite 슬롯 갯수)
    byte 1           : category   (entity 분류)
    byte 2..2+slot_count : sprite_indices (1..51 범위)
    bytes nb (post-header): animation_data (size 가변)

Hero4 분포 (117 파일):
    slot_count: 1(51) > 6(33) > 4(12) > 2(11) > 8(4) > 3(4) > 5(2)
    category : 0(27) > 2(23) > 1(15) > 3(11) > 4..28 (희소)

slot=8, category=0: 4 hero CIFs (_H_001..004) — 메인 캐릭터 4명, 86~135KB
slot=6, category=0~25: 33 NPC/enemy CIFs — 1.3~41KB
slot=1, category=0~27: 51 single-slot CIFs — 10B~33KB, 다양한 special entity

sprite_indices: 모든 117 CIF 종합 1..51 range
    → 51개의 sprite "slot pool" 을 4 hero + 33 NPC/enemy + 시스템 entity 가 공유.
    실제 sprite asset 은 OBJ/ 247 파일이지만, CIF 의 indices 는 별도 sprite "slot
    table" 을 가리키는 것으로 보임 (정확한 매핑은 Phase B Ghidra).

CIF ↔ EXD pair 가설: 117개 CIF + 117개 EXD = 1:1 페어, 같은 entity 의 sprite 정의 + box layout 정의.

animation_data 영역의 정확한 byte stride / opcode 는 Hero3 와 다를 수 있음 (Hero3 hero=41B
fixed stride, boss/enemy=4B cell stream). Hero4 는 sample 분석 후 확정.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CIF_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4' / 'CIF'
EXD_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4' / 'EXD'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'cif_parsed.json'


def parse_cif(data: bytes) -> dict:
    """Hero3-compatible CIF header parse."""
    if len(data) < 2:
        return {'slot_count': 0, 'category': 0, 'indices': [], 'anim_size': 0, 'error': 'too_short'}
    slot_count = data[0]
    category = data[1]
    end = 2 + slot_count
    indices = list(data[2:end]) if end <= len(data) else list(data[2:])
    rest = data[end:] if end <= len(data) else b''
    return {
        'slot_count': slot_count,
        'category': category,
        'indices': indices,
        'anim_size': len(rest),
        'anim_first_16': rest[:16].hex(),
    }


def classify_entity(parsed: dict) -> str:
    """Heuristic entity classification by (slot_count, category, anim_size)."""
    sc = parsed['slot_count']
    cat = parsed['category']
    sz = parsed['anim_size']
    if sc == 8 and cat == 0:
        return 'hero'                    # 4 main characters
    if sc == 6 and cat == 0:
        return 'major_npc'               # 10 major NPCs
    if sc == 6 and cat in (1, 2, 3):
        return 'enemy_or_npc'            # boss/enemy/secondary NPC
    if sc == 6:
        return 'special_6slot'
    if sc == 4:
        return 'minor_npc' if cat <= 3 else 'special_4slot'
    if sc == 1:
        if sz < 100:
            return 'system_or_marker'    # 작은 metadata
        return 'single_entity'           # boss/quest item/dialog speaker
    if sc == 2:
        return 'small_npc'
    if sc == 3:
        return 'mid_entity'
    if sc == 5:
        return 'rare_5slot'
    return f'unknown_slot{sc}_cat{cat}'


def detect_anim_stride(anim: bytes, entity_class: str) -> dict:
    """Hero3 animation stride hypothesis verification.
    Hero3: hero=41B fixed stride / boss-enemy=4B cell stream.
    """
    if not anim:
        return {'stride': None, 'frames': 0, 'fit': 'empty'}
    if entity_class == 'hero':
        # Try 41B stride after a possible 0-N byte prologue
        for prologue in range(0, 32):
            body = anim[prologue:]
            if len(body) > 0 and len(body) % 41 == 0:
                return {'stride': 41, 'prologue_bytes': prologue,
                        'frames': len(body) // 41, 'fit': 'hero_41B'}
        return {'stride': 41, 'frames': len(anim) // 41,
                'fit': 'hero_41B_approx', 'remainder': len(anim) % 41}
    # NPC / enemy: try 4B stride
    if len(anim) % 4 == 0:
        return {'stride': 4, 'frames': len(anim) // 4, 'fit': 'enemy_4B'}
    # Try with prologue
    for prologue in range(0, 16):
        body = anim[prologue:]
        if len(body) > 0 and len(body) % 4 == 0:
            return {'stride': 4, 'prologue_bytes': prologue,
                    'frames': len(body) // 4, 'fit': 'enemy_4B'}
    return {'stride': 4, 'frames': len(anim) // 4,
            'fit': 'enemy_4B_approx', 'remainder': len(anim) % 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    args = ap.parse_args()

    files = sorted(CIF_DIR.glob('_H_*_CIF'))
    parsed = []
    by_class = Counter()
    by_slot = Counter()
    by_cat = Counter()
    indices_used = Counter()

    for f in files:
        d = f.read_bytes()
        r = parse_cif(d)
        r['file'] = f.name
        r['size'] = len(d)
        r['entity_class'] = classify_entity(r)
        # Animation stride
        anim_data = d[2 + r['slot_count']:]
        r['anim_stride_info'] = detect_anim_stride(anim_data, r['entity_class'])
        # Pair EXD
        exd_name = f.name.replace('_CIF', '_EXD')
        exd_path = EXD_DIR / exd_name
        r['exd_paired'] = exd_path.exists()
        parsed.append(r)
        by_class[r['entity_class']] += 1
        by_slot[r['slot_count']] += 1
        by_cat[r['category']] += 1
        for idx in r['indices']:
            indices_used[idx] += 1

    out = {
        'files': len(parsed),
        'distribution': {
            'entity_class': dict(by_class),
            'slot_count': dict(by_slot),
            'category': dict(by_cat),
        },
        'sprite_slot_usage': {
            'index_range': [min(indices_used.keys()), max(indices_used.keys())] if indices_used else [0, 0],
            'unique_slots_used': len(indices_used),
            'top10_used_slots': [{'slot': s, 'refs': c} for s, c in indices_used.most_common(10)],
        },
        'parsed': parsed,
    }
    exd_paired = sum(1 for p in parsed if p['exd_paired'])
    out['exd_pairing_rate'] = f'{exd_paired}/{len(parsed)}'

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print(f'Parsed {len(parsed)} CIF files -> {args.out}')
    print(f'\nEntity class distribution:')
    for k, v in by_class.most_common():
        print(f'  {k:25}: {v}')
    print(f'\nSprite slot usage:')
    print(f'  index range: {out["sprite_slot_usage"]["index_range"]}')
    print(f'  unique slots used: {out["sprite_slot_usage"]["unique_slots_used"]} / 51 possible')
    print(f'  top10 slots: {out["sprite_slot_usage"]["top10_used_slots"]}')
    print(f'\nCIF<->EXD pairing: {out["exd_pairing_rate"]}')

    print(f'\n=== Hero CIFs (slot=8, category=0) ===')
    for p in parsed:
        if p['entity_class'] == 'hero':
            print(f'  {p["file"]:18} ({p["size"]}B) indices={p["indices"]} anim={p["anim_size"]}B '
                  f'stride={p["anim_stride_info"]}')

    # Stride fit summary
    fit_c = Counter()
    for p in parsed:
        fit_c[p['anim_stride_info'].get('fit', 'unknown')] += 1
    print(f'\n=== Anim stride fit distribution ===')
    for k, v in fit_c.most_common():
        print(f'  {k}: {v}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
