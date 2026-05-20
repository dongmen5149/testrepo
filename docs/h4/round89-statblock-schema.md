# Hero4 Round 89 — 23B stat block 통합 schema 식별 + R87 정정

> R87 의 stat block field 표를 전수(21 block) 비교로 정정 + 확장.
> **3 template × 4 PASSIVE subtype** 카탈로그 확정.

## TL;DR

`_H_SS` 의 23B stat block 21 개 (boss 1 + summon active 11 + global passive 4 + divider 1) 분석.
- `byte[0]` 가 **template marker** (3종): ACTIVE_ATTACK(20) / DIVIDER(10) / PASSIVE_TEMPLATE(0)
- PASSIVE_TEMPLATE 에서 `byte[5]` 가 **subtype** 결정 (4종): SHIELD(6) / STATUS_PROC(7) / AURA(11) / PASSIVE(12)
- 모든 21 entry 가 schema 에 부합 (unknown 0건)

## R87 정정 사항

| 항목 | R87 추정 | R89 확정 |
|---|---|---|
| damage field | `byte[3]` 단일 (44/200/144/44/244) | `byte[3..4]` LE16 (300/200/400/300/500) |
| type field | `byte[0]` 통일된 type id | `byte[0]` = template marker, `byte[5]` = PASSIVE subtype |
| status/aura/passive 통일성 | 분리 분석 | 모두 `byte[0]=0` 으로 PASSIVE template 공유 |

## Template 카탈로그

### Template A — ACTIVE_ATTACK (`byte[0] = 0x14`, 5 entries) + DIVIDER (`0x0a`, 1 entry)

동일 schema 공유. divider 는 group separator 라서 별도 marker 사용.

| field | offset | 의미 |
|---|---|---|
| template_id | `byte[0]` | 0x14=basic, 0x0a=divider |
| damage      | `byte[3..4]` LE16 | 200-500 |
| element     | `byte[5]` | const 2 (= 마법속성?) |
| heal_flag   | `byte[6]` | 0=damage, 2=heal |
| speed       | `byte[7]` | 53 standard, 61 heal |
| range       | `byte[8]` | 100-160 |
| animation   | `byte[10]` | 3-20 |

| 환수 | name | damage | range | anim | heal? |
|---|---|---|---|---|---|
| 베놈       | 뇌격 | 300 | 120 | 4  | no |
| 헤지호그   | 뇌격 | 200 | 100 | 4  | no |
| 그래비티   | 뇌격 | 400 | 160 | 5  | no |
| 쇼커       | 뇌격 | 300 | 140 | 5  | no |
| 세이프가드 | 회복 | 500 | 100 | 20 | **yes** |
| (divider)  | 환수A공격 | 200 | 120 | 3 | no |

### Template B — PASSIVE_TEMPLATE (`byte[0] = 0x00`, 15 entries)

`byte[5]` 가 4 subtype 결정.

#### Subtype 6 — SHIELD (1 entry, paired_skill 실드)

| 위치 | 의미 |
|---|---|
| byte[6] | const 2 |
| byte[7] | shield strength (63) |
| byte[8] | cost (50) |
| byte[10] | animation (5) |
| byte[11-14] | secondary (HP/SP buff: value=17, subtype=2, anim=2) |

세이프가드 고유의 paired heal+shield skill.

#### Subtype 7 — STATUS_PROC (5 entries: 4 status + boss)

| 위치 | 의미 |
|---|---|
| byte[2] | 0 (일반), 5 (boss 망각의저주만) |
| byte[6] | reflect_flag (0=일반, 3=되돌리기) |
| byte[7] | strength/duration |
| byte[8] | cost (1, boss=0) |
| byte[10] | animation (1) |

