# Skill desc placeholder 의 실제 stat source 분석 (R105)

> R75 `resolve_skill_desc` 의 `stats_u16[NN]` 치환 가설이 실 데이터로 검증 불가능함을 R105 가 경험적으로 확인. 정확한 stat source 는 Formula::calc 런타임 — 미통합.

## 1. R90 placeholder 시스템 요약

- Spirit / class skill desc 는 `}#NN<unit>|` 형식 placeholder 를 포함
  (예: `정령마력 }#05%|의 피해를 준다`, `재사용대기 }#09초|`)
- R75 의 `resolve_skill_desc` 가 `stats_u16[NN]` 값으로 `#NN` 을 치환
- R90 의 `resolve_skill_desc_display` 가 `}TEXT|` → `[TEXT]` + `;` → `\n` 정제

## 2. R105 실측 데이터

### 2.1 spirit (class_5) 16 record 의 placeholder 분포

```
Spirit  desc placeholder              stats_u16 index 값 (모든 spirit 동일)
─────────────────────────────────────────────────────────────────────
#0  암흑탄    }#05%|                  u16[5]=7728   ← 고정 상수
#1  마법기    }#06%|                  u16[6]=23808  ← 고정 상수
#2  영혼의회복 }#08초|                 u16[8]=0
#3-#15 다양     #05%|/#08초|/#12배|     동일 상수만 반복
```

### 2.2 class_0 (Warrior) 43 skill 의 patten

```
#1 광폭      stats=[4,0,0,26624,8,20528,23808,1] → #05%|=20528 (불가능)
#2 강타     stats=[7,0,0,26624,8,41008,23808,1] → #05%|=41008 (불가능)
#3 추격타격   stats=[4,0,0,26624,8,41008,23808,1] → #05%|=41008
#6 통격     stats[8]=-1 (signed) → #08초|=-1 (불가능)
```

### 2.3 결론

- **stats_u16[5]/[6]/[8]/[12]** 가 spirit/class 모두 같은 상수 (7728, 23808, 0, 32569)
  → 이 위치들은 **file 의 헤더 magic / struct padding bytes** 이지 stat 값이 아님
- 실측 값들 (20528, 41008, -1) 은 모두 일반적인 게임 stat 범위 (0..200) 를 벗어남
- 즉 **R75 의 `stats_u16[NN]` 가설은 잘못된 매핑** — placeholder NN 의 실제 source 는 다른 곳

## 3. 실제 stat source 추정

R72/R73 의 ProcHeroSkill RE 결과를 종합하면, 실 게임에서 desc 의 stat 값은:

1. **Formula::calc** (HSI+0x30 의 dynamic_formula_id) 가 HERO stats + 스킬 baseline 으로 계산
2. **HSI runtime field** (R72 의 +0x44/+0x46/+0x48 등 — 단 R79 에서 dead reads 로 확정)
3. **per-class lookup table** (HSI base 영역 +0x00..+0x43 의 file-loaded 7 field 중 일부)

placeholder `#NN` 의 NN 값은 **stat 종류 enum** (예: damage%=5, cooldown_sec=9, duration=8, multiplier=12) 이며, 각 값은 Formula::calc(formula_id, HERO_stat_pack) 로 도출.

## 4. R105 휴리스틱 fallback + R106 의미 label

R105: `game_data.gd::resolve_skill_desc` 가 stat 값이 `PLACEHOLDER_UNREASONABLE_THRESHOLD (500)` 를 넘으면 `"?"` 로 표시 — garbage `[7728%]` 대신 `[?%]` 노출.

**R106 보강 — `PLACEHOLDER_LABELS` 의미 매핑** (R75 convention 기반):

| NN | label | 의미 (R75 + R57 convention) |
|----|-------|-----------------------------|
| 4  | 효과% | 효과 강도 (effect_pct) |
| 5  | 공격% | damage % (spirit/class 공통) |
| 7  | MP   | MP cost |
| 8  | 지속초 | duration sec (buff/curse) |
| 9  | 쿨초  | cooldown sec |
| 12 | 배수  | multiplier (e.g. 1.5배) |

