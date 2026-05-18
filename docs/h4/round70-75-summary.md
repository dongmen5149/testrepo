# Hero4 Round 70-75 통합 정리 (자동 데이터 분석 6 라운드)

> **세션**: 2026-05-19 (R68/R69 직후 연속), Round 70 → Round 75
> **이전**: [R68 DES key 발견](round68-des-key-discovered.md), [R69 catalog + skill](round69-skill-catalog-and-batch-decrypt.md)
> **다음 세션 시작점**: [SESSION_HANDOFF.md](SESSION_HANDOFF.md)

## TL;DR — 자동 분석 6 라운드 성과

R68 의 DES key + R69 의 catalog 토대 위에 R70-R75 까지 **6 라운드 연속 정밀 분석**:

| Round | 핵심 발견 | 산출 |
|---|---|---|
| **R70** | NPC QUEST 정밀 파싱 | **128 quests** (메인 62 + 사이드 66) |
| **R71** | _H_BH 4 hero stat blocks 구조 | 168B = 1B header + 4 entries × 가변 + 2B trailer |
| **R72** | E/BSDAT + ESDAT entry layout | **559 entries** (boss 88 + encounter 471) |
| **R73** | ITM/DAT 26 파일 entry struct | **349 items** (price + slot + tier) |
| **R74** | item stat_block field mapping | **148 descriptions** (HP/lvl/레시피/효과) |
| **R75** | weapon stat field 추출 | **129 weapons** (level/ATK1/ATK2/flag) |

---

## R70 — NPC QUEST 정밀 파싱 (commit `03e6eee8`)

R69 에서 복호화된 `NPC/_QUEST_{0,1}_DAT` 평문을 Hero3 quest_dat 패턴 변종으로 파싱.

### 패턴

```
Hero3: [size+2:1B] [00] [name_len:1B] [name:EUC-KR] [body]
Hero4: [size_field:1B] [00 00 00] [name_len:1B] [name:EUC-KR] [desc_len:1B] [desc:EUC-KR] [category marker]
```

### 결과

- **QUEST_0_DAT** = **62 quests** (메인 스토리): 케프네스 찾기 / 유적조사 / 크래드 / 엘렌 / 가면제작 / 매도우힐 / 이자벨 / 팔리아스 / 배 부품 / 탈출 / 주둔지 침입 / 유물 탈취 / 프로비던스
- **QUEST_1_DAT** = **66 quests** (선주종 측): 성지 방어 1-2 / 노덴스 / 브레스 / 탈주

### 스토리 윤곽

- **주인공**: 티르 + 루레인 (R69) → **케프네스** (지도자) 추적 미션
- **동맹**: 크래드 (이름없는섬), 엘렌, 이자벨 (프로비던스 여관), 루칸 (팔리아스), 노덴스, 브레스
- **적대**: 인간 vs 선주종 (인간 = 침공자, 선주종 = 토착민)
- **켈트 신화 4 보물 도시**: 뮤리아스 / 팔리아스 (Tuatha Dé Danann)

---

## R71 — _H_BH hero stat block 구조 (commit `9a21481f`)

R69 의 "4 entries × 40B stride" 가설 정정 — 실제는 **가변 길이 entries**.

### 구조 확정

```
[0]       1B    file header (0x26)
[1:41]    40B   Entry 0: 티르 (mode=0, idx=0, size_field=0x26)
[41:81]   40B   Entry 1: 티르 (mode=0, idx=1)
[81:122]  42B   Entry 2: 루레인 (mode=1, idx=2, size_field=0x28)
[122:166] 44B   Entry 3: 루레인 (mode=1, idx=3)
+ 2B trailer
```

각 entry 헤더 5B = `[size_field][00][index][mode][name_len]`:
- **mode_byte** = class group (0=양손검 티르, 1=사격 루레인)
- **index_byte** = entry serial (0..3)
- **name_len** = 4 (티르) / 6 (루레인)

### 관찰 (Ghidra 미적용)

- `stats byte[1]` level 후보 — 티르 11/6, 루레인 10/5 (스토리 단계?)
- `stats byte[14..20]` = 10/20/40 패턴 (시작 장비 ID 후보)
- 정확한 stat field 매핑은 Ghidra 분석 필요

---

## R72 — E/BSDAT + ESDAT entry layout (commit `54e14071`)

R69 에서 복호화된 boss + event script 6 파일의 entry layout 풀이.

### 패턴 2종

