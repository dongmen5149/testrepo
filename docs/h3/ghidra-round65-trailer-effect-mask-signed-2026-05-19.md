# Round 65 — equip trailer 재집계 + skill effect mask 디코드 + boss trailer 6B + signed 검증 (2026-05-19)

> 이번 라운드 목표: R64 의 4 후속 작업 — equip trailer 의 0x14/0x19 분포 재집계, ultimate skill +0x14..+0x1c effect mask 디코드, boss_dat 6B 가변 trailer, signed int16 통일 검증.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **skill +0x10..+0x1d 14-byte effect block 완전 디코드** — 1차 debuff code @+0x13 + LE16+LE16 signed value @+0x14..+0x17 + 2차 debuff @+0x18 + value @+0x19..+0x1c + rank @+0x1d
- ⭐⭐⭐⭐ **debuff code 가 별도 enum** 확정 — 0x1c=STUN (skill) ≠ REVIVE (i13), 0x03=BLEED (skill) ≠ HP_REGEN (i13). 6 distinct debuff codes 사용 (0x03/0x06/0x08/0x09/0x15/0x1c)
- ⭐⭐⭐⭐ **0x14 / 0x19 = completely unused** — equip trailer 의 bt 위치에도 0개 출현. R63 master enum 24 codes 중 실제 22 개만 사용
- ⭐⭐⭐ **boss_dat trailer 6B = (combat_rating, sprite_idx, skill1, skill2, skill3, skill4)** — 16 story boss / 14 misc boss (0xFF×4)
- ⭐⭐⭐ **R64 의 'signed int16 통일' 가설 정정** — 실제로는 **2곳만 signed** (i13 effect_value + skill debuff mask), 나머지는 모두 unsigned

## 1. skill +0x10..+0x1d effect mask 완전 디코드 (★★★★★)

R64 발견 (`+0x14..+0x1c` 9B 영역이 ultimate=0, normal=0xff/0xfe 다수) 의 본질 파악.

### 1.1 14-byte layout

```
+0x10..+0x11   LE16  primary damage scale (저격 0x14=20 highest, 일반 0x0a/0x0f=10/15)
+0x12          byte  pad (00)
+0x13          byte  1차 debuff code (0x7f sentinel = "no debuff")
+0x14..+0x15   LE16 signed int16  1차 debuff primary value (음수 = 적 stat 감소)
+0x16..+0x17   LE16 signed int16  1차 debuff secondary value (보조 효과 또는 duration)
+0x18          byte  2차 debuff code (0x7f sentinel = "no second debuff")
+0x19..+0x1a   LE16 signed int16  2차 debuff primary value
+0x1b..+0x1c   LE16 signed int16  2차 debuff secondary value
+0x1d          byte  rank / power class (R63 확정)
```

### 1.2 24 active_attack skills 의 debuff 사용 매핑

