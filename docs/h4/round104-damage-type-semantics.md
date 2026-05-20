# Hero4 Round 104 — damage_type enum 별 특성 식별 (R102 후속)

> R102 의 byte[5] damage_type enum (0/5/20/25) 의 in-game 의미를 description text cross-ref 로 확정.

## TL;DR

| type | label | count | in-game 의미 |
|---|---|---|---|
| **0** | MAGIC_OR_SKILL | 54 | skill 자체 damage 값 사용 + MP 소비 (대다수 84.4%) |
| **5** | WEAPON_BASIC | 7 | weapon stat 기반 (skill damage = 0, character ATK 사용) |
| **20** | DEBUFF | 2 | 적 stat 감소 (방어도 감소 / 둔화) |
| **25** | WEAPON_SPECIAL | 1 | 특수 무기 콤보 (철의주먹 = 암즈 2콤보) |

## type=5 WEAPON_BASIC (7 skills, S000+S001 만)

모든 entries 가 **dmg=0** (자체 damage 값 없음) — character 의 weapon stat 사용.

| class | name | MP | description |
|---|---|---|---|
| S000 | 대검공격 | 0 | 양손검의 기본 콤보공격 |
| S000 | 기절의검 | 19 | 적을 공격하여 높은 확률로 스턴 |
| S000 | 유린의검 | 23 | 빠른 공격 후 후방으로 회피 |
| S001 | 사격 | 0 | 더블건의 기본 공격 |
| S001 | 산탄사격 | 15 | 전방을 향해 넓은 영역 사격 |
| S001 | 동시사격 | 1 | 더블건을 모아 더 강력한 사격 |
| S001 | 급소사격 | 4 | 치명상을 입혀 출혈을 유발 |

→ **무기 기반 skill** — character 의 ATK + 무기 stat 으로 damage 계산.

## type=20 DEBUFF (2 skills, S000 만)

| class | name | MP | description |
|---|---|---|---|
| S000 | 약화의검 | 1 | 강한 일격으로 적의 방어도를 감소 |
| S000 | 압도의검 | 22 | 적을 위축시켜 둔화시키는 공격 |

→ **상태 약화 skill** — defense 감소 / slow status. 직접 damage 보다 utility.

## type=25 WEAPON_SPECIAL (1 skill, S000 만)

| class | name | MP | description |
|---|---|---|---|
| S000 | 철의주먹 | 5 | 암즈로 2콤보 직접 타격 |

→ **특수 weapon combo** — 단일 unique skill. "암즈" = arms (weapon system) 와 연동. 추가 콤보 입력으로 발동.

## type=0 MAGIC_OR_SKILL (54 skills, 대다수)

skill 자체에 damage 값 보유 (예: 반동의영검 dmg=300). MP 소비하여 발동.

예시 (모든 magic-based skill 의 default):
- 반동의영검: MP=4, dmg=300 — 연타 추가타
- 회전의영검: MP=13, dmg=300 — 범위 공격
- 빙결의단도: MP=0, dmg=20 — 빙결 마법
- (S002/S003 의 모든 16+16 = 32 skill 이 type=0)

## Class 별 dtype 분포

| class | type=0 | type=5 | type=20 | type=25 | total |
|---|---|---|---|---|---|
| **S000** 양손검 | 10 | 3 | 2 | 1 | **16 (4 type 모두 보유)** |
| **S001** 사격 | 12 | 4 | 0 | 0 | 16 (2 type) |
| **S002** 마검 | 16 | 0 | 0 | 0 | 16 (1 type) |
| **S003** 마법 | 16 | 0 | 0 | 0 | 16 (1 type) |

## Design observations

1. **무기 클래스 (S000/S001) 만 WEAPON_BASIC (type=5) 보유**: 양손검과 사격 두 무기 class 가 dmg=0 의 weapon-based 공격을 가지며, 나머지 마검/마법 class 는 모두 skill-based damage 사용.

2. **S000 (양손검) 이 가장 다양한 dtype 보유** (4 type 모두): debuff (약화/압도의검) + special (철의주먹) + basic weapon + magic skill 의 조합 — 양손검 class 가 **전투 다양성** 의 핵심.

3. **type=0 dominance (84.4%)**: 대다수 skill 이 자체 damage 값 사용. 무기 stat 의존 skill 은 7/64 = 11% 만.

4. **DEBUFF + SPECIAL 은 S000 양손검 전용**: 마검/마법 class 는 magic-based 만 사용. 양손검은 "물리/debuff/특수 일체" character class.

## 산출

- `tools/converter/parse_h4_damage_type_semantics.py` (신규)
- `work/h4/converted/h4_damage_type_semantics.json` (13.7KB)
- `docs/h4/round104-damage-type-semantics.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
2. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
3. **환수 합신 / 환수특공 / 환수증폭 dialogue 검색** (R103 후속)
4. **R100 milestone 결산 문서**
5. **type=0 magic skill 의 sub-categorization** (R104 후속) — 54 skill 의 더 세분 분류
