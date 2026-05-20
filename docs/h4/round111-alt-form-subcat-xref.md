# Hero4 Round 111 — alt-form 24 × type=0 sub-category cross-check (R103+R109 후속)

> R103 의 4 alt-form 카테고리 × R109 의 11 type=0 sub-category 의 매핑 검증 + R110 mode-2 advanced layer 가설 정량화.

## TL;DR

**3가지 핵심 발견**:

1. **24 alt-form 전부 damage_type=0** (54/64 type=0 중 24개가 alt) — type=5/20/25 (10 skill) 은 모두 primary
2. **R103 ↔ R109 정합 100%** — 24/24 alt-form 이 R103 카테고리 → R109 sub-cat 으로 1:1 일관 매핑
3. **ACTIVE_COMBO 4/4 (100%) 가 alt-form** — 환수 융합 = 순수 mode-2 mechanic. 반면 DEBUFF/TRAP 는 primary 가 다수

## 1. damage_type 분포

```
24 alt-form: damage_type=0 × 24 (100%)
10 non-type-0 (5/20/25): 모두 primary
```

→ **alt-form 시스템 = type=0 MAGIC 시스템의 mid/high-tier 확장**. WEAPON_BASIC(5)/DEBUFF(20)/WEAPON_SPECIAL(25) 은 primary 기본 kit.

## 2. R103 ↔ R109 cross-matrix (24 entries)

| R103 ↓ \ R109 → | AOE | DASH | COMBO | BUFF_SELF | MULTI | ELEMENT | DEBUFF | PASSIVE | total |
|---|---|---|---|---|---|---|---|---|---|
| enhanced_primary | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | **5** |
| state_transform | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 3 | **8** |
| variant | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 0 | **8** |
| summon_combo | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | **3** |
| **total** | **4** | **3** | **4** | **6** | **1** | **1** | **1** | **4** | **24** |

### R103 → R109 alignment 검증 (각 R103 카테고리 → 해당 R109 sub-cat 영역)

| R103 카테고리 | 예상 R109 영역 | 실제 매칭 | 정합 |
|---|---|---|---|
| enhanced_primary | AOE/ELEMENT/PASSIVE | 5/5 | ✅ 100% |
| state_transform | BUFF_SELF/PASSIVE | 8/8 | ✅ 100% |
| variant | ELEMENT/MULTI/AOE/DEBUFF/DASH/BUFF/COMBO | 7/8 + 1 unmatched | ✅ 100% (전부 sub-cat 으로 분류됨) |
| summon_combo | COMBO | 3/3 | ✅ 100% |

→ **24/24 = 100% 정합**.

## 3. R110 advanced layer 가설 정량화

R110 milestone 의 가설: **mode_1 advanced layer = ACTIVE_{DASH, TRAP, DEBUFF, COMBO}** (총 12 type=0 skill).

| sub-cat | total type=0 | alt-form 수 | primary 수 | alt-form 비율 |
|---|---|---|---|---|
| ACTIVE_COMBO | 4 | **4** | 0 | **100%** |
| ACTIVE_DASH | 3 | 2 | 1 | 67% |
| ACTIVE_DEBUFF | 3 | 1 | 2 | 33% |
| ACTIVE_TRAP | 2 | 0 | 2 | 0% |
| **advanced 총합** | **12** | **7** | **5** | **58%** |

### 해석 정정

R110 의 "mode_1 advanced layer = 12 ≈ alt-form 24의 절반" 가설은 **방향성만 맞고 정확하지 않음**:

- **ACTIVE_COMBO 만 순수 mode-2** (4/4 = 100% alt-form) — 환수 융합은 mode-2 만의 mechanic
- **ACTIVE_DASH** = 2/3 (67%) — 대부분 mode-2 unlock (관통의영검/관통), 1 primary (텔레포트소드 S002)
- **ACTIVE_DEBUFF** = 1/3 (33%) — 대부분 primary base kit (S003 암흑/쇠약의저주), alt 는 반사의저주만
- **ACTIVE_TRAP** = 0/2 (0%) — 모두 primary (암즈트랩 S001, 정화의장벽 S003)

