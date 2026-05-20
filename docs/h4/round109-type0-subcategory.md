# Hero4 Round 109 — type=0 magic skill sub-categorization (R104 후속)

> R104 의 type=0 (MAGIC_OR_SKILL) 54 skill (전체 64 skill 의 84.4%) 의 design intent 세분화.

## TL;DR

description text + name + dmg 기반 11 sub-category 분류:

| category | count | semantic |
|---|---|---|
| **PASSIVE_DEEP** | **16** | name "\|" prefix — lvl_req=11 passive layer (정확히 4 class × 4 passive) |
| **ACTIVE_BUFF_SELF** | 10 | self enhancement (회복/극대/SP 충전/은신/쿨타임 감소) |
| ACTIVE_BASIC | 3 | 기본 단발/콤보 공격 |
| ACTIVE_MULTI_HIT | 2 | 연속/추가타 (반동의영검, 더블암즈샷) |
| ACTIVE_STATUS_HIT | 1 | 공격 + status 유도 (크리티컬샷 스턴) |
| ACTIVE_AOE | 5 | 범위/연속/대지/낙하 |
| ACTIVE_DASH | 3 | 돌격/텔레포트 (gap-closer) |
| ACTIVE_TRAP | 2 | 설치형 (암즈트랩, 정화의장벽) |
| ACTIVE_ELEMENT | 5 | 화염/빙결/얼음 elemental |
| **ACTIVE_DEBUFF** | **3** | S003 전용 magic debuff (저주/암흑) |
| **ACTIVE_COMBO** | **4** | 환수 융합 — S002/S003 만 |

총 **54 = 16 + 10 + 3 + 2 + 1 + 5 + 3 + 2 + 5 + 3 + 4** ✓

## Class layered distribution (4 character class)

R101 schema (4 class × 16 entry) 와 정합:

| class | passive | buff | basic | multi | status | aoe | dash | trap | element | debuff | combo | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **S000 양손검** | 4 | 3 | — | 1 | — | 1 | 1 | — | — | — | — | **10** |
| **S001 사격** | 4 | 4 | 1 | 1 | 1 | — | — | 1 | — | — | — | **12** |
| **S002 마검** | 4 | 2 | 2 | — | — | 1 | 2 | — | 3 | — | 2 | **16** |
| **S003 마법** | 4 | 1 | — | — | — | 3 | — | 1 | 2 | 3 | 2 | **16** |
| total | **16** | 10 | 3 | 2 | 1 | 5 | 3 | 2 | 5 | 3 | 4 | **54** |

(S000/S001 total < 16 인 이유 = R104 의 type=5 WEAPON_BASIC 7 entries (S000 3 + S001 4) 를 제외했기 때문)

## Mode layer 모델 (R101/R103 정합)

R101 32B class skill 의 4×16 schema 와 R103 의 mode-0/mode-1 분리 가설을 종합:

| layer | category | count | lvl_req 패턴 |
|---|---|---|---|
| **passive_layer** | PASSIVE_DEEP | 16 (4×4) | lvl_req=11 (deep tree) |
| **mode_0_basic_layer** | BASIC + MULTI + STATUS + ELEMENT | 3+2+1+5 = **11** | lvl_req=0/3 (low) |
| **mode_0_charge_layer** | BUFF_SELF + AOE | 10+5 = **15** | lvl_req=3/5 (mid-low) |
| **mode_1_advanced_layer** | DASH + TRAP + DEBUFF + COMBO | 3+2+3+4 = **12** | lvl_req=5/6/10 (mid-tier, R103 alt-form 비중) |

→ **mode_1 advanced layer 12 = R103 의 24 alt-form 의 절반** (type=0 만; type=5/20/25 alt-form 도 합산하면 24 일치)

## 4 class 의 design philosophy

### S000 양손검 (티르 mode 0) — "물리 + 다양성"
- 가장 적은 type=0 (10) — R104 의 WEAPON_BASIC/DEBUFF/SPECIAL 6 skill 사용
- buff(3) + multi(1) + aoe(1) + dash(1) — **물리 전투 specialist**
- ELEMENT/COMBO/DEBUFF 부재 — magic class 와 명확히 분리

### S001 사격 (루레인 mode 0) — "장거리 + 유틸리티"
- buff(4) 최다 — 차징암즈샷/은신/광폭/지축 — **준비-발동 패턴**
- TRAP(1) 보유 — 암즈트랩 — 유일하게 trap 보유한 무기 class
- ELEMENT/COMBO 부재 — 물리 class

### S002 마검 (티르 mode 1) — "근접 마법 + 환수"
- ELEMENT(3) — 양단/프레임/아이스 인첸트 (화염/빙결 부여)
- DASH(2) — 텔레포트소드 + 관통 — 가장 많은 gap-closer
- COMBO(2) — 소울웨이브 + 환수 합신 — 환수 융합 시작

### S003 마법 (루레인 mode 1, 소환사) — "원거리 + 환수 + 저주"
- DEBUFF(3) **전용** — 암흑/쇠약의저주/반사의저주
- AOE(3) 최다 — 정화의구/빙결의대지/정화의심판
- COMBO(2) + 환수흡수(buff) — **환수 시스템 핵심 class**
- DASH/MULTI/STATUS/TRAP 부재 (TRAP 1 만)

## 검증 포인트

1. ✅ **PASSIVE_DEEP = 16 = 정확히 4 class × 4** — R101/R102 schema 의 passive layer 와 일치
2. ✅ **ACTIVE_COMBO = S002+S003 만** — R86–R108 환수 시스템과 일치
3. ✅ **ACTIVE_DEBUFF = S003 만** — R104 type=20 (S000-only) 과 분리된 마법 debuff
4. ✅ **ACTIVE_ELEMENT = S002+S003 만** — 마검/마법 class 만 elemental
5. ✅ **mode_1 advanced layer 12** ≈ R103 의 24 alt-form 의 type=0 분량

## 산출

- `tools/converter/parse_h4_type0_subcategory.py` (신규)
- `work/h4/converted/h4_type0_subcategory.json` (18.1KB)
- `docs/h4/round109-type0-subcategory.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. ~~environments combo dialogue~~ ✅ R108
2. ~~type=0 sub-cat~~ ✅ R109
3. ⭐ **R100 milestone 결산 문서** (`docs/h4/MILESTONE_R100.md` — R68–R109 누적, Hero5 R100 마일스톤 패턴)
4. **alt-form 24 × type=0 sub-cat cross-check** (R103 후속) — 24 alt-form 중 type=0 비중 vs primary type=0 분포
5. 사용자 트랙: A1 영어 번역, Phase C Step 4d
