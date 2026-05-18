# Round 64 — game_balance.json 통합 출력 + value scale + ultimate skill diff (2026-05-19)

> 이번 라운드 목표: R56-R63 의 모든 recon 산출물을 **Android 리메이크용 single source of truth** 로 통합 (`game_balance.json`). 추가로 value scale (flat vs ratio) 분석, 0x14/0x19 미사용 코드 추적, ultimate skill byte diff 수행.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **`work/h3/game_balance.json` 생성 (537KB, schema v1.0)** — stat enum + items + skills + enemies + bosses + quests + char + DES status 모두 통합
- ⭐⭐⭐⭐ **value scale 매핑 확정** — i12/i16/equip trailer = flat / i13 stat buff = ratio% / i13 HP·SP heal = flat / i18 HP heal = flat / i18 SP heal = ratio×10
- ⭐⭐⭐ **signed int16 debuff value 발견** — i13 `드래곤피어 65506` = `-30` (HP 최대치 감소), `사막의폭염 65486` = `-50` (방어력 감소). 모든 적용 대상 디버프가 음수 LE16 인코딩
- ⭐⭐⭐ **0x14 / 0x19 = i*_dat / s*_dat 의 stat enum 으로는 미사용** — i13/i16/i17 에 0회 출현 확인. equip trailer 에는 출현 (R62 의 bonus pair 후보로 잔존)
- ⭐⭐⭐ **Ultimate skill sentinel byte 발견 — `+0x13 = 0x7f`** — 4개 ultimate 모두 보유, normal active skill 은 다양 (28/206/253 등). `+0x14..0x1c` = ultimate-only effect mask 후보

## 1. game_balance.json 스키마 (★★★★★)

`work/h3/game_balance.json` (537,438B, schema v1.0) — Android 리메이크가 직접 import 가능한 master 데이터.

```
{
  "meta":       {round:64, date:"2026-05-19", schema_version:"1.0", items_categories:18, ...},
  "stat_enum":  { 0x00..0x1c: {name, desc, from} },        // R63 master
  "rarity":     { prefix → {name, modifier_armor, modifier_weapon} },  // R62
  "items":      { i0~i18: {category, n_items, items:[...]} },   // 529 items total
  "skills":     { s4~s10: {weapon, n_skills, rank_info, skills:[...]} },   // 105 skills
  "enemies":    { normal:[...], hard:[...] },     // 161 × 2
  "bosses":     { normal:[...], hard:[...] },     // 15 × 2
  "quests":     { files: {...}, item_xref: {...} },
  "char_classes": [{name1, weapon_byte, ...}],    // 10 playable classes
  "des_status": { algorithm, key, pending_files:[8] }
}
```

### 1.1 items enrichment (R64 신규)

각 item 에 `rarity` (R62 prefix detect) + `clean_name` (prefix 제거) 필드 추가:

```json
{
  "pos": 27,
  "name": "|레인저슈트",
  "clean_name": "레인저슈트",
  "rarity": "magic",
  "layout": "equip20",
  "price": 600,
  "tier": 1,
  ...
}
```

i0_dat 헬멧 rarity 분포 예: `boss_drop=3, endgame=2, epic=2, legendary=5, magic=8, normal=12, quest_reward=1`.

### 1.2 enemies/bosses 19B stat interpretation (R60 적용)

R60 의 boss HP 검증 결과로 `+0x0a..+0x0b BE16 = MaxHP` 확정. enemy_dat / bossh_dat 모두 동일 layout.

```json
{
  "name": "리츠1",
  "stats": {
    "lvl": 14, "hp_max": 1200, "hp_cur": 1200, "exp_gold": 1200,
    "f4_5": 30, "f6_7": 30, "f8_9": 200, "f16": 5, "agi_or": 8, "f18": 0
  },
  "stat_block_hex": "0e 00 00 00 ...",
  "trailer_hex": "01 1e ... (boss 6B variable)"
}
```

## 2. value scale 분석 (★★★★) — `work/h3/recon/value_scale.json`

### 2.1 통합 매핑