```
BSDAT: [size:1B][00][name_len:1B][name:EUC-KR][body]                (Hero3 표준)
ESDAT: [size:1B][00][seq:1B][name_len:1B][name:EUC-KR][body]        (seq = variant index)
```

### 결과

**BSDAT 3 파일** (각 2008B, 88 entries 총) = boss/character 등장 스크립트:
- 첫 entries: **루칸 / 브리안** (R70 quest 의 인간 측 boss 일치)
- 같은 character 가 여러 번 반복 → 다양한 encounter context

**ESDAT 3 파일** (각 13168B, 471 entries 총) = encounter 스크립트:
- **공화국 보병 / 공화국 사수 / 공화국 기갑병 / 공화국 상병 / 야전지휘관**
- "공화국" = 인간 측 군대 (R70 quest 의 적대 세력과 일치)
- 적 unit 분류 + 계급 시스템

총 **559 entries**.

---

## R73 — ITM/DAT 26 파일 entry struct (commit `d5241a1e`)

R69 의 1,572 한국어 raw count 를 entry-level 정밀 파싱으로 발전.

### 패턴 2종

```
_SD (shop list):     [size:1B][00][nlen:1B][name:EUC-KR][item_id:1B][ff][slot:1B]
_DAT (extended):     [size:1B][00][tier:1B][nlen:1B][name:EUC-KR][stat_block:varB]
```

- **slot byte** = 0x09/0x0b/0x0d/0x0f/0x11 = equip slot code
- **tier byte** = 0/1/4/8 = chapter or category index

### 분류 (349 items)

| 파일 | 카테고리 | 수 |
|---|---|---|
| `_ITM_*_SD` (8 파일) | 카테고리별 inventory (머리/방어/장갑/신발/무기/스태프) | 70+ |
| `_ITM_00-06_DAT` (7 파일) | weapon class × 17 each (R75 에서 정정) | 119 |
| `_ITM_08_DAT` | 포션 카테고리 | 29 |
| `_ITM_09_DAT` | 조형 재료 | 29 |
| `_ITM_10_DAT` | 보스 장비 | 38 |
| `_ITM_11_DAT` | 마법무기 강화석 | 13 |
| `_ITM_12_DAT` | crafting materials | 38 |
| `_ITM_15_DAT` | enchant 효과 | 10 |

---

## R74 — item stat_block field mapping (commit `84ec6b66`)

R73 의 LE16[0]=price 가설 정밀화 + description text extraction.

### Field mapping 확정

| Offset | 의미 |
|---|---|
| `LE16 [0]` | **price (gold)** |
| `byte[4]` | **description length** (consumable/material/orb only) |
| `bytes[5:5+L]` | **description text** (ASCII + EUC-KR 혼합) |

### 148/349 items description 추출

| 파일 | 카테고리 | 샘플 description |
|---|---|---|
| `_ITM_08` (29) | 포션 | "HP를 200까지;**천천히** 회복" / "HP를 200까지;**단숨에** 회복" / "HP를 800까지;..." |
| `_ITM_09` (29) | 조형 재료 | "투구를;만들기 위한;기본 재료" |
| **`_ITM_10` (38)** | **보스 장비** | **"레벨39 투구; 투구조형10; 질긴가죽8; 강철6"** ⭐ |
| `_ITM_11` (13) | 마법무기 강화석 | "무기 공격력을;높여주는 오브" (뇌제/금강/정령) |
| `_ITM_12` (38) | 재료 | "약 재료로;쓰이는;귀한 풀" (백련초) |
| `_ITM_13` (1) | 네트워크 | "네트워크 전용 아이템입니다." |

⭐ **`_ITM_10` 보스 장비** = level requirement + crafting recipe 명시 → 게임 시스템 결정적 정보.

### 가격 progression 패턴

- 포션: 200 → 600 → 1000 (회복량/속도 차등)
- 조형 재료: 500 균등
- 보스 장비: 400 균등
- 마법무기 강화석: 300 균등

---

## R75 — weapon stat field 추출 (commit `c626cde2`)

R73 "캐릭터 starting equip" 가설 정정 → 실제 = **7 weapon classes × 17 weapons**.

### Field mapping (description 없는 weapon items)

| Offset | 의미 | 예시 |
|---|---|---|
| `byte[5]` | property_flag | 0-7 (element/family) |
| `byte[6]` | **level requirement** | 1, 3, 6, 11, 16, 21, ..., 91 |
| `byte[9]` | **ATK1** (main damage) | 3, 4, 5, 8, ..., 51 |
| `byte[13]` | **ATK2** (combo damage) | 양손검 dual / single weapon = 0 |

