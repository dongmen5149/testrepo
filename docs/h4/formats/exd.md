# `_EXD` 캐릭터 확장 데이터 (Hero4)

117개 파일 (`H4/EXD/_H_NNN_EXD`). H4/CIF, H4/PAL 과 페어 (=> 117 캐릭터).

## 헤더 (8 byte, 검증됨)

```
byte 0 : count          (1 ~ 35, frame/entry 카운트 추정)
byte 1 : 0x00
byte 2 : 0x01
byte 3 : 0x00
byte 4 : 0x01
byte 5 : subtype        (1, 2, 또는 3 — 대부분 3)
byte 6 : 0x00
byte 7 : 0x00
```

검증 통계:
- byte[1:4] == `00 01 00` : **115/117**
- byte[6:8] == `00 00`    : **114/117**

## Payload — count=1 케이스 풀림 (2026-05-18)

`byte 8` 부터의 payload 가 **box 데이터 (signed LE int16 dx, dy, w, h)** 임을 통계로 확정.

### count=1 entry layouts

| subtype | entry size | layout |
|---|---|---|
| 1 | 가변 (2/3/7B) | sentinel/footer 데이터 (5 files, 미정) |
| 2 | **12B** | 4B head + 1×8B box  (14 files) |
| 3 | **21B** | 4B head + box1(8) + sep_byte(0x02) + box2(8)  (26 files) |

**4B head**: `00 ?? ff 01`
- byte 0 = 0x00 (entry marker)
- byte 1 = variable (sprite id / character id / y-offset)
- byte 2 = 0xff (separator)
- byte 3 = 0x01 (flag, "first box follows")

**8B box** (4 × signed LE int16):
- `dx, dy` = top-left offset (보통 음수, ±10)
- `w, h` = width/height (양수, 8~32)

### count=1, subtype=3 box 분포 (26 파일 통계)

| | box1 (feet/collision) | box2 (body/sprite) |
|---|---|---|
| dx | -10 ~ -5 (avg -8) | -10 ~ -5 (avg -7) |
| dy | -10 ~ -3 (avg -5) | **-34 ~ -9** (avg -24) |
| w | 10 ~ 20 (avg 14) | 10 ~ 20 (avg 12) |
| h | 8 ~ 12 (avg 9) | **16 ~ 40** (avg 25) |

→ box1 = 캐릭터 발 / 충돌 박스 (~14×9 around feet)
→ box2 = 캐릭터 sprite render bounds (~12×25 tall, dy~-24 = 머리 위치)

샘플:
- `_H_021_EXD`: box1=(-7,-4,14,8) box2=(-5,-25,10,25) — 평범한 캐릭터
- `_H_014_EXD`: box1=(-8,-6,16,12) box2=(-8,-9,16,16) — 작은 NPC

### count>1 케이스 (72 files, 부분 풀림)

count=2~35 multi-entry 파일. **첫 entry 는 subtype=3 (21B) 동일 layout**. 두번째+ entry 는 가변 길이, `0x03` box separator 패턴 발견:

```
_H_010_EXD count=2 (53B payload):
  entry1 (21B): [subtype=3 layout — box1 + 0x02 + box2]
  entry2 (32B): 5B prefix + 0x03 + box + 0x03 + box + 0x03 + box
```

추가 box 들이 추가 animation frame / attack hitbox 으로 보임. 정확한 entry 2+ 구조는 Phase B Ghidra 분석으로 보류.

### 파서 + JSON 출력

[tools/converter/parse_h4_exd.py](../../tools/converter/parse_h4_exd.py) 117 파일 모두 파싱, `work/h4/converted/exd_parsed.json` 출력. 117/117 처리, header_check 112/117 통과.

## Size 분포 (117 파일)

| 범위 | 개수 | 추정 |
|---|---|---|
| 0~99 | 88 | 단순 캐릭터 (NPC/소형 enemy) |
| 100~299 | 18 | 중간 |
| 300~999 | 4 | 풍부한 데이터 |
| 1000+ | 7 | 메인 캐릭터 (히어로/보스) |

## Subtype 분포

- subtype=1: 2개
- subtype=2: 1개  
- subtype=3: 114개 (대부분)

subtype 의 의미는 미확정. `count` byte 와 조합되어 entry 구조가 다를 가능성.

## 변환

`tools/converter/convert_exd.py` 가 헤더 추출 + payload hex 보존만:
```json
{
  "count": 1,
  "header": "010001000102000000",
  "subtype": 2,
  "payload_size": 12,
  "payload_first_64": "ddff01f9fffcff0e000800"
}
```

정확한 entry struct 는 Ghidra 에서 `/H4/EXD/_H_%03d_EXD` 로더 함수 추적 후 확정.