| source | 적용 시점 | value 의미 | 예 |
|---|---|---|---|
| **i12 ring** | 영구 (장착) | **flat stat bonus** | 힘의반지 +8 = ATT1+8 |
| **i16 enchant** | 영구 (결합) | **flat magnitude** (tail[1]) | 투신의 tail=`02 05 ..` = HP+5 |
| **equip trailer** | 영구 (장착) | **flat (R62)** | (bonus_type, value) 페어 |
| **i13 HP/SP heal (high 0x01/0x04)** | 임시 (사용) | **flat HP/SP delta** | 자비의손길 +600 HP |
| **i13 HP_MAX (high 0x02)** | 임시 (사용) | **flat HP+** | 오우거의의지 +30 HP |
| **i13 HP_REGEN (high 0x03)** | 임시 (사용) | **flat regen+** | 승리의염원 +60 regen |
| **i13 stat buff (high 0x05-0x12)** | 임시 (사용) | **ratio %** | 끓어오르는피 ATT1 +40% |
| **i13 debuff (적대상)** | 임시 (사용) | **signed int16 음수** | 드래곤피어 -30 (65506=-30 LE16) |
| **i18 HP potion (low 0x12-0x15)** | 즉시 | **flat (200/600/1500/3000)** | 4 tier |
| **i18 SP potion (low 0x16-0x18)** | 즉시 | **ratio (×10)** | 과일쥬스 200=20%, 포도주 500=50% |
| **i18 special (low 0x19-0x1c)** | 즉시 | **boolean** (value=0) | 귀환서 / 부활서 |
| **i13 status (high 0x16/0x17/0x1c)** | 즉시 | **boolean** (value=0) | 망각의향 / 혼의외침 / 피닉스의숨결 |

### 2.2 effect_type low byte = target/duration enum

| low | name | 의미 |
|---:|---|---|
| 0x02 | self_temp | 사용자 단일 (일정시간 buff/debuff) |
| 0x03 | target_inst | 대상 즉시 효과 |
| 0x04 | party_temp | 파티 전체 (일정시간) |
| 0x12-0x15 | heal_t1..t4 | HP heal flat tier |
| 0x16-0x18 | sp_t1..t3 | SP heal ratio×10 |
| 0x19 | revive | 전투불능 회복 (boolean) |
| 0x1a | town_return | 귀환서 (boolean) |
| 0x1b | town_warp | 그리폰의피리 (boolean) |
| 0x1c | special | 오브원석 / 피닉스의숨결 (boolean) |

### 2.3 디버프 signed int16 인코딩 발견 ★★★

R64 새 발견: i13 의 적 대상 디버프 (드래곤피어 / 사막의폭염 / 머메이드의노래 / 아레스의구름 / 결박하는대지) 의 effect_value 가 **65506 / 65486 / 65486 / 65506 / 65506** 으로 일정 패턴:

```
65506 = 0xFFE2 = -30 (signed int16)
65486 = 0xFFCE = -50
```

→ 모든 디버프가 **signed int16 음수값** 으로 인코딩. Android 리메이크 구현 시 `(int16_t)value` 캐스팅 필수.

## 3. 0x14 / 0x19 미사용 코드 추적 (★★★) — `work/h3/recon/unused_codes.json`

### 3.1 결과 요약

| code | i13_dat | i16_dat | i17_dat | i18_dat | equip trailers | binary literal pool |
|---:|---:|---:|---:|---:|---|---:|
| **0x14** | 0 | 0 | 0 | 1 | 출현 (i0/i1/i2 등) | 11 word-aligned |
| **0x19** | 0 | 0 | 0 | 3 | 출현 | 5 word-aligned |

### 3.2 결론

- **0x14, 0x19 는 i13/i16/i17 의 stat enum 으로는 사용 안 됨** — R63 추정 "미식별" 확정
- 단 equip trailer 에는 출현 → **R62 의 bonus pair (177/346 equip 의 trailer 4B) 의 잔존 후보 stat code**
- binary literal pool aligned 11회 (0x14) / 5회 (0x19) — switch table entry 일 가능성 (FUN_4f358 본문 정밀 후속 작업)
- enemy/boss/quest 의 random byte 출현은 통계적 noise (수천 byte 중 수십회)

**가설 (잔존)**:
- 0x14 = boss-specific stat (예: STATUS_RESIST) — boss trailer 의 6B 가변 영역에 출현 가능
- 0x19 = 보조 effect flag (raid-only or PvP-only)

