# Hero3 (영웅서기3-운명의수레바퀴) Master Spec

> Round 56-70 누적 발견. Android 리메이크가 단일 reference 로 사용. 출처 = `work/h3/game_balance.json` v1.1 (582KB) + R56-R69 recon 산출물.
>
> **이 문서가 Hero3 리메이크 개발자의 권장 entry point**. 코드 구현 시 이 spec 을 그대로 참조.

## 0. 게임 시스템 한눈 요약

| 영역 | 개수 / 상태 | 출처 |
|---|---|---|
| **플레이어 캐릭터** | 2 주인공 × 5 클래스 = 10 playable | R59 |
| **NPC** | 78 NPCs | R59 |
| **적** | 161 normal + 161 hard (4 exp 그룹) | R56 / R69 |
| **보스** | 15 normal + 15 hard (16 story + 14 misc) | R58 / R65 |
| **무기 class** | 7 (창/대검/단검/건/라이플/다크석/홀리석) | R59 |
| **skill** | 7 class × 15 = 105 (7 passive + 8 active per class) | R60 |
| **active_attack skill** | 24 (24 중 9 debuff 보유, 4 ultimate) | R61 / R66 |
| **item** | 18 카테고리 × 480+ items = 529 total | R60-R63 |
| **rarity** | 6 prefix (magic/legendary/epic/boss_drop/endgame/quest_reward) + normal | R62 |
| **stat enum** | 24 codes (실제 사용 22, 0x14/0x19 unused) | R63 / R65 |
| **퀘스트** | 44+ across 4 files | R58 |
| **지역** | 8 main regions | R58 |
| **string table** | 246 UI strings (InGame_txt 196 + menu 50) | R60 |
| **dialogue** | 9,740 unique Korean (~34K chars) | R57 / R69 |
| **DES 파일** | 8 pending (사용자 환경 필요) | R57 |

## 1. Master Stat Enum (24 codes, 실제 사용 22)

| code | name | i12 ring | i13 buff (low byte) | i16 enchant | equip trailer | skill debuff | context |
|---:|---|---|---|---|---|---|---|
| 0x00 | ATT1_BASE | — | — | 뇌제의 | — | — | i16 무기 공격력 강화 only |
| 0x01 | HP_HEAL_INSTANT | — | 자비의손길 | — | rare | — | i13 즉시 HP 회복 |
| 0x02 | HP_MAX | — | 오우거의의지 | 투신의 | ✓ | — | HP 최대치 |
| 0x03 | HP_REGEN / BLEED | 회복의반지 | 승리의염원 | 공명의 | ✓ | 암영/직격 | i13=buff, skill 음수=bleed |
| 0x04 | SP_MAX | 데몬의뿔 | 잠재의식 | — | rare | — | SP 최대치/회복 |
| 0x05 | ATT1 (물공) | 힘의반지 | 끓어오르는피 | — | ✓ | 망각 | UI: 힘 / internal: ATT1 |
| 0x06 | ATT2 (특공) | 정신의반지 | 악마의속삼임 | — | ✓ | 망각 | UI: 정신 / internal: ATT2 |
| 0x07 | P_DEF (물방) | 체력의반지 | 철벽의가드 | 금강의 | ✓ | 전율 | UI: 체력 |
| 0x08 | M_DEF (특방) | 히드라/배리어 | 오로라의장벽 | 정령의 | ✓ | 전율 | M_DEF (마법/총기) |
| 0x09 | ACC | 콘돌/백발백중 | 사냥꾼의눈 | 사신의 | ✓ | 압도/격광 | 명중률 |
| 0x0a | DOD | 민첩의반지 | 시간의지배자 | 영제의 | ✓ | 전율 2차 | UI: 민첩 |
| 0x0b | BLOCK | 기사/프로텍트 | 용자의가호 | 철벽의 | ✓ | **유도 (+5 자기 buff)** | 방패방어율 |
| 0x0c | CRI_RATE | 독사의이빨 | — | 속박의 | ✓ | — | 크리티컬 발생율 |
| 0x0d | CRI_DEF / **STUN_RESIST_DEBUFF** | — | — | 결의의 | ✓ | **위협 (skill 컨텍스트)** | i13/equip=CRI_DEF, skill=기절저항 감소 |
| 0x0e | SP_COST_REDUCE | 총명의반지 | — | 현자의 | ✓ | — | 스킬 SP 소모 감소 |
| 0x0f | SP_REGEN | 지혜의반지 | — | 마도의 | ✓ | — | SP 회복속도 |
| 0x10 | HP_DRAIN | 카오스/데몬 | — | 흡혈의 | ✓ | — | 공격시 HP 흡수 |
| 0x11 | CD_REDUCE | 헤이스트/자칼 | 질풍노도 | 폭풍의 | ✓ | — | 스킬 쿨타임 감소 |
| 0x12 | SHIELD_PIERCE | 맹공/샤프니스 | — | 직격의 | ✓ | — | 방패 무시 |
| **0x14** | (unused) | — | — | — | — | — | R63/R65: completely unused |
| **0x15** | **TAUNT** (R66 신규) | — | — | — | — | **유도** | 적의 공격을 자신에게 집중 |
| 0x16 | BUFF_REMOVE | — | 망각의향 | — | — | — | 능력치 증가 해제 |
| 0x17 | CURE_STATUS | — | 혼의외침 | — | — | — | 상태이상 회복 |
| **0x19** | (unused) | — | — | — | — | — | R63/R65: completely unused |
| 0x1c | REVIVE / **STUN_TRIGGER** | — | 피닉스의숨결 | — | — | **참혼/저격** | i13=REVIVE, skill val=0=STUN |

