# `HDAT/` 디렉토리 (Hero4)

25개 파일. 정확한 binary layout 은 미해독 (Ghidra 후 확정). 이름과 byte 패턴으로 그룹 분류만 됨.

## 그룹 분류

### Group A: SCN 과 동일 DES 키로 암호화된 파일 (2026-05-18 확정)

| 파일 | size | 첫 16 byte | 마지막 8 byte |
|---|---|---|---|
| `_H_BH` | 168 | `a8 20 86 97 89 85 61 60 d8 2a 78 37 ff 65 26 e6` | `83dff219dcc9f35a` |
| `_H_BS` | 136 | `b4 fb 29 43 29 52 87 2e 87 cf 88 ca e6 5f 0b 1b` | `39e9584b1712bfeb` |
| `_H_SA` | 960 | `d6 88 89 5a d1 58 8f 09 e4 d3 87 c0 39 a8 d5 eb` | **`3b7af9a427907dac`** |
| `_H_SS` | 1624 | `fc 62 5b 25 d6 cc 5e 57 e8 35 0c 9d 89 78 45 13` | `396f68546fede600` |
| `_H_S000` | 1232 | `00 37 d8 65 1d b7 70 d5 62 51 e3 7b 1b 55 71 a3` | `762c70a60e2c74e8` |
| `_H_S001` | 1176 | `6f d8 f0 c8 ba 5a 00 40 f3 9a 77 c4 d2 ff e1 bd` | `096ad10bdc06a2a8` |
| `_H_S002` | 1184 | `00 37 d8 65 1d b7 70 d5 62 51 e3 7b 1b 55 71 a3` | `ef84db78eeffa299` |
| `_H_S003` | 1240 | `56 75 45 58 c1 f0 c2 2b b3 cd e1 d4 21 13 e0 48` | `49d7199144ed8908` |

**모두 8-byte aligned, entropy 6.3~7.8 (high) → DES ECB 암호화 확정**.

**결정적 증거** — SCN 의 가장 흔한 last cipher block `3b7af9a427907dac` (348 SCN 중 38회 = sentinel) 가 Group A 에서도 **92회 반복 등장** (sliding window):
- `_H_SA`: 37회 (마지막 8 byte 가 정확히 이 sentinel)
- `_H_SS`: 23회
- `_H_S001`: 9회, `_H_S003`: 8회, `_H_S000`: 7회, `_H_S002`: 5회, `_H_BS`: 3회

→ **SCN + HDAT Group A 가 동일 DES 키 사용**. Phase B 에서 키 발견 시 자동 파이프라인에 **Group A 8 파일도 포함**:

```bash
# decrypt_h4_scn.py 확장 또는 별도:
python tools/converter/decrypt_h4_scn.py --key <KEY> work/h4/extracted/HDAT/_H_SA decoded.bin
```

**파일 간 cipher block sharing** (같은 plaintext patterns 시사):
- `_H_S000` ↔ `_H_S002`: 9 shared blocks (첫 16 byte 동일 + 9 blocks common → save template 변형)
- `_H_S002` ↔ `_H_S003`: 7 shared
- `_H_S001` ↔ `_H_S002`: 6 shared
- `_H_S001` ↔ `_H_S003`: 4 shared

추정 의미 (Ghidra 후 확정):
- `_H_BH` (168B = 21 blocks) — Boss Hero data
- `_H_BS` (136B = 17 blocks) — Boss Stat data  
- `_H_SA` (960B) — Save template A (Hardcore?)
- `_H_SS` (1624B) — Save template SS (?)
- `_H_S000~S003` — Save game default slot templates 4종

### Group B: progression / cost table — **2026-05-18 풀림**

`_H_P000` ~ `_H_P005` 6개 파일. **`3B header + N × 50B entries`** 일관된 layout.

```
Header (3 bytes):
   byte 0  : group_type (P000=0, P005=1, P004=2, P001/P002/P003=3)
   byte 1  : 0x00
   byte 2  : 0x00

Entry (50 bytes):
   offset 0..15 (16B) : 8 × uint16 LE — main progression values
      val[0] : 5/10/15/20/50            ← level / rank / count
      val[1] : 300~1000                  ← HP / cost / stat1
      val[2] : 0 always                  ← reserved
      val[3] : 400~2000                  ← stat2
      val[4] : 0 always                  ← reserved
      val[5] : 100~20000                 ← gold / EXP / large value
      val[6] : 800~1500                  ← atk / def
      val[7] : 1000~2000                 ← hp_max / cap
   offset 16 (1B)     : marker (0xff in 11/13 entries, 0x00 for P004 entry[0])
   offset 17..21 (5B) : param block (0xb4 0xf4 0xc8 ... 식, 의미 미정)
   offset 22..49 (28B): 14 × uint16 LE — nested sub-records (대부분 0, 일부 stat pair)
```

