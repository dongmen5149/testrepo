# Hero5 ItemInfo / EquipItemInfo 구조체 layout (부분)

원본: `tools/h5_disasm_item_funcs.py` → `work/h5/analysis/item_funcs.txt`

`EquipItemInfo::CopyData(EquipItemInfo*)` 의 ldr/str 오프셋 패턴에서 추출.
**부분만** — CopyData 가 모든 필드를 복사한다는 보장은 없음.

---

## EquipItemInfo (총 크기 ≥ 0x178 = 376B, ItemTable record size 0x178)

`tools/h5_dump_caller.py _ZN13EquipItemInfo*` 로 disasm. CopyData / IsEquipPossible /
GetLevelLimit 분석 결과 (Round 13 — 2026-05-10):

| offset | 크기 | 의미 | 근거 |
|---:|---:|---|---|
| `+0x02` | u8/u16 | 아이템 타입/카테고리 | (이전 라운드) |
| `+0x04` | u32 | itemID 또는 32-bit field | (이전 라운드) |
| `+0x08` | u32 | ? (probably stat) | |
| `+0x0c` | u32 | ? | |
| `+0x14` | s8 | **item_category / slot_type** ✅ Round 13 | IsEquipPossible 의 jumptable: 5=무기/0xa=특수, 4=방어구, 6/7/8/9=악세 |
| `+0x15` | u8 | flag (refine count?) | CopyData copies separately |
| `+0x16` | u16 | refine_value 또는 enchant_level | CopyData ldrh/strh |
| `+0x18..0x28` | 16B | **stat block 1** (4×4B reg via ldm/stm) | inheritance copy block |
| `+0x28..0x30` | 8B | stat block 2 | |
| `+0x30` | u32 | pointer or large value | |
| `+0x34..0x134` | 256B | **sub-records / large data block** | memcpy via bl 0x3130c |
| `+0x138..0x140` | 8B | stat ldrd pair | |
| `+0x140..0x148` | 8B | stat ldrd pair | |
| `+0x148..0x150` | 8B | stat ldrd pair | |
| `+0x150` | u16 | ? | |
| `+0x152` | u16 | ? | |
| `+0x154` | u8 | flag | |
| `+0x155` | s8 | **class_restriction** ✅ Round 13 | IsEquipPossible: `ldrb r0, [r0, #0x155]` 와 HERO+0x22c (class_id) 비교 |
| `+0x156..0x15a` | u16 ×3 | stats | |
| `+0x15c` | u8 | flag | |
| `+0x15d` | s8 | **level_limit** ✅ Round 13 | GetLevelLimit: `ldrb r4, [r0, #0x15d]` - GetRelieveLevelLimit() |
| `+0x15e` | s8 | flag | |
| `+0x15f` | s8 | extra | |
| `+0x160` | s8 | flag | |
| `+0x161` | s8 | flag | |
| `+0x162` | u16 | ? | |
| `+0x165` | u8 | flag | |
| `+0x166` | u8 | flag | |
| `+0x168` | u8 | **socket slot 0** (filled flag) ✅ Round 13 | EquipItem init: `dst[0x168]=0; memset(dst+0x169, 0xff, 5)` |
| `+0x169..+0x16d` | u8 ×5 | **socket slots 1..5** (orb/refine ID) | 0xff=빈슬롯, otherwise orb_idx |
| `+0x16e` | u16 | refine bonus | CopyData `mov r3, #0x16c; add r3, r3, #2; ldrh` |
| `+0x170` | u16 | refine bonus | |

**핵심 RE 단서**:
- HERO 의 `+0x22c` byte = 현재 class_id (1..5).
- IsEquipPossible 가 `r1` 인수로 받는 slot type (0..7) 별 jumptable:
  - slot 1 (armor): item.0x14 ≤ 4 → item.0x155 == HERO.0x22c
  - slot 2 (weapon special): item.0x14 == 5
  - slot 3 (헬멧): item.0x14 == 6
  - slot 4 (장갑): item.0x14 == 7
  - slot 5 (신발): item.0x14 == 8
  - slot 6 (액세서리): item.0x14 == 9 + item.0x14 ≤ 4 검증
  - slot 0/7: 일반/특수 (item.0x14 == 5/0xa)

## ItemBase (Formula::calc 의 5번째 인수, V[168..182] 의 base struct — 별도 클래스)

`tools/h5_extract_formula_vars.py` 산출 `formula_var_dict.tsv` 의 'item' 라벨 영역:

