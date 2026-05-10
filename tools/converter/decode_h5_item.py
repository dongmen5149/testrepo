"""
item_NN.dat 디코더.

표준 csv 와 다른 포맷:
  u16 count
  records:
    u16 record_size
    u16 prefix (icon_id 또는 item_category 추정)
    u8 strlen
    bytes[strlen] (EUC-KR 이름)
    bytes[record_size - 3 - strlen] (stats)

검증 (item_00.dat 첫 record):
  count=86, size=0x2a (42), prefix=0xc7 (199), strlen=6, "롱소드", extra=33B

slot_N → ItemTable category (분석 결과, ITEM_STRUCT.md 참조):
  slot_0..slot_10 = EquipItemInfo (weapon/armor/etc, 376B runtime record)
  slot_11        = BattleUseItemInfo (potion, 312B) — 4 byte ext
  slot_12        = BattleUseItemInfo (scroll, 312B) — 4 byte ext (Round 19)
  slot_13        = OrbItemInfo (gem/orb, 312B) — 2 byte ext
  slot_14, 15    = MixItemInfo (alchemy material, 308B)
  slot_16        = MixBookItemInfo (recipe book, 324B) — 12 byte ext (Round 19)
  slot_17        = SkillBookItemInfo (skill book, 312B) — 4 byte ext (Round 20)
  slot_18        = CashItemInfo (premium item, 312B) — 2 byte ext (Round 20)

산출:
  apps/hero5-godot/assets/gamedata/items.json
"""
from __future__ import annotations
import csv, pathlib, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'items.json'


CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'

