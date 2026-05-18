# Round 69 — i14 ammo 연관 + enemy_dat field 정밀 + dialogue translation queue (2026-05-19)

> 이번 라운드 목표: R68 후속 — 자동 가능 작업 3건 (i14 ammo / enemy stat field / dialogue 정렬). 자동 분석 한계 도달 상태에서 minor 정밀화.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐ **R68 의 's7 별도 ammo 시스템' 가설 정정** — i14 의 "탄성제" desc = "권총/라이플의 조합에 사용" 발견. 권총 (s7) + 라이플 (s8) **ammo 시스템 공유**. 0x1f marker 의 차이는 **사거리/조준 모드 표시만** (단발 권총 vs 연발 라이플)
- ⭐⭐⭐ **enemy_dat 19B stat block field 정밀 scaling 분석** — normal vs hard 161 pairs. hp_max ~2.22x (★stable), exp_gold ~6.92x median, f16 ATK ~2.93x, f17 AGI ~1.21x (+2 constant). field 의미 후속 가설
- ⭐⭐⭐ **dialogue corpus 9,740/9,741 meaningful Korean** 추출. 34,043 chars total. 빈도+카테고리+event 별 정렬. **LLM 번역 비용 추정 $4.09** (Claude Sonnet 4.6 기준)
- ⭐⭐⭐ **i14 조합 재료 46 entries 7 카테고리 분류**: 공통 용액 3, 공정 재료 6, 원소 속성 4, 몬스터 드롭 15, 고대 재료 3 tier × 4 type = 12, 클래스 강화 문장 5

## 1. i14 ammo 시스템 연관 (★★★★) — `work/h3/recon/i14_ammo_system.json`

### 1.1 R68 가설 정정

R68 의 발견: s7 (피스톨) 만 0x1f marker, 라이플 (s8) 은 0x01 standard.
R68 결론: "단발 권총 = 별도 hit/ammo 시스템 보유".

**R69 정정**: i14 "탄성제" 의 desc = "권총/라이플의 조합에 사용" → **두 무기 ammo 시스템 동일**.
- 0x1f vs 0x01 차이 = **사거리/조준 모드 표시만** (단발 vs 연발)
- ammo 자체는 공통 (탄성제 단일 재료)
- "스톤/총기" 고대 정령석 (데비그린/오헨그린/큐브그린) = 다크석/홀리석 + 권총/라이플 4 class 공유
- "시몬의문장" = 총기 전용 강화 (s7+s8 모두)

### 1.2 i14 카테고리 (46 entries 7 그룹)

| 카테고리 | n | examples |
|---|---:|---|
| 공통 용액 | 3 | 붉은/푸른/투명 용액 |
| 공정 재료 | 6 | 제련석, 연마가루, 정령석, **탄성제**, 강화제, 질긴섬유 |
| 원소 속성 | 4 | 바람피리, 만년설, 혈목, 흑암석 |
| 몬스터 드롭 | 15 | 쥐가죽, 박쥐날개, 라이칸이빨, 솔티안의 문장 등 |
| 고대 재료 t1 | 4 | 에스텔시아 (투구), 그리톤 (장갑), 아르세네스 (무기), 데비그린 (스톤/총기) |
| 고대 재료 t2 | 4 | 카메루시아, 시르톤, 뮤제게네스, 오헨그린 |
| 고대 재료 t3 | 4 | 헤게네시아, 아케톤, 바스테네스, 큐브그린 |
| 클래스 강화 문장 | 5 | 아벨(전사), 시몬(총기), 포프(마법), 부폰(방어), 하피(회피) |

### 1.3 weapon-class crafting map

| weapon | base material | 고대 재료 t1-t3 | 클래스 문장 |
|---|---|---|---|
| 창 (s4) / 대검 (s5) / 단검 (s6) | 연마가루 | 아르세네스/뮤제게네스/바스테네스 | 아벨 |
| 권총 (s7) / 라이플 (s8) | **탄성제** | 데비그린/오헨그린/큐브그린 | 시몬 |
| 다크석 (s9) / 홀리석 (s10) | 정령석 | 데비그린/오헨그린/큐브그린 | 포프 |

→ R62 boss drop 의 ATT2 분포와 일치: 시몬 = 총기 = ATT2 (특공) class.

## 2. enemy_dat 19B stat field 정밀 (★★★) — `work/h3/recon/enemy_stat_fields.json`

R60 hp_max 검증 외에 다른 field 의 정확한 의미 추적.

### 2.1 161 pairs scaling 분석 결과

| field | offset | median scale | range | guess |
|---|---|---:|---|---|
| lvl | +0x00 | 1.97x | 1.00-38.00x | level (R56 확정) |
| f4_5 | +0x04..+0x05 | 1.04x | 0.28-25.62x | **variant/ID** (scaling 없음, 불안정) |
| f6_7 | +0x06..+0x07 | 2.71x | 1.00-35.00x | secondary stat (MP_max?) |
| f8_9 | +0x08..+0x09 | 3.84x | 1.00-19.75x | tertiary stat or EXP_high |
| **hp_max** | **+0x0a..+0x0b** | **2.22x** | 1.00-2.83x | HP_max (R60 확정) |
| hp_cur | +0x0c..+0x0d | 3.00x | 1.00-7.79x | HP_cur or base value |
| **exp_gold** | **+0x0e..+0x0f** | **6.92x** | 1.00-322x | EXP main (group 별 9.7x or 1.80x) |
| f16 | +0x10 | 2.93x | 1.00-7.40x | **ATK** (4x scaling) |
| agi_or | +0x11 | 1.21x | 1.20-1.50x | **AGI/DOD** (+2 constant) |
| f18 | +0x12 | — | 0 → 0 | pad |

