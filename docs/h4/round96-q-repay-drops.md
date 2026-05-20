# Hero4 Round 96 — Q_REPAY drop_id 의미 검증 + ITM cross-ref

> R90 의 "drop_id 의미" 미해결 해소. 65 drop record 의 대부분이 ITM 카탈로그로 정확 매핑됨을 확인.

## TL;DR

Q_REPAY_0/1 의 20B record 의 drop slot 구조 확정:

```
bytes[8-10]:  drop slot 1 = [ITM_file_id:1B][item_idx:1B][qty:1B]
bytes[14-16]: drop slot 2 (보통 [0xff,0,0] = empty)
```

전 65 drop record 중 **55 (85%)** 가 `_ITM_NN_DAT` 의 item entries 에 직접 매핑됨.

## 검증된 quest ↔ 보상 매핑 예시

| repay# | quest | drop file/idx | 보상 item | qty |
|---|---|---|---|---|
| 15 | 추가병력 합류 | ITM_12 [3] | **가면** | 1 |
| 23 | 주둔지 침입 | ITM_12 [5] | **하급통행증** | 1 |
| 24 | 유물 탈취 | ITM_12 [6] | **중급통행증** | 5 |
| 25 | 프로비던스로 | ITM_12 [7] | **상급통행증** | 1 |
| 60 | 전이장치 | ITM_12 [12] | **단열복** | 1 |
| 70 | 선박 탈취 | ITM_08 [6] | **제련석** | 5 |
| 73 | 방어 준비 이후 | ITM_11 [0] | **뇌제** | 1 |
| 75 | 웜의 껍질 | ITM_08 [9] | **암즈탄** | 5 |
| 76 | 스트레이츠 | ITM_10 [4] | **그라디우스** | 5 |
| 77 | 악령 | ITM_12 [15] | **편지** | 1 |
| 95 | 팔리아스의 봉인 | ITM_12 [35] | **유품** | 1 |
| 167 | (extra) | ITM_15 [0] | **뇌격** (환수) | 8 |

→ quest 이름과 보상 item 이 **thematically 정확 일치**. 추가 검증 불필요한 수준.

## drop_id 분포 (65 records)

| drop_id | 파일 | 매핑 count | 비고 |
|---|---|---|---|
| 12 | `_ITM_12_DAT` (38 items) | **24** | quest item 의 핵심 (가면/통행증/단열복/편지 등) |
| 8  | `_ITM_08_DAT` (29 items) | 8 | 자원 (제련석/암즈탄) |
| 11 | `_ITM_11_DAT` (13 items) | 8 | 무기 (뇌제) |
| 13 | `_ITM_13_DAT` (1 item) | 5 | "네트워크전용" 단일 item (qty 변동) |
| 10 | `_ITM_10_DAT` (38 items) | 5 | 장비 (그라디우스) |
| 15 | `_ITM_15_DAT` (10 items) | 4 | **환수 catalog** (R92 발견) |
| 4  | `_ITM_04_DAT` (17 DAT + SD) | 2 | 단공격 무기 |
| 16 | (unknown) | 4 | drop_id > 15, 가상 currency 가설 |
| 17 | (unknown) | 4 | drop_id 17, qty=232 등 → **gold/EXP currency** 가설 |
| 23 | (unknown) | 1 | 단일 outlier |

### drop_id > 15 (16/17/23) 의 추정

`_ITM_NN_DAT` 파일은 16+ 부재. drop_id 17 record (repay#168) 의 qty=232 등 큰 값 → **currency type id** 가능성 (16=gold, 17=EXP-multiplier 등). R97+ 별도 검증 가능.

## SD subdata 통합 가설

ITM_04 DAT(17) + ITM_4_SD(10) = 27 items. drop record 가 item_idx=22 (DAT 16 max 초과) 일 때 → SD[5] 로 매핑되는 것으로 추정. 6 record 가 DAT range 초과하나 SD count 합산으로 거의 cover.

## R90 후속 결론

| R90 미해결 | R96 결과 |
|---|---|
| drop_id 가 ITM 아이템 idx 인지 검증 | ✅ 확정 (drop_id = ITM file index 1B + item_idx 1B + qty 1B) |
| 두 drop slot 인가? | ✅ 확정 (slot 1 at [8-10], slot 2 at [14-16]) |
| out-of-range item_idx 어떻게? | _ITM_X_SD subdata 와 결합 (DAT count 가산) |
| drop_id > 15 | gold/EXP currency 추정 (R97+ 검증) |

## 산출

- `tools/converter/parse_h4_q_repay_drops.py` (신규)
- `work/h4/converted/h4_q_repay_drops.json` (27.8KB)
- `docs/h4/round96-q-repay-drops.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **drop_id 16/17/23 currency 가설 검증** (R96 후속)
2. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
3. **n0124_scn tutorial 전문 분석** (R92 후속)
4. **bonus_id=0 + tier_value 의미** (R94 후속)
5. **character class skill (S000-S003) stat block schema** (R95 후속)