# slot_N → 카테고리 메타데이터 (ItemTable::GetItemTableInfo dispatch 참조)
SLOT_META = {
    0:  {"category": "equip", "kind": "weapon",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    1:  {"category": "equip", "kind": "weapon_2",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    2:  {"category": "equip", "kind": "weapon_3",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    3:  {"category": "equip", "kind": "weapon_4",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    4:  {"category": "equip", "kind": "armor",        "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    5:  {"category": "equip", "kind": "helmet",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    6:  {"category": "equip", "kind": "boots",        "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    7:  {"category": "equip", "kind": "accessory",    "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    8:  {"category": "equip", "kind": "accessory_2",  "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    9:  {"category": "equip", "kind": "shield",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    10: {"category": "equip", "kind": "spirit",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    # Round 23: SLOT_META 정정 — record 이름 + ext_after_sb 길이 cross-check 로:
    # slot_11: 포션/미들포션/엘릭서 (포션류, 4 byte ext) ✓ BattleUseItem
    # slot_12: 뇌제의오브/금강의오브/정령의오브 (오브, 2 byte ext) — 이전 'scroll' 잘못
    # slot_13: 살코기/황혼버섯/재료2..9 (mix material, 0 ext) — 이전 'orb' 잘못
    # slot_14: 전갈갑피/은빛귀걸이/광휘의열쇠 (mix material_2, 0 ext)
    # slot_15: 황혼수프가루/포션/엘릭서 (mix_book recipe, 13 byte ext) — 이전 'material_2' 잘못
    11: {"category": "battle_use", "kind": "potion",     "runtime_struct": "BattleUseItemInfo",  "runtime_size": 312},
    12: {"category": "orb",       "kind": "orb",         "runtime_struct": "OrbItemInfo",        "runtime_size": 312},
    13: {"category": "mix",       "kind": "material",    "runtime_struct": "MixItemInfo",        "runtime_size": 308},
    14: {"category": "mix",       "kind": "material_2",  "runtime_struct": "MixItemInfo",        "runtime_size": 308},
    15: {"category": "mix_book",  "kind": "recipe",      "runtime_struct": "MixBookItemInfo",    "runtime_size": 324},
    # Round 21: slot_16 은 실제로 SkillBookItem (Warrior+Rogue 스킬북: 양손베기/돌진/
    # 내려찍기 등). HERO::IfLearnSkill 의 (class_id/2)+16 공식이 cat 16 = Warrior(0)/
    # Rogue(1) 매핑. 기존 "mix_book" 라벨은 잘못.
    16: {"category": "skill_book", "kind": "skill_book_wr", "runtime_struct": "SkillBookItemInfo", "runtime_size": 312},
    17: {"category": "skill_book", "kind": "skill_book_gk", "runtime_struct": "SkillBookItemInfo", "runtime_size": 312},
    18: {"category": "cash",       "kind": "cash_item",     "runtime_struct": "CashItemInfo",      "runtime_size": 312},
}


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_by_hash(name: str) -> pathlib.Path | None:
    """asset_names.tsv 가 false-positive 인 경우 (item_NN 등) catalog 에서
    hash 직접 매칭."""
    target_h = djb2(name.encode())
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target_h:
                idx = int(r['index'])
                return ENTRIES / f'{idx:05d}_{target_h:08x}.bin'
    return None


def find(target: str) -> pathlib.Path | None:
    return find_by_hash(target)


def parse_common_extra(extra: bytes) -> dict:
    """모든 카테고리 공통 layout (Round 18 — LoadItemTable 의 cat 12-18 cross-check):
       extra +0..+3: u32 → struct +0x30 (item_id)
       extra +4: u8 sub_record_len
       extra +5..(4+sblen): sub-record bytes (struct +0x34..+0x134, 256B padded)

    EquipItem (cat 1-11) 만 sb 영역 (struct +0x150..+0x167) 가 추가로 있음 —
    parse_equip_extra 가 추가 처리.
    """
    if len(extra) < 5:
        return {}
    item_id = struct.unpack_from('<I', extra, 0)[0]
    sblen = extra[4]
    if 5 + sblen > len(extra):
        return {'item_id': item_id, 'sub_record_len': sblen}
    sub_record = extra[5:5 + sblen]
    return {
        'item_id': item_id,
        'sub_record_len': sblen,
        'sub_record_hex': sub_record.hex(),
    }


def parse_battle_use_extra(extra: bytes) -> dict:
    """BattleUseItem (slot_11 only) 의 추가 4 byte fields (struct +0x134..+0x137).

    HERO::BattleUseItem (0x8fd20, 536B) 분석으로 의미 식별 (Round 23):
      +0x134 (effect_type) HERO+0x2fe 에 저장 → CalcStatusComputation 분기:
        91 (0x5b): HP heal — 포션/미들포션/하이포션/훈련용물약/포션ex 등
        90 (0x5a): SP heal — 퀵포션/미들퀵포션/엘릭서 등
        87 (0x57): buff (보호의 부적) — HERO[0x19c] = 100 set
        92 (0x5c): special — 마석
        19 (0x13): test — 포션9
         0      : 제련석 (취급 불가능)
      +0x135 (success_rate %) random(0,99) 와 비교 → blt 면 적용 (모든 records 100)
      +0x136 (effect_value) HERO+0x300 (u16) 에 저장 → 실제 회복량 또는 buff 강도
        포션 LV1/2/3: 4/10/20, 퀵포션 LV1/2/3: 40/100/160, 엘릭서: 250
      +0x137 (duration) HERO+0x302 (s16) 에 저장 → 지속 시간 또는 보조 파라미터
        HP buff: 50, SP instant: 1, 보호의부적: 120 (turn duration)
      이후 SetPotionCoolTime(100) — 포션 cooldown 100 frames.
    """
    if len(extra) < 5:
        return {}
    sblen = extra[4]
    sb_start = 5 + sblen
    if sb_start + 4 > len(extra):
        return {}
    return {
        'effect_type': extra[sb_start + 0],   # +0x134 → HERO+0x2fe
        'success_rate': extra[sb_start + 1],  # +0x135
        'effect_value': extra[sb_start + 2],  # +0x136 → HERO+0x300 (u16)
        'duration': extra[sb_start + 3],      # +0x137 → HERO+0x302 (s16)
    }


def parse_orb_extra(extra: bytes) -> dict:
    """OrbItem (cat 13) 의 추가 2 byte fields (struct +0x134..+0x135)."""
    if len(extra) < 5:
        return {}
    sblen = extra[4]
    sb_start = 5 + sblen
    if sb_start + 2 > len(extra):
        return {}
    return {
        'val_134': extra[sb_start + 0],
        'val_135': extra[sb_start + 1],
    }


def parse_skill_book_extra(extra: bytes) -> dict:
    """SkillBookItem (slot_16, slot_17) 의 추가 4 byte fields (struct +0x134..+0x137).

    LoadItemTable @0xa47c0 disasm (Round 20):
      record_size = 0x138 (312B). jumptable case 16/17 모두 동일 코드 path 공유.
      common base 후 sb 시작 위치 (5+sblen) 부터 4 byte:
        +0: u8 → struct +0x134  class_id (HERO 클래스, 0..4)
        +1: u8 → struct +0x135  skill_index (HERO::skills[] 배열 인덱스)
        +2: u8 → struct +0x136  skill_level (1, 2, 3, ...)
        +3: u8 → struct +0x137  required_level (HERO 레벨 요구치)

    HERO::IfLearnSkill (Round 21 — 0x95d08, 316B) 분석으로 의미 확정:
      - 공식 (class_id/2)+16 → ItemTable category 결정:
        Warrior(0)/Rogue(1) → cat 16 (slot_16)
        Gunslinger(2)/Knight(3) → cat 17 (slot_17)
        Sorcerer(4) → cat 18 (slot_18, CashItem — Sorcerer 별도 처리 추정)
      - +0x135 (skill_index) 가 HERO+0x248+skill_index 의 byte 와 cmp →
        이미 학습 여부 확인.
      - +0x137 (required_level) 가 HERO+0x22d 와 cmp → bgt 면 학습 불가.

    검증: slot_17 records '연속사격LV1..LV4' → skill_level = 1, 2, 3, 4 정확 매칭.
    val_137 monotonically increasing (1, 4, 10, 22) — required level 성장.
    slot_16 records '양손베기LV1..3', '돌진LV1..4' 등 Warrior 스킬 95개.
    """
    if len(extra) < 5:
        return {}
    sblen = extra[4]
    sb_start = 5 + sblen
    if sb_start + 4 > len(extra):
        return {}
    return {
        'class_id': extra[sb_start + 0],
        'skill_index': extra[sb_start + 1],
        'skill_level': extra[sb_start + 2],
        'required_level': extra[sb_start + 3],
    }


def parse_cash_extra(extra: bytes) -> dict:
    """CashItem (slot_18) 의 추가 2 byte fields (struct +0x134..+0x135).

    LoadItemTable @0xa3b38 disasm (Round 20):
      record_size = 0x138 (312B). jumptable case 18 의 단독 코드 path —
      hardcoded type 0x12=18 at +0x14. SkillBook(case 16/17) 와 다른 layout.
      common base 후 sb 시작 위치 (5+sblen) 부터 2 byte:
        +0: u8 → struct +0x134
        +1: u8 → struct +0x135
      관찰: slot_18 records '창고확장(nt)', '프리미엄판매' 등 — premium/cash shop
      items 의 metadata. 2 byte 의미는 다음 라운드 CashItemInfo::Use 분석으로 식별.
    """
    if len(extra) < 5:
        return {}
    sblen = extra[4]
    sb_start = 5 + sblen
    if sb_start + 2 > len(extra):
        return {}
    return {
        'val_134': extra[sb_start + 0],
        'val_135': extra[sb_start + 1],
    }


def parse_mix_book_extra(extra: bytes) -> dict:
    """MixBookItem (slot_15, recipe) 의 13 byte ext.

    LoadItemTable @0xa4578 (case 15) disasm: record_size = 0x144 (324B), sb_loop
    가 13 byte 를 struct +0x134..+0x140 영역에 sub-byte indexing 으로 저장.

    Round 25: items.json 116 records 패턴 분석으로 layout 확정 (이름 cross-check):
      byte  0: 0x00 (separator/version flag)
      bytes 1..3: ingredient 1 — (cat: u8, idx: u8, count: u8)
      bytes 4..6: ingredient 2 — (cat, idx, count) or (0xff, 0xff, 0x00/0xff) if unused
      bytes 7..9: ingredient 3 — same format
      bytes 10..11: result — (cat: u8, idx: u8) — count = 1
      byte 12: success_rate % (0x64=100, 0x5a=90)

    cat 인덱스는 items.json 의 slot_NN 과 동일 (0=weapon, 0xb=potion, 0xd=mix
    material, 0xe=mix material_2, 0xf=mix book recipe).

    Recipe 패턴 검증:
      - 쿠킹 (cat 0xe 결과): 살코기+황혼버섯 → 황혼수프가루 (100%)
      - 포션 합성 (cat 0xb 결과): 포션 ×2 → 미들포션 (100%)
      - 퀵포션 (cat 0xb 결과): 포션 ×2 + 지혈초 ×1 → 퀵포션 (100%)
      - 재료 정제 (cat 0xd 결과): 엑토플라즘 ×10 → 에테르 (90%)
      - 무기 제작 (cat 0..3 결과): 칼날 ×20 + 가죽 ×6 + 강철 ×3 → 투란기어 (90%)
    """
    if len(extra) < 5:
        return {}
    sblen = extra[4]
    sb_start = 5 + sblen
    if sb_start + 13 > len(extra):
        return {}
    sb = extra[sb_start:sb_start + 13]

    def parse_ing(c: int, i: int, ct: int) -> dict | None:
        """0xff sentinel 면 None 반환."""
        if c == 0xff:
            return None
        return {'cat': c, 'idx': i, 'count': ct}

    return {
        'sb_extra_hex': sb.hex(),
        'recipe': {
            'ing1': parse_ing(sb[1], sb[2], sb[3]),
            'ing2': parse_ing(sb[4], sb[5], sb[6]),
            'ing3': parse_ing(sb[7], sb[8], sb[9]),
            'result_cat': sb[10],
            'result_idx': sb[11],
            'success_rate': sb[12],
        },
    }


def parse_equip_extra(extra: bytes) -> dict:
    """EquipItem (cat 1-11) extra 의 가변 layout parse.

    Round 14 의 LoadItemTable disasm 으로 확정된 layout:
      +0..+3: u32 → struct +0x30 (item_id 또는 large flag)
      +4: u8 sub_record_len (sblen)
      +5..(4+sblen): sub-record bytes (struct +0x34..+0x134, 256B padded)
      sb 위치 (= 5+sblen) 부터:
        +0..+1: u16 → struct +0x150
        +2..+3: u16 → struct +0x152
        +4: u8 → struct +0x154
        +5: u8 → struct +0x155 (class_restriction)
        +6..+7: u16 → struct +0x156
        +8..+9: u16 → struct +0x158
        +0xa..+0xb: u16 → struct +0x15a
        +0xc: u8 → struct +0x15c
        +0xd: u8 → struct +0x15d (level_limit)
        +0xe: u8 → struct +0x15e
        +0xf: u8 → struct +0x15f
        +0x10: u8 → struct +0x160
        +0x11..+0x13: u8 ×3 → struct +0x162..+0x164
    """
    if len(extra) < 5:
        return {}
    pos = 0
    item_id = struct.unpack_from('<I', extra, pos)[0]; pos += 4
    sblen = extra[pos]; pos += 1
    if pos + sblen > len(extra):
        return {'item_id': item_id, 'sub_record_len': sblen}
    sub_record = extra[pos:pos + sblen]; pos += sblen
    res: dict = {'item_id': item_id, 'sub_record_hex': sub_record.hex()}
    # sb 영역 — 안전하게 length check
    def _u16(o: int) -> int | None:
        return struct.unpack_from('<H', extra, pos + o)[0] if pos + o + 2 <= len(extra) else None
    def _u8(o: int) -> int | None:
        return extra[pos + o] if pos + o < len(extra) else None
    res['val_150'] = _u16(0)
    res['val_152'] = _u16(2)
    res['val_154'] = _u8(4)
    # Round 16: +0x155 가 class_restriction 아니라 subtype code 임이 IsEquipPossible
    # cross-check 로 확인됨 (slot_10 spirit 의 cls=5 가 17 records 인데 SpiritEquip
    # 은 cls=7 만 허용 — 즉 cls 가 weapon/armor sub-type 분류). 진짜 class mask 는
    # val_15f 후보 (다음 라운드 검증).
    res['subtype'] = _u8(5)              # struct +0x155 (이전 class_restriction 잘못)
    res['val_156'] = _u16(6)
    res['val_158'] = _u16(8)
    res['val_15a'] = _u16(0xa)
    res['val_15c'] = _u8(0xc)
    res['level_limit'] = _u8(0xd)        # struct +0x15d
    res['val_15e'] = _u8(0xe)
    # Round 16: val_15f & 0x1f = 5 클래스 비트 마스크 (W=1/R=2/G=4/K=8/S=16)
    # 검증: val=31 (WRGKS all) 385 records, val=0 43 records, val=9 (WK) 31, val=17 (WS) 40.
    # Round 24: val_15f >> 5 (upper 3 bit) 의 의미 식별 — items.json cross-check 결과:
    #   upper=0 (170 records): 보스/전설 named weapons (실가라스/디바인세이버 등)
    #   upper=1 (248 records, bit5): 중급 무기/방어구
    #   upper=3 (9 records, bit5+6): slot_5 보석 헤어핀/서클릿 (청금석/루비 등)
    #   upper=7 (362 records, bit5+6+7): 일반 상점 아이템 (롱소드/단검 등)
    # 가설: bit5 = "obtainable" (named legendary 외), bit6 = "gem-accessory" (보석류
    # 전용 액세서리), bit7 = "common-tier" (상점/낮은 등급).
    # 정확한 게임 의미는 SetItemOption 동작과는 별개 — runtime val_15f 는
    # SetItemOption 실행 후 option_type code 로 overwrite (RefineItem +0x6c='l' 등).
    val_15f = _u8(0xf)
    res['val_15f'] = val_15f
    if val_15f is not None:
        mask = val_15f & 0x1f
        res['class_mask'] = mask
        labels = []
        if mask & 1:  labels.append('W')
        if mask & 2:  labels.append('R')
        if mask & 4:  labels.append('G')
        if mask & 8:  labels.append('K')
        if mask & 16: labels.append('S')
        res['class_label'] = ''.join(labels) or '-'
        # Round 24: upper 3 bit (tier flags)
        tier = val_15f >> 5
        res['tier_flags'] = tier
        # 실증적 라벨 (items.json 분포 기반 — 정확한 의미 추후 확정)
        res['tier_label'] = {
            0: 'legendary',  # boss/named items
            1: 'rare',       # mid-tier
            3: 'gem',        # slot_5 gem headwear only
            7: 'common',     # shop basic
        }.get(tier, f'tier_{tier}')
    res['val_160'] = _u8(0x10)
    triplet = []
    for o in (0x11, 0x12, 0x13):
        b = _u8(o)
        if b is None: break
        triplet.append(b)
    res['triplet_162'] = triplet
    return res


def parse_items(d: bytes, slot_idx: int = -1) -> list[dict]:
    if len(d) < 2: return []
    count = struct.unpack_from('<H', d, 0)[0]
    pos = 2
    is_equip = SLOT_META.get(slot_idx, {}).get("category") == "equip"
    out = []
    for i in range(count):
        if pos + 5 > len(d): break
        rec_sz = struct.unpack_from('<H', d, pos)[0]; pos += 2
        if pos + rec_sz > len(d): break
        body_start = pos
        prefix = struct.unpack_from('<H', d, pos)[0]; pos += 2
        strlen = d[pos]; pos += 1
        if strlen > rec_sz - 3:
            pos = body_start + rec_sz
            out.append({'idx': i, 'name': '?', 'prefix': prefix, 'extra_hex': ''})
            continue
        try:
            name = d[pos:pos + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        pos += strlen
        extra_len = rec_sz - 3 - strlen
        extra = d[pos:pos + extra_len]
        pos += extra_len
        n_u16 = len(extra) // 2
        u16 = list(struct.unpack(f'<{n_u16}H', extra[:n_u16*2])) if n_u16 else []
        rec = {
            'idx': i,
            'name': name,
            'prefix': prefix,    # icon_id 또는 category
            'price': u16[0] if u16 else 0,
            'stats_u16': u16,
            'extra_hex': extra.hex(),
        }
        # Round 18: 모든 카테고리에 common base (item_id + sub_record_hex) 부여.
        # Round 19: 카테고리별 추가 fields parser dispatch.
        rec.update(parse_common_extra(extra))
        cat = SLOT_META.get(slot_idx, {}).get("category", "")
        if cat == "equip":              # cat 1-11
            rec.update(parse_equip_extra(extra))
        elif cat == "battle_use":       # slot_11 only (potion, 4 byte ext)
            rec.update(parse_battle_use_extra(extra))
        elif cat == "orb":              # slot_12 (orb, 2 byte ext)
            rec.update(parse_orb_extra(extra))
        elif cat == "mix_book":         # slot_15 (recipe, 13 byte ext)
            rec.update(parse_mix_book_extra(extra))
        elif cat == "skill_book":       # slot_17 (4 byte ext)
            rec.update(parse_skill_book_extra(extra))
        elif cat == "cash":             # slot_18 (2 byte ext)
            rec.update(parse_cash_extra(extra))
        # 'mix' (cat 14, 15) 는 추가 fields 없음 (record_size 0x134 = base)
        out.append(rec)
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # 호환성: 기존 GameData loader 가 data["slot_N"] 직접 접근. 평면 구조 유지하고
    # 메타데이터는 별도 key 로.
    all_items: dict = {"_meta": {"category_dispatch": SLOT_META}}
    total = 0
    for slot in range(19):  # item_00..item_18
        p = find(f'c/csv/item_{slot:02d}.dat')
        if not p: continue
        items = parse_items(p.read_bytes(), slot_idx=slot)
        all_items[f'slot_{slot}'] = items
        meta = SLOT_META.get(slot, {})
        named = sum(1 for x in items if x.get('name', '').strip() and x['name'] != '?')
        total += named
        print(f'item_{slot:02d} ({meta.get("kind", "?"):<14}): {len(items)} records, {named} named')
        for x in items[:5]:
            print(f'  prefix=0x{x.get("prefix",0):04x}  price={x.get("price", 0):>4}  {x.get("name","?")!r}  stats={x.get("stats_u16",[])[:6]}')

    OUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT} (total {total} named items)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
