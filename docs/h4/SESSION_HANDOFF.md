# Hero4 Session Handoff — Round 96 종료, 다음 세션 시작 가이드

> **다음 세션 시작점**: 이 문서를 가장 먼저 읽기.
> R70-R75 누적 요약은 [`round70-75-summary.md`](round70-75-summary.md), R76-R96 은 각 round 문서.

## 🏆 Round 76-R96 누적 (2026-05-19 ~ 2026-05-20, 21 라운드 연속 자동 분석)

| R | 핵심 발견 | 문서 |
|---|---|---|
| R76A | weapon class × character mode 매핑 (7 → 4 dual + 3 single) | [round76-weapon-class-mapping.md](round76-weapon-class-mapping.md) |
| R76B | BSDAT body = stat block (R72 SCN bytecode 가설 정정) | [round76-track-b-bsdat-stat-block.md](round76-track-b-bsdat-stat-block.md) |
| R77 | BSDAT 49B stat field (HP/MP/lvl/gold 위치) | [round77-bsdat-stat-fields.md](round77-bsdat-stat-fields.md) |
| R78 | ESDAT 67B encounter layout + `0xff 0x3f` section marker | [round78-esdat-encounter-layout.md](round78-esdat-encounter-layout.md) |
| R79 | ESDAT outlier = multi-phase boss encounters | [round79-esdat-outliers.md](round79-esdat-outliers.md) |
| R80 | 73B phase + 6B inter-phase link (`0x47` signature + phase_id chain) | [round80-esdat-phase-link.md](round80-esdat-phase-link.md) |
| R81 | `_H_BH` = **2 영웅 × 2 mode** (R76 미해결 `_ITM_03` 사용자 해소) | [round81-hero-bh-resolved.md](round81-hero-bh-resolved.md) |
| R82 | 트랙 C: ITEMDROP + BASIC_SM + SD 상점 (101 tiered items) | [round82-itemdrop-shop.md](round82-itemdrop-shop.md) |
| R83 | REPAY/Q_REPAY/CASH 보상 테이블 6 파일 stride 식별 | [round83-reward-tables.md](round83-reward-tables.md) |
| R84 | `_ITM_OPTION` enchantment pool **51종** (클래스 보완 affix) | [round84-enchantment-pool.md](round84-enchantment-pool.md) |
| R85 | Quest reward 분리: Q_REPAY_0 = EXP, Q_REPAY_1 = gold (~11배) | [round85-quest-reward-distribution.md](round85-quest-reward-distribution.md) |
| R86 | `_H_SS` 환수(소환수) 시스템 발견 (베놈/헤지호그/그래비티/쇼커/세이프가드) | [round86-summon-system.md](round86-summon-system.md) |
| R87 | 환수 시스템 정밀화 — 5 logical skills × 5 환수 + 23B stat block field 의미 + global passive skill_id 91-94 | [round87-summon-stat-detail.md](round87-summon-stat-detail.md) |
| R88 | `_H_BS` + `_H_SA` 정밀화 — R86 stride 가설 정정 (5×27B / 40×24B). 5 환수 base stat + learn skill ID(6-20), 8 ability × 3 tier, 5 summon × 3 growth tier (value = tier × 10) | [round88-summon-progression.md](round88-summon-progression.md) |
| R89 | 23B stat block 통합 schema — 3 template (ACTIVE_ATTACK/DIVIDER/PASSIVE_TEMPLATE) × 4 PASSIVE subtype (SHIELD/STATUS_PROC/AURA/PASSIVE). R87 정정: damage byte[3-4] LE16, byte[5]가 subtype | [round89-statblock-schema.md](round89-statblock-schema.md) |
| R90 | Q_REPAY idx ↔ quest 1:1 매핑 확정 — idx 0-127 = 128 quest 직접 매핑 (경계 61→62 = _QUEST_0→_QUEST_1), 128-198 = 71 extra (52 repeatable + 8 mid + 11 endgame), 199 = sentinel | [round90-quest-reward-map.md](round90-quest-reward-map.md) |
| R91 | 보스 phase stat scaling 정량 — 4 outlier (좀비/오토마톤/소환된좀비/기갑병) 추출. 표준 보스 phase 0→final HP/ATK/DEF +20-25%, gold/EXP +25-30% 일관 ratio. 오토마톤 V-shape (phase 1 cinematic dip). enemy_class byte 도 phase 별 전환 | [round91-boss-phase-scaling.md](round91-boss-phase-scaling.md) |
| R92 | Summon dialogue corpus cross-ref — 252 파일/484KB 스캔. 5 환수 개별 이름은 catalog/item/shop NPC/tutorial 4 파일만, 환수 시스템 acquisition entry = `NPCUI_GUARDIANSHOP_DAT` (수호자 상점), tutorial = `n0124_scn` (베놈 예시), 보스 망각의 저주 catalog 외 0 hits | [round92-summon-dialogue-xref.md](round92-summon-dialogue-xref.md) |
| R93 | _H_SA group_id ↔ 5 환수 매핑 검증 — group 0=베놈/64=헤지호그/78=그래비티/38=쇼커/75=세이프가드 ordinal match 확정. 5 verification check 모두 통과 | [round93-sa-summon-map.md](round93-sa-summon-map.md) |
| R94 | _H_SA ability skill_id 카테고리 식별 — 8 skill_id = global skill_id 0-39 매핑 (`class×10+local`). S001 사격 5/8 (deepest tree), S000 양손검 0 | [round94-sa-ability-skill-map.md](round94-sa-ability-skill-map.md) |
| R95 | element byte[5]=2 검증 + R89 정정 — `_H_SS` 전용 5 hit, byte[5]=2 invariant = summon-exclusive subtype marker | [round95-active-attack-xref.md](round95-active-attack-xref.md) |
| **R96** | **★ Q_REPAY drop_id ↔ ITM 매핑 검증** — drop slot 구조 [ITM_file_id:1B][item_idx:1B][qty:1B] × 2 slot. 65 drop 중 55 (85%) DAT 직접 매핑 (가면/통행증/제련석/뇌격 등 quest-thematic 일치). drop_id 16/17/23 은 currency 추정 | [round96-q-repay-drops.md](round96-q-repay-drops.md) |