| offset | 크기 | var_id | 사용 패턴 |
|---:|---:|---:|---|
| `+0x0e` | s16 | V[168] | `V[168]*(100-V[123])/100` → **base SP cost** ✅ Round 13 |
| `+0x12` | s16 | V[169] | (formula 직접 사용 미발견) |
| `+0x16` | s16 | V[170] | `V[170]*(100-V[125])/100` → **base cooldown** ✅ Round 13 |
| `+0x1a` | s16 | V[171] | (formula 직접 사용 미발견) |
| `+0x20` | s16 | V[172] | (formula 직접 사용 미발견) |
| `+0x24` | s16 | V[173] | bounds [0, 3] — `V[173]+V[175..177]` 합산 (4단계 stat) |
| `+0x44` | s8 | V[174] | `V[56]+(V[57]*V[174])` 데미지 multiplier — **무기 강화 단계 / atk power tier** ✅ Round 13 |
| `+0x45` | s8 | V[175] | `(50+V[47])-V[240]+5*V[175]` — accuracy 보정 |
| `+0x46` | s8 | V[176] | `V[247]*(V[57]*V[176])/100` — 추가 damage 보정 |
| `+0x47` | s8 | V[177] | `5*V[177]` — minor stat 보정 |
| `+0x48` | s16 | V[178] | `(V[178]-300)/700` — large value 보정 (skill rank?) |
| `+0x4a` | s16 | V[179] | (직접 사용 미발견) |
| `+0x4c` | s16 | V[180] | (직접 사용 미발견) |
| `+0x4e` | s8 | V[181] | `V[42]*.../V[181]` divisor — **속도/weight unit** ✅ Round 13 |
| `+0x50` | s16 | V[182] | (직접 사용 미발견) |

ItemBase 는 EquipItemInfo / OrbItemInfo / SkillBookItemInfo 등의 base class 일 가능성.
이 struct field 는 **무기/스킬 base stat** 영역 — Formula::calc 가 직접 fetch.

`+0x168..0x16d` 는 EquipItemInfo 의 socket 영역 ↔ `+0x44..0x4e` 는 ItemBase 의 stat
영역 — 별도 struct 임을 주의.

---

## CSV → EquipItemInfo struct 매핑 (Round 14 — 2026-05-10)

`ItemTable::LoadItemTable` (4320B) @0xa38e0 의 EquipItem 처리 영역
(0xa3cf0 ~ 0xa4060) 디스어셈블로 csv record layout 추출:

| csv offset | size | 의미 | struct dst |
|---:|---:|---|---|
| 0..1 | u16 | record count (loop init) | — (count) |
| 2..3 | u16 | (read but discarded — function arg 우선) | struct +0x14 ← function arg (category) |
| 2 | (zero init) | — | struct +0x15 = 0 |
| 4..5 | u16 | refine_value 또는 enchant_level | struct +0x16 |
| 4 | (zero init 0x18..0x2c) | — | struct +0x18..+0x2c, +0x2c = 0 |
| 6 | u8 | name_len (`nl`) | — |
| 7..6+nl | bytes | name string (UTF-8/euc-kr) | struct +0x18 (memcpy `nl` bytes) |
| 7+nl..10+nl | u32 | item_id 또는 large flag | struct +0x30 |
| 11+nl | u8 | sub_record_len (`sblen`) | — |
| 11+nl..11+nl+sblen | bytes | sub-record (256B padded) | struct +0x34..+0x134 (memcpy 256B) |
| `sblen+11+nl` (= sb 시작) | u16 | u16 | struct +0x150 |
| sb+2 | u16 | u16 | struct +0x152 |
| sb+4 | u8 | flag | struct +0x154 |
| sb+5 | u8 | **class_restriction** | struct +0x155 (✅ Round 13 확정) |
| sb+6 | u16 | u16 | struct +0x156 |
| sb+8 | u16 | u16 | struct +0x158 |
| sb+0xa | u16 | u16 | struct +0x15a |
| sb+0xc | u8 | flag | struct +0x15c |
| sb+0xd | u8 | **level_limit** | struct +0x15d (✅ Round 13 확정) |
| sb+0xe | u8 | flag | struct +0x15e |
| sb+0xf | u8 | flag triplet[0] | struct +0x15f |
| sb+0x10..0x12 | u8 ×3 | (3-byte loop) | struct +0x160 / +0x162..+0x164 |
| sb+0x13... | (more reads) | + Formula::calc(0x7f3) 호출 | base stat 계산 결과 |

**자동 추출 도구**: `tools/h5_extract_loaditem_layout.py` — register tracking
한계로 일부만 추출 (수동 disasm 분석이 보완). 다음 라운드 — 자동 추출
정확화 (sb/r9 register propagation 강화).

