# Hero4 Remake — 진행 상황 & 핸드오프

> 다음 세션에서 가장 먼저 읽기. 디테일은 분류별 폴더 / 파일 참조.
>
> **"영웅서기4 다음 내용 진행해줘"** 받았으면 → 먼저 [SESSION_HANDOFF.md](SESSION_HANDOFF.md), 그 다음 §🏆 R68-R75 누적.

## 🏆 Round 95 (2026-05-20) — element byte[5]=2 검증 + R89 정정 ★

> R89 의 "element field byte[5]=2" 명명 정정. 상세: [round95-active-attack-xref.md](round95-active-attack-xref.md).
>
> 전 252 decrypted 파일 scan 결과 valid ACTIVE_ATTACK signature (0x14...) 는 `_H_SS` 전용 5 hit (모두 byte[5]=2, valid speed/range/anim). 다른 파일에 11 hit 있으나 모두 false-positive (coincidental 0x14 byte + all-zero supporting fields). 즉 byte[5]=2 는 "element" 가 아닌 **summon-exclusive 'ACTIVE_ATTACK subtype marker'** (= 환수 attack 종류). PASSIVE_TEMPLATE 의 byte[5] 가 subtype 결정자 역할을 하는 것과 동일한 layer (단 ACTIVE_ATTACK 에서만 한 값(2) 만 사용).
>
> Character class skill (S000-S003) 은 별개 stat block schema 사용 — 가변 길이 body, EUC-KR description suffix 포함. R96+ 별도 분석 대상.
>
> `parse_h4_active_attack_xref.py` 신규 + `h4_active_attack_xref.json` 6.5KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 94 (2026-05-20) — _H_SA ability skill_id 카테고리 식별 (R88 후속) ★

> R88 의 24 ability slot skill_id 8 종 매핑. 상세: [round94-sa-ability-skill-map.md](round94-sa-ability-skill-map.md).
>
> Global skill_id 규칙 `skill_id = class_index × 10 + local_index` 확인 (R69 40 character skills 의 통합 ID space). 매핑 결과: S001 사격(루레인) 5 ability (동시사격/급소사격/에이밍샷/암즈트랩/암즈강화), S002 마검(티르) 2 (마검공격/텔레포트소드), S003 마법(루레인) 1 (마법강화), S000 양손검(티르) **0**. 3 bonus chain (회피증가/암즈강화/속사) 모두 S001 — 사격 class 가 self-contained skill tree. S000 base class 는 ability tier upgrade 부재.
>
> `parse_h4_sa_ability_skill_map.py` 신규 + `h4_sa_ability_skill_map.json` 9.7KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 93 (2026-05-20) — _H_SA group_id ↔ 5 환수 매핑 검증 (R88 후속) ★

> R88 의 5 group_id (0/64/78/38/75) → 5 환수 매핑 가설을 검증. 상세: [round93-sa-summon-map.md](round93-sa-summon-map.md).
>
> ordinal 매핑 확정: group 0=베놈, 64=헤지호그, 78=그래비티, 38=쇼커, 75=세이프가드. 5 verification check 모두 통과: (1) group 64 유일 signed-LE16 negative extras (-30/-50/-70) = 헤지호그 되돌리기 reflect mechanic, (2) group 38 가 non-reflect groups 중 max count 성장 (20/40/60), (3) group 38 환수가 유일 aura_cost=2 (= 쇼커 마력의 오러), (4) group 64 환수의 ranged_status = '되돌리기', (5) 5 환수 ranged_status skill 5/5 매치 (맹독/되돌리기/슬로우/스턴/실드).
>
> R86-R93 통합 stat 매트릭스 완성 — 5 환수 × 모든 stat axis (damage/range/skill/aura/reflect/cost/tier/count).
>
> `parse_h4_sa_summon_map.py` 신규 + `h4_sa_summon_map.json` 4KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 92 (2026-05-20) — Summon dialogue corpus cross-ref (R87 후속) ★

> R87 의 dialogue cross-ref 완료. 상세: [round92-summon-dialogue-xref.md](round92-summon-dialogue-xref.md).
>
> 252 decrypted 파일 / 484KB 전수 스캔. 5 환수 개별 이름은 **catalog (`_H_SS`) + item catalog (`_ITM_15_DAT`) + 상점 NPC (`NPCUI_GUARDIANSHOP_DAT`) + tutorial scene (`n0124_scn`, 베놈 예시) 4 파일** 외 거의 부재. generic "환수" 147 hits / "소환수" 130 hits 35 파일에 산재. "소환사" 9 hits 만, "소환술" 0 hits, 보스 "망각의 저주" catalog 외 0 hits.
>
> 환수 시스템 in-game 입문 경로 식별: tutorial(n0124) → 수호자 상점(NPCUI_GUARDIANSHOP_DAT) 획득 → catalog 사용. story-isolated 부가 시스템임을 검증.
>
> `parse_h4_summon_dialogue_xref.py` 신규 + `h4_summon_dialogue_xref.json` 11.3KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 91 (2026-05-20) — Multi-phase boss encounter stat scaling 정량 (R80 후속) ★

> R80 미해결 보스 phase 강화율 정량화. 상세: [round91-boss-phase-scaling.md](round91-boss-phase-scaling.md).
>
> 4 ESDAT outlier (좀비 213B / 소환된 좀비 140B / 오토마톤 432B / 기갑병 140B) phase 별 stat 추출. 표준 보스 (좀비/오토마톤) 의 phase 0 → final 강화율 **HP +17-27%, ATK +9-33%, DEF +12-24%, gold 1.30× (정확), EXP 1.25× (정확)** — gold/EXP 두 보스가 정확히 동일 ratio → 공식 기반 scaling. 오토마톤 5-phase 는 phase 1 dip (취약 cinematic, EXP=0) → 회복 → enemy_class 13→26→47 진화 → 최종 enraged. 6B inter-phase link (R80) 재검증 통과. 소환된 좀비는 역방향 (phase 0=peak, final=defeat). 기갑병은 R80 의 marker 부재 anomaly 확인.
>
> `parse_h4_boss_phases.py` 신규 + `h4_boss_phases.json` 13.8KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 90 (2026-05-20) — Q_REPAY idx ↔ quest 1:1 매핑 확정 (R85 미해결 해소) ★

> R85 의 "200 vs 128 차이 72" 미해결 해소. 상세: [round90-quest-reward-map.md](round90-quest-reward-map.md).
>
> Q_REPAY_0/1 idx 0-127 이 R70 의 128 quest 와 직접 1:1 매핑 확인 (idx 0='케프네스를 찾아라', 경계 idx 61→62 에서 `_QUEST_0_DAT`→`_QUEST_1_DAT` 정확 전환). idx 128-198 = 71 extra reward slots: 52 repeatable mission + 8 mid achievement + 11 endgame achievement (idx 192-198 의 EXP 67k-88k / gold 180k+ multi-stage 보상). idx 199 = zero sentinel.
>
> `parse_h4_quest_reward_map.py` 신규 + `h4_quest_reward_map.json` 35KB + catalog 통합 + Android 자산 배포.

---

## 🏆 Round 89 (2026-05-20) — 23B stat block 통합 schema (R87 정정) ★

> R87 의 stat block field 표 전수 정정. 상세: [round89-statblock-schema.md](round89-statblock-schema.md).
>
> 21 개 23B block (boss + summon active 11 + global passive 4 + divider 1) 통합 분석. `byte[0]` = template marker (3종: 0x14 ACTIVE_ATTACK / 0x0a DIVIDER / 0x00 PASSIVE_TEMPLATE), PASSIVE_TEMPLATE 의 `byte[5]` = subtype (4종: 6 SHIELD / 7 STATUS_PROC / 11 AURA / 12 PASSIVE).
>
> R87 정정: damage 가 byte[3] 단일 (44/200/144/44/244) 이 아닌 byte[3-4] LE16 (300/200/400/300/500). element=2, heal_flag/reflect_flag/secondary buff 등 모든 field 의미 확정. `parse_h4_statblock_schema.py` 신규 + `h4_statblock_schema.json` 17.5KB + catalog 통합.

---

## 🏆 Round 88 (2026-05-20) — `_H_BS` + `_H_SA` 환수 progression / ability slot 정밀화 ★

> R86 동반 파일 두 개 정밀화. 상세: [round88-summon-progression.md](round88-summon-progression.md).
>
> R86 stride 가설 정정: `_H_BS` = **5 환수 × 27B + 1B 패딩** (이전 "17×8B" 폐기), `_H_SA` = **40 records × 24B** (1 헤더 + 24 ability slot + 15 summon-tier; 이전 "24×40B" 폐기).
>
> `_H_BS`: 환수당 5 stat (HP/SP/ATK/DEF/MAG?) + sequential learn skill IDs 6-20 (5 환수 × 3 skill). `_H_SA`: 8 unique ability skill_id {12,13,15,16,18,21,22,37} × 3 tier (총 24) + 5 summon-group × 3 growth tier (총 15, `value_le16 = tier × 10` 불변량 확인). `parse_h4_summon_progression.py` 신규 + `h4_summon_progression.json` 12.5KB + catalog 통합.

---

## 🏆 Round 87 (2026-05-19) — `_H_SS` 환수 시스템 stat block 정밀화 ★

> R86 후속 정밀화 라운드. 상세: [round87-summon-stat-detail.md](round87-summon-stat-detail.md).
>
> `_H_SS` 전체 layout 6 section 분해. **5 환수 × 5 logical skills (raw 7 entries 매핑)** + 4 global passive (**skill_id 91-94**) + 1 boss-tier "망각의 저주". 23B stat block field 5종 의미 식별 (type/damage/element/strength/animation).
>
> Active skill type catalog 초안: 0x14=basic_attack, 0x07=status proc, 0x0c=passive. 되돌리기 reflect flag 위치도 확정. `parse_h4_summon_system.py` 신규 + `h4_summon_system.json` 26KB. catalog 74.9KB 로 업데이트.

---

## 🏆 Round 86 (2026-05-19) — `_H_SS` 환수(소환수) 시스템 발견

> 신규 게임 시스템 발견. 상세: [round86-summon-system.md](round86-summon-system.md).
>
> `_H_SS` 1624B = **5+ 환수 catalog** (베놈/헤지호그/그래비티/쇼커/세이프가드). 각 환수 5 스킬 (기본공격/원거리/효과/오러/소환시) + 4 글로벌 강화 (마법력/교감도/체력/정신). R69 의 4 character class 스킬과 별개 시스템.
>
> R76/R81 의 캐릭터 모델 보강: 2 영웅 × 2 mode + **소환수 시스템** = ARPG + summon hybrid. S003 의 "환수흡수" 스킬이 직접 연결고리.

---

## 🏆 Round 85 (2026-05-19) — Quest reward LE32 분포 (EXP vs gold)

> 상세: [round85-quest-reward-distribution.md](round85-quest-reward-distribution.md).
>
> Q_REPAY_0/1 같은 200 records 인데 LE32 median 3700 vs 41700 (~11배) → **Q_REPAY_0 = EXP 보상, Q_REPAY_1 = gold 보상**. 200 - 128 (R70 quest) = 72 차이 = achievement/multi-stage reward 가설.

---

## 🏆 Round 84 (2026-05-19) — `_ITM_OPTION` enchantment pool 51종

> 상세: [round84-enchantment-pool.md](round84-enchantment-pool.md).
>
> 1928B = **120 entries / 51 unique enchantments / L1-L4 진행**. HP/SP 계열, 공격/방어, proc 발동 (화염/결빙/스턴/슬로우/넉백), 상태이상 저항, 시스템 (쿨타임/레벨제한), 클래스 보완 (양손검 보완 = 티르 mode 0, 사격/마법 보완 = 루레인 mode 0) → R81 다중 mode 가설 강화.

---

## 🏆 Round 83 (2026-05-19) — REPAY / Q_REPAY / CASH 보상 테이블

> ITM/DAT 의 보상 테이블 6 파일 일괄 복호화 + stride 식별. 상세: [round83-reward-tables.md](round83-reward-tables.md).
>
> REPAY_0=14B×88, REPAY_1=12B×74, Q_REPAY_0/1=20B×200, Q_REPAY_2=12B×332, CASH_RANOMBOX=16B×23. 부수 발견: `_ITM_OPTION` 1928B = enchantment pool (HPmax/회복/공격/방어/명중/회피/크리티컬 등 15+ 종).

---

