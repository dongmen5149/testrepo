# Hero4 Round 100+ 밀레스톤 결산 (R68–R109)

> R68–R109 **42 라운드** 누적 — Hero4 데이터 RE 의 거의 종결 (~95% → ~99%) + 게임 메카닉 모델 확정.
> 본 문서는 R110 결산용. 일별 라운드 상세는 [PROGRESS.md](PROGRESS.md), 즉시 재개는 [SESSION_HANDOFF.md](SESSION_HANDOFF.md).
> 완성도 4지표·베타 정의는 [COMPLETION.md](COMPLETION.md) (R109+: 데이터 RE **~99%** · 베타 **~12–18%**).

---

## 1. 누적 변화 (R68 시작 → R109 종료)

| 카테고리 | R68 시작 | R109 종료 | Δ | 주요 라운드 |
|---|---|---|---|---|
| A. 암호화 / 복호화 | 0% | **100%** | **+100** | R68 DES key J@IWO8N7 발견 + 49 파일 batch |
| B. 자산 파일 포맷 | 30% | **98%** | +68 | R68-R69 SCN/HDAT/E/ITM/NPC/FR 모두 식별 |
| C. 대사 corpus | 0% | **100%** | **+100** | R68 35,752 dialogue 추출 |
| D. 게임 데이터 RE (JSON catalog) | 5% | **99%** | **+94** | R69-R109 42 라운드 누적 |
| E. 게임 메카닉 모델 | 5% | **97%** | +92 | R86-R109 환수/2모드/alt-form/type=0 sub-cat |
| F. KMM engine-core | 50% | **75%** | +25 | Step 1-5+4a/b/c 완료, **4d Compose MP UI ⏳** |
| G. Android 플레이 런타임 | 5% | **5%** | — | catalog 텍스트 PoC만, 씬·전투·맵 미구현 |
| H. 베타 QA·릴리즈 | 0% | **0%** | — | 실 디바이스 빌드·플레이 없음 |
| **종합 (베타 정의)** | **~5%** | **~15%** | **+10** | 데이터 99% 와 별도 |
| **데이터·RE 트랙만** | **~30%** | **~99%** | **+69** | 본 milestone 의 main subject |

→ 가장 큰 임팩트 영역: **A (+100%p)** DES 풀림 / **D (+94%p)** catalog 정밀화 / **E (+92%p)** 게임 모델 확정.

---

## 2. 카테고리별 주요 마일스톤

### A. 암호화 (100% — R68 종결)
- ✅ DES key `J@IWO8N7` 발견 (Hero3 R57 + Hero5 mx_des_decrypt 변종 활용, Ghidra 우회)
- ✅ 49 파일 sentinel-shared batch decrypt 검증 100%
- ✅ R68-R75 408 파일 복호화 (SCN 350 + HDAT 8 + E/ITM/NPC/FR 49 + plaintext 2)

### B. 자산 포맷 (98%)
- ✅ SCN 350 (대사·이벤트·맵) — `tools/converter/decrypt_h4_scn.py` + opcode 디스어셈
- ✅ HDAT-A 8 (battle/shop/zone) — entry layout `[size][00][nlen][name][body]`
- ✅ HDAT 환수 시스템: `_H_SS` / `_H_SA` / `_H_BS` / `_H_BH`
- ✅ BSDAT/ESDAT (event/boss script) — R76B body=stat block + R77 49B field
- ✅ ITM/DAT 26 + NPC 7 + FR 3
- ❌ SMAF audio (.mmf) — 디코더 부재 (사용자 트랙)

### C. 대사 corpus (100% — R68 종결)
- ✅ 35,752 dialogue lines 추출 (EUC-KR)
- ✅ `dialogue_corpus.json` + `dialogue_top_texts.json`
- ✅ Round 92/108 cross-ref 으로 환수 시스템 도입 경로 확정 (NPCUI_GUARDIANSHOP_DAT + n0124_scn)

### D. 게임 데이터 RE (99% — R69-R109 종결)
주요 catalog 산출물:

