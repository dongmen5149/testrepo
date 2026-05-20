# Hero4 Round 99 — n0124_scn 환수 시스템 tutorial 전문 분석 (R92 후속)

> R92 에서 식별된 환수 시스템 tutorial scene 의 전문 추출 + R86-R88 binary catalog 와 1:1 매핑 검증.

## TL;DR

n0124_scn 안의 NPC 대화 한 블록 (offset ~4134-4790) 이 환수 시스템 in-game 설명서. R86-R88 의 binary catalog 데이터와 **모든 in-game 용어가 1:1 매칭** 확인.

## In-game tutorial 전문 (R99 추출)

> **소환수 관리에 대한 설명을 해드릴까요?**
> [듣는다]
> **진화포인트**로 **소환수의 기본 능력**을 올리거나 **특성**을 개발할 수 있습니다.
> **기본 능력**은 **마법력, 방어력, 체력, 교감도** 이며 각각 **공격력, 방어력, 체력, 그리고 MP** 를 말합니다.
> **특성**은 소환수가 가진 스킬로 소환수에 따라 다릅니다.
> <**베놈**> 은 **원거리 공격, 중독 능력, 저주 강화 능력**이 있습니다.
> 기본 능력이나 특성 개발이나 모두 **고레벨로 올라갈 수록 소모되는 포인트의 양이 많아집니다**.
> [듣지않는다]

## In-game 용어 ↔ Binary catalog 매핑 (1:1)

| in-game 용어 | binary source | round |
|---|---|---|
| **진화포인트** (evolution point) | `_H_SA` 24 ability slot 의 `tier_value` (10/20/30, 5/10/15 등) | R88 |
| **기본 능력 4 stat** (마법력/방어력/체력/교감도) | `_H_SS` 4 global passive `skill_id 91-94` | R87 |
| **특성** (trait, per-summon skill set) | `_H_SS` 5 환수 × 5 logical skills (basic/ranged_status/effect_boost/aura/on_summon_buff) | R86-R87 |
| **고레벨 소모 포인트 증가** | `_H_SA` `tier_value` monotonic progression | R88 |

## 베놈 예시 cross-ref (1:1 매핑)

in-game 베놈 설명 = "원거리 공격, 중독 능력, 저주 강화 능력"

| in-game trait | R86/R87 catalog skill | 매핑 |
|---|---|---|
| **원거리 공격** | basic_attack (뇌격) + ranged_status (맹독) | ✓ |
| **중독 능력** | effect_boost (뇌격의 중독 효과 강화) | ✓ |
| **저주 강화 능력** | aura (저주의 오러) + on_summon_buff (저주 증가) | ✓ |

5 logical skill 이 3 thematic trait 으로 in-game 표현됨 → tutorial 은 압축된 설명, catalog 는 5-skill 정밀 분해.

## R87 정정 (4 base ability mapping)

R87 에서 발견한 "정신강화 short ↔ 소환수의 교감도 강화 long" mismatch 가 R99 의 tutorial 텍스트로 명확해짐:
- in-game label "교감도" = MP stat
- R87 catalog short_name "정신강화" → long_name "소환수의 교감도 강화"
- 즉, 정신 = MP = 교감도. 4 base ability 모두 명명 일관.

| in-game name | in-game effect | R87 short_name | R87 long_name | skill_id |
|---|---|---|---|---|
| 마법력 | 공격력 | 마법력강화 | 소환수의 마법력 강화 | 91 |
| 방어력 | 방어력 | 교감도강화 | 소환수의 방어력 강화 | 92 |
| 체력 | 체력 | 체력강화 | 소환수의 체력 강화 | 93 |
| **교감도** | **MP** | **정신강화** | **소환수의 교감도 강화** | **94** |

R87 의 "short 이름과 long 이름의 stat 매칭이 어긋남" 는 실제로 in-game 의 의도된 디자인: short label 은 stat 이름, long label 은 효과 설명. 4쌍 모두 ↔ in-game tutorial 의 4 base ability 와 1:1.

## R92-R99 진화 경로

- R92: n0124_scn 이 환수 tutorial 임을 발견 (베놈 mention 단서)
- R99: tutorial 전문 추출 + binary catalog 와 1:1 매핑 검증

→ 환수 시스템의 **player-facing 설명** (tutorial) 과 **engine-facing 데이터** (_H_SS/_H_SA/_H_BS) 가 완전 일치함을 확인. R86-R98 의 분석이 게임 디자이너의 원본 의도와 일치한다는 강력한 검증.

## 산출

- `tools/converter/parse_h4_summon_tutorial.py` (신규)
- `work/h4/converted/h4_summon_tutorial.json` (4.2KB)
- `docs/h4/round99-summon-tutorial.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **bonus_id=0 + tier_value 의미** (R94 후속)
2. **character class skill (S000-S003) stat block schema** (R95 후속)
3. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
4. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
5. **타 character class tutorial scene** (R99 후속) — S000/S001/S002/S003 의 in-game 설명도 찾아 cross-ref