## 🏆 Round 82 (2026-05-19) — 트랙 C: ITEMDROP + BASIC_SM + SD 상점

> 상세: [round82-itemdrop-shop.md](round82-itemdrop-shop.md).
>
> ITM root 의 3종 보조 파일 모두 plaintext. `_ITEMDROP` = 9 records × 8B (slot[0..5] drop table), `BASIC_SM_DAT` = 5 records × 44B (모두 [8,8,8,0] baseline 시스템 프로필), `_ITM_SD0/1/2` = 101 tiered shop items (성장 재료 전문 상점).

---

## 🏆 Round 81 (2026-05-19) — `_H_BH` 4 stat block 정체 + R76 미해결 해소

> R71 의 "4 hero stat blocks" 해석 정정. 상세: [round81-hero-bh-resolved.md](round81-hero-bh-resolved.md).
>
> **4 entries = 2 영웅 × 2 mode** (4명 아님). byte[3] = hero_id (티르=0, 루레인=1). entry 0/1 = 티르 mode 0/1 (S000 양손검 / S002 마검), entry 2/3 = 루레인 mode 0/1.
>
> R76 의 `_ITM_03` 사용자 미스터리 해소: 루레인이 사격 (`_ITM_04..06`) + 검 (`_ITM_03`) 다중 mode 가능성. heroes.list[0] note "_H_S000 / _H_S002 (variants)" 와 일치.

---

## 🏆 Round 80 (2026-05-19) — ESDAT 73B phase 6B link 구조

> R79 정밀화. 상세: [round80-esdat-phase-link.md](round80-esdat-phase-link.md).
>
> Outlier layout 확정: `encounter = N × 73B phase + 67B final-phase`. 6B link = `[0x47][0x00][LE16 phase_id][LE16 transition_marker]`. transition = `bf fa` continue / `b1 bc` final. 오토마톤 phase ID sequential (654→658) = encounter chain.

---

## 🏆 Round 79 (2026-05-19) — ESDAT outlier (multi-phase boss) 구조

> 5 outlier ESDAT entries (72B/140B/213B/432B) 분석. 상세: [round79-esdat-outliers.md](round79-esdat-outliers.md).
>
> 핵심: `0xff 0x3f` marker 가 **정확히 73B 간격** 으로 반복 (42, 115, 188, 261). multi-phase boss encounters.
>
> 73B/phase = 67B 정형 인카운터 (R78) + 6B inter-phase link. 같은 적 (오토마톤/좀비/기갑병) 이 67B 일반 + outlier 보스 dual-mode 보유.

---

## 🏆 Round 78 (2026-05-19) — ESDAT 67B encounter layout + R76 가설 정정

> 3 ESDAT = 157 일반 적의 난이도 3 stage. 67B body (152/157 = 97%) 분석. 상세: [round78-esdat-encounter-layout.md](round78-esdat-encounter-layout.md).
>
> **R76 의 "0x3f opcode 274회" 정정**: opcode 가 아니라 **section boundary marker** (0xff 0x3f at pos[42-43], 125/150 entries). ESDAT 도 BSDAT 와 동일 부류의 stat block, script bytecode 아님.
>
> 67B layout: pos[0]=enemy class, pos[2-3]=EXP base, pos[23-25]=HP, pos[29-32]=stat pair, pos[35-40]=ATK/DEF, pos[44-55]=drop, pos[57-60]=gold/EXP reward.

---

## 🏆 Round 77 (2026-05-19) — BSDAT 49B stat field mapping

> 49B 보스 body (13 entries × 3 stages) stat layout 추정. 상세: [round77-bsdat-stat-fields.md](round77-bsdat-stat-fields.md).
>
> 핵심: pos[4]=level_req, pos[17-18]=EXP, pos[29-30]=MP_max, **pos[31-34]=HP max/current 페어**, pos[35-38]=DEF 페어, pos[40-41]=gold reward (×4.5 stage scaling).

---

## 🏆 Round 76 (2026-05-19) — Weapon class 매핑 + BSDAT stat block 확정

### Track A: Weapon class × Character class 매핑

> R75 의 7 weapon classes 와 R69 의 4 character classes 매핑 완료. 상세: [round76-weapon-class-mapping.md](round76-weapon-class-mapping.md).
>
> 핵심: dual-ATK 4종 (`_ITM_00..03`) = 검류 (S000/S002/S003 + 잉여 1), single-ATK 3종 (`_ITM_04..06`) = S001 사격 sub-types. `_ITM_01` (avg dmg 65.0) = **티르 양손검**, `_ITM_04..06` = **루레인 권총/저화력총/중화기**.
>
> 남은 미해결: `_ITM_03` 사용자 (4번째 영웅 또는 NPC class), `_H_BH` 4번째 stat block 캐릭터.

### Track B: BSDAT body = boss stat block 확정

> R72 가설 정정. 상세: [round76-track-b-bsdat-stat-block.md](round76-track-b-bsdat-stat-block.md).
>
> 3 `_BSDAT_{0,1,2}` = **같은 88 boss 의 난이도/단계 3 버전**. 같은 보스 이름이 동일 body 길이로 등장 (루칸=105B, 브리안=49B). LE16 overflow 패턴 (82/317/797) = HP-like 지수 증가. SCN bytecode 가 아님 (op_0x01 reference 0회). ESDAT 는 별개 (`0x3f` opcode 빈도 + ff separator 1.7/entry → script-like).

---

## 🏆 Round 68 - 75 (2026-05-18/19) — Hero4 자동 데이터 분석 8 라운드 종결

> **상태**: ⚡ **Hero4 자동 영역 ~95% 종결**. 407 파일 복호화 + 40 skills + 128 quests + 559 event scripts + 349 items (148 descriptions + 129 weapon stats) + 4 hero stat block.
>
> 라운드별 상세: [round68-des-key-discovered.md](round68-des-key-discovered.md) · [round69-skill-catalog-and-batch-decrypt.md](round69-skill-catalog-and-batch-decrypt.md) · **[round70-75-summary.md](round70-75-summary.md)** ★

### R70-R75 한눈에 (2026-05-19)

| R | 작업 | 결과 |
|---|---|---|
| **R70** | NPC QUEST 정밀 파싱 (`commit 03e6eee8`) | **128 quests** (메인 62 + 사이드 66) |
| **R71** | _H_BH hero stat block 구조 (`commit 9a21481f`) | 4 entries 가변 길이 + mode/index 구조 |
| **R72** | E/BSDAT + ESDAT (`commit 54e14071`) | **559 entries** (boss 88 + encounter 471) |
| **R73** | ITM/DAT entry struct (`commit d5241a1e`) | **349 items** (price + slot + tier) |
| **R74** | item stat_block field mapping (`commit 84ec6b66`) | **148 descriptions** (HP/lvl/레시피/효과) |
| **R75** | weapon stat field (`commit c626cde2`) | **129 weapons** (lvl 1→91, ATK1/ATK2) |

**Round 76 즉시 시작** — [SESSION_HANDOFF.md](SESSION_HANDOFF.md) 의 트랙 A-F 참조.

---

## 🏆 Round 68+69 (2026-05-18/19) — DES + 게임 데이터 100% 추출

> **상태**: ⚡ **Hero4 모든 DES 자원 (407 파일) 복호화 완료** + **4 캐릭터 × 10 스킬 catalog 완성**. R69 = R68 추가 49 파일 + entry layout 분석. 자세한 사항 [`round68-des-key-discovered.md`](round68-des-key-discovered.md) + [`round69-skill-catalog-and-batch-decrypt.md`](round69-skill-catalog-and-batch-decrypt.md).

**Round 68 (DES 해제)**:
- DES key = `J@IWO8N7` (binary 0x86edc 의 `J@IWO8N7L0E7E` 첫 8 byte)
- Cipher = Hero5 `tools/h5_des.py` mx_des_decrypt 변종 (S1[58]=2 + swap+reversed subkey)
- 발견 경로: Hero3 R57 + Hero5 h5_des.py cross-game 분석 (Ghidra 없이)
- 복호화: SCN 350 + HDAT-A 8 = 358 파일
- dialogue corpus 4,078 garbage → **35,752 entries (15,127 unique)**

**Round 69 (게임 데이터 완성)**:
- 추가 49 파일 (E/BSDAT/ESDAT, ITM/DAT 26, NPC 7, FR 3, HDAT 7) 일괄 복호화 100% 성공
- Hero4 캐릭터: **티르 (양손검)**, **루레인 (사격/총)** + 2 추가 클래스
- **40 스킬 catalog** (4 클래스 × 10 스킬 정확 매트릭스)
- 1,572 아이템 한국어 + 2,427 quest/UI 한국어 entries
- 통합 `work/h4/converted/h4_catalog.json` 생성 (Android single source of truth)

**누적 407 파일 복호화 = Hero4 전체 DES 자원**.

**Round 70 추천 작업** (다음 세션):
1. ⭐ **A1 영어 번역** (Claude Haiku, ~$0.30) — corpus + catalog 모두 한국어 진본화 완료
2. NPC QUEST_0/1_DAT 정밀 파싱 (Hero3 quest_*_dat 동일 패턴 가능)
3. HDAT-A _H_BH 40B stat block 정밀 (level/HP/SP/ATK/DEF/...)
4. E/BSDAT, E/ESDAT 6 파일 SCN-like script 분석 (boss/event dialogue)
5. Phase C (Hero3 KMM 분리) — Hero4 모든 자산 준비 완료, engine wiring 만 남음

---

## ⚡ 다음 세션 — 시작 전 30초 체크

> **최신 상태 (2026-05-18 Round 68) — 🏁 DES 자동 차단 해제**: 누적 **48 건 진전**. SCN+HDAT-A 358 파일 복호화, corpus 35,752 entries. 차단 해제 작업 (E/ITM/NPC 추가 복호화, HDAT-A 파싱, 영어 번역) 모두 Round 69 에서 자동 가능.

### ⚡⚡ 다음 세션 첫 행동 — "영웅서기4 다음 내용 진행해줘" 즉시 응답 가이드

**사용자가 가장 먼저 가져올 것**: Ghidra GUI 에서 발굴한 **DES key 8 bytes** (16 hex chars 또는 8 ASCII bytes)

**즉시 실행 (사용자가 키를 주면 바로 copy-paste)**:
```bash
cd d:/testrepo

# 0. 1초 검증 — 9 known-ciphertext sentinel 중 가장 흔한 3개로 빠르게 확인
KEY_HEX="<KEY_16HEX_HERE>"   # 또는 KEY_HEX="$(printf '%s' '<8ASCII>' | xxd -p)"
python -c "
from Crypto.Cipher import DES
k = bytes.fromhex('$KEY_HEX')
c = DES.new(k, DES.MODE_ECB)
# SCN/HDAT-A 가장 흔한 last block (38회 + 92회 = 130회 반복)
p1 = c.decrypt(bytes.fromhex('3b7af9a427907dac'))
# SCN 가장 흔한 first block (8회 — signature 검증)
p2 = c.decrypt(bytes.fromhex('4655b8f39c0fe0b2'))
# BSDAT 첫 블록 (3 파일 공유)
p3 = c.decrypt(bytes.fromhex('d6c1b1be38099f0e'))
print('sent:', p1.hex(), '  (00*8 / ff*8 / SCN sig 매칭 시 OK)')
print('frst:', p2.hex(), '  (01 ?? 01 53 00 01 ?? ?? 매칭 시 OK)')
print('bsdt:', p3.hex(), '  (signature 또는 low-entropy 매칭 시 OK)')
sig_ok = p2[0]==0x01 and p2[2]==0x01 and p2[3]==0x53 and p2[4]==0x00 and p2[5]==0x01
print('KEY VALID:', sig_ok)
"
# 검증 OK 면 다음 단계로
```