| 파일 | size | group | N | 대표 entry main_values |
|---|---|---|---|---|
| `_H_P000` | 53 | 0 | 1 | [20, 400, 0, 600, 0, 200, 1400, 2000] |
| `_H_P001` | 103 | 3 | 2 | [10, 300, 0, 400, 0, 100, 1500, 2000] |
| `_H_P002` | 103 | 3 | 2 | [10, 600, 0, 1000, 0, 200, 800, 1200] |
| `_H_P003` | 103 | 3 | 2 | [15, 500, 0, 800, 0, 200, 900, 1400] |
| `_H_P004` | 153 | 2 | 3 | [10, 1000, 0, 2000, 0, **20000**, 1000, 2000] ← entry[0] mk=0x00 outlier |
| `_H_P005` | 103 | 1 | 2 | [5, 1000, 0, 2000, 0, 200, 1000, 2000] |

해석 가설: 각 entry = 1 tier/grade 의 stat threshold (level cap, hp_max, gold reward 등). group 별로 다른 카테고리 (P000=intro tutorial, P004=boss/special, P005=basic tier). 정확한 field 매핑은 Phase B Ghidra 후.

파서: [tools/converter/parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py), 출력 JSON: `work/h4/converted/hdat_p_parsed.json`.

### Group C: 캐릭터 클래스 progression (70-byte, 공통 prefix) — **2026-05-14 entry layout 추론 완료**

9개 파일. **PS000~007 = 70 byte 동일 schema**, **PS008 = 69 byte 별도 schema**.

[`tools/recon/analyze_hdat_ps.py`](../../tools/recon/analyze_hdat_ps.py) 의 byte-position 분포 분석으로 다음 layout 확정 (Ghidra 없이 통계 추론):

**Schema A — PS000~007 (70 bytes)**:

```
Header (10 bytes, offset 0..9):
   byte 0..5: 06 00 01 02 03 04        ← 고정 signature/version
   byte 6   : <class>                  ← 1..4 (1=워리어, 2=마법, 3=도적, 4=궁수)
   byte 7..9: 01 01 06                 ← 고정

6 records × 10 bytes (offset 10..69):
   byte 0   : 01                       ← 레코드 marker (PS003 R4/R5 만 a5)
   byte 1   : 85                       ← 고정 type code
   byte 2   : <param_a>                ← 캐릭터별 고정 (PS000=0x0b, PS001=0x28, PS003=0x0a, PS004=0x08)
   byte 3..4: <flags>                  ← 보통 00 00 (PS003 만 변형)
   byte 5,6 : <stat_pair> (보통 동일)  ← e.g. PS000: 0a/0a → 09/09 → 07/07 → 06/06...
   byte 7   : <extra>                  ← 보통 00 (PS003 만 sequence)
   byte 8   : <curve>                  ← PS000: ff→f0→dc→c8→c8→c8 (255→240→220→200 plateau)
   byte 9   : <terminator>             ← 보통 0x1c (PS003 만 0x10/0x11)
```

| 파일 | class | byte 2 param | byte 5/6 stat seq (R0→R5) | byte 8 curve (R0→R5) |
|---|---|---|---|---|
| PS000 | 1 워리어 | 0x0b | 10/9/7/6/6/6 (descending) | ff/f0/dc/c8/c8/c8 |
| PS001 | 2 마법 | 0x28 | 5/5/5/5/5/5 (flat) | ff/ff/dc/c8/c8/c8 |
| PS002 | 2 마법 | 0x28 | 8/8/8/8/8/8 (flat) | ff/ff/dc/c8/c8/c8 |
| PS003 | 3 도적 | 0x0a | 10/10/10/10/10/10 | ff/ff/ff/b4/78/50 (special curve) |
| PS004 | 3 도적 | 0x08 | 8/8/8/8/8/8 | ff/ff/d2/dc/c8/c8 |
| PS005 | 3 도적 | 0x09 | 8/8/8/8/8/8 | ff/ff/dc/d2/c8/c8 |
| PS006 | 4 궁수 | 0x06 | 8/8/8/8/8/8 | ff/ff/dc/d2/c8/c8 |
| PS007 | 4 궁수 | 0x09 | 8/8/8/6/6/6 (taper) | ff/dc/d2/c8/c8/c8 |