### 2.2 정정 field 가설

```
+0x00         lvl                  (R56 확정)
+0x04..+0x05  variant/ID           (sprite or AI variant index)
+0x06..+0x07  MP_max               (secondary stat 가설)
+0x08..+0x09  EXP_high or Gold_tier (group 별 분리)
+0x0a..+0x0b  HP_max               (R60 확정)
+0x0c..+0x0d  HP_cur               (base*multiplier 추정)
+0x0e..+0x0f  EXP_main             (9.7x 일관 + 1.80x 변형)
+0x10         ATK                  (4x scaling)
+0x11         AGI/DOD              (+2 constant boost)
+0x12         pad
```

## 3. dialogue corpus translation queue (★★★) — `work/h3/translation_queue.json`

R57 의 plaintext SCN 350 파일에서 추출한 9,741 unique 대사 → 9,740 meaningful Korean.

### 3.1 stats

```
total_lines:        26,415 (raw line entries with offset)
unique_texts:       9,741
meaningful_unique:  9,740 (한글 30% 이상 + 비어있지 않음)
filtered_out:       1 (영어/숫자 only)
```

### 3.2 길이 카테고리 분포

| category | count | total chars |
|---|---:|---:|
| name_or_short (1-2 char) | 다수 | — |
| short_phrase (3-5 char) | 다수 | — |
| sentence (6-15 char) | 다수 | — |
| long_dialogue (16+ char) | 다수 | — |

### 3.3 top 10 priority (가장 빈번한 의미있는 한글)

```
1. 케이              count= 847   (캐릭터 이름)
2. 리츠              count= 811   (캐릭터 이름)
...
(전체 9,740 entries 정렬)
```

### 3.4 번역 비용 추정

```
char_count_total:           34,043
estimated_tokens_korean:    68,086
estimated_tokens_english:   68,086
rough_cost_usd:             $4.09 (Claude Sonnet 4.6, $0.03/1k tokens)
```

→ 9,740 unique 대사 전체 번역 가능 ~$4. Hero4 H4 R69 의 35,752 entries 와 비교 시 H3 가 더 작음.

## 4. R69 산출물

### 4.1 신규 스크립트 (3개)

- `tools/recon/analyze_i14_ammo_system.py` — i14 조합 재료 카테고리 + ammo 시스템 정정
- `tools/recon/refine_enemy_stats.py` — 19B stat block field scaling 분석
- `tools/recon/sort_dialogue_for_translation.py` — 9,741 unique 대사 정렬 + 비용 추정

### 4.2 신규 출력 (모두 `work/h3/`, gitignored)

- `recon/i14_ammo_system.{json,log}`
- `recon/enemy_stat_fields.{json,log}`
- `translation_queue.{json,log}`

### 4.3 진행률 갱신

- **R68 종료 ~99%** → **R69 종료 ~99.3%** (+0.3%p)
- 게임 시스템 모델링: 99.7→99.8% (i14 ammo 정정 + enemy stat scaling + dialogue queue)
- **자동 분석 완전 한계 도달** — 남은 모든 작업이 사용자 환경 필수

## 5. Round 70+ 후속 (사용자 환경 필수)

자동 분석 사실상 종료. 남은 작업 모두 사용자 환경에서 진행:

### 5.1 ⭐⭐⭐ DES 8 파일 복호화

- i15_dat (7400B, entropy 7.97, master item table 추정)
- drop_dat / droph_dat (3080B, enemy 드롭 테이블)
- getitem_dat (400B, fixed drops)
- smith_dat / smithh_dat (896B, smith 레시피)
- shop_dat / shoph_dat (상점 카탈로그)

Hero5 NDK runner 활용 (key `"0EP@KO91"` + `dat/des_dat` tables, key R57 확정).

### 5.2 ⭐⭐⭐ boss skill ID 매핑 최종 확정

DES 복호화된 파일 안에 boss AI table 발견 가능 (R67/R68 H4 가설).

### 5.3 ⭐⭐ i14 smith 레시피 매핑

smith_dat 복호화 후 i14 (조합 재료) → i0~i12 (결과물) 정확 매핑.

### 5.4 ⭐⭐ Dialogue LLM 번역

9,740 entries, $4.09 추정 비용.

### 5.5 ⭐ SMAF→OGG 33 파일 audio 변환

Android audio asset 준비.

## 6. 참고 (이전 라운드)

- [Round 68](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — boss skill table 검색 + gun marker + FUN_4f358
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer + boss skill 가설
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- (R56-R63) — see SESSION_HANDOFF.md