**핵심 단서**:
- csv extra (실제 file 의 record body) 는 u8/u16 mixed layout — 이전 items.json
  의 stats_u16 는 단순 u16 array 로 dump 라 정확한 stat 의미 부여가 어려움
  (u8 byte 들이 u16 의 일부로 잘못 합쳐질 수 있음).
- LoadItemTable 안에서 `Formula::calc(formula_id=0x7f3=2035, ...)` 호출 — load
  시점에 base stat 가 자동 계산되어 cache.

## decode_h5_item.py 의 parse_equip_extra (Round 15 — 2026-05-10)

EquipItem (cat 1-11) 의 extra body 가변 parse:
- extra +0..+3: u32 → struct +0x30 (`item_id` 또는 large flag)
- extra +4: u8 sub_record_len (`sblen`)
- extra +5..(4+sblen): sub-record bytes (struct +0x34..+0x134 destination)
- extra +(5+sblen)..: sb 영역 — 위 표 참조

items.json 에 새 named fields 부여 (cat 1-11 only):
- `item_id`: u32 (struct +0x30)
- `sub_record_hex`: hex string (sub-record byte sequence)
- `class_restriction`: u8 (struct +0x155)
- `level_limit`: u8 (struct +0x15d)
- `val_150`, `val_152`, `val_154`, `val_156`, `val_158`, `val_15a`,
  `val_15c`, `val_15e`, `val_15f`, `val_160`: u8/u16 raw stat slots
- `triplet_162`: 3-byte triplet (struct +0x162..+0x164)

## Round 16 (2026-05-10) 정정 — `+0x155` 는 subtype, 진짜 class mask 는 `val_15f`

이전 라운드 (Round 13/15) 의 `class_restriction = struct +0x155` 매핑은 **오류**.
IsEquipPossible / IsEquipPossibleSpirit cross-check 결과:

`+0x155` = **item subtype code** (slot_0..3 무기 4종류 = 0/1/2/3, slot_4 = 4,
slot_5..8 = 5/6/7 helmet/boots/accessory, slot_9 shield = 3, slot_10 spirit = 5/7).
`IsEquipPossibleSpirit` 가 `0x155 == 7` 만 spirit 으로 허용. 즉 single-byte category code.

**진짜 class restriction** = `val_15f` (struct +0x15f) 의 lower 5 bit:
- bit 0 (1)  = W (워리어)
- bit 1 (2)  = R (로그)
- bit 2 (4)  = G (건슬링어)
- bit 3 (8)  = K (나이트)
- bit 4 (16) = S (소서러)

검증 (items.json 의 val_15f 분포):
- val=31 (`0b11111`) WRGKS (모든 클래스) → 385 records (가장 많음)
- val=0 → 43 records (특수 — class restrict 없음 또는 다른 의미)
- val=9 (WK) → 31 records (방패형)
- val=17 (WS) → 40 records
- val=15 (WRGK) → 32 records (소서러 제외)

검증 결과 (items.json):
| slot | item | subtype | class_mask | class_label | lv |
|---|---|---:|---:|---|---:|
| slot_0 (검류) | 롱소드 | 0 | 31 | WRGKS | 1 |
| slot_5 (헬멧) | 서클릿 | 5 | 31 | WRGKS | 1 |
| slot_9 (방패) | 버클러 | 3 | 31 | WRGKS | 1 |
| slot_10 (스피릿) | 고렘의인장 | 5 | 18 | RS | 1 |
| slot_10 | 데몬의뿔 | 5 | 1 | W | 1 |
| slot_10 | 팬텀의부적 | 5 | 17 | WS | 1 |
| slot_10 | 기사의징표 | 5 | 14 | RGK | 1 |

Spirit (slot_10) 의 class_mask 분포가 다양 (W/RS/WS/RGK) → class restriction 가
정확히 `val_15f & 0x1f` 임이 확정.

`val_15f` 의 upper 3 bit (값 32, 64, 128) — 추가 의미 (career/tier/cash) 가능성,
다음 라운드 분석.

decode_h5_item.py 의 출력 fields:
- `subtype` (이전 `class_restriction` 잘못, 정정됨)
- `class_mask` (val_15f & 0x1f)
- `class_label` (W/R/G/K/S 조합 또는 "-")

## Round 17 (2026-05-10) — refine field 매핑 + val_15f upper bits 분석

### RefineItem::ApplyItemRefine (956B) disasm 결과

