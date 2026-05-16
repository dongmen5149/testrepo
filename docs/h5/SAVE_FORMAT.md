# Hero5 Save 파일 포맷

> Round 41 (2026-05-17) — 8개 save 파일 종류 식별 + dispatch 흐름 + write event 자동 추출.
> 상세 byte 매핑은 다음 라운드 (각 사용 함수의 source register propagation 추적 필요).

## 1. 핵심 발견

### 1.1 DES 는 save 에 적용되지 않음

`MX_desEncrypt` / `MX_desDecrypt` (DES variant, key `0EP@KO91`) 의 caller 를
.text 전체에서 스캔한 결과 **0건** — DES 는 save 가 아닌 다른 protected
resource (calc_*.dat 등) 에만 사용됨. Save 파일은 **plain bytes** 로
SD container 에 저장됨.

`_midas_funcSdMakeName` 도 단순 filename 길이 truncation (15 char) 만 수행 —
encryption 없음.

### 1.2 8 개 save 파일 종류 (.rodata 식별)

| 파일명 패턴 | 위치 (.rodata) | 작성 함수 | 용도 |
|---|---|---|---|
| `LOCAL.sav` | 0x157df0 | `CommonUi::SaveLocalSaveData` (192B) | 로컬 진척 메타 |
| `EX.sav` | 0x157f28 | `CommonUi::SaveExpertSaveData` (180B) | Expert (난이도?) 데이터 |
| `ET.sav` | 0x157f30 | `CommonUi::SaveEctSaveData` (152B) | 기타 (etc) 데이터 |
| `OP.sav` | 0x157f38 | `CommonUi::SaveGameOption` (152B) | 게임 옵션 |
| `M.sav` | 0x158208 | `Mission::SaveData` (572B) | Mission 진척 (105 missions) |
| `H_%d.sav` | 0x158278 | `HERO::SaveHeroData` (736B) | Hero stat 슬롯별 |
| `B_%d.sav` | 0x158288 | `HERO::SaveBagData` | 인벤토리 슬롯별 |
| `SL_%d.sav` | 0x158298 | `SlotInfo::SaveSlotData` (2076B) | 슬롯 메타 + class data |
| `DEBUG.sav` | 0x15aae0 | (debug only) | — |

### 1.3 SaveAll dispatch (0x8f924, 92B)

```
HERO::SaveAll(slot_idx)
├── SlotInfo::SaveSlotData(slot_idx)   ; SL_%d.sav (slot 메타 + class info)
├── HERO::SaveHeroData(slot_idx)        ; H_%d.sav (hero stat)
├── HERO::SaveBagData(slot_idx)         ; B_%d.sav (inventory)
└── Mission::SaveData() [tail call]     ; M.sav (mission progress)
```

LOCAL/EX/ET/OP 는 별도 흐름 (게임 옵션/메타) — slot 과 무관.

## 2. 자동 추출 도구

`tools/h5_extract_save_writes.py` — ARM disasm + register propagation 으로
buffer write event (`Int{8,16,32,64}ToByte`, `memcpy`, `strb/h/(w)`) 추출.

```bash
python tools/h5_extract_save_writes.py _ZN8SlotInfo12SaveSlotDataEa
# → work/h5/analysis/<symbol>_writes.tsv
```

산출 TSV 컬럼: `addr | kind | buf | offset | size | source`

## 3. 파일별 layout 개요 (Round 41 시점)

### 3.1 H_%d.sav (HERO::SaveHeroData, 736B 함수)

총 ~23 write event. base offset 영역별:

| offset | size | 추정 의미 |
|---:|---:|---|
| +0x0 | u32 | hero level 또는 main stat composite |
| +0x4 | u8 | flag |
| +0x5 | u8 | flag |
| +0x6 | u32 | EXP 또는 gold |
| +0xa..+0x19 | 8 × u16 | **8 stat block** (HP/MP/STR/DEX/CON/INT + 2) |
| +0x45..+0x4b | 7 × u8 | **7 equipment slot** (cat 0-6 추정 — Round 14 의 EquipItem categories 와 일치) |
| +0x4c..+0x4f | u32 | 추가 stat |
| +0x60 | u8 | flag |
| +? | 2 × u64 | timestamp pair (생성 + 최근 저장 추정) |

검증: 8 u16 (+0xa..+0x19) 가 Round 11 의 V[60..63]=base_str/dex/con/int + HP/MP/SP 와 매핑 가능성.

### 3.2 SL_%d.sav (SlotInfo::SaveSlotData, 2076B 함수)

총 ~91 write event. 가장 큰 save 파일. malloc(0x2d80 + 0x1f = 11679B) buffer 사용.

| offset 영역 | size | 추정 의미 |
|---:|---:|---|
| +0x0..+0x1 | 2 bytes | class_id (+0 = HERO+0x22c) + level encode |
| +0x2..+0x5 | u32 | GetX (position) |
| +0x6..+0x9 | u32 | GetY |
| +0xa..+0x11 | u64 | playtime (MC_knlCurrentTime - HERO+0x1fd0) |
| +0x12..+0x15 | u32 | scene_idx |
| +0x16 | u8 | HERO_class+0x8b |
| +0x17..+0x117 | 256 × 3 = 768B | 3 × 256B blocks (HERO_class+0x288/+0x388/+0x488 영역, 추정: inventory / stat snapshot / buff status) |
| +0x31c..+0x320 | 5 bytes | secondary block 1 |
| +0x32c..+0x330 | 5 bytes | secondary block 2 |
| +0x328..+0x32b | 4 bytes | 4 u8 markers (sl/lr/r3/sb) |
| +0x42c..+0x42d | 2 bytes | flag pair |
| +0x494..+0x496 | 3 bytes | 추가 markers |
| +0x4c..+0x489 | various | 6 × (memcpy 256B/200B/28B chunks for sub-sections) |

R5 (= malloc'd buffer base) 가 main file content 작성에 사용됨.

### 3.3 M.sav (Mission::SaveData, 572B 함수)

총 ~15 write event. 105 missions × variable 데이터.

- 다수의 `Int32ToByte` 호출 (u32 mission flag/count 직렬화)
- 정확한 layout 은 mission loop body 분석 (offset register 추적 필요) — 다음 라운드

### 3.4 LOCAL/EX/ET/OP/B sav

각 함수 분석 미완 — 함수 크기 작음 (152~288B). 비슷한 도구로 추출 가능.

## 4. 다음 라운드 작업 (Round 42 후보)

1. **load 함수 cross-check** — `HERO::LoadHeroData` (808B), `SlotInfo::LoadSlotData`
   (968B), `Mission::LoadData` (604B) 의 read pattern 추적으로 write/read 매칭
   검증. 같은 offset 에 같은 size 가 보이면 layout 확정.
2. **register propagation 정밀화** — `h5_extract_save_writes.py` 의 trk 가
   r2 (offset) 만 추적함. r1 (buf base) 도 propagate 시 offset=? 인 memcpy 값
   확정 가능.
3. **각 write 의 source struct field 식별** — r0 = HERO+offset / class_info+offset
   인지 trace 하여 의미 라벨 부여.

## 5. 산출

- `tools/h5_extract_save_writes.py` (write event extractor)
- `work/h5/analysis/saveslotdata_disasm.txt` (전체 disasm)
- `work/h5/analysis/_ZN8SlotInfo12SaveSlotDataEa_writes.tsv` (91 events)
- `work/h5/analysis/_ZN4HERO12SaveHeroDataEa_writes.tsv` (23 events)
- `work/h5/analysis/_ZN7Mission8SaveDataEv_writes.tsv` (15 events)
