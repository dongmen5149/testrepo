# Hero4 Round 105 — drop_id 17 byte10=232 정확한 해석 (R97 정정)

> R97 의 ambiguity 해소. byte 단일이 아닌 LE16 임을 raw record 재검토로 확인.

## TL;DR

R97 에서 ambiguous 였던 drop_id 17 의 `byte10=232` 가 실제로는 **bytes[10-11] LE16 = 0x03e8 = 1000** 임을 raw record 재검토로 확정.

drop_id 17 = `_ITM_OPTION` (alphabetic order 유지) × **qty 1000** = endgame achievement 의 enchantment scroll 대량 보상.

## Raw record 분석 (4/4 entries 동일)

```
12000d008e0701001100e8030000ff0000000000  (Q_REPAY_0 #168/196 — EXP file)
12000d008cc602001100e8030000ff0000000000  (Q_REPAY_1 #168/196 — gold file)
```

bytes[8-13] = `[17, 0, 232, 3, 0, 0]`

- byte[8] = 17 (drop_id)
- byte[9] = 0 (item_idx — OPTION pool 첫 entry)
- **bytes[10-11] LE16 = 0x03e8 = 1000** (qty)
- bytes[12-13] = 0 (padding)

## Record format revised (variable-width qty)

| field | bytes | width | range |
|---|---|---|---|
| drop_id | [8] | 1B | 0-23 (ITM file alphabetic idx) |
| item_idx | [9] | 1B | item index within file |
| **qty** | **[10-11]** | **LE16** | **1-65535** (variable-width) |
| padding | [12-13] | 2B | reserved |

**대다수 drop 의 qty 가 < 256** 이라 byte[10] 단일로 보였으나, drop_id 17 의 qty=1000 이 LE16 임을 확인.

## qty examples revisited

### 작은 qty (byte[10] alone, byte[11]=0)

| drop | qty |
|---|---|
| ITM_12 가면 (quest) | 1 |
| ITM_08 제련석 (자원) | 5 |
| ITM_15 뇌격 (환수) | 8 |
| ITM_13 네트워크전용 (consumable 대량) | 64, 118 |

### 큰 qty (LE16, byte[11] > 0)

| drop | qty | 의미 |
|---|---|---|
| **drop_id 17 OPTION (endgame)** | **1000** | endgame achievement 의 OPTION enchantment scroll 대량 보상 |

## R97 정정 사항

| 항목 | R97 | R105 |
|---|---|---|
| field interpretation | byte[10]=232 single byte | **bytes[10-11] LE16=1000** |
| drop_id 17 의미 | OPTION 매핑 ambiguous (qty 232 fits 없음) | **OPTION × qty 1000** 확정 |
| 다른 drop 의 byte[11] | 0 (대부분) — single-byte qty 인 듯 | qty < 256 일 때 byte[11]=0 (LE16 still valid) |

drop_id 17 = `_ITM_OPTION` (alphabetic order index 16=CASH/17=OPTION/23=REPAY_2 모두 R97 매핑 그대로 유지). qty 만 LE16 변환.

## endgame achievement 보상 구조 (R96 + R97 + R105 통합)

repay#168/196 + repay#169/197 = **endgame achievement 의 2-step paired reward**:

| repay# | drop_id | item | qty | 의미 |
|---|---|---|---|---|
| 168 / 196 | 17 | `_ITM_OPTION` [0] | **1000** | enchantment scroll 1000개 |
| 169 / 197 | 16 | `_ITM_CASH_RANOMBOX` [0] | 1 | cash random box 1개 |

→ 게임 클리어 / 최종 보스 격파 보상 = **massive enchantment pool + 1 random cash box**.

## drop_id 통합 매핑표 (R96 + R97 + R105 최종)

| drop_id | 파일 | qty width | 의미 |
|---|---|---|---|
| 0-6 | `_ITM_00 ~ _ITM_06` | 1B byte[10] | 7 weapon classes |
| 8-15 | `_ITM_08 ~ _ITM_15` | 1B byte[10] | 8 item types |
| 16 | `_ITM_CASH_RANOMBOX` | 1B byte[10] | cash box (endgame) |
| **17** | **`_ITM_OPTION`** | **LE16 [10-11]** | **enchantment scrolls (large qty endgame)** |
| 23 | `_ITM_REPAY_2` | 1B byte[10] | reward currency type C |

## 산출

- `tools/converter/parse_h4_drop_id_17_fix.py` (신규)
- `work/h4/converted/h4_drop_id_17_fix.json` (3.2KB)
- `docs/h4/round105-drop-id-17-fix.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
2. **환수 합신 / 환수특공 / 환수증폭 dialogue 검색** (R103 후속)
3. **type=0 magic skill 의 sub-categorization** (R104 후속) — 54 skill 세분
4. **R100 milestone 결산 문서**
5. **OPTION 1928B 구조 정밀** (R105 후속) — 1928 / 16 = 120.5 non-integer, 다른 stride 가능성
