# Round 66 — debuff codes 정밀 + skill effect v2 + boss combat_rating + game_balance.json v1.1 (2026-05-19)

> 이번 라운드 목표: R65 의 4 후속 작업 — debuff code 정밀 매핑 (skill ↔ i13 비교), R65 schema 정정 (3-debuff 케이스), boss combat_rating 공식 추적, game_balance.json v1.1 출력.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **R65 의 'debuff = 별도 enum' 가설 정정 → 'stat enum 동일, value 부호로 buff/debuff'** — i13 디버프 5 cases (effect_type high byte) 와 skill 디버프 9 cases 가 동일 enum 사용 확인
- ⭐⭐⭐⭐⭐ **skill effect block schema v2 정정** — R65 의 "+0x13 = d1_code, +0x18 = d2_code" 부분 오류. 실제 layout 은 **right-justified chain** (rank @+0x1d 고정, debuff slots 3개까지). 전율 = 3 debuff (P_DEF + M_DEF + DOD) 누락 발견
- ⭐⭐⭐⭐ **skill debuff codes 6 → 11 distinct 확장** — R66 신규 발견 5개: 0x05 (ATT1 망각), 0x07 (P_DEF 전율), 0x0b (BLOCK 유도 자기버프), 0x0d (STUN_RESIST_DEBUFF 위협), 0x15 (TAUNT 유도)
- ⭐⭐⭐⭐ **boss combat_rating 공식 발견** — `rating = round(lvl/2 + 44)` (normal) / `round(lvl/2 + 64)` (hard). 30 boss entries 모두 검증 통과
- ⭐⭐⭐ **game_balance.json v1.1 출력** — 582KB. R66 skill effect_v2 + boss trailer_decoded + combat_rating formula + debuff codes 통합

## 1. debuff codes 정밀 매핑 (★★★★★)

R65 의 "skill debuff = 별도 enum (6 codes)" 가설을 i13 디버프와 cross-reference 로 정정.

### 1.1 cross-reference (i13 stat_code ↔ skill debuff code)

| code | master enum | i13 디버프 (양수=buff/음수=debuff) | skill 디버프 (음수) |
|---:|---|---|---|
| 0x02 | HP_MAX | 드래곤피어 -30 (적 HP최대치 감소) | (skill 미사용) |
| 0x03 | HP_REGEN | (i13 양수 = HP_REGEN buff) | **암영/직격 -50 (BLEED = HP_REGEN 음수 = 적 HP 시간 감소)** |
| 0x05 | ATT1 | (i13 양수 = ATT1 buff) | **망각 -3 (ATT1 격감)** |
| 0x06 | ATT2 | (i13 양수 = ATT2 buff) | **망각 -10 (ATT2 격감)** |
| 0x07 | P_DEF | 사막의폭염 -50 (적 P_DEF 감소) | **전율 -3 (P_DEF)** |
| 0x08 | M_DEF | 머메이드의노래 -50 (적 M_DEF 감소) | 전율 -10 (M_DEF) |
| 0x09 | ACC | 아레스의구름 -30 (적 ACC 감소) | 압도 -10, 격광 -10 (ACC) |
| 0x0a | DOD | 결박하는대지 -30 (적 DOD 감소) | 전율 -10 (DOD 2차) |
| 0x0b | BLOCK | (i13 양수 = BLOCK buff) | **유도 +5 (자기 BLOCK buff)** |
| 0x0d | CRI_DEF | (i13/equip = CRI_DEF) | **위협 -10 (STUN_RESIST_DEBUFF, 컨텍스트별 의미)** |
| 0x15 | (R63 미식별) | — | **유도 (TAUNT)** ★ R66 신규 master enum 추가 |
| 0x1c | REVIVE | 피닉스의숨결 (REVIVE buff) | **참혼/저격 val=0 (STUN_TRIGGER, 컨텍스트별 의미)** |

### 1.2 정정 결론

- **debuff code = stat enum 동일** (R65 의 "별도 enum" 가설 폐기)
- **value 부호로 buff/debuff 구분**: 양수 = stat 증가, 음수 = stat 감소
- **2 컨텍스트 분리 코드**:
  - 0x0d: i13/equip = CRI_DEF (크리피해 감소), skill = STUN_RESIST_DEBUFF (기절저항 감소)
  - 0x1c: i13 = REVIVE (전투불능 회복), skill = STUN_TRIGGER (기절)
- **신규 master enum 코드**: 0x15 = TAUNT (R63 미식별 코드 의 의미 확정)
- **0x14, 0x19 = 여전히 unused** (R65 와 동일)

## 2. skill effect block schema v2 (★★★★★)

R65 schema 의 부분 오류 발견 — 전율 (3-debuff) 같은 케이스를 d1+d2 만 캡처.

