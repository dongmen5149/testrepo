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

## 다음 분석 가능

- `ItemTable::GetItemTableInfo(ItemInfo*, char, char)` (288B) ─ 외부 데이터에서
  ItemInfo 채우는 함수. csv/dat 파일 → struct field 매핑 직접 노출.
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