강화 결과 (r7 jumptable, 0xa2b60):
- r7=0 (0xa2c98): 강화 +1 success — `+0x165 += 1`, `+0x166 += 2`
- r7=1 (0xa2c6c): 강화 +1 success — `+0x165 += 1`, `+0x166 += 1`
- r7=2 (0xa2a14): 다른 path
- r7=3 (0xa2c58): refine lock 적용 — `+0x167 = 1`
- r7=4 (0xa2bd0): 강화 실패 — `ClearEquipItem` (아이템 destroy)

| offset | 의미 | 변경 함수 |
|---:|---|---|
| `+0x165` | refine_count (강화 횟수, u8) | ApplyItemRefine 성공 시 +1 |
| `+0x166` | refine_sub_count (보조 강화, u8) | 성공 시 +1 또는 +2 |
| `+0x167` | refine_locked (1=영구 잠금) | r7=3 case |

CopyData 가 위 3 byte 모두 복사 (0x000a8884..8890) — runtime 변경 후 saved
across copies.

### val_15f upper 3 bit (>>5) 분포

items.json EquipItem 통계:

| upper | bit pattern | count | 추정 의미 |
|---:|---|---:|---|
| 0 | `0b000` | 170 | 중급/희귀 |
| 1 | `0b001` (bit5=32) | 248 | 강화 무기/방어구 (스톰브링거/캘라보그 등) |
| 3 | `0b011` (bit5+6=96) | 9 | 헤어핀/서클릿 보석 (slot_5 only) |
| 7 | `0b111` (all=224) | 362 | common 기본 아이템 (롱소드/브로드액스/서클릿 등) |

Sample analysis:
- upper=7: 롱소드/나이트롱소드/브로드액스 — 일반 시작 무기 (cls_mask=31 다수)
- upper=1: 스톰브링거/캘라보그/지옥수호도끼 — 보스/희귀 무기
- upper=0: 실가라스/투란기어/바리사다 — 중급 무기
- upper=3: 청금석헤어핀/석류석서클릿 — 보석 액세서리

가설:
- bit5 (32) = ?
- bit6 (64) = "gem" 또는 "사회술 액세서리"
- bit7 (128) = "common/default" flag

정확 의미 식별을 위해 ItemTable::SetItemOption (240B) 또는 DropTable 분석 필요
(다음 라운드).

### Round 18 (2026-05-10) — SetItemOption + 모든 카테고리 common base 부여

#### ItemTable::SetItemOption (240B, @0xa0ff8) 분석

- 인수: r0=this(ItemTable), r1=item_ptr (sb), r2=offset (sl)
- random `option_table[i]` 을 픽 해서 item 의 +0x15f, +0x162 영역에 store:
  - `+0x15f` (offset+0x15f) = option_type (option_table[i].byte 0)
  - `+0x162` (offset+0x162) = option_value (level_limit * option_param * randint(0x50,0x78) / 32)

`+0x15f` 가 random option_type byte 임을 확인. 즉 csv 의 `val_15f` 가 init
default 이지만 SetItemOption 가 호출되면 random change 될 수 있음. items.json
에 보이는 `class_label` 통계는 csv default 값 — runtime 변경 가능성 있음.

#### LoadItemTable cat 12+ jumptable 모두 analyzed (Round 18)

cat 12 (BattleUseItem, 0xa4060): record_size=0x138 (312B). 같은 base layout
(csv +2 read+discarded, +4 strh +0x16, +6 strlen, name → +0x18, u32 → +0x30,
sub_record_len + memcpy → +0x34..+0x134) + 4 byte (struct +0x134..+0x137).

cat 13 (OrbItem, 0xa423c): 같은 base. 추가 fields 미상.
cat 14, 16 (MixItem/MixBookItem): 같은 base.
cat 17, 18 (SkillBookItem/CashItem): 같은 base + 추가 5+ byte.

→ 모든 카테고리가 **공통 base layout** (item_id u32 + sub_record bytes) 을
공유. EquipItem (cat 1-11) 만 sb-area (struct +0x150..+0x167) 추가.

`decode_h5_item.py` 에 `parse_common_extra` 함수 추가 — 모든 cat 에 적용:
- `item_id` (u32 from extra+0)
- `sub_record_len` (u8)
- `sub_record_hex` (variable length bytes)

검증: 모든 19 slot 의 첫 record 모두 item_id + sub_record 부여 확인 (롱소드,
포션, 살코기, 양손베기LV1, 창고확장 등).

## Round 19 (2026-05-10) — 카테고리별 추가 fields 정확 매핑

### LoadItemTable 의 jumptable case 별 추가 fields

