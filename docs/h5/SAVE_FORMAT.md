# Hero5 Save 파일 포맷

> Round 41 (2026-05-17) — 8개 save 파일 종류 식별 + dispatch + write event 자동 추출.
> Round 42 (2026-05-17) — load 함수 cross-check 로 layout **확정**.
> H_*.sav: **21/21 write↔read 매칭 (0 mismatch)**. SL_*.sav: 24 matched + 13 in-memory writes.

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

### 3.1 H_%d.sav (HERO::SaveHeroData, 736B 함수) — **확정**

Save 23 event + Load 33 event cross-check 결과 **21/21 offset 일치 (0 mismatch)** +
load 측에서 추가 발견된 timestamp 2 × u64.

| offset | size | 의미 (Save write ↔ Load read 양쪽 검증) |
|---:|---:|---|
| +0x0 | u32 | (Save) Int32ToByte / (Load) ByteToInt32 → HERO+0xf0 |
| +0x4 | u8 | HERO+0x22c (class_id, Round 13 의 IsEquipPossible 와 일치) |
| +0x5 | u8 | HERO+0x22d (level 또는 보조 class field) |
| +0x6 | u32 | EXP 또는 gold |
| +0xa..+0x19 | **8 × u16** | **stat block** (HP/MP/STR/DEX/CON/INT + 2 — Round 11 base stat 와 매핑 후보) |
| +0x45..+0x4b | **7 × u8** | **equipment slot** (EquipItem cat 0-6, Round 14 일치 추정) |
| +0x4c..+0x4f | u32 | 추가 stat |
| +0x60 | u8 | flag |
| **+0x1fc..+0x203** | **u64** | timestamp #1 (생성 시각 추정) |
| **+0x204..+0x20b** | **u64** | timestamp #2 (최근 저장 시각 추정) |

전체 사용 영역 = 약 0x20c bytes (524 B). 524 B 이외 영역은 0 padding 또는 안 씀.

Round 13 의 EquipItemInfo +0x14 = item_subtype/cat 과 +0x45..+0x4b 의 7 슬롯이 정확
대응 (weapon/shield/helmet/boots/accessory ×2/spirit).

### 3.2 SL_%d.sav (SlotInfo::SaveSlotData, 2076B 함수) — **확정 (대부분)**

Save 91 event + Load 73 event cross-check 결과 **24 offset 정밀 일치 (0 mismatch)** +
변수 offset memcpy 12-18 block (file content 영역). r4=SlotInfo struct (in-memory)
의 13 write 는 file 영역 아님. malloc(0x2d80 + 0x1f = 11679 B) buffer 가 실 파일.

**Header (+0x00..+0x15) — 확정**:

| offset | size | 의미 |
|---:|---:|---|
| +0x0..+0x1 | 2 bytes | class+level encode (Save: strb r4+0=HERO+0x22c, +1=HERO+0x22d) |
| +0x2..+0x5 | u32 | GetX (OBJECT::GetX 호출) |
| +0x6..+0x9 | u32 | GetY |
| +0xa..+0x11 | **u64** | playtime (MC_knlCurrentTime - HERO+0x1fd0 delta) — Load 측 ByteToInt64 검증 |
| +0x12..+0x15 | u32 | scene_idx (HERO_class+0xa0) |

**Body sub-blocks — Save 면만 확정 (Load 도 같은 offset 사용)**:

| offset 영역 | size | 의미 추정 |
|---:|---:|---|
| +0x16 | u8 | HERO_class+0x8b flag |
| +0x17 부터 | 3 × 256B | inventory / stat snapshot / buff (HERO_class+0x288/0x388/0x488) |
| +0x321..+0x324 | 4 bytes (strb pairs) | item slot marker |
| +0x425..+0x426 | 2 bytes | flag pair |
| **+0x433..+0x438** | **6 bytes** | sub-block 1 (cat-style 6 entries — 강화/orb socket 후보) |
| **+0x45d..+0x462** | **6 bytes** | sub-block 2 (sub-block 1 의 보조) |
| +0x487..+0x489 | 3 bytes | trailer markers |
| +0x494..+0x496 | 3 bytes | 추가 markers (in-memory only?) |

