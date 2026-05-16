# Hero5 Save 파일 포맷

> Round 41 (2026-05-17) — 8개 save 파일 종류 식별 + dispatch + write event 자동 추출.
> Round 42 (2026-05-17) — load 함수 cross-check 로 layout **확정**.
> Round 43 (2026-05-17) — load 함수 disasm 으로 file offset → HERO struct offset 매핑 + **의미 라벨링**.
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

### 3.1 H_%d.sav (HERO::SaveHeroData, 736B 함수) — **확정 + struct field 매핑**

Save 23 event + Load 33 event cross-check 결과 **21/21 offset 일치 (0 mismatch)** +
load 측에서 추가 발견된 timestamp 2 × u64. **LoadHeroData disasm 으로 file →
HERO struct field 매핑 추가 (Round 43)**.

| file offset | size | HERO struct | 의미 |
|---:|---:|---|---|
| +0x0 | u32 | HERO+0xf0 | (용도 미상 — 큰 정수 stat composite) |
| +0x4 | u8 | HERO+0x22c | **class_id** (Round 13 IsEquipPossible 일치) |
| +0x5 | u8 | HERO+0x22d | level 또는 보조 class field |
| +0x6 | u32 | HERO+0x230 | EXP 또는 gold |
| +0xa | u16 | HERO+0x234 | **stat[0]** (HP base 추정) |
| +0xc | u16 | HERO+0x23e | stat[1] (10 byte 점프 — in-memory 만 있는 derived stat 5개 사이에) |
| +0xe | u16 | HERO+0x240 | stat[2] |
| +0x10 | u16 | HERO+0x242 | stat[3] |
| +0x12 | u16 | HERO+0x244 | stat[4] |
| +0x14 | u16 | HERO+0x246 | stat[5] |
| +0x16 | u16 | HERO+0x248 | stat[6] |
| +0x18 | u16 | HERO+0x24a | stat[7] |
| +0x1a..+0x44 | 43 × u8 | HERO+0x24c..+0x276 | **불연속 byte block** (skill list/buff state, Round 11 의 V[112..116] secondary stat cache 추정) |
| +0x45 | u8 | HERO+0x277 | **equip slot 0** (Save 시 SlotInfo+1 = level 인코딩 byte 와 동일 — slot 슬롯 vs level encoded 양면) |
| +0x46..+0x4b | 6 × u8 | HERO+0x1790..+0x1795 | **equip slot 1-6** (EquipItem cat 1-6, Round 14 일치) |
| +0x4c..+0x4f | u32 | HERO+0x1798 | quest/inventory composite |
| +0x50..+0x5f | 16 × u8 | HERO+0x17a6..+0x17b5 | sub-block (skill cooldown/buff 추정) |
| +0x60 | u8 | HERO+0x1b61 | obj_count (다음 loop 의 record count, signed) |
| +0x61..+(0x60+0x29*10) | 10 × 41B | HERO+0x1b62..+(0x1b62+0x19a) | **10 slot × 41B** records (스킬 entry?) |
| +0x1fc..+0x203 | u64 | HERO+0x310, HERO+0x318 (양쪽 write) | **timestamp #1** (save 생성 시각) |
| +0x204..+0x20b | u64 | HERO+0x328, HERO+0x330 (양쪽 write) | **timestamp #2** (save 갱신 시각) |

전체 사용 영역 = 약 **0x20c bytes (524 B)**. 524 B 이외 영역은 0 padding 또는 안 씀.

**핵심 발견** (Round 43):
- HERO+0x277 은 **equip slot 0** 또는 **level 의 인코딩 source** 두 가지 역할.
  SaveSlotData 가 `file[0] = HERO+0x277 * 10 + HERO+0x22c` 로 packing —
  즉 `class_id + 10 * level` (5 클래스 × max 25 level = 125 < 256 byte 안 들어감,
  따라서 max level 약 25 추정).
- 8 u16 stat block 의 HERO+0x234 → 0x23e 점프 (10 byte 간격) 은 in-memory derived
  stat 5개 (저장 안 됨) 가 그 사이에 위치 — 보조 stat 캐시.

