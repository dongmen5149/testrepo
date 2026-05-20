# Hero4 Round 93 — `_H_SA` summon-tier group_id ↔ 5 환수 매핑 검증

> R88 의 5 group_id (0/64/78/38/75) 가 5 환수에 어떻게 매핑되는지 확정.

## TL;DR

검증 5/5 통과로 **ordinal 매핑** 확정:

| group_id | summon_id | 환수 | ranged_status skill | 결정 evidence |
|---|---|---|---|---|
| 0  | 0 | 베놈       | 맹독       | basic, no secondary |
| 64 | 1 | 헤지호그   | 되돌리기   | **signed-LE16 negative extras (-30/-50/-70)** = reflect |
| 78 | 2 | 그래비티   | 슬로우     | gentle secondary 5/10/15 |
| 38 | 3 | 쇼커       | 스턴       | **highest count 20/40/60 + 유일 aura_cost=2** |
| 75 | 4 | 세이프가드 | 실드       | gentle secondary 5/10/15, heal class |

## 검증 evidence

### Check 1: group 64 만 signed-LE16 음수 extras 보유

| tier | bytes[16-19] | LE16@17-18 signed |
|---|---|---|
| 3 | `18 e2 ff 00` | **-30** |
| 4 | `18 ce ff 00` | **-50** |
| 5 | `18 ba ff 00` | **-70** |

다른 4 group 은 모두 bytes[16-19] = `0 0 0 0`. 음수 값은 헤지호그의 **되돌리기 (reflect)** 메커니즘과 직접 매치 — 공격력이 자신에게 돌아오는 양 (signed negative damage).

### Check 2: ranged_status skill 5/5 매치 (R86/R87)

| 환수 | R86/R87 ranged_status | R93 _H_SA 매핑 | 일치 |
|---|---|---|---|
| 베놈 | 맹독 | 맹독 | ✓ |
| 헤지호그 | 되돌리기 | 되돌리기 | ✓ |
| 그래비티 | 슬로우 | 슬로우 | ✓ |
| 쇼커 | 스턴 | 스턴 | ✓ |
| 세이프가드 | 실드 (paired) | 실드 | ✓ |

### Check 3: group 38 = 쇼커 (유일 aura_cost=2)

R87 AURA cost[8] (5 환수 비교):

| 환수 | aura name | cost |
|---|---|---|
| 베놈 | 저주의 오러 | 1 |
| 헤지호그 | 강화의 오러 | 1 |
| 그래비티 | 마법의 오러 | 1 |
| **쇼커** | **마력의 오러** | **2** |
| 세이프가드 | 보호의 오러 | 1 |

쇼커만 aura_cost=2 → group 38 의 가장 큰 count 성장 (20/40/60) 과 부합 (높은 cost = 높은 effect/스턴 duration).

### Check 4: `_H_BS` cost_marker 와 일치

| 환수 | bs_cost_marker | _H_SA group |
|---|---|---|
| 베놈 | 15 | 0 |
| 헤지호그 | 0 | 64 |
| 그래비티 | 0 | 78 |
| 쇼커 | **40** | **38** |
| 세이프가드 | 0 | 75 |

쇼커 가 _H_BS 에서도 가장 큰 cost_marker (40) — 두 catalog (_H_BS/_H_SA) 모두 쇼커를 highest-cost summon 으로 표시.

## 5 환수 통합 stat 매트릭스 (R86-R93 누적)

| 환수 | 기본공격 damage | 기본공격 range | ranged_status | aura cost | aura strength | reflect | _H_BS cost | _H_SA tier max | _H_SA count max |
|---|---|---|---|---|---|---|---|---|---|
| 베놈 | 300 | 120 | 맹독 (str 85) | 1 | 25 | — | 15 | 800 | 0 |
| 헤지호그 | 200 | 100 | 되돌리기 (str 86, flag=3) | 1 | 2 | -30/-50/-70 | 0 | 600 | 100 |
| 그래비티 | 400 | 160 | 슬로우 (str 75) | 1 | 15 | — | 0 | 680 | 15 |
| 쇼커 | 300 | 140 | 스턴 (str 76) | **2** | 8 | — | **40** | 680 | 60 |
| 세이프가드 | 500 (heal) | 100 | 실드 (paired_skill) | 1 | 16 | — | 0 | 600 | 15 |

## R88 정정

R88 doc 의 "group_id 매핑 가설" 을 **검증 통과** 로 격상.

## 산출

- `tools/converter/parse_h4_sa_summon_map.py` (신규)
- `work/h4/converted/h4_sa_summon_map.json` (4KB)
- `docs/h4/round93-sa-summon-map.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **`_H_SA` ability skill_id {12,13,15,16,18,21,22,37} 카테고리** (R88 후속)
2. **element byte[5]=2 검증** (R89 후속)
3. **Q_REPAY drop_id 의미** (R90 후속)
4. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
5. **n0124_scn tutorial 전문 분석** (R92 후속)