| 환수 | name | strength | reflect | cost |
|---|---|---|---|---|
| (boss)     | 망각의 저주 | 66 | 0 | 0 |
| 베놈       | 맹독       | 85 | 0 | 1 |
| 헤지호그   | 되돌리기   | 86 | **3** | 1 |
| 그래비티   | 슬로우     | 75 | 0 | 1 |
| 쇼커       | 스턴       | 76 | 0 | 1 |

#### Subtype 11 — AURA (5 entries, 환수당 1개)

| 위치 | 의미 |
|---|---|
| byte[6] | const 2 (aura marker) |
| byte[7] | aura strength |
| byte[8] | cost (1 또는 2) |
| byte[10] | animation (1 또는 2) |
| byte[11] | secondary buff value (HP/SP boost) |
| byte[12] | secondary subtype |
| byte[14] | secondary anim |

| 환수 | name | strength | cost | anim | secondary[11,12,14] |
|---|---|---|---|---|---|
| 베놈       | 저주의 오러 | 25 | 1 | 1 | [0, 0, 0]   |
| 헤지호그   | 강화의 오러 | 2  | 1 | 1 | [6, 1, 1]   |
| 그래비티   | 마법의 오러 | 15 | 1 | 1 | [30, 1, 1]  |
| 쇼커       | 마력의 오러 | 8  | 2 | 2 | [0, 0, 0]   |
| 세이프가드 | 보호의 오러 | 16 | 1 | 1 | [17, 1, 1]  |

3 환수 (헤지호그/그래비티/세이프가드) 가 secondary HP/SP buff 동반.

#### Subtype 12 — PASSIVE (4 entries, 글로벌 소환사 강화)

| 위치 | 의미 |
|---|---|
| byte[6] | const 3 (passive marker) |
| byte[7] | skill_id (91-94 = 0x5b-0x5e) |
| byte[8] | level (const 2) |
| byte[10] | 0 |

| name | skill_id |
|---|---|
| 마법력강화 | 91 |
| 교감도강화 | 92 |
| 체력강화   | 93 |
| 정신강화   | 94 |

## 통합 schema 표 (memo card)

```
byte[0]:
  0x14 → ACTIVE_ATTACK   { damage_le16(3-4), element(5), heal(6), speed(7), range(8), anim(10) }
  0x0a → DIVIDER         (ACTIVE_ATTACK 와 동일 schema)
  0x00 → PASSIVE_TEMPLATE:
    byte[5]:
      6  → SHIELD         { flag(6)=2, str(7), cost(8), anim(10), 2nd(11-14) }
      7  → STATUS_PROC    { reflect(6), str(7), cost(8), anim(10), boss_marker(2) }
      11 → AURA           { const(6)=2, str(7), cost(8), anim(10), 2nd(11-14) }
      12 → PASSIVE        { const(6)=3, skill_id(7), lvl(8)=2 }
```

## 미확정 사항

- `element` byte[5]=2 의 의미 (속성? 단순 marker?) — 모든 attack 동일값이라 검증 불가
- `secondary subtype` byte[12] 의 1 vs 2 차이 (3 entries 1 vs 1 entry 2)
- DIVIDER 는 stat 가 실제 effect 인지 placeholder 인지 불명

## 산출

- `tools/converter/parse_h4_statblock_schema.py` (신규)
- `work/h4/converted/h4_statblock_schema.json` (17.5KB)
- `docs/h4/round89-statblock-schema.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **Q_REPAY idx ↔ R70 quest name 매핑** (R85 후속) — 200 - 128 = 72 차이 해소
2. **보스 phase stat 강화율 정량** (R80 후속) — 오토마톤 5 phase 비교
3. **dialogue corpus 환수 등장 빈도** (R87 후속) — 베놈/헤지호그 × 35,752 대사
4. **`_H_SA` group_id ↔ 5 환수 매핑 검증** (R88 후속) — group 0/64/78/38/75
5. **`_H_SA` ability skill_id {12-37} 카테고리 식별** (R88 후속)
6. **element byte[5]=2 검증** — non-summon active skills 와 cross-ref (R89 후속)