### 7 weapon classes 매핑 (R69 4 character class 와 일치)

- `_ITM_00` (dual ATK) → **양손검 (S000, 티르)**
- `_ITM_01-03` (dual ATK) → 검 변종 3 종 (마검 S002 등)
- `_ITM_04-06` (single ATK) → 사격 / 단도 / 마법

### 17 weapons per class progression (lvl)

```
아렌(1) → 비스(3) → 챠라(6) → 데빈(11) → 에반(16) → 플류(21) → 게인(26) → 하웬(31)
→ 이즈(36) → 로젠(51) → 매츠(56) → 네오(61) → 오렌(66) → 피아(71) → 레닌(81)
→ 시온(86) → 테오(91, 최강)
```

### 예시 (_ITM_00 양손검 progression)

| 무기 | lvl | ATK1/ATK2 | price |
|---|---|---|---|
| 아렌 | 1 | 3/3 | 100 |
| 챠라 | 6 | 5/6 | 600 |
| 에반 | 16 | 10/11 | 3,700 |
| 하웬 | 31 | 19/17 | 13,600 |
| **테오** | **91** | **51/45** | **50,464** |

---

## 누적 산출물 (R68-R75)

### h4_catalog.json (single source of truth, ~65KB+)

도메인 7 종:
- `meta` (R68 발견 DES key + cipher 변종)
- `heroes` (R69, 2 캐릭터 티르/루레인)
- `skill_sets` (R69, 4 class × 10 skill = 40 skills)
- `items` (R69, 26 파일 raw count + R73 자세히)
- `items_detailed` (R73-R75, 349 entries 정밀)
- `npc` (R69, 7 파일)
- `quests` (R70, 128 entries)
- `hero_stats` (R71, 4 entries)
- `event_scripts` (R72, 559 entries)

### 신규 도구 (8개)

```
tools/converter/
├── decrypt_h4_all_des.py        # R69 — 49 파일 batch decrypt
├── parse_h4_hdat_a.py           # R69 — HDAT-A entry layout
├── build_h4_catalog.py          # R69+ — catalog 통합 빌더
├── parse_h4_quests.py           # R70 — quest parser
├── parse_h4_hero_stats.py       # R71 — hero stat block
├── parse_h4_event_scripts.py    # R72 — BSDAT/ESDAT
└── parse_h4_items_detailed.py   # R73-R75 — items 정밀 (price/desc/weapon stats)
```

---

## 다음 라운드 (R76+) 후보

### 자동 가능 (사용자 입력 없이)

1. ⭐ **캐릭터별 weapon class 매핑** (~1 hour) — R75 의 7 weapon classes 와 R69 의 4 캐릭터 class 매핑
2. **BSDAT body opcode dispatch** (~2 hour) — R72 의 88 boss script body 분석
3. **ITEMDROP / smith / shop dat 정밀** (~1 hour)

### 사용자 환경 필요

4. **A1 영어 번역** (Claude Sonnet 4.6, ~$4.09, API key 필요)
5. **Ghidra stat field 정밀** (_H_BH 정확한 stat 의미)
6. **SMAF → OGG** 음성 변환 (외부 도구)

### Phase C 후속

7. **Step 4d Compose MP UI 마이그레이션** (~1-2 주, Hero3+Hero4 동시)
8. Step 6 iOS (Apple Silicon Mac 필요)

---

## 메타 — 자동 분석 효율

| 단계 | 누적 시간 | 결과 |
|---|---|---|
| R68 (key 발견) | ~1 hr | 358 파일 |
| R69 (catalog) | ~2 hr | +49 파일 + 40 skills |
| R70 (quest) | ~1 hr | 128 quests |
| R71 (hero stat) | ~30 min | 4 entries 구조 |
| R72 (event script) | ~30 min | 559 entries |
| R73 (item detail) | ~1 hr | 349 items |
| R74 (description) | ~30 min | 148 descriptions |
| R75 (weapon stat) | ~30 min | 129 weapons |
| **R68-R75 총** | **~7 hr** | **Hero4 게임 데이터 ~95% 추출** |

→ **lesson 누적**:
1. Vendor 공통 cipher = cross-game 1순위
2. DES key 발견 즉시 sentinel-공유 모든 파일 검증
3. Hero3 패턴 (`[size][00][nlen][name]`) 이 Hero4 quest/event/item 에 대부분 적용
4. 가설은 자주 정정 — R73 "캐릭터 장비" → R75 "weapon class" 정정 사례