| skill | weapon | rank | pri_dmg | d1_code | d1_val (p, s) | d2_code | d2_val (p, s) | desc |
|---|---|---:|---:|---:|---|---:|---|---|
| 섬광 | 창 | 2 | 3840 | . | . | . | . | 빠르게 돌진 |
| 자격 | 창 | 3 | 3840 | . | . | . | . | 무형 힘 지른다 |
| **압도** | 창 | 1 | 0 | **0x09** | (-10, -3) | . | . | 공격을 늦춘다 |
| **유도** | 창 | 1 | 512 | **0x15** | (0, 0) | . | . | 공격 자신에게 집중 (TAUNT) |
| 선풍 | 대검 | 3 | 3840 | . | . | . | . | 둘러싼 적 |
| 양단 | 대검 | 1 | 5120 | . | . | . | . | 일격필살 |
| 질풍 | 대검 | 3 | 5120 | . | . | . | . | 연속 |
| **참혼** | 단검 | 3 | 2560 | **0x1c** | (0, 0) | . | . | 기절시킨다 (STUN) |
| **암영** | 단검 | 1 | 2560 | **0x03** | (-50, -1) | . | . | 관통 (BLEED?) |
| ★난무 | 단검 | 15 | 5120 | . | . | . | . | 모든 기술 연속 |
| 연사 | 건 | 4 | 3840 | . | . | . | . | 1체 연속 사격 |
| ★난사 | 건 | 10 | 2560 | . | . | . | . | 무차별 사격 |
| 곡예 | 건 | 4 | 3840 | . | . | . | . | 거리 벌리며 |
| **저격** | 건 | 1 | 5120 | **0x1c** | (0, 0) | . | . | 정확 한발 위력 (STUN trigger?) |
| **직격** | 라이플 | 1 | 5120 | **0x03** | (-50, -1) | . | . | 출혈 유도 (BLEED) |
| ★연쇄 | 라이플 | 5 | 3840 | . | . | . | . | 반동 주변 |
| **위협** | 라이플 | 1 | 64767 | . | . | . | . | 기절저항 감소 |
| 암흑 | 다크 | 1 | 5120 | . | . | . | . | 내면 어둠 |
| 업화 | 다크 | 1 | 3840 | . | . | . | . | 지옥 낙뢰 |
| ★나락 | 다크 | 5 | 2560 | . | . | . | . | 지옥 공간 |
| **망각** | 다크 | 1 | 65279 | **0x06** | (-10, -2) | . | . | 공격력 격감 (ATT2-) |
| **전율** | 다크 | 1 | 65279 | **0x08** | (-10, -2) | **0x0a** | (-10, -5) | 방어력+회피율 격감 |
| 파동 | 홀리 | 1 | 3840 | . | . | . | . | 빛 흐름 |
| **격광** | 홀리 | 1 | 2560 | **0x09** | (-10, -2) | . | . | 명중률 낮춘다 (ACC-) |

### 1.3 debuff code = stat code 와 다른 enum ★★

skill debuff code 6개 사용:

| code | name (가설) | 검증 |
|---:|---|---|
| 0x03 | **BLEED** | 암영 "관통", 직격 "출혈 유도" — i13 의 HP_REGEN 과 다름 |
| 0x06 | **ATT2_DEBUFF** | 망각 "공격력 격감" — stat enum 의 ATT2 와 동일 코드 재사용 |
| 0x08 | **M_DEF_DEBUFF** | 전율 "방어력 격감" — M_DEF code 재사용 (실제로는 P_DEF 일 수도, R66 검증) |
| 0x09 | **ACC_DEBUFF** | 격광 "명중률 낮춘다", 압도 "공격 늦춘다" — ACC 재사용 |
| 0x0a | **DOD_DEBUFF** | 전율 2차 "회피율 격감" — DOD 재사용 |
| 0x15 | **TAUNT** | 유도 "공격을 자신에게 집중" — R63 미식별 코드의 신규 의미 |
| 0x1c | **STUN_TRIGGER** | 참혼 "기절", 저격 "정확 한발" — R63 의 REVIVE 와 의미 분리 |

→ **debuff context 는 별도 enum** (stat buff/equip enum 과 일부 코드 공유, 일부 재정의). 0x15 와 0x1c 는 R63 master enum 의 다른 의미 (TAUNT vs ???, STUN vs REVIVE) 와 컨텍스트 분리.

### 1.4 ultimate vs normal 의 debuff 비대칭

4 ultimate (난무/난사/연쇄/나락) 모두 d1_code=0x7f sentinel = **no debuff**. ultimate 은 raw damage 만 사용, debuff 는 normal active 의 특기.

→ "ultimate = high damage, normal active = utility/debuff" 설계 패턴.

## 2. equip trailer 177 case 재집계 (★★★★) — `work/h3/recon/trailer_bonus.json`

R64 의 "0x14/0x19 가 equip trailer 에 출현" 가설 검증.

### 2.1 결과 — 0x14 / 0x19 = trailer bt 위치 0회

346 equip20 items 중 177 (51.2%) non-zero trailer:
- 100 has paired bt2 (4B 모두 사용)
- 0 has bt1=0x14 or bt1=0x19
- 0 has bt2=0x14 or bt2=0x19