**Hero4 게임 데이터 자동 분석 ~99.99%+ 종결**. drop slot 구조 확정. 남은 자동 트랙은 죽음의 구, character skill schema, currency drop_id.

## ⏭ 다음 세션 — "영웅서기4 다음 진행해줘" 받으면

### Option 1: 정밀화 자동 트랙 (1-2h, 즉시 시작 가능)

1. ⭐ **drop_id 16/17/23 currency 가설 검증** (R96 후속)
2. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
3. **n0124_scn tutorial 전문 분석** (R92 후속)
4. **bonus_id=0 + tier_value 의미** (R94 후속)
5. **character class skill (S000-S003) stat block schema** (R95 후속)

### Option 2: 사용자 환경 트랙 (⛔ 자동 불가)

- **트랙 D: A1 영어 번역** — `ANTHROPIC_API_KEY` 필요, Claude Sonnet 4.6, ~$4 견적
- **트랙 E: Phase C Step 4d** — Compose MP UI 마이그레이션, 1-2주 큰 작업
- **트랙 F**: SMAF→OGG, Ghidra stat 정밀, iOS Mac

### Hero4 게임 메카닉 모델 (R87 까지 누적)

- **2 영웅 × 2 mode** = 4 character class slots
  - 티르: mode 0 (S000 양손검) / mode 1 (S002 마검)
  - 루레인: mode 0 (S001 사격 + `_ITM_03` 검 변종) / mode 1 (S003 단도+마법 = **소환사 class**)
