# Hero4 Round 103 — 24 alt-form mode 매핑 (R101 후속)

> R101 의 alt-form (`= 이름` prefix) 24개의 활성화 mode/condition 분석.

## TL;DR

24 alt-form 의 stat/이름/lvl_req 패턴 분석 결과:
- alt-form 은 primary skill 의 **확장/advanced variant** — 같은 어근 공유
- 평균 MP cost: primary 12.6 → alt 19.0 (약 **1.5× 높음** = 고급 skill)
- **환수 합신/특공/증폭 3개 = 환수 시스템 cross-link** (S002/S003 의 advanced 환수+character combo skill)
- R81 의 2 mode 구조와 정합: **mode-2 skill 으로 추정**

## Primary vs Alt-form 비교

| 항목 | primary (40) | alt-form (24) | 차이 |
|---|---|---|---|
| MP mean (nonzero) | 12.6 | **19.0** | 1.5× 높음 |
| lvl_req=0 (always) | 5 | 0 | alt 는 unlock 필요 |
| lvl_req=3 | 14 | 6 | primary 비중 큼 |
| lvl_req=11 (passive deep) | 12 | 4 | primary passive 대부분 |
| lvl_req=5/6/10 | 6 | 10 | alt 가 mid-tier 비중 큼 |

→ alt-form 은 mid-tier (5/6/10) 에서 unlock 되는 advanced variant.

## Alt-form 카테고리 분포

| category | count | 예시 |
|---|---|---|
| **enhanced_primary** | 5 | 빙결의대지(빙결의 확장), 정화의심판, 마법단련 |
| **state_transform** | 8 | 은신, 광폭, 지축, 격노, 금강귀, 집중력, 체질개선, 강타연마 |
| **variant** | 8 | 회전의영검, 관통의영검, 양단, 관통, 소울웨이브, 절륜, 헤이스트, 차징암즈샷, 더블암즈샷, 반사의저주 |
| **summon_combo** | 3 | 환수 합신 (S002), 환수특공 / 환수증폭 (S003) |

## ★ Summon-linked alt-forms (3)

S002/S003 의 환수 시스템 cross-link skill:

| class | name | lvl | MP | dmg | 의미 |
|---|---|---|---|---|---|
| _H_S002 (티르 마검) | **환수 합신** | 6 | 27 | 300 | 환수 + 티르 마검 mode 합체 skill |
| _H_S003 (루레인 마법) | **환수특공** | 10 | 24 | 210 | 환수 + 루레인 마법 mode 특공 |
| _H_S003 (루레인 마법) | **환수증폭** | 10 | 28 | 210 | 환수 + 루레인 마법 amplification |

R86-R99 의 환수 시스템과 character skill 시스템의 **gameplay 연결점**. 마검/마법 mode 에서 환수와 조합한 advanced combo skill.

또한 S003 primary 의 `환수흡수` (lvl 10) + `흡혈환수` (lvl 11) 와 함께 환수 시스템이 S003 (루레인 마법 = 소환사 class) 의 핵심임을 재확인.

## R81 mode 구조 부합

R81: "2 영웅 (티르/루레인) × 2 mode (mode 0/mode 1) = 4 character slot"

R103 매핑 가설:
- mode 0 (default): 10 primary skill 사용
- mode 1 (advanced): 6 alt-form skill 추가 활성

근거:
1. ✅ alt-form 모든 skill 이 advanced variant (mid-tier unlock)
2. ✅ alt-form 평균 MP cost 가 primary 보다 명백히 높음 (1.5×)
3. ✅ alt-form 이름이 primary 어근 공유 (영검 → 회전의영검, 빙결의단도 → 빙결의대지)
4. ✅ alt-form 에 환수 합체 skill 포함 (mode 변경 = 환수 sync)
5. ✅ alt-form lvl_req=11 (passive deep) 부재 — primary passive 와 다른 layer

S002 의 환수 합신 (lvl 6) 은 mode 1 진입 보스 skill / 또는 환수 등록 시 활성화되는 special skill.

## R86-R103 누적 환수 ↔ character 연결

| Layer | skill | class | 의미 |
|---|---|---|---|
| 환수 primary | 뇌격/맹독/슬로우/스턴/실드 (5종 × 5 환수) | _H_SS | 환수 본인 skill (R86-R87) |
| 환수 ability tree | 8 ability × 3 tier | _H_SA | character 가 환수 양육 (R88, R94) |
| character → 환수 | 환수흡수 (S003 lvl 10) | _H_S003 | character 가 환수 흡수 |
| 환수 + character combo | **환수 합신/특공/증폭** | _H_S002/_H_S003 | mode-2 combo skill (R103 신규 발견) |
| 4 글로벌 강화 | 마법력강화/교감도강화/체력강화/정신강화 | _H_SS | 4 base ability (R87, R99) |

## 산출

- `tools/converter/parse_h4_alt_form_mode.py` (신규)
- `work/h4/converted/h4_alt_form_mode.json` (9.7KB)
- `docs/h4/round103-alt-form-mode.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **damage type 5/20/25 별 특성** (R102 후속) — 10 skill 의 in-game 의미
2. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
3. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
4. **R100 milestone 결산 문서**
5. **환수 합신 / 환수특공 / 환수증폭 in-game 발견 가능성** (R103 후속) — dialogue corpus 에 등장하는지 검색