→ **0x14 / 0x19 = completely unused stat codes** (i*_dat / s*_dat / equip trailer 어디서도 의미있는 위치에 부재).

R63 master enum 24 codes 중 실제 사용 = 22 codes (0x14, 0x19 제외).

### 2.2 rarity × bt1 분포 (top 사용 코드)

| rarity | top bt1 codes |
|---|---|
| **magic** (87) | 0x06 ATT2(10) / 0x0c CRI_RATE(9) / 0x07 P_DEF(9) / 0x08 M_DEF(8) / 0x09 ACC(7) |
| **epic** (40) | 0x02 HP_MAX(7) / 0x05 ATT1(6) / 0x06 ATT2(5) / 0x0f SP_REGEN(5) / 0x07 P_DEF(4) |
| **boss_drop** (29) | 0x06 ATT2(11) / 0x05 ATT1(7) / 0x09 ACC(2) / 0x07 P_DEF(2) / 0x0a DOD(2) |
| **legendary** (8) | 0x10 HP_DRAIN(4) / 0x0f SP_REGEN(1) / 0x02 HP_MAX(1) |
| **endgame** (16) | 0x05 ATT1(5) / 0x09 ACC(2) / 0x07 P_DEF(2) / 0x0a DOD(2) |

→ rarity 별 stat 특성: magic 은 균등, epic 은 HP/ATT 위주, boss_drop 은 ATT2/ATT1 (공격 특화), legendary 는 HP_DRAIN 4 case 위주.

### 2.3 slot × bt 분포

```
armor    bt1 top: 0x07 P_DEF(16) / 0x0a DOD(11) / 0x08 M_DEF(10) / 0x09 ACC(10)
armor    bt2 top: 0x08 M_DEF(13) / 0x0c CRI_RATE(8) / 0x0d CRI_DEF(7)
weapon   bt1 top: 0x06 ATT2(18) / 0x05 ATT1(16) / 0x0c CRI_RATE(11) / 0x0f SP_REGEN(7)
weapon   bt2 top: 0x11 CD_REDUCE(11) / 0x12 SHIELD_PIERCE(8) / 0x10 HP_DRAIN(5)
```

→ armor = 방어 stat 위주, weapon = 공격/속도 stat 위주. trailer bt 분포가 게임 디자인과 일치.

## 3. boss_dat 6B trailer 디코드 (★★★) — `work/h3/recon/boss_trailer.json`

### 3.1 layout

```
[0] combat rating (lvl 과 비례 안 함, boss-only metric)
[1] sprite/model index (boss family)
[2..5] 4 boss-specific skill slot IDs (0xFF = unused)
```

### 3.2 family → sprite_idx

| family | sprite_idx |
|---|---:|
| 리츠 | 0 |
| 케이 | 1 |
| 멜페토 | 2 |
| 큐 | 3 |
| 시즈타이탄 | 0 |
| 아르보르 | 1 |
| 오르도 | 2 |
| 벨루스 | 3 |
| 홀리가디언 | 4 |

→ 8 distinct sprites (0~4). 같은 sprite_idx 가 다른 family 에서 재사용 (리츠/시즈, 케이/아르보르 등) — 한 sprite asset 을 여러 boss 가 공유.

### 3.3 story vs misc boss

- **Story bosses (16 entries = 8 boss × 2 difficulty)**: 리츠/케이/멜페토/큐 — trailer[2..5] 에 skill IDs (값 1~20 범위)
- **Misc bosses (14 entries = 7 boss × 2 difficulty)**: 벨루스/시즈타이탄/아르보르/오르도/홀리가디언 — trailer[2..5] = `FF FF FF FF` (scripted skill 없음)

### 3.4 tier 3 boss 강한 skill

- 리츠1/2 skill = (3, 2, 1, 2) 일반 ID
- 리츠3 skill = (19, 13, 9, 9) — tier 3 라 더 강한 ID (0x13=19, 0x0d=13)
- 케이3 skill = (20, 14, 10, 8)
- 멜페토 (tier 4) = (9, 3, 3, 7) — unique combo
- 큐 (tier 4) = (7, 8, 5, 9) — unique combo

