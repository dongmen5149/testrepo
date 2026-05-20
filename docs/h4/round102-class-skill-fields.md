# Hero4 Round 102 — 32B class skill stat block field 정밀 (R101 후속)

> R101 의 64 skill 전수 byte 분포 분석으로 32B stat block 의 각 field 의미 식별.

## TL;DR

R101 의 4 후보 field (byte 0/3-4/5/8) 검증 + **byte[16-19] speed/range/anim cluster** 식별.

`_H_SS` (환수) 의 23B stat block 과 layout 이 다르나, **field semantics 는 유사 layer** 공유 (speed/range/animation).

## 확정 field (high-evidence)

| pos | field name | unique vals | 의미 |
|---|---|---|---|
| 0 | MP cost | 29 | 60/64 nonzero, min=1 max=29 mean=15.2 |
| 1 | flag1 | 16 | 0xff dominant (23×) |
| 2 | section marker | 6 | 0xff dominant (55/64), section boundary |
| **3-4** | **damage LE16** | 29 nonzero | min=20 max=320 |
| **5** | **damage type** | 4 enum | 0=54×, 5=7×, 20=2×, 25=1× |
| 7 | pre-cast flag | 3 | 0 dominant |
| **8** | **skill level requirement** | 8 | 0/3/6/11 가 주요 tier |
| 9 | secondary flag | 5 | 2 dominant (24×) |
| 13 | flag13 | binary | 0/1 |
| 14 | const marker | 2 | 0 또는 120 (0x78) |
| 15 | always 0 | 1 | invariant |
| **16** | **speed** | 37 | 51-63 range dominant (환수 stat block speed 53 와 유사) |
| **17** | **range/duration** | 23 | 4/150/44/100 common |
| 18 | flag18 | binary | |
| **19** | **animation_id** | 21 | 15/4 common (환수 anim 4-20 과 유사 layer) |
| 20-21 | secondary effect LE16 | 20+10 | proc/status 강도 후보 |
| 22 | sub_boundary | 2 | 항상 0 (1 outlier=255) |
| 23 | bonus value | 9 | 1/10 common |
| 24-31 | reserved | 1-9 | 대부분 0 |

## Damage type enum (byte[5])

| type id | 의미 추정 | count |
|---|---|---|
| 0 | 마법 / 기절 / 버프 (no direct damage 표시) | 54 |
| 5 | 물리 공격 | 7 |
| 20 | 특수 (강력) | 2 |
| 25 | 최강 / 보스 | 1 |

## Skill level requirement (byte[8])

| lvl_req | count | 의미 |
|---|---|---|
| 0  | 5  | 기본 공격 / always available |
| 3  | 20 | early tier 1 (가장 빈번한 unlock 시점) |
| 4  | 2  | |
| 5  | 4  | |
| 6  | 9  | mid tier |
| 7  | 4  | |
| 10 | 4  | |
| 11 | 16 | late tier 2 (deep unlock) |

→ 2 major unlock tiers (3 / 11) 가 대다수 — 게임 디자인의 phase progression.

## S001 사격 sample decode

| skill | MP | dmg | dtype | lvl | speed | range | anim |
|---|---|---|---|---|---|---|---|
| 사격 (basic) | 0 | 0 | 5 | 0 | 52 | 90 | 2 |
| 산탄사격 | 15 | 0 | 5 | 3 | 52 | 110 | 11 |
| 동시사격 | 1 | 0 | 5 | 3 | 52 | 150 | 15 |

→ 모두 dtype=5 (shooter), speed=52 invariant (사격 class 공통). range 증가 패턴.

## R101 가설 검증

| field | R101 후보 | R102 확정 |
|---|---|---|
| byte[0] | MP cost | ✓ (60/64 nonzero, 1-29 range) |
| byte[3-4] LE16 | damage | ✓ (29 nonzero, 20-320 range) |
| byte[5] | damage type | ✓ (4 enum value) |
| byte[8] | skill level requirement | ✓ (lvl tiers 0/3/6/11 dominant) |
| byte[16-19] | speed/range/anim cluster | ✓ (speed 52-63, range varies, anim 1-20) |

R101 의 모든 후보 확정 + cluster 식별 추가.

## `_H_SS` 환수 stat block 과 비교

| field | 환수 23B (R87) | character 32B (R102) |
|---|---|---|
| damage | byte[3-4] LE16 | byte[3-4] LE16 |
| type/marker | byte[0] = 0x14 (template), byte[5] = subtype | byte[5] = damage type |
| speed | byte[7] | byte[16] |
| range | byte[8] | byte[17] |
| animation | byte[10] | byte[19] |

→ 환수와 character 모두 **speed/range/animation triplet** 을 공통 stat 으로 보유. 다만 environment 는 fixed offset 7-10, character 는 16-19 (offset shift +9). Layout 다르지만 game engine 의 internal stat dispatching 은 같은 layer.

## 산출

- `tools/converter/parse_h4_class_skill_fields.py` (신규)
- `work/h4/converted/h4_class_skill_fields.json` (35.7KB)
- `docs/h4/round102-class-skill-fields.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **24 alt-form 의 mode 매핑** (R101 후속) — alt-form 이 어떤 mode/condition 에서 활성화
2. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
3. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
4. **damage type 5/20/25 별 특성** (R102 후속) — 7+2+1=10 skill의 in-game 의미
5. **R100 milestone 결산 문서**
