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

## Payload (미해독)

byte 8 부터 가변 길이 entry table. 정확한 byte layout 미확정.

샘플 `_H_000_EXD` (20 byte, 가장 작음):
```
header: 01 00 01 00 01 02 00 00
payload: 00 dd ff 01 f9 ff fc ff 0e 00 08 00
```

### 가설들

- **2-byte signed pairs (dx, dy)**: payload 12 byte = 6 페어. 일부 값이 자연스럽 (-7, -4, 14, 8) 이지만 첫 페어 (-35, -1791) 는 이상
- **Triplet (dx, dy, count) 또는 (frame_idx, anim_speed, ...)**: 3 byte 그룹 가능
- **Variable-length entries** with separator bytes (0xff 빈도 높음)

CIF 의 보완 데이터 추정. CIF 가 sprite frame 매핑이라면 EXD 는 **animation timing / event triggers / hitbox 정보** 가능성. Hero3 의 미해독 _cif animation 데이터와 같은 역할일 수도.

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
