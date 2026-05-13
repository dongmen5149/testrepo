# `HDAT/` 디렉토리 (Hero4)

25개 파일. 정확한 binary layout 은 미해독 (Ghidra 후 확정). 이름과 byte 패턴으로 그룹 분류만 됨.

## 그룹 분류

### Group A: random-look 큰 파일 (저장 템플릿 / 암호화 시드 추정)

| 파일 | size | 첫 16 byte |
|---|---|---|
| `_H_BH` | 168 | `a8 20 86 97 89 85 61 60 d8 2a 78 37 ff 65 26 e6` |
| `_H_BS` | 136 | `b4 fb 29 43 29 52 87 2e 87 cf 88 ca e6 5f 0b 1b` |
| `_H_SA` | 960 | `d6 88 89 5a d1 58 8f 09 e4 d3 87 c0 39 a8 d5 eb` |
| `_H_SS` | 1624 | `fc 62 5b 25 d6 cc 5e 57 e8 35 0c 9d 89 78 45 13` |
| `_H_S000` | 1232 | `00 37 d8 65 1d b7 70 d5 62 51 e3 7b 1b 55 71 a3` |
| `_H_S001` | 1176 | `6f d8 f0 c8 ba 5a 00 40 f3 9a 77 c4 d2 ff e1 bd` |
| `_H_S002` | 1184 | `00 37 d8 65 1d b7 70 d5 62 51 e3 7b 1b 55 71 a3` |
| `_H_S003` | 1240 | `56 75 45 58 c1 f0 c2 2b b3 cd e1 d4 21 13 e0 48` |

`_H_S000` 와 `_H_S002` 의 첫 16 byte 동일 — 같은 시드로 만든 변형 가능성.

`_H_BH` (Boss Hero?), `_H_BS` (Boss Stat?), `_H_SA/SS` (?). `_H_S???` 는 Save 템플릿 0~3 슬롯 추정.

### Group B: progression / exp_table (uint8/16/32 LE values)

| 파일 | size | 첫 12 byte |
|---|---|---|
| `_H_P000` | 53 | `00 00 00 14 00 90 01 00 00 58 02 00` |
| `_H_P001` | 103 | `03 00 00 0a 00 2c 01 00 00 90 01 00` |
| `_H_P002` | 103 | `03 00 00 0a 00 58 02 00 00 e8 03 00` |
| `_H_P003` | 103 | `03 00 00 0f 00 f4 01 00 00 20 03 00` |
| `_H_P004` | 153 | `02 00 00 0a 00 e8 03 00 00 d0 07 00` |
| `_H_P005` | 103 | `01 00 00 05 00 e8 03 00 00 d0 07 00` |

uint16/32 값들의 패턴 (`0x190=400`, `0x258=600`, `0xc8=200`, `0xd007=2000`) → exp / HP / level cap 같은 progression value table 추정.

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

### Group D: 게임 시작 / UI 메타

| 파일 | size | 첫 12 byte | 추정 |
|---|---|---|---|
| `_H_PDAT` | 86 | `0e 00 00 00 00 00 ff ff 01 03 00 00` | Player Data 초기값 |
| `_H_SG` | 170 | `0f 00 13 13 ff ff 0c ff ff ff 05 ff` | Save Game 메타 / 슬롯 헤더 |

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