| 카테고리 | 라운드 | 결과 |
|---|---|---|
| 4 character class × 16 skill | R69, R101-R103 | 64 skill = 40 primary + 24 alt-form (S000 양손검 / S001 사격 / S002 마검 / S003 마법) |
| 128 quest | R70, R90, R96 | 메인 62 + 사이드 66, Q_REPAY idx 0-127 1:1 매핑, drop slot [file_id:1][idx:1][qty:1]×2 |
| 4 hero stat blocks | R71, R81 | _H_BH = 2 영웅 × 2 mode = 4 character slot |
| 559 event/boss script | R72, R78-R80, R91, R98 | BSDAT 88 entries + ESDAT 471 (67B 표준 + 73B phase + 6B link + 72B time-limited boss) |
| 349 items / 129 weapons / 7 weapon classes / 17 tier | R73-R75, R76A | _ITM_00-06 무기 class × 17 무기/class |
| Item drop / shop / reward | R82, R83, R85 | ITEMDROP + BASIC_SM + SD 상점 101 tier items + Q_REPAY EXP/gold |
| 51 enchantments | R84, R106 | _ITM_OPTION 1928B = 6B hdr + 122 entries × 3B `[effect_id][cat][mag]` |
| 5 환수 시스템 | R86-R88, R92-R95, R99 | 베놈/헤지호그/그래비티/쇼커/세이프가드, 25 환수 skill + 8 ability × 3 tier + 4 글로벌 패시브 |
| 88 boss + phase scaling | R79, R80, R91 | 4 outlier (좀비/오토마톤/소환된좀비/기갑병) +20-25% HP/ATK ratio |
| Death sphere boss | R98, R107 | pos[63-64] LE16 = seconds (600/480/360 = 10/8/6분) |
| Q_REPAY drop currency | R96, R97, R105 | drop_id 16=CASH_RANOMBOX / 23=REPAY_2 / 17=OPTION × qty 1000 (endgame) |
| Tier-bonus / damage type | R100, R102, R104 | byte[5] enum 0=MAGIC (54) / 5=WEAPON_BASIC (7) / 20=DEBUFF (2) / 25=SPECIAL (1) |
| Class skill schema | R101, R102, R109 | 32B field 정밀 + type=0 11 sub-category (PASSIVE/BUFF/COMBO/DEBUFF 등) |
| Alt-form mode-2 | R103, R108 | 24 alt-form = mode-2 advanced (환수 합신/특공/증폭 + 환수흡수/흡혈환수 = mechanic-only, dialogue 0) |

### E. 게임 메카닉 모델 (97% — R86–R109 종결)
R109 확정 4 character class design philosophy:

- **티르 (Tyr)**:
  - mode 0 = S000 양손검 (물리 + DEBUFF + WEAPON_SPECIAL) — 4 dtype 모두 보유
  - mode 1 = S002 마검 (ELEMENT/DASH/COMBO with 환수 융합 시작)
- **루레인 (Lurain)**:
  - mode 0 = S001 사격 (장거리 + BUFF + TRAP, dual-weapon)
  - mode 1 = S003 마법 (DEBUFF/AOE/환수 시스템 핵심 = 소환사 class)

확정 system:
- 5 환수 × 5 logical skill = 25 환수 skill + 4 글로벌 패시브 (skill_id 91-94)
- 8 ability × 3 tier (`_H_SA`, group_id ↔ 5 환수 ordinal match)
- 17 tier × 7 weapon class = 129 무기 stat progression (lvl 1→91)
- 88 boss + 471 일반 인카운터 + 1 time-limited boss (죽음의 구)
- 51 enchantment × 3 magnitude (cat 0/15/100)
- 128 quest + 199 reward record (Q_REPAY EXP/gold + sentinel)

### F. KMM engine-core (75%)
- ✅ Step 1 engine-core 모듈 + 12 pure Kotlin
- ✅ Step 2 GameStateView interface
- ✅ Step 3 KMM 전환 (Android AAR + JVM JAR)
- ✅ Step 4a AppSettings interface
- ✅ Step 4b+4c AssetReader interface
- ✅ Step 5 Hero4 catalog loader PoC
- ⏳ **Step 4d Compose MP UI 마이그레이션** — 1-2주 큰 작업 (베타 핵심)
- ⏳ Step 6 iOS (Apple Silicon 필요)

### G. Android 플레이 런타임 (5% — 미시작)
- ✅ `apps/hero4-android` — catalog 텍스트 PoC
- ✅ h4_catalog.json (61KB+) + sprites/ 496 PNG + assets/ 전체
- ❌ 원작 240×320 UI · 스프라이트 · 맵 렌더 0%
- ❌ SCN/퀘스트 진행기 0%
- ❌ 전투 / 환수 / 2모드 / alt-form / 인챈트 런타임 0%

### H. 베타 QA·릴리즈 (0%)
- ❌ 실 디바이스 빌드·플레이 0%
- ❌ 본편 구간 플레이 QA 0%
- ❌ Play 내부 트랙 0%
- ❌ SMAF→OGG 음성 변환 0%
- ❌ 영어 번역 0% (Sonnet 4.6, 견적 ~$4)

