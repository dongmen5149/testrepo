# Hero4 Round 80 — ESDAT 73B phase block 의 6B inter-phase link

> R79 의 73B/phase 가설 정밀화. inter-phase 6B link 구조 해독.

## TL;DR

ESDAT outlier 인카운터의 layout 확정:

```
encounter = N × 73B phase block + 67B final-phase
```

검증 (정확):
- 140B = **1** × 73 + 67 (1 phase + final)
- 213B = **2** × 73 + 67 (2 phase + final)
- 432B = **5** × 73 + 67 (5 phase + final)

73B phase block 구조:
```
pos[0..41]   base stat (R78 67B 와 동일 layout)
pos[42-43]   0xff 0x3f section marker
pos[44..66]  drop/reward (R78 와 동일)
pos[67-72]   ★ 6B inter-phase link
```

마지막 67B 블록은 link 없이 끝 = "loot / final encounter".

## 6B link 구조

```
bytes[0]     = 0x47 (constant — 'G' 또는 link signature)
bytes[1]     = 0x00 (constant padding)
bytes[2-3]   = LE16 phase ID (sequential per next-encounter)
bytes[4-5]   = LE16 transition marker
```

### transition marker 의미

| 값 | hex LE16 | 의미 추정 |
|---|---|---|
| 0xbcb1 | `b1 bc` | 다음 phase = final/loot (마지막 phase 직전) |
| 0xfabf | `bf fa` | 다음 phase = continue (계속) |

### 오토마톤 432B 의 phase progression

| phase | link bytes[2-3] LE16 | link bytes[4-5] | 해석 |
|---|---|---|---|
| 0 → 1 | 0x028e (654) | `bf fa` | continue |
| 1 → 2 | 0x028f (655) | `bf fa` | continue |
| 2 → 3 | 0x0290 (656) | `bf fa` | continue |
| 3 → 4 | 0x0291 (657) | `b1 bc` | **final 진입** |
| 4 → final | 0x0292 (658) | `b1 bc` | final |

phase ID sequential (+1) → encounter chain (선형 진행).

### 좀비 213B

| phase | link bytes[2-3] | link bytes[4-5] |
|---|---|---|
| 0 → 1 | 0x023f | `b1 bc` |
| 1 → final | 0x0240 | `b1 bc` |

좀비는 짧은 chain, 모두 `b1 bc` (보스 진입 즉시 final 직행).

## 정정

R79 의 "73B/phase 만 반복" 가설 → 마지막 67B trailer 가 항상 추가됨. 즉 multi-phase 인카운터의 **마지막 phase 는 link 가 없다** (67B 만).

## 72B 죽음의 구 anomaly

72B = 0 × 73 + 72 = single phase + 5B extra. 0xff 0x3f marker 부재 → 67B 표준 layout 가 아니다. 특수 적 (보스 카운트다운 / mini-boss). 후속 분석.

## 기갑병 140B anomaly

phase 0 의 pos[42-43] = `33 33` (0xff 0x3f 아님). 다른 outlier 와 다른 layout — `0xff 0x3f` 가 trailer 내부에만 존재. 한 phase 가 다른 record 형식 사용 가능성.

## 다음 후보

1. ⭐ link bytes[2-3] phase ID (654-658 등) ↔ 다른 ESDAT entry index 매핑 (chain reference?)
2. 72B 죽음의 구 / 기갑병 140B variant 정밀
3. 보스 phase stat 강화율 정량 (일반 67B 대비)

## 산출

- `docs/h4/round80-esdat-phase-link.md` (이 문서)
- (도구 변경 없음, 분석만)