| cat | record_size | 함수 위치 | 추가 fields (struct) |
|---:|---:|---|---|
| 1-11 | 0x178 (376B) | 0xa3cf0 (EquipItem) | sb 영역 +0x150..+0x167 (24+ byte) |
| 12 | 0x138 (312B) | 0xa4060 (BattleUseItem) | +0x134/0x135/0x136/0x137 (4 byte) |
| 13 | 0x138 (312B) | 0xa423c (OrbItem) | +0x134/0x135 (2 byte, csv 에 실제 없음) |
| 14, 15 | 0x134 (308B) | 0xa43f4 (MixItem) | 추가 fields 없음 (base layout 만) |
| 16 | 0x144 (324B) | 0xa4578 (MixBookItem) | +0x134, sub-loop +0x135..+0x140 (12+ byte, csv 에 실제 없음) |
| 16, 17 | 0x138 (312B) | 0xa47c0 (SkillBook, case 16/17 공유 — Round 21: slot_16 도 SkillBook 임이 확인) | +0x134=class_id, +0x135=skill_index, +0x136=skill_level, +0x137=required_level (Round 20/21) |
| 18 | 0x138 (312B) | 0xa3b38 (CashItem, hardcoded 0x12) | +0x134/0x135 (2 byte) — Round 20 |

### items.json 에서 sb 영역 (rem = extra_len - sb_start) 분포

```
slot_0..10  (equip)        rem=21  sb 영역 가능 (Round 15 매핑)
slot_11     (battle_use)   rem= 4  +0x134..+0x137 4 byte 모두 csv 에 있음 ✓
slot_12     (battle_use)   rem= 2  빈소켓류 (불완전)
slot_13     (orb)          rem= 0  csv 에 추가 fields 없음
slot_14     (mix)          rem= 0
slot_15     (mix)          rem=13  특수 layout
slot_16     (mix_book)     rem= 4  추가 4 byte (disasm 가설은 12+ byte 였으나 csv 에 없음)
slot_17     (skill_book)   rem= 4  +0x134..+0x137 4 byte 모두 csv 에 있음 ✓ (Round 20)
slot_18     (cash_item)    rem= 2  +0x134/0x135 2 byte 모두 csv 에 있음 ✓ (Round 20)
```

**LoadItemTable disasm 가 read 하는 추가 byte 들 중 일부는 csv 에 없을 수 있음** —
실제 게임이 그 위치에서 garbage 값 또는 다음 record 의 첫 byte 를 read.
또는 record_size (csv prefix) 가 모든 byte 를 cover 하지 않음.

slot_11 (포션) 만 disasm 매핑이 csv 에 정확 일치 → BattleUseItem 의 추가 4 byte
가 검증된 매핑.

### decode_h5_item.py 새 카테고리별 parsers

- `parse_battle_use_extra` (slot_11, Round 23 정정): effect_type / success_rate / effect_value / duration (4 byte, 의미 식별 완료)
- `parse_orb_extra` (slot_12, Round 23 정정 — 이전 'scroll' 잘못): val_134/135 (2 byte)
- `parse_mix_book_extra` (slot_15, Round 23 정정 — 이전 slot_16): sb_extra_hex (raw 13 byte recipe)
- `parse_skill_book_extra` (slot_16, slot_17, Round 20/21): class_id / skill_index / skill_level / required_level (4 byte)
- `parse_cash_extra` (slot_18, Round 20): val_134/val_135 (2 byte)
- slot_13/14 (mix material, 0 ext) 만 추가 fields 없음

## Round 24 (2026-05-10) — val_15f upper 3 bit (tier flags) 의미 식별

### 핵심 발견: csv-time vs runtime val_15f 의 용도 차이

`val_15f` 는 **csv 로드 시점** 과 **runtime** 에 다른 의미:

| 시점 | 값 | 의미 |
|---|---|---|
| **csv load** (LoadItemTable) | bits 0..4 = class_mask (W/R/G/K/S, Round 16) + bits 5..7 = tier_flags (Round 24) | item 설정 metadata |
| **runtime** (SetItemOption 후) | option_type code (e.g. 0x6c='l' = level relieve) | 옵션 타입 — option_table 인덱스 |

`SetItemOption(item, opt_idx)` (0xa0ff8) 가 호출되면 +0x15f 가 random option_type 으로
**완전 덮어씀** (`strb r2, [sl, #0x15f]`). 이후 `EquipItemInfo::GetRelieveLevelLimit`
(0xa835c) 등이 `cmp #0x6c` 같이 option_type code 와 비교.

`MakeItemOption` (0xa10e8) 이 +0x15c (option_grade) 검사로 SetItemOption 호출 여부 결정:
- val_15c == 0: SetItemOption 미호출 → csv val_15f 유지
- val_15c >= 1: SetItemOption 호출 → val_15f overwrite