### 1.1 value scale 규칙

| source | scale | examples |
|---|---|---|
| **i12 ring** | flat | 힘의반지 +8 = ATT1+8 |
| **i16 enchant** | flat (tail[1] magnitude) | 투신의 = HP+5 |
| **equip trailer** | flat (byte v1, v2) | $아레스실드 (0x01, 10) = bonus 10 |
| **i13 HP/SP heal** | flat (HP/SP delta) | 자비의손길 +600 HP |
| **i13 stat buff** | **ratio %** | 끓어오르는피 +40% ATT1 |
| **i13 적 대상 debuff** | **signed int16 음수** (65506=-30, 65486=-50) | 드래곤피어 -30 HP_MAX |
| **i18 HP potion** | flat (4 tier 200/600/1500/3000) | 포션 +200 HP |
| **i18 SP potion** | ratio×10 (200=20%, 500=50%) | 과일쥬스 +20% SP |
| **i18 special** | boolean (value=0) | 귀환서 / 피닉스의숨결 |
| **skill +0x14..+0x17 debuff** | **LE16+LE16 signed** | 망각 ATT1(-3,-2) ATT2(-10,-2) |

## 2. Rarity Prefix System (R62)

| prefix | name | color | modifier_armor | modifier_weapon |
|---|---|---|---:|---:|
| (none) | normal | gray | 1.00 | 1.00 |
| `\|` | magic | blue | 1.13 | 1.01 |
| `'` | legendary | gold | 1.06 | 1.00 |
| `$` | epic | purple | 1.15 | 0.93 |
| `{` | boss_drop | orange | 1.50 | **0.03** (사실상 무료 loot) |
| `@` | endgame | red | 1.00 | 1.00 |
| `}` | quest_reward | green | 0.00 | 0.00 |

→ **stat-driven, not price-driven**: 무기 boss_drop 가격 = 무료. armor magic 13% bonus, epic 15% bonus.

## 3. Item Catalog (18 카테고리, 529 items)

### 3.1 카테고리 매핑

| i# | category | n | layout |
|---:|---|---:|---|
| 0 | 헬멧 (helmet) | 33 | equip20 |
| 1 | 갑옷 (armor) | 41 | equip20 |
| 2 | 장갑 (gloves) | 37 | equip20 |
| 3 | 신발 (shoes) | 38 | equip20 |
| 4 | 창 (spear) | 25 | equip20 |
| 5 | 대검 (great sword) | 25 | equip20 |
| 6 | 단검 (dagger) | 25 | equip20 |
| 7 | 건 (pistol) | 25 | equip20 |
| 8 | 라이플 (rifle) | 25 | equip20 |
| 9 | 다크석 (dark magic stone) | 25 | equip20 |
| 10 | 홀리석 (holy magic stone) | 25 | equip20 |
| 11 | 방패 (shield) | 22 | equip20 |
| 12 | 반지 (ring) | 40 | ring18 |
| 13 | 패시브스크롤 (i13) | 35 | consumable |
| 14 | 조합재료 (i14) | 46 | text-only |
| 16 | enchant 옵션 | 15 | enchant |
| 17 | 퀘스트 아이템 | 21 | text-only |
| 18 | 소비 (potion 등) | 26 | consumable |

