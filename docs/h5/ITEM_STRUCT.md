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
