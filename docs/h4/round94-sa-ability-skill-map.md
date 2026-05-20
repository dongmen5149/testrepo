# Hero4 Round 94 — `_H_SA` ability skill_id 카테고리 식별 (R88 후속)

> R88 의 24 ability slot 의 skill_id 8 종 {12,13,15,16,18,21,22,37} 이 R69 catalog 의
> 40 character class skill 에 대해 **global skill_id (0-39)** 로 매핑됨을 확정.

## TL;DR

| skill_id | class | 로컬 idx | skill name | tier values | bonus chain |
|---|---|---|---|---|---|
| 12 | S001 | 2 | 동시사격 | 10/20/30 | → 암즈강화 +5/10/15 |
| 13 | S001 | 3 | 급소사격 | 10/20/30 | — |
| 15 | S001 | 5 | 에이밍샷 | 10/20/30 | → 속사 +5/10/15 |
| 16 | S001 | 6 | 암즈트랩 | 10/20/30 | → 회피증가 +10/20/30 |
| 18 | S001 | 8 | 암즈강화 | 10/20/30 | — |
| 21 | S002 | 1 | 마검공격 | 5/10/15 | — |
| 22 | S002 | 2 | 텔레포트소드 | 10/25/40 | — |
| 37 | S003 | 7 | 마법강화 | 20/40/60 | — |

**Global skill_id 규칙**: `skill_id = class_index × 10 + local_index` (40 = 4 class × 10 skills).

## Class 분포 (8 ability)

| class | role | 가지는 ability 수 |
|---|---|---|
| S000 | 티르 양손검 (base) | **0** (default skills only) |
| **S001** | **루레인 사격 (shooter)** | **5 / 8 (deepest customization)** |
| S002 | 티르 마검 (mage-sword) | 2 (combat 변종) |
| S003 | 루레인 단도+마법 (소환사) | 1 (마법강화) |

## Design observations

1. **S001 dominance**: 5/8 ability + 3/3 bonus chain 모두 S001 — **사격(shooter) class 가 self-contained skill tree**. 다른 class 보다 customization depth 가 명백히 큼.
2. **S000 부재**: 티르의 양손검 base class 는 ability tier upgrade 가 **하나도 없음**. 게임 디자인 관점: S000 = "tutorial/default" class, S001 = "specialization" class.
3. **S002/S003 minimal**: 각 1-2 개만 — 이들은 mode-2 class (티르 마검 / 루레인 마법) 로 mode switch 시 활성화되며, 기본 stat tier 는 _H_SS 환수 시스템과 연동되어 ability tree 가 가벼움.
4. **Bonus chain 의 의미**: 4 ability (12, 15, 16, 18) 만 bonus 보유 — 모두 S001 사격 계열. 다른 S001/S002/S003 ability 4개는 단순 단일-skill tier upgrade.

## R88/R69 cross-ref 강화

- R69 의 "40 skills × 4 character classes" catalog 가 **global ID space (0-39)** 으로 명시적 통합 확인
- R88 의 unresolved skill_id 8 종이 모두 character class skill 풀에 존재
- R86-R87 의 환수 시스템 skill_id 5-20 (locally indexed for 환수) 와 character class skill_id 0-39 (globally indexed) 은 **별개의 ID space** 임이 확인됨

## R88 후속 미해결

- `bonus_id 0` 의미 (4 ability 는 bonus 가 없음 = no-bonus marker)
- tier_value 가 게임 내 어떻게 사용되는지 (max level cap? mp cost? base damage scaling?)
- `_H_SA` 가 character ability 와 환수 growth 를 한 파일에 묶은 이유 — 둘 다 "leveling-up tree" 공통점

## 산출

- `tools/converter/parse_h4_sa_ability_skill_map.py` (신규)
- `work/h4/converted/h4_sa_ability_skill_map.json` (9.7KB)
- `docs/h4/round94-sa-ability-skill-map.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **element byte[5]=2 검증** (R89 후속) — non-summon active skills 와 cross-ref
2. **Q_REPAY drop_id 의미** (R90 후속) — 32 entries 의 drop_id 검증
3. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
4. **n0124_scn tutorial 전문 분석** (R92 후속) — 환수 시스템 in-game 설명 전문
5. **bonus_id=0 의미 + tier_value 의미** (R94 후속)