**키 OK 확정 시 자동 파이프라인 (~30분)**:
```bash
# 1. SCN 348 + HDAT-A 8 일괄 복호화
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" --batch

# 1b. HDAT Group A 8 파일도 같은 키로 복호화
for f in _H_BH _H_BS _H_SA _H_SS _H_S000 _H_S001 _H_S002 _H_S003; do
    python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" \
        work/h4/extracted/HDAT/$f work/h4/decrypted/HDAT/$f
done

# 1c. ITM/DAT 16 + E/BSDAT/ESDAT 6 + NPC scripts ~7 + FR ~5 도 같은 키 (107 confirmed + 141 likely = ~400 파일)
# (decrypt_h4_scn.py 가 단일 파일도 처리, 디렉토리 일괄 batch 옵션 활용)
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" \
    --input_dir work/h4/extracted/E --output_dir work/h4/decrypted/E
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key "$KEY_HEX" \
    --input_dir work/h4/extracted/ITM/DAT --output_dir work/h4/decrypted/ITM/DAT

# 2. 단일 파일 1차 검증 — EUC-KR 한글이 보이면 성공
xxd work/h4/decrypted/SC/e0001_scn | head -10

# 3. decrypted SC 를 extracted 로 백업-치환 (convert_all.py 가 extracted 만 봄)
cp -r work/h4/extracted/MAP/SC work/h4/extracted/MAP/SC.encrypted_backup
cp work/h4/decrypted/SC/* work/h4/extracted/MAP/SC/

# 4. corpus 재생성 + Android assets 재배포
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/converter/prepare_android_assets.py \
    work/h4/converted apps/hero4-android/app/src/main/assets

# 5. A1 영어 번역 (~30분, ~$0.30, Claude Haiku)
export ANTHROPIC_API_KEY="..."
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

### 🎯 4-way 진입 셀렉터 (사용자 메시지 따라 분기)

```
□ 1. 사용자가 DES key 8-byte 후보 제시?
    YES → 위 ⚡⚡ 자동 파이프라인 즉시 실행 (~30분)
    NO  → ↓