### val_15f upper 3 bit (tier_flags) 의 실증 패턴

EquipItem (slot_0..10) 789 records 의 분포:

| tier_flags | upper 값 | 비트 | 분포 | record 종류 |
|---:|---:|---|---:|---|
| 0 | 0 | -- | 170 | **legendary** — 보스/named 무기 (실가라스/투란기어/디바인세이버 등) |
| 1 | 32 | bit5 | 248 | **rare** — 중급 무기/방어구 |
| 3 | 96 | bit5+bit6 | 9 | **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔 등 9종 only) |
| 7 | 224 | bit5+bit6+bit7 | 362 | **common** — 일반 상점/기본 아이템 (롱소드/단검 등) |

가설:
- **bit 5 (32) = "obtainable"** flag — legendary 외 일반 입수 경로 표시
- **bit 6 (64) = "gem-accessory"** flag — slot_5 의 보석류 액세서리 전용 (9 records)
- **bit 7 (128) = "common-tier"** flag — 상점에서 살 수 있는 낮은 등급

slot_4 (armor) 가 1 record 만 ("스태프", tier=legendary, cls=-) — Sorcerer 전용
(class_mask=0 = 어떤 4 implemented class 도 사용 불가) — Round 22 의 미구현 stub
사실과 cross-confirm.

### decode_h5_item.py 새 fields (Round 24)

`parse_equip_extra` 가 추가 fields 부여:
- `tier_flags` (val_15f >> 5): 0/1/3/7 정수
- `tier_label`: legendary / rare / gem / common 라벨 string

## Round 23 (2026-05-10) — HERO::BattleUseItem 분석 + SLOT_META 전면 정정

### slot_11 (BattleUseItem) 4 byte fields 의미 (HERO::BattleUseItem 0x8fd20 분석)

`HERO::BattleUseItem(item_idx)` 의 핵심 흐름:
1. cooldown 체크 (GetPotionCoolTime — 0이면 사용 가능)
2. BagItem::DeleteBagItemCategoryIndex(11, item_idx, 1) — 인벤토리 차감
3. GetItemTableInfo(sp, 11, item_idx) — 스택의 ItemInfo 채우기
4. random(0,99) < struct[+0x135] 면 효과 적용 (성공 확률)
5. **HERO[0x2fe] = struct[+0x134]** (u8, effect_type)
6. **HERO[0x300] = struct[+0x136]** (u16, effect_value)
7. **HERO[0x302] = struct[+0x137]** (s16, duration)
8. SetPotionCoolTime(100) — 100 frame cooldown
9. CommonUi::NewCommonEffectOnce(1c) — visual effect

이후 `HERO::CalcStatusComputation` 가 HERO[0x2fe] (effect_type) 를 분기:
- `effect_type == 0x57 (87)`: HERO[0x19c] = 100 (보호 buff cap 설정)
- 기타 effect_type 값별로 다른 stat 적용 (HP/SP heal/buff)

#### slot_11 records 의 effect_type 분포 (검증)

| effect_type | 의미 | 예시 records | effect_value | duration |
|---:|---|---|---:|---:|
| **91** (0x5b) | HP heal | 포션 / 미들포션 / 하이포션 / 훈련용물약 / 포션(ex) | 1, 4, 10, 20 | 50 |
| **90** (0x5a) | SP heal | 퀵포션 / 미들퀵포션 / 하이퀵포션 / 집게발구이 / 엘릭서 | 40, 50, 100, 160, 250 | 1 |
| **87** (0x57) | buff (보호) | 보호의 부적 | 1 | 120 (turns) |
| **92** (0x5c) | special | 마석 | 1 | 1 |
| **19** (0x13) | test | 포션9 | 1 | 1 |
| **0** | 무효 | 제련석 (BattleUse 외 용도) | - | - |

success_rate 는 모든 records 에서 100 (100% 성공).

### SLOT_META 전면 정정 (Round 23)

기존 SLOT_META 가 record 이름 vs ext_after_sb 길이 cross-check 시 다수 mismatch
확인 — Round 11~22 에서 발견된 patterns 의 합산:

| slot | 기존 meta | 정정 후 (Round 23) | 근거 |
|---:|---|---|---|
| 11 | battle_use potion | battle_use potion ✓ | 4 byte ext, 포션 names |
| 12 | battle_use scroll | **orb** | 2 byte ext, 뇌제의오브/금강의오브 names |
| 13 | orb | **mix material** | 0 ext, 살코기/재료2..9 names |
| 14 | mix material | mix material_2 | 0 ext, 전갈갑피/은빛귀걸이 names |
| 15 | mix material_2 | **mix_book recipe** | 13 byte ext, 황혼수프/포션 (recipe) |
| 16 | mix_book | skill_book_wr (R21) | 4 byte ext, 양손베기 (Warrior) |
| 17 | skill_book | skill_book_gk (R21) | 4 byte ext, 연속사격 (Gunslinger) |
| 18 | skill_book | cash (R20) | 2 byte ext, 창고확장 등 |

## Round 20 (2026-05-10) — slot_17/slot_18 layout 정확 식별

### slot_16 / slot_17 (SkillBookItem) — 4 byte ext @ 0xa47c0

LoadItemTable jumptable case 16, 17 모두 0xa47c0 으로 분기 (동일 코드 path).
struct +0x14 = sp[0x10] = caller-supplied category arg (16 또는 17).

| offset | 의미 | 검증 (Round 21 — HERO::IfLearnSkill 분석) |
|---:|---|---|
| `+0x134` | u8 **class_id** | HERO 클래스 인덱스 0..4 (slot_16: 0/1, slot_17: 2/3) |
| `+0x135` | u8 **skill_index** | HERO::skills[skill_index] — 클래스별 0..9 (각 10 skills) |
| `+0x136` | u8 **skill_level** | "양손베기LV1..3", "연속사격LV1..7" 등 — 이름 LV 와 정확 매칭 ✓ |
| `+0x137` | u8 **required_level** | LV1..N 으로 가면서 monotonic 증가 (HERO+0x22d 와 cmp) |

#### HERO::IfLearnSkill (0x95d08, 316B) 의 class → category 공식

```
category = (class_id / 2) + 16   ; signed div, round-toward-zero
```

| class_id | class | → ItemTable category | items.json slot |
|---:|---|---:|---|
| 0 | Warrior (워리어) | 16 | slot_16 |
| 1 | Rogue (로그) | 16 | slot_16 |
| 2 | Gunslinger (건슬링어) | 17 | slot_17 |
| 3 | Knight (나이트) | 17 | slot_17 |
| 4 | Sorcerer (소서러) | 18 | slot_18 (CashItem!) |

**Sorcerer (class_id=4) 는 미구현 stub** (Round 22 확정):
- `c/csv/skill_04.dat` 파일 **부재** (skill_00..03 + skill_05 만 존재; skill_05 는
  몬스터/보스 스킬 — 암흑탄/지옥소환/얼음폭풍/완전면역 등 16개)
- .so 바이너리에 **SORCERER class object 없음** (WARRIOR/ROGUE/GUNNER/KNIGHT 만)
- `class_stats.json` 의 소서러 entry: STR/DEX/CON/INT 는 정의됐으나
  **unk1..unk14 모두 placeholder 값 1** (다른 클래스는 6/12/18/24 등 secondary stat
  growth 계수). unk0=320 (다른 1000)
- IfLearnSkill 의 `(class/2)+16=18` 매핑은 placeholder — 실제로 호출되어도
  slot_18 (CashItem) records 에 class_id=4 없음 → 학습 불가
- `skills_for_class(4)` (game_data.gd) 가 빈 배열 반환 → 게임 동작 시 무스킬

class_select.gd UI 에 "소서러 (미구현)" 라벨 표시 (Round 22).

#### 검증 통계 (Round 21)

| slot | records | class_id | skill_index 범위 |
|---:|---:|---|---|
| slot_16 | 95 | 0 (Warrior, 48) + 1 (Rogue, 47) | 0..9 (10 skills/class) |
| slot_17 | 98 | 2 (Gunslinger, 49) + 3 (Knight, 49) | 0..9 (10 skills/class) |

slot_16 Warrior 첫 5 skills: 양손베기 (3 lv) / 돌진 (4 lv) / 내려찍기 (7 lv) /
어깨치기 (4 lv) / 올려베기 (6 lv).
slot_17 Gunslinger 첫 5 skills: 연속사격 (4 lv) / 동시사격 (4 lv) / 샷건 (5 lv) /
화염방사 (7 lv) / 충격포 (5 lv).

### slot_18 (CashItem) — 2 byte ext @ 0xa3b38

LoadItemTable jumptable case 18 → 0xa3b38 (단독 코드 path, hardcoded type 0x12=18 at +0x14).
SkillBookItem 와 다른 layout — 2 byte 만 sb 영역.

| offset | 의미 | 관찰 |
|---:|---|---|
| `+0x134` | u8 cash_category | val ∈ {0, 1, 2, 3} — UI/orb/refine/utility 추정 |
| `+0x135` | u8 stack 또는 type | val ∈ {0..5, 255} — 255 = "no limit" 또는 "passive" 추정 |