- **5 환수 × 5 logical skills = 25 환수 스킬** (R87 확정)
  - 베놈 (독), 헤지호그 (반사), 그래비티 (슬로우), 쇼커 (스턴), 세이프가드 (회복)
  - 각 5 skills: basic_attack + ranged_status + effect_boost + aura + on_summon_buff
  - 환수 base stat 5-axis + 학습 skill ID 시퀀스 6-20 (R88 `_H_BS`)
  - 환수 성장 LE16 = tier × 10 (5 group × 3 tier, R88 `_H_SA`)
- **8 ability slots × 3 tier** (R88 `_H_SA`) — skill_id {12,13,15,16,18,21,22,37}
- **4 글로벌 소환사 패시브** (skill_id 91-94) — 마법력/교감도/체력/정신 강화
- **1 보스급 status** — 망각의 저주 (str=66, type=7)
- **51 enchantments** (HP/SP, 공격/방어, proc, 시스템, 클래스 보완)
- **128 quests** (R70: 메인 62 + 사이드 66) + **400+ reward records** (Q_REPAY EXP/gold)
- **88 boss + 471 일반 인카운터** (BSDAT 3-stage + ESDAT 67B/73B/multi-phase)
- **349 items / 129 weapons / 7 weapon classes / 17 tier levels**
- **35,752 dialogue lines** (R68 corpus)

---

## (R75 시점 이전 내용 — history) 30초 요약

**🏆 Round 75 종료 (2026-05-19)** — Hero4 자동 데이터 분석 거의 종결:
- **DES key 발견** = `J@IWO8N7` (R68, Hero5 mx_des_decrypt 변종)
- **407 파일 복호화** (SCN 350 + HDAT-A 8 + E/ITM/NPC/FR 49)
- **dialogue corpus = 35,752 entries** (R68)
- **40 skills × 4 character classes** (R69)
- **128 quests** (R70, 메인스토리 62 + 사이드 66)
- **4 hero stat blocks** 구조 (R71, 티르/루레인)
- **559 event/boss scripts** (R72, 인간 공화국 군대 unit)
- **349 detailed items + 148 descriptions** (R73+R74)
- **129 weapon stats** (R75, lvl 1→91 progression × 7 weapon classes × 17 weapons)
- **h4_catalog.json** = Android single source of truth (~65KB+)
- engine-core (KMM) + Hero4 wiring 완료 (Phase C Step 5)

## Round 76 즉시 시작 — 자동 가능 트랙

### 트랙 A ⭐: 캐릭터별 weapon class 매핑 (자동, ~1 hour)

R75 에서 7 weapon classes 발견 (_ITM_00-06 각 17 무기) + R69 의 4 character class (S000 양손검 / S001 사격 / S002 마검 / S003 단도마법) 매핑 필요.

가설:
- `_ITM_00` (dual ATK1/ATK2) → 양손검 (S000, **티르**)
- `_ITM_01-03` → 검 변종 3 종 (마검 S002 + ?)
- `_ITM_04-06` (single ATK) → 사격 (S001 **루레인**) / 단도 (S003) / 마법

검증 방법:
1. _ITM_04 ATK 패턴 vs S001 사격 스킬 damage 비교 (산탄/동시/급소사격)
2. _ITM_05/06 ATK 패턴 vs S003 단도마법 skill 비교
3. 무기 이름 (아렌/비스/...) 의 cross-reference (R72 BSDAT 등장 NPC 와 비교)

### 트랙 B: BSDAT body opcode dispatch (자동, ~2 hour)

R72 에서 BSDAT 88 entries (루칸/브리안 등) entry 구조 풀이. 각 entry 의 body bytes (~50-100B) 안에 SCN bytecode 유사 opcode 가 있을 가능성.

R69 의 `docs/h4/formats/scn.md` 의 opcode 0x01/0x0c/0xff 와 비교 + SCN disassembler (`tools/converter/disasm_h4_scn.py`) 재활용.