(i15 = 7400B DES, master item table 추정 — 사용자 환경 필요)

### 3.2 equip20 layout (20-byte body)

```
+0..1   LE16  price (Gold cost)
+2..3   pad
+4      tier index (0..7)
+5      variant (sprite index, 0xff default)
+6..7   pad
+8      required level
+9..11  pad
+12..13 LE16 stat_primary (DEF for armor, ATT for weapon)
+14..15 LE16 stat_secondary (sub-stat or zero)
+16..19 trailer (4B) — 51% of equips have (bonus_type, value, bonus_type2, value2)
```

### 3.3 무기 base damage (per tier)

| weapon | base ATT | scaling | 비고 |
|---|---:|---|---|
| 창 (i4) | 43 | +10/tier | 7 tier |
| 대검 (i5) | 51 | +12/tier | 양손, 큰 데미지 |
| 단검 (i6) | 47 | +11/tier | 빠름 |
| 건 (i7) | 40 | +10/tier | 피스톨, 0x1f marker |
| 라이플 (i8) | 59 | +13/tier | 가장 강함 |
| 다크석 (i9) | 60 | +13/tier | 마법 |
| 홀리석 (i10) | 45 | +9/tier | 가장 약함 but 회복 보조 |

## 4. Skill System (7 weapon × 15 skill = 105)

### 4.1 카테고리 구조 (per weapon class)

```
weapon_passive (7) — tier 1-7 마스터리 자동 적용
active_attack (3)   — 공격 active skill
active_buff (2)     — 자기/파티 강화 buff
passive_bonus (3)   — 영구 stat bonus
```

### 4.2 skill body layout (30-byte tail)

```
+0x00..+0x01  LE16   SP cost (100/200/300/400/500/600/800 = 7 tier)
+0x02..+0x03  pad
+0x04         byte   primary damage base
+0x05         byte   secondary damage base (combo)
+0x06         pad
+0x07         byte   utility marker (0x14 for utility)
+0x08         pad
+0x09..+0x0a  byte pair  animation timing / sprite frames
              (85,85) = utility skill, (41,41) = 단검 1체, weapon-specific else
+0x0b         byte   range/AoE radius (20 단검 / 30 창 / 40 검·마법 / 80 라이플 / 100 utility)
+0x0c         byte   weapon flag (1 attack, 31 gun marker s7 전용, 0 utility)
+0x0d         byte   hit flag (1 HIT_PHYSICAL, 0 no hit)
+0x0e..+0x1c  effect chain (right-justified):
                slot1 pos 14..18, slot2 pos 19..23, slot3 pos 24..28
                각 slot = (1 byte debuff code, LE16 primary, LE16 secondary)
                0x7f = sentinel (no debuff)
+0x1d         byte   rank / power class
                일반 active: 1-4
                ultimate: 5-15 (단검 난무 r15, 건 난사 r10, 라이플 연쇄·다크 나락 r5)
                weapon_passive: 1-5
```

### 4.3 skill debuff chain (R66/R69)

```
distinct debuff codes (11): 0x03 BLEED / 0x05 ATT1 / 0x06 ATT2 / 0x07 P_DEF /
                            0x08 M_DEF / 0x09 ACC / 0x0a DOD /
                            0x0b BLOCK (유도 양수=자기 buff) /
                            0x0d STUN_RESIST_DEBUFF (위협 컨텍스트) /
                            0x15 TAUNT (유도) / 0x1c STUN_TRIGGER (val=0)

chain length 분포 (24 active_attack):
  0 debuffs (raw damage): 14 — ultimate 포함 (난무/난사/연쇄/나락)
  1 debuff: 6 — 참혼/암영/저격/직격/위협/격광
  2 debuffs: 3 — 압도/유도/망각
  3 debuffs: 1 — 전율 (P_DEF + M_DEF + DOD)
```

### 4.4 ultimate skill (4)