### 2.1 정정된 schema (right-justified chain)

```
Tail = 30 bytes 고정
+0x1d (pos 29) = rank (R63 확정)
Effect chain = right-justified, 마지막 byte 직전부터 거꾸로 읽음

Slot layout (pos 기준):
  Slot 1: pos 14 (code), pos 15..18 (LE16 primary + LE16 secondary)
  Slot 2: pos 19 (code), pos 20..23 (value)
  Slot 3: pos 24 (code), pos 25..28 (value)
  pos 29: rank

각 slot:
  - 0x7f = sentinel (no debuff)
  - 0x00 = "zero slot" (skill 자체가 raw damage only, debuff 없음)
  - else = active debuff (code + LE16 + LE16 signed value)
```

### 2.2 chain length 분포

| n_debuffs | count |
|---:|---:|
| 0 (raw damage only) | 14 |
| 1 | 6 |
| 2 | 3 |
| **3** | **1 (전율)** |

### 2.3 전율 3-debuff (R66 신규 발견)

```
전율 (s9_dat, rank 1, "주변 적의 방어력과 회피율을 격감"):
  slot1: 0x07 P_DEF (-3, -2)
  slot2: 0x08 M_DEF (-10, -2)
  slot3: 0x0a DOD   (-10, -5)
```

→ R65 는 slot2 (M_DEF) + slot3 (DOD) 만 캡처, slot1 (P_DEF) 누락. 실제로는 3 stat 모두 debuff.

### 2.4 R65 의 weird values 해명

- **위협** primary_damage = 64767 (-769) → 사실 R65 schema 가 잘못된 위치 읽음. 실제 위협은 slot1 = 0x0d STUN_RESIST_DEBUFF (-10, -4), header padding 의 0xff 가 R65 의 "primary_damage" 위치로 잘못 잡힌 것.
- **망각/전율** primary_damage = 65279 (-257) → 동일한 잘못된 위치 읽음. 실제로는 효과 chain 의 일부 (망각 slot1=ATT1, 전율 slot1=P_DEF).

### 2.5 모든 24 active_attack 의 effect slot 정밀 매핑

| skill | weapon | rank | n_db | slot1 | slot2 | slot3 |
|---|---|---:|---:|---|---|---|
| 섬광 | 창 | 2 | 0 | zz | . | . |
| 자격 | 창 | 3 | 0 | zz | . | . |
| 압도 | 창 | 1 | 2 | 0x1c STUN(0,0) | 0x09 ACC(-10,-3) | . |
| 유도 | 창 | 1 | 2 | 0x0b BLOCK(+5,+2) | 0x15 TAUNT(0,0) | . |
| 선풍 | 대검 | 3 | 0 | zz | . | . |
| 양단 | 대검 | 1 | 0 | zz | . | . |
| 질풍 | 대검 | 3 | 0 | zz | . | . |
| 참혼 | 단검 | 3 | 1 | zz | 0x1c STUN(0,0) | . |
| 암영 | 단검 | 1 | 1 | zz | 0x03 BLEED(-50,0) | . |
| ★난무 | 단검 | 15 | 0 | zz | . | . |
| 연사 | 건 | 4 | 0 | zz | . | . |
| ★난사 | 건 | 10 | 0 | zz | . | . |
| 곡예 | 건 | 4 | 0 | zz | . | . |
| 저격 | 건 | 1 | 1 | zz | 0x1c STUN(0,0) | . |
| 직격 | 라이플 | 1 | 1 | zz | 0x03 BLEED(-50,0) | . |
| ★연쇄 | 라이플 | 5 | 0 | zz | . | . |
| 위협 | 라이플 | 1 | 1 | 0x0d STUN_RESIST(-10,-4) | . | . |
| 암흑 | 다크 | 1 | 0 | zz | . | . |
| 업화 | 다크 | 1 | 0 | zz | . | . |
| ★나락 | 다크 | 5 | 0 | zz | . | . |
| 망각 | 다크 | 1 | 2 | 0x05 ATT1(-3,-2) | 0x06 ATT2(-10,-2) | . |
| **전율** | **다크** | **1** | **3** | **0x07 P_DEF(-3,-2)** | **0x08 M_DEF(-10,-2)** | **0x0a DOD(-10,-5)** |
| 파동 | 홀리 | 1 | 0 | zz | . | . |
| 격광 | 홀리 | 1 | 1 | zz | 0x09 ACC(-10,-2) | . |

→ ultimate (난무/난사/연쇄/나락) 는 모두 0 debuff = raw damage only.
→ utility/debuff active 는 normal rank (1~3) 가 담당.
→ **유도**가 자기 BLOCK buff (+5, +2) 와 TAUNT 동시 발동 = 탱커 능력.

## 3. boss combat_rating 공식 (★★★★) — R66 신규 발견