R65 후속: equip trailer 의 177 case 의 bonus_type 분포를 0x14/0x19 기준으로 재집계.

## 4. Ultimate skill byte diff (★★★) — `work/h3/recon/ultimate_skills.json`

### 4.1 4 ultimate skills

| weapon | skill | rank @+0x1d | desc |
|---|---|---:|---|
| 단검 (s6) | 난무 | 15 | 적 1체에게 모든 기술을 연속 구사 |
| 건 (s7) | 난사 | 10 | 불특정 다수의 적을 무차별 사격 |
| 라이플 (s8) | 연쇄 | 5 | 사격후 반동으로 주변 적 타격 |
| 다크석 (s9) | 나락 | 5 | 일정시간 지옥 공간 소환 지속 |

### 4.2 cross-weapon ultimate diff (12 varying cols + 16 common)

```
+0x00..01 LE16 SP cost:     난무 600, 난사 600, 연쇄 400, 나락 500
+0x04     damage_base:       난무 120, 난사 80, 연쇄 120, 나락 104
+0x05     special spell flag: 다크만 0x78 (마법 효과 표식)
+0x09..0a LE16 damage scale: 난무 0x6d6c=28012, 난사 0x5454=21588 등
+0x0b     bonus_stat:        난무 20, 난사 0, 연쇄 40, 나락 40
+0x0c..0d flags:             난사만 0x1f01 (multi-target?), 나머지 0x0101
+0x0f     secondary scale:   난무 30, 난사 10, 연쇄 20, 나락 10
+0x11     tertiary scale:    난무 20, 난사 10, 연쇄 15, 나락 10
+0x1d     rank/power class:  난무 15, 난사 10, 연쇄 5, 나락 5  ← R63 확정
```

### 4.3 ultimate sentinel byte 발견 ★★

vs normal active skill 비교에서 **모든 ultimate 의 `+0x13 = 0x7f` (127)** — normal 은 다양 (28/206/253/127). 단 normal 도 일부 0x7f → "ultimate-only" 확정 아님, "high-tier marker" 가능.

**더 안정적**: `+0x14..+0x1c` 9-byte 영역이 ultimate 에서 거의 모두 0, normal 에서 0xff/0xfe/0xfd 다수 → **ultimate-only effect mask 후보**.

→ 이 영역은 multi-hit 패턴 또는 추가 effect chain 인코딩. R65 후속 작업.

## 5. Round 64 산출물

### 5.1 신규 스크립트 (4개)

- `tools/recon/export_game_balance.py` — master JSON export (537KB output)
- `tools/recon/analyze_value_scale.py` — value flat/ratio 분류 + signed debuff 식별
- `tools/recon/analyze_unused_stat_codes.py` — 0x14/0x19 binary + dat scan
- `tools/recon/decode_ultimate_skills.py` — ultimate vs normal byte diff

### 5.2 신규 출력 (모두 `work/h3/`, gitignored)

- `game_balance.json` (537KB) — master output
- `game_balance_summary.log` (4KB)
- `recon/value_scale.{json,log}`
- `recon/unused_codes.{json,log}`
- `recon/ultimate_skills.{json,log}`

### 5.3 진행률 갱신

- **R63 종료 기준 ~91-94%** → **R64 종료 기준 ~94-96%** (+3%p)
- 데이터 모델링 92→95% (game_balance.json 통합)
- 게임 시스템 이해 85→92% (value scale + ultimate field 매핑)
- DES 8 파일 보류 = 사용자 환경 필요 (R65+)

## 6. Round 65 후속 작업

1. ⭐⭐⭐ **i15_dat NDK 복호화** + 7 DES 파일 일괄 처리 — 사용자 환경
2. ⭐⭐ **equip trailer 177 case 의 0x14/0x19 분포 재집계** — boss-only stat code 가설 검증
3. ⭐⭐ **ultimate `+0x14..+0x1c` 9B effect mask 디코드** — multi-hit pattern 또는 chain effect
4. ⭐ **FUN_4f358 본문 ARM disassembly** — 0x14/0x19 binary literal 의 의미 (switch table)
5. ⭐ **boss_dat trailer 6B 가변 영역 디코드** — boss-specific stat fields

## 7. 참고 (Round 63 까지의 master enum)

(R63 SESSION_HANDOFF §3.3 참조 — 24 codes 100% 매핑)
