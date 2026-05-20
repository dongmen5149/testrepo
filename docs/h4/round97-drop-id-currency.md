# Hero4 Round 97 — drop_id 16/17/23 currency 가설 검증 (R96 후속)

> R96 의 미해결 drop_id 3 종 의미 식별. 2/3 확정 + 1 ambiguous.

## TL;DR

| drop_id | 매핑 | byte9 범위 | 확정도 |
|---|---|---|---|
| **16** | **`_ITM_CASH_RANOMBOX`** (23 records, 16B stride) | 0 only | ✅ 확정 |
| **23** | **`_ITM_REPAY_2`** (74 records, 12B stride) | 2-20 (in range) | ✅ 확정 |
| 17 | `_ITM_OPTION` 또는 currency | byte10=232 invariant | ⚠ ambiguous |

핵심 발견: drop_id 가 ITM 파일의 **alphabetic order index** 로 매핑됨 (0-15 numeric, 16+ 명칭).

## drop_id 16 = `_ITM_CASH_RANOMBOX` (확정)

| repay# | source | byte9 | byte10 |
|---|---|---|---|
| 169 | Q_REPAY_0 drop1 | 0 | 1 |
| 197 | Q_REPAY_0 drop1 | 0 | 1 |
| 169 | Q_REPAY_1 drop1 | 0 | 1 |
| 197 | Q_REPAY_1 drop1 | 0 | 1 |

- 4 hits 모두 byte9=0, byte10=1 → CASH_RANOMBOX[0] qty=1
- `_ITM_CASH_RANOMBOX` = 23 records × 16B → byte9 ∈ [0, 22] valid range. 0 in range ✓
- endgame achievement (idx 169/197) 의 **1 개 cash box 보상**

## drop_id 23 = `_ITM_REPAY_2` (확정)

| repay# | source | byte9 | byte10 |
|---|---|---|---|
| 79  | Q_REPAY_0 drop2 | 5  | 1 |
| 83  | Q_REPAY_0 drop2 | 8  | 1 |
| 87  | Q_REPAY_0 drop2 | 2  | 1 |
| 88  | Q_REPAY_0 drop2 | 13 | 1 |
| 97  | Q_REPAY_0 drop2 | 11 | 1 |
| 5   | Q_REPAY_1 drop1 | 13 | 1 |
| 79  | Q_REPAY_1 drop2 | 5  | 1 |
| 83  | Q_REPAY_1 drop2 | 17 | 1 |
| 87  | Q_REPAY_1 drop2 | 2  | 1 |
| 88  | Q_REPAY_1 drop2 | 19 | 1 |
| 97  | Q_REPAY_1 drop2 | 20 | 1 |

- 11 hits, byte9 ∈ {2, 5, 8, 11, 13, 17, 19, 20} — **모두 [0, 73] range 내**
- `_ITM_REPAY_2` = 74 records × 12B
- 흥미: Q_REPAY_0 drop2 (예: repay#83 byte9=8) ≠ Q_REPAY_1 drop2 (byte9=17) — **EXP-pool 과 gold-pool 에서 다른 REPAY_2 sub-item 참조**

## drop_id 17 — ambiguous

| repay# | source | byte9 | byte10 | LE16 |
|---|---|---|---|---|
| 168 | Q_REPAY_0 drop1 | 0 | 232 | 59392 |
| 196 | Q_REPAY_0 drop1 | 0 | 232 | 59392 |
| 168 | Q_REPAY_1 drop1 | 0 | 232 | 59392 |
| 196 | Q_REPAY_1 drop1 | 0 | 232 | 59392 |

- 4 hits 모두 byte9=0, byte10=232 (invariant)
- alphabetic order 가설 → `_ITM_OPTION` (120 records)
- byte10=232 가 record idx 면 OOR (120 max)
- byte10=232 가 **currency qty** 가설 우세: endgame achievement 의 "OPTION enchantment scroll 232개" 또는 "EXP/gold token 232"

Endgame paired interpretation:
- repay#168/196 → drop_id 17 (OPTION scroll/token × 232)
- repay#169/197 → drop_id 16 (CASH_RANOMBOX × 1)

두 보상이 endgame 의 **2-step pair reward** (마지막 보스 사망시 cash box + enchantment 다발 동시 획득).

## drop_id 전체 매핑표 (R96 + R97 통합)

| drop_id | 파일 | 의미 |
|---|---|---|
| 0-6 | `_ITM_00 ~ _ITM_06` | 7 weapon classes |
| 7 | _ITM_07 없음 (skip) | — |
| 8-15 | `_ITM_08 ~ _ITM_15` | 8 item types (08=자원, 15=환수) |
| **16** | **`_ITM_CASH_RANOMBOX`** | cash box (endgame) |
| **17** | **`_ITM_OPTION` (or currency 232)** | enchantment pool / currency |
| 18-20 | `_ITM_Q_REPAY_0/1/2` | self-ref (used 없음 추정) |
| 21-22 | `_ITM_REPAY_0/1` | reward currency type A/B |
| **23** | **`_ITM_REPAY_2`** | reward currency type C (drop2 secondary) |

## 산출

- `tools/converter/parse_h4_drop_id_currency.py` (신규)
- `work/h4/converted/h4_drop_id_currency.json` (5.8KB)
- `docs/h4/round97-drop-id-currency.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
2. **n0124_scn tutorial 전문 분석** (R92 후속)
3. **bonus_id=0 + tier_value 의미** (R94 후속)
4. **character class skill (S000-S003) stat block schema** (R95 후속)
5. **drop_id 17 byte10=232 정확한 해석** (R97 후속) — OPTION idx vs currency qty 분리 검증
