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

### Group C: 캐릭터 클래스 progression (70-byte 비슷, 공통 prefix)

9개 파일 모두 70 byte 동일 크기:
| 파일 | 첫 12 byte |
|---|---|
| `_H_PS000` | `06 00 01 02 03 04 01 01 01 06 01 85` |
| `_H_PS001` | `06 00 01 02 03 04 02 01 01 06 01 85` |
| `_H_PS002` | `06 00 01 02 03 04 02 01 01 06 01 85` |
| `_H_PS003` | `06 00 01 02 03 04 03 01 01 06 01 85` |
| `_H_PS004` | `06 00 01 02 03 04 03 01 01 06 01 85` |
| `_H_PS005` | `06 00 01 02 03 04 03 01 01 06 01 85` |
| `_H_PS006` | `06 00 01 02 03 04 04 01 01 06 01 85` |
| `_H_PS007` | `06 00 01 02 03 04 04 01 01 06 01 85` |
| `_H_PS008` | `05 00 01 02 03 04 04 01 01 06 01 84` (size=69, 다름) |

공통 prefix `06 00 01 02 03 04` → byte 6 (`01`/`02`/`03`/`04`) 가 클래스 분류 (1: 워리어계, 2: 마법계, 3: 도적계, 4: 궁수계 추정). 9개 캐릭터의 클래스 progression 데이터.

Hero3 분석에서 발견된 캐릭터별 클래스 (리츠 5클래스, 케이 5클래스 등) 와 유사한 시스템.

### Group D: 게임 시작 / UI 메타

| 파일 | size | 첫 12 byte | 추정 |
|---|---|---|---|
| `_H_PDAT` | 86 | `0e 00 00 00 00 00 ff ff 01 03 00 00` | Player Data 초기값 |
| `_H_SG` | 170 | `0f 00 13 13 ff ff 0c ff ff ff 05 ff` | Save Game 메타 / 슬롯 헤더 |

## 변환 결과

현재 `tools/converter/` 에 HDAT 파서 없음. 모든 파일이 `skipped` 카운트에 포함. 정확한 entry layout 은 Ghidra 분석 후 게임-specific 파서 작성:

```python
# 미래 작성 예시
tools/converter/convert_h4_hdat.py
  - parse_progression_table(data) → exp_table.json
  - parse_class_data(data) → classes.json
  - parse_save_template(data) → save_template_blob (보존만)
```

## 미해독: 정확한 entry struct

각 그룹의 entry layout 은 Ghidra 에서 다음 string xref 추적:
- `/HDAT/_H_P*`, `/HDAT/_H_PS*`, `/HDAT/_H_S*` 같은 path string 이 binary 에 있는지 확인 (extract_strings 결과에서 보이지 않음 — 직접 파일명으로 로드되거나 인덱스 매핑)
- 또는 string `'frameBuf is NULL'` 처럼 에러 메시지에서 함수 진입점 추적

Phase B 단계에서 진행.