| weapon | name | rank | SP | damage_base | n_debuffs | desc |
|---|---|---:|---:|---:|---:|---|
| 단검 (s6) | 난무 | 15 | 600 | 120 | 0 | 적 1체에게 모든 기술 연속 |
| 건 (s7) | 난사 | 10 | 600 | 80 | 0 | 무차별 사격 (0x1f marker) |
| 라이플 (s8) | 연쇄 | 5 | 400 | 120 | 0 | 반동 활용 주변 타격 |
| 다크석 (s9) | 나락 | 5 | 500 | 104 | 0 | 지옥 공간 소환 지속 |

→ 모두 raw damage only (debuff 0), utility skill 은 normal active 가 담당.

## 5. Enemy System

### 5.1 enemy_dat 19B stat block

```
+0x00         lvl (byte)
+0x01..+0x03  pad
+0x04..+0x05  variant/ID (scaling 1.04x = 변동 없음, sprite or AI variant)
+0x06..+0x07  MP_max or secondary (scaling 2.71x median)
+0x08..+0x09  EXP_high or Gold_tier (scaling 3.84x median, group별 분리)
+0x0a..+0x0b  HP_max (BE16, R60 확정, scaling 2.22x stable)
+0x0c..+0x0d  HP_cur or base (scaling 3.00x)
+0x0e..+0x0f  EXP_main (scaling 6.92x median — group별 9.7x or 1.80x)
+0x10         ATK (byte, scaling 2.93x)
+0x11         AGI/DOD (byte, +2 constant boost)
+0x12         pad
```

### 5.2 enemy 2B trailer

```
[0] difficulty marker:  0x01 normal / 0x02 hard / 0x05 cross-mode / 0x00 sentinel
[1] encounter type:     0x1e standard battle (126/161=78%) / 0xff special/scripted (35)
```

### 5.3 4 exp_gold scaling groups (R70)

| group | n | pattern | example |
|---|---:|---|---|
| **9.7x** | 41 | normal ~800 → hard ~7,700 | standard combat (가드/워리어/템플러) |
| **1.8x** | 22 | normal ~6,400 → hard ~11,500 | scout/rogue (로그/체이서/말벌) |
| **stable** | 16 | normal ≈ hard ≈ 2,600 (no change) | boss/special encounter (`{` prefix 다수) |
| **other** | 82 | 다양 | gunners/skeletons/creatures |

→ implicit "enemy tier" 시스템. Android 리메이크 enemy spawn 균형용.

## 6. Boss System (15 × 2 difficulty)

### 6.1 boss 6-byte trailer

```
[0] combat rating
    공식: rating = round(lvl/2 + 44) normal / round(lvl/2 + 64) hard
    의미: "challenge equivalence level" = 권장 player level

[1] sprite/model index (8 distinct, sprite asset 재사용)
    리츠=0, 케이=1, 멜페토=2, 큐=3, 시즈타이탄=0, 아르보르=1, 오르도=2, 벨루스=3, 홀리가디언=4

[2..5] 4 boss skill slot IDs
    Story boss (16 entries): 1..20 range, 보스별 unique combination
    Misc boss (14 entries): 0xFF×4 (no scripted skill)

    distinct IDs: {1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 19, 20}
    매핑 미해결 (DES 8 파일 복호화 후 확정 가능)
```

### 6.2 boss roster

| boss | family | sprite | tier 1/2 trailer | tier 3 trailer |
|---|---|---:|---|---|
| 리츠 | 어쌀트워리어 | 0 | (3, 2, 1, 2) | (19, 13, 9, 9) |
| 케이 | 버서커 | 1 | (2, 2, 1, 1) | (20, 14, 10, 8) |
| 멜페토 | (tier 4) | 2 | — | (9, 3, 3, 7) |
| 큐 | (tier 4) | 3 | — | (7, 8, 5, 9) |
| 벨루스/시즈/아르보르/오르도/홀리가디언 | misc | 0-4 | 0xFF×4 | 0xFF×4 |

## 7. Crafting System (i14 → 7 카테고리)

### 7.1 weapon-class crafting map

| weapon | base material | 고대 재료 (3 tier) | 클래스 문장 |
|---|---|---|---|
| 창/대검/단검 (s4/5/6) | 연마가루 | 아르세네스 / 뮤제게네스 / 바스테네스 | 아벨 (전사) |
| 권총/라이플 (s7/8) | **탄성제** | 데비그린 / 오헨그린 / 큐브그린 | 시몬 (총기) |
| 다크석/홀리석 (s9/10) | 정령석 | (스톤/총기 공유) | 포프 (마법) |