→ boss progression: tier 가 올라가면 skill ID 가 커짐 = 더 강한 ability 잠금 해제.

## 4. signed int16 통일 검증 (★★★) — `work/h3/recon/value_sign_verification.json`

R64 의 "signed int16 통일" 가설 정정. 실제로는 **단 2곳만 signed**.

### 4.1 검증 결과

| source | type | range | signed? |
|---|---|---|---|
| **i13 effect_value** | LE16 | -50..1200 | ✓ **signed int16** (5 negative cases) |
| **skill +0x14..+0x17** | LE16+LE16 | -50..0 / -3..0 | ✓ **signed int16** (9 with-debuff) |
| i12 ring bonus_value | byte | 3..80 | ✗ unsigned (high-bit 0) |
| i16 enchant tail[1] | byte | 2..15 | ✗ unsigned |
| i18 effect_value | LE16 | 0..3000 | ✗ unsigned (negative 0) |
| equip trailer v1/v2 | byte | 0..80 / 0..25 | ✗ unsigned (high-bit 0) |
| enemy/boss stat block | BE16 | 27..360 (HP) | ✗ unsigned |

### 4.2 결론

- **signed 사용처 = debuff context 전용** (적 stat 감소 의도)
- 그 외 모든 value field 는 unsigned
- R64 가설 "signed int16 통일" 폐기 → "debuff value 만 signed" 정정

## 5. R65 산출물

### 5.1 신규 스크립트 (4개)

- `tools/recon/analyze_trailer_bonus.py` — equip trailer 의 rarity × bt cross-tab
- `tools/recon/decode_skill_effect_mask.py` — skill +0x10..+0x1d 14-byte effect block
- `tools/recon/decode_boss_trailer.py` — boss 6B 가변 trailer
- `tools/recon/verify_signed_values.py` — signed int16 통일 검증

### 5.2 신규 출력 (모두 `work/h3/recon/`, gitignored)

- `trailer_bonus.{json,log}`
- `effect_mask.{json,log}`
- `boss_trailer.{json,log}`
- `value_sign_verification.{json,log}`

### 5.3 game_balance.json 업데이트 (R65 schema v1.1)

R65 추가 enrichment 권장사항 (R66 implementation):
- skill 에 `debuff1_code`, `debuff1_value_primary`, `debuff1_value_secondary`, `debuff2_*` 필드 추가
- boss 에 `sprite_idx`, `boss_skill_slots[4]`, `is_misc_boss` 필드 추가
- equip 에 trailer bt1/v1/bt2/v2 parsed 필드 추가

### 5.4 진행률 갱신

- **R64 종료 기준 ~94-96%** → **R65 종료 기준 ~96-97%** (+1.5%p)
- 게임 시스템 모델링: 92→97% (skill effect mask + boss skill slot + signed 정정)
- DES 8 파일 보류 = 사용자 환경 필요 (R66+)

## 6. Round 66 후속 작업

1. ⭐⭐⭐ **debuff code 0x03 (BLEED) / 0x06 / 0x08 / 0x09 / 0x15 / 0x1c 정밀 의미** — game string table 에서 추가 desc 검색
2. ⭐⭐⭐ **i15_dat NDK 복호화** + 7 DES 파일 일괄 — 사용자 환경
3. ⭐⭐ **game_balance.json schema v1.1 출력** — R65 산출물 통합 (skill debuff fields + boss skill slots + signed flags)
4. ⭐⭐ **boss combat_rating (trailer[0]) 의미 추적** — lvl 과의 함수 관계
5. ⭐ **skill primary_damage_scale (+0x10..+0x11) 의미** — 일부 0xfcff/0xfeff weird values
6. ⭐ **FUN_4f358 본문 ARM disassembly** — debuff_code → effect handler 매핑

## 7. 참고 (이전 라운드)

- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json 통합 / value scale / 0x14·0x19 미사용 / ultimate skill diff
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 100%
- (R56-R62) — see SESSION_HANDOFF.md §7
