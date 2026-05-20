# Hero4 Round 90 — Q_REPAY idx ↔ R70 quest name 1:1 매핑 확정

> R85 의 "200 vs 128 차이 72" 미해결 완전 해소.

## TL;DR

| 영역 | idx 범위 | 개수 | 의미 |
|---|---|---|---|
| **Quest 1:1 매핑** | 0 - 127 | 128 | R70 의 128 quest 와 직접 매핑 |
| Repeatable mission | 128 - 198 (대부분) | 52 | 저-중 보상 슬롯 (사이드 반복 보상) |
| Mid achievement | 128 - 198 | 8 | 중간 업적 |
| Endgame achievement | 128 - 198 | 11 | endgame 대형 보상 (EXP 60k+/gold 180k+) |
| Sentinel | 199 | 1 | zero terminator |
| **합계** | 0 - 199 | **200** | — |

## 매핑 검증 (decisive)

| idx | quest_source | quest_name | EXP | gold |
|---|---|---|---|---|
| 0   | _QUEST_0_DAT | 케프네스를 찾아라 | 80 | 19,400 |
| 1   | _QUEST_0_DAT | (종속퀘) | 3,300 | 47,500 |
| 60  | _QUEST_0_DAT | 전이장치 | 41,750 | 84,700 |
| 61  | _QUEST_0_DAT | 케프네스 | 7,980 | 16,600 |
| 62  | _QUEST_1_DAT | 성지 방어1 | 7,980 | 16,600 |
| 63  | _QUEST_1_DAT | 성지 방어2 | 39,900 | 83,400 |
| 127 | _QUEST_1_DAT | (마지막 quest) | — | — |

**경계 idx 61 → 62 에서 source file 이 `_QUEST_0_DAT` → `_QUEST_1_DAT` 으로 정확히 전환**. R70 의 quest count split (62 + 66 = 128) 와 일치.

## Extra reward 영역 (idx 128-198, 71 slots)

### Endgame achievement (idx 167, 168, 169, ..., 192, 193, 196, 197, 198 — 총 11)

- EXP 60,000-88,000 / gold 180,000-198,000
- 동일 LE32 가 2-4 entries 반복 → multi-stage final mission (예: 4-phase boss)
- idx 192-193 = (67470 EXP / 181900 gold) × 2
- idx 196-197 = (67470 / 181900) × 2
- idx 198 = (88100 / 198100) = 최종 보상

### Mid achievement (idx 166, 174, 175, ..., 8 entries)
- EXP 5,000-50,000 / gold 100,000-150,000
- 중간 단계 업적 / 도전 보상

### Repeatable mission (idx 128-191 대부분, 52 entries)
- EXP 1,500-3,700 / gold 11,000-90,000
- 동일 reward 가 2 entries 반복하는 패턴 빈출 → 일일/반복 mission

### Sentinel (idx 199)
- EXP=0, gold=0 → 종료 marker

## R83/R85 갱신

| R83 가설 | R90 확정 |
|---|---|
| Q_REPAY_0/1 200 records = 200 quests | idx 0-127 만 quest, 128-198 = 71 extra reward |
| Q_REPAY_0 = EXP 분포 | 확정 (1:1 매핑으로 quest 별 EXP 추적 가능) |
| Q_REPAY_1 = gold (~11× EXP) | 확정 |

## 산출

- `tools/converter/parse_h4_quest_reward_map.py` (신규)
- `work/h4/converted/h4_quest_reward_map.json` (35KB)
- `docs/h4/round90-quest-reward-map.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **보스 phase stat 강화율 정량** (R80 후속) — 오토마톤 5 phase 비교
2. **dialogue corpus 환수 등장 빈도** (R87 후속) — 베놈/헤지호그/… × 35,752 대사
3. **`_H_SA` group_id ↔ 5 환수 매핑 검증** (R88 후속) — group 0/64/78/38/75
4. **`_H_SA` ability skill_id {12,13,15,16,18,21,22,37} 카테고리** (R88 후속)
5. **element byte[5]=2 검증** (R89 후속)
6. **Q_REPAY drop_id 의미** — 0xff 외 32 entries 가 가지는 drop_id 가 ITM 아이템 idx 인지 검증 (R90 후속)