□ 2. 사용자가 Ghidra GUI 작업 중 / 부분 결과 보고?
    YES → [`ghidra-guide.md`](ghidra-guide.md) §5.1 + 추적 string 3개 안내
          (`/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1)
    NO  → ↓

□ 3. 사용자가 Phase C 시작 결정 (KMM 분리)?
    YES → `git tag v0.1-pre-kmm` + Hero3 commonMain 분리 시작
          docs/h3/PROGRESS.md 참조 + Hero4 자동 inherit 검증
    NO  → ↓

□ 4. 사용자가 Hero3/Hero5 트랙 전환?
    YES → 해당 PROGRESS.md 가이드
    NO  → ↓

□ 5. 자동 분석 잔여 없음 — 사용자 결정 대기
    → "Ghidra 작업 결과 대기 중. 다른 결정 알려주세요" 응답
```

### 47개 자동 진전 요약 (2026-05-18 세션 누적 — 🏁 진짜 종결)

| # | 발견 | 도구/문서 |
|---|---|---|
| 1 | plaintext SCN 2개 (e0184/e0185) | misaligned outlier 정밀 분석 |
| 2 | e0185 글로벌 entity catalog (87 strings) | `work/h4/converted/e0185_name_table.json` |
| 3 | `CHARACTERS_H4` 사전 prefill (52 entries) | [translation_dict.py](../../tools/i18n/translation_dict.py) |
| 4 | SCN known-plaintext signature `01 ?? 01 53 00 01 ?? ??` | 5 byte fixed = 40 known bits |
| 5 | `_DAT_DES` S1[58] 1-byte 변형 (`std=3 → got=2`) | [verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py) |
| 6 | Custom DES 구현 (pure Python) | [custom_des_h4.py](../../tools/converter/custom_des_h4.py) |
| 7 | DES brute-force v3 (Hero4 signature) | [find_h4_des_key_v3.py](../../tools/recon/find_h4_des_key_v3.py) — 0 hit |
| 8 | DES brute-force v4 (custom DES, 513k cand) | [find_h4_des_key_v4.py](../../tools/recon/find_h4_des_key_v4.py) — 0 hit |
| 9 | `_PAL` secondary RGB 통계 (alpha 가설 기각) | [analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py) |
| 10 | `_EXD` box layout (count=1 subtype 2/3 풀림) | [parse_h4_exd.py](../../tools/converter/parse_h4_exd.py) |
| 11 | `_MAP_M_` extras multi-section (4-8 sections × 8B records) | [parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py) |
| 12 | SCN second-block crib `f7740f758b9a6ae4` (×17) | known-ciphertext 추가 |
| 13 | HDAT Group B (P000-P005) layout 풀림 | [parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py) |
| 14 | e0184 SCN bytecode 구조 추론 | [scn.md](formats/scn.md) |
| 15 | **HDAT Group A 8 파일 = SCN 동일 DES 키** | sentinel 92회 cross-ref |
| 16 | HDAT Group D (PDAT/SG) + OBJ 그룹 분포 | [hdat.md §Group D](formats/hdat.md), [bm-tile-obj.md §OBJ 분포](formats/bm-tile-obj.md) |
| 17 | **_MAP_M_ extras sub[2] = global OBJ id** | [analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py), 16,358 rec 0 OOB |
| 18 | **plaintext SCN disassembler + name_table 추출** | [disasm_h4_scn.py](../../tools/converter/disasm_h4_scn.py), 80 entries |
| 19 | **_MAP_M_ sec[4+] = event block header** | 77/97 maps `[count][00 01][type]` 매칭 |
| 20 | **e0185 op_0x01 = 9-byte fixed schema** | 462 refs, REFERENCE_ENTITY opcode 추정 |
| 21 | OBJ id 매핑 정정 (filename = global id 그대로) | [analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py) 수정 |
| 22 | **CIF 117 = Hero3 parser 100% 호환** | [parse_h4_cif.py](../../tools/converter/parse_h4_cif.py), 117/117 ok |
| 23 | **CIF stride hero=41B / enemy=4B Hero3 동일** | 113/117 enemy + 4/4 hero fit |
| 24 | **CIF↔EXD 117/117 페어링** | `work/h4/converted/cif_exd_xref.json` |
| 25 | **DES file pool 356→~400** (E/ITM/NPC/FR 추가) | [scan_h4_des_files.py](../../tools/recon/scan_h4_des_files.py), 107 confirmed + 141 likely |
| 26 | **Hero4 CIF 117 animation 완전 디코드** | [decode_h4_cif_frames.py](../../tools/converter/decode_h4_cif_frames.py), 0 errors |
| 27 | **EGDAT 167 enemies 100% 파싱** | [parse_h4_npc_data.py](../../tools/converter/parse_h4_npc_data.py), HP/atk/def/stats |
| 28 | NPCG_DAT 60 records + variant | 39 unique NPC IDs |
| 29 | FT/ HNF 폰트 + E/ AI scripts 43 분류 | English/Korean bitmap fonts + AI bytecode |
| 30 | **CIF id ↔ e0185 catalog 직접 매핑** | 80/117 한국어 이름 (브레스/브리안/앨리스 등) |
| 31 | **EGDAT 59 enemy types × variants** | `work/h4/converted/egdat_enemy_types.json` |
| 32 | **_FT_HANINFO = 2350 KS X 1001 한글 lookup** | EUC-KR code → glyph slot, 즉시 텍스트 렌더링 가능 |
| 33 | **ITM SD0/SD1 = 147 아이템 한국어 이름** | 소마주/백색마도/파워러젬 등 |
| 34 | **GMenu/NPCUI = 169 UI 한국어 텍스트** | 메뉴/스탯/장비/12 orbs/시스템 메시지 |
| 35 | _EVENT_POP_TXT 11 이벤트 라벨 | 획득! / 스탯포인트 + / 스킬오픈 등 |
| 36 | AI script 43 files 통계 (byte 0=0x01, 0x64=END marker) | script dispatch 의미는 Ghidra 후 |
| 37 | **_NPCG_DAT byte 2 = CIF id 직접 매핑** | 39 NPC IDs ↔ CIF 1:1 |
| 38 | ITM/_ITEMDROP = 9 drop tier × 6 slots | zone progressive drop pool |
| 39 | **BSDAT 8B + ESDAT 16B 공유 cipher prefix** | DES key validation 핵심 known-ciphertext |
| 40 | AI byte 1 = script length/complexity | enemy class 아님 (2/43 매칭) |
| 41 | NPCG_DAT_ = NPCG_DAT subset (29 ⊂ 39) | tutorial mode 추정 |
| 42 | 자산 변환 커버리지 495 PNG + JSON 완전 확인 | Hero3 디코더 100% 호환 |
| 43 | **H4/000-007 368 _HIMG → 3,372 PNG** | [batch_h4_himg.py](../../tools/converter/batch_h4_himg.py), 0 errors |
| 44 | tdf/TITLE_BM 290×199 메인 타이틀 디코드 | 단일 frame BM 0x0c |
| 45 | l/_LOGO 6-frame 로고 애니메이션 디코드 | 30×9~86×98 progression |
| 46 | tdf/ 107 한국어 entries 추출 (매뉴얼/팁/메뉴) | 회사명 한라트로드 어모바일 확인 |
| 47 | _HIMG ↔ CIF/OBJ 매핑 가설 + 3,874 PNG 배포 | 자산 7.8배 증가 |

### 핸드오프 Q&A (다음 세션 빠른 응답)

| 질문 | 답 위치 |
|---|---|
| **"영웅서기4 다음 내용 진행해줘"** | 위 §⚡⚡ + §🎯 4-way 셀렉터 → 시나리오 1-4 |
| **사용자가 DES key 8 bytes 가져오면?** | 위 §⚡⚡ 의 자동 파이프라인 즉시 실행 (~30분) |
| **DES key 검증 방법** | SCN first block decrypt = `01 ?? 01 53 00 01 ?? ??` 매칭 (40 known bits) |
| **DES key 발견 시 한번에 복호화되는 파일** | **~400 파일** (SCN 348 + HDAT-A 8 + ITM/DAT 16 + E/BSDAT/ESDAT 6 + NPC ~7 + FR ~5) |
| **지금 1순위 차단 이슈** | DES key 8 bytes (Phase B Ghidra 필수) — §🚨 핵심 차단 |
| Ghidra GUI 분석 가이드 | [`ghidra-guide.md`](ghidra-guide.md) §5.1 + 추적 string 3개 |
| **DES key 추적 string (Ghidra 용)** | `/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1 |
| **자동 brute-force 진행 결과** | v1/v2/v3/v4 모두 0 hit. 키는 binary literal 아님 확정 — 다시 시도 X |
| 자산 포맷 분석 디테일 | [`formats/`](formats/) (7 문서: pal/map/exd/bm-tile-obj/hdat/scn/cif) |
| **work/ gitignore 대응 (JSON 재생성)** | `python tools/converter/{parse_h4_map_extras,parse_h4_exd,parse_h4_cif,decode_h4_cif_frames,parse_h4_npc_data,batch_h4_himg}.py` |
| **추출 산출물 위치** | `work/h4/converted/` (JSON/TXT) + `apps/hero4-android/app/src/main/assets/` (3,874 PNG + JSON) |
| **번역 사전 H4 entry 수** | CHARACTERS_H4=52, PLACES_H4=12 + e0185 catalog 80 + 추가 ITM 147 + UI 169 + tdf 107 |
| Phase C/D 시작 시 안내 | `git tag v0.1-pre-kmm` → Hero3 commonMain 분리 → Hero4 자동 inherit (CIF/BM/_TXT 호환 검증됨) |
| 프로젝트 전체 (Hero3/5 포함) 컨텍스트 | [`../../Readme.md`](../../Readme.md), [`../h3/PROGRESS.md`](../h3/PROGRESS.md), [`../h5/PROGRESS.md`](../h5/PROGRESS.md) |

---

## ✅ 핵심 차단 해제 — DES key 발견 (Round 68, 2026-05-18)

**Hero4 DES key = `J@IWO8N7`** (8-byte ASCII = `4a 40 49 57 4f 38 4e 37`)
**Cipher = Hero5 `mx_des_decrypt`** (`tools/h5_des.py`) — startDes(mode=0) + reversed subkey + S1[58]=2

발견 경로: Hero3 R57 (`0EP@KO91` + binary 0xac594 위치 패턴) + Hero5 h5_des.py 변종 cross-game 분석. v1-v4 가 cipher 변종을 부분만 모델링 (S1 1 byte) 해서 실패했으나, Hero5 의 풀 변종 (swap + reversed subkey + S1 mod) 적용 즉시 발견. 자세한 R68 분석 [`round68-des-key-discovered.md`](round68-des-key-discovered.md) 참조.

### 즉시 명령 (재현)

```bash
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key 'J@IWO8N7' --batch
# → SCN 350 + HDAT-A 8 = 358 파일 일괄 복호화 (~5초)

cp work/h4/extracted/MAP/SC/e0184_scn work/h4/decrypted/SC/   # plaintext 복원
cp work/h4/extracted/MAP/SC/e0185_scn work/h4/decrypted/SC/
cp work/h4/decrypted/SC/* work/h4/extracted/MAP/SC/

HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/converter/prepare_android_assets.py work/h4/converted apps/hero4-android/app/src/main/assets

# 영어 번역 (Round 69 가능):
export ANTHROPIC_API_KEY=...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

### 잔여 작업 (Round 69)

- E/BSDAT 3 + E/ESDAT 3 + ITM/DAT 16 + NPC ~7 + FR ~5 ≈ 30+ 파일은 같은 키로 추가 복호화 가능 (cipher prefix sentinel 공유 확인됨)
- HDAT-A 8 파일 entry layout 분석 (decrypt 완료, parser 작성 필요)

---

## 🚨 (HISTORY) Round 67 까지 핵심 차단 — DES key

> Round 68 에서 해제됨. 다음 문단은 히스토리 참조용. 

Hero4 SCN 348개 (350 중 2개는 plaintext) = **DES ECB 로 암호화** (2026-05-14 100% 확정). 단, **2026-05-18 추가 발견**: `_DAT_DES` 의 S1[58] 1 byte 가 표준 DES 와 다름 (`std=3 → got=2`). 의도적 변형이라면 표준 `Crypto.Cipher.DES` 로는 영원히 풀리지 않고, Ghidra 키 발견 후에도 **custom DES 구현** ([tools/converter/custom_des_h4.py](../../tools/converter/custom_des_h4.py)) 사용 필수. 자동 brute-force 완전 한계 → Ghidra GUI 작업 필수. **Round 68 에서 Ghidra 없이 Hero5 cross-game 분석으로 해결**.

**바로 시작 명령**:
```bash
# 1. Ghidra 락 해제 (열려있으면 먼저 종료)
rm work/h3/ghidra_proj/*.lock work/h3/ghidra_proj/*.lock~ 2>/dev/null

# 2. Hero4 Ghidra 프로젝트 생성
#    File > New Project > work/h4/ghidra_proj/Hero4
#    File > Import > work/h4/extracted/client.bin387872
#    Language: ARM:LE:32:Cortex (gcc)

# 3. 우선 추적 string xref:
#    "/DAT/_DAT_DES" @ 0x86ecc → 사용 함수 = SCN decrypt 진입점
#    그 함수 호출자에서 8-byte literal 또는 키 파생 input 추출
#    🔍 **추가 단서 (2026-05-14)**: `_DAT_DES` 바로 다음 (0x86edc) 에
#       의문의 13-char ASCII 문자열 `J@IWO8N7L0E7E\x00` 존재.
#       label / 스크램블 키 / 별도 자원 명일 가능성. 이 string 의 xref 도 같이 확인.

# 4. 키 발견 후 즉시 (자동 — Claude 가 처리 가능):
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key <KEY_HEX_OR_ASCII> --batch
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py   # corpus 재생성
HERO_GAME=h4 python tools/i18n/translate_dialogues.py          # A1 번역
```

**DES key 빠른 검증용 known-ciphertext 9개** (2026-05-18 후속10 보강):

```python
from Crypto.Cipher import DES
key = bytes.fromhex('<KEY>')
c = DES.new(key, DES.MODE_ECB)

# SCN/HDAT-A 빈도 sentinel (last/first cipher blocks)
c.decrypt(bytes.fromhex('3b7af9a427907dac'))   # SCN last × 38 + HDAT-A × 92
c.decrypt(bytes.fromhex('1b7559e5bcf49488'))   # SCN last × 13
c.decrypt(bytes.fromhex('ef9c94a1d8247276'))   # SCN last × 12
c.decrypt(bytes.fromhex('c0f2daf72c2210e1'))   # SCN last × 11
c.decrypt(bytes.fromhex('4655b8f39c0fe0b2'))   # SCN first × 8
c.decrypt(bytes.fromhex('38d18f6ac1c49c07'))   # SCN first × 7
c.decrypt(bytes.fromhex('f7740f758b9a6ae4'))   # SCN second × 17

# BSDAT/ESDAT 공유 prefix (Boss/Event script 헤더 추정)
c.decrypt(bytes.fromhex('d6c1b1be38099f0e'))   # BSDAT_0/1/2 첫 block
c.decrypt(bytes.fromhex('8d6507ea29d02ca9'))   # ESDAT_0/1/2 첫 block
c.decrypt(bytes.fromhex('7bdfaeacc9e1755a'))   # ESDAT_0/1/2 두번째 block

# 모두 low-entropy plaintext (00*8, ff*8) 또는 SCN signature `01 ?? 01 53 00 01 ?? ??` 매치 시 키 정답
```

근거 자료 (이미 자동 정찰로 확립):
- [tools/recon/diagnose_h4_scn_cipher.py](../../tools/recon/diagnose_h4_scn_cipher.py): SCN 350개 — 99% 8-byte aligned, 엔트로피 7.9962, 첫 cipher block 22% sharing → ECB DES 강력 시사
- [work/h4/extracted/DAT/_DAT_DES](../../work/h4/extracted/DAT/_DAT_DES) (824 bytes) = 표준 DES 테이블 (PC-1, E-box, P-box, S1) 1:1 매칭 검증 완료. 추가 검증: 마지막 64 byte 도 표준 P-box / IP-Inv 패턴, **별도 키 첨부 없음**
- [tools/recon/find_h4_des_key.py](../../tools/recon/find_h4_des_key.py) (v1): `.data` ASCII (2,311) + sliding-window (59,556) brute force 모두 키 미발견
- [tools/recon/find_h4_des_key_v2.py](../../tools/recon/find_h4_des_key_v2.py) (v2, 2026-05-14): **전체 binary** (566K 바이트, 511,006 sliding 후보) + `__adf__`/`__class__` descriptor 토큰 (736) + AID 파생 (24) + weak/common keys (14) **모두 검증** — Phase 1 last-block sentinel 매치 0건
- [tools/recon/des_key_extended_hypotheses.py](../../tools/recon/des_key_extended_hypotheses.py): MD5/SHA1 of `/DAT/_DAT_DES` / `J@IWO8N7L0E7E` / `010100D4` / `한빛` 등 + SLvl 숫자 BE/LE + sequential bytes 0x79..0x86 + `JIWONLEE` (J@IWO8N7L0E7E 에서 letter-only 추출) — 모두 매치 0건
- Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c …`) 패턴 Hero4 binary 에 NOT FOUND → Hero4 별도 키

### 🔑 known-ciphertext leverage (Ghidra 키 발견 시 즉시 검증용)

ECB 100% 확정 근거 + 강한 known-plaintext crib (2026-05-14):

| ciphertext (hex) | 출현 위치 | 빈도 | 추정 plaintext |
|---|---|---|---|
| `3b7af9a427907dac` | SCN **마지막** 8 byte | **38 / 350** | EOS sentinel / 공통 종단 opcode |
| `1b7559e5bcf49488` | SCN 마지막 8 byte | 13 / 350 | (다른) 종단 패턴 |
| `ef9c94a1d8247276` | SCN 마지막 8 byte | 12 / 350 | (다른) 종단 패턴 |
| `c0f2daf72c2210e1` | SCN 마지막 8 byte | 11 / 350 | (다른) 종단 패턴 |
| `4655b8f39c0fe0b2` | SCN **첫** 8 byte | 8 / 350 | 공통 헤더 |
| `38d18f6ac1c49c07` | SCN 첫 8 byte | 7 / 350 | 공통 헤더 |
| `0206740aa7b9edea` | SCN 첫 8 byte | 6 / 350 | 공통 헤더 |

**Ghidra 에서 키 후보 발견 시 1차 검증 방법**:
```python
from Crypto.Cipher import DES
key = bytes.fromhex('<KEY_HEX>')  # 또는 ASCII
c = DES.new(key, DES.MODE_ECB)
# 가장 흔한 last block 복호화 — sentinel/low-entropy plaintext 면 키 정답
print(c.decrypt(bytes.fromhex('3b7af9a427907dac')).hex())
# 가장 흔한 first block 복호화 — Hero3 SCN signature `00 00 00 ff ff ff ...` 가설 검증
print(c.decrypt(bytes.fromhex('4655b8f39c0fe0b2')).hex())
```
38회 반복은 CBC 모드에서는 거의 불가능 (per-file IV 라면 마지막 cipher block 도 거의 unique). ECB 단정.

**키 발견 시 100% 최종 검증**: `tools/converter/decrypt_h4_scn.py --key <KEY> --batch` 후 첫 SCN 의 처음 16 byte 가 의미 있는 패턴이거나 (Hero3 처럼 `00 00 00 ff ff ff …`), EUC-KR 한글 (0xa1-0xfe) 시퀀스가 나타나면 성공.

**더 강한 검증 (2026-05-18 발견)** — Hero4 SCN known-plaintext signature:

| plaintext SCN | first 8 byte | 추론 가능 signature |
|---|---|---|
| `e0184_scn` (30B, misaligned) | `01 00 01 53 00 01 a1 ff` | `01 ?? 01 53 00 01 ?? ??` |
| `e0185_scn` (6313B+1, misaligned) | `01 02 01 53 00 01 c8 ff` | `01 ?? 01 53 00 01 ?? ??` |

5 byte (= 40 known bits) fixed signature. 키 검증 시:
```python
import sys; sys.path.insert(0, 'tools')
from converter.custom_des_h4 import decrypt as h4_decrypt
key = bytes.fromhex('<KEY_HEX>')
# 가장 흔한 first cipher block (8/348)
p = h4_decrypt(key, bytes.fromhex('4655b8f39c0fe0b2'))
assert p[0]==0x01 and p[2]==0x01 and p[3]==0x53 and p[4]==0x00 and p[5]==0x01, '키 오답'
```
Standard `Crypto.Cipher.DES` 와 custom (S1[58]=2) 둘 다 시도 권장.

**부수 작업 (Ghidra 진입 후 같이)**: `_PAL` secondary RGB 의미, `_EXD` payload struct, `_MAP_M_` extras 영역 — 모두 string xref 기반.

---

## 📊 현재 상태 스냅샷 (2026-05-07 갱신)

### Phase A — 자산 변환 ✅ **종료**

```
python tools/converter/convert_all.py work/h4/extracted work/h4/converted

Done. txt=5 pa=196 bm_files=30 bm_frames=200 cif=148 mp=0 scn=350
      scn_dialogues=4078 dat=26 h4_map=97 exd=117 h4_tile=276
      skipped=564 errors=0
```

| 카테고리 | 결과 |
|---|---|
| _TXT, _CIF, _DAT, _SCN, _MMF | Hero3 호환 (자세히는 [`formats/README.md`](formats/README.md)) |
| _PAL (8byte/color) | **196/196** — [`formats/pal.md`](formats/pal.md) |
| _MAP_M_NNN (3가지 헤더 버전 + 풀 body) | **97/97** — [`formats/map.md`](formats/map.md) |
| _EXD (헤더 추출, payload 보존) | **117/117** — [`formats/exd.md`](formats/exd.md) |
| TILE/, OBJ/{000,001,002}/ (single-frame 0x0c 8-bit dense) | **30 + 246 PNG** — [`formats/bm-tile-obj.md`](formats/bm-tile-obj.md) |
| HDAT/ (그룹 분류만) | 25 (Phase B 후 파싱) — [`formats/hdat.md`](formats/hdat.md) |

### 인프라 완성

- ✅ `tools/_game.py` — 게임-aware path 중앙 관리 (`HERO_GAME` 환경변수)
- ✅ `apps/hero4-android/` — Android 모듈 스켈레톤 (com.hero4.remake), 자산 699 file 배포
- ✅ `work/h4/converted_hd/` — scale4x 4× HD 209 PNG
- ⚠️ `work/h4/converted/dialogue_corpus.json` — 4,078 라인이지만 **DES 미복호화 → garbage**. apps/hero4-android assets 에도 garbage 사본 존재. **DES key 발견 후 재생성 필요**
- ✅ `work/h4/converted/asset_catalog.json` — 97 maps + 30 sprite dirs
- ✅ `tools/i18n/translation_dict.py` — game-aware (CHARACTERS_H3/H4, PLACES_H3/H4, `for_game(id)`). Hero4 zone 12개 prefill (켈트 4 보물 도시 + 한국어 zone)
- ✅ `tools/converter/decrypt_h4_scn.py` — DES 키 받아 SCN decrypt (단일/일괄, ECB/CBC). 키 발견 후 즉시 사용
- ✅ `tools/recon/find_h4_des_key.py` — DES brute-force (ASCII/sliding-window). 결과: 키는 binary 안 단순 8-byte 아님
- ✅ `tools/recon/diagnose_h4_scn_cipher.py` — SCN 통계 진단 (size/entropy/ECB hypothesis)

### 핵심 발견

- ⭐ **Hero4 SCN = 표준 DES (ECB 거의 확실) 암호화** — `_DAT_DES` 가 표준 DES 테이블 그대로 (2026-05-07 후속). **키 미발견** → Phase B 1순위
- ⭐ **0x0c BM = 8-bit dense palette indexed** (Ghidra `FUN_00010fe4` 분석). Hero3 미해독 91 BM (theme 47 + obj 44) 도 동시 unblocking
- **_PAL** 8byte/color (Hero3 4byte 의 2배) — primary + secondary RGB 페어
- **_MAP_M_** 헤더 버전 일반화: `0xff` separator 개수 = v, `nlen` offset = `2v+1`
- **_MAP_M_** post-NUL body = Hero3 `_mp` 100% 동일 layout
- Hero4 zone 이름 = **켈트 신화 Tuatha Dé Danann** 패러디 (뮤리아스/핀디아스/팔리아스/고리아스)
- Hero3+Hero4 = **같은 한빛 내부 엔진의 진화형** (`'frameBuf is NULL'` 동일 에러). 단 Hero4 는 SCN 암호화 추가
- `client.bin387872` 안에 **WIPI/JLet API 임베드** (`org/kwis/msp/lcdui/*`) — Clet+KTF 호환 빌드
- 모든 자산 path string 이 binary 에 명시되어 디스어셈블 없이도 자산 로딩 흐름 파악 가능

---

## 📁 디렉토리 구조

### 코드/도구
```
tools/
├── _game.py                      ← 게임 path/binary 설정 중앙 관리
├── converter/
│   ├── convert_all.py            ← 게임-aware 일괄 변환
│   ├── convert_palette.py        ← Hero3 4byte + Hero4 8byte 듀얼
│   ├── convert_h4_map.py         ← Hero4 _MAP_M_NNN
│   ├── convert_h4_tile.py        ← Hero4 single-frame BM (TILE/OBJ)
│   ├── convert_exd.py            ← Hero4 _EXD 헤더
│   ├── convert_bm_v2.py          ← BM 디코더 (0x0b dense 4-bit, 0x0c dense 8-bit)
│   ├── decrypt_h4_scn.py         ← ★ Hero4 SCN DES decrypt (키 발견 후 사용)
│   └── ... (Hero3 와 공유)
├── recon/                        ← `HERO_GAME` env 로 게임 선택
│   ├── find_h4_des_key.py        ← DES brute-force (한계 도달, 결과 PROGRESS 참조)
│   ├── diagnose_h4_scn_cipher.py ← SCN 통계 진단
│   └── ... (extract_strings, find_xrefs 등 game-aware)
└── i18n/                         ← `HERO_GAME` env 로 게임 선택
    ├── translation_dict.py       ← game-aware 사전 (for_game/all_translations)
    └── translate_dialogues.py    ← Claude Haiku 번역 (--dry-run 으로 prompt 검증)
```

### 자산
```
Hero4/010100D4.jar               ← 원본 (수정 금지)
work/h4/                         ← gitignore
├── extracted/                   ← JAR 추출 (1,850 file)
├── converted/                   ← PNG/JSON 변환 결과
├── converted_hd/                ← scale4x 4× upscale
└── ghidra_proj/                 ← Phase B 시 생성

apps/hero4-android/              ← 모노레포 옵션 A
├── app/src/main/
│   ├── java/com/hero4/remake/MainActivity.kt   ← Phase 3 placeholder
│   ├── assets/                  ← 변환된 자산 699 files
│   └── res/values/strings.xml + values-ko/strings.xml
├── build.gradle.kts             ← com.hero4.remake
└── README.md
```

### 문서
```
docs/h4/
├── PROGRESS.md                  ← 이 문서 (메인 핸드오프)
├── next-steps.md                ← 앞으로 해야 할 것 (★ 다음 작업 시 읽기)
├── ghidra-guide.md              ← Ghidra GUI 분석 가이드
├── formats/                     ← 자산 포맷 분석 디테일
│   ├── README.md                ← 인덱스
│   ├── pal.md                   ← _PAL 8byte/color
│   ├── map.md                   ← _MAP_M_NNN
│   ├── exd.md                   ← _EXD 캐릭터 데이터
│   ├── bm-tile-obj.md           ← BM 0x0b/0x0c, TILE, OBJ 디코더
│   └── hdat.md                  ← HDAT/ 25 파일 그룹 분류
└── binary/
    └── recon-results.md         ← client.bin387872 정찰 결과
```

---

## 🔧 재현 명령

### 자산 재변환

```bash
cd c:/gameRemake/testrepo

# Hero4 (default 가 h3 라 환경변수 명시)
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted

# Hero4 Android assets 배포
python tools/converter/prepare_android_assets.py work/h4/converted apps/hero4-android/app/src/main/assets

# Hero4 HD 업스케일
HERO_GAME=h4 python tools/hd/batch_upscale.py

# Hero4 대사 corpus + asset catalog
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/i18n/build_asset_catalog.py
```

### 바이너리 정찰

```bash
HERO_GAME=h4 python tools/recon/extract_strings.py     # 8,167 strings
HERO_GAME=h4 python tools/recon/find_f81f.py           # 0xf81f 위치 10
HERO_GAME=h4 python tools/recon/disasm_thumb.py        # 첫 256 byte 디스어셈블

# DES 진단 / brute force (이미 한계 도달, 참고용)
python tools/recon/diagnose_h4_scn_cipher.py          # SCN 350 통계 (entropy/ECB hint)
python tools/recon/find_h4_des_key.py --source ascii   # ASCII 8-byte 후보 brute force (~수 초)
python tools/recon/find_h4_des_key.py --source all     # sliding-window 전체 (~10초)
```

### DES key 발견 후 자동 파이프라인

```bash
# (Phase B 에서 8-byte 키 발견 가정)
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key <KEY> --batch
#   → work/h4/decrypted/SC/*_scn 350 file 생성

# 그 다음 SCN parser 가 decrypted 디렉토리 읽도록 수정 필요 (현재 convert_all.py 는 extracted 만 봄)
# 임시: cp work/h4/decrypted/SC/*_scn work/h4/extracted/MAP/SC/  (백업 후)
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

### Android 빌드 (스켈레톤)

```bash
cd apps/hero4-android
./gradlew assembleDebug
# 결과: app/build/outputs/apk/debug/app-debug.apk
# 현재 placeholder Activity (검은 화면 + "Phase 3 통합 대기 중")
```

---

## ⚠️ 알려진 이슈 / 보류

- ⛔ **NEW Hero4 SCN = DES 암호화** (2026-05-07 후속 발견) — 350 SCN + 4,078 대사 corpus 가 모두 garbage. ECB DES 거의 확실 (entropy 7.9962, 첫 cipher block 22% sharing, 99% 8-byte aligned). 자동 brute-force 한계 → **Phase B 1순위**. Diagnostic / brute-force 도구는 위 §🚨 참조
- ⛔ **A1 (대사 영어 번역)** — DES key 발굴 후 corpus 재생성 가능해야 의미 있음. `translation_dict.py` / `translate_dialogues.py` 는 Hero4 game-aware 로 이미 준비됨
- ~~**`_TILE_030`**~~ ✅ **풀림 (2026-05-07)**: 컨테이너 prefix `01 00 00 00 <size LE32>` 감지 → inner BM 으로 재진입. [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 에 반영. h4_tile=276→**277**, skipped=564→563
- **work/h3/ghidra_proj/*.lock** — Hero3 Ghidra 프로젝트 락이 걸려있어 work/h3/ 일부 이동 못 함. Ghidra 닫고 락 정리 필요
- ~~**`tools/recon/find_xrefs.py`, `find_pic_xrefs.py`, `find_base.py`** — hardcoded TARGETS~~ ✅ **풀림 (2026-05-07)**: [extract_strings.py](../../tools/recon/extract_strings.py) `--json` 옵션 + [_targets.py](../../tools/recon/_targets.py) 헬퍼 도입. 3 스크립트 모두 game-aware. h3/h4 양쪽 검증
- **`_PAL` secondary RGB 의미** — 미확정. 가장 유력한 가설은 alpha mask. Phase B 에서 확정
- **_EXD payload, _MAP_M_ extras, HDAT entry layout** — 모두 Phase B 후 확정
- **Hero4 binary 의 string xref 추적** — h3 와 다른 addressing (PIC LDR+ADD T1 인접 패턴 거의 없음). Phase B Ghidra GUI 에서는 32-bit LDR.W (T4) 또는 다른 sequence 추적 필요
- **2 misaligned SCN** — `e0184_scn` (30B), `e0185_scn` (6313B+1) 8-byte 정렬 안 됨. outlier, DES 적용 시 별도 처리 필요할 수도

---

## 📜 이번 세션 (2026-05-06) 작업 압축

1. **모노레포 옵션 A 결정** + 디렉토리 분리 (work/h{3,4,5}, docs/h{3,4,5})
2. **`tools/_game.py`** 게임-aware 모듈 + 모든 hardcoded path 리팩터
3. **Hero4 JAR 추출** 후 Hero3 컨버터 dry-run → 호환률 ~80% 측정
4. **`_PAL` 8byte/color 분기 추가** → 196/196 변환
5. **`_MAP_M_NNN` 파서 작성** (헤더 v1/v2/v3 + 풀 body) → 97/97 변환
6. **`_EXD` 헤더 파서** 작성 → 117/117 변환 (payload 보존)
7. **TILE/OBJ single-frame BM 디코더** (`convert_h4_tile.py`) → 276 PNG
8. **0x0c BM 디코더 풀이** (Ghidra `FUN_00010fe4` 분석 결과를 사용자가 docstring 으로 반영, 코드 동기화). Hero3 미해독 91 BM 동시 unblocking
9. **client.bin387872 정찰** (extract_strings 8,167개, find_f81f 10 위치)
10. **Hero4 Android 모듈 스켈레톤** (`apps/hero4-android/`, com.hero4.remake) 생성 + 자산 699 file 배포
11. **Hero4 i18n / HD / dialogue corpus** 인프라 구동 (build_asset_catalog 의 폴더 카테고리 game-aware 화)
12. **문서 재구성** — `formats/` (5+1), `binary/` (1), `next-steps.md`, 메인 PROGRESS

errors=0 양 게임 모두. 다음: [`next-steps.md`](next-steps.md) 의 Phase B 또는 A1/A4 자동 작업.

---

## 📜 세션 (2026-05-07) 작업 압축

1. **A4 — recon 도구 game-aware 리팩토링 완료**
   - [extract_strings.py](../../tools/recon/extract_strings.py): `--json OUT` / `--game` / `--quiet` 옵션. path-like + 라벨을 자동 추출, `code_end_estimate` 도 path-like 최소 offset 으로 자동 산출
   - [_targets.py](../../tools/recon/_targets.py) 신규: `load_targets(priority_only=...)` 게임별 JSON 로더
   - [find_xrefs.py](../../tools/recon/find_xrefs.py), [find_pic_xrefs.py](../../tools/recon/find_pic_xrefs.py), [find_base.py](../../tools/recon/find_base.py) 의 hardcoded TARGETS 모두 제거
   - 산출: `work/h3/converted/string_offsets.json` (105 targets), `work/h4/converted/string_offsets.json` (93 targets)
   - Hero4 정찰로 발견: code/data 경계 ≈ **0x77000**, 핵심 라벨 4개 (`====> Alpha Palette Index Not Found` @0x820dc, `====> frameBuf is NULL` @0x82104, `java/lang/NullPointerException`, `(null)`)

2. **A5 — `_TILE_030` 풀림**
   - 컨테이너 포맷: `01 00 00 00` (count?) + size LE32 (0x8d=141) + inner BM
   - [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 의 `decode_h4_tile` 에 prefix 감지 분기 추가
   - 결과: 16×16 dark blue placeholder tile. h4_tile 카운트 +1
   - `01 00 00 00` prefix 가 있는 파일은 TILE/OBJ 통틀어 단 1개 (`_TILE_030`) — 일회성 케이스

3. **인프라 정리**
   - Hero3 layout 마이그레이션: `work/extracted/` → `work/h3/extracted/` (`_game.py` 가 기대하는 nested 레이아웃)
   - Hero4 JAR 추출: `work/h4/extracted/client.bin387872`

4. **문서**
   - [docs/REMAKE_METHODOLOGY.md](../REMAKE_METHODOLOGY.md) 신규 — "리메이크" 의 정의 + JAR/APK 케이스별 작업 방식 + 시리즈 진행 기록
   - [Readme.md](../../Readme.md) 상단에 방법론 문서 링크 추가

---

## 📜 세션 (2026-05-07 후속) — A3 + DES 발견

1. **A3 — translation_dict.py game-aware 리팩토링 완료**
   - `CHARACTERS_H3` / `CHARACTERS_H4`, `PLACES_H3` / `PLACES_H4` 분리 (이전 `CHARACTERS` / `PLACES` 는 H3 alias 로 보존 → 기존 호출자 무회귀)
   - `for_game(id)` / `all_translations(id)` 게임별 묶음 조회 API 추가
   - [translate_dialogues.py](../../tools/i18n/translate_dialogues.py) 의 `build_system_prompt` 가 `_g.id` 기반으로 게임 헤더 (`GAME_HEADERS`) + dict 자동 선택
   - Hero4 zone 12개 prefill: 뮤리아스/핀디아스/팔리아스/고리아스 (켈트 4 보물 도시) + 수레바퀴섬/매도우힐/이름없는섬/아눈섬/검은바위섬/은바위섬/해적소굴/환영의검
   - `--dry-run` 이 corpus 부재시에도 system prompt 검증 가능하도록 수정
   - 검증: `HERO_GAME=h4 python translate_dialogues.py --dry-run` → 219 항목, Hero4 헤더 + Tuatha Dé Danann 설명 정상 출력. Hero3 회귀 없음 (249 항목 그대로)

2. **🚨 A1 차단 원인 발견 — Hero4 SCN = DES 암호화**
   - 증상: `dialogue_corpus.json` 에 한자/깨진 문자 (`曝삑킴`, `承孼`, `偉煌`) — Hero3 의 EUC-KR extractor 가 random 바이트를 garbage 로 디코딩
   - Hero3 SCN 첫 64B = `00 00 00 ff ff ff ...` plaintext bytecode
   - Hero4 SCN 첫 64B = `28 69 6c 88 a4 2a ca 09 ...` **high-entropy 암호 바이트**
   - **결정적 단서**: `work/h4/extracted/DAT/_DAT_DES` (824 bytes) 가 표준 DES 알고리즘 테이블 (PC-1, E-box, P-box, S1) 을 그대로 담고 있음을 검증. 따라서 Hero4 는 표준 DES (custom 알고리즘 아님)
   - Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c 31 11 21 39 02 09 13 2a`) 패턴을 Hero4 binary 에서 검색 → **NOT FOUND**. Hero4 는 별도 키 사용
   - **다음 단계 (Phase B 1순위)**: Ghidra 에서 `/DAT/_DAT_DES` (string @ 0x86ecc) xref 추적 → SCN decryption 진입점 → DES key 8 bytes 추출. 키 발견 후 SCN 재복호화 → corpus 재생성 → A1 진행 가능

3. **문서 갱신**
   - [next-steps.md](next-steps.md): A1 ⛔ DES 차단 표시, Phase B 우선순위 표 최상단에 **DES key (8 bytes)** 추가
   - 해당 발견 요약 inline note 추가

4. **자동 brute-force 시도 + diagnostic** (Phase B 진입 전 자동 가능 영역 한계 도달)
   - [tools/converter/decrypt_h4_scn.py](../../tools/converter/decrypt_h4_scn.py) 신규 — DES 키 받아 SCN decrypt (단일/일괄, ECB/CBC). 키 발견 즉시 사용 가능
   - [tools/recon/find_h4_des_key.py](../../tools/recon/find_h4_des_key.py) 신규 — binary `.data` 영역 (start=0x77000) 의 ASCII / sliding-window 8-byte 후보를 brute force. Hero3 SCN signature `00 00 00 ff ff ff` 매칭 시 score+200
     - ASCII 후보 (2,311개): max score 81 (BASIC_SM 등 binary 안 부분문자열). 진짜 키 신호 없음
     - sliding-window 전체 (59,556개): max score 87. 여전히 signature 매칭 0건
     - **결론**: ECB 라면 키는 binary 안 단순 8-byte 가 아니거나, plaintext format 이 Hero3 SCN 과 달라 scoring 가정 자체가 빗나감
   - [tools/recon/diagnose_h4_scn_cipher.py](../../tools/recon/diagnose_h4_scn_cipher.py) 신규 — 350 SCN 통계 진단:
     - **99% (348/350) 가 8-byte aligned** → DES 호환 ✓
     - **Shannon entropy 7.9962 bits/byte** (uniform random 8.0) → 강한 암호 (DES/AES) 또는 compressed. XOR 류 약한 obfuscation 배제
     - **반복 cipher block 1~5%** + **첫 cipher block 22% sharing** (273/350 unique) → **ECB DES 강력 시사** (CBC 면 per-file IV 로 거의 100% unique 나와야)
     - Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c …`) 패턴 검색 → Hero4 binary 에 NOT FOUND. 별개 키
     - misaligned 2개 (e0184_scn=30B, e0185_scn=6313B+1) — outlier, 별도 처리 필요할 수도

다음 작업: **Phase B (Ghidra GUI) — 사용자 환경 작업 필수**. 자동 정찰의 한계는 명확.
1순위: `/DAT/_DAT_DES` (string @ 0x86ecc) xref 추적 → SCN decrypt 진입점 함수 → 그 함수 호출자에서 키 source (literal 8 bytes 또는 키 파생 input)
키 발견 후: `python tools/converter/decrypt_h4_scn.py --key <KEY> --batch` 한 번이면 350 파일 즉시 복호화 → corpus 재생성 → A1 진행 가능.

---

## 📜 세션 (2026-05-14) — DES brute-force v2 + known-ciphertext leverage 확립

자동 영역 추가 시도 (Phase B Ghidra 진입 전 마지막 자동 탐색). 결론: **자동 brute-force 완전 한계 확정**.

1. **SCN ciphertext 정밀 통계** — ECB 모드 100% 단정
   - 마지막 8-byte ciphertext `3b7af9a427907dac` 가 **38 / 350 SCN 에서 반복** (11%)
   - 마지막 8-byte 가 13+회 반복되는 패턴이 최소 3종 (`1b7559e5bcf49488` ×13, `ef9c94a1d8247276` ×12, `c0f2daf72c2210e1` ×11)
   - 첫 8-byte 도 `4655b8f39c0fe0b2` ×8, `38d18f6ac1c49c07` ×7 등 반복
   - CBC 라면 per-file IV 로 거의 100% unique 해야 함 — **ECB 단정**, 38회 반복 last block 은 공통 평문 종단 (sentinel / EOS opcode) 의 강한 known-ciphertext crib

2. **확장 brute-force 도구화** ([tools/recon/find_h4_des_key_v2.py](../../tools/recon/find_h4_des_key_v2.py))
   - v1 한계 (`.data` start=0x77000 만) 해소 → **전체 binary** (start=0, 566K 바이트, 511,006 sliding-window 후보)
   - 추가 후보 소스: `__adf__` / `__class__` SKT descriptor ASCII tokens (736), AID 파생 (24), weak/common DES keys (14)
   - 검증 전략: 가장 흔한 last-block (`3b7af9a427907dac`) decrypt → plaintext 가 sentinel 패턴이면 통과
   - 결과: **Phase 1 survivors 0** (sentinel/low-entropy 가설 모두 미통과)

3. **확장 가설 별도 검증** ([tools/recon/des_key_extended_hypotheses.py](../../tools/recon/des_key_extended_hypotheses.py))
   - MD5/SHA1 of `/DAT/_DAT_DES`, `_DAT_DES`, `DES`, `J@IWO8N7L0E7E`, `010100D4`, `한빛` (UTF-8/EUC-KR) 등 → 0 match
   - `__adf__` 의 SLvl/SLvl2/FSize/Timestamp 를 BE/LE 8-byte → 0 match
   - sequential bytes 0x79..0x86 (binary `_DAT_DES` 근처 ascending pattern) → 0 match
   - `JIWONLEE` (J@IWO8N7L0E7E 에서 letter-only 추출 = "Lee Ji-won" 패턴, 매우 유망 가설) → 0 match
   - `JIWONLEE` reversed / lowercase / 8-byte sliding 변형 → 0 match

4. **`_DAT_DES` 파일 자체 검증**
   - 824 byte 전체가 표준 DES 알고리즘 테이블만 (시작: PC-1 `3a 32 2a 22 1a 12 0a 02` = bit 58,50,42,34,26,18,10,2 ✓)
   - 마지막 64 byte 도 표준 P-box / IP-Inv 패턴 — **별도 key 첨부 없음**
   - ⚠ **2026-05-18 재검증**: 첫 64 byte 는 PC-1 이 아니라 **IP (Initial Permutation)** 임을 확인. 정확한 layout:
     IP(64) + IP-Inv(64) + E(48) + P(32) + S1(64) + S2(64) + ... + S8(64) + PC-1(56) + PC-2(48) = 824
     824 byte 중 **823 byte 가 표준 DES 와 정확히 일치, 1 byte 만 다름** (S1[58]).

5. **🔍 새 단서 — `J@IWO8N7L0E7E` @0x86edc**
   - `_DAT_DES` 문자열 (@0x86ecc) 바로 다음 위치에 의문의 13-char ASCII null-term 문자열
   - hex: `4a 40 49 57 4f 38 4e 37 4c 30 45 37 45 00 00 00`
   - letter-only 추출 = `JIWONLEE` (8 chars, "Lee Ji-won" 한국 이름 패턴) — 키 직접 매치는 실패했지만 Ghidra 에서 xref 추적 필수
   - 가능성: (a) 스크램블된 키 (XOR/permutation), (b) 다른 자원 식별자, (c) 개발자 서명 string

6. **자동 영역 완전 종결 — 다음 진입은 Ghidra 1순위**
   - 위 known-ciphertext (`3b7af9a427907dac`, `4655b8f39c0fe0b2`) 는 Ghidra 에서 키 발견 시 단발 검증용으로 즉시 사용 가능 — `decrypt_h4_scn.py` 돌리기 전에 `Crypto.Cipher.DES` 로 1초 검증
   - 추적 대상 strings (Ghidra xref): `/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1

---

## 📜 세션 (2026-05-18) — plaintext SCN 발견 + custom DES 가설 + PAL 통계

자동 영역 추가 발견 — 2026-05-14 의 "자동 영역 완전 종결" 선언을 **재검토**. 4개 신규 발견:

1. **🌟 plaintext SCN 2개 발견** — e0184_scn (30B) / e0185_scn (6313B) misaligned outlier 가 실은 **DES 처리 안 된 raw plaintext** 였음을 확인
   - e0184: `01 00 01 53 00 01 a1 ff …` + ASCII "VALUE" 문자열. 짧은 metadata SCN
   - e0185: `01 02 01 53 00 01 c8 ff …` + 끝부분에 EUC-KR 한글 풀 풀 풀 (`b9ab b1e2 …`)
   - 공통 헤더 signature: **`01 ?? 01 53 00 01 ?? ??`** (5 byte fixed = 40 known bits, DES known-plaintext attack 의 강한 crib)
   - 348 encrypted SCN 중 어느 것도 plaintext signature 와 match 안 됨 (이미 빈 sample, 자명)

2. **🌟 e0185_scn = Hero4 글로벌 entity catalog** — 87 null-terminated 문자열, 게임 전체 NPC/객체 이름 정의
   - 추출 결과: `work/h4/converted/e0185_name_table.json` (offset + text)
   - 켈트 신화 인물 33+: 앨리스(Alice), 브리안(Brian), 디어드리(Deirdre), 노덴스(Nodens), 누아다(Nuada), 티르(Tyr), 브레스(Bres), 케프네스(Kephness) — Tuatha Dé Danann 패러디 확정
   - 일반 명사: 인간/선주/꼬마/병사/대장장이/연금술사/소환술사 등 직업 19개
   - 게임 상태: 출구/결계/블라인드/대미지/넉백/이벤트 등 transition 라벨
   - **CHARACTERS_H4 사전 prefill 완료** (52 entries) — [translation_dict.py](../../tools/i18n/translation_dict.py). h4 system prompt 길이 2,689 chars

3. **🌟 `_DAT_DES` S1 1-byte 변형 발견 — Hero4 custom DES 가설**
   - 정확한 layout 분석: IP(64) + IP-Inv(64) + E(48) + P(32) + 8×S(512) + PC-1(56) + PC-2(48) = 824B
   - 823 byte 표준 DES 와 정확 일치. **단 1 byte 차이**: S1[58] (= S1 row 3, col 10) `std=3, _DAT_DES=2` @ file offset 0x010a
   - 단일 비트 차이 (3 = 0b011, 2 = 0b010, bit 0 toggle). 단순 typo 가능성과 의도적 anti-piracy 가능성 모두 존재
   - **함의**: 의도적 변형이라면 `Crypto.Cipher.DES` / `SunJCE` 로는 영원히 복호화 불가
   - 검증 도구: [tools/recon/verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py) — `824 byte: 1 deviation @S1[58]`
   - 구현: [tools/converter/custom_des_h4.py](../../tools/converter/custom_des_h4.py) — pure Python DES with S1[58]=2, roundtrip self-test 통과 (5,876 blocks/s pure python)

4. **v3 + v4 brute-force 종결 재확인** — Hero4-specific signature + custom DES 둘 다 시도, 키 미발견
   - v3 ([find_h4_des_key_v3.py](../../tools/recon/find_h4_des_key_v3.py)): 표준 DES + 5 top first-cipher × Hero4 signature. binary + DAT_DES + plaintext SCN + JAR 자원 (_LOGO/TITLE_BM/tdf/*) 전체 검색. Phase 2 cross-validation 결과 모두 partial 만, perfect 0건
   - v4 ([find_h4_des_key_v4.py](../../tools/recon/find_h4_des_key_v4.py)): custom DES (S1[58]=2) + 513,941 candidates × 5 ciphers, ~7 분. 백그라운드 실행 결과 동일 — 키는 8-byte literal 로 어디에도 없음
   - 두 결과 모두 0 → **키는 binary 안 8-byte literal 이 아님** (scrambled / derived / 별도 위치)

5. **🌟 `_PAL` secondary RGB 통계 분석** — A1/A2 = 0 padding, identical 0%, scale-darken 만 11%
   - 196 PAL 파일 5,724 entries 분석. 포맷 재확정: `u8 count + N×8B entries`, 8B entry = `R1 G1 B1 A1 R2 G2 B2 A2`
   - **A1 / A2 (byte 3, 7) = 모두 0** (5724/5724) → 이전 가설 "alpha mask" 기각. 순수 padding
   - **primary == secondary 인 entry: 0건** → palette swap 가설도 부분 기각 (identical 이 0% 이면 always 다른 색)
   - 관계 분포: independent 37.3% / darker_no_scale 34.6% / lighter_no_scale 12.9% / scaled_near1 9.2% / scaled_darker 5.8% / scaled_lighter 0.2%
   - "scale-darken (uniform shadow)" 가설은 6% 뿐. **두 separate color slot** (color cycling / two-tone / animation frame / display profile variant) 가 더 유력
   - 도구: [tools/recon/analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py), 결과 JSON: `work/h4/converted/pal_secondary_stats.json`

요약: 자동 영역에서 **DES key 추가 발굴은 여전히 불가** 이나, **CHARACTERS_H4 사전 + plaintext signature crib + custom DES 구현 + PAL 의미 후보 좁힘** 의 4 가지 누적 진전. Phase B 진입 시 검증 도구가 한 단계 더 강해짐.

---

## 📜 세션 (2026-05-18 후속) — _EXD 파싱 + _MAP_M_ extras multi-section 구조

위 5건 발견 후 추가 진전 3건:

7. **🌟 v4 brute-force 결과 확정 (백그라운드 438s)** — custom DES (S1[58]=2) + 513,941 후보 × 5 cipher = 모두 시도, **0 survivors**. 키는 binary literal 아님 100% 확정 (v3 표준 DES + v4 custom DES 양쪽 fail).

8. **🌟 _EXD payload struct 풀림 (count=1 케이스)** — 117 캐릭터 데이터 파싱
   - count=1, subtype=2 (14 files): 12B entry = 4B head (`00 ?? ff 01`) + 1×8B box (LE int16 dx,dy,w,h)
   - count=1, subtype=3 (26 files): 21B entry = 4B head + box1(8) + sep_byte(0x02) + box2(8)
     - box1 = 캐릭터 발/충돌 영역 (dx~-8, dy~-5, w~14, h~9)
     - box2 = sprite render bounds (dx~-7, dy~-24, w~12, h~25 vertical)
   - count=1, subtype=1 (5 files): 가변 (2/3/7 byte), 미정
   - count>1 (72 files): 첫 entry 21B subtype3 + 나머지 가변 (0x03 box separator 있음)
   - 파서: [tools/converter/parse_h4_exd.py](../../tools/converter/parse_h4_exd.py), JSON: `work/h4/converted/exd_parsed.json`
   - 헤더 check 통과: 112/117

9. **🌟 _MAP_M_ extras 영역 multi-section 구조 풀림** — 97 맵 파일 부분 파싱
   - extras = **N개 section, 각 section = `1B count + N × 8B records`**
   - 8B record layout: `type(1B) + sub_data(3B) + x(LE uint16) + y(LE uint16)`
   - section 수 분포: 4 sections (28 files) / 5 (48) / 6 (15) / 7 (4) / 8 (2)
   - **13/97 파일 완전 소비** (no tail), 84/97 1~40B trailing (variable-length tail section)
   - 모든 파일이 first 4 sections 까지 정상 파싱 → 핵심 layout 확정
   - section 별 의미 추정: sec0=tile/NPC spawn (대량), sec1+=exit/event/trigger (소량) — Ghidra 명명 필요
   - 파서: [tools/converter/parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py), JSON: `work/h4/converted/map_extras_parsed.json`
   - 샘플 `_MAP_M_000` (수레바퀴섬/선착장): 4 sections × (55/26/24/0 records), tail 6B

10. **encrypted SCN second cipher block crib 추가** — `f7740f758b9a6ae4` 가 17/348 회 반복 (이전 last-block 38회, first-block 8회 외에 새로운 3번째 known-ciphertext)
    - Ghidra 에서 키 검증 시 추가 cross-validation 사용 가능
    - `c.decrypt(bytes.fromhex('f7740f758b9a6ae4'))` 도 추가 plaintext signature check

요약 update: Phase B 진입 전 자동 작업이 **추가 3 단계** 진전 — _EXD 파서 + _MAP_M_ extras 파서 + DES 다중 cipher crib. 콘텐츠 wiring (Phase C/D) 단계에서 NPC/exit/event 데이터가 즉시 사용 가능.

---

## 📜 세션 (2026-05-18 후속2) — HDAT Group B layout + e0184 SCN bytecode 분해

추가 자동 발견 2건:

11. **🌟 HDAT Group B (P000-P005) layout 풀림** — 6 파일 progression/cost table
    - **`3B header + N × 50B entries`** 일관된 layout (P000=1ent, P001-3=2ent, P004=3ent, P005=2ent)
    - Entry 50B = **8 × uint16 LE main values** + 1B marker (0xff/0x00) + 5B param block + 28B nested tail u16s
    - main values 패턴: `[level/rank, hp/cost, 0, stat2, 0, gold/EXP, atk, hp_max]`
    - P004 entry[0] outlier: marker=0x00 + val[5]=20000 (boss/special tier?)
    - 파서: [tools/converter/parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py), JSON: `work/h4/converted/hdat_p_parsed.json`

12. **🌟 e0184_scn (30B plaintext) 완전 분해 + SCN bytecode 구조 추론**
    - 12B 헤더 signature `01 ?? 01 53 00 01 ?? ?? ff ff ff ff ff` (변수 byte 2개, 나머지 10 byte 고정)
    - 본문 영역: record-based bytecode (opcode + length + body)
      - opcode 0x01: string entry (length-prefixed + null-terminated)
      - opcode 0x0c: small immediate value
      - 0xff: record separator
    - e0184/e0185 의 **bytes 15-20 동일** (`00 00 ff 0c 00 ff`) — sub-header marker
    - 새 문서: [docs/h4/formats/scn.md](formats/scn.md)
    - 함의: DES key 발견 시 348 encrypted SCN 도 같은 구조 파서로 즉시 복원 가능
    - DES key 검증 시 best signature: 첫 8 byte decrypt 결과가 `01 ?? 01 53 00 01 ?? ??` 매칭 (40 known bits)

이번 누적 발견 (총 12 항목): plaintext SCN 2개 + CHARACTERS_H4 prefill + SCN signature + custom DES (S1[58]=2) + v3/v4 brute-force (모두 0건) + PAL 통계 + _EXD box layout + _MAP_M_ multi-section + SCN 2nd-block crib + **HDAT Group B layout + e0184 bytecode 구조**.

---

## 📜 세션 (2026-05-18 후속3) — HDAT Group A 암호화 키 공유 확인 + Group D 풀림 + OBJ 그룹 분포

추가 발견 4건:

13. **🚨 HDAT Group A 8 파일도 SCN 과 동일 DES 키로 암호화 — 확정**
    - 모두 8-byte aligned (entropy 6.3~7.8)
    - **SCN sentinel block `3b7af9a427907dac` (38회 SCN) 가 Group A 에서도 92회 반복**:
      - `_H_SA` 37회 (마지막 8 byte 가 이 sentinel), `_H_SS` 23회, `_H_S001` 9회, `_H_S003` 8회, `_H_S000` 7회, `_H_S002` 5회, `_H_BS` 3회
    - `_H_S000` ↔ `_H_S002` 9 shared blocks (첫 16 byte 동일 + ECB pattern) → 같은 plaintext 변형
    - **함의**: DES key 1개 발견 시 SCN 348 + HDAT Group A 8 = **356 파일 한 번에 복호화**
    - 추정 의미: `_H_BH`=Boss Hero, `_H_BS`=Boss Stat, `_H_SA/SS`=Save template A/Special, `_H_S000-S003`=4 save slots

14. **🌟 HDAT Group D (PDAT, SG) layout 풀림**
    - `_H_SG` (170B): **10 슬롯 × 17B** = 12B constant prefix + 5B variable. 5 slots (group "13 13") + 5 slots (group "12 12") — **2 모드 × 5 캐릭터** 가설 (Normal/Hardcore 또는 Story/Free)
    - var bytes 패턴: 8b ff ff ff 8f → 8c..90 → 8d..91 → 8e..92 (4 캐릭터 × CIF id + zone id)
    - `_H_PDAT` (86B): 17 변수 길이 records, 0xff terminated. 첫 record = `0e 00 00 00 00 00` (header), 이후 character/skill/quest/inventory init data
    - [hdat.md](formats/hdat.md) 갱신

15. **🌟 OBJ/{000,001,002}/ 그룹 분포 측정**
    - `OBJ/000/`: 100 파일, **모두 16×16 균일** (small icon / UI)
    - `OBJ/001/`: 100 파일, variable 12~60×13~92 (캐릭터/큰 객체)
    - `OBJ/002/`: 47 파일, variable 8~36×11~35 (아이템/중형)
    - 247 single-frame BM, 게임 내 정확한 매핑은 `_MAP_M_` extras `sub[3]` field 와 cross-reference 후 확정
    - [bm-tile-obj.md](formats/bm-tile-obj.md) §"OBJ 그룹 분포" 추가

16. **e0185 body 통계 (5545B catalog 이전 영역)** — 555개 0xff separator, top byte 분포 `0x00`(1786) / `0x01`(1193) / `0xff`(560) / `0x2e`(498) / `0x07`(485). 복잡한 nested bytecode 구조. opcode 0x2e (= '.') 와 0x07 의 의미는 Ghidra 후 확정.

이번 누적 발견 (총 16 항목): 1~12 + **HDAT Group A 키 공유 확인 + Group D 풀림 + OBJ 그룹 분포 + e0185 body 통계**.

---

## 📜 세션 (2026-05-18 후속4) — _MAP_M_ extras 의미론 완전 풀이 + SCN disassembler

이전 세션 "자동 영역 완전 종결" 선언을 다시 깨고 추가 발견 2건.

17. **🌟 _MAP_M_ extras 의 sub[2] = global OBJ id (0..246) — 100% 검증**
    - 사전 분석: 97 파일 16,358 sec[0..3] records 의 sub[2] 가 **0..246 범위에 100% fit**, 0 out-of-bounds
    - 매핑: `0..99 = OBJ/000/_OBJ_NNN`, `100..199 = OBJ/001/_OBJ_(NNN-100)`, `200..246 = OBJ/002/_OBJ_(NNN-200)`
    - x/y 좌표 = **16-pixel 단위 픽셀 좌표** 확정 (max_x/16+1 / max_y/16+1 = map tile 차원과 정확 일치)
    - sub[1] = 0xff 100% (16,358/16,358) → category marker
    - type byte 99% = 0x00 또는 0x40 → bit flag (0x40 = flip-x 추정)
    - sub[0] = state/variant byte (sec[3] 에서 `state=40, obj_id=10` 페어 105회 반복 → 특정 OBJ 의 표준 instance)
    - Section 별 의미 (resource pool 분포):
      | sec | total | unique | g000/g001/g002 | 추정 |
      |---|---|---|---|---|
      | 0 | 8022 | 135 | 47/18/34% | terrain decoration / props (가장 큰 layer) |
      | 1 | 6010 | 164 | 47/23/28% | secondary decoration / interactive objects |
      | 2 | 1956 | 113 | 52/45/2% | NPC / character mix |
      | 3 | 370 | **19** | 32/60/6% | 특수 NPC / portal / 이벤트 (좁은 pool) |
    - Top placement: `OBJ/000/_OBJ_098` (1273회), `OBJ/001/_OBJ_099` (949회), `OBJ/002/_OBJ_028` (622회)
    - 도구: [tools/recon/analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py), JSON: `work/h4/converted/map_extras_semantics.json`
    - 문서 갱신: [formats/map.md](formats/map.md) "8B record 필드 의미" + "Section 별 의미" 섹션

18. **🌟 plaintext SCN disassembler + e0185 name_table 자동 추출**
    - 도구: [tools/converter/disasm_h4_scn.py](../../tools/converter/disasm_h4_scn.py) — e0184/e0185 (DES 미적용 outlier 2개) tokenizer
    - 헤더 검증: signature_ok flag, variant_a/b 추출
    - bytecode tokenize: 0xff record separator + opcode pattern detection (0x01 string-like, 0x07 magic, 0x0c immediate, 0xf7 3-arg bind)
    - 출력 1: `work/h4/converted/{e0184,e0185}_scn_disasm.json`
    - 출력 2: `work/h4/converted/e0185_name_table.json` (80 entries — Tuatha Dé Danann 캐릭터 + 게임 객체 catalog)
    - e0185 분석 결과:
      - bytecode 5577B = 1110 tokens
      - **`op_0x01` 462회** (가장 흔한 record kind — string-like 또는 entity reference)
      - 462개 op_0x01 records 안에 `07 00 00 00` substring 자주 등장 → 공통 prefix 확정
      - 555개 0xff separator
    - DES key 발견 시: encrypted SCN 350개 = 같은 disassembler 로 토큰 분포 cross-validate 가능
    - 문서 갱신: [formats/scn.md](formats/scn.md) "디스어셈블러" 섹션

이번 누적 발견 (총 18 항목): 1~16 + **_MAP_M_ extras OBJ id 매핑 (검증된 schema) + SCN disassembler (재현 가능 도구)**.

자동 영역에서 남은 미해결 (모두 Phase B Ghidra 의존):
- _MAP_M_ extras sec[4+] schema (1B count + 8B records 가설 무효 — sub[1] != 0xff)
- sec[3] `state=40` 의 정확한 의미 (frame? facing? animation?)
- _EXD count>1 entry 2+ 구조
- e0185 op_0x01 records 의 `07 00 00 00` prefix 후 4 byte body 의미
- HDAT Group A 의 평문 구조 (DES key 후)

---

## 📜 세션 (2026-05-18 후속5) — sec[4+] event block header + op_0x01 정밀 구조 + OBJ 매핑 수정

이전 후속4 의 미해결 두 항목을 추가로 풀이.

19. **🌟 _MAP_M_ extras sec[4+] = single event block (count + 2B magic + type + variable records)**
    - **77/97 maps** 가 일관된 4-byte header `[count: 1B] [00 01: 2B fixed] [type: 1B]` 매칭 (≥80%)
    - count 분포: 3 (51 maps, 표준), 4 (26 maps, 확장)
    - type byte: 0x03 (52 maps), 0x02 (34 maps), 0x06 (1 map) — 거의 binary 분류
    - records 는 variable-length (count=3 평균 12B/rec, range 3-20B) — script opcode 추정
    - 0xff separator 없음, 작은 byte values (0x00..0x30) 위주 → script bytecode 가능성 높음
    - 남은 20 maps 의 variant headers: `00 00 ...` (10), `01 03 01 03` (8), `03 00 01 02` (8 — type=2)
    - 정확한 record schema 는 Ghidra 후 (script opcode dispatch 함수 추적 필요)

20. **🌟 e0185 op_0x01 record 일관된 9-byte schema 확정**
    - 462 records 모두 `[01] [00 07 00 00 00 fixed 5B prefix] [2~4B middle] [2e terminator]`
    - 392/462 = 9 bytes (middle = 2B), 45/462 = 5 bytes (단축), 19/462 = 7 bytes (확장), 4/462 = 14 bytes (긴 형식)
    - 6-byte prefix `01 00 07 00 00 00` = REFERENCE_ENTITY opcode 추정
    - middle = string index + sub-id pair (1..3 incrementing 패턴 발견)
    - 462 refs / 80 catalog entries ≈ **6 refs per entity** → 다른 SCN 도 catalog index 로 참조하는 구조
    - DES key 발견 시 즉시 검증: encrypted SCN 들도 같은 schema 인지 disassembler 로 cross-validate

21. **OBJ id ↔ filesystem 매핑 정정 (이전 #17 후속4 발견 수정)**
    - 잘못된 매핑: `OBJ/001/_OBJ_(obj_id-100)`, `OBJ/002/_OBJ_(obj_id-200)`
    - **정확한 매핑: `OBJ/NNN/_OBJ_NNN`** — filename 이 글로벌 id 그대로 보존, group dir 만 100 단위 분류
    - 예: `obj_id=199 → OBJ/001/_OBJ_199` (NOT `_OBJ_099`)
    - [tools/recon/analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py) 의 `obj_id_to_path()` 수정
    - 파일 존재성 검증: obj_id 98/199/228/229/48/246 모두 ✓ EXISTS

이번 누적 발견 (총 21 항목): 1~18 + **sec[4+] event block header schema + op_0x01 9-byte 일관 schema + OBJ 파일명 매핑 정정**.

자동 영역에서 남은 미해결 (Phase B Ghidra 의존):
- sec[4+] event records 의 variable-length 내부 schema (script opcode dispatch)
- sec[3] `state=40` 의 의미 (frame? facing?)
- _EXD count>1 entry 2+ 구조
- HDAT Group A 의 평문 구조 (DES key 후)
- e0185 op_0x01 의 middle index → catalog 엔트리 매핑 (확정하려면 SCN 들이 같은 catalog 를 어떻게 참조하는지 봐야 함 = DES key 후)

---

## 📜 세션 (2026-05-18 후속6) — CIF 117 파일 layout + DES 암호화 파일 풀 확장

추가 자동 진전 4건. 누적 21 → **25 건**.

22. **🌟 CIF 117 파일 = Hero3 parser 100% 호환** (Hero3 엔진 commonMain 이전 시 Hero4 자동 inherit)
    - Hero3 `parse_cif()` 함수 그대로 사용 → 117/117 파싱 성공
    - slot_count 분포: 1(51), 6(33), 4(12), 2(11), 8(4), 3(4), 5(2)
    - **4 hero CIF** (slot=8, cat=0): _H_001~004 (브라이언/디어드리/크리스탈/+ 한명)
    - category 0..28 (Hero3 의 0/1/2 만 비교 시 대폭 확장 — quest item / weapon / armor 세분화 추정)
    - 도구: [tools/converter/parse_h4_cif.py](../../tools/converter/parse_h4_cif.py)
    - JSON: `work/h4/converted/cif_parsed.json`
    - 문서: [docs/h4/formats/cif.md](formats/cif.md) (신규)

23. **🌟 CIF animation_data stride = Hero3 와 완전 동일**
    - hero (slot=8): **41-byte fixed stride** per frame entry (Hero3 hero stride 동일)
      - _H_001 = perfect 41B + 15B prologue fit (2170 frames)
      - _H_002/003/004 = 41B + 31~40 byte trailing footer
    - enemy/NPC (slot=1~6): **4-byte cell stream** (Hero3 boss/enemy stride 동일)
      - **113 / 117 files** 가 4B 완벽 fit (오직 4 hero 만 41B)
    - 함의: Hero3 sprite/animation renderer → Phase C commonMain 이전 시 **Hero4 추가 코드 0줄** 로 작동
    - sprite slot pool: 1..51 범위 (50/51 사용, slot 51 미사용) — 51개 표준 sprite 슬롯

24. **🌟 CIF ↔ EXD 117/117 = 100% pairing**
    - 모든 _H_NNN_CIF 가 같은 NNN 의 _H_NNN_EXD 페어
    - EXD subtype 분포 (CIF class 기준):
      - hero/major_npc/enemy: 모두 subtype=3 (collision feet + sprite body box)
      - single_entity (slot=1): 33 subtype=3, 12 subtype=2, 1 subtype=1
    - JSON: `work/h4/converted/cif_exd_xref.json` (cross-reference 매트릭스)

25. **🔥 DES 암호화 파일 풀 확장 — 356 → ~400 파일** (Hero4 전체 트리 스캔)
    - 도구: [tools/recon/scan_h4_des_files.py](../../tools/recon/scan_h4_des_files.py)
    - SCN cipher sentinel 7개 (3b7af9a4..., 1b7559e5..., ef9c94a1..., c0f2daf7..., f7740f75..., 4655b8f3..., 38d18f6a...) 로 전체 1,809 파일 스캔
    - **CONFIRMED (sentinel match)**: 107 files
      - MAP/SC: 88 (이미 SCN 348 안에 포함)
      - HDAT: 7 (Group A 8개 중 _H_BH 만 sentinel 없음, 나머지 모두 매치)
      - **E/: 6** (NEW — `_BSDAT_0/1/2` 보스 스크립트 + `_ESDAT_0/1/2` 이벤트 스크립트, sentinel @offset 200/112)
      - **ITM/DAT: 5** (NEW — `_ITM_08`, `_ITM_13`, `_ITM_OPTION`, `_ITM_Q_REPAY_1`, `_ITM_REPAY_0`)
      - **NPC/: 1** (NEW — `PROBABILITY_DAT`)
    - **LIKELY (high-entropy 8B-aligned, no sentinel)**: 141 files
      - **ITM/DAT: 21 more** (전체 26 ITM/DAT 중 21개, sentinel 없지만 entropy 7.7+)
      - **NPC/: 6** (NEW — `_QUEST_0/1_DAT`, `_NPCUI_COMBINE_DAT_0/1/2`, `NPCUI_GUARDIANSHOP_DAT`)
      - **FR/: 3** (NEW — `_FR_BA`, `_FR_PL`, `_FR_SK` — FR_EN/SU 는 작아서 sentinel 미검출)
      - MAP/SC: 111 (already in 348)
    - **DES key 발견 시 unblocking pool**:
      ```
      350 SCN (348 enc + 2 plaintext) + 8 HDAT-A + 12 NEW confirmed + 30 NEW likely
      ≈ 400 파일 동시 복호화
      ```
    - 이는 이전 추정 356 보다 **44 파일 더 많음**. ITM (아이템 메뉴), E (보스/이벤트 스크립트), NPC (퀘스트), FR (?) 의 추가 복호화로 **퀘스트 시스템 + 보스 시스템 + 아이템 시스템 전부** 복원 가능.

이번 누적 발견 (총 25 항목): 1~21 + **CIF Hero3 parser 100% 호환 + Hero4 CIF stride 41B/4B + CIF-EXD pairing 100% + DES file pool 확장 ~400**.

자동 영역에서 남은 미해결 (모두 Phase B Ghidra 의존):
- sec[4+] event records 의 variable-length 내부 schema
- sec[3] state=40 의미
- _EXD count>1 entry 2+ 구조
- 51-slot sprite pool → OBJ asset 매핑 lookup table 위치
- hero CIF 41B frame entry 내부 field 의미 (Hero3 분석 결과 활용 가능)
- enemy CIF 4B cell stream opcode 의미 (Hero3 `FUN_00098ef8` 디코더 활용)
- DES key 자체 (1순위 차단)