garbage 값 (> 500) 일 때 `"?(공격%)"` 형식으로 표시 → 사용자가 "이 자리는 damage 인데 값을 모름" 을 인지 가능. 미매핑 NN 은 `?` 유지.

예 (spirit #0 암흑탄): raw `"정령마력 }#05%|의 피해"` + stats[5]=7728 → R105: `"정령마력 [?%]의 피해"` → **R106: `"정령마력 [?(공격%)%]의 피해"`**.

## 5. R108 Formula + explicit field 통합 (1차)

`game_data.gd` 의 `resolve_skill_desc` 가 `PLACEHOLDER_STAT_SOURCE` 로 NN 별
해석 순서를 고정:

1. `FormulaVM.calc(formula_id_1|2)` — `assets/data/formula/*.json` export 시
2. spirit R87 explicit field (`primary_u16`, `secondary_u16`, `mp_cost`, `cooldown`)
3. `stats_u16[NN]` (값 ≤ 500 일 때만 legacy)
4. `?(label)` — R106

| NN | label (R106) | label (R109) | field / formula |
|----|--------------|--------------|-----------------|
| 4 | 효과% | 효과 | formula_id_2 → secondary_u16 |
| 5 | 공격% | 공격 | formula_id_1 → primary_u16 |
| 6 | 마법% | 마법 | formula_id_1 → primary_u16 |
| 7 | MP | MP | mp_cost |
| 8 | 지속초 | 지속 | formula_id_2 → secondary_u16 |
| 9 | 쿨초 | 쿨 | cooldown |
| 12 | 배수 | 수치 | ~~primary_u16~~ (R109 제거) → stats_u16 fallback |

**검증 예 (spirit #0 암흑탄)**: `primary_u16=400` → `}#05%|` → `}400%|` (이전 `}7728%|` 또는 `[?(공격%)]`).

## 6. R109 단위 분리 + #12 매핑 정정

R106 label 이 unit (`%`, `초`) 을 포함 → desc 본문의 unit 과 중복 노출:

- R106 시점: `}#05%|` unresolved → `}?(공격%)%|` → `[?(공격%)%]` (이중 `%`)
- R106 시점: `}#08초|` unresolved → `}?(지속초)초|` → `[?(지속초)초]` (이중 `초`)

R109 fix: `PLACEHOLDER_LABELS` 에서 unit 제거. 본문의 `}#NN<unit>|` 가 unit 을 보유.

- R109: `}#05%|` unresolved → `}?(공격)%|` → `[?(공격)%]` ✓
- R109: `}#08초|` unresolved → `}?(지속)초|` → `[?(지속)초]` ✓

**#12 매핑 제거**: `12: {"field": "primary_u16"}` 가 spirit #6 폭발 `}#12초|` 에
서 damage% (300) 으로 잘못 노출되던 케이스 차단. NN=12 미매핑 → stats_u16[12]
fallback → 대부분 garbage → `[?(수치)초]` 안전 가드.

| spirit (R109 적용) | 변경 전 (R108) | 변경 후 (R109) |
|-------------------|---------------|----------------|
| #0 암흑탄 `}#05%\|` | `[400%]` | `[400%]` (동일) |
| #1 빛의구 `}#06%\|` | `[0%]` (primary=0) | `[0%]` (동일) |
| #6 폭발 `}#12초\|` | `[300초]` (damage% 오해석) | `[?(수치)초]` (정직) |
| #14 어둠의세례 `}#05%\|` | `[4%]` | `[4%]` (동일) |
| #14 어둠의세례 `}#08초\|` | `[0초]` (sec=0) | `[0초]` (동일 — R109+ duration RE 미완) |

### 6.1 spirit 16 record 실 값 (2026-05-20 추출)

`tools/h5_r109_spirit_placeholder_audit.py` 산출:

| idx | name | primary | secondary | cooldown_byte | fid1 | fid2 | placeholders |
|----:|------|--------:|----------:|--------------:|-----:|-----:|--------------|
|   0 | 암흑탄 | 400 | 0 | 93 | 0 | 0 | `#05%\|` |
|   1 | 빛의구 | 0 | 0 | 93 | 57 | 68 | `#06%\|` |
|   2 | 영혼의회복 | 0 | 0 | 93 | 57 | 68 | `#08초\|` |
|   3 | 파괴광선 | 100 | 0 | 93 | 0 | 0 | `#05%\|` |
|   4 | 지옥소환 | 12 | 0 | 93 | 0 | 0 | `#05%\|` |
|   5 | 유도탄 | 200 | 0 | 93 | 0 | 0 | `#05%\|` |
|   6 | 폭발 | 300 | 0 | 93 | 0 | 0 | `#05%\|`, `#12초\|` |
|   7 | 정신감응 | 0 | 0 | 93 | 57 | 0 | (none) |
|   8 | 동화 | 0 | 0 | 93 | 59 | 0 | (none) |
|   9 | 염도 | 0 | 0 | 93 | 57 | 110 | (none) |
|  10 | 제압 | 0 | 0 | 93 | 57 | 110 | (none) |
|  11 | 얼음폭풍 | 0 | 0 | 93 | 57 | 110 | (none) |
|  12 | 날개 | 0 | 0 | 93 | 57 | 109 | `#08초\|` |
|  13 | 왜곡필드 | 0 | 0 | 93 | 57 | 109 | `#08초\|` |
|  14 | 어둠의세례 | 4 | 0 | 93 | 57 | 110 | `#08초\|`, `#05%\|` |
|  15 | 완전면역 | 0 | 0 | 93 | 57 | 109 | `#08초\|` |

**관측**:
- cooldown byte 0x0d=93 모든 record 동일 → spirit `cooldown` field 무의미
  (실 cooldown 은 formula 또는 다른 offset). R109 에서는 그대로 두고
  `}#09쿨|` 가 desc 에 부재이므로 영향 없음.
- secondary_u16 모든 record 0 → `}#08초|` 는 항상 0 으로 해석 (실 duration RE 미완).
- primary_u16 6/16 record 에서 비-0 (damage% 또는 multiplier 자릿수).

**잔여 (R111+)**:
- `tools/h5_export_formulas.py` 산출 JSON 복원 → formula_id 57/68/109/110 런타임 calc
- duration source RE (extra_hex 0x00..0x32 외 byte 영역)
- class_0..3 warrior skill 의 formula-only placeholder

## 7. R110 Bracket-aware 치환 — class_0..3 skill-link 보존

class_0..3 의 desc 는 두 종류의 `#NN` 패턴 보유:

| 패턴 | 예 | 의미 |
|------|-----|------|
| `}…#NN<unit>\|` 또는 `}#NN<unit>\|` | `}#09초\|`, `}SP #07\|` | 진짜 stat placeholder |
| bare `;#NN<text>` | `;#01돌격-스턴효과`, `;#02돌격-밟고가기` | 관련 스킬/특성 link 참조 |

R108 의 무차별 `result.replace("#%02d", val)` 가 **bare `#NN` 도 치환** → skill-link
참조 corruption:

```
class_0 돌진 desc:
  ...{관련특성|;#01돌격-스턴효과;#02돌격-밟고가기;#03돌격-각력

R108 resolved (corrupt):
  ...{관련특성|;0돌격-스턴효과;0돌격-밟고가기;?돌격-각력
                ↑ stats[1]=0 치환
```

R110 fix: `_replace_placeholders_in_brackets` helper 신규 — `}...|` 강조 괄호
내부의 `#NN` 만 치환.

```gdscript
func _replace_placeholders_in_brackets(desc: String, values: Dictionary) -> String:
    # `}...|` 강조 괄호 내부의 #NN 만 치환. bare #NN 은 보존.
```

R110 후 동일 돌진 desc:
```
재사용대기 [?(쿨)초].;정면의 가장 가까운 적에게;빠르게 돌진한다.;충돌시 대상에게;
근접공격력 [?(공격)%]의;피해를 준다.;{관련특성|;#01돌격-스턴효과;#02돌격-밟고가기;
#03돌격-각력
```

**실 데이터 영향** (`tools/h5_r110_bracket_aware_audit.py`):
- 괄호 내부 placeholder 244 회 (`}#NN<unit>|` + `}<label> #NN<unit>|`) — R110 유지
- bare skill-link 46 회 (`;#NN<text>`) — R110 보존, R108 시점 corruption

class_0..3 의 `}SP #07| 소모` 같은 라벨 placeholder 도 동일 helper 가 처리:
괄호 내부의 모든 `#NN` 을 iteration 으로 치환 (단일 괄호에 여러 `#NN` 등장 가능).

## 8. R111 섹션 헤더 + 불릿 + #10/#11/#13 label

R110 후 class_0..3 desc 의 잔여 UX 문제:
- **`{관련특성|`** 섹션 헤더가 raw 로 노출 (`{관련특성|` 그대로 표시) — 37건
- **bare `#NN<text>`** 스킬-링크가 `#01돌격-스턴효과` raw 로 표시 — 46건
- **#10/#11/#13** 가 PLACEHOLDER_LABELS 미매핑 → 미해결 시 단순 `?` 노출 (class_0..3 에서 #10 은 71회 사용)

R111 fix 3종:

### 8.1 PLACEHOLDER_LABELS 3 entry 추가 (총 10 entry)

| NN | label | 컨텍스트 (desc) |
|----|-------|-----------------|
| 10 | 값 | `}#10\|`, `}#10%\|`, `}#10단계\|` — passive 효과량 |
| 11 | 강화 | `}#11%\|` — buff strength |
| 13 | 양 | `}#13\|`, `}#13초\|` — 회복량/duration |

### 8.2 `resolve_skill_desc` indices 자동 수집

R110 까지는 `PLACEHOLDER_STAT_SOURCE` 키 + `stats.size()` 범위만 indices 에 포함.
R111 = 괄호 내부 `#NN` 도 자동 스캔하여 indices 에 추가 → values dict 에 entry
보장 → 미매핑 NN 의 fallback display 동작.

### 8.3 `resolve_skill_desc_display` 섹션 + 불릿

```gdscript
elif c == "{":
    # `{관련특성|` → `▸ 관련 특성:`. 일반 `{TEXT|` 도 `▸ TEXT:`.
elif c == "#" and ... (NN digits):
    # bare `#NN<text>` → `• <text>` (skill-link 불릿)
```

class_0 돌진 R110 vs R111 비교:

```
R110 출력:                       R111 출력:
재사용대기 [?(쿨)초].             재사용대기 [?(쿨)초].
정면의 가장 가까운 적에게          정면의 가장 가까운 적에게
빠르게 돌진한다.                  빠르게 돌진한다.
충돌시 대상에게                  충돌시 대상에게
근접공격력 [?(공격)%]의            근접공격력 [?(공격)%]의
피해를 준다.                     피해를 준다.
{관련특성|                       ▸ 관련 특성:
#01돌격-스턴효과                  • 돌격-스턴효과
#02돌격-밟고가기                  • 돌격-밟고가기
#03돌격-각력                     • 돌격-각력
```

**`tools/h5_test_placeholder_section_render.py`** (14 검증) — 10 entry LABELS +
indices 자동 수집 + `{TEXT\|` → `▸ TEXT:` + bare `#NN<text>` → `• <text>` +
Python 시뮬 (돌진 전체 변환) + 실 데이터 37 섹션 + 69 skill-link + R105-R110
회귀 + R111 docstring, **14/14 PASS**.

## 9. R112 데이터 quirk 흡수 — 188/188 → 187 클린, 1 outlier

R111 까지의 시스템이 전수 검증 (`tools/h5_r112_skill_desc_audit.py`) 결과 188
class skill 중 **62 건 잔존 raw marker** 발견. 원인 분석 후 4 fix 적용:

### 9.1 디코더 fix — 선행 `}` 보존

`tools/converter/decode_h5_skill.py::split_stats_desc` 가 한글 시작 위치를
desc_start 로 사용. passive 스킬은 desc 가 `}<active_skill>|<text>` form (예:
`}돌진| 스킬과...`) 인데 EUC-KR 한글 첫 byte 가 `돌` (`}` 이 아닌) 이라 `}` 가
stats area 로 흡수되고 desc 가 `돌진| 스킬과...` 로 시작 → 첫 `|` 가 orphan.

R112 backtrack: `if desc_start > 0 and b[desc_start - 1] == 0x7d: desc_start -= 1`.
skills.json 재생성 후 ~58건 자동 해결.

### 9.2 중첩 `}` 평탄화

원본 데이터에 `}<text>}<num>|` 같은 중첩이 존재 (예: 봉쇄/섬광탄
`}시야를 }1|로` — 시야 → 값 1 의미). R112 display 가 inner `}` 를 제거 후
flat bracket 으로 처리:

```gdscript
var inner := raw.substr(i + 1, close - i - 1).replace("}", "")
out += "[" + inner + "]"
```

→ `}시야를 }1|로` → `[시야를 1]로`.

### 9.3 `{` 를 alt close marker 로 수용

쐐기탄 `}민첩 12당 1{의 피해를` — `|` close 가 누락된 데이터 quirk (`|`=0x7c
vs `{`=0x7b 단일 bit 차이, 원본 파일 bit-flip 가설). R112 display 가 `|` 와
`{` 중 가까운 쪽을 close marker 로 수용:

```gdscript
var close_pipe := raw.find("|", i + 1)
var close_brace := raw.find("{", i + 1)
var close := close_pipe if close_brace == -1 else (
    close_brace if close_pipe == -1 else min(close_pipe, close_brace))
```

→ `}민첩 12당 1{의` → `[민첩 12당 1]의`.

### 9.4 불릿 line-start 가드

R111 의 bare `#NN<text>` → `• <text>` 가 포격 `사격당 |#07|의` 의 `#07` 을
잘못 불릿화 (`사격당 |• |의`). R112 가드: 불릿은 `out.is_empty()` 또는
`out.ends_with("\n")` 일 때만 fire — 줄 시작 위치만 skill-link 후보.

### 9.5 최종 audit 결과

| 단계 | 잔존 raw marker | 비율 |
|------|----------------:|-----:|
| R111 시점 | 62 / 188 | 33.0% |
| R112 디코더 fix | 4 / 188 | 2.1% |
| R112 중첩 평탄화 | 3 / 188 | 1.6% |
| R112 `{` alt close | 2 / 188 | 1.1% |
| R112 불릿 가드 | **1 / 188** | **0.5%** |

남은 1건 = **포격 (class_2[9])** 의 `사격당 |#07|의 SP가 감소` — `}` 없는 orphan
`|` 쌍 사이 `#07`. 원본 게임 데이터의 의도적 emphasis 가능성 (`|...|` 강조) —
R112 에서는 data 그대로 유지. 추후 R113+ 에서 별도 marker 로 정식 처리 검토.

**`tools/h5_test_skill_desc_quirks.py`** (14 검증) — 디코더 backtrack + skills.json
sample 검증 + 3 quirk fix (`{` alt close + 중첩 `}` + 불릿 line-start) + 3 실
스킬 사례 (봉쇄/쐐기탄/포격) + 188/188 audit 1 outlier 한도 + R90-R111 회귀
+ R112 docstring, **14/14 PASS**.

업데이트: 2026-05-20 (Round 112).
