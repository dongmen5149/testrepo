# Hero4 Round 83 — REPAY / Q_REPAY / CASH_RANOMBOX 보상 테이블

> R69 의 추가 미분석 ITM/DAT 파일 일괄 정리.

## TL;DR

ITM/DAT 의 보상 테이블 6 파일 모두 DES 복호화 + 레코드 stride 식별 완료.

| 파일 | size | record stride | record 수 | 가설 |
|---|---|---|---|---|
| `_ITM_REPAY_0` | 1232B | 14B | 88 | 일반 보상 테이블 0 |
| `_ITM_REPAY_1` | 888B | 12B | 74 | 일반 보상 테이블 1 |
| `_ITM_Q_REPAY_0` | 4000B | 20B | 200 | 메인 quest 보상 |
| `_ITM_Q_REPAY_1` | 4000B | 20B | 200 | 사이드 quest 보상 |
| `_ITM_Q_REPAY_2` | 3984B | 12B | 332 | 단발성 quest 보상 |
| `_ITM_CASH_RANOMBOX` | 368B | 16B | 23 | 캐시 박스 (랜덤박스) 보상 |

## Record 구조 (공통 prefix 발견)

**REPAY_0** (14B):
```
[size=0x09][00][0c][item_idx:1B][01 or status][00×7]
```
첫 4 records: item_idx = 0x24, 0x09, 0x0a, 0x25 — global drop item index.

**REPAY_1** (12B):
```
[size=0x06][00][0c][item_idx:1B][01 or ff×4 - empty marker][00×?]
```
빈 reward (`ff ff ff ff`) 가 중간에 끼는 record 多.

**Q_REPAY_0/1** (20B):
```
[size=0x12][00][0e][00][reward_LE32][drop_byte_array:5B][00×7]
```
첫 record: reward_LE32 = 0x00000050 = 80 (gold? EXP?). 두번째: 0x00000ce4 = 3300 — 단조 증가.

**Q_REPAY_2** (12B):
```
[size=0x12][00][0e][00][reward_LE32][drop_bytes][00×4]
```
20B 의 짧은 변형.

**CASH_RANOMBOX** (16B):
```
[size=0x0e][00][00][00][08][0f][cat:1B][slot:1B][stat:?B]
```
23 records — 캐시 박스 보상 풀.

## item_idx 의 범위 (REPAY 와 ITEMDROP cross-check)

R82 의 `_ITEMDROP` slot values 20-29 와 REPAY 의 item_idx (0x09, 0x0a, 0x24=36, 0x25=37, 0x26=38) 가 **부분 겹침** — 둘 다 **글로벌 drop item 인덱스 공간** 사용 가능성.

확정 매핑은 _ITM_OPTION (R83 부수 발견) 와 cross-ref 필요:
- `_ITM_OPTION` (1928B): "HPmax L1" ASCII + 회복/물약회복/특수공격/근접공격/원거리공격/마법공격/물리방어/마법방어/명중/회피/크리티컬/회복/흡수/소모/물약회복 등 enchantment pool. 각 enchant 의 idx 가 위 item_idx 값일 가능성.

## 산출

- 추가 복호화: `_ITM_REPAY_0/1`, `_ITM_Q_REPAY_0/1/2`, `_ITM_CASH_RANOMBOX` (6 파일, ~14KB)
- `docs/h4/round83-reward-tables.md` (이 문서)

## 다음 후보

1. ⭐ `_ITM_OPTION` 1928B entry 파싱 (HPmax L1 등 enchantment pool index → 이름 매핑)
2. REPAY/Q_REPAY 의 LE32 reward 값 분포 분석 (gold vs EXP 구분)
3. 보스 phase stat 강화율 정량 (R80 후속)
4. _ITM_EMPTY 15B 의미