---

## 3. 잔여 큰 덩어리 (R110+ 우선순위)

### 자동 가능 트랙 (남은 정밀화)

1. **Spirit/skill 정밀 byte→field 매핑** — type=0 sub-cat (R109) 까지 도달했으나 stat block 32B field 의 일부 byte 는 미확정
2. **alt-form × type=0 cross-check** (R103 + R109 후속) — 24 alt-form 의 sub-category 분포 검증
3. **environmental scripts** — n0124_scn 외 환수 시스템 secondary tutorial 검색
4. **SCN opcode dispatch 정밀** — R72 BSDAT body opcode 와 SCN bytecode 매핑

### 사용자 환경 의존 트랙 (자동 불가)

1. ⭐ **트랙 E: Phase C Step 4d** — Compose MP UI 마이그레이션 (베타 핵심, **1-2주 큰 작업**)
2. **원작 UI 맵+전투 빌드** — Hero3 씬 스택 이식 + MapWalk/Battle/Dialogue
3. **SCN·퀘스트 진행기** — 350 SCN / 128 quest 를 런타임과 연결
4. **트랙 D: A1 영어 번역** — `ANTHROPIC_API_KEY` 필요, ~$4
5. **SMAF→OGG** + iOS (Apple Silicon)

→ **데이터 RE 천장**: 추가 자동 라운드로 +0.5-1.0%p 정도 (R109 시점에서 거의 한계).
→ **베타 100% 까지**: 위 사용자 트랙 4개 모두 + 본편 QA → 베타 ~15% → ~90%+ 도약 가능.

---

## 4. R68–R109 라운드 라인업 (42 라운드)

### Foundation (R68-R75) — 분석 인프라
```
R68  DES key J@IWO8N7 발견 + 35,752 dialogue
R69  4 class × 40 skill catalog + 49 batch decrypt
R70  128 quest (메인 62 + 사이드 66)
R71  4 hero stat blocks (티르/루레인 mode 구조)
R72  559 event/boss script (BSDAT/ESDAT/NPC unit)
R73  349 items detailed
R74  148 item descriptions (LE32→LE16 overflow 정정)
R75  129 weapon stats × 17 tier × 7 class
```

### Item / encounter (R76-R85) — 카탈로그 깊이
```
R76A weapon class × character mode 매핑 (7→4 dual + 3 single)
R76B BSDAT body = stat block (R72 SCN bytecode 가설 정정)
R77  BSDAT 49B stat field (HP/MP/lvl/gold)
R78  ESDAT 67B encounter + 0xff 0x3f section marker
R79  ESDAT outlier = multi-phase boss
R80  73B phase + 6B inter-phase link (0x47 + phase_id chain)
R81  _H_BH = 2 영웅 × 2 mode (R76 _ITM_03 해소)
R82  ITEMDROP + BASIC_SM + SD 상점 (101 tiered items)
R83  REPAY/Q_REPAY/CASH 보상 6 파일 stride
R84  _ITM_OPTION enchantment pool 51종
R85  Quest reward 분리: Q_REPAY_0 EXP, Q_REPAY_1 gold (~11배)
```

### Summon system (R86-R99) — 환수 cluster
```
R86  _H_SS 환수 시스템 (5 환수)
R87  5×5 환수 skill + 23B stat block + global passive 91-94
R88  _H_BS + _H_SA 정밀화 (5×27B / 40×24B)
R89  23B stat block 통합 schema (ACTIVE/DIVIDER/PASSIVE)
R90  Q_REPAY idx ↔ quest 1:1 매핑 (128 + 71 extra + sentinel)
R91  보스 phase stat scaling 정량 (4 outlier +20-25%)
R92  Summon dialogue corpus cross-ref (5 환수 = 4 파일만)
R93  _H_SA group_id ↔ 5 환수 매핑 검증
R94  _H_SA ability skill_id 카테고리 (global skill_id 0-39)
R95  element byte[5]=2 검증 + R89 정정
R96  Q_REPAY drop_id ↔ ITM (55/65 DAT 매핑)
R97  drop_id 16/17/23 currency 검증 (17 ambiguous)
R98  죽음의 구 72B = time-limited boss (pos[63-64] LE16)
R99  n0124_scn 환수 tutorial + R86-R88 catalog 1:1
```