### 7.2 7 카테고리

```
1. 공통 용액 (3): 붉은/푸른/투명
2. 공정 재료 (6): 제련석, 연마가루, 정령석, 탄성제, 강화제, 질긴섬유
3. 원소 속성 (4): 바람피리, 만년설, 혈목, 흑암석
4. 몬스터 드롭 (15): 쥐가죽, 박쥐날개, 라이칸이빨 등
5. 고대 재료 3 tier × 4 type (12):
   투구/갑옷: 에스텔시아/카메루시아/헤게네시아 (금속)
   장갑/신발: 그리톤/시르톤/아케톤 (가죽)
   물리무기/방패: 아르세네스/뮤제게네스/바스테네스 (제련석)
   스톤/총기: 데비그린/오헨그린/큐브그린 (정령석)
6. 클래스 강화 문장 (5):
   아벨(전사), 시몬(총기), 포프(마법), 부폰(방어), 하피(회피)
```

## 8. Quest System (44+, 4 files)

- quest_00_dat (4851B) — 메인퀘스트
- quest_01_dat (4216B)
- quest_10_dat (5360B)
- quest_11_dat (4269B)

i17 (21 quest items) ↔ quest_*_dat 매칭 20/21 (R62). 매칭 1개 = 반토막난 지도 (튜토리얼 시작).

## 9. Asset Catalog (R57)

```
dat/des_dat            — DES 알고리즘 테이블 (824B FIPS, 평문 포함)
dat/InGame_txt         — 196 UI 텍스트 (i18n)
dat/i0~i18             — 18 item 카테고리 (i15 = DES)
dat/enemy_dat          — 161 enemies (5495B)
dat/enemyh_dat         — 161 hard mode enemies
dat/enemyg_dat         — enemy graphics (3542B, 22 byte/entry sprite info)
dat/char_dat           — 10 playable classes (R59)
dat/quest_*_dat        — 4 quest files
dat/drop_dat (DES)     — enemy 드롭 테이블
dat/droph_dat (DES)    — hard 드롭
dat/getitem_dat (DES)  — fixed drops
dat/smith_dat (DES)    — smith 레시피
dat/smithh_dat (DES)   — hard smith
dat/shop_dat (DES)     — 상점 카탈로그
dat/shoph_dat (DES)    — hard 상점
boss/boss_dat          — 15 bosses (508B)
boss/bossh_dat         — 15 hard bosses
skill/s4~s10_dat       — 7 weapon class skill files (105 skills)
npc/npcg_dat           — 78 NPCs graphics (1014B, 13 byte/entry)
menu/*_txt             — 50 menu UI strings
event/e000X_scn        — 350 dialogue SCN files (9,740 unique Korean)
```

## 10. DES System (R57)

- algorithm: standard FIPS DES (ECB-like, see Hero5 NDK runner)
- key: `"0EP@KO91"` (binary @0xac594)
- tables: `dat/des_dat` (824B FIPS, IP/IP⁻¹/E/P/S1-S8/PC1/PC2 모두 평문)
- pending: 8 files (i15/drop/droph/getitem/smith/smithh/shop/shoph)
- blocker: 사용자 환경 NDK runner 필요 (`reference_h5_des_blocker.md` 참고)

## 11. Region Map (8 main, R58)

- 네메시스숲 (시작 지역)
- 네오솔티아 (홈 도시)
- 협곡
- 아스크라 (적국)
- 엔자크사막
- 토레즈 (광산도시)
- 로우엔 평원
- 리파이너의 유적 (최종 던전)

## 12. Hero3 핵심 게임 디자인 통찰

### 12.1 stat enum 의 다중 사용

- 동일 24-code stat enum 이 4 소스 (i12 ring + i13 buff + i16 enchant + equip trailer + skill debuff) 에서 공유
- 컨텍스트별 의미 분리:
  - 0x03: HP_REGEN (i13 양수) vs BLEED (skill 음수)
  - 0x0d: CRI_DEF (i13/equip) vs STUN_RESIST_DEBUFF (skill)
  - 0x1c: REVIVE (i13) vs STUN_TRIGGER (skill val=0)
- value 부호로 buff/debuff 구분 (signed int16)

