# Hero4 Round 101 — character class skill (S000-S003) stat block schema 정밀 (R95 후속)

> R95 의 미해결 character skill 구조 확정. R69 catalog 가 누락한 24 alt-form skill 추가 발견.

## TL;DR

`_H_S000-_H_S003` 4 파일 모두 **16 entries × 4 = 64 skill** 보유. R69 catalog 의 40 skill 은 primary skill 만 카운트했고, **24 alt-form** (= prefix entries) 가 추가로 존재.

각 entry 의 layout (자가검증 통과):

```
[size:1B][00][nlen:1B][name:EUC-KR][stat_block:32B][desc_len:1B][desc:1B='{' + EUC-KR text]
```

자가검증: `body[32]` (desc_len field) == `len(body) - 32`. 64/64 entries 모두 부합.

## 64 skill 분포

| 파일 | role | primary | alt-form | total |
|---|---|---|---|---|
| `_H_S000` | 티르 양손검 (base) | 10 | 6 | 16 |
| `_H_S001` | 루레인 사격 (shooter) | 10 | 6 | 16 |
| `_H_S002` | 티르 마검 (mage-sword) | 10 | 6 | 16 |
| `_H_S003` | 루레인 단도+마법 (소환사) | 10 | 6 | 16 |
| **total** | | **40** | **24** | **64** |

→ alt-form 패턴 (`= 이름` prefix) 균일 — 4 class 각각 정확히 6 alt-form 보유.

## Alt-form 가설 (R81 cross-ref)

R81 발견: 2 영웅 × 2 mode = 4 character class slot. 각 class 의 6 alt-form 은 **mode-2 alt skill** 가능성:
- primary = mode 0 (또는 default) skill
- alt-form = mode 1 (또는 advanced) skill

예시 (`_H_S000` 양손검):
- primary: 대검공격, 반동의영검, 기절의검, 유린의검, 찰라의영검, 철의주먹, 약화의검, 압도의검, 철벽방어, 분노축적
- alt-form: 회전의영검, 관통의영검, 격노, 금강귀, ... (6개)

## 32B stat block field 후보

R101 sample analysis (S000 첫 3 entries):

| skill | MP[0] | damage[3-4] LE16 | dtype[5] | lvl_req[8] | desc 예시 |
|---|---|---|---|---|---|
| 대검공격 (basic) | 0 | 0 | 5 | 0 | "양손검의 기본 콤보공격" |
| 반동의영검 | 4 | 300 | 0 | 3 | "연타로 추가타 가능한 띄우기 공격" |
| 기절의검 | 19 | 0 | 5 | 3 | "적을 공격하여 높은 확률로 스턴" |

Field candidates:
- `byte[0]` = MP cost (0-23 varies, 0 for basic attack)
- `byte[1-2]` = flags / 0xff marker
- `byte[3-4]` LE16 = damage (0 for stun-type, 300+ for damage skills)
- `byte[5]` = damage type (0 = magical?, 5 = physical?)
- `byte[8]` = skill level requirement (0 = always available, 3+ = tier locked)
- `byte[16-19]` = speed/range/anim cluster (R101 미정밀)
- `byte[20-31]` = mostly zero padding

## R69 정정

R69 (`h4_skills.json` / catalog 의 `skill_sets`) 는 4 class × **10 skill** 만 보고. R101 검증으로 **+24 alt-form** 추가 발견.

R69 누락 이유 추정: R69 parser 가 nlen 의 모든 변형 (특히 `= ` prefix) 을 정상 entry 로 인식 못함. R101 검증 (body[32] 자가검증) 적용시 64/64 통과.

## Description 구조

description = `{` (1B opener) + EUC-KR text. 일부 entry 는 `}SP3` 같은 suffix (SP cost) 포함:
- 반동의영검: "{연타로 추가타;가능한 띄우기;공격 }**SP3**"
- 즉 `{...}` 묶음 후 `SP[숫자]` = SP 비용 표기

→ 게임 내 skill 설명 UI 와 SP 비용 표기가 함께 저장됨.

## R95 통합 결론

R95 의 "character skill 별개 schema" 가설 검증:
- ✅ ACTIVE_ATTACK template (`byte[0]=0x14`) 미사용
- ✅ 가변 길이 body
- ✅ EUC-KR description suffix 포함
- ✅ 32B stat block + 1B desc_len header

`_H_SS` (환수) schema 와 별개의 layer임을 확인. 환수는 23B fixed stat block, character skill 은 32B stat block + desc.

## 산출

- `tools/converter/parse_h4_class_skill_schema.py` (신규)
- `work/h4/converted/h4_class_skill_schema.json` (46KB)
- `docs/h4/round101-class-skill-schema.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
2. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
3. **타 character class tutorial scene** (R99 후속) — S000-S003 in-game 설명 검색
4. **R100 milestone 결산 문서** (Hero5 MILESTONE_R100.md 처럼)
5. **32B stat block field 정밀** (R101 후속) — byte[16-19] speed/range/anim 식별
6. **24 alt-form 의 mode 매핑** (R101 후속) — alt-form 이 어떤 mode 또는 condition 에서 활성화되나