### 3.1 공식

```
combat_rating = round(level / 2 + offset)

offset = 44 if difficulty == "normal"
offset = 64 if difficulty == "hard"
```

### 3.2 검증 (30 entries 모두 통과)

normal:
- 리츠1 lvl 14 → rating 51 = round(14/2 + 44) = 51 ✓
- 리츠3 lvl 32 → rating 60 = round(32/2 + 44) = 60 ✓
- 멜페토 lvl 44 → rating 66 = round(44/2 + 44) = 66 ✓
- 홀리가디언 lvl 46 → rating 67 = round(46/2 + 44) = 67 ✓

hard:
- 리츠1 lvl 51 → rating 90 = round(51/2 + 64) = 90 ✓
- 홀리가디언 lvl 67 → rating 98 = round(67/2 + 64) = 98 ✓

### 3.3 의미

- **combat_rating = "challenge equivalence level"** — boss 가 표시하는 권장 player level
- normal 모드 lvl_cap = 88 (44 × 2) 추정, hard 모드 lvl_cap = 128 (64 × 2) 추정
- rating = (lvl + cap_offset×2) / 2 = (lvl + 88) / 2 (normal), (lvl + 128) / 2 (hard)
- 즉 boss의 raw lvl 과 게임 cap 의 중간값 = displayed difficulty

## 4. game_balance.json v1.1 출력 (★★★)

`work/h3/game_balance.json` 갱신 — 537KB → 582KB.

### 4.1 v1.1 추가 필드

```diff
+ skills.{file}.skills[].effect_v2 = {rank, n_debuffs, slot1, slot2, slot3, header}
+ bosses.normal[].trailer_decoded = {combat_rating, sprite_idx, skill_slots, is_misc_boss, expected_rating, rating_matches}
+ bosses.hard[].trailer_decoded   = (same)
+ bosses.combat_rating_formula    = {normal: "round(lvl/2 + 44)", hard: "round(lvl/2 + 64)"}
+ stat_enum.0x0b.context_buff     = {skill_buff: "BLOCK (유도)"}
+ stat_enum.0x0d.context_split    = {i13/i16/equip: "CRI_DEF", skill_debuff: "STUN_RESIST_DEBUFF"}
+ stat_enum.0x1c.context_split    = {i13_buff: "REVIVE", skill_debuff: "STUN"}
+ stat_enum.0x15                  = {name: "TAUNT", desc: "...", from: "skill 유도 0x15 (R66 신규)"}
+ skill_debuff_codes              = {doc, codes: {11 distinct}, chain_length_distribution}
```

### 4.2 schema_version: 1.0 → 1.1

## 5. R66 산출물

### 5.1 신규/수정 스크립트

- `tools/recon/refine_debuff_codes.py` (신규) — i13 ↔ skill cross-reference
- `tools/recon/decode_skill_effect_v2.py` (신규) — right-justified chain 파싱
- `tools/recon/export_game_balance.py` (수정) — v1.1 출력 (R66 enrichment)

### 5.2 신규 출력 (모두 `work/h3/recon/`, gitignored)

- `debuff_codes_refined.{json,log}`
- `skill_effect_v2.{json,log}`
- `game_balance.json` (582KB v1.1)
- `game_balance_summary.log`

### 5.3 진행률 갱신

- **R65 종료 ~96-97%** → **R66 종료 ~97-98%** (+1%p)
- 게임 시스템 모델링: 97→99% (debuff schema 정밀 + 3-debuff 케이스 발견 + boss combat_rating 공식)
- DES 8 파일 보류 = 사용자 환경 필요 (R67+)

## 6. Round 67 후속 작업

1. ⭐⭐⭐ **i15_dat NDK 복호화** + 7 DES 파일 일괄 — 사용자 환경 (계속 보류)
2. ⭐⭐⭐ **skill header (+0x00..+0x0d) 의 의미 정밀** — SP cost 외 byte 4/5, byte 9/10/11 의 의미
3. ⭐⭐ **boss skill slot ID (0x01..0x14) → skill_dat ID 매핑** — story boss 의 4 skill 어떤 actual skill 인지
4. ⭐⭐ **i14 조합 재료 → smith_dat 레시피 매핑** — smith_dat (DES) 복호 시 직접 매칭
5. ⭐⭐ **FUN_4f358 본문 ARM disassembly** — debuff handler dispatch 검증
6. ⭐ **enemy_dat 19B trailer (`01 1e`)** 의미 — `1e` = 30 = boss spawn flag?

## 7. 참고 (이전 라운드)

- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer 재집계 + effect mask + signed 정정 (정정될 R65 schema)
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0 + value scale + 0x14/0x19
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 100%
- (R56-R62) — see SESSION_HANDOFF.md §7