7개 in-memory writes (r4 base, +0x0/+0x16/+0x18/+0x1c 등) 는 file 영역이 아니라
SlotInfo struct 의 cached field — Save 후 다음 호출에서 사용. Load 측에서는 별도
함수에서 동일 정보 set 하므로 cross-check 에는 안 나옴.

### 3.3 M.sav (Mission::SaveData, 572B / Mission::LoadData 604B) — 부분 확인

Save 15 + Load 33 events. 대부분 변수 offset (105 mission iter loop) — register
propagation 추적기가 imm offset 인식 못함. 그러나 load 측 `+0x4` 위치에서 `ldrsh`
2회 (u16 read) 가 csv-style 헤더 패턴과 일치 — **u16 record_count 또는 count+size pair**.

| offset | 의미 추정 |
|---:|---|
| +0x4..+0x5 | u16 (Load 측 ldrsh 2회) — record_count 또는 first record size |
| +0xfb | u8 marker (cross-checked save +0xfb) |
| loop body | 105 missions × variable bytes (각 mission 의 type/sub/target/count 직렬화) |

Layout 정밀 매핑은 mission iter body disasm 으로 다음 라운드 가능 (LoadMissionTable
Round 38 의 구조와 유사 추정).

### 3.4 LOCAL/EX/ET/OP/B sav

각 함수 분석 미완 — 함수 크기 작음 (152~288B). 비슷한 도구로 추출 가능.

## 4. Cross-check 도구 (Round 42 신규)

`tools/h5_save_crosscheck.py` — save / load write↔read 매칭으로 layout 확정.

```bash
# HERO save vs load (기본):
python tools/h5_save_crosscheck.py

# 임의 함수 비교:
python tools/h5_save_crosscheck.py <save_sym> <load_sym> [save_bufs] [load_bufs]
```

출력: offset 별 save_size, load_size, match status (OK / MISS / S> / <L).

## 5. 다음 라운드 작업 (Round 43 후보)

1. **register propagation 정밀화** — `h5_extract_save_writes.py` 의 r1 (buf base)
   추적기를 propagate 시 memcpy 의 offset=? 가 imm 값으로 확정 → SlotInfo의 sub-block
   layout 정밀화.
2. **각 write 의 source struct field 식별** — r0 = HERO+offset / class_info+offset
   인지 trace 하여 의미 라벨 부여 (특히 SL_*.sav 의 +0x17 부터 3×256B 블록).
3. **Mission save iter body 분석** — 105 mission 의 직렬화 stride 확정 (Round 38 의
   MissionInfo 44B struct 와 매핑 추정).
4. **나머지 5 save 함수 (LOCAL/EX/ET/OP/B) 분석** — 작은 함수 (152-288B) 라 빠름.

## 6. 산출

- `tools/h5_extract_save_writes.py` (R41) — write/read event extractor (load 지원 추가 R42)
- `tools/h5_save_crosscheck.py` (R42) — write↔read offset 매칭 도구
- `work/h5/analysis/saveslotdata_disasm.txt`
- `work/h5/analysis/_ZN8SlotInfo12SaveSlotDataEa_writes.tsv` (91 events)
- `work/h5/analysis/_ZN4HERO12SaveHeroDataEa_writes.tsv` (23 events)
- `work/h5/analysis/_ZN7Mission8SaveDataEv_writes.tsv` (15 events)
- `work/h5/analysis/_ZN4HERO12LoadHeroDataEa_writes.tsv` (33 events, R42)
- `work/h5/analysis/_ZN8SlotInfo12LoadSlotDataEa_writes.tsv` (73 events, R42)
- `work/h5/analysis/_ZN7Mission8LoadDataEv_writes.tsv` (33 events, R42)
