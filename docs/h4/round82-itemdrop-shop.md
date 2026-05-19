# Hero4 Round 82 — Track C: ITEMDROP + BASIC_SM_DAT + SD 상점

> R69 의 "raw 만 추출" 상태에서 entry struct 풀이 완료.

## TL;DR

3 종류 보조 파일 모두 **DES 평문** (암호화 없음). 모두 빠르게 파싱.

| 파일 | size | 결과 | 의미 |
|---|---|---|---|
| `_ITEMDROP` | 72B | 9 records × 8B drop table | 적 처치 시 drop pool (slot[0..5]) |
| `BASIC_SM_DAT` | 220B | 5 records × 44B | 5 기본 프로필 (모두 stat=[8,8,8,0] baseline) |
| `_ITM_SD0` | 957B | 35 entries | 스톤/소마주/흑색마도/극주/쌍기주 단계 상점 |
| `_ITM_SD1` | 1249B | 39 entries | 파워젬/파워러젬 단계 상점 |
| `_ITM_SD2` | 651B | 27 entries | 진골/용골 단계 상점 |

## ITEMDROP layout

```
record = [type=0x06][reserved=0x00][slot0..slot5]  (8B fixed)
0xff = empty slot, else = item index
```

9 records:
- rec 0-1: 전부 empty (placeholder)
- rec 2-3: item 20 + 26 (early game)
- rec 4-5: item 21-22 + 27 (mid)
- rec 6-8: items 23-29 (late, 4-5 unique items per drop)

→ **floor/area 별 drop pool 인덱스 진행** (적이 떨어뜨릴 수 있는 후보 풀).

## BASIC_SM_DAT layout

```
record = [marker=0x2a][00][id:1B][00][stat:4B][rest mostly zeros]  (44B fixed)
```

5 records, id = 0..4, 모두 stat[4-7] = `[8, 8, 8, 0]` baseline.

해석: **5 시스템 초기 프로필 / 카테고리 기본값** (난이도? 슬롯? UI 메뉴 default). Stat 가 동일 baseline 이므로 캐릭터 stat 가 아닌 **시스템 메뉴/카운터 초기치** 추정.

## SD 상점 catalog

R69 SD parser 와 동일 패턴 (`[size][00][nlen][name:EUC-KR][item_id][ff][slot]`). 단 SD0/1/2 는 ITM root 직접 (DAT 하위 아님), tiered items:

- SD0: 기본스톤 1단계 → 쌍기주 8단계
- SD1: 파워젬 1단계 → 파워러젬 8단계
- SD2: 진골 1단계 → 용골 N단계

총 **101 tiered shop items** (35+39+27). 게임 내 **성장 재료 상점** 으로 해석 (강화석/포션 등 단계별 판매).

## R69 가설 정정

R69 의 "SD = 일반 상점" 추정 → 정정: SD0/1/2 는 **성장 재료 전문 상점**. ITM/DAT 의 _ITM_SD 와는 다른 위치 (ITM root) 에 존재.

## 다음 후보

1. ⭐ ITEMDROP의 item index 20-29 ↔ R75 item catalog 매핑 (item id 20..29 의 실제 이름)
2. BASIC_SM_DAT 의 [8,8,8,0] baseline 정체 (게임 메뉴 시스템 코드 분석 필요)
3. R69 의 ITM/DAT/_ITM_REPAY/_ITM_Q_REPAY/_ITM_OPTION/_ITM_CASH_RANOMBOX 등 추가 분석
4. SMAF → OGG 음성 변환 트랙

## 산출

- `tools/analysis/parse_h4_itemdrop_sm.py`
- `work/h4/converted/h4_itemdrop_sm.json`
- `docs/h4/round82-itemdrop-shop.md` (이 문서)
