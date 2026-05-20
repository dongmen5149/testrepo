# Hero4 Round 92 — Summon dialogue corpus cross-reference (R87 후속)

> R87 의 "dialogue corpus 환수 등장 빈도 cross-ref" 완료. 252 decrypted 파일 / 484KB 전수 스캔.

## TL;DR

5 환수 (베놈/헤지호그/그래비티/쇼커/세이프가드) 의 개별 이름은 **4 파일에만 한정 출현** (catalog primary + item catalog + 상점 NPC + tutorial scene). 35,752 대사 라인 main story 에는 **개별 이름 거의 부재**. 환수 시스템은 story-isolated 한 부가 시스템임을 검증.

## Keyword 출현 빈도

### 개별 환수 이름 (5종, 거의 동일 빈도)

| 환수 | hits | files |
|---|---|---|
| 베놈 | 8 | 4 (catalog/item/shop/tutorial) |
| 헤지호그 / 그래비티 / 쇼커 / 세이프가드 | 7 each | 3 (catalog/item/shop) |

→ 베놈만 `n0124_scn` tutorial scene 에 한번 더 등장 (예시 환수).

### Generic 용어

| 용어 | hits | files |
|---|---|---|
| 환수 | 147 | 35 |
| 소환수 | 130 | 33 |
| 소환사 | 9 | 3 |
| **소환술** | **0** | **0** |
| **망각 / 망각의 저주** | **1 / 1** | **1 / 1** |

- "환수"/"소환수" 광범위 사용 (35 파일)
- "소환사" class name 으로 dialogue 거의 부재 (9 hits)
- "소환술" 명시 skill 이름으로 dialogue **완전 부재**
- 보스 "망각의 저주" catalog 외 dialogue **0 hits**

## 5 환수 출현 4 파일 (source 분류)

| role | path | 5/5 환수 포함 |
|---|---|---|
| **catalog_primary** | `HDAT/_H_SS` | yes (R86-R89 핵심) |
| **item_catalog_sub** | `ITM/DAT/_ITM_15_DAT` (768B) | yes — 환수 시스템 item 형태 사본 |
| **shop_npc** | `NPC/NPCUI_GUARDIANSHOP_DAT` (1304B) | yes — "수호자 상점" 환수 획득 UI |
| **scene_dialogue** | `MAP/SC/n0124_scn` (16968B) | 1 (베놈 만 — tutorial 예시) |

### NPCUI_GUARDIANSHOP_DAT 의 의미

문자열 fragment `헤지호그의`, `그래비티의`, `세이프가드` 등이 등장 → **수호자 상점 NPC** 의 환수 구매/계약 메뉴. 환수 시스템의 **게임 내 획득 진입점**.

### n0124_scn tutorial excerpt

베놈 mention 직전 context:
> "성은 소환수가 가진 스킬로 소환수에 따라 다릅니다. <베놈은 원거리 공격, 중독 능력, 저주 강화 능력이 ..."

→ `n0124_scn` = **환수 시스템 in-game tutorial scene** (베놈 을 예시로 설명).
이로써 환수 시스템의 in-game 입문 경로 발견:
1. tutorial scene (`n0124_scn`)
2. 수호자 상점에서 획득 (`NPCUI_GUARDIANSHOP_DAT`)
3. catalog (`_H_SS`, `_ITM_15_DAT`) 로 사용

## ITM/DAT/_ITM_15_DAT 의 정체

R87 의 `_H_SS` (1624B) 와 별개로 768B 의 환수 catalog 사본. 모든 5 환수 이름 + 모든 logical skill (뇌격/맹독/되돌리기/슬로우/스턴/실드) + aura/passive 다 포함.

가설: `_H_SS` 는 **engine stat data**, `_ITM_15_DAT` 는 **inventory item 형태 wrapper** (UI 표시용).

## R87 cross-ref 결론

| R87 후속 질문 | R92 답 |
|---|---|
| 5 환수 가 dialogue 에서 어떻게 언급되나? | catalog + 상점 + tutorial scene 외 거의 없음 |
| 소환사 class 가 명시되나? | "소환사" 9 hits/3 파일 — 거의 없음 |
| 망각의 저주 보스 가 story 에 등장하나? | catalog 외 0 hits — story 노출 없음 |
| 환수 획득 entry point | NPCUI_GUARDIANSHOP_DAT (수호자 상점) |
| 환수 시스템 tutorial | n0124_scn (베놈 예시) |

R87 가설 강화: 환수 시스템은 게임 후반 / DLC-style 부가 시스템으로 story 와 약하게 통합됨.

## 산출

- `tools/converter/parse_h4_summon_dialogue_xref.py` (신규)
- `work/h4/converted/h4_summon_dialogue_xref.json` (11.3KB)
- `docs/h4/round92-summon-dialogue-xref.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **`_H_SA` group_id ↔ 5 환수 매핑 검증** (R88 후속) — 0/64/78/38/75
2. **`_H_SA` ability skill_id {12,13,15,16,18,21,22,37} 카테고리** (R88 후속)
3. **element byte[5]=2 검증** (R89 후속)
4. **Q_REPAY drop_id 의미** (R90 후속)
5. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
6. **n0124_scn tutorial 전체 분석** (R92 후속) — 환수 시스템 in-game 설명 전문