### Class skill / damage (R100-R107) — 메카닉 정밀
```
R100 tier_value/bonus_id semantic (R94 ambiguity 해소) ★ 마일스톤
R101 character class skill schema (4×16 = 64)
R102 32B class skill field 정밀
R103 24 alt-form mode 매핑 (mode-2 advanced + 환수 combo)
R104 damage_type enum (0/5/20/25)
R105 drop_id 17 byte10=232 정정 (LE16=1000 endgame)
R106 _ITM_OPTION 1928B 구조 (6B hdr + 122 entries × 3B)
R107 죽음의 구 timer 단위 확정 (600/480/360 = 초 = 10/8/6분)
```

### Final polish (R108-R109) — design model 확정
```
R108 환수 combo skill dialogue 부재 확정 (catalog-only, mode-2 mechanic-only)
R109 type=0 (54 skill) 11 sub-category — 4 class design philosophy
```

---

## 5. 핵심 RE 종결 사실 (이후 라운드 재참조용)

### 데이터 구조

- **DES key** = `J@IWO8N7` (R68, Hero5 mx_des_decrypt 변종)
- **HDAT entry layout** = `[size][00][nlen][name][body]` (Hero3 R58 quest_dat 패턴 그대로)
- **BSDAT body** = 49B stat block (HP/MP/lvl/gold, R76B/R77)
- **ESDAT layouts** = 67B 표준 encounter / 73B phase / 6B inter-phase link / 72B time-limited boss
- **_H_BH** = 2 영웅 × 2 mode = 4 character class (티르 0/1, 루레인 0/1)
- **_H_SS** = 5 환수 × 5 logical skill × 23B stat block (R86-R89)
- **_H_SA** = 40 ability × 24B = 8 ability × 3 tier × 5 환수 (R88)
- **_ITM_OPTION** = 1928B = 6B header + 122 entries × 3B `[effect_id][cat 0/15/100][mag]` (R106)
- **Q_REPAY drop slot** = `[ITM_file_id:1B][item_idx:1B][qty:1B]` × 2 slot, qty 0xE8 (R97) = LE16=1000 (R105)
- **죽음의 구 timer** = pos[63-64] LE16 seconds (600/480/360 = 10/8/6분, R98+R107)

### 게임 메카닉

- **4 character class skill schema** = 32B × 16 entry × 4 file = 64 skill = 40 primary + 24 alt-form (R101)
- **damage_type byte[5]** = 0 MAGIC (54, 84%) / 5 WEAPON_BASIC (7) / 20 DEBUFF (2) / 25 SPECIAL (1) (R104)
- **type=0 11 sub-category** = PASSIVE 16 + BUFF 10 + ELEMENT 5 + AOE 5 + COMBO 4 + DEBUFF 3 + DASH 3 + BASIC 3 + TRAP 2 + MULTI 2 + STATUS 1 (R109)
- **alt-form = mode-2 advanced variant** — MP 1.5× higher, lvl_req mid-tier, 환수 combo 포함, dialogue 노출 0 (R103+R108)
- **환수 시스템 = side-mechanic** — 메인 시나리오 (62 quest) 와 독립, NPCUI_GUARDIANSHOP_DAT 상점 + n0124_scn tutorial 외 story 노출 0 (R92+R99+R108)

### 인프라

- **Hero3 + Hero4 catalog pattern 공통**: `[size][00][nlen][name][body]` entry — Hero3 R58 → Hero4 R69 직접 이식
- **Cross-game vendor analysis > Ghidra**: Hero3 R57 + Hero5 h5_des.py 가 cipher 변종 풀어둠 → Hero4 R68 즉시 해결
- **자동 라운드당 평균**: 42 라운드 / 데이터 RE 30% → 99% = **+1.65%p / 라운드**
- **가설 정정 사이클**: R73 "starting equip" → R75 "weapon class" / R86 stride → R88 / R94 ambiguity → R100 / R102 schema → R109 sub-cat

---

## 6. Hero3 / Hero5 와의 대비

| 작품 | 데이터/RE | 베타 오픈 정의 % | 비고 |
|------|-----------|-------------------|------|
| **Hero3** | ~99.98% | **~97–98%** | 22 씬 + 전투 + 맵 + 퀘스트 + 133 tests |
| **Hero5 (Godot)** | ~96% | **~87%** | R82-R108 18+ 라운드 implementation |
| **Hero4** | **~97–99%** | **~12–18%** | 본 문서 — **데이터 RE 종결, 베타 미시작** |

→ Hero4 는 **데이터 RE 트랙은 Hero3 와 동급**, **베타 트랙은 Hero5 와 비교 시 ~70%p 차이**.
→ 차이의 본질 = Phase C Step 4d (Compose MP UI) + 원작 UI 이식 + 본편 QA.

---

업데이트: 2026-05-20 (R110 milestone 결산 작성, R68–R109 누적 42 라운드).
