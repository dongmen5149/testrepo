# Hero4 Round 85 — Quest reward LE32 분포 (EXP vs gold 분리)

> R83 의 stride 만 식별한 Q_REPAY 파일에서 LE32 reward 값 의미 추정.

## TL;DR

`_ITM_Q_REPAY_0/1` 각 200 records × 20B 동일 stride 인데 **LE32 boost 값이 ~11배 차이**:

| 파일 | LE32@4 범위 | median | 평균 | 가설 |
|---|---|---|---|---|
| `_ITM_Q_REPAY_0` | 0 → 88,100 | **3,700** | low | **EXP 보상** |
| `_ITM_Q_REPAY_1` | 0 → 399,000 | **41,700** | high | **gold 보상** (~11× EXP) |

같은 200 quest 인덱스에 두 파일이 동일 record idx 로 대응 → **Q_REPAY_0 = EXP, Q_REPAY_1 = gold** 분할 저장.

## Record layout (20B 확정)

```
[size=0x12][00][0e][00][LE32 reward][3B drop?][7B padding/extra]
```

샘플 (Q_REPAY_0 메인 quest):
| idx | LE32 EXP | 비고 |
|---|---|---|
| 0 | 80 | 초기 quest (자은 tutorial) |
| 1 | 3300 | 초반 |
| 2 | 8070 | |
| 5 | 19680 | 중반 점프 |
| 8 | 1720 | 사이드 분기 |

Q_REPAY_1 (gold) idx 0..7: 19400 → 47500 → 10900 → 16400 → 67100 → 39900 → 79800.

## R70 quest count mismatch

- R70 (`_QUEST_0_DAT` + `_QUEST_1_DAT`) = **128 quests** (메인 62 + 사이드 66)
- Q_REPAY_0/1 record 수 = **200 each**

72 record 차이 가능성:
1. Q_REPAY 는 quest 외 **achievement / event reward** 도 포함
2. quest 1개당 multiple reward stages (대화 1→2→3 단계별 별도 reward)
3. R70 의 128 quests 중 일부가 multiple reward index 사용 (128 × 1.56 avg ≈ 200)

R83 의 Q_REPAY_2 (332 records × 12B) 는 단발성/이벤트 보상 별도 풀일 가능성.

## `_ITM_REPAY_0/1` 매핑

- `_ITM_REPAY_0` (88 records × 14B) — Quest 외 일반 reward (적 처치 / 이벤트)
- `_ITM_REPAY_1` (74 records × 12B) — REPAY_0 의 sub-type

REPAY_0 의 record 일부에 `ff ff ff ff` 빈 reward marker → **conditional reward** (조건 미충족 시 skip).

## 후속

1. ⭐ Q_REPAY_0 / Q_REPAY_1 record idx ↔ R70 quest name 매핑 (200 record - 128 quest 차이 해소)
2. Q_REPAY 의 3B drop bytes (offset 8-10) 의미 — drop item idx?
3. CASH_RANOMBOX 23 records 의 보상 풀 (캐시 박스 = 유료 아이템)

## 산출

- `docs/h4/round85-quest-reward-distribution.md` (이 문서)
- (도구 변경 없음 — 분포 분석만)