검증 records: 창고확장(nt), 프리미엄판매, 작은오브원석, 고급제련석, 달성의부적, 소켓확장 등 49 records.

---

## 카테고리 dispatch (GetItemTableInfo 분석 결과, 2026-05-09)

`ItemTable::GetItemTableInfo(ItemInfo* dst, char category, char idx)` 가
**19 카테고리 switch** 로 record_size 별 sub-table 에서 fetch + Copy:

| category | record size | 구조 | 호출되는 CopyData |
|---:|---:|---|---|
| 0 | (return) | null/invalid | — |
| **1-11** | 0x178 (376B) | **EquipItemInfo** | `EquipItemInfo::CopyData` |
| 12 | 0x138 (312B) | BattleUseItemInfo | `BattlelUseItemInfo::CopyData` (sic) |
| 13 | 0x138 | OrbItemInfo | `OrbItemInfo::CopyData` |
| 14 | 0x134 (308B) | MixItemInfo | `MixItemInfo::CopyData` |
| 15 | 0x134 | MixItemInfo (변종) | 동일 |
| 16 | 0x144 (324B) | MixBookItemInfo | `MixBookItemInfo::CopyData` |
| 17, 18 | 0x138 | SkillBookItemInfo | `SkillBookItemInfo::CopyData` |
| 19 | 0x138 | CashItemInfo | `CashItemInfo::CopyData` |

**카테고리 1-11 (장비) 의 sub-table 위치**: `ItemTable[r0, +0xa+(category)*4]` —
ItemTable 객체 안 0x28-0x54 영역에 11개 sub-table 포인터가 배열로 있음.

**카테고리 12+의 sub-table 위치**: `[r0, +0x54], +0x58, +0x5c, +0x60, +0x64, +0x70`
(고정 offset 으로 직접 dispatch).

**EquipItem 만 socket 초기화**: `dst[0x168] = 0; memset(dst+0x169, 0xff, 5)` —
6 슬롯 중 1번째는 0, 나머지 5는 0xff (빈 슬롯). 이는 ITEM_STRUCT 의 +0x154-+0x168
관찰과 일치.

## 현재 Godot 디코더 (`decode_h5_item.py`) 와의 차이

현재 출력 `items.json`:
```json
"slot_0": [{ "idx": 0, "name": "롱소드", "stats_u16": [200, 0, 48647, ...] }]
```

- `slot_N` 의 N 이 **category** 와 일치 (확인됨: slot_0 = 무기 = category 1).
- `stats_u16` 의 16 × 2B = 32B = 레코드의 앞 32 바이트.
- 376B EquipItem 레코드의 나머지 344B 는 `extra_hex` 에 hex 로 dump 됨 — **파싱 안 됨**.

후속 작업으로 `decode_h5_item.py` 를 EquipItemInfo CopyData offset 에 맞춰
정식 필드명 (atk/def/level_req/class_req/socket[5]) 으로 라벨링 가능.

## 다음 분석 가능

- `EquipItemInfo::IsEquipPossible(char class_id)` (272B) ─ 클래스 제한 체크.
  어떤 byte 가 "허용 클래스 비트마스크" 인지 확인 가능.
- `EquipItemSpirit::SetEquipItemSpirit(char, short)` (200B) ─ 스피릿 슬롯 처리.
- `RefineItem::ApplyItemRefine(...)` (956B) ─ 강화 시 어떤 필드가 증가하는지.

이 모두를 분석하면 `decode_h5_item.py` 의 stats_u16 dump 가 어떤 의미인지 정확히
매핑 가능 — 현재 임시 stat 라벨을 정식 이름으로 교체할 수 있다.

---

## 현재 Godot 측 격차

`apps/hero5-godot/assets/gamedata/items.json` ─ `tools/converter/decode_h5_item.py`
가 csv/c_item_*.dat 에서 이름 + stats_u16[] 만 dump. struct field 의 실제 의미
(어떤 인덱스가 ATK, DEF, level 요구치, 클래스 제한) 미정.

따라서 현재 game UI 에서:
- 아이템 이름·아이콘·가격: ✅ 정확.
- 무기 ATK / 방어구 DEF: ⚠ stats_u16 의 어느 슬롯인지는 추정 (대체로 stats[1] = 주 능력치).
- 레벨/클래스 제한: ❌ 미적용.

후속 disasm 으로 ItemInfo struct 가 완전히 매핑되면 이를 Godot 측 GameData
loader 에 반영 가능.
