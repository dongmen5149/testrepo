# Hero5 ItemInfo / EquipItemInfo 구조체 layout (부분)

원본: `tools/h5_disasm_item_funcs.py` → `work/h5/analysis/item_funcs.txt`

`EquipItemInfo::CopyData(EquipItemInfo*)` 의 ldr/str 오프셋 패턴에서 추출.
**부분만** — CopyData 가 모든 필드를 복사한다는 보장은 없음.

---

## EquipItemInfo (총 크기 ≥ 0x168 = 360B)

| offset | 크기 | 추정 의미 |
|---:|---:|---|
| `+0x02` | u8/u16 | 아이템 타입/카테고리 |
| `+0x04` | u32 | itemID 또는 32-bit field |
| `+0x08` | u32 | ? (probably stat) |
| `+0x0c` | u32 | ? |
| `+0x14..0x15` | u8×2 | flag pair |
| `+0x16` | u16 | ? |
| `+0x30` | u32 | pointer or large value |
| `+0x154..0x168` | bytes | **socket/option 블록** (인접 byte 다수 = 소켓 슬롯) |

`+0x154` 부터 0x168 까지 인접 1B 8개 = 소켓 정보 (orb/refine/option)
저장 영역 추정. 0x30 ~ 0x154 사이의 ~0x124 (292B) 는 추가 분석 필요.

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