**해석 가설** (Hero3 캐릭터 시스템 유사):
- 6 records = **6 레벨/단계** (성장 곡선)
- byte 5/6 stat pair = 레벨별 기본 능력치 (HP/MP/ATK?)
- byte 8 curve = 다른 progression (cost? 누적 EXP? 0xff=∞ sentinel → 점진 감소)
- PS003 (도적 0x0a) 가 특이한 변형 → 메인 캐릭터 또는 부스터 캐릭터 (`a5` 레코드 marker 변화)

**Schema B — PS008 (69 bytes)**: 별도 entity (보스 / 펫 / 탈것 추정)
- 헤더 끝 차이: `05 00 01 02 03 00 01 01 06 01` (vs PS000-007 `06 00 01 02 03 04 <c> 01 01 06`)
- byte 5 = 0x00 (PS000-007 은 0x04)
- 레코드 패턴이 PS000-007 과 align 안 됨 — 별도 파서 필요

원본 분석 데이터: [`work/h4/converted/hdat_ps_analysis.json`](../../work/h4/converted/hdat_ps_analysis.json)

### Group D: 게임 시작 / UI 메타 — **2026-05-18 부분 풀림**

#### `_H_SG` (170B) — Save Game 슬롯 헤더

**10 슬롯 × 17B** (170 / 17 = 10) 구조 확정.

```
17B slot layout:
  byte 0..11 (12B): 고정 prefix
     slots 0..4: 0f 00 13 13 ff ff 0c ff ff ff 05 ff   (group "13 13")
     slots 5..9: 0f 00 12 12 ff 13 0c 0e ff ff 05 ff   (group "12 12")
  byte 12..16 (5B): variable
     slot 0,5: ff ff ff ff ff   (empty)
     slot 1,6: 8b ff ff ff 8f
     slot 2,7: 8c ff ff ff 90
     slot 3,8: 8d ff ff ff 91
     slot 4,9: 8e ff ff ff 92
```

해석 가설: **2 모드 × 5 기본 캐릭터** = 10 슬롯. var byte 0 (8b~8e) = starting character CIF id, var byte 4 (8f~92) = starting zone id. 2 모드 = (Normal, Hardcore?) 또는 (Story, Free?).

#### `_H_PDAT` (86B) — Player initial data, 17 records (variable-length)

records terminated by `0xff` byte. 첫 record `0e 00 00 00 00 00` (byte 0 = 14, count?), 이후 16 records.

| rec | size | hex | 추정 |
|---|---|---|---|
| 0 | 6B | `0e 00 00 00 00 00` | 헤더 (14 = total record count?) |
| 1-3 | 5B | `01 03 00 00 00`, `00 01 01 01 02`, `01 03 01 01 02` | character/skill init triples |
| 4-10 | 4-5B | `00 00 02 05`, ... 7개 | quest/event triggers |
| 11-16 | 2-3B | `00 05`, `08 01`, ... | inventory/shortcut slots |

정확한 field 명명은 Phase B Ghidra 후. 0xff 가 record separator 임은 SCN bytecode 와 같은 패턴.

## 변환 결과

현재 `tools/converter/` 에 HDAT 파서 부분만. 모든 파일이 `skipped` 카운트에 포함되어 있었으나 PS schema 가 풀려서 일부 자동 파싱 가능.

```python
# 작성 가능
tools/converter/convert_h4_hdat.py
  - parse_ps_a(data)              → Schema A (PS000-007): class + 6 records
  - parse_ps_b(data)              → Schema B (PS008): 별도 entity
  - parse_progression_table(data) → exp_table.json (Group B, Phase B 후)
  - parse_save_template(data)     → save_template_blob (Group A, 보존만)
```

## 미해독: 그룹 A/B/D 의 정확한 entry struct

- **Group A** (random-look): 암호화 시드 or save template. Phase B 에서 `_DAT_DES` 키 발견 후 복호화 시도 가능
- **Group B** (P000-P005): uint8/16/32 LE progression. 정확한 의미는 Phase B 에서 string xref 또는 게임 로직 추적 후 확정
- **Group D** (PDAT, SG): Player Data 초기값 / Save Game 메타. Phase B 에서 string `'frameBuf is NULL'` 인접 함수에서 SaveGame 로직 추적
- **Group C PS008**: 별도 schema. byte 0 = 0x05 (다른 그룹은 0x06) → entity type 분기

Phase B 에서 다음 string xref 추적 보강:
- `/HDAT/_H_P*`, `/HDAT/_H_PS*`, `/HDAT/_H_S*` 같은 path string 이 binary 에 있는지 확인 (extract_strings 결과에서 보이지 않음 — 직접 파일명 enum 으로 로드되거나 인덱스 매핑)
- 에러 메시지 인접 함수에서 HDAT 진입점 추적