### 12.2 weapon class 차별화

- **창/대검/단검** (s4/5/6): standard melee, P_DEF/ATT1 위주
- **건/라이플** (s7/8): ammo 시스템 공유 (탄성제), 0x1f marker = s7 사거리/조준 모드 표시
- **다크석/홀리석** (s9/10): 마법, ATT2 (특공) 위주, 스톤/총기 정령석 4 class 공유

### 12.3 ultimate vs utility 역할 분리

- ultimate (rank 5-15): raw damage only
- normal active (rank 1-4): debuff / utility / TAUNT / STUN trigger
- 유도 (창 1-rank) = 자기 BLOCK +5 + TAUNT 동시 = 탱커 능력

### 12.4 boss tier progression

- tier 1/2 (lvl 14/24): 약한 skill ID 사용 (1-3)
- tier 3 (lvl 32): 강한 skill ID 사용 (9-20)
- combat_rating 공식: `round(lvl/2 + 44|64)` — challenge equivalence

### 12.5 enemy tier (exp_gold grouping)

- 9.7x group: 일반 전투
- 1.8x group: 정찰/고급
- stable group: 보스/특별 (difficulty 와 무관)
- other: 다양 카테고리

## 13. Android 리메이크 권장 구현 순서

1. **engine-core** (Phase C Step 1-5 완료): pure Kotlin engine, GameStateView interface
2. **data loader**: `work/h3/game_balance.json` (582KB) 또는 dat 파일 직접 파싱
3. **stat system**: 24-code enum + value scale 규칙 구현
4. **item system**: 18 카테고리 + rarity prefix + equip trailer bonus pair
5. **skill system**: 30-byte tail layout + effect chain (slot1/2/3) + ultimate sentinel
6. **enemy/boss system**: 19B stat block + 6B boss trailer + combat_rating formula
7. **i18n**: 246 UI strings + 9,740 dialogue (LLM 번역 후)
8. **DES decryption** (사용자 환경 의존): drop/smith/shop 테이블
9. **audio**: SMAF→OGG 33 files

## 14. R56-R69 round-by-round 진행 요약

| round | 핵심 발견 | 진행률 |
|---:|---|---|
| R56 | enemy_dat 161 entries × 19B | ~70% |
| R57 | DES 시스템 + key `0EP@KO91` + 25 dat path strings | ~70% |
| R58 | boss_dat / quest_*_dat 평문 파싱 + DES variant 실패 | ~72-75% |
| R59 | char_dat (10 클래스) + npcg_dat (78) + s4_dat | ~75-78% |
| R60 | skill 7 파일 일괄 + boss HP @+0x0a..+0x0b + item 17 파일 + i15_dat 신규 DES | ~82-85% |
| R61 | item body 정밀 (20B equip / 18B ring / variable consumable) + i13/i14 식별 | ~86-89% |
| R62 | item trailer = bonus pair (177/346) + rarity 7 prefix + skill rank @+0x1d + i17 quest xref | ~88-91% |
| R63 | master stat enum 100% (i16 enchant desc Rosetta Stone) + R61 가설 5건 정정 | ~91-94% |
| R64 | game_balance.json v1.0 (537KB) + value scale + 0x14/0x19 미사용 | ~94-96% |
| R65 | skill effect mask + boss 6B trailer + signed 검증 (R64 정정) | ~96-97% |
| R66 | debuff code 정밀 (별도 enum → stat enum 동일) + skill effect v2 + boss combat_rating | ~97-98% |
| R67 | skill header 14B + enemy 2B trailer + boss skill 가설 H1-H4 | ~98-99% |
| R68 | gun marker 0x1f (s7 unique) + boss skill 검색 + FUN_4f358 재확인 | ~99% |
| R69 | i14 ammo 정정 (s7+s8 공유) + enemy stat scaling + dialogue queue ($4.09) | ~99.3% |
| **R70** | **이 master spec 통합 + exp_gold 4 그룹** | **~99.5%** |

## 15. 참고

- 모든 round docs: `docs/h3/ghidra-round*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
- master data: `work/h3/game_balance.json` (582KB v1.1)
- 모든 recon output: `work/h3/recon/*.{json,log}`
- SESSION_HANDOFF.md — 다음 세션 가이드
- PROGRESS.md — 전체 진행 히스토리
