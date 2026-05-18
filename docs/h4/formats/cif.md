# `_H_NNN_CIF` 캐릭터 정보 파일 (Hero4)

117개 파일 (`H4/CIF/_H_000_CIF` ~ `_H_116_CIF`). 각 파일이 game entity 한 명/하나의 sprite/animation 정의.

## Hero3 와 동일한 헤더 schema (2026-05-18 후속6 검증)

```
struct CIFHeader {
    uint8 slot_count;          // sprite 슬롯 개수 (1..8)
    uint8 category;            // entity 분류 (0..28)
    uint8 sprite_indices[slot_count];  // 1..51 sprite slot pool 참조
}
// post-header: animation_data (가변 크기)
```

[tools/converter/parse_h4_cif.py](../../tools/converter/parse_h4_cif.py) 가 Hero3 `parse_cif()` 함수 재사용. **추가 변경 없이 117 파일 모두 정상 파싱**.

## 분포 (117 파일)

### slot_count 분포

| slots | n | 추정 |
|---|---|---|
| 1 | 51 | system/marker / single boss / dialog speaker |
| 6 | 33 | 표준 NPC / enemy (6-direction sprite) |
| 4 | 12 | minor NPC |
| 2 | 11 | small NPC |
| 8 | 4 | **hero (4 main characters)** |
| 3 | 4 | mid entity |
| 5 | 2 | rare special |

### category 분포 (29종)

`0` (27), `2` (23), `1` (15), `3` (11) 가 주류. `4..28` 은 소수 (각 1-3 file).

Hero3 의 0/1/2 (hero/enemy/boss) 만 비교하면 Hero4 는 **30+ category** 로 확장. quest item, weapon, armor, spell 등 세분화 추정.

### Entity classification (heuristic)

| class | 정의 | n | 예 |
|---|---|---|---|
| hero | slot=8, cat=0 | 4 | _H_001~004 |
| major_npc | slot=6, cat=0 | 10 | _H_018, _H_076 |
| enemy_or_npc | slot=6, cat=1~3 | 14 | _H_021 |
| minor_npc | slot=4, cat=0~3 | 12 | |
| small_npc | slot=2 | 11 | |
| mid_entity | slot=3 | 4 | |
| rare_5slot | slot=5 | 2 | |
| single_entity | slot=1, size≥100 | 46 | boss/quest item |
| system_or_marker | slot=1, size<100 | 5 | placeholder |

## animation_data stride 검증 — **Hero3 엔진 100% 호환** (★)

Hero3 의 두 stride 가설을 Hero4 에 적용:
- hero: 41-byte fixed stride per frame
- enemy/boss: 4-byte cell stream

**검증 결과 (117 파일)**:
- **113 / 117 enemy CIF가 4B stride 완벽 fit** (NPC/minor/small/mid/rare 등 hero 제외 전부)
- **4 / 4 hero CIF 가 41B stride fit** (_H_001 = perfect 41B+15B prologue, _H_002/003/004 = 31~40 byte 잔여 footer)

→ **Hero3 sprite/animation decoder 가 Hero4 CIF 에 추가 수정 없이 작동**.

이 발견의 Phase C 함의:
1. KMM commonMain 으로 Hero3 sprite renderer 이전 시 Hero4 자동 호환
2. 117 entity × (frame 데이터) = Hero4 전체 캐릭터 애니메이션 즉시 사용 가능 (DES key 무관, CIF 는 plaintext)
3. 메인 캐릭터 4명 = ~88-135 KB sprite data 각 = ~2000-3300 animation frames

## sprite slot pool (1..51)

CIF indices 범위 = 1..51 (50/51 슬롯 사용, slot 51 만 미사용).

Top 사용 슬롯 (refs across 117 CIFs):
| slot | refs |
|---|---|
| 1 | 43 |
| 6 | 41 |
| 3 | 34 |
| 5 | 31 |
| 2 | 28 |
| 4 | 24 |
| 7 | 18 |
| 11 | 16 |
| 8 | 14 |
| 12 | 11 |

**가설**: 51개 sprite slot pool 은 게임 runtime 의 표준 sprite 자원 풀 (game engine 내 lookup table). OBJ id (0..246) 와 직접 매핑 안 됨 — 별도 indirection layer. 정확한 51 slot → OBJ asset 매핑은 Phase B Ghidra 후.

## CIF ↔ EXD 페어링 (★)

**117 / 117 = 100% pairing**. 모든 `_H_NNN_CIF` 가 같은 NNN 의 `_H_NNN_EXD` 와 페어.

EXD subtype 별 분포 (CIF class 기준):
| CIF class | EXD subtype 1 | subtype 2 | subtype 3 |
|---|---|---|---|
| hero | 0 | 0 | 4 |
| major_npc | 0 | 1 | 9 |
| enemy_or_npc | 0 | 0 | 14 |
| minor_npc | 0 | 0 | 12 |
| small_npc | 0 | 0 | 11 |
| single_entity | 1 | 12 | 33 |
| system_or_marker | 4 | 1 | 0 |

- **subtype=3 (collision feet + sprite body box)**: 88 files — game-relevant entities (hero/NPC/enemy)
- **subtype=2 (single box)**: 14 files — static items / single-frame entities
- **subtype=1 (variable raw)**: 5 files — system markers

Hero CIFs detail:
| file | size | EXD count (frame poses) | indices |
|---|---|---|---|
| _H_001_CIF | 88,995B | 35 | [1, 2, 3, 5, 8, 12, 14, 42] |
| _H_002_CIF | 88,733B | 27 | [1, 2, 3, 6, 9, 12, 14, 43] |
| _H_003_CIF | 135,957B | 29 | [1, 2, 3, 5, 10, 12, 13, 34] |
| _H_004_CIF | 86,066B | 19 | [1, 2, 3, 7, 11, 12, 7, 31] |

공통 indices `[1, 2, 3, 12]` = 표준 hero pose 슬롯. 추가 4-5개 = 캐릭터별 고유 (특기/스킬).

## 파서 + 출력 + cross-reference

- [tools/converter/parse_h4_cif.py](../../tools/converter/parse_h4_cif.py) → `work/h4/converted/cif_parsed.json`
- `work/h4/converted/cif_exd_xref.json` (117 entity 페어 매트릭스)

## 미해결 (Phase B Ghidra)

- 51-slot sprite pool → OBJ asset (0..246) 매핑 lookup table 위치
- hero CIF 의 41-byte frame entry 내부 field 의미 (Hero3 분석 결과 활용 가능)
- enemy 4B cell stream 의 opcode 의미 (Hero3 `FUN_00098ef8` 디코더 활용 가능)
- category 0..28 의 각 의미 (weapon/armor/quest 등 세분화)