### 트랙 C: ITEMDROP / smith / shop dat 정밀 (자동, ~1 hour)

이미 R69 에서 `_ITEMDROP` (9 records × 8B) 발견. shop_dat / smith_dat 등 추가 dat 정밀 파싱.

### 트랙 D: A1 영어 번역 ⛔ (사용자 API key 필요)

corpus (35,752) + item descriptions (148) + quest text (128) + skill names (40) 등 모두 한국어 진본. Claude Sonnet 4.6 번역 비용 ~$4.09 (Hero3 R69 견적).

```bash
export ANTHROPIC_API_KEY=sk-...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

### 트랙 E: Phase C Step 4d (Compose MP UI 마이그레이션) ⏳

`docs/architecture/phase-c-step1-engine-core.md` 의 Step 4d. Hero3 + Hero4 양쪽 UI 를 Compose Multiplatform 으로. **1-2 주 큰 작업**.

### 트랙 F: 사용자 트랙 (수동/외부)

- SMAF → OGG 음성 변환 (`docs/h3/SMAF_pipeline.md` 가이드)
- Ghidra stat field 정밀 (`_H_BH` 40B 의 정확한 stat 의미)
- iOS 출시 (Phase D, Mac 필요)

## 산출물 위치 (R68-R75 누적)

### 복호화 데이터

| 경로 | 내용 |
|---|---|
| `work/h4/decrypted/SC/*_scn` | 350 SCN (348 decrypt + 2 plaintext) |
| `work/h4/decrypted/HDAT/_H_*` | 8 HDAT-A (battle/shop/zone) |
| `work/h4/decrypted/E/_BSDAT_*` `_ESDAT_*` | 6 event/boss script |
| `work/h4/decrypted/ITM/DAT/_ITM_*` | 26 item data |
| `work/h4/decrypted/NPC/*` | 7 NPC scripts (PROBABILITY/NPCUI/QUEST) |
| `work/h4/decrypted/FR/_FR_*` | 3 battle frames |

### 변환 catalog

| 파일 | 내용 |
|---|---|
| `work/h4/converted/dialogue_corpus.json` | 35,752 dialogue lines (R68) |
| `work/h4/converted/dialogue_top_texts.json` | top 200 빈도 |
| `work/h4/converted/hdat_a_parsed.json` | HDAT-A 8 파일 entry catalog (R69) |
| `work/h4/converted/h4_quests.json` | 128 quests (R70) |
| `work/h4/converted/h4_hero_stats.json` | 4 hero stat blocks 구조 (R71) |
| `work/h4/converted/h4_event_scripts.json` | 559 event/boss entries (R72) |
| `work/h4/converted/h4_items_detailed.json` | 349 items + 148 desc + 129 weapon stats (R73-R75) |
| **`work/h4/converted/h4_catalog.json`** | **★ 통합 single source of truth** |

### Android 자산 배포 (`apps/hero4-android/app/src/main/assets/`)

- `h4_catalog.json` (61KB+)
- `h4_quests.json` (37KB)
- `h4_hero_stats.json` (5KB)
- `h4_event_scripts.json` (115KB)
- `h4_items_detailed.json` (확장됨)
- 기타 sprites/ 496 PNG + 기존 자산

### 신규 도구 (R68-R75)

| 도구 | 라운드 |
|---|---|
| `tools/recon/find_h4_des_key_v5.py` | R68 — DES key 발견 |
| `tools/converter/decrypt_h4_scn.py` (갱신) | R68 — mx-des default |
| `tools/converter/decrypt_h4_all_des.py` | R69 — 49 파일 batch |
| `tools/converter/parse_h4_hdat_a.py` | R69 — HDAT-A entry layout |
| `tools/converter/build_h4_catalog.py` | R69+ — catalog 빌더 |
| `tools/converter/parse_h4_quests.py` | R70 — quest parsing |
| `tools/converter/parse_h4_hero_stats.py` | R71 — hero stat block |
| `tools/converter/parse_h4_event_scripts.py` | R72 — BSDAT/ESDAT |
| `tools/converter/parse_h4_items_detailed.py` | R73-R75 — items + desc + weapon stats |

### 문서

| 문서 | 라운드 |
|---|---|
| `docs/h4/round68-des-key-discovered.md` | R68 |
| `docs/h4/round69-skill-catalog-and-batch-decrypt.md` | R69 |
| `docs/h4/round70-75-summary.md` | R70-R75 통합 (이 세션) |
| `docs/h4/PROGRESS.md` | 메인 핸드오프 |
| `docs/h4/SESSION_HANDOFF.md` | 이 문서 |

## Phase C (engine wiring) 진행 상황

- ✅ Step 1 (`9c096c40`) engine-core 모듈 + 12 pure Kotlin files
- ✅ Step 2 (`5e511839`) GameStateView interface
- ✅ Step 3 (`4b5e056d`) KMM 전환 (Android AAR + JVM JAR)
- ✅ Step 5 (`7a82cdb9`) Hero4 가 engine-core 의존 + h4_catalog 로더 PoC
- ✅ Step 4a (`ffc90c6a`) AppSettings interface
- ✅ Step 4b+4c (`6aceb993`) AssetReader interface (Hero4 catalog loader 가 사용)
- ⏳ **Step 4d** = Compose MP UI 마이그레이션 (가장 큰 작업, ~1-2 주)
- ⏳ Step 6 = iOS (Apple Silicon Mac 필요)

상세는 [`../architecture/phase-c-step1-engine-core.md`](../architecture/phase-c-step1-engine-core.md) + [`project_phase_c.md`](../../../../Users/viewe/.claude/projects/c--gameRemake-testrepo/memory/project_phase_c.md).

## 진행률 갱신 (R75 시점)

| 영역 | R67 (R68 직전) | R75 |
|---|---|---|
| 자산 포맷 분석/변환 | ~95% | **~100%** (모든 DES 풀림) |
| 대사 corpus 한국어 | 0% garbage | **100%** (35,752 entries) |
| 게임 시스템 데이터 | 0% | **~90%** (스킬/아이템/quest/weapon/event/boss 분류 완료) |
| 암호화 시스템 | ~70% (key 미발견) | **100%** (407 파일 전체 복호화) |
| Phase A | 99% | **100%** |
| Phase B (Ghidra) | 30% | 30% (선택적, stat field 정밀화에만 필요) |
| Phase C (KMM) | 0% | **75%** (Step 1+2+3+4a/4b/4c+5 완료, Step 4d만 남음) |
| Phase D (iOS) | 0% | 0% (Mac 환경 필요) |

**Hero4 Android remake 완성 기준**: 약 **55-65%** (자산+데이터+엔진 결합 완료, UI/scene wiring 만 남음)

## 핵심 lesson 누적

1. **Cross-game vendor analysis 가 Ghidra 보다 빠름** (R68): Hero3 R57 + Hero5 h5_des.py 가 cipher 변종 풀어둠 → Hero4 R68 즉시 해결
2. **DES key 발견 즉시 모든 sentinel-공유 파일 검증** (R69): 49 파일 49 hit
3. **공통 패턴 반복**: Hero3 + Hero4 가 같은 entry 구조 사용 (`[size][00][nlen][name][body]`) — Hero3 R58 quest_dat 패턴 그대로 Hero4 quest/event/item 에 적용
4. **Field offset 의미 정정**: R73 LE16[0]=price 가설 → R74 검증 (LE32 overflow 회피 → LE16 유지) → R75 byte[6]=level/byte[9]=ATK1 등 정밀화
5. **가설 자주 정정**: R73 "캐릭터 starting equip" → R75 "weapon class 7종" 정정