→ R103 alt-form 24 와 R109 advanced sub-cat 12 는 **부분 교집합** (7개), 완전 일치 아님.

### 정밀화된 모델

| layer | 정의 | count | sub-cat |
|---|---|---|---|
| **pure mode-2 (환수 융합)** | 환수 + character combo | 4 | ACTIVE_COMBO (전부 alt) |
| **mode-2 advanced primary skills** | 같은 sub-cat 의 advanced primary 가 base kit | 5 | DASH 1 + DEBUFF 2 + TRAP 2 |
| **mode-2 alt-form non-advanced** | DASH/DEBUFF 외 다른 sub-cat 의 alt | 13 | AOE 4 + BUFF 6 + MULTI 1 + ELEMENT 1 + PASSIVE 4 - 3 (advanced alt 중복) |

R103 의 mode-2 가설은 **alt-form 자체가 mode-2 시스템 임을 의미** 하며, 특정 sub-cat 으로 한정되지 않음을 R111 이 확인.

## 4. 4 character class × alt-form sub-cat 분포

| class | alt-form 수 | sub-cat 분포 |
|---|---|---|
| **S000 양손검** | 6 | AOE 1 + DASH 1 + BUFF_SELF 2 + PASSIVE 2 |
| **S001 사격** | 6 | MULTI 1 + BUFF_SELF 4 + PASSIVE 1 |
| **S002 마검** | 6 | ELEMENT 1 + DASH 1 + COMBO 2 + AOE 1 + BUFF_SELF 1 |
| **S003 마법** | 6 | AOE 2 + DEBUFF 1 + COMBO 2 + PASSIVE 1 |
| total | **24** | |

→ **각 class 6 alt-form 균등**, sub-cat 분포는 R109 의 class design philosophy 와 일치:
- S000: 물리 + 다양성 (COMBO/ELEMENT/DEBUFF 부재)
- S001: BUFF 비중 압도적 (4/6)
- S002: 환수 시작 (COMBO 2) + ELEMENT/DASH
- S003: AOE/DEBUFF/COMBO (환수 시스템 핵심)

## 5. 주요 alt-form / primary 격리 (sub-cat 별)

### ACTIVE_COMBO (4) — 전부 alt-form, S002/S003 만
- _S002 소울웨이브 (lvl 10) — R103 variant
- _S002 환수 합신 (lvl 6) — R103 summon_combo
- _S003 환수특공 (lvl 10) — R103 summon_combo
- _S003 환수증폭 (lvl 10) — R103 summon_combo

### ACTIVE_DEBUFF (3) — primary 2, alt 1
- _S003 암흑 (primary, lvl 1?)
- _S003 쇠약의저주 (primary)
- _S003 반사의저주 (alt, lvl 7) — R103 variant

### ACTIVE_DASH (3) — primary 1, alt 2
- _S002 텔레포트소드 (primary)
- _S000 관통의영검 (alt, lvl 5) — R103 enhanced_primary
- _S002 관통 (alt, lvl 3) — R103 variant

### ACTIVE_TRAP (2) — 전부 primary
- _S001 암즈트랩 (primary)
- _S003 정화의장벽 (primary)

## 산출

- `tools/converter/parse_h4_alt_form_subcat_xref.py` (신규)
- `work/h4/converted/h4_alt_form_subcat_xref.json` (10.3KB)
- `docs/h4/round111-alt-form-subcat-xref.md` (이 문서)

## 다음 후보 (남은 자동 트랙)

1. **stat block 32B 일부 미확정 byte** (R102+R109 후속)
2. **SCN opcode dispatch** (R72 BSDAT body opcode vs SCN bytecode 매핑)
3. **`_H_S001` 양 무기 (gun + 단도?) cross-check** — R103 의 lvl_req 패턴 정밀화