### 3.2 SL_%d.sav (SlotInfo::SaveSlotData, 2076B 함수) — **확정 + 인코딩 패킹 규칙**

Save 91 event + Load 73 event cross-check 결과 **24 offset 정밀 일치 (0 mismatch)** +
변수 offset memcpy 12-18 block (file content 영역). r4=SlotInfo struct (in-memory)
의 13 write 는 file 영역 아님. malloc(0x2d80 + 0x1f = 11679 B) buffer 가 실 파일.

**Header (+0x00..+0x15) — 확정 + 매핑**:

| file offset | size | SlotInfo struct | HERO source | 의미 |
|---:|---:|---|---|---|
| +0x0 | u8 | SlotInfo[0]=class, SlotInfo[1]=level | HERO+0x22c, HERO+0x277 | **packed class+level**: `file[0] = HERO+0x277 * 10 + HERO+0x22c`. Load 가 `% 10` / `/ 10` 으로 분리. **max level ≈ 25** 추정 |
| +0x1 | u8 | SlotInfo+2 | HERO+0x22d | 보조 class field |
| +0x2..+0x5 | u32 | SlotInfo+4 | OBJECT::GetX() | **map X position** |
| +0x6..+0x9 | u32 | SlotInfo+8 | OBJECT::GetY() | **map Y position** |
| +0xa..+0x11 | u64 | SlotInfo+0x10 | MC_knlCurrentTime - HERO+0x1fd0 | **playtime (ms 또는 s)** |
| +0x12..+0x15 | u32 | SlotInfo+0x18 | HERO_class+0xa0 | **scene_idx** (현재 맵 ID) |
| +0x16 | u8 | SlotInfo+0x1c | HERO_class+0x8b | 게임 상태 flag |

**Body sub-blocks — file content layout 추가 매핑** (Round 43):

| file offset | size | source (gv+0x1474 sub-struct 가능) | 의미 추정 |
|---:|---:|---|---|
| +0x17..+0x116 | 256B memcpy | gv+0x288 | **block 0**: 인벤토리 grid 또는 stat 스냅샷 |
| +0x117..+0x216 | 256B memcpy | gv+0x388 | **block 1**: stat / buff cache |
| +0x217..+0x316 | 256B memcpy | gv+0x488 | **block 2**: secondary cache (skill cooldown 추정) |
| +0x317..+0x31b | 5B memcpy | gv+? | sub-block (5 단위 = formula stat slot 후보) |
| +0x31c..+0x320 | 5B memcpy | gv+? | sub-block |
| +0x321..+0x324 | 4B strb | individual fields | item slot markers |
| +0x425..+0x426 | 2B strb | flag pair | game state flags |
| +0x433..+0x438 | 6B strb | 6 individual byte fields | **sub-block 1** (cat-style 6 entries, 강화/orb socket 후보) |
| +0x45d..+0x462 | 6B strb | 6 individual byte fields | **sub-block 2** (sub-block 1 의 보조 — 같은 6 entries 의 두 번째 dim) |
| +0x487..+0x489 | 3B strb | individual fields | trailer markers |
| (+0x494..+0x496) | 3B | r8 base writes | (in-memory only — file 영역 아닐 가능 높음) |

**핵심 발견** (Round 43):
- **class + level encoded packing**: `file[0] = level * 10 + class`. 5 클래스 (0-4) +
  max level 약 25. 게임 디자인의 level cap 추정 가능.
- **gv+0x1474 sub-struct (Round 5/6 의 111 fields 영역) 가 save 의 핵심 source** —
  3 × 256B blocks 는 모두 gv+0x288/0x388/0x488 영역 (= V[58..167+] 의 stat/buff
  cache 와 인접한 영역). Load 가 그대로 복원 → save/load round-trip 안전.
- 7개 in-memory writes (r4 base, +0x0/+0x16/+0x18/+0x1c 등) 는 file 영역이 아니라
  SlotInfo struct 의 cached field — Save 후 다음 호출에서 사용.

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
