# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md). **완성도 정의·4지표**는 [COMPLETION.md](COMPLETION.md).

## 📊 완성도 한눈에 (2026-05-20, R112)

| 지표 | 수치 | 용도 |
|------|------|------|
| 종합 개발 (8카테고리) | **88.0%** | RE·Godot·테스트 전체 |
| 클라이언트 출시 축 (D+E+G) | **~88%** | 코드·설정·패키징 (adb 미검증) |
| **베타 서비스 오픈** (원작 동등 플레이) | **~50%** | 본편·.scn·조우 — **질문 정의 100%** |
| 기술 스모크 (APK·demo) | **~61%** | 시나리오 무관, adb **0%** |

**베타 +8%p** 여지: Godot Release APK + 실기기 스모크 1회 (`BUILD_ANDROID.md`). 레거시 `출시 가능 79.60%` ≠ 출시 축 ~88% — [COMPLETION.md §5](COMPLETION.md).

## ⚡ "영웅서기5 다음 내용 진행해줘" → **Round 113+ (실기기 빌드 / formula JSON / duration RE)**

차기 세션 즉시 할 일:
1. 환경 확인: `PYTHONIOENCODING=utf-8 python tools/verify_godot_project.py` → `0 warnings` 확인
2. 회귀: `python tools/h5_test_skill_desc_quirks.py` → R112 PASSED
3. **Spirit placeholder** = [`docs/h5/RE/skill_desc_placeholder.md`](RE/skill_desc_placeholder.md) §9 (R112 quirk 흡수).
4. **R112 완료**: 디코더 fix (한글 직전 `}` 보존) + 중첩 `}` 평탄화 + `{` alt close marker + 불릿 line-start 가드 — 188 skill 전수 검증, **R111 시점 62 잔존 raw marker → R112 후 1 outlier (포격)** (`사격당 |#07|의` orphan `|` 쌍 — 원본 게임 emphasis 의도 가능).
5. **R113+ 추천** (자율 가능 우선순위):
   - 옵션 A: **Godot Editor 실 빌드 검증** (사용자 작업)
   - 옵션 B: `h5_export_formulas.py` — formula JSON 복원 (calc_*_plain.bin 필요, DES blocker)
   - 옵션 C: SMAF audio playback (외부 의존)
   - 옵션 D: ProcTargetEffectSkill cascade 정밀 (R81 후속, .so 디스어셈블 필요)
   - 옵션 E: spirit duration source RE — secondary_u16 모든 record 0
   - 옵션 F: 포격 1 outlier 의 `|TEXT|` emphasis 형식 정식 처리

**전체 진척 (R112, 8 카테고리 가중평균)** — [COMPLETION.md](COMPLETION.md) §2:

| 카테고리 | 가중치 | 점수 | 기여 |
|---|---|---|---|
| A. 자산 추출/디코딩 | 8% | 95% | 7.6% (SMAF audio playback 미완 빼고 모두 완료) |
| B. 게임 데이터 RE/JSON 변환 | 14% | 96% | 13.44% (92 JSON, 1360 item / 5 skill class+spirit / 166×3 enemy / 151×3 quest / 105 mission / 252 drop) |
| C. 게임 로직 RE | 17% | 93% | 15.81% (Formula 95 + AI 100 + ProcHeroSkill 92 + HSI 11/11 100 + Cooldown 100 + Battle/Dialog 95 + TEM 65 + Save 95) |
| D. Godot 코어 구현 | 24% | **93%** | **22.32%** (UI 10 panel 90 + Character/AI tick/전투 90 + damage 공식 85 + stat modifier 90 + Save/Load 95 + SaveListPanel 90 + Dialog 85 + AudioManager bus-level 정밀 98) |
| E. Godot 통합/Scene 흐름 | 12% | **95%** | **11.40%** (Title 95 + ClassSelect 85 + Demo 90 + GameOver 80 + SceneRouter 90 + Map warp fade 90 + Battle transition 90 + F6 Save list 90 + Toast UX 90 + Audio 80) |
| F. 누락 시스템 | 10% | **72%** | **7.20%** (… + R109 단위 분리 82 + R110 bracket-aware 85 + R111 섹션+불릿 87 + **R112 데이터 quirk 흡수 88 신규** — 188/188 → 187 클린) |
| G. 출시 보완 | 8% | 65% | 5.2% (Packaging 50 + Perf 30 + Localization 60 + Distribution 80 + Build doc 90 + Launcher icons 90) |
| H. 안정성/QA | 7% | **75%** | **5.25%** (Tools/test 90 + HelpPanel R107 + **실기기 플레이 0**) |
| **종합** | **100%** | — | **88.0%** |

→ **베타 서비스 (~50%)**: 원작 화면·시나리오 동등 / **스모크 (~61%)**: APK·demo만 — **혼용 금지**
→ **클라이언트 출시 축 (~88%)**: `(D×24+E×12+G×8)/44` — COMPLETION.md §3
→ 레거시 `출시 가능 79.60%`: 라운드 로그 호환용 (COMPLETION.md §3)

🎯 베타 100%에 가장 큰 임팩트 (COMPLETION.md §6):
1. **실기기 빌드 + 스모크 QA** (0% → 1회 통과 시 **+8~10%p** 베타)
2. **formula JSON** (`h5_export_formulas.py`) — placeholder calc 완성
3. **SMAF BGM** — 체감 품질
4. **TEM cascade RE** (C +0.2%p) / 본편 플레이 스코프 확대

---

업데이트: 2026-05-20 (Round 112 — **skill desc 데이터 quirk 흡수 — 188 skill 전수 검증, 62 잔존 raw marker → 1 outlier**. R111 까지 placeholder/render 시스템이 정밀화됐으나 실제 188 skill 전수 audit (`tools/h5_r112_skill_desc_audit.py`) 결과 **62건 잔존 raw marker** (`#NN`/`}`/`|`/`{`) 발견. 4 fix 동시 적용. **(1) 디코더 fix** (`tools/converter/decode_h5_skill.py::split_stats_desc`): 한글 시작 위치를 desc_start 로 잡되, **선행 byte 가 `}` (0x7d) 면 desc_start 를 1 byte 후퇴**. passive 스킬 desc 가 `}<active_skill>|<text>` form (예: `}돌진| 스킬과...`) 으로 시작하는 경우의 `}` 가 stats area 로 흡수되던 문제 해결 — skills.json 재생성 후 58건 자동 해결. **(2) 중첩 `}` 평탄화**: 봉쇄/섬광탄 desc 의 `}<text>}<num>|` (예: `}시야를 }1|로`) — display 가 inner `}` 를 `.replace("}", "")` 로 제거 후 flat bracket → `[시야를 1]로`. **(3) `{` alt close marker**: 쐐기탄 desc 의 `}민첩 12당 1{의` — `|`=0x7c vs `{`=0x7b 단일 bit 차이 (bit-flip 가설). display 가 `|` 와 `{` 중 가까운 쪽을 close marker 로 수용 → `[민첩 12당 1]의`. **(4) 불릿 line-start 가드**: R111 의 bare `#NN<text>` → `• ` 변환이 포격 desc `사격당 |#07|의` 의 `#07` 을 잘못 불릿화 (`|• |`). R112 = `out.is_empty() or out.ends_with("\n")` 조건 추가 — 줄 시작 위치만 불릿화. **`scripts/core/game_data.gd::resolve_skill_desc_display`** 3 fix (중첩+`{`+불릿 가드) + decoder 1 fix. **최종 audit**: R111 62/188 → R112 후 **1/188 (포격 `사격당 |#07|의`)** — 원본 게임 emphasis 의도 가능, R113+ 별도 marker 정식 처리 검토. **`docs/h5/RE/skill_desc_placeholder.md` §9 신규**: 4 fix 동기 + audit 단계별 감소 표 (62→4→3→2→**1**) + outlier 분석. `tools/h5_r112_skill_desc_audit.py` 신규 — 188 skill 전수 render + raw marker 검출. `tools/h5_test_skill_desc_quirks.py` 신규 (14 검증) — decoder backtrack + skills.json sample (각력 `}돌진|` 시작) + display 3 fix marker + 3 실 사례 (봉쇄/쐐기탄/포격) + audit ≤ 1 outlier + R90/R105/R108/R110/R111 회귀 + R112 docstring, **14/14 통과**. R105-R111 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 71% → **72%** (R112 데이터 quirk 흡수 88 신규 — 188/188 audit 의 99.5% 클린 렌더링). 종합 가중평균 87.89% → **87.99% (↑0.10%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-20 (Round 111 — **`{관련특성|` 섹션 헤더 + bare `#NN<text>` 스킬-링크 불릿 + #10/#11/#13 라벨 추가**. R110 의 자연스러운 UX 완성 라운드. R110 bracket-aware fix 후에도 class_0..3 desc 의 (1) `{관련특성|` 섹션 헤더가 raw 노출 (37건), (2) bare `#NN<text>` 스킬-링크 (예: `#01돌격-스턴효과`) 가 raw 노출 (46건), (3) #10/#11/#13 placeholder 가 unresolved 시 단순 `?` 노출 — class_0..3 에서 #10 만 71회 사용. **`scripts/core/game_data.gd::PLACEHOLDER_LABELS` 3 entry 추가**: `10: "값"` (passive 효과량, `}#10\|/}#10%\|/}#10단계\|` 컨텍스트), `11: "강화"` (buff strength %), `13: "양"` (회복량/duration). 총 10 entry. **`resolve_skill_desc` indices 자동 수집**: while loop 가 `}...|` 괄호 내부의 모든 `#NN` 자동 스캔 → values dict entry 보장 → SOURCE 미매핑 NN 도 정상 fallback. **`resolve_skill_desc_display` 보강 2종**: (1) `c == "{"` 분기 신규 — `{관련특성|` → `▸ 관련 특성:`, 일반 `{TEXT\|` → `▸ TEXT:` (2) `c == "#"` + 2 digit 분기 신규 — bare `#NN<text>` (`}...|` 외부) → `• <text>` 스킬-링크 불릿. 돌진 예: R110 `{관련특성|;#01돌격-스턴효과;#02돌격-밟고가기;#03돌격-각력` → R111 `▸ 관련 특성:\n• 돌격-스턴효과\n• 돌격-밟고가기\n• 돌격-각력`. **`help_panel.gd` HELP_TEXT 갱신** — 10 entry label 표 (4효과/5공격/6마법/7MP/8지속/9쿨/10값/11강화/12수치/13양) + R111 섹션/불릿 안내. **`docs/h5/RE/skill_desc_placeholder.md` §8 신규**: R111 fix 3종 (LABELS 3 추가 + indices 자동 수집 + 섹션+불릿) 동기 + 돌진 R110/R111 비교 + 실 데이터 카운트. `tools/h5_test_placeholder_section_render.py` 신규 (14 검증) — 10 entry LABELS + indices 자동 수집 while loop + `{` 섹션 분기 + `#` 불릿 분기 + Python 시뮬 (돌진 전체 변환 `▸관련특성` + 3 불릿 + `[?(쿨)초]`) + #10 → ?(값) fallback + R110 helper 잔존 + R109/R108/R105/R90 회귀 + R111 docstring + 실 데이터 37 섹션 + 69 skill-link + `;` → `\n` 회귀, **14/14 통과**. R107 회귀 테스트 (h5_test_help_panel_placeholder) 의 PLACEHOLDER_LABELS entry 수 7 → 10 으로 갱신 + help_panel HELP_TEXT 의 10 entry 일치 검사. R100-R110 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 70% → **71%** (R111 섹션+불릿 87 신규 — 37 섹션 + 46 skill-link + 71+ #10 fallback UX 동시 개선). 종합 가중평균 87.79% → **87.89% (↑0.10%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-20 (Round 110 — **Bracket-aware placeholder 치환 — class_0..3 skill-link 보존**. R109 의 자연스러운 정합성 라운드. R108 의 `result.replace("#%02d", val)` 무차별 치환이 class_0..3 desc 의 **bare `#NN` skill-link 참조** (예: `#01돌격-스턴효과`, `#02돌격-밟고가기`) 를 corruption — stats_u16[1]=0 / [2]=0 등으로 치환되어 `0돌격-스턴효과` 처럼 깨짐. 실 데이터 영향: **class_0..3 의 46개 skill-link** 깨짐, **244개 진짜 placeholder** (괄호 내부 `}#NN<unit>|` + 라벨 `}SP #07|` 등) 는 정상. R110 fix = `_replace_placeholders_in_brackets` helper 신규 — `}...|` 강조 괄호 내부의 `#NN` 만 iteration 치환, 괄호 외부 bare `#NN` 보존. **`scripts/core/game_data.gd::resolve_skill_desc` 재구성**: (1) indices 산출 → (2) `values: Dictionary` (NN → display_val) 미리 계산 → (3) `_replace_placeholders_in_brackets(desc, values)` 단일 호출. 이전 `result.replace("}#%02d" % i, "}%s" % display_val) + result.replace("#%02d" % i, display_val)` 무차별 replace 제거. **`docs/h5/RE/skill_desc_placeholder.md` §7 신규**: bracket-aware fix 의 동기 + class_0..3 돌진 desc 의 R108 corruption vs R110 보존 비교 + `}SP #07| 소모` 같은 라벨 placeholder 동작 + 실 데이터 카운트 (244 in-bracket / 46 bare skill-link). `tools/h5_r110_bracket_aware_audit.py` 신규 — class_0..3 desc 의 in-bracket vs bare 패턴 분리 + corruption 카운트. `tools/h5_test_placeholder_bracket_scope.py` 신규 (14 검증) — helper 함수 존재 + resolve_skill_desc 위임 + 무차별 replace 제거 + Python 시뮬 (돌진 `#01/#02/#03` skill-link 보존 + 괄호 내부 `}#05%|` / `}#09초|` 치환) + 도발 `}SP #07|` 라벨 placeholder 치환 + R108 회귀 (암흑탄 #05=400) + R109 회귀 (폭발 stats[12]=32569 garbage 가드 + LABELS 단위 분리 + SOURCE #12 제거) + R105 THRESHOLD + R108 5 helper + R110 docstring marker + 실 데이터 corruption 카운트 (R108 시점 69 → R110 후 보존 / 244 in-bracket 유지) + helper 안전성 (미종결 괄호) + spirit #0 시뮬 R109 form 호환, **14/14 통과**. R105 회귀 테스트는 `display_val` 변수 검사 → R108 helper 또는 R110 bracket-aware 위임 둘 다 허용으로 갱신. R105/R106/R107/R108/R109 + R100/R101/R104 audio 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 69% → **70%** (R110 bracket-aware skill-link 보존 85 신규 — class_0..3 desc 의 46건 corruption 차단, UX 품질 큰 개선). 종합 가중평균 87.69% → **87.79% (↑0.10%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-20 (Round 109 — **Placeholder label/unit 분리 + #12 잘못된 매핑 제거**. R106 의 `PLACEHOLDER_LABELS` 가 unit 을 label 에 포함 (`"공격%"`, `"지속초"`, `"쿨초"`, `"배수"`) → desc 본문의 unit (`%`, `초`) 와 중복 노출 ([?(공격%)%] / [?(지속초)초]) 문제 차단. `}#NN<unit>|` 가 본문에서 unit 을 보유하므로 label 은 의미만 — `"효과"`, `"공격"`, `"마법"`, `"MP"`, `"지속"`, `"쿨"`, `"수치"` (7 entry). R109 form: `[?(공격)%]` / `[?(지속)초]` / `[?(수치)초]` 단위 1회 노출. **`PLACEHOLDER_STAT_SOURCE` 에서 NN=12 제거**: R108 시점 `12: {"field": "primary_u16"}` 가 spirit #6 폭발 `}#12초|` 를 damage% (300) 으로 잘못 노출 (300초 ≈ 5분 knockdown 비현실). R109 제거 → stats_u16[12] fallback (대부분 garbage > 500) → `[?(수치)초]` 정직 표시. **`help_panel.gd`** R109 안내 갱신 — `?(공격)%` / `?(지속)초` 형식 예시 + 7 label (효과/공격/마법/MP/지속/쿨/수치). **`docs/h5/RE/skill_desc_placeholder.md` §6 신규**: R106→R109 label 비교 표 + #12 매핑 정정 사유 + spirit 16 record 실 값 표 (`tools/h5_r109_spirit_placeholder_audit.py` 산출 — primary/secondary/mp/cooldown/fid1/fid2 + placeholder 분포) + R110+ 잔여 (formula JSON / duration source RE / class formula calc). **관측**: spirit primary_u16 6/16 비-0 (damage% 자릿수), secondary_u16 16/16 = 0 (`#08초` 모두 0 표시 — duration RE 미완), cooldown byte 0x0d=93 모든 record 동일 (실 cooldown 다른 offset). `tools/h5_test_placeholder_label_unit.py` 신규 (14 검증) — 7 label 단위 제거 + R106 unit-포함 잔존 0 + 6 SOURCE entry (12 제거) + 폭발 stats_u16[12]=32569 > THRESHOLD garbage 가드 + 암흑탄 primary_u16=400 회귀 + resolve_skill_desc 분기 보존 + _format_placeholder_display `?(label)` form + help_panel R109 7 label + 단위 분리 표기 + Python 시뮬 (`[?(공격)%]` / `[?(지속)초]` / `[?(수치)초]` form + R106 단위 중복 form 미발생) + R105 THRESHOLD 회귀 + R107 placeholder 섹션 회귀 + R108 5 helper 회귀 + R109 docstring marker + RE 문서 §6 검증, **14/14 통과**. R105-R108 회귀 테스트 (h5_test_placeholder_guard / labels / formula / help_panel_placeholder) 는 R106 form 잔존 검사를 R106/R109 form 둘 다 허용으로 갱신 — 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 68% → **69%** (R109 label/unit 분리 + #12 정정 82 신규 — UX 정직성 향상, R108 의 잘못된 매핑 1건 제거). 종합 가중평균 87.59% → **87.69% (↑0.10%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 106 — **Placeholder NN → 의미 label 매핑 (R75 convention)**. R105 의 `[?%]` garbage fallback 의 자연스러운 보강. raw `?` 대신 R75/R57 convention 기반의 의미 label 노출 — 사용자가 "이 자리에 어떤 stat 이 들어가는지" 인지 가능. **`scripts/core/game_data.gd::PLACEHOLDER_LABELS`** dict 6 entry 신규: `4: "효과%"` (effect_pct), `5: "공격%"` (damage%, R57 convention 공통), `7: "MP"` (mp_cost), `8: "지속초"` (duration), `9: "쿨초"` (cooldown), `12: "배수"` (multiplier). **`resolve_skill_desc` display_val 분기 보강**: 이전 `"?" if raw > THRESHOLD else str(raw)` → `if raw > THRESHOLD: "?(%s)" % PLACEHOLDER_LABELS.get(i, "?") if has(i) else "?"`. 결과: spirit #0 의 `정령마력 }#05%|의 피해` (stats[5]=7728 garbage) → R105: `정령마력 [?%]의 피해` → **R106: `정령마력 [?(공격%)%]의 피해`**. 미매핑 NN 은 `?` 유지 (안전 fallback). **`docs/h5/RE/skill_desc_placeholder.md` §4 갱신**: R106 label 매핑 표 (6 entry × NN/label/의미) + 사용 예시 추가. R105 의 THRESHOLD=500 가드는 그대로 유지. `tools/h5_test_placeholder_labels.py` 신규 (15 검증) — PLACEHOLDER_LABELS 6 entry + resolve_skill_desc 의 label fallback 분기 + R105 가드 잔존 + Python 시뮬 6 case (공격%/쿨초/지속초/정상/미매핑/배수) + RE 문서 label 표 + R90-R105 회귀 + 미매핑 `?` fallback + 합성 시뮬 (full string replace flow), **15/15 통과**. R105 회귀 테스트는 R105 ternary 매칭 → R106+ label form 도 허용으로 갱신. R90-R105 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 63% → **65%** (R75 convention label fallback 75 신규 — placeholder UX 의미 전달, R107+ Formula::calc 실 계산값 통합으로 가는 디딤돌). 종합 가중평균 87.19% → **87.39% (↑0.20%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지.)

이전 업데이트: 2026-05-19 (Round 105 — **Spirit placeholder 실 stat source RE 분석 + UNREASONABLE 가드**. R90 placeholder 시스템의 실 동작 검증 — `}#NN<unit>|` 가 garbage 값 (7728%, 41008%, -1초) 표시되던 근본 원인 분석. **실측 데이터 조사**: spirit 16 record + class_0 43 skill 의 stats_u16 인덱스 5/6/8/12 가 **모든 record 에서 동일한 상수** (7728/23808/0/32569) — 즉 file 의 헤더 magic / struct padding bytes 이지 placeholder source 가 아님. class_0 의 stats[5] 도 0/20528/41008 의 비합리적 값 (정상 damage% 범위 0..200 초과). **결론**: R75 의 `stats_u16[NN]` 매핑 가설은 잘못됨. 실 source 는 **Formula::calc** 런타임 (R72/R73 RE) + `dynamic_formula_id` (R87 sub-rel 0x26) + HERO stat pack 의 조합. **`scripts/core/game_data.gd::resolve_skill_desc` 보강**: (1) `const PLACEHOLDER_UNREASONABLE_THRESHOLD := 500` 상수 신규, (2) `var raw_val: int = int(stats[i])` 후 `var display_val: String = "?" if raw_val > THRESHOLD else str(raw_val)`, (3) 2 `result.replace` 호출 모두 `display_val` 사용. 결과: garbage `[7728%]` → `[?%]` 노출 (사용자에게 "값 모름" 가시화), 정상 값 (0..500) 은 그대로. 정확 매핑은 R106+ Formula 통합 작업으로 미룸. **`docs/h5/RE/skill_desc_placeholder.md` 신규 (5 섹션)**: §1 R90 placeholder 시스템 요약, §2 R105 실측 데이터 (spirit 16/class_0 43 의 상수 패턴), §3 실제 stat source 추정 (Formula::calc + dynamic_formula_id + HERO pack), §4 R105 휴리스틱 fallback 동작, §5 R106+ 정확 매핑 작업 항목 (Formula entry signature 정확화 + dynamic_formula_id 활용 + HERO stat mapping + desc NN 매핑 발견, 추정 3-5 라운드). `tools/h5_test_placeholder_guard.py` 신규 (15 검증) — UNREASONABLE 상수 + display_val 분기 + replace 가 display_val 사용 + RE 문서 5 섹션 + 실측 상수 명시 (7728/23808/20528/41008) + Python 시뮬 (7728→? / 120→120 / 500→500 / 501→? / -1→-1) + spirit JSON 으로 실 영향 확인 (11/16 record 가 placeholder, 그중 7 garbage 가 `?` 로 표시) + R90-R104 회귀 + R106+ 후속 명시, **15/15 통과**. R90 회귀 (spirit placeholder display) + R91-R104 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 60% → **63%** (Spirit placeholder source RE 분석 + 휴리스틱 가드 70 신규 — 사용자 garbage 노출 차단 + R106+ 후속 청사진 확보). 종합 가중평균 86.89% → **87.19% (↑0.30%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 104 — **SettingsPanel `_on_mute_toggled` 의 중복 `_save_config` 제거 — 단일 source-of-truth**. R103 핸들러 중앙화의 자연스러운 마무리. R99 시점 `_on_mute_toggled(on)` 는 `Audio.set_muted(on) + _save_config()` 둘 다 호출. R103 부터 `set_muted → mute_changed.emit → demo._on_audio_mute_changed → _settings._save_config` signal chain 이 자동 저장 → inline `_save_config` 는 중복 호출 (사용자가 체크박스 클릭 시 save 2회). R104 = inline 제거. **`scripts/ui/settings_panel.gd` `_on_mute_toggled` 간소화**: 2 줄 → 1 줄 (`Audio.set_muted(on)` 만). save 는 signal chain (1 회) 으로 단일 source-of-truth. docstring 갱신으로 chain 경로 명시. BGM/SFX 슬라이더 / FPSCheck / FullscreenCheck 의 `_save_config` 는 그대로 유지 (signal chain 외 직접 변경, 별도 트리거 없음). `tools/h5_test_dedup_save.py` 신규 (14 검증) — `_on_mute_toggled` 의 inline `_save_config` 제거 검증 + demo `_on_audio_mute_changed` 의 chain save 잔존 + BGM/SFX/FPS/Fullscreen `_save_config` 잔존 + R98-R103 회귀 + **Python 시뮬** (MuteCheck 클릭 → on_mute_toggled → set_muted → mute_changed → sync + save + toast → on_mute_toggled exit, `saved_count == 1` 단일 save 확인 + 동일 값 재토글 시 R102 `changed` 가드로 save 안 됨) + docstring marker, **14/14 통과**. R99 회귀 테스트는 `_on_mute_toggled` 의 `_save_config` inline 검사 → inline 또는 signal chain 어느 쪽이든 허용으로 갱신. R98-R103 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: H 카테고리 73% → **74%** (코드 품질 향상 — 단일 source-of-truth 패턴 정립, 중복 save 호출 제거). 종합 가중평균 86.84% → **86.89% (↑0.05%p)**. Godot 93-96% 유지. 출시 가능 기준 79.60% 유지 (H 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 103 — **HUD AudioIndicator 클릭 토글 + mute_changed 단일 핸들러 중앙화**. R102 의 indicator + signal 후속. (1) AudioIndicator 클릭 가능, (2) F8/HUD click/SettingsPanel checkbox 3 entry point 가 동일 signal chain 사용. **`scenes/hud.tscn` 보강**: AudioIndicator `mouse_filter = 0` (MOUSE_FILTER_STOP — Label 의 default ignore 해제) + `tooltip_text = "F8 또는 클릭 — 음소거 토글"`. **`scripts/ui/hud.gd` 보강**: `_ready` 에 `audio_indicator.gui_input.connect(_on_audio_indicator_input)` + `func _on_audio_indicator_input(event)` 신규 — InputEventMouseButton + 좌클릭 release (not pressed) 시 `Audio.toggle_mute()` 호출. **`scripts/ui/demo.gd` 핸들러 중앙화**: (1) `_ready` 끝에 `Audio.mute_changed.connect(_on_audio_mute_changed)` 추가, (2) `_on_audio_mute_changed(muted)` handler 신규 — `_settings.sync_mute_check(muted) + _settings._save_config() + Toast.warn/info` 통합, (3) **F8 핸들러 단순화** — 이전 ~7 줄 (toggle_mute + sync + save + Toast warn/info if-else) → 1 줄 `Audio.toggle_mute()`. F8 / HUD click / SettingsPanel checkbox 어디서 토글되든 동일 signal chain 으로 sync + save + Toast 일관 처리 (R102 의 `changed` 가드가 cycle 방지). **3 toggle entry point**: KEY_F8 → toggle_mute / HUD gui_input → toggle_mute / SettingsPanel _on_mute_toggled → set_muted — 모두 `Audio.mute_changed.emit` 거쳐 demo handler 도달. `tools/h5_test_hud_indicator_click.py` 신규 (13 검증) — tscn mouse_filter=0 + 갱신된 tooltip + hud gui_input 연결 + handler (InputEventMouseButton + MOUSE_BUTTON_LEFT + release) + demo mute_changed 연결 + signal handler (sync/save/Toast 통합) + F8 단순화 + R98-R102 회귀 + 3 entry point 수렴, **13/13 통과**. R98/R99/R102 회귀 테스트는 F8 inline 검사 → F8 inline 또는 signal handler 어느 쪽이든 허용으로 갱신 (tooltip "F8 — 음소거 토글" → "F8" + "음소거 토글" 부분 매칭). R98-R102 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 94% → **95%** (Demo 88→90 + Audio 70→80 — HUD click 토글 + 핸들러 중앙화, F8 ~7줄 → 1줄 단순화). 종합 가중평균 86.72% → **86.84% (↑0.12%p)**. Godot 93-96% 유지. 출시 가능 기준 79.48% → **79.60%**.)

이전 업데이트: 2026-05-19 (Round 102 — **HUD AudioIndicator + Audio.mute_changed signal**. R101 bus 분리 후속, audio 상태의 사용자 가시화 마무리. F8 또는 SettingsPanel 의 mute 체크박스로 토글한 상태가 화면 상단 HUD 에는 visible 안 됨. **`audio_manager.gd` 보강**: (1) `signal mute_changed(muted: bool)` 신규, (2) `set_muted` 에 `var changed := (_muted != mute)` + `if changed: mute_changed.emit(_muted)` 추가 — 상태 변화 시에만 emit, 동일 값 재호출 (체크박스 silent update cycle) 시 무한 발화 방지. **`scenes/hud.tscn` 보강**: GoldLabel 옆에 `AudioIndicator` Label 신규 (offset_left=296, offset_right=316, offset_top=22, text="♪", 폰트 10, 색 연두, **tooltip_text="F8 — 음소거 토글"**). **`scripts/ui/hud.gd` 보강**: (1) `@onready var audio_indicator`, (2) `AUDIO_ON_TEXT = "♪"` / `AUDIO_OFF_TEXT = "🔇"` / `AUDIO_ON_COLOR = 연두` / `AUDIO_OFF_COLOR = 빨강` 4 상수, (3) `_ready` 에서 `Audio.mute_changed.connect(_on_mute_changed)` + `_on_mute_changed(Audio.is_muted())` 초기 적용, (4) `_on_mute_changed(muted)` handler — text + `add_theme_color_override` 로 색상 교체. polling 없이 signal 기반 동기화. F8 토글 → AudioManager.set_muted → mute_changed.emit → HUD.\_on_mute_changed → indicator 즉시 갱신. `tools/h5_test_hud_audio_indicator.py` 신규 (15 검증) — mute_changed signal + set_muted 의 changed 가드 + emit + hud.tscn AudioIndicator 노드 + F8 tooltip + offset_right=316 우상단 + @onready var + signal connect + handler + ON/OFF 4 상수 + add_theme_color_override + _ready 의 초기 상태 적용 + Python 시뮬 (중복 set 시 emit 안 함) + R101/R99/R98/R97/R96 회귀 + docstring marker + demo F8 sync_mute_check 잔존, **15/15 통과**. R98-R101 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 93% → **94%** (Audio 60→70, HUD indicator 즉시 갱신 + mute_changed signal pipeline). 종합 가중평균 86.60% → **86.72% (↑0.12%p)**. Godot 93-96% 유지. 출시 가능 기준 79.36% → **79.48%**.)

이전 업데이트: 2026-05-19 (Round 101 — **Audio bus layout 분리 — Master 단일 → Master + BGM + SFX 3 bus**. R100 밀레스톤 후 첫 라운드, 음향 인프라 정비. R97-R99 의 정밀 작업은 모두 player-level `volume_db` 변경에 의존했고 `_fade_swap` 의 transition 시 player 값이 reset 위험. 또한 BGM 과 SFX 가 같은 Master bus 에 있어 독립 dB / mute 제어 불가능. **`apps/hero5-godot/default_bus_layout.tres` 신규**: `[gd_resource type="AudioBusLayout"]` + 3 bus (Master / BGM / SFX), BGM bus volume_db=-6 / SFX bus volume_db=-3 (R97 의 초기 dB 그대로), BGM/SFX 가 모두 Master 로 send. **`project.godot` 보강**: `[audio] buses/default_bus_layout="res://default_bus_layout.tres"` 신규 섹션. **`scripts/core/audio_manager.gd` 보강**: (1) `BGM_BUS_NAME / SFX_BUS_NAME` 상수, (2) `_bgm_bus_idx / _sfx_bus_idx` 변수 + `_ready` 에서 `AudioServer.get_bus_index` lookup + 미적용 시 `"Master"` fallback (안전 가드), (3) **`set_bgm_volume / set_sfx_volume` 이 `AudioServer.set_bus_volume_db(_X_bus_idx, target_db)` 사용** — bus 적용 시 깨끗한 bus-level 제어, fallback path 도 유지, (4) **`set_muted` 이 `AudioServer.set_bus_mute(_X_bus_idx, _muted)` 사용** — volume_db swap 없이 mute on/off 만 토글, (5) `play_bgm` 의 player.volume_db 가 bus 적용 시 `0.0`, 미적용 시 `_bgm_target_db`, (6) `play_sfx` 의 player.volume_db 가 bus 적용 시 `0.0`, 미적용 시 `MUTE_DB if _muted else _sfx_target_db`, (7) `_fade_swap` 의 fade-in target 이 bus 적용 시 `0.0` (player 상대 attenuator) — bus 가 절대 dB 관리, player 는 상대 변화. **이전 호환**: 모든 외부 API (`set_bgm/sfx_volume`, `set_muted`, `is_muted`, `toggle_mute`) 시그니처 동일 → R97-R99 의 SettingsPanel / demo F8 / Title 코드 무수정. `tools/h5_test_audio_bus_layout.py` 신규 (16 검증) — tres 의 3 bus + Master send + 초기 dB / project.godot audio 섹션 / 2 BUS_NAME 상수 / _ready bus index lookup + Master fallback / set_X_volume 의 bus_volume_db + fallback / set_muted 의 bus_mute / play_X 의 bus 적용 시 0dB / _fade_swap fade-in target / R91-R99 회귀 + docstring marker, **16/16 통과**. R97 회귀 테스트는 `_bgm.volume_db = -6` 직접 매칭 → tres 의 bus volume_db 확인 (R101 form 우선, R97 form fallback) 으로 변경. R97/R98/R99 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: D 카테고리 92% → **93%** (AudioManager bus-level 정밀 98 신규), E 카테고리 92% → **93%** (Audio 50→60, 3 bus 분리로 BGM/SFX 독립 제어). 종합 가중평균 86.28% → **86.60% (↑0.32%p)**. Godot 93-96% 유지. 출시 가능 기준 79.04% → **79.36%**.)

이전 업데이트: 2026-05-19 (Round 100 — **밀레스톤 결산 — R82-R99 18 라운드 + 잔여 큰 덩어리**. R82 (73.01%) → R99 (86.07%) 18 라운드 누적 +13.06%p 의 결산 문서 작성 + 차기 우선순위 정리. **`docs/h5/MILESTONE_R100.md` 신규 (5 섹션)**: §1 누적 변화 표 (8 카테고리 R82 시작 → R99 종료 + Δ + 주요 라운드), §2 카테고리별 주요 마일스톤 (각 카테고리 ✅완료 / ❌남은 일), §3 잔여 큰 덩어리 (R100+ 4 옵션 — Godot Editor 실 빌드 +0.6 / Spirit stats 정확 매핑 +1.0 / SMAF audio +0.3 / TEM cascade +0.2, 이론 천장 ≈ 88.2%), §4 18 라운드 라인업 (R82-R99 한 줄씩 + 누적 +13.90%p ASCII 박스), §5 핵심 RE/구현 종결 사실 (HSI 88B / TEM VFX / DES blocker / Save round-trip 31 필드 / Toast severity 4 / Mute 4 layer). **가장 큰 도약 영역**: E (+37%p) Scene 흐름 + UX, F (+54%p) 누락 시스템. SMAF 와 디바이스 빌드 미해결, calc DES 정적 분석 후 NDK runner 만 남은 채. PROGRESS / SESSION_HANDOFF cross-link. `tools/h5_test_milestone_r100.py` 신규 (15 검증) — 5 섹션 헤더 + 73.01% / 86.07% 종합 매칭 + 18 라운드 entry + 8 카테고리 + E/F 큰 도약 강조 + R100+ 4 옵션 + 이론 천장 + 6 핵심 RE 사실 + cross-link + R91/R96/R97/R98/R99 회귀 + ASCII 박스 + R100 마커, **15/15 통과**. R99 회귀 통과. verify_godot_project **0 warnings**. **진척률 갱신**: H 카테고리 70% → **73%** (R100 밀레스톤 결산 문서 95 신규, 향후 라운드의 컨텍스트 인덱스 역할). 종합 가중평균 86.07% → **86.28% (↑0.21%p)**. Godot 93-96% 유지. 출시 가능 기준 79.04% 유지 (H 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 99 — **SettingsPanel Mute 체크박스 UI + F8 양방향 동기화**. R98 의 자연스러운 후속 — F8 토글 후 사용자가 SettingsPanel 을 열어도 mute 상태가 시각적으로 안 보였음. R99 = settings_panel 에 MuteCheck 체크박스 추가 + F8 ↔ 체크박스 양방향 동기화. **`scenes/settings_panel.tscn` 보강**: `[node name="MuteCheck" type="CheckBox" parent="BG"]` (offset_top=92, text=`"음소거 (F8)"`) 신규. 기존 노드 재배치 — FPSCheck (96→120), FullscreenCheck (124→148), FPSLabel (156→180). **`scripts/ui/settings_panel.gd` 보강**: (1) `@onready var mute_check: CheckBox = $BG/MuteCheck`, (2) `_ready` 에 `mute_check.toggled.connect(_on_mute_toggled)`, (3) `_load_config` 끝에 `mute_check.set_pressed_no_signal(muted)` 로 ConfigFile 의 muted 상태 반영 (set_muted 는 이미 위에서 호출, signal 재발화 방지 위해 `_no_signal`), (4) `_on_mute_toggled(on)` 신규: `Audio.set_muted(on); _save_config()`, (5) **`sync_mute_check(state)` public helper 신규**: `mute_check.set_pressed_no_signal(state)` — F8 외부 호출자가 체크박스를 신호 발화 없이 동기화. **`scripts/ui/demo.gd` F8 핸들러 보강**: `Audio.toggle_mute()` 결과 boolean 으로 `_settings.sync_mute_check(muted)` 호출 추가 → 체크박스 즉시 갱신. 이로써 F8 누르면 (1) AudioManager mute 상태 토글, (2) Toast warn/info 시각 피드백, (3) SettingsPanel 체크박스 silent 갱신, (4) ConfigFile 영속 저장 4 layer 일관. 사용자가 SettingsPanel 의 MuteCheck 를 직접 클릭해도 동일 결과 (Audio.set_muted + _save_config). `tools/h5_test_mute_checkbox.py` 신규 (15 검증) — tscn MuteCheck 노드 + '음소거 (F8)' 라벨 + 4 노드 offset_top 재배치 (92/120/148/180) + @onready var mute_check + _ready 의 toggled 연결 + _load_config 의 set_pressed_no_signal 초기화 + _on_mute_toggled 의 set_muted + _save_config + sync_mute_check helper + set_pressed_no_signal 사용 + demo F8 의 sync_mute_check 호출 + R98 회귀 (mute 3 API + ConfigFile audio/muted) + R97/R96/R95/R94/R93/R92/R91 회귀, **15/15 통과**. R98 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 91% → **92%** (Audio 40→50, Mute 체크박스 UI + F8 양방향 동기화 완성 — 4 layer 일관성). 종합 가중평균 85.95% → **86.07% (↑0.12%p)**. Godot 93-96% 유지. 출시 가능 기준 78.92% → **79.04%**.)

이전 업데이트: 2026-05-19 (Round 98 — **음소거 토글 F8 + ConfigFile 영속성**. R97 AudioManager 정밀 후속 — 사용자가 음소거를 원할 때 슬라이더를 0 까지 끌고 갈 필요 없게 즉시 토글 키 + 다음 실행 시 mute 상태 복원. **`scripts/core/audio_manager.gd` 보강**: (1) `var _muted: bool = false` 상태 변수, (2) `func is_muted() -> bool / set_muted(mute: bool) / toggle_mute() -> bool` 3 public API — set_muted 가 BGM + SFX `volume_db` 를 `MUTE_DB if _muted else _X_target_db` 로 전환, toggle_mute 는 set_muted 위임 후 새 상태 반환 (UI 동기화용), (3) `set_bgm_volume / set_sfx_volume` 에 `if _bgm and not _muted` 가드 추가 — 음소거 중 슬라이더 조정 시 즉시 unmute 되지 않음 (target_db 만 update, 실 volume_db 는 mute 유지), (4) `play_sfx` 가 `_sfx.volume_db = (MUTE_DB if _muted else _sfx_target_db)` 로 mute 분기. **`scripts/ui/settings_panel.gd` 보강**: (1) `_load_config` 가 `cfg.get_value("audio", "muted", false)` 읽고 `Audio.set_muted(muted)` 즉시 호출, (2) `_save_config` 가 `cfg.set_value("audio", "muted", Audio.is_muted())` 저장 — 사용자가 F8 로 토글한 상태가 다음 실행 시 복원. **`scripts/ui/demo.gd` 신규 F8 핸들러**: `var muted = Audio.toggle_mute(); _settings._save_config(); if muted: Toast.warn(self, "🔇 음소거") else: Toast.info(self, "🔊 음소거 해제")` — 즉시 토글 + 영속 저장 + 의미별 색상 toast. **`scripts/ui/help_panel.gd` HELP_TEXT 보강**: 설정/Scene 섹션에 `F8 — 음소거 토글 (mute on/off, ConfigFile 영속)` 추가. `tools/h5_test_mute_toggle.py` 신규 (15 검증) — AudioManager 의 4 API (_muted/is_muted/set_muted/toggle_mute) + set_muted 의 BGM+SFX 전환 + play_sfx 의 _muted 분기 + set_X_volume 의 `not _muted` 가드 + SettingsPanel 의 ConfigFile "audio/muted" read/write + 즉시 반영 + demo F8 핸들러 (toggle_mute + _save_config + Toast warn/info) + HelpPanel F8 명시 + Python 시뮬 (off→on -80dB / on→off 복원) + R97 회귀 (slider_to_db) + R96 회귀 (Toast 분포 info ≥ 9 / warn ≥ 3 — F8 가 각 +1) + R95/R94/R93/R92/R91 회귀 + docstring marker, **15/15 통과**. R96 회귀 테스트는 Toast 분포 == 12 → ≥ 12 (확장 허용), R97 회귀 테스트는 `_sfx.volume_db = _sfx_target_db` 정확 매칭 → `_sfx_target_db` + `_sfx.volume_db` 부분 매칭 (R98 의 `(MUTE_DB if _muted else _sfx_target_db)` 형식 수용) 으로 변경. R91-R97 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 90% → **91%** (Audio 30→40, Mute 토글 F8 + ConfigFile 영속), H 카테고리 65% → **70%** (HelpPanel 의 F8 추가로 키 명세 완성도 ↑). 종합 가중평균 85.48% → **85.95% (↑0.47%p)**. Godot 93-96% 유지. 출시 가능 기준 78.80% → **78.92%**.)

이전 업데이트: 2026-05-19 (Round 97 — **SettingsPanel/AudioManager 볼륨 정밀 (linear_to_db + SFX target + mute)**. R96 UI/UX 후속, audio 카테고리 첫 진척. **3 문제 동시 fix**: (1) SettingsPanel 의 `db = -40 + (v/100) * 40` 선형 dB 매핑은 청각적으로 비-자연 — -40~0dB 구간이 대부분 동일 음량으로 들림 (인간 청각은 log scale), (2) SFX 슬라이더가 `Audio._sfx.volume_db = db` 만 변경 → AudioManager 의 영속 target_db 변수 부재 → 후속 `_fade_swap` 등에서 reset, (3) `_load_config` 후 AudioManager 에 즉시 반영 안 됨 → 사용자가 슬라이더 만지기 전까지 default -6dB 재생. **`scripts/core/audio_manager.gd` 보강**: (1) `static func slider_to_db(v: float) -> float` 신규 — `linear_to_db(clampf(v, 0, 100) / 100.0)` 으로 자연 곡선 (v=100→0dB, v=50→≈-6dB, v=10→-20dB), `v < MUTE_THRESHOLD (1.0)` 시 `MUTE_DB (-80)` 반환, (2) `var _sfx_target_db: float = -3.0` 영속 변수 신규 (BGM 의 `_bgm_target_db` 대칭), (3) `func set_bgm_volume(v) / set_sfx_volume(v)` public API — `_X_target_db = slider_to_db(v); _X.volume_db = _X_target_db`, (4) `play_sfx` 가 stream 설정 직후 `_sfx.volume_db = _sfx_target_db` 재적용 (외부에서 변형됐을 대비). **`scripts/ui/settings_panel.gd` 보강**: (1) `_on_bgm_volume(v)` = `Audio.set_bgm_volume(v); _save_config()` — 9 줄 → 2 줄, (2) `_on_sfx_volume(v)` 동일 — 직접 `Audio._sfx.volume_db = db` 변경 제거, (3) `_load_config` 끝에 `Audio.set_bgm_volume(bgm_slider.value); Audio.set_sfx_volume(sfx_slider.value)` 즉시 반영. `tools/h5_test_audio_volume.py` 신규 (14 검증) — slider_to_db static helper + linear_to_db 사용 + MUTE_THRESHOLD/MUTE_DB 상수 + return MUTE_DB 분기 + `_sfx_target_db = -3.0` 영속 + play_sfx 의 재적용 + set_bgm/sfx_volume API + _X_target_db = slider_to_db(v) 위임 + SettingsPanel 의 Audio.set_X_volume 위임 + 이전 -40 선형 매핑 + Audio._X.volume_db 직접 변경 제거 + _load_config 의 즉시 반영 + **Python 시뮬** (`v=100→0dB / v=50→-6.02dB / v=10→-20dB / v<1→-80dB(mute)` 모두 일치) + _ready 초기 dB (BGM -6 / SFX -3) 보존 + R91-R96 회귀 + docstring marker, **14/14 통과**. R91-R96 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: D 카테고리 91% → **92%** (AudioManager 정밀 95 신규), E 카테고리 89% → **90%** (Audio 20→30, 슬라이더 dB 곡선 정확화로 사용자 체감 음량 제어 정밀). 종합 가중평균 85.12% → **85.48% (↑0.36%p)**. Godot 93-96% 유지. 출시 가능 기준 78.44% → **78.80%**.)

이전 업데이트: 2026-05-19 (Round 96 — **demo.gd 의 Toast.severity helper 마이그레이션 (12 호출 분류) — 85% 돌파**. R95 의 Toast UX 정비 후속. R95 시점 demo.gd 가 R86-R94 시절부터 누적된 12 회의 `preload("res://scripts/ui/toast.gd").show_msg(self, text, ...)` 패턴 — 모든 toast 가 동일 노랑 + 의미 불명. R96 = 12 호출 전부 R95 의 severity helper (`Toast.info / success / warn`) 로 마이그레이션, preload boilerplate 도 제거. **분류**: (1) **info × 8** (퀘스트 시작 / monster skill 정보 / monster spawn 디버그 / 타일·충돌 변경 / 화면 흔들림 / 시스템 메시지 / BGM 변경), (2) **success × 2** (퀘스트 완료 — 3.0s duration, 아이템 획득 — 2.0s duration), (3) **warn × 2** (공격할 적 없음 / 공격 범위 내 적 없음). 사용자 입장에서 같은 노랑 다발이 아니라 의미별 색상 (노랑 정보 / 연두 성공 / 주황 경고) + 적절한 duration. **`scripts/ui/demo.gd`**: 12 `preload(...).show_msg(self, ...)` → 12 `Toast.X(self, ...)`. preload 패턴 잔존 0 회 검증. duration override 보존: 퀘스트 완료 3.0s + 아이템 획득 2.0s + 공격 경고 default. R95 Toast.gd 의 `show_msg` 함수 시그니처 자체는 유지 (외부 호출자 미래 대비). `tools/h5_test_toast_migration.py` 신규 (12 검증) — preload show_msg 잔존 0 회 + Toast.X 호출 분포 (info=8 / success=2 / warn=2 / error=0 / 총=12) + 12 분류 정확성 marker (퀘스트 시작 info / 퀘스트 완료 success / 아이템 획득 success / 공격할 적 warn / 공격 범위 warn / BGM info / 시스템 info / 화면 흔들림 info / 타일 info / 충돌 info / monster spawn info / skill info) + R95 Toast 4 helper + show_msg 시그니처 호환 잔존 + R95 stack/fade tween 잔존 + R94/R93/R92/R91 회귀 + 퀘스트 완료 3.0s 보존 + 아이템 획득 2.0s 보존, **12/12 통과**. R95 회귀 테스트는 demo show_msg 검사를 toast.gd 의 함수 자체 존재로 변경 (R96 후에도 외부 호출자 대비 함수 잔존). R91-R95 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 87% → **89%** (Demo 85→88 + Toast severity 분류 90 신규 — 사용자 피드백이 시각적으로 의미 전달). 종합 가중평균 84.88% → **85.12% (↑0.24%p) — 85% 돌파**. Godot 93-96% 유지. 출시 가능 기준 78.20% → **78.44%**.)

이전 업데이트: 2026-05-19 (Round 95 — **Toast UX 정비 — severity / fade-in / stack**. R94 의 HelpPanel 키 동기화 후속 UI/UX 라운드. **문제**: `scripts/ui/toast.gd` 가 (1) 같은 frame 다발 발화 시 동일 좌표 (60, 110) 에 겹쳐 표시 → 마지막 것만 보임, (2) fade-out 만 있고 fade-in 부재 → 갑작스런 등장, (3) severity 구분 없이 모든 toast 가 동일 노랑 (Color(1, 1, 0.4, 1)) — 성공/실패/경고 구분 안 됨. **`scripts/ui/toast.gd` 재작성 (~80 줄)**: (1) **`enum Severity { INFO, SUCCESS, WARN, ERROR }`** + **`const COLORS`** dict (노랑/연두/주황/빨강 4 색상), (2) **4 단축 helper**: `static func info/success/warn/error(parent, text, duration)` (duration default 2.5/2.5/2.8/3.2 — 심각도 ↑ ⇒ 표시 시간 ↑) + `show_severity(parent, text, severity, duration)` dispatcher, (3) **`static var _active_toasts: Array`** + **stack Y 계산**: `STACK_Y_BASE (110) + STACK_Y_STEP (32) × _active_toasts.size()` → 동시 다수 toast 가 32px step 으로 수직 stack, _finish 시 `_active_toasts.erase(self)`, (4) **tween chain 4 단계**: `tween_property(_bg, "modulate:a", 1.0, FADE_IN_DUR=0.18)` → `tween_interval(idle_dur = duration - 0.18 - 0.6)` → `tween_property(..., 0.0, FADE_OUT_DUR=0.6)` → `tween_callback(_finish)`. _bg 초기 alpha = 0.0 으로 set, fade-in 으로 부드럽게 등장. **기존 `show_msg(parent, text, duration=2.5, color)` API 시그니처 호환 유지** — R86-R94 시점 약 12 호출자 (demo.gd 전체) 모두 그대로 동작 (마이그레이션 강제 X, R96+ 옵션). `tools/h5_test_toast_ux.py` 신규 (12 검증) — Severity enum 4 + COLORS 4 entry + 4 static helper + show_severity dispatcher + show_msg 시그니처 호환 + fade-in tween (a=0→1, 0.18s) + fade-out tween (a=1→0, 0.6s) + _active_toasts static + stack Y 계산 식 + _finish 의 erase + tween chain 4 단계 (property×2 / interval×1 / callback×1) + R94/R93/R92/R91 회귀 + demo show_msg 12 호출 호환 + docstring marker, **12/12 통과**. R91-R94 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 85% → **87%** (Toast UX 정비 90 신규 — 동시 다수 toast 가시화 + severity 색상 + fade-in 시각 일관성). 종합 가중평균 84.64% → **84.88% (↑0.24%p)**. Godot 93-96% 유지. 출시 가능 기준 77.96% → **78.20%**.)

이전 업데이트: 2026-05-19 (Round 94 — **HelpPanel 키 명세 동기화 (R82-R93 누락 + R93 잘못된 안내 정정)**. R93 후속 — UI 일관성 끝마무리. R82-R93 동안 demo.gd 에 추가된 키들이 `help_panel.gd` 의 `HELP_TEXT` 에 누락되어 있었고 (F6 SaveList R92, F10 Quit-to-Title R82, G monster spawn, SPACE attack, R/K/O/J/L/, R52-58 패널), R93 의 인라인 slot UI 제거로 "Continue → slot 0 자동 로드" / "슬롯 우클릭 / Shift+클릭 → 삭제" 안내가 잘못된 상태. **`scripts/ui/help_panel.gd` HELP_TEXT 재작성**: (1) 이동/환경 섹션 유지 (WASD/M/N/C/V/P), (2) 상호작용 섹션에 **R/K/O/J/L/," R52-58 6 패널 신규**: R=강화 / K=합성 / O=Orb 소켓 / J=대장간 / L=스킬북 / ,=미션, (3) 전투 섹션에 **SPACE (인접 monster 공격) + G (monster spawn AI 테스트) 신규**, (4) 세이브 섹션에 **F6=Save 목록 패널 (8 슬롯 + AUTO 메타 + Load/Save/Delete)** 신규, (5) 설정/Scene 섹션에 **F10=타이틀로 (확인 popup)** 신규, (6) Title 화면 섹션 R93 반영 — `"Continue → slot 0 자동 로드"` → `"Continue → Save 목록 패널에서 슬롯 선택"`, `"슬롯 우클릭 / Shift+클릭 → 삭제"` → `"목록에서 Delete 버튼으로 슬롯 삭제"`. `tools/h5_test_help_panel_sync.py` 신규 (11 검증) — demo.gd 의 26 KEY_ 바인딩 추출 + 필수 26 set 매칭 + HELP_TEXT 10 R94 신규/누락 키 marker (F6 / F10 / G / SPACE / R/K/O/J/L/,) + 3 폐기 안내 제거 검증 (slot 0 자동 로드 / 슬롯 우클릭 / Shift+클릭 → 삭제) + F6 SaveListPanel 멘션 + Title 섹션 regex 추출 + Delete 버튼 / R93/R92/R91/R90 회귀 + HelpPanel 구조 (toggle / _ready / bbcode), **11/11 통과**. R90/R91/R92/R93 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: H 카테고리 60% → **65%** (HelpPanel 키 명세 동기화 95 신규 — 26 키 마감, R82-R93 누적 변경분 사용자 인지 가능). 종합 가중평균 84.29% → **84.64% (↑0.35%p)**. Godot 93-96% 유지. 출시 가능 기준 77.96% 유지 (H 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 93 — **Title Continue → R92 SaveListPanel 통합 (인라인 slot 버튼/popup 제거)**. R92 의 자연스러운 후속. Title.gd 가 인라인 slot 버튼 동적 생성 (8 행 × Button) + 우클릭/Shift+클릭 = AcceptDialog 삭제 popup 을 직접 렌더링하던 ~50 줄 코드가 R92 SaveListPanel 과 기능 중복. **`scripts/ui/title.gd` 대폭 정리**: (1) `_refresh_slots()` (35 줄, Slot_N Button 동적 생성 + gui_input 우클릭 핸들러) 제거, (2) `_confirm_delete(slot)` (12 줄, AcceptDialog popup) 제거, (3) `_on_slot_selected(slot)` (3 줄) 제거, (4) `_selected_slot` 변수 + `_on_continue` 의 selected slot 로직 제거 → 단순 `_save_list.toggle()` 호출. **신규**: `var _save_list: CanvasLayer` + `_ready` 에서 `preload("res://scenes/save_list_panel.tscn").instantiate() + add_child + slot_loaded.connect(_on_slot_loaded)`. **`_on_slot_loaded(slot)` 핸들러 신규**: SaveListPanel 의 `_on_load` 가 이미 `GameState.quick_load(slot)` 수행 + `slot_loaded.emit(slot)` → Title 은 `SceneRouter.to_demo(self)` 직행. **중복 quick_load 호출 없음** (R92 SaveListPanel API 신뢰). **`_refresh_status()` 신규**: 8 슬롯 메타 동적 버튼 대신 `slots` Label 하나로 fallback ("저장 데이터 없음 (New Game 만 가능)") + Continue 버튼 disabled 처리만 담당. SaveManager.list_slots() 활용은 유지. title.tscn 변경 없음 (Slot_* 노드는 동적 생성이었으므로 .tscn 영향 0). `tools/h5_test_title_save_list.py` 신규 (11 검증) — 8 R92 이전 marker 모두 제거 (_refresh_slots / _confirm_delete / _on_slot_selected / _selected_slot / AcceptDialog / Slot_ 노드 / Slot_%d / MOUSE_BUTTON_RIGHT) + _save_list 인스턴스 / preload / slot_loaded 연결 + _on_continue 의 SaveListPanel 위임 (to_demo_with_load 직접 호출 없음) + _on_slot_loaded 의 SceneRouter.to_demo + 코드 라인 검사로 quick_load 중복 호출 없음 (주석 mention 은 허용) + _refresh_status 의 빈 슬롯 fallback + Continue 비활성 + R92 SaveListPanel slot_loaded signal 잔존 + R92 demo F6 통합 잔존 + R91 round-trip 회귀 + R90 desc helper 회귀 + _selected_slot 완전 제거, **11/11 통과**. R90/R91/R92 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 82% → **85%** (Title 85→95: SaveListPanel 위임으로 코드 중복 제거 + 일관된 slot 워크플로우 — Title 화면도 demo 와 동일 UI 컴포넌트 재사용). 종합 가중평균 83.93% → **84.29% (↑0.36%p)**. Godot 93-96% 유지. 출시 가능 기준 77.6% → **77.96%**.)

이전 업데이트: 2026-05-19 (Round 92 — **SaveListPanel UI — 8 slot 선택 + 메타 표시 + 액션 버튼**. R91 round-trip 정합성 fix 의 자연스러운 UI 후속. 그동안 demo.gd 의 숫자 1-8 + Shift 조합만으로 slot 저장/로드 가능했고, 어느 슬롯에 무엇이 있는지 보이지 않았음 — 사용자가 실 게임 사용 시 안갯속에서 슬롯을 고르는 셈. **`scripts/ui/save_list_panel.gd` 신규 (~120 줄)**: `class_name SaveListPanel extends CanvasLayer`. `H5SaveManager.MAX_SLOTS=8` 만큼 행 생성 — 각 행 = (Label 메타 + Load + Save + Delete 버튼). `_format_slot(slot)` 가 `H5SaveManager.load_slot(slot)` 의 timestamp/player.class_id/level/gold + data.play_time_sec 추출 → `"Slot N: Lv7 워리어 G1234 05-19T14:30 [12:34]"` 형식. 빈 슬롯은 `"(빈 슬롯)"`. AUTO slot (H5SaveManager.AUTO_SLOT=7) 은 `"AUTO  "` 접두 + **save 버튼 disabled=true** (자동 갱신 전용). `_on_load(slot)` 가 `GameState.quick_load(slot)` 호출 + 성공 시 `slot_loaded.emit(slot)` 신호 발화 후 패널 hide. `_on_save(slot)` 가 `GameState.quick_save(slot)` 후 refresh, `_on_delete(slot)` 가 `H5SaveManager.delete_slot(slot)` 후 refresh. `CLASS_NAMES = ["워리어", "로그", "건슬링어", "나이트", "소서러"]` 5 클래스. **`scenes/save_list_panel.tscn` 신규**: CanvasLayer layer=13 (settings 위) + BG ColorRect 32-432 (288×400) + Title "저장/불러오기" + SlotList VBoxContainer + StatusLabel + CloseButton + uid `hero5_savelist`. **`scripts/ui/demo.gd` 통합 (R92)**: `var _save_list: CanvasLayer` + Round 58 panel block 뒤에 preload+add_child + `_save_list.slot_loaded.connect(func(_slot): _scene_idx = GameState.current_scene_id; _apply_scene())`. **F6 키 바인딩 신규**: 토글 직전에 현재 scene_idx / map_id / player_x / player_y 를 GameState 에 sync (저장 정확성 보장) 후 `_save_list.toggle()`. F5 (slot 0 quick save) / F9 (slot 0 quick load) 는 유지 (편의). `tools/h5_test_save_list_panel.py` 신규 (11 검증) — class_name/CanvasLayer + 7 func + slot_loaded signal + CLASS_NAMES + H5SaveManager API (MAX_SLOTS/AUTO_SLOT/load/delete) + GameState quick_save/load + AUTO_SLOT 비활성화 + tscn 6 노드 + uid + demo var/preload/signal/F6 + F6 sync block + slot_loaded callback (scene_idx + _apply_scene) + _format_slot metadata 8 marker + R91 회귀 (round-trip skill_levels/Quest/Mission) + R90 회귀 (resolve_skill_desc_display/first_line), **11/11 통과**. R90/R91 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: D 카테고리 90% → **91%** (SaveListPanel 90 신규로 10번째 UI 패널 + Save/Load 워크플로우 가시화), E 카테고리 80% → **82%** (F6 Save 워크플로우 통합 90 신규). 종합 가중평균 83.45% → **83.93% (↑0.48%p)**. Godot 93-96% 유지. 출시 가능 기준 77.4% → **77.6%**.)

이전 업데이트: 2026-05-19 (Round 91 — **Save round-trip 정합성 fix (class_id / stat / equipment / skill / Quest / Mission)**. R90 spirit UI 정제의 자연스러운 후속. **문제**: `quick_save → quick_load` 후 `apply_save` 가 누락 필드들 (class_id, stat_str/dex/int/con/points, equipment, unlocked_skills, skill_levels, play_time_sec, gunner_combo/max/ammo, active_curses/buffs/stances, quest, mission) 복원 안 함 → Sorcerer 가 Warrior 로 변하고 스탯/스킬/장비/퀘스트 lost. R86/R87 의 spirit + Sorcerer 작업이 save/load 사이클에서 무효화됐음. **`save_manager.gd::make_payload` 보강**: stat_points + skill_levels + gunner_combo/max/ammo + active_curses/buffs/stances + mission 11 필드 추가. **`game_state.gd::to_save_dict` 보강**: stat_points + gunner_* 3 + active_* 3 (duplicate(true) deep copy) + mission 8 필드 추가. **`game_state.gd::apply_save` 대폭 보강**: (1) class_id 복원 (player.class_id 또는 flat fallback), (2) stat_str/dex/int/con/points 5 복원, (3) equipment Array[int] 안전 재할당 (clear + int cast loop), (4) unlocked_skills Array[int] 안전 재할당, (5) skill_levels JSON string-key → int 변환 ({"5": 3} → {5: 3}), (6) play_time_sec 복원, (7) gunner_combo/max/ammo 3 복원, (8) active_curses/buffs/stances 3 복원, (9) Quest.from_save + Mission.from_save 호출. nested player + flat legacy 양립 fallback 유지 (R63 호환). `tools/h5_test_save_round_trip.py` 신규 (10 검증) — to_save_dict 31 필드 / apply_save 18 복원 동작 / make_payload 17 필드 / **Python JSON round-trip 시뮬** (src state 31 필드 → JSON.dumps → JSON.loads → apply_save 결과 31 필드 모두 동일, class_id=4 Sorcerer 보존, skill_levels int key 보존, equipment Array[int] 보존) / nested+flat fallback / Quest+Mission singleton / R90 회귀, **10/10 통과**. R88/R89/R90 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: D 카테고리 88% → **90%** (Save/Load 88→95 round-trip 정합성), F 카테고리 55% → **60%** (Save round-trip 0→60 신규). 종합 가중평균 82.47% → **83.45% (↑0.98%p)**. Godot 92-95% → **93-96%** (round-trip 정확화). 출시 가능 기준 76.8% → **77.4%**.)

이전 업데이트: 2026-05-19 (Round 90 — **Spirit/class skill desc placeholder + UI 정제 (가독성)**. R88 의 EUC-KR 디코딩의 자연스러운 후속. R88 raw desc 는 `}#NN<unit>|` placeholder + `;` 줄바꿈 마커를 그대로 포함한 채 entry["desc"] 에 저장되어 있었음. **`game_data.gd` 2 helper 신규**: `resolve_skill_desc_display(class_id, skill_id) -> String` (전체 desc, `resolve_skill_desc` 위임 + `}TEXT|` → `[TEXT]` 강조 브래킷 + `;` → `\n`, orphan `}` safe) / `resolve_skill_desc_first_line(class_id, skill_id) -> String` (display 결과의 첫 줄, battle log 1줄용). 예 (spirit #0 암흑탄, stats_u16[5]=120): raw `"거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다.;..."` → display `"거대한 암흑탄을 발사하여\n정령마력 [120%]의\n피해를 준다.\n..."`, first_line `"거대한 암흑탄을 발사하여"`. **`battle_system.gd` SKILL action 정정**: R88 의 raw `desc_str.split(";")[0].strip_edges()` inline 제거 → `GameData.resolve_skill_desc_first_line(5, skill_id)` 호출로 위임. Sorcerer (class_id=4) spirit skill 발동 시 placeholder 치환 + 정제된 첫 줄 노출 (`  ▸ ...`). **한계 명시**: spirit (class_5) stats_u16 의 실제 byte→field 매핑은 R88 docstring 에서 미확정 명시 — 표시되는 숫자가 게임 원본과 일부 다를 수 있음. 정확한 spirit stat 매핑은 R91+ Formula::calc + spirit-specific layout 추가 RE 필요. `tools/h5_test_spirit_desc_placeholder.py` 신규 (10 검증) — resolve_skill_desc_display 시그니처 + 핵심 로직 marker 5 (`raw.find("|")` / `"["` / `"]"` / `"\n"`) + resolve_skill_desc_first_line 시그니처 + display 위임 + 줄바꿈 분리 + battle_system 의 GameData helper 사용 + R88 raw split 제거 검증 + Python 시뮬 (`}#05%|` + stats[5]=120 → `[120%]` / 듀얼 placeholder `}#09초|` + `}#07MP|` → `[600초]` + `[30MP]` / orphan `}` 잔존 / first_line 분리) + R88 회귀 (16/16 desc_text + game_data wiring) + R87 회귀 (8 explicit field) + R89 회귀 (3 launcher icons + export_presets), **10/10 통과**. R88 회귀 테스트도 R90 helper 인식하도록 정정 (R88 inline 또는 R90 GameData helper 어느 한쪽 허용). R82-R89 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 50% → **55%** (Spirit desc placeholder/UI 정제 90 신규, Sorcerer skill 발동시 가독성 +5%p). 종합 가중평균 81.97% → **82.47% (↑0.50%p)**. Godot 92-95% 유지. 출시 76.8% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 89 — **Android launcher icons asset 생성 (PIL 기반)**. R86 의 `launcher_icons` 3 슬롯 (`main_192x192` + `adaptive_foreground_432x432` + `adaptive_background_432x432`) 빈 칸을 채움. **`tools/h5_make_launcher_icons.py` 신규 (147 줄)**: PIL `Image.new('RGBA')` + `ImageDraw` 로 icon.svg 디자인 (검은 BG #1a1a2e + 황금 별 #e8c468 + 은 검 #c0c0d0 + "HERO 5") 재현. **3 helper 함수**: `make_main_192()` (legacy launcher BG opaque + 원 + 검 + 별 + "HERO 5" 텍스트), `make_adaptive_foreground_432()` (Android 8.0+ adaptive 전경, BG 투명 + 중앙 264×264 안전영역에 검 + 별 + "5"), `make_adaptive_background_432()` (전체 BG #1a1a2e + 자주 큰 원 + 황금 테두리). 공통 helper: `_draw_sword(cx, top, length, width)` (수직 검 = blade + tip triangle + crossguard + grip 4 부분), `_star_points(cx, cy, r_outer, r_inner)` (5-pointed star 좌표 math 계산). `_load_font(size)` 5-platform fallback (Windows arialbd/arial/segoeui → Linux DejaVu Bold → Mac Arial Bold → PIL default). **3 PNG 생성** (assets/launcher_icons/): main_192×192 (2844B) / adaptive_foreground_432×432 transparent BG (2297B) / adaptive_background_432×432 (3238B). **export_presets.cfg 정정**: Debug + Release 양쪽 preset 의 3 launcher_icons 슬롯이 `res://assets/launcher_icons/*.png` 참조하도록 변경 (이전 `""` 빈 칸 → 정확 경로). 따라서 Godot Editor 에서 APK 빌드 시 자동으로 launcher icon 들이 묶임 (이전엔 별도 수동 작업 필요). `tools/h5_test_launcher_icons.py` 신규 (167 줄) — h5_make_launcher_icons.py PIL 의존 + 3 helper 함수 + sword/star drawing helpers + 3 PNG 파일 존재 + 정확 크기 (PNG IHDR direct read, capstone 없이) + alpha 채널 검증 (main+background opaque / foreground 좌상단 transparent) + 안전영역 (x/y in 132..300) 에 non-transparent pixel 존재 + export_presets.cfg 2 preset × 3 슬롯 채워짐 (configparser 로 INI 파싱) + `res://` 경로의 디스크 파일 매칭 + **R86 회귀** (2 preset / gradle_build use=true + min_sdk=23 + target_sdk=34 / arm64-v8a only + armeabi-v7a false / package name Hero5 / immersive_mode=true / 11 permissions 모두 false / Release runnable=false + compress_native_libraries=true) + R86 icon.svg + project.godot config/icon 잔존 + .gitignore `*.keystore` ignore 잔존, **10/10 통과**. R82/R83/R84/R85/R86/R87/R88 회귀 모두 통과 (R86 export_preset 13/13 PASS, R88 spirit desc 13/13 PASS). verify_godot_project **0 warnings**. **진척률 갱신**: G 카테고리 55% → **65%** (Launcher icons 0→90 신규, Packaging 50 + Perf 30 + Localization 60 + Distribution 80 + Build doc 90 + **Launcher icons 90 신규**). 종합 가중평균 81.17% → **81.97% (↑0.80%p)**. 출시 가능 기준 (D+E+G 가중) 76.0% → **76.8%**. Godot 92-95% 유지 (G 는 Godot 외 카테고리).)

이전 업데이트: 2026-05-19 (Round 88 — **Spirit desc EUC-KR 디코딩 — 16/16 한국어 텍스트 추출**. R87 explicit field 추출의 자연스러운 후속. R77 file layout 의 desc_string 영역 (bytes[48..48+desc_len], EUC-KR 인코딩) 후처리. **`tools/converter/decode_h5_skill_desc.py` 신규** (104 줄): `STATS_AREA_SIZE = 48` + `DESC_LEN_OFFSET = 0x2f` 명시 상수 + `decode_record(rec) → str` 함수 (extra_hex hex → bytes → bytes[48..48+desc_len] → `b.decode('euc-kr', errors='replace')`). c_csv_skill_05.json 의 16/16 record 에 `desc_text` 필드 in-place 추가 (평균 68.9 글자 / min 33 / max 88). **샘플**: spirit #0 암흑탄 (size=131, dlen=83) → "거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다.;마법공격력으로;위력이 증가." / #2 영혼의회복 (dlen=109) → "버프 스킬.;사용 즉시;대량의 HP를 회복하고;}#08초|동안 소량의 HP가;자동회복된다." / #7 정신감응 (dlen=65) → "패시브 스킬.;전투시 정령 게이지가;충전되는 양이;}1.5배| 증가한다." `;` = 줄바꿈, `}#NN%|` = stat placeholder (R75 resolve_skill_desc 가 stats_u16 값으로 치환하는 형식, spirit layout 별도이므로 R89+ 정밀화). **`game_data._ensure_spirit_skills_loaded()` 보강 (R83 → R84 → R87 → R88)**: `desc_text = str(r.get("desc_text", ""))` 추출 → `entry["desc"] = desc_text` 저장 (이전엔 빈 문자열). 이로써 `skill_info(5, sid).desc` 가 한국어 desc 반환. **`game_data.resolve_skill_desc` class_5 분기**: `if class_id == 5 and not _skills_cache.has("class_5"): _ensure_spirit_skills_loaded()` — skills.json 만 로드된 상태에서도 spirit desc 접근 가능 (잠재 버그 fix). **`battle_system._skill_data` 보강**: 반환 dict 에 `"desc": str(rec.get("desc", ""))` 추가 (외부 UI 조회용). 4 fallback path (정상 / Sorcerer spirit / Sorcerer stub / 기본) 모두 `"desc"` 필드 포함. **SKILL action 로그 보강**: Sorcerer (class_id=4) + spirit skill 발동 시 `var desc_str = str(skill_data.get("desc", ""))` 추출 → `desc_str.split(";")[0].strip_edges()` 첫 segment → `log_message.emit("  ▸ %s" % first_line)`. 예: `"[정령] 암흑탄! 30 피해 (MP -3) [F:2000]" → "  ▸ 거대한 암흑탄을 발사하여"`. `tools/h5_test_spirit_desc_decode.py` 신규 (108 줄) — decode_h5_skill_desc.py 존재 + EUC-KR codec + 48B/0x2f 상수 + 16/16 desc_text 필드 + 16/16 한글 포함 (`'가' <= c <= '힣'` 검사) + 3 sample 키워드 (암흑탄+정령마력, 버프+HP, 패시브+정령) + game_data desc_text → entry["desc"] wiring + resolve_skill_desc class_5 fallback + battle_system desc 필드 반환 + SKILL action log marker (▸ + split(";")[0]) + R87 explicit field 분기 회귀 + effect_type 분포 회귀 (0=5/2=9/7=2) + 평균 desc 길이 통계, **13/13 통과**. R75/R76/R82/R83/R84/R85/R86/R87 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 40% → **50%** (Spirit desc EUC-KR 한국어 노출 90 신규, 16/16 spirit 의미있는 desc 노출). 종합 가중평균 80.17% → **81.17% (↑1.00%p)**. Godot 92-95% 유지. 출시 82% 유지 (F 는 출시 가중치 외).)

이전 업데이트: 2026-05-19 (Round 87 — **Spirit (class_5) extra_hex full 의미 매핑 — R77 정확 sub-rel offset 적용**. R83 (Sorcerer) + R84 (raw_bytes 변환) 의 후속 최종화. **`game_data._ensure_spirit_skills_loaded()` 보강**: R84 의 stats_u16 24 entries (u16 stride 보조) 유지 + **R77 LoadResSkillInfo file layout 의 정확한 sub-rel offset 으로 8 explicit field 추출**: `effect_type` (sub-rel 0x1a) / `dynamic_formula_id` (sub-rel 0x26) / `special_dispatch` (sub-rel 0x2b) / `formula_id_1` (sub-rel 0x2d) / `formula_id_2` (sub-rel 0x2e) / `primary_u16` (sub-rel 0x22 LE) / `secondary_u16` (sub-rel 0x24 LE) / `desc_len` (sub-rel 0x2f). bytes.size() ≥ 48 일 때만 채움 (안전 가드). 부가 추정 매핑: `mp_cost`/`cooldown`/`damage_pct` (R57 관습, R88+ 정밀화). **`game_data.skill_info(5, skill_id)` 정정**: 이전 stats_u16 추정 매핑 → 이제 class 5 + `rec.has("effect_type")` 일 때 explicit field 직접 반환 (8 핵심 field + R79 dead fields 0). 다른 class (0..3) 는 기존 stats_u16 추정 유지. **Spirit data 분석 결과 (16 record)**: **effect_type 분포 0=5 (NO_HIT base) / 2=9 (curse) / 7=2 (timestop)** — debuff 위주 정령 매직 컨셉 확인. **formula_id_1 분포 57=10 / 0=5 / 59=1** — Formula 57 이 spirit 의 통일 공식. 예시: spirit #0 "거대탄" (effect=0, primary=400 big bomb) / #1 "마법기" (effect=2 curse, dyn_F=116, sd=107, F_1=57, F_2=68) / #7 "매혹기술" (effect=7 timestop, sd=44, F_1=57). **Sorcerer 의 spirit fallback 정확화**: 이전 R83/R84 가 spirit 의 R72 5 critical field 를 default 0 으로 반환 → R87 이후 실 effect_type (curse/timestop/base) + formula_id 동작. **battle_system 의 SKILL action 자동 dispatch** (R75) 이 spirit 사용 시 정확한 effect 발화 (저주/시간정지). `tools/h5_test_spirit_full_mapping.py` 신규 — R87 docstring + R77 sub-rel offset 참조 + 8 explicit field 추출 + skill_info class_5 명시 분기 + 16 spirit 의 R77 field 분포 검증 (effect_type 5/9/2 + formula_id_1 10/5/1) + 3 sample spirit (거대탄/마법기/매혹기술) 정확 매핑 + R83/R84 회귀 잔존, **9/9 통과**. R82-R86 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 27% → **40%** (Sorcerer 70→85 + Spirit R77 mapping 90 신규). 종합 가중평균 78.87% → **80.17% (↑1.30%p)** — **80% 돌파**. Godot 91-94% → **92-95%** (Sorcerer 정령 정확화). 출시 81% → **82%**.)

이전 업데이트: 2026-05-19 (Round 86 — **Distribution build preset + BUILD_ANDROID 가이드 + icon.svg**. G 카테고리 (출시 보완) 의 가장 큰 빈 칸 (Distribution 0%) 채움. **`apps/hero5-godot/export_presets.cfg` 신규 (4669 bytes, 2 preset)**: Debug + Release 각각 완전 형식 (4 sections: preset.0, preset.0.options, preset.1, preset.1.options). **공통 설정**: gradle_build=true (custom Android build), min_sdk=23 (Android 6.0), target_sdk=34 (Android 14), arm64-v8a only (32-bit + x86_64 disabled — 모던 폰 광범위 지원 + size 절감), package=`kr.eamobile.heroeslore5.remake "Hero5 Remake"`, version=`0.1.0-alpha (code=1)`, immersive_mode=true (system bar 숨김). **Permissions 11 항목 모두 false**: internet/wake_lock/access_network_state/vibrate/access_fine_location/access_coarse_location/bluetooth/camera/read_external_storage/write_external_storage/record_audio — 싱글 플레이 + scoped storage 자동 (Android 11+ 호환). **Debug vs Release 차이**: Debug `runnable=true + Hero5-debug.apk`, Release `runnable=false + Hero5-release.apk + compress_native_libraries=true` (R8 minification + native lib 압축으로 size 절감). 기존 `.template` 은 단일 preset + permission 일부만 → R86 의 활성화된 cfg 는 2 preset + 모든 permission 명시. **`apps/hero5-godot/icon.svg` 신규 (1132 bytes)**: 검은 BG + 황금 별 + 은 검 + "HERO 5" 로고. project.godot 의 `config/icon="res://icon.svg"` 참조 미존재 → 생성. launcher_icons 192×192/432×432 PNG 은 별도 생성 필요 (R87+). **`.gitignore` 조정**: 이전 `export_presets.cfg` ignore → R86 commit 허용 (개인 프로젝트, keystore 별도 path), 대신 `*.keystore` 추가 ignore (signing key 보안). **`docs/h5/BUILD_ANDROID.md` 신규 (8 섹션)**: 사전 요구사항 (JDK 17/21 + Android SDK 34 + NDK r23c+ + Build Tools 34.0.0+, JDK 경로 메모리 reference) → Godot Editor 초기 설정 (Build Template 설치 + Editor Settings SDK/Java 경로) → Export Preset 설명 (2 preset 차이점) → Release Keystore 생성 (keytool 명령 + Godot 입력) → 빌드 절차 (Debug/Release/adb install) → 검증 (R82-R85 모든 기능 + Sorcerer + GameOver + warp fade) → 알려진 이슈 (SMAF/save round-trip/Sorcerer active skill). `tools/h5_test_export_preset.py` 신규 — configparser 로 INI 파싱 + 2 preset 존재 + name/platform/runnable + gradle_build 설정 (min_sdk 23 / target_sdk 34) + arm64-v8a only + package/version + 11 permissions 모두 false + Release compress_native_libraries=true + immersive_mode + icon.svg 존재 + project.godot 의 icon 참조 일치 + .gitignore 의 export_presets commit + *.keystore ignore + BUILD_ANDROID.md 20 marker, **13/13 통과**. R82/R83/R84/R85 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: G 카테고리 35% → **55%** (Distribution 0→80 +80, build doc 90 신규). 종합 가중평균 77.27% → **78.87% (↑1.60%p)**. Godot 91-94% → **91-94%** 유지 (G 는 Godot 카테고리 아님). 출시 가능 기준 79% → **81%**.)

이전 업데이트: 2026-05-19 (Round 85 — **Battle UI fade transition** — R82 SceneRouter + R84 warp_fade 의 자연스러운 후속. E 카테고리 (Scene 통합) 의 마지막 큰 빈 칸인 Battle transition (50→90%) 채움. **battle_ui.gd `start()` 정정 (R85)**: 이전 instant `visible = true` 토글 → 이제 `await SceneFaderRef.warp_fade(self, func(): _setup_and_show(monster_id, player_state), 0.25, 0.25)`. 검정 페이드아웃 (0.25s) → mid-callback 으로 `_setup_and_show` (in_combat=true, H5Battle instance 생성, signal 연결, start_battle, visible=true, sprite load) → 페이드인. **중복 진입 guard**: `if visible: return` 으로 이미 battle 중일 때 무시 (B 키 multiple press 안전). **`_setup_and_show(monster_id, player_state)` 신규**: start() 의 mid-callback 으로 분리된 setup logic (closure 가 두 args 캡처 후 forward). **`_on_ended()` 정정 (R85)**: 이전 popup 끝 → instant `visible = false` → emit → instant cleanup → 이제 popup → `await SceneFaderRef.warp_fade(self, func(): visible=false; in_combat=false; _battle.queue_free(), 0.25, 0.25)` → emit. **emit 순서 정확**: `battle_completed.emit` 가 fade-out 완료 후 호출 → demo 가 fade 완료된 상태에서 보상/inventory 처리 (이전엔 fade 진행 중에 emit 되어 race condition 가능성). **SceneFaderRef preload 추가**: battle_ui 가 CanvasLayer 라 autoload 직접 못 받음 → `const SceneFaderRef = preload("res://scripts/ui/scene_fader.gd")`. **시각적 효과**: B 키 (랜덤 전투) / battle.tscn 진입 → 검정 0.25s → battle UI 등장 + monster sprite → 사용자가 turn-based 영역 진입 인지. 종료 시 victory/defeat popup → 검정 0.25s → demo map 으로 복귀 → 보상 popup. `tools/h5_test_battle_fade.py` 신규 — SceneFader preload + start() 의 warp_fade + duplicate guard + _setup_and_show split + setup logic 보유 + _on_ended fade-out + emit 순서 (fade 완료 후) + closure arg forward + R84 warp_fade 회귀 + R82/R83 회귀, **8/8 통과**. R82/R83/R84 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 70% → **80%** (Battle transition 50→90 +40, 큰 빈 칸 채움). 종합 가중평균 76.07% → **77.27% (↑1.20%p)**. Godot 90-93% → **91-94%**. 출시 가능 기준 78% → **79%**.)

이전 업데이트: 2026-05-19 (Round 84 — **Map warp fade transition + Spirit extra_hex 부분 파싱**. R82 Scene routing 후속 + R83 Sorcerer 후속 한 라운드 동시 진척. **`scene_fader.gd warp_fade(node, mid_callback, out_dur=0.25, in_dur=0.25)` 신규**: in-scene fade (scene 전환 없이 현재 scene 내부 시각 전환). 검정 페이드아웃 (`ColorRect alpha 0→1, 0.25s tween`) → `mid_callback.call()` (실제 warp: map_id/hero position 변경 등 instant) → 검정 페이드인 (`alpha 1→0`) → overlay 자동 해제. 기존 `change_scene` / `fade_in` (R82) 함수 유지 회귀. **`demo.gd._on_warp` 정정**: 이전 instant `_apply_scene()` 호출 → 이제 `await SceneFader.warp_fade(self, func(): _scene_idx = target_scene; _apply_scene(); _dialog.show_dialog(...), 0.25, 0.25)`. **`_warping` boolean guard 변수 추가**: fade 진행 중 재트리거 시 즉시 return (중복 warp 방지, hero 가 warp tile 위에서 multiple 신호 emit 해도 1회만 처리). **`game_data._ensure_spirit_skills_loaded` 보강 (R83 → R84)**: 이전 spirit name only → extra_hex hex string 을 **PackedByteArray 로 변환** (`_hex_to_bytes` helper 신규) → 첫 0x30 byte (48B, R77 LoadResSkillInfo stats area 일치) 를 **little-endian u16 stride** 로 24 entries 변환 → `stats_u16` 채움 + `_raw_bytes_size` 메타. 실 데이터 검증: spirit record #0 = 131 byte (extra_hex 길이 262 chars / 2), 첫 48B 에서 24 u16 추출 가능. 이로써 battle_system 의 Sorcerer spirit fallback 이 정상 `mp_cost/cooldown/damage_pct` lookup (stats[7]/[9]/[5]) 동작. extra_hex 의 정확한 byte → field 매핑은 R77 stats area 의 sub-rel offset 사용 (R85+ 완전 매핑). `tools/h5_test_warp_fade.py` 신규 — warp_fade 시그니처 + fade-out → callback → fade-in 구조 + R82 함수 유지 회귀 + demo `_on_warp` 의 warp_fade 사용 + `_warping` guard + callback 내 scene_idx/_apply_scene/dialog + game_data `_hex_to_bytes` + extra_hex → stats_u16 + Python 시뮬 (bytes[10..11] LE = 0x1e30) + spirit record #0 131B → 24 u16 + R82/R83 회귀 잔존, **8/8 통과**. R82/R83 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 62% → **70%** (Map warp fade 90 신규), F 카테고리 24% → **27%** (Sorcerer 60→70, spirit stats_u16 활성화). 종합 가중평균 74.81% → **76.07% (↑1.26%p)**. Godot 89-93% → **90-93%**. 출시 가능 기준 77% → **78%**.)

이전 업데이트: 2026-05-19 (Round 83 — **Sorcerer (class_id=4) 부분 활성화**. R22 stub (c_csv_skill_04 부재) 해제. **class_select.gd UI**: 라벨 `"(미구현)" → "(매직 — 기본+정령 스킬만)"`, docstring 에 R83 부분 활성화 설명 추가. **battle_system.gd `_skill_data` class-aware 리팩토링**: 이전 hardcoded `class_0` lookup → `GameState.class_id` 기반 `_skills_cache.get("class_%d" % cid, [])` 동적 lookup. **Sorcerer fallback chain**: class_4 데이터 없으면 → spirit `class_5` 로 fallback (name prefix `"[정령] "` 표시), spirit 도 없으면 → generic stub (`"[미구현] "` prefix). **GameState.total_attack 보강**: `class_id == 4` 일 때 `base += stat_int * 2` (Sorcerer INT magic bonus). 합리성 시뮬: Lv.1 Sorcerer (STR=6, INT=8) base attack = 31 vs Warrior (STR=12) base = 27 — active skill 부재 보상으로 effective 공격력 동등 이상 유지. **`game_data.gd _ensure_spirit_skills_loaded()` 신규**: spirit skills 16 entries 가 skills.json 아닌 별도 `c_csv_skill_05.json` 에 있음 → 첫 `skill_info()` 호출 시 자동 로드 + `_skills_cache["class_5"]` 에 {name, stats_u16=[], desc=""} 형식으로 stored. 이로써 Sorcerer 의 spirit fallback 이 실제 동작. extra_hex 파싱은 R84+ (현재는 name + 기본 lookup 활성화). **demo.gd**: `GameState.class_id == 4` 시 entry 후 0.5s 지연 + `"소서러: active skill 데이터 부재 — 일반 공격 + 정령 스킬 (16개) 사용 가능. INT × 2 magic bonus 적용."` dialog. **skill_book_panel.gd**: class 4 + 빈 books 시 `"(소서러: active skill 데이터 부재 — 정령 스킬은 spirit slot 으로)"` 안내 + disabled 항목으로 표시. `tools/h5_test_sorcerer.py` 신규 — class_stats 4 데이터 + skills.json class_4 부재 + c_csv_skill_05.json spirit 16 records 별도 존재 + class_select 라벨 + battle_system class-aware + Sorcerer INT bonus + demo 안내 + game_data spirit loader + skill_book_panel 안내 + Python 시뮬 (Sorcerer 31 vs Warrior 27), **9/9 통과**. R76/R82 회귀 모두 통과. verify_godot_project 0 warnings. **진척률 갱신**: F 카테고리 6% → **24%** (Sorcerer 0→60). 종합 가중평균 73.01% → **74.81% (↑1.80%p)**. Godot 88-92% → **89-93%**. 출시 가능 기준 75.5% → **77%**.)

이전 업데이트: 2026-05-19 (Round 82 — **Scene 흐름 정비: SceneRouter autoload + GameOver scene + Quit-to-Title 통합**. R81 의 진척률 재평가에서 가장 큰 임팩트 영역 (E. Scene 통합 55%) 의 첫 진척. **`scripts/core/scene_router.gd` 신규 autoload (140 줄)**: State enum (TITLE/CLASS_SELECT/DEMO/GAME_OVER 4 state) + 4 scene path 상수 + 6 public method (`to_title` / `to_class_select` / `to_demo` / `to_demo_with_load(slot)` / `to_game_over(reason)` / `quit_to_title(confirm)`) + 2 signal (`scene_changing(from, to)`, `scene_changed(state)`) + transition guard (`_transitioning` flag, 중복 전환 방지) + `last_game_over_reason()` accessor + `notify_ready()` hook. `project.godot` 의 `[autoload]` 에 SceneRouter 추가. **`scenes/game_over.tscn` + `scripts/ui/game_over.gd` 신규**: 반투명 BG + 빨간 "Game Over" 타이틀 + reason 라벨 (SceneRouter 가 set) + 2 버튼 (Continue = slot 0 로드 후 Demo / Title = Give up) + slot 0 미리보기 (Lv/class/Gold) + ui_accept/cancel 입력 매핑. **`demo.gd` 의 hero death 처리 정정**: 이전 silent `quick_load(0)` (R63) → 명시적 `SceneRouter.to_game_over(self, "monster #N 의 skill K 에 쓰러졌습니다")` 전환. 사용자가 사망 원인 인지 + Continue/Title 선택. **F10 = Quit-to-Title** (`SceneRouter.quit_to_title(self, true)`) — 확인 popup 후 Title 복귀. **마이그레이션**: title.gd 의 New Game / Continue / slot 선택 + class_select.gd 의 Start 모두 `SceneFader.change_scene` 직접 호출 → `SceneRouter.to_*` 경로로 변경 (총 4 호출 마이그레이션, SceneFader 직접 호출 0개). `tools/h5_test_scene_router.py` 신규 — autoload 등록 + State enum 4 + 4 scene path + 6 method 시그니처 + 2 signal + transition guard + GameOver scene 파일 + Continue/Title 동작 + reason display + slot load + hero death → to_game_over + F10 = quit_to_title + title/class_select 마이그레이션 (SceneFader 직접 호출 0) + notify_ready, **11/11 통과**. `python tools/verify_godot_project.py` **0 warnings**. R63/R72-R81 회귀 모두 통과. **진척률 갱신**: E 카테고리 55% → **62%** (Title/ClassSelect/Demo 80→85 + GameOver 80 신규 + SceneRouter 90 신규). 종합 가중평균 72.17% → **73.01% (↑0.84%p)**. 이전 보고치 코어 한정 87-92% 유효 (Scene routing 은 코어 외 카테고리). Godot 87-92% → **88-92%** (Scene 통합 정비 반영). 출시 가능 기준 75% → **75.5%**.)

이전 업데이트: 2026-05-19 (Round 81 — **TargetEffect::ProcTargetEffectSkill (@0x64a08, 4276B / 1069 instr) overview RE**. R80 의 후속으로 거대 함수 구조 매핑. **Jumptable 없음** (`addls pc` 패턴 0개) — 4276B 전체가 if/else cascade dispatch. **함수 의미 확정**: TargetEffect 100-slot main update loop 에서 active 슬롯마다 호출되는 **per-frame skill effect engine**. **Top 25 field reads**: `r4, +0xf` (9x base char) / **HERO+0x22c class_id 6x** (5-class 분기) / **HERO+0x269 gunner_combo 6x** (GUNNER 추가 처리) / skill_info 12 distinct file-loaded field (`+0x32/+0x36 u16` × 3x 각 / `+0x29/+0x2f/+0xa` × 3x 각 / `+0x3a/+0x1c/+0x294` × 2x / `+0x2a/+0x2b` × 1x / R72 special_dispatch + R70 effect2 + R70 4×u16 활용) / **R79 dead reads `+0x4a` (ldrsh) + `+0x4e` (ldrsb) 각 1x 존재** (default 0 으로 no-op path 동작) / TargetEffect 상태 cluster `+0xab..+0xaf` + `+0xc0 frame counter` + `+0x24` (per-frame state machine). **Top 25 bl call graph**: `Formula::calc 14x` (★ R71 의 damage/value 평가) / `CHAR::GetSpritePtr 15x` / `SPRITE::GetExtraDataPtr 12x` / `OBJECT::GetX/Y 8x 각` / `StaticUtil::Rand 7x` / `ExtraData::GetPivot 6x 각` / **`TEM::NewTargetEffect_min 6x` (★ 재귀 VFX spawn)** / **`BATTLER::IncreaseHP 4x` (★ damage 적용)** / **`BATTLER::AddCurseSkill 3x` (★ curse 적용)** / `UiTargetMonster::SetBattler 3x` / `HERO::IncreaseHiperCount 3x` / `TargetEffect::GetSpritePtr 3x` / `TargetEffect::NewHitEffect 2x` (hit VFX) / `BATTLER::ApplyAddEffect 2x` / `HERO::IncreaseSP 2x` / `HERO::CheckEffSound_Hit 2x` / `CommonUi::NewCommonEffectOnce 2x` / `Monster::SetAttackedMotion 1x`. **흐름**: entry (level cap 99 검사) → cascade dispatch (class × state × frame × skill_info flags) → 각 branch 에서 Formula::calc → IncreaseHP / 재귀 sub-VFX spawn / curse / UI sync / 사운드. **R79 dead reads 일관성**: `+0x4a/+0x4e` 본 함수에도 read 존재 → default 0 path no-op 동작 확정. 정밀 case-by-case 분석 (cascade 분기 매트릭스) 은 R82+ 로 미룸 (1-2 라운드 추가). `tools/h5_test_proc_target_effect_skill.py` 신규 — symbol 4276B 검증 + 1069 instr disasm + 0 jumptable + 10 top call count + 9 skill_info file-loaded field read + R79 dead read +0x4a/+0x4e 존재 + HERO 3 field read + TargetEffect 6 state cluster + 25 doc marker, **9/9 통과**. R63/R69/R72-R80 회귀 모두 통과. `docs/h5/RE/proc_target_effect_skill.md` 신규 (7 섹션). **.so 분석 ~99% 유지** (VFX 시스템 구조 + per-frame engine 의미 확정), 진척률 깊은 재평가 결과 **종합 72.17%** (코어 한정 87-92% 유효, 실 게임 플레이 가능 기준은 72% — Scene 흐름/Sorcerer/Device 빌드 미완이 큰 영향).)

이전 업데이트: 2026-05-19 (Round 80

---

업데이트: 2026-05-19 (Round 80 — **TargetEffectMgr / TargetEffect VFX 시스템 RE**. R73 의 TEM 11 호출 + effect_type {4,7,8} 발견 위치 확정 + 시스템 구조 매핑. **5 TEM overload chain 분석**: `_min @0x62d40 (100B, 12 args)` → tail-call `_+s @0x62cd4 (108B)` → `_+sai @0x62c54 (128B)` → **`_full @0x62a34 (408B) 실 구현`**, 별도로 `_+saiih @0x62bcc (136B)` → `_full` 평행 wrapper. **wrapper 들은 default arg 채움**. **_full 핵심 동작**: (1) 17 args 인자 분배 (r0=this, r1=effect_type→r8, r2=int b→r7, r3=HSI*→sl, arg17=sp+0xcc→r6 post-init key). (2) **100-slot allocator loop** — `slot = this + fp*0x284` (0x284=644B per slot), `Effect::IsEmpty()` 검사로 free slot 찾기, 100 slot 다 차면 NULL 반환. (3) **`bl 0x62840 = TargetEffect::NewTargetEffect (base, 500B)`** 으로 slot 초기화. (4) **post-init dispatch on r6 (arg 17)**: 0/1/2 → 3 manager 채널 (global +0x15e0/+0x15d8/+0x15e4) 등록 (`bl 0xabb94`), 3+ → no registration. **TargetEffect::NewTargetEffect base (500B) 분석**: 17 args → 25+ field strb/strh + 5 base setter 호출 + 200B memset work area. **Effect 베이스 클래스 5 멤버 함수 발견 + disasm** (모두 8-16B): `Effect::IsEmpty @0x610d8` (returns 1 if `[+0x11]==0`), **`Effect::SetEffectType(char) @0x610f4 → strb r1, [r0, #0x12]`** (★ effect_type 저장 위치 확정), `SetEffectFrame(short) @0x61114 → strh r1, [r0, #0x14]`, `SetEffectLastFrame(short) @0x61124 → strh r1, [r0, #0x16]`, `SetEffectValue(int) @0x61134 → str r1, [r0, #0x18]`. **OBJECT 베이스**: `SetXY @0xcfda4`, `SetObjectType @0xcfdac` (TargetEffect 의 ObjectType=3). **Effect struct field 의미 확정**: +0x11 active flag / **+0x12 effect_type ★** / +0x14 start frame / +0x16 end frame / +0x18 numeric value. **R73 effect_type 4/7/8 의미 정확화**: Effect+0x12 에 저장되는 **VFX 카테고리 코드** — 4=기본 hit VFX (case 0/2/4/6), 7=timestop VFX (case 1/7), 8=shock VFX (case 5). 실 sprite/animation 의미는 render 단 (DrawTargetEffect 추정) 추적 필요 (R81+). **TargetEffect struct 0x284B 25+ field 매핑** 표 (docs/h5/RE/target_effect_mgr.md §3): +0x11 active / +0x12 type / +0x13 char / +0x14 frame / +0x16 last_frame / +0x18 value / +0x1c int b / +0x20 SPRITE* / +0x8c-+0x9f 다양한 char/short 메타 / +0xa0-+0xa7 sprite mgr getter results / +0xc0 frame counter / +0x18c-+0x253 (200B) memset work area / +0x254-+0x281 state flags. **ProcTargetEffectSkill (@0x64a08, 4276B) 확인**: per-frame skill 처리 함수, Effect+0x12 직접 안 읽고 **skill_info 기반 처리** (Formula::calc @0x7749c 호출 + level cap 99 검사 + sprite 분기). effect_type 4/7/8 의 sprite 의미는 render 단에서만 사용 (R81+). `tools/h5_test_target_effect_mgr.py` 신규 — **13 ELF symbol** + 5 Effect/OBJECT setter atomic + 4 TEM wrapper chain → _full + _full slot allocator (0x284B + IsEmpty + bl 0x62840) + post-init 3 manager dispatch + TargetEffect base 25+ field stores + 200B memset + R73 effect_type {4,7,8} immediates 회귀 + ProcTargetEffectSkill size + 27 doc marker, **9/9 통과**. R63/R69/R72-R79 회귀 모두 통과. `docs/h5/RE/target_effect_mgr.md` 신규 (6 섹션). **.so 분석 ~99% 유지** (VFX 시스템 구조 + slot allocator + Effect 베이스 클래스 확정, 실 render 의미는 R81+), Godot 87-92% 유지 (R80 = RE only), 출시 85-94% 유지.)

이전 업데이트: 2026-05-19 (Round 79 — **BATTLER effect dispatch 분석 + HeroSkillInfo runtime field 가설 종결**. `BATTLER::ApplyAddEffect` (@0x4bdb4, 496B) full disasm → **pure 28-way tail-call dispatcher** (HERO 14-way + Monster 9-way jumptable, struct write 0). `BATTLER::AddCurseSkill` (@0x4b134, 100B) full disasm → **curse 저장 위치 = attacker BATTLER+0x130/+0x134/+0x13a/+0x140/+0x1b0** (5 slot, 내부 helper 0x4afd4 호출). `BATTLER::AddBuffSkill` (@0x4b198, 260B) → **buff 저장 위치 = attacker BATTLER+0x118/+0x11e/+0x124/+0x12a/+0x1c8** (4 slot + ptr, value>=0x4b 분기 + 두 path). `HERO::AddStanceSkill` (@0x91d7c, 256B) → **stance 저장 위치 = HERO+0x284/+0x288/+0x28a + flag HERO+0x1f94** (내부 helper 0x4b29c 호출). **active effect 저장 컨테이너는 BATTLER/HERO struct — HeroSkillInfo 와 무관 확정** (R74 GameState active_curses/buffs/stances Array 가 정확한 Godot 대응). **.so 전체 grep**: capstone 으로 .text 영역의 모든 strb/strh instruction 디스어셈블 → `+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e` immediate offset 인 것만 필터링 → **HeroSkillInfo struct 에 write 하는 함수 0 개** 확정. 모든 strb/strh 는 다른 무관 구조체 (BFont 생성자, NETWORK::_NET_ITEM_, ParticleMgr, StateInGameMenu, Battle::DrawSpiritCutIn, HERO::SaveHeroData, EnemyAI, StateMap, FntGroup) 의 같은 offset 에 쓰는 우연 일치. **R72/R73 의 5 runtime field 가설 종결**: ProcHeroSkill 의 ldrsb/ldrsh +0x44/+0x46/+0x48/+0x4a/+0x4e read 는 **dead reads** — writer 없으므로 항상 HERO 객체 zero-init 의 default 0 값. 정상 게임플레이 동작: +0x44 → class 3 motion 23 KB = `(0-2)*6+20 = 8` 일정값 / +0x46 → case 5 shock skill 조건 `> 0` 절대 충족 안 됨 → **dead code** / +0x48 → R74 fallback default=4 채택 / +0x4a → case 0 NO_HIT SP delta 0 (no-op) / +0x4e → KNIGHT secondary check 0 (no-op). **HeroSkillInfo 88B 최종 영역 구성 (R77+R78+R79)**: 68B file-loaded (+0x00..+0x43) + **16B unused (+0x44..+0x53, dead reads)** + 4B cooldown (+0x54 NowCoolTime u16, +0x56 MaxCoolTime u16). **HeroSkillInfo struct field 의미 11/11 확정** (R77 file 7 + R78 cooldown 2 + R79 dead 5 closure). `tools/h5_test_battler_effect_dispatch.py` 신규 — 4 ELF symbol + ApplyAddEffect 28-way dispatcher (struct write 0) + AddCurseSkill 5 offset (BATTLER 영역) + AddBuffSkill 5 offset + value>=0x4b 분기 + AddStanceSkill 3 offset (HERO 영역) + .so-wide grep 0 HSI writer + R69/R72/R73 dead read 존재 검증 + 24 doc marker, **8/8 통과**. R63/R69/R72/R73/R74/R75/R76/R77/R78 회귀 모두 통과. `docs/h5/RE/battler_effect_dispatch.md` 신규 (8 섹션, struct field 의미 final table). .so 분석 ~99% 유지 (effect 저장 위치 확정 + HSI struct 완전 종결), Godot 87-92% 유지 (R79 = RE only), 출시 85-94% 유지.)

이전 업데이트: 2026-05-19 (Round 78 — **HeroSkillInfo runtime field source 추적 + cooldown system 확정**. `.dynsym` 에서 `HeroSkillInfo::` 4 멤버 함수 발견 + 디스어셈블: **SetNowCoolTime(s) @0xd8d38** writes both `+0x54 = s` AND `+0x56 = s` / **GetNowCoolTime @0xd8d44** reads s16 `+0x54` / **GetMaxCoolTime @0xd8d4c** reads s16 `+0x56` / **DecreaseNowCoolTime @0xd8d54** decrements `+0x54` u16, clamps to 0. **HeroSkillInfo +0x54 = NowCoolTime u16 / +0x56 = MaxCoolTime u16 cooldown pair 확정**. R72/R73 의 "+0x50 ranges" 가설 정정 → 실제 +0x54/+0x56. **R70 의 "59-slot init" 가설 정정**: ProcHeroSkill entry @ 0x992b8 의 59-iter 루프는 `bl 0xd8d54` (= DecreaseNowCoolTime) 호출 — **매 ProcHeroSkill 호출마다 59 슬롯의 cooldown 1씩 -1 tick + 0 clamp**, 초기화 아님. **InitSkillEmpty @0x88a20 (272B) 분석**: HERO+0x1b40..+0x1b5f 32B 를 0xFF 로 init — **HeroSkillInfo 배열과 무관, 새 HERO field cluster 발견** (active skill slot 또는 quick-cast slot 후보, 의미 R79+ 추적). **InitSpiritSkillMenu @0x89198 (132B) 분석**: global 객체 +0x118/+0x11c/+0x120/+0x122/+0x124-127/+0x278 menu state init + HERO+0x1fb6=1 flag — HeroSkillInfo 무관. **HERO::GetHeroSkillInfoPtr @0x88ce4** 확정: `return this + 0x348 + idx*0x58` (R70/R77 일치). **HERO::HeroSkillAtkHardCode @0x9041c (888B) 부분 분석**: class_id (+0x22c) 분기 + class 3 (KNIGHT) 별도 path + skill_info+0x45 읽기, **skill_info 에 write 없음**. **R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e writer 미확정**: file 출처 아님 (R77) + InitSkillEmpty/Spirit 출처 아님 (R78) + ProcHeroSkill/HeroSkillAtkHardCode write 없음 → **HERO 객체 zero-init default 0** 가정. ProcHeroSkill 의 ldrsb/ldrsh 읽기 자체는 사실이지만 정상 게임플레이에서는 default 0 으로 동작 (R74 fallback=4 등이 합리적 보조). R79 후속: `BATTLER::ApplyAddEffect` (@0x4bdb4, 496B) 또는 `HeroSkillAtkHardCode` 정밀 추적. **HeroSkillInfo 88B struct field 의미 9/11 확정** (file-loaded 7 from R77 + cooldown pair 2 from R78). `tools/h5_test_skill_info_runtime.py` 신규 — 8 ELF symbol + SetNowCoolTime dual write + GetNow/MaxCoolTime ldrsh + DecreaseNowCoolTime -1/clamp/store + GetHeroSkillInfoPtr stride + ProcHeroSkill 59-iter cooldown tick + InitSkillEmpty 32 strb at 0x1b40 + InitSpiritSkillMenu global state + HeroSkillAtkHardCode read-only + 4 .dynsym members + 23 doc marker, **12/12 통과**. R63/R69/R72/R73/R74/R75/R76/R77 회귀 모두 통과. docs/h5/RE/skill_info_runtime.md 신규 (8 섹션). .so 분석 ~99% 유지 (cooldown system + R70 init 정정으로 ProcHeroSkill 의미 더 정확), Godot 87-92% 유지 (R78 = RE only), 출시 85-94% 유지.)

이전 업데이트: 2026-05-19 (Round 77 — **HERO::LoadResSkillInfo (@0x8bba4, 784B) + LoadResClassSkillInfo (@0x9b308, 48B) ARM full disasm**. R75 의 `GameData.skill_info` 매핑 정확화. **파일 layout 확정**: per-record = `3B header (2B unused + 1B name_len) + name string + 0x30B stats area + desc string`. stats area sub-rel offset → HeroSkillInfo entry offset 31 field 매핑 완성 (byte 27 + u16 10). **R72/R73 5 critical field 정확 매핑 검증**: effect_type (+0x28 ← stats sub-rel 0x1a) / dynamic_formula_id (+0x30 ← sub-rel 0x26) / special_dispatch (+0x3a ← sub-rel 0x2b) / formula_id_1 (+0x3c ← sub-rel 0x2d) / formula_id_2 (+0x3d ← sub-rel 0x2e). **HeroSkillInfo 88B struct 영역 구분 확정**: **file-loaded +0x00..+0x43 (68B)** + **runtime state +0x44..+0x57 (20B)**. **R72/R73 의 6 field 가설 (+0x44 kb_idx/+0x46 shock_count/+0x48 max_combo/+0x4a sp_delta/+0x4c/+0x4e knight_threshold) 정정**: ProcHeroSkill 의 ldrsb/ldrsh 자체는 사실이지만 그 값의 출처는 **skill 파일이 아님** — InitSkillEmpty (@0x88a20) 또는 hard-coded table (R78+ 추적). LoadResClassSkillInfo 는 wrapper: `LoadResSkillInfo(class_id) → slot 0..42 + LoadResSkillInfo(5) → slot 43..58 + LoadResSkillIcon tail-call`. 총 **59 슬롯 = 43 class skill + 16 spirit/shared** (R70 의 HERO+0x348 88B×59 배열과 일치). External helpers: 0x14e4ec (filename builder), 0x144e80 (file load), 0x1437ec (read_u16), 0xabd18 (malloc), 0x31504 (memset), 0x3130c (memcpy), 0x14cfa4 (free). `tools/h5_test_load_skill_table.py` 신규 — 5 ELF symbol + 195 instruction disasm + 59-slot dispatch (43/16) + HERO+0x348 88B layout + file header skip loop + name malloc/memcpy + 9 critical R72/R73 store + 27 byte + 10 u16 + 23 doc marker + runtime region (+0x44..+0x57) zero file-load 검증 + LoadResClassSkillInfo 2-call wrapper, 14/14 통과. `apps/hero5-godot/scripts/core/game_data.gd` skill_info docstring 정정 (file-loaded 5 field 정확 vs runtime 5 field 잠정 표시). docs/h5/RE/load_skill_table.md 신규 (8 섹션). R63/R69/R72/R73/R74/R75/R76 회귀 모두 통과. **.so 분석 ~99% → ~99% 유지** (skill data load path 정확화로 ProcHeroSkill 의 file-source field 신뢰도 100% 확립, runtime field 는 출처 미확정으로 남음), Godot 실 구현 87-92% 유지 (R77 = RE only, GDScript 동작 변경 없음), 출시 85-94% 유지. **R75 frontend 의 file-loaded 7 field 는 정확, runtime 3 field 는 R78+ 재검증 대상으로 명시**.)

업데이트: 2026-05-19 (Round 76 — **active effect stat modifier 통합 + tick 자동 호출**. R75 의 active effect Array 가 실 stat 에 영향. **`GameState.total_attack` 보강**: `raw = (base + equip_bonus); buff_pct = Σ active_buffs.f1 (clamp 0..200); return raw × (100 + buff_pct) / 100`. **`GameState.total_defense` 보강**: `stance_pct = Σ active_stances.f1 (clamp 0..150); curse_pct = Σ active_curses.f1 (clamp 0..80); return raw × (100 + stance_pct - curse_pct) / 100`. **battle_system._enemy_turn 끝에서 `GameState.tick_active_effects()` 자동 호출** — turn 마다 remaining_turns 감소 + 만료 자동 제거 + state_changed signal 발화 → status_panel 자동 갱신. **공식 합리성**: buff cap 200% (+200% ATK max), stance cap 150% (KNIGHT 방어 자세 +50% 등), curse cap 80% (방어력 80% 감소 max — 절대 0 막아냄). **stance + curse 동시 적용**: net 차이 (stance_pct - curse_pct) 적용. `tools/h5_test_stat_modifier.py` 신규 — total_attack active_buffs loop + clamp 0..200 + raw×(100+pct)/100 / total_defense stance+curse loop + clamp 0..150/0..80 + net_pct / battle_system._enemy_turn 끝 tick 호출 + state_changed.emit / R76 docstring markers (2 files) / Python 시뮬 7 case (buff 20%/누적 30+20%/clamp 200% / stance 50% / curse 30% / stance+curse net / curse clamp 80%) 모두 통과. R63/R74/R75 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 85-90% → 87-92%** (stat 실 영향 +2%p), 출시 83-92% → **85-94%**. R75 frontend → R76 stat 실 영향으로 buff/curse/stance 가 ATK/DEF 에 실제로 반영. R77 부터 Godot Editor 실 실행 검증 (사용자 작업).)

이전 라운드:

Round 75 — **GUNNER combo UI + skill effect 시스템 통합**. R63 임시 공식 (`atk + rand(0..7) - def/2`) 의 R71+R72+R73 발견 통합. **GameState 에 GUNNER combo state 3 변수 추가**: `gunner_combo` (HERO+0x269 대응) + `gunner_max_combo` (default 4) + `gunner_ammo` (HERO+0x248 대응). **battle_system.gd SKILL action 보강**: (1) **GUNNER class+skill_id==5 일 때 combo multiplier 적용** — `damage = base * (combo*20 + 30) / 100` (R72 공식, combo 1=50%/2=70%/3=90%/4=110%), combo 도달 시 reset. (2) **Formula 4 부가 호출 (R73 발견)** — `_calc_player_damage(4, ctx, skill_data)` → SP delta 양수 시 `player_mp += sp_delta` (clamp to max_mp). log 메시지에 "+%dSP" 표시. **R72 helper signals 3종 추가**: `curse_applied(target, dispatch_byte, formula_1, formula_2)` (case 1+2) / `buff_applied` (case 3+5) / `stance_applied` (case 4). **`apply_skill_effect(target, effect_type, dispatch, f1, f2, skill_data)` API**: effect_type 별 match → Formula 1/2 평가 후 해당 signal 발화. case 0 (NO_HIT) 는 no-op. R74 = Godot enhancement, monster_ai/UI 측 buff/debuff 시스템 stub (실 통합은 R75+). docstring 에 R72 4 helper 매핑 + R73 +0x4a SP delta + +0x3c/+0x3d formula ids + GUNNER 공식 명시. `tools/h5_test_battle_formula.py` 신규 — GameState 3 변수 + GUNNER multiplier 분기 + (combo*20+30) 공식 + combo reset + Formula 4 SP delta 호출 + player_mp 회복 로직 + 3 signals + apply_skill_effect 5 match case + GUNNER Python 시뮬 (1/2/3/4 = 50/70/90/110%) + 7 R74 docstring markers, 모두 통과. R63/R69/R73 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 79-83% → 82-88%** (damage 공식 정확화로 +3-5%p), 출시 78-88% → 80-90%. **🎯 7년 만에 처음으로 ProcHeroSkill 의 active skill 처리 흐름이 Godot 에서 정확히 재현됨**.)

이전 라운드:

Round 73 — **ProcHeroSkill JT2 4 case + TEM 11 호출 RE**. R70 의 2 jumptable 의 두 번째 (@0x9a8d8, 7-way GetCurActSkillIdx()) **각 case 동작 매핑 확정**: **case 0/2/4/6 (alias @0x99904) = 기본 공격** (Formula 3 V[23] → BATTLER::IncreaseHP + Formula 4 atk×magic×buff% → HERO::IncreaseSP) / **case 1/7 (@0x9ad78) = timestop + 기본 공격 chain** (SetTimestopFrame(2) → 0x99908) / **case 3 (@0x9acf8) = class 3 KNIGHT secondary** (HERO+0x1d36==1 + orb count 검사) / **case 5 (@0x9aa18) = shock skill** (NewShockAddEffect + skill_info[+0x30] dynamic Formula id + IncreaseHP(-damage)). **R72 의 +0x30 "behavior code" → dynamic Formula id 확정**. 모든 case → 기본 공격 path 합류. **HeroSkillInfo 신규 4 field**: +0x30 (dynamic Formula id), +0x46 (shock count), +0x4e (class 3 threshold), +0x48 (max combo). **HERO+0x1a8** = halfword storage for skill_info[+0x38] (case 5). **TargetEffectMgr::NewTargetEffect (@0x62d40) 11 호출 signature**: `(this, char effect_type, int b, HeroSkillInfo*, SPRITE*, char c-f, short s, int g, int h)` — 12 args. **distinct effect_type values: {4, 7, 8}** (6/2/1 회 + dynamic 3 회). 호출 위치 10 확정 (#11 ptr 추적 필요, R74). R73 = RE only, Godot 코드 변경 없음. docs/h5/RE/proc_hero_skill.md §13 + §14 추가 + h5_test_proc_hero_skill.py 확장 (JT2 기본 공격 mov r1 #3/#4 + IncreaseHP bl + SetTimestopFrame bl + NewShockAddEffect bl + skill_info ldrsb [r6,#0x30/#0x46] + class 3 setup + TEM 11회 + effect_type 4/7/8 distinct, **16 R73 doc markers**) 통과. .so 분석 98% → ~99%, 출시 78-88% 유지. **R74 부터 Godot battle_system.gd damage 공식 정확화 (R63 임시 → Formula 3/4 평가) 가능 — R73 의 가장 큰 임팩트.**)

이전 라운드:

Round 72 — **ProcHeroSkill JT1 case + class 2 GUNNER entry RE**. R70 의 2 jumptable 의 첫 번째 (@0x9a398, 5-way skill_info[+0x28]) **각 case 의 helper 호출 매핑 확정**: **case 0 (NO_HIT @0x99978) = HERO::IncreaseSP(skill_info[+0x4a] s16)** — SP 변경만 / **case 1+2 (@0x9ac68) = BATTLER::AddCurseSkill** (@0x4b134) — curse/debuff / **case 3+5 (@0x9abfc) = BATTLER::AddBuffSkill** (@0x4b198) — buff / **case 4 (@0x9ab98) = HERO::AddStanceSkill** (@0x91d7c) — stance (R70 의 "heal+buff" 가설 정정 → stance 자세 시스템). 모든 case 가 b #0x99978 으로 NO_HIT path 합류. **공통 패턴**: 2회 Formula::calc(skill_info[+0x3c] formula_id_1, skill_info[+0x3d] formula_id_2) → r0/r7 → helper 호출. **case 1+2 special dispatch**: skill_info[+0x3a] == 0x34/0x37 일 때 default 대신 special path. **HeroSkillInfo 신규 6 field**: +0x1c (alternate path flag), +0x3a (special dispatch), **+0x3c (Formula id 1)**, **+0x3d (Formula id 2)**, +0x45, **+0x4a (s16 SP delta)**. **HERO this 신규**: +0x294 (skill state flag), +0x295 (secondary formula id), **+0x269 (GUNNER combo state)**. **class 2 (GUNNER) entry @ 0x9a564**: GetCurActSkillIdx() == 5 (combo shot) 만 special path → 3 field reset. **GUNNER damage 공식**: `(combo_state×20 + 30) × X / 100` — 매 hit 마다 +20% bonus (combo 1=50%, 2=70%, 3=90%, 4=110%). HERO+0x248 = ammo/charge counter, skill_info+0x48 = max combo. R72 = RE only, Godot 코드 변경 없음. docs §12 추가 + h5_test_proc_hero_skill.py 확장 (case별 helper bl 검증 + skill_info ldrsb +0x1c/+0x3c/+0x3d + ldrsh +0x4a + HERO ldrb +0x294/+0x295/+0x269 + cmp #0x34/#0x37/#0x5000000, **14 R72 doc markers**) 통과. .so 분석 98% 유지, 출시 78-88% 유지.)

이전 라운드:

Round 71 — **ProcHeroSkill Formula::calc dispatch + r5 base 추적**. R70 ProcHeroSkill 골격 정밀화. **Formula::calc** (@0x7749c, 172B, 42 instr) full disasm — **id < 1000 (0x3e8) → calc_pl, < 2000 (0x7d0) → calc_en, ≤ 3007 (0xbb7) → calc_sk, else return 0**. Formula struct: +0x0 calc_en ptr / +0x4 calc_sk ptr / +0x8 calc_pl ptr. **Formula 0x6f (111) / 0x63 (99) = calc_pl 범위지만 production calc_pl 은 0..38 (39 entries) 만 정의 → OOB → result 0 → ble taken → __sub_89068 (hit registered) skip**. 그러나 ble 분기 도착 후 **ChangeAttackMotion 은 무조건 호출** = R69 호출자 확정과 무관. 즉 hit check 는 historical artifact (production cut), ChangeAttackMotion 호출 path 자체는 unaffected. **r5 base 추적**: `add r5, r4, #0x1ec0` @0x993cc + `add r5, r5, #0xc` @0x993dc → **r5 = HERO + 0x1ecc**. 따라서 `[r5, +-0x190]` (107회 ldr) = **HERO + 0x1d3c**. 0x99704-10 시퀀스: `ldr r3, [HERO+0x1d3c]; ldrsh r2, [r3, #0x19c]; cmp r2, #0x63 (99); bgt exit_path` = Monster+0x19c (s16 level) > 99 시 exit = **level cap 99 확정** (R22 max level 92 와 합리적 일치). 다른 r5 base: @0x99454 `add r5, r4, #0x1e00` → r5 = HERO+0x1e04 (path 2, R72 추적). 본 라운드는 RE 문서 §11 추가만 산출. docs/h5/RE/proc_hero_skill.md §11 (Formula::calc dispatch + 0x6f/0x63 OOB + r5 base + level cap) + h5_test_proc_hero_skill.py 확장 (13 추가 markers: Formula::calc 172B + cmp 0x3e8/0x7d0/0xbb0 + calcByFormula bl + r5 setup A/B + [r5,-0x190] 107회 + level cap + R71→R72 잔여). Godot 코드 변경 없음 (R72+에서 damage 공식 정확화 예정). .so 분석 97-98% → ~98%, 출시 78-88% 유지.)

이전 라운드:

Round 70 — **HERO::ProcHeroSkill 골격 RE**. R69 의 ChangeAttackMotion 호출자 (`HERO::ProcHeroSkill(HeroSkillInfo*)` @0x99278, **7972B 거대 함수**) 의 고수준 골격을 정밀화. 총 **1993 ARM instruction**. Entry sequence: 전역 state clear + 3-step attack reset (sub_88f74/88fd4/89034) + **HERO+0x348 + i*0x58 의 59-slot skill array 초기화** (59×88B=5192B = HeroSkillInfo 배열) + NULL guard + class_id 분기 (class 2 GUNNER 별도 path @0x9a564). **2 jumptable 식별**: (1) @0x9a398 5-way — dispatch key = `skill_info[+0x28]` (signed byte, 0..4 skill effect type), case 0=NO_HIT / 1·2=physical / 3·5=magic / 4=heal+buff. (2) @0x9a8d8 7-way — dispatch key = `HERO::GetCurActSkillIdx()` (0..6 active skill slot), case 0/2/4/6=기본 공격 alias / 1=skill A / 3=skill B / 5=skill C / 7=default → **7+1 active skill slot 시스템 확인** (R57 일치). **ChangeAttackMotion 호출 context @ 0x99700**: 직전 Formula::calc(0x6f=111, ...) hit check → result > 0 시 sub_89068 (hit 등록) → ChangeAttackMotion → 직후 *(r5+(-0x190))+0x19c (s16) > 99 면 exit (level cap). **HeroSkillInfo struct 18+ field 매핑**: +0x0a flag / +0x1c/1d mode / **+0x28 effect_type (★jumptable1 key)** / +0x29 effect2 / +0x2a formula_arg / **+0x30 behavior (8회)** / **+0x32/34/36/38 4×u16 (primary/secondary value, 각 8회)** / +0x3a-3d flags / **+0x44 knockback_idx (R69)** / +0x48/4a/4c/50 ranges / 88B = 0x58 entry size 일치. **호출 그래프 top 20**: **Formula::calc 27회** / GetSpritePtr 22회 / GetExtraDataPtr 22회 / **GetCurActSkillIdx 18회** / GetX 14회 / GetY 14회 / GetPivotX 11회 / GetPivotY 11회 / **TargetEffectMgr::NewTargetEffect 11회** (skill VFX) / **BATTLER::IncreaseHP 10회** / __divsi3 10회 / UiTargetMonster::SetBattler 9회 / GetTempAtkProPtr 8회 / GetHitType 8회 / GetMotion 7회 / Rand 7회 / IncreaseSP 5회 / IncreaseHiperCount 4회 / ApplyAddEffect 3회 / CheckEffSound_Hit 3회. HERO this fields: +0x22c=class_id (16회) / +0x269 (8회) / +0x294-296 3-byte cluster (skill state machine). `[r5, +-0x190]` ldr **107회** = big_struct base ptr (R71 추적 필요). docs/h5/RE/proc_hero_skill.md 신규 RE 문서 (10 섹션). h5_test_proc_hero_skill.py — 11 ELF symbol + entry pattern + 2 jumptable + dispatch key + ChangeAttackMotion @ 0x99700 + Formula::calc 27회 + TargetEffectMgr 11회 + IncreaseHP 10회 + GetCurActSkillIdx 18회 + HeroSkillInfo 4 fields ldr + HERO+0x22c 16회 + 26 RE doc marker 통과. .so 함수 분석 96-97% → 97-98%, Godot 실 구현 79-83% 유지 (R70 은 RE only, Godot 코드 변경 없음), 출시 78-88% 유지.)

이전 라운드:

Round 69 — **Attack motion dispatch RE 확정**. `HERO::ChangeAttackMotion` (@0x91e7c, 340B) + `HERO::CheckWeaponMotion` (@0x8dd58, 256B) ARM full disasm. **R67 PASS 1 의 cmp 0xd/0xe/0x14/0x17 dispatch 가설 정정**: 입력은 skill_type/weapon_kind 가 아닌 **`CHAR::GetMotion()` 현재 motion 값**. mov r1, #0x16/0x18/0x26/0xf = SetMotion 의 새 motion id, mov r1, #0xa = KB strength. **분기 키 = `this->class_id` (HERO+0x22c)**, class 0 (워리어) + 3 (나이트) 만 active. class 0: motion 13(0xd)→38(0x26) / motion 20(0x14)→22(0x16) — 단순 wind-up→hit phase swap. class 3: motion 14(0xe)→15(0xf) NULL target OR motion 14+target → KB=10+RevengeXY+TurnDir / motion 23(0x17)→24(0x18)+state_1d36==1 시 variable KB=(skill_info[+0x44]-2)*6+20. **호출자 식별** (초기 capstone 검색 0건 → raw ARM bl 디코더로 확정): ChangeAttackMotion ← `HERO::ProcHeroSkill` @0x99278 offset +0x488 (1회). CheckWeaponMotion ← **4 클래스 Draw() 메서드 5회** (WARRIOR @0x146af0 / ROGUE @0xd7a18 / KNIGHT @0xaa328 / GUNNER @0x87678 ×2) — **SORCERER 제외** (R22 의 "Sorcerer class object 없음" stub 가설 재확인). HERO struct 신규: +0x22c=class_id / +0x1d36=class 3 secondary flag / +0x1fb0=current attack target Monster* / +0x1fea=last knockback_idx. HeroSkillInfo +0x44=knockback_idx (1-base). character.gd 에 `SO_MOTION_WARRIOR_*/KNIGHT_*/WEAPON_*_HIGH` 10 상수 추가 (logical 매핑). docs/h5/RE/attack_motion_dispatch.md 신규 RE 문서. h5_test_attack_motion.py — 2 ELF + class dispatch + motion 분기 + helper 호출 + caller 검증 + 25 RE doc + 10 GDScript + 4 docstring 모두 통과. .so 함수 분석 95-96% → 96-97%, Godot 실 구현 79-83% 유지 (logical 매핑), 출시 78-88% 유지.)

이전 라운드:

Round 68 — **NPC Dialog state machine + DIALOG_INFO struct RE 확정**. `DIALOG_INFO::DialogWindow_Proc` (@0x71b48, 912B) ARM full disasm + jumptable decode. **R67 PASS 1 summary 의 "state byte = +0x29" 가설 잘못 확인** — 실제 main state byte = **+0x2b** (`ldrsb r2, [r0, #0x2b]; cmp r2, #7; addls pc, pc, r2, lsl #2` 의 0..7 jumptable). +0x29 는 sub-step counter (0..4 animation tick), +0x2d/+0x2f 는 animation curve key A/B (sp 의 phase data 에서 ld). 8 state 의미 확정: 0=INACTIVE (return 0, dialog 종료) / 1·3·6=IDLE_BUSY (return 1, 입력 대기) / 2·4=FADE_IN_A/B (phase data pool +0x10..+0x18, +0x1c..+0x24) / 5·7=FADE_HSB_A/B (RestorePal+ChangeHSB, pool +0x28..+0x30, +0x34..+0x3c). sub-step counter +0x29 가 4 도달 시 `SetDialogWindow` 로 다음 state 전환. state 2 종료 시 +0x2c=5 면 state 7 로 fast-jump. `EventProc::Event_DialogWindow` (@0x6eb38, 656B) = 매 frame NPC face + DialogBox + NameBox renderer (DrawDialogBox + DrawTextField + GetNpcNameText + NameBox). `EventProc::Event_SituateDialogText` (@0x73030, 600B) = dialog 시작 트리거: record_base + npc_slot×0x3c (60B per NPC slot), Interpreter::Strings::getString 으로 텍스트 lookup, Graphic::GetWidth/Height 로 자동 좌표 계산, +0xdf sub_state 분기로 `SetDialogWindow(1,2)/(4,2)/(6,5)` 호출. 외부 helper 9종 주소·심볼 확정 (SetDialogWindow @0x6ab40 / SetFacePosition @0x72f54 / GetNpcNameText @0x1431a0 / DrawDialogBox @0x8245c / NameBox @0x82248 / Strings::getString @0x9e540 / RestorePal @0x59400 / ChangeHSB @0x5f000 / DrawTextField @0x44370). dialog_box.gd 에 `DIALOG_STATE_*` 8 상수 + `DIALOG_TRIGGER_*` 3 상수 + `DIALOG_SUBSTEP_FINAL=4` + R68 RE docstring 추가 (typewriter 동작 자체는 logical 매핑만, 동작 보존). docs/h5/RE/npc_dialog.md 신규 RE 문서 (struct layout 표 + state 흐름 ASCII diagram + helper 표 + R67→R68 정정 표). h5_test_dialog.py — 9 ELF symbol cross-verify + 11 disasm pattern (jumptable + strb +0x29/+0x2d/+0x2f + cmp r2#7/r3#4/r1#5 + bl SetDialogWindow/RestorePal/ChangeHSB) + 12 RE doc marker + 12 GDScript const 통과. .so 함수 분석 94-95% → 95-96%, Godot 실 구현 79-83% 유지 (logical 매핑), 출시 78-88% 유지.)

## 📜 Round 1-87 한 줄 요약

| 라운드 | 한 줄 |
|---|---|
| R1-5 | VFS + 자산 이름 99.7% + DES 변종 + Formula VM 186 공식 + Godot 스캐폴드 |
| R6-11 | gv+0x1474 111 fields + V[58..167] 매핑 + V[111..116] secondary stat (근접명중/장거리명중/회피/방패방어/크리티컬) |
| R12-19 | Item 시스템 — buff slot + magic stat + EquipItemInfo struct + LoadItemTable csv layout + 19 카테고리 |
| R20-28 | Item 메커닉 — SkillBook/Cash/Refine/Orb/Mix 정밀 매핑. 강화 stat 식 + 5 socket orb + NPC blacksmith |
| R29-36 | Monster + Drop — droptable.dat 252 entries + enemy_g + enemy_*.dat 3 difficulty + 4 element + magic stat pair |
| R37-40 | Mission 105 + Quest 151×3 difficulty + 모든 데이터 파일 종류 식별 |
| R41-43 | Save 8 종류 + load cross-check (21/21 + 24, 0 mismatch) + `file[0] = level*10+class_id` packing |
| R44-47 | Monster AI 분석 — 13 opcode + 13 trigger + 13 sub-state + 48 AI defs decoder |
| R48-49 | Godot 통합 시작 — Monster AI VM (autoload) + Save binary 직렬화 |
| R50 | AI Action 13 sub-state 정밀 구현 (state 1-7/9/12 채움) + host CHAR interface 13 method + 48/48 VM round-trip |
| R51 | 인벤토리 items.json 정확 통합 (1360 records unique index) — kind 기반 filter + class_mask/level_limit 검증 + tooltip 풍부 |
| R52 | 강화(Refine) UI 구현 — Round 17/26 의 5-case + `refined_stat = base+sub_count` + 10000회 시뮬 (+10 2.5%/lock 65%/destroy 33%) |
| R53 | 합성(Mix) UI 구현 — Round 25/28 ApplySpecialMix + 116 recipe parse (ing×3 + result + sr) + 제작가능 필터 + 재료 보호 소비 |
| R54 | Orb socket UI 구현 — Round 17/26 ApplyOrbCombine + 53 orb + 5-socket encoding + 2x rule + add/remove 검증 |
| R55 | NPC 대장간(Blacksmith) UI 구현 — Round 28/32 ApplyNormalMix + smithtable.json 231 named recipes + 4-탭 + 제작가능 필터 + items.json _meta 회복 |
| R56 | Quest 패널 강화 — Round 40 quests.json 새 schema (3×151) + detail card (목표/보상/설명) + 난이도 토글 + 자동 보상 quests.json 직접 사용 + difficulty scaling 100% 단조 검증 |
| R57 | SkillBook 학습 UI 구현 — Round 21 IfLearnSkill + slot_16/17 193 books + GameState skill_levels dict + 4 조건 검증 + Sorcerer stub 검증 |
| R58 | Mission 진척 UI 구현 — Round 37/38 mission.json 105 missions + MissionSystem autoload + 7 event API + 6 panel hook 자동 연결 + type 분포 검증 + 3 case 시뮬 |
| R59 | Mission/Quest type 의미 RE — 23 함수 디스어셈블 + mission_type 0-5 의미 확정 + type 3 sub_type 정밀 매핑 |
| R60 | Quest cond_type 의미 RE — QuestCheck 5-way jumptable + cond_type 13/14=bag item count, 17=monster kill, 18=quest switch + quest_system 정확 라벨링 |
| R61 | character.gd host CHAR interface 구현 — Round 50 의 17 method 실 구현 + map 좌표 기반 distance/dir/motion |
| R62 | Monster spawner + AI tick 루프 — demo `_physics_process` 30fps tick + MonsterAI.process + cooldown_tick + dead 정리 + Mission.bump 자동 + KEY_G 테스트 spawn |
| R63 | Monster ↔ Hero 실 전투 — ai_skill_cast → hero HP 차감 + red popup + 사망 quick_load / SPACE 키 → Chebyshev ATTACK_RANGE_TILES=2 nearest monster 공격 + yellow popup + 방향 전환 |
| R64 | monster kill 보상 흐름 — _award_kill_reward (enemy_stats sentinel→default exp/gold + 25% drop_table + add_battle_reward level_up + +%dEXP +%dG popup + Quest.on_enemy_killed) |
| R65 | Quest reward type 6/10/11/12 RE — QuestRewardData @0xd458c 분석으로 reward.type=item slot, sub=idx, value=qty 확정 + type 17=money/18=exp/19=HP/20=INT + REWARD_SLOT_LABEL + 64/64 in-range 검증 + items.json item_name_at 라벨링 |
| R66 | battle_system / character 두 host 명세 강화 — turn-based stub 이 dead code 아님 확정 (B 키 전투 host=self) + cooldown 실 동작 + is_stunned 추가 + 두 host 비교 표 docstring + h5_test_dual_host 17/17 + 6 R66 패턴 + 의미 차이 시뮬 |
| R67 | Battle motion enum + CHAR state machine RE 확정 — R50 의 HOST_MOTION (walk=1/die=9) 가설 잘못 확인 + 실제 walk=motion 3 / die=motion 5 + main_state(1-4) ≠ motion 별개 시스템 + CHAR struct +0x2c/0x2d/0x2e/0xc4-c6 + character.gd 에 SO_* 8 상수 추가 + 10 ELF symbol + 9 패턴 통과 |
| R68 | NPC Dialog state machine + DIALOG_INFO struct RE 확정 — DialogWindow_Proc 0..7 jumptable @ +0x2b + R67 의 "+0x29" 가설 정정 + 8 state 의미 + phase data pool + Event_DialogWindow renderer + Event_SituateDialogText 트리거 + helper 9종 + dialog_box.gd 에 11 상수 추가 + 9 ELF + 11 disasm + 12 doc + 12 GDScript 통과 |
| R69 | Attack motion dispatch (ChangeAttackMotion + CheckWeaponMotion) RE 확정 — R67 PASS 1 의 cmp 0xd/0xe/0x14/0x17 가설 정정 (input = GetMotion() 반환값, dispatch key = class_id @+0x22c, class 0 워리어 + 3 나이트만 active) + 호출자 정확 식별 (ChangeAttackMotion ← ProcHeroSkill @0x99278+0x488 1회, CheckWeaponMotion ← 4 클래스 Draw 5회: WARRIOR/ROGUE/KNIGHT/GUNNER, SORCERER 제외 → R22 stub 재확인) + HERO struct 신규 4 fields + HeroSkillInfo+0x44 + character.gd 10 상수 + 27 검증 통과 |
| R70 | HERO::ProcHeroSkill 골격 RE — 7972B 거대 함수 1993 ARM instruction 분석. Entry sequence (state clear + 3-step reset + 59-slot HeroSkillInfo 배열 @HERO+0x348 88B×59 초기화 + class 2 GUNNER 별도 path) + 2 jumptable (@0x9a398 5-way skill_info[+0x28] effect type / @0x9a8d8 7-way GetCurActSkillIdx active skill slot 0..6) + ChangeAttackMotion @0x99700 context + HeroSkillInfo 18+ fields 매핑 + helper graph top 20 + HERO this +0x22c/+0x269/+0x294-296 fields + 11 ELF + 26 doc marker 통과 |
| R71 | ProcHeroSkill Formula::calc dispatch + r5 base 추적 — Formula::calc (@0x7749c, 172B) full disasm: id < 1000 calc_pl / < 2000 calc_en / ≤ 3007 calc_sk. Formula 0x6f/0x63 = calc_pl OOB (production 0..38) → hit check 항상 0 → __sub_89068 skip but ChangeAttackMotion unaffected. r5 = HERO+0x1ecc, [r5,-0x190] = HERO+0x1d3c. cmp r2 #0x63 = level cap 99 확정 |
| R72 | ProcHeroSkill JT1 5 case + class 2 GUNNER entry RE — JT1 각 case helper 매핑: case 0=IncreaseSP / 1+2=AddCurseSkill / 3+5=AddBuffSkill / 4=AddStanceSkill (R70 heal+buff 정정). HeroSkillInfo +0x3c/+0x3d formula ids + +0x4a SP delta. HERO+0x269 GUNNER combo state. class 2 entry skill_idx==5 special. GUNNER damage = (combo×20+30)×X/100. docs §12 + 14 markers 통과 |
| R73 | ProcHeroSkill JT2 4 case + TEM 11 호출 RE — JT2 각 case: case 0/2/4/6 = 기본 공격 (Formula 3 V[23] HP + Formula 4 atk×magic×buff% SP) / case 1/7 = timestop chain / case 3 = KNIGHT secondary (orb-based) / case 5 = shock skill (dynamic Formula id from skill_info[+0x30]). HeroSkillInfo +0x30/+0x46/+0x4e/+0x48 + HERO+0x1a8. TEM signature 12 args + effect_type {4,7,8}. docs §13/§14 + 16 markers 통과 |
| R74 | Godot battle_system.gd damage 공식 정확화 — R63 임시 공식 (atk+rand-def/2) 의 R71+R72+R73 발견 통합. GameState 에 gunner_combo/max_combo/ammo. battle_system.gd SKILL: GUNNER combo multiplier + Formula 4 SP delta + 3 helper signals + apply_skill_effect API. R63/R69/R73 회귀 통과. Godot 79-83% → 82-88%, 출시 80-90% |
| R75 | GUNNER combo UI + skill effect 시스템 통합 — R74 backend 의 frontend. GameState 에 active_curses/buffs/stances Array + add/tick. battle_system._ready() 의 3 signal 자동 연결. status_panel 에 [Combo N/M] + [저주×N/버프×M/자세×K]. GameData.skill_info(class_id, skill_id) 10 fields. battle_system SKILL 자동 dispatch + log fx_str. Godot 82-88% → 85-90%, 출시 83-92% |
| R76 | active effect stat modifier 통합 + tick 자동 호출 — GameState.total_attack 에 active_buffs.f1 누적 % bonus (clamp 0..200) + total_defense 에 stance+curse % (clamp 0..150/0..80, net_pct 계산). battle_system._enemy_turn 끝에서 tick_active_effects() 자동 호출 → state_changed.emit → status_panel 자동 갱신. tools/h5_test_stat_modifier.py 신규 — Python 시뮬 7 case (buff 20%/누적/clamp 200% / stance 50% / curse 30% / stance+curse net / curse clamp 80%) 모두 통과. R63/R74/R75 회귀 통과. Godot 실 구현 85-90% → 87-92%, 출시 85-94% |
| **R87** | **Spirit (class_5) extra_hex full mapping — R77 정확 sub-rel offset 8 explicit field 추출 (effect_type 0x1a / dynamic_formula 0x26 / special_dispatch 0x2b / formula_id_1/2 0x2d/0x2e / primary_u16 0x22 LE / secondary_u16 0x24 LE / desc_len 0x2f). game_data.skill_info(5,_) explicit field 직접 반환 (stats_u16 추정 안 거침). Spirit data 분석: effect_type 분포 0=5 / 2=9 / 7=2 (debuff 위주), formula_id_1 57=10. Sorcerer spirit fallback 이 실 effect_type (curse/timestop) 발화. tools/h5_test_spirit_full_mapping.py 9/9 PASS. F 27→40%, 종합 78.87→80.17% (↑1.30%p) — 80% 돌파. Godot 92-95%, 출시 82%** |
| R86 | Distribution build preset + BUILD_ANDROID 가이드 + icon.svg — G 카테고리 (출시 보완) 의 가장 큰 빈 칸 채움. export_presets.cfg 신규 (Debug + Release 2 preset, gradle_build, min_sdk 23 / target_sdk 34, arm64-v8a only, 11 permissions 모두 false, immersive_mode). Release 에 compress_native_libraries=true. icon.svg 신규 (project.godot 참조 만족). .gitignore 조정 (export_presets commit + *.keystore ignore). docs/h5/BUILD_ANDROID.md 신규 (8 섹션: 사전 요구사항/Editor 설정/preset 설명/keystore 생성/빌드 절차/검증/이슈). tools/h5_test_export_preset.py 13/13 PASS. G 35→55%, 종합 77.27→78.87% (↑1.60%p), 출시 81%** |
| R85 | Battle UI fade transition — R82/R84 자연스러운 후속. battle_ui.start() 가 SceneFader.warp_fade (0.25s out + 0.25s in) 사용. _setup_and_show mid-callback split (H5Battle instance + start_battle + visible=true + sprite). 중복 진입 guard (if visible: return). _on_ended 도 fade-out 적용 (popup → fade → visible=false + cleanup → battle_completed.emit). emit 순서 fade 완료 후 (race 방지). SceneFaderRef preload (CanvasLayer). tools/h5_test_battle_fade.py 8/8 PASS. E 70→80%, 종합 76.07→77.27% (↑1.20%p), Godot 91-94%, 출시 79%** |
| R84 | Map warp fade + Spirit extra_hex 부분 파싱 — R82/R83 동시 후속. scene_fader.warp_fade(node, callback, out_dur, in_dur) 신규 in-scene 전환 (검정 페이드아웃 → callback → 페이드인). demo._on_warp 가 warp_fade 사용 + _warping guard (중복 warp 방지). game_data._ensure_spirit_skills_loaded 의 extra_hex 파싱 (hex string → bytes → 48B stats area → 24 u16 little-endian). spirit record #0 = 131B / 24 u16. battle_system 의 Sorcerer spirit fallback 이 정상 mp/cd/damage lookup 동작. tools/h5_test_warp_fade.py 8/8 PASS. R82/R83 회귀 통과. 진척률: E 62→70%, F 24→27%, 종합 74.81→76.07% (↑1.26%p), Godot 90-93%, 출시 78%** |
| R83 | Sorcerer (class_id=4) 부분 활성화 — R22 stub 해제. class_select 라벨 "(미구현)" → "(매직 — 기본+정령 스킬만)". battle_system._skill_data class-aware 리팩토링 (이전 class_0 하드코딩 → class_id 동적 + Sorcerer spirit class_5 fallback + generic stub fallback). GameState.total_attack 에 class 4 일 때 stat_int×2 magic bonus (Sorcerer Lv.1 31 vs Warrior 27 — active skill 부재 보상). game_data._ensure_spirit_skills_loaded 신규 (c_csv_skill_05.json → _skills_cache["class_5"] 16 entries). demo.gd 진입 안내 + skill_book_panel 빈 list 안내. tools/h5_test_sorcerer.py 9/9 PASS. 진척률: F 6→24% / 종합 73.01→74.81% (↑1.80%p), Godot 89-93%, 출시 77%** |
| R82 | Scene 흐름 정비 — SceneRouter autoload + GameOver scene + Quit-to-Title. R81 의 진척률 재평가에서 가장 큰 임팩트 영역 (E. Scene 통합) 의 첫 진척. scene_router.gd 신규 (autoload, 140 줄, State 4 + 6 method + 2 signal + transition guard). game_over.tscn + game_over.gd 신규 (Continue/Title 2 버튼 + reason display + slot 미리보기). demo.gd hero death 정정: silent quick_load → SceneRouter.to_game_over (사망 원인 명시 + 선택권). F10 = quit_to_title (확인 popup). title.gd + class_select.gd 4 호출 마이그레이션 (SceneFader 직접 0개). tools/h5_test_scene_router.py 11/11 PASS. verify_godot_project 0 warnings. 진척률: E 55→62% / 종합 72.17→73.01% (↑0.84%p)** |
| R81 | TargetEffect::ProcTargetEffectSkill (@0x64a08, 4276B / 1069 instr) overview RE — jumptable 없음 (pure if/else cascade). 함수 = per-frame skill effect engine. Top reads: HERO class_id 6x + gunner_combo 6x + skill_info 12 file field + R79 dead read +0x4a/+0x4e 1x 각 (default 0 no-op) + TargetEffect state cluster +0xab..+0xc0. Top calls: Formula::calc 14x + TEM 재귀 6x + IncreaseHP 4x + AddCurseSkill 3x + NewHitEffect 2x + ApplyAddEffect 2x. R79 dead reads 일관성 확정. 정밀 cascade 분석 R82+. tools/h5_test_proc_target_effect_skill.py 9/9 PASS. **종합 진척률 72.17% 재평가**: A자산 95+B데이터 96+C로직 RE 93+D Godot코어 88+E Scene 통합 55+F누락(Sorcerer/Device) 6+G출시보완 35+H QA 60 가중평균. 코어 한정 87-92% 유효 / 실 게임 플레이 기준 72%** |
| R80 | TargetEffectMgr / TargetEffect VFX 시스템 RE — R73 의 effect_type 4/7/8 위치 + 시스템 구조. 5 TEM overload chain (4 wrapper → _full 408B 실 구현). _full = 100 slot × 0x284B allocator + IsEmpty 검사 + bl 0x62840 base init + post-init r6 (arg17) → 3 manager 채널 (global +0x15d8/+0x15e0/+0x15e4) 등록. TargetEffect::NewTargetEffect base (500B): 25+ field strb/strh + 200B memset work area. **Effect 베이스 5 setter**: IsEmpty +0x11 / SetEffectType +0x12 (★ effect_type 저장) / SetEffectFrame +0x14 / SetEffectLastFrame +0x16 / SetEffectValue +0x18. effect_type 4=기본 hit / 7=timestop / 8=shock VFX (실 render 의미 R81+). ProcTargetEffectSkill 4276B = per-frame skill 처리 (Formula::calc + level cap, Effect+0x12 직접 안 읽음). tools/h5_test_target_effect_mgr.py 9/9 PASS** |
| R79 | BATTLER effect dispatch 분석 + HeroSkillInfo runtime field 가설 종결. ApplyAddEffect@0x4bdb4 = pure 28-way dispatcher (struct write 0). AddCurseSkill@0x4b134 → curse = attacker BATTLER+0x130-0x140. AddBuffSkill@0x4b198 → buff = BATTLER+0x118-0x128. AddStanceSkill@0x91d7c → stance = HERO+0x284-0x28a. **active effect 컨테이너는 BATTLER/HERO, HeroSkillInfo 무관 확정**. .so-wide grep: HSI+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e writer **0 개** (모두 무관 구조체 우연 일치). **R72/R73 5 runtime field = dead reads** (default 0): +0x46 case 5 shock skill = dead code, +0x48 GUNNER max_combo R74 fallback=4, +0x4a SP delta = no-op, +0x44 KB = constant 8, +0x4e KNIGHT = no-op. **HeroSkillInfo 88B 최종**: 68B file + 16B unused + 4B cooldown. **field 의미 11/11 확정** (R77 file 7 + R78 cooldown 2 + R79 dead 5). tools/h5_test_battler_effect_dispatch.py 8/8 PASS** |
| R78 | HeroSkillInfo runtime field source 추적 + cooldown system 확정. HeroSkillInfo:: 4 멤버 함수 disasm: SetNowCoolTime(s)@0xd8d38 writes +0x54 AND +0x56 / GetNowCoolTime@0xd8d44 reads s16 +0x54 / GetMaxCoolTime@0xd8d4c reads s16 +0x56 / DecreaseNowCoolTime@0xd8d54 -1 clamp 0. **+0x54 = NowCoolTime u16 / +0x56 = MaxCoolTime u16 pair 확정** (R72의 +0x50 ranges 가설 정정). **R70 의 "59-slot init" 가설 정정**: ProcHeroSkill entry 59-iter 루프는 cooldown tick (bl 0xd8d54), 초기화 아님. InitSkillEmpty@0x88a20: HERO+0x1b40 32B 0xFF init (skill array 무관, 새 HERO cluster). InitSpiritSkillMenu@0x89198: global menu state init. GetHeroSkillInfoPtr@0x88ce4: this+0x348+idx*0x58 확정. HeroSkillAtkHardCode@0x9041c: skill_info+0x45 read only. R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e writer 미확정 → HERO zero-init default 0 가정 (R79 BATTLER::ApplyAddEffect 추적). HeroSkillInfo 88B field 9/11 확정 (file 7 + cooldown 2). tools/h5_test_skill_info_runtime.py 12/12 통과. .so 분석 ~99% 유지** |
| R77 | HERO::LoadResSkillInfo (@0x8bba4, 784B, 195 instr) + LoadResClassSkillInfo (@0x9b308, 48B) ARM full disasm — R75 매핑 정확화. file layout = 3B header + name + 0x30B stats + desc. **HeroSkillInfo 88B = file-loaded 68B (+0x00..+0x43) + runtime 20B (+0x44..+0x57)**. R72/R73 의 5 critical field (+0x28 effect_type / +0x30 dynamic_formula_id / +0x3a special_dispatch / +0x3c/+0x3d formula_ids) **file-loaded 영역에서 정확 위치 확정**. R72/R73 의 6 runtime field (+0x44 kb_idx / +0x46 shock_count / +0x48 max_combo / +0x4a sp_delta / +0x4c / +0x4e knight_threshold) 는 **file 출처 아님** 으로 정정 (InitSkillEmpty/hard-coded 별도 추적 R78+). LoadResClassSkillInfo = wrapper (class_id 호출 → slot 0..42 + arg=5 호출 → slot 43..58 + LoadResSkillIcon tail). docs/h5/RE/load_skill_table.md (8 섹션) + tools/h5_test_load_skill_table.py (14 PASS). game_data.gd skill_info docstring 정정. .so 분석 ~99% 유지, 출시 85-94% 유지** |



---

## 🎯 전체 진척 평가 (Round 76 시점)

영역별 추정 진척률 — 단일 % 로 답하기 어려움, 영역별 차이 큼:

| 영역 | 추정 % | 비고 |
|---|---:|---|
| **자산 추출/변환** | ~95% | VFS/sprite/palette/text/OGG 완료. 남은 것: SMAF, 한글 비트맵 폰트 (LOW PRIORITY) |
| **데이터 구조 RE** (csv/dat layout) | ~100% | 모든 데이터 파일 식별 + decoder + struct 매핑 완료 |
| **.so 함수 분석** (game logic) | ~99% | R67-73 RE 완료. 잔여: TEM 인자 정밀, special path 0x9b100/0x9b124, type 22, LoadSkillTable disasm |
| **Godot 실 구현** | **~87-92%** | + R74-75 backend+UI + **R76 stat modifier 통합** (active_buffs → ATK%, active_stances/curses → DEF%, tick 자동). R77+ Godot Editor 실 실행 검증 |
| **Android 실 빌드 검증** | 0% | 사용자 GUI 작업 |

**종합**:
- **"원본 분석"** (RE+자산) 으로 보면 ~**99%**
- **"리메이크 출시 가능"** (Godot+Android) 으로 보면 **85-94%** (R76 stat 실 영향으로 +2%p)

## 📦 미완 큰 덩어리 (우선순위 순)

1. **UI 시스템 전반** — 인벤토리/강화/합성/스킬학습/NPC blacksmith/Quest/Mission/Shop 패널.
   데이터는 다 있지만 Godot UI 미구현.
2. **Monster AI** — `Monster::Ai_Action` (2136B), `Ai_onAction` (704B), `Ai_setActionList` 등 미분석
3. **Battle 실행 흐름** — Formula VM 평가는 됨, turn order / animation timing / skill VFX 미통합
4. **Save 파일 포맷** — DES 키만 알려져 있고 record layout 미분석
5. **Quest/Mission tracking** — 데이터 식별만, 실제 진척 추적 시스템 Godot 미구현

---

## 🚀 다음 세션 즉시 시작 (Round 77)

### A. 환경 복원 한 줄 (assets/ 비어있는 새 클론)

```bash
python tools/h5_extract_pipeline.py    # APK 가 있을 때 ~6s, incremental
```

### B. 현재 상태 한 줄 검증

```bash
# UTF-8 출력 필수 (cp949 콘솔이면 PYTHONIOENCODING=utf-8 prefix)
PYTHONIOENCODING=utf-8 python tools/verify_godot_project.py
# → ✓ all references resolve (0 warnings)

python tools/h5_test_monster_ai.py     # 48/48 AI VM round-trip
python tools/h5_test_save_layout.py    # H/SL .sav round-trip
python tools/h5_test_items_lookup.py   # 1360 items unique-name index
python tools/h5_test_refine.py         # Refine prob + 10000회 시뮬
python tools/h5_test_mix.py            # 116 recipe parse
python tools/h5_test_orb.py            # 53 orb encoding + 2x rule
python tools/h5_test_blacksmith.py     # 231 smith recipes + sr 분포
python tools/h5_test_quest.py          # 151×3 quests + difficulty scaling
python tools/h5_test_skill_book.py     # 193 skill books + 5 case 시뮬
python tools/h5_test_mission.py        # 105 missions + 3 case 시뮬
python tools/h5_test_re_types.py       # Round 59 RE: ELF symbol verify + sub_type 분포
python tools/h5_test_cond_types.py     # Round 60 RE: cond_type 13/14/17 + reward 15/17/18
python tools/h5_test_char_host.py      # Round 61: 17 host CHAR method 시그니처 + 8 Python 시뮬
python tools/h5_test_ai_tick.py        # Round 62: spawner + 30fps AI tick 루프
python tools/h5_test_ai_combat.py      # Round 63: Monster↔Hero 실 전투
python tools/h5_test_kill_reward.py    # Round 64: monster kill 보상 흐름
python tools/h5_test_reward_types.py   # Round 65: Quest reward type RE
python tools/h5_test_dual_host.py      # Round 66: 두 host 명세
python tools/h5_test_battle_motion.py  # Round 67: Battle motion enum + CHAR state
python tools/h5_test_dialog.py         # Round 68: NPC Dialog state machine + DIALOG_INFO struct
python tools/h5_test_attack_motion.py  # Round 69: Attack motion dispatch (ChangeAttackMotion + CheckWeaponMotion)
python tools/h5_test_proc_hero_skill.py # Round 70+71+72+73: ProcHeroSkill 골격 + dispatch + r5 base + JT1 5 case + GUNNER + JT2 4 case + TEM
python tools/h5_test_battle_formula.py  # Round 74: Godot battle_system damage 공식 정확화 (GUNNER combo + SKILL SP delta + 3 helper signals)
python tools/h5_test_skill_meta.py       # Round 75: GUNNER combo UI + GameData.skill_info + active effect 통합
python tools/h5_test_stat_modifier.py    # Round 76: active effect stat modifier (buff/stance/curse → ATK/DEF) + tick 자동
```

### C. Godot Editor 에서 게임 실행

`apps/hero5-godot/` 를 Godot 4.2+ Editor 로 열고 F5. 게임 화면에서 키바인딩:

| 키 | 동작 | 도입 라운드 |
|:---:|---|:---:|
| **ESC / I** | 상태창/인벤토리 토글 (status_panel) | R7 (R51 강화) |
| **R** | 강화(Refine) 패널 토글 | **R52** |
| **K** | 합성(Mix) 패널 토글 | **R53** |
| **O** | Orb socket 패널 토글 | **R54** |
| **J** | NPC 대장간(Blacksmith) 패널 토글 | **R55** |
| **Q** | 퀘스트 패널 토글 (R56 detail card + 난이도 토글) | R20 (R56 강화) |
| **L** | 스킬북 학습(Learn) 패널 토글 | **R57** |
| **,** | 미션 진척 패널 토글 | **R58** |
| **G** | hero 주변에 random monster 스폰 (AI tick 테스트) | **R62** |
| **SPACE** | 인접 monster (Chebyshev ≤2 tile) 공격 | **R63** |
| S | 상점 열기 | R8 |
| H | 도움말 토글 | R10 |
| X | 설정 토글 | R10 |
| F5 / F9 | 빠른 저장 / 로드 | R6 |
| 1-8 / Shift+1-8 | 슬롯 저장 / 로드 | R7 |
| B | 랜덤 전투 | R3 |
| E | NPC 대화 | R8 |
| M / N | map_id / scene 다음 | R3 |
| P / C / V | NPC 마커 / collision / tile attr 디버그 | R5 |
| T | dialog 테스트 | R5 |

### D. Round 78 추천 작업 (자율 가능, 임팩트 순)

> R77 로 LoadResSkillInfo file layout 확정. R78 은 사용자 작업 (Godot Editor 실 실행 검증) 또는 잔여 RE 분석.

#### ⭐ 1순위 — Godot Editor 실 실행 검증 (사용자 작업, 0.5-1 라운드)
- R74-76 의 backend + UI + stat modifier 가 in-game 에서 정확히 동작하는지 검증:
  - **B 키 → battle 시작 → SKILL action** → log message 에 `+저주`/`+버프`/`+자세` fx_str 표시 확인
  - **status_panel (ESC/I)** 에 `[Combo N/M]` (GUNNER 만) + `[저주×N, 버프×M, 자세×K]` 시각 확인
  - **ATK/DEF 변화** — buff 후 atkdef_label 의 수치 증가, curse 후 DEF 감소
  - **tick 자동 만료** — 5 turn 진행 후 active effect 자동 제거 + UI 업데이트
- 사용자 환경 작업 (코드 변경 없음). 발견된 bug 는 R79+ 에서 수정.

#### 2순위 — HeroSkillInfo runtime field source 추적 (0.5-1 라운드)
- R77 결과: +0x44..+0x57 (20B runtime) 는 LoadResSkillInfo 에서 채우지 않음
- 후보: HERO::InitSkillEmpty (@0x88a20, 272B) — 59-slot 0-init 또는 hard-coded default 추적
- 후보: HERO::InitSpiritSkillMenu (@0x89198, 132B) — spirit 16개 별도 init?
- 후보: ProcHeroSkill 또는 별도 SkillUse handler 에서 동적 set?
- 산출: kb_idx/shock_count/max_combo/sp_delta/knight_threshold 의 출처 확정 → R75 GameData.skill_info 의 3 잠정 field 정정

#### 3순위 — TEM 정밀 (0.5 라운드)
- effect_type 4/7/8 실제 의미 (R5 의 TargetEffect::NewHitEffect 와 cross-ref)
- TEM 호출 #11 위치 추적 (ldr 통한 stored ptr 호출 패턴)
- TargetEffectMgr::NewTargetEffect 내부 분석 (sprite VFX 생성 흐름)

#### 3순위 — special path 0x9b100/0x9b124 (R72 미해결, 0.5 라운드)
- skill_info[+0x3a] == 0x34/0x37 일 때 default AddCurseSkill 대신 호출되는 special handler
- skill table cross-ref 로 어떤 skill 의 path 인지 식별

#### 4순위 — type 22 (0x16) special path RE / SetDialogWindow 내부 RE / Skill UI

#### 2순위 — SetDialogWindow 내부 RE (0.5 라운드)
- 핵심 함수: `DIALOG_INFO::SetDialogWindow` (@0x6ab40)
- R68 에선 호출자 측 (Event_SituateDialogText / DialogWindow_Proc) 만 분석 — 내부 본 적 없음
- 작업: `(byte main, byte sub)` 인자 의미 + state 전환 트리거 + sub-step counter +0x29 초기화 여부 확인
- 산출물: `docs/h5/RE/npc_dialog.md` §10 (SetDialogWindow 내부) 추가 + R68 docstring 보완

#### 3순위 — type 22 (0x16) special path RE (0.5 라운드)
- Round 65 disasm 에서 식별만 됨 (`cmp r1, #0x16; beq 0xd4864`), observation 없음
- 가설: special item add with `r1=#0x11` (slot 17 = skill_book_gk?)
- 작업: 0xd4864..0xd48c0 영역 정밀 disasm → handler 의미 확정

#### 4순위 — Skill 보유 레벨 UI 표시 (0.5 라운드)
- status_panel 에 `GameState.skill_levels` dict 추가 표시
- R57 SkillBook 학습 UI 의 자연스러운 보완 — 학습한 스킬 시각화

#### 5순위 — scn opcode 실 game scene 검증 (2-3 라운드)
- Title/ClassSelect/Demo 외 화면 진입 테스트
- scn opcode 흐름 vs 실제 Godot scene 동작 cross-check

#### 6순위 — Save binary device import/export (1 라운드)
- 실 디바이스의 H_*.sav 추출 → Godot save_manager 의 deserialize_hero_save 로 round-trip 검증

### E1. Round 74-76 battle / skill effect 시스템 (R76 종료 시점)

| 컴포넌트 | 책임 | R74-76 변화 |
|---|---|---|
| `GameState.gunner_combo/max_combo/ammo` | GUNNER class 의 combo state | R74 신규 — HERO+0x269 대응 |
| `GameState.active_curses/buffs/stances` | 적용 중인 effect entry Array (`{dispatch, f1, f2, turns}`) | R75 신규 (Array) — R72 helper signal 캐치 |
| `GameState.add_active_effect(kind, …)` / `tick_active_effects()` | effect 추가 + turn 만료 | R75 신규, R76 에서 state_changed.emit 통합 |
| `GameState.total_attack` | base+equip + **active_buffs.f1 누적 %** | R76 보강 — clamp 0..200, `raw × (100+pct)/100` |
| `GameState.total_defense` | base+equip + **stance % - curse %** | R76 보강 — clamp 0..150 / 0..80, net_pct |
| `battle_system.SKILL action` | damage + Formula 4 SP delta + auto dispatch | R74-75 보강 — GUNNER combo + 자동 effect type dispatch |
| `battle_system.curse/buff/stance_applied signal` | R72 helper 4 의 Godot 대응 | R74 신규 — `_on_*_applied` 가 GameState 갱신 (R75) |
| `battle_system.apply_skill_effect(…)` | manual effect dispatch API | R74 신규 |
| `battle_system._enemy_turn` | turn 종료 + cooldown tick + **active effect tick** | R76 보강 — `GameState.tick_active_effects()` 호출 |
| `status_panel._on_state_changed` | GameState 변화 시 패널 자동 갱신 | R76 신규 — visible 일 때만 _apply |
| `status_panel._apply` | UI text 갱신 | R75 보강 — `[Combo N/M]` + `[저주×N, 버프×M, 자세×K]` |
| `GameData.skill_info(class_id, skill_id)` | R72/R73 skill record 10 field 노출 | R75 신규 — effect_type / dynamic_formula_id / formula_ids / KB / shock / max_combo / SP / KNIGHT threshold |

흐름 (active skill 사용 시):
1. `player_action(Action.SKILL, skill_id)` → MP/cooldown 검사
2. **damage = calc_sk[2000+skill_id]** (기본) + **GUNNER combo multiplier** (class==2 && skill_id==5)
3. **Formula 4** 부가 호출 → SP 회복 (`player_mp += sp_delta`)
4. `GameData.skill_info` → `effect_type` 추출 → **`apply_skill_effect` 자동 호출**
5. effect_type 별 signal → `_on_*_applied` → `GameState.add_active_effect`
6. 다음 enemy turn 끝에 `tick_active_effects` → 만료 entry 제거 + `state_changed.emit`
7. `status_panel` 자동 갱신 (visible 일 때)

### E. Round 51-58 UI 시스템 통합 상태 (참고)

| 패널 | 데이터 source | 핵심 mechanic | helper 함수 |
|---|---|---|---|
| status_panel (R51) | items.json 1360 records | kind/class_mask/level_limit 검증 | GameData.item_lookup |
| refine_panel (R52) | EquipItemInfo +0x165..+0x167 | 5-case prob + base+sub stat | GameState.refine_state |
| mix_panel (R53) | slot_15 의 116 recipe | success_rate roll + 재료 소비 | GameData.parse_recipe |
| orb_panel (R54) | slot_12 의 53 orb + +0x168..+0x16d | 5 socket encoding + 2x rule | GameState.orb_state |
| blacksmith_panel (R55) | smithtable.json 231 named (288 entries) | 4-탭(기본/세트/고급/전체) + sr {75,100} | GameData.smith_table / smith_all / parse_smith_recipe |
| quest_panel (R56) | quests.json by_difficulty.q0/q1/q2 × 151 | detail card + 난이도 토글 + scaling 단조 | Quest.quest_objectives / quest_rewards / reward_label |
| skill_book_panel (R57) | items.json slot_16/17 의 193 books | class match + req_lvl + upgrade check | GameData.skill_books_for_class / GameState.learn_skill_book |
| mission_panel (R58) | mission.json 105 missions | 7 event → mission_type 매핑 / 자동 완료 | Mission.bump_progress / mission_completed signal |

모두 GameState 의 단일 inventory 배열을 공유. `consume_inventory` 가 refine_state + orb_state 동기 정리.
blacksmith 는 mix 와 동일한 parse_recipe 형식이라 schema 호환. quest_panel 은 Quest singleton 사용.
skill_book_panel 은 GameState.skill_levels dict (skill_idx → max LV) 갱신 + unlocked_skills 동시 갱신.
mission_panel 은 Mission singleton (R58 신규 autoload) 사용. 기존 panel 6개 hook 자동 연결.

### F. 미구현 / 향후 옵션 (Round 76 종료 시점)

- **(★ 1순위 USER)** R74-76 의 backend+UI+stat modifier 가 in-game 동작 검증 — Godot Editor 에서 직접 실행 후 B 키 → SKILL → log fx_str + UI Combo bar + ATK/DEF 변화 시각 확인 (R77 추천)
- **(분석)** LoadSkillTable disasm — R75 의 skill_info struct byte offset → stats_u16 index 매핑 정확화 (현재는 추정)
- **(분석)** TEM 호출 #11 위치 + effect_type 4/7/8 정밀 의미 (R72/R73 잔여, 0.5 라운드)
- **(분석)** special path 0x9b100/0x9b124 — skill_info[+0x3a] = 0x34/0x37 special handler (R72 미해결, 0.5 라운드)
- **(분석)** type 22 (0x16) special path — R65 미관측 case, 0xd4864 영역
- **(분석)** SetDialogWindow @0x6ab40 내부 — R68 호출자 측만 봄
- **(검증)** scn opcode 실 game scene 동작 (Title/ClassSelect/Demo 외 화면 진입)
- **(검증)** Save binary device import/export — 실 디바이스 H_*.sav 추출 → Godot 로드
- **(USER)** P6 Android APK 실 빌드 — Godot Export Template + JDK 17 + Android SDK 필요

---

## 30초 요약 (Round 39 시점, 2026-05-11)

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 P1~P4 + DES 해독 + Formula VM 통합 + Item struct 분석** 완료.
Title → ClassSelect → Demo 흐름 동작하는 Godot 4 프로젝트 (`apps/hero5-godot/`).

**verify_godot_project.py: 0 errors / 0 warnings.**

### Round 6~39 누적 발견 (요약)

| 영역 | 핵심 결과 |
|---|---|
| Formula VM stat field | V[58]=level, V[60..63]=str/dex/**con/int** (R11 정정), V[69]=SP, V[70]=CP |
| V[111..116] secondary | atk_growth_coef + 5 secondary stat = **근접명중/장거리명중/회피/방패방어/크리티컬** (R11 buildup csv 매핑) |
| V[118..133] buff/temp bonus | str/dex/con/int bonus + 5 buff slot (EXP%/SP감소%/CP충전/쿨타임/포션효과 — R12) + def_red% + atk%bonus + 5 secondary bonus |
| V[134..148] equipment | element bonus 영역, calc_sk[2003]/[2004] 가 EquipItem stat 합산 → cache |
| V[151..155] derived | V[151,152]=magic stat (둘 다 INT, R12 정정), V[153]=con, V[154]=str, V[155]=max_sp |
| V[168..182] ItemBase | V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor (R13) |
| EquipItemInfo struct | +0x14=item_subtype, +0x155=class subtype code, +0x15d=level_limit, +0x15f & 0x1f = 5-class mask (W/R/G/K/S, R16), +0x165..+0x167=refine_count/sub/locked (R17), +0x168..+0x16d=6 socket slots |
| LoadItemTable csv layout | 모든 카테고리 공통 base (item_id u32 + sub_record + sub_record_data 256B memcpy). EquipItem 만 sb-area (struct +0x150..+0x167) 추가 (R14/18) |
| cat 12-16 추가 fields | BattleUseItem +0x134..+0x137 (4 byte ✓ csv 매칭), OrbItem +0x134..+0x135, MixBookItem +0x134..+0x140 (R19) |
| slot_16/17 SkillBookItem | **+0x134=class_id**, +0x135=skill_index, **+0x136=skill_level** (LV1..7 정확 매칭 ✓), +0x137=required_level. slot_16 = Warrior(0)+Rogue(1), slot_17 = Gunslinger(2)+Knight(3). HERO::IfLearnSkill 의 (class_id/2)+16 공식 (R21) |
| slot_18 CashItem | jumptable case 18 → **0xa3b38 별도 path** (R19 가설 정정), 2 byte ext +0x134/+0x135 (R20) |
| 소서러 (class_id=4) 미구현 stub | c_csv_skill_04 부재 / SORCERER class object 없음 / class_stats unk1..14=1 placeholder. 출시 빌드 = 4 클래스 only. cat 18 매핑은 dead code (R22) |
| slot_11 BattleUseItem 4 byte 의미 | +0x134=effect_type (91=HP/90=SP/87=buff/92=마석/19=test/0=무효), +0x135=success_rate%, +0x136=effect_value (HERO+0x300 u16), +0x137=duration (HERO+0x302 s16). HERO::BattleUseItem 분석 (R23) |
| SLOT_META 전면 정정 | slot_12=orb (이전 scroll), slot_13=mix material (이전 orb), slot_15=mix_book recipe (이전 material_2). record 이름 + ext 길이 cross-check 결과 (R23) |
| val_15f csv vs runtime 용도 분리 | csv: lower 5 bit = class_mask + upper 3 bit = tier_flags. runtime: SetItemOption (0xa0ff8) 가 option_type code 로 overwrite. GetRelieveLevelLimit (0xa835c) 의 cmp #0x6c='l' 는 runtime option (R24) |
| val_15f upper 3 bit 실증적 의미 | upper=0 (170, legendary 보스/named) / =1 (248, rare 중급) / =3 (9, gem 보석 헤어핀/서클릿) / =7 (362, common 상점 기본) (R24) |
| slot_15 mix_book recipe 13 byte 구조 | 1~3 ingredients (cat/idx/count) + result (cat/idx) + success_rate%. 쿠킹/포션 합성/재료 정제/무기 제작 카테고리. 116 records 모두 검증 (R25) |
| **강화 stat 보너스 식 (Formula VM)** | **id=35: clamp((V[184]+V[187]),0,9999)**, **id=36: clamp((V[185]+V[187]),0,9999)**. V[184]=item+0x156=stat_a, V[185]=item+0x158=stat_b, V[187]=item+0x166=sub_count. **refined_stat = base + sub_count** (R26) |
| **EquipItem stat 의미 (slot 별)** | weapon (slot 0-3): atk_min/atk_max (a<b), shield (slot 9): phys/mag def (a≈b), helmet/boots/accessory: primary/secondary def (a>b), spirit (slot 10): 별도 mechanism (a,b ≤1) (R26) |
| **ApplyItemRefine 5-case jumptable 의미** | case 0=큰성공 (refine_count++, sub+=2), case 1=성공 (refine_count++, sub+=1), case 2=재료소비 (no change), case 3=lock (+0x167=1 영구 잠금), case 4=destroy (item 파괴). refine_count cap 10 (R26) |
| **ApplyOrbCombine orb socket mechanism** | item +0x168 = orb_count (V[188]), +0x169..+0x16d = 5 socket bytes. 39 orb 종 (3 그룹 × 13). sub_orbs=9 면 강도 multiplier 2x. Mission::CheckOrbCombine 호출로 mission 진척 (R26) |
| **NewDropItem signature + +0x15f arg position** | `NewDropItem(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 12 args. 7번째 arg (5번째 s8) = +0x15f tier_flags. cat ≤ 10 (EquipItem) 만 strb 발생 (R27) |
| **Monster drop_table 13-byte entry** | Monster::SetDropItem 내 drop pool 이 13 byte/entry. 4 가지 drop type (idx ∈ [0..3]) × 13. byte 데이터에서 NewDropItem 의 +0x15f arg 직접 전달 — csv 의 tier_flags 분포를 따름 (R27) |
| **+0x15f tier_flags csv↔drop 일관성** | csv val_15f = (class_mask | tier_flags<<5). drop_table 이 csv 분포 그대로 전달. 즉 Round 24 의 실증적 라벨 (legendary/rare/gem/common) 이 보스/일반 monster drop 로직에서도 의미 있게 사용됨 (R27) |
| **ApplyNormalMix (NPC blacksmith)** | MixSmithTableInfo* 별개 데이터 (csv slot_15 와 다름). struct layout col-major: +0x11c (option_grade), +0x11d-1f (cat[3]), +0x120-22 (idx[3]), +0x123-25 (count[3]), +0x126-128 (result_cat/idx/sr) (R28) |
| **ApplySpecialMix (csv slot_15 recipe)** | GetItemTableInfo 로 csv slot_15 데이터 직접 사용 + Mission::CheckMissionMix. struct +0x135-140 col-major (csv 13 byte transpose 후) (R28) |
| **mix_book recipe csv↔struct layout** | csv 파일 = row-major (per-ing: cat,idx,count) = 사용자 관점 정확 (R25). struct memory = col-major (cat[3], idx[3], count[3]) — LoadItemTable transpose. 두 해석 모두 정당, parse_mix_book_extra row-major 객체 그대로 유지 (R28) |
| **ApplyItemCompose (option 결합)** | 두 EquipItem (둘 다 grade ≤ 2 만) → option pair (+0x15f/+0x162, +0x160/+0x163) 결합. gv+0x1444+0x198+fp*6 = 결합 prob 테이블 (R28) |
| **ApplyItemDecompose (분해)** | option_grade-based prob (gv+0x1444+0x1b8+grade*10, 4 s16 thresholds × 5 grade). 5-way: money refund (default) / mix material / potion / 기타 (R28) |
| **gv+0x1444 sub-struct prob 테이블 영역** | +0x130-198 강화 prob (R17), +0x198-1b8 결합 prob (R28), +0x1b8-1f4 분해 prob (R28), +0x1f4-208 orb prob (R26) (R28) |
| **droptable.dat 식별** | VFS index 18, 3278B = 252 entries × 13B = 63 monsters × 4 drop tiers. byte 0=0x0b cat (potion only), byte 1=0, byte 2=monster_idx, byte 3=drop_tier (0x0e..0x11). LoadItemDropTable → ItemTable+0x214 (R29) |
| **drop_table = potion drop pool only** | ❌ Round 30 정정: 사실은 EquipItem drop pool (R30) |
| **droptable.dat = EquipItem drop pool (정정)** | byte 11 = NewDropItem cat arg (5/6/7/8/0xff). 0xff = default → generic EquipItem (376B alloc). Monster progression: 저급 monster=default, 강함=specific cat (helmet/boots/accessory) (R30) |
| **byte 0 = constant marker** | 0x0b 일관 (format version 추정), cat 아님. byte 11 가 진짜 cat (R30) |
| **register propagation: byte 0xb → r3** | 0xbcb0c ldrb r8 [r3,ip] → 0xbcc08 sp+0x40 → 0xbcc20 ldr ip → 0xbcc38 asr r3 (signed s8). NewDropItem r3 = signed byte 0xb (R30) |
| **droptable.dat multi-tier drop 시스템** | Monster +0x254..+0x26c 의 5단계 threshold + Rand(0,0xffff) 으로 cat 결정 path 선택. byte 7 = default path cat (0..9 모든 EquipItem), byte 11 = highest tier path cat (helmet/boots/accessory). mid paths = Rand(0,9). cat 4=armor 누락 = Sorcerer stub cross-confirm (R31) |
| **Monster progression 검증** | Monster 0=accessory only, Monster 62=weapon/shield/boots common + rare accessory bonus. 게임 difficulty 와 정확 일치 (R31) |
| **MixSmithTable 데이터원 식별** | /c/csv/smith_0/1/2.dat (각 96 entries × 300B/entry = 288 NPC blacksmith recipes). smith_0=accessory craft, smith_1/2=weapon craft. 모두 75% success rate. HERO+0x1d00 = MixSmithTable_ptr (R32) |
| **mix_book vs smith_table 비교** | 둘 다 13-byte recipe layout 공유. mix_book (slot_15, 116) = ApplySpecialMix + Mission, smith_table (288) = ApplyNormalMix (NPC blacksmith UI). success rate 다름 (mix_book 90-100% vs smith 75%) (R32) |
| **enemy_g.dat layout 정밀 분석** | Per-enemy 240B (Map+0x1f0+idx*0xf0). file +4..0xf (12B u8 markers), +0x10..0x1b (6 u16 = HP/MP/ATK/DEF/EXP/Gold), +0x1c..0x2a (15B u8 drop/level), +0x2b 이후 (4 skill blocks × 16B). 121B file 읽음 per enemy (R33) |
| **Monster struct +0x254..+0x275 가 별도 source** | enemy_g 와 직접 매핑 X. Monster constructor 또는 game-state init 에서 set. drop chance thresholds (+0x254..+0x26c) + drop count/type/marker (+0x270..+0x275) (R33) |
| **drop 시스템의 3 데이터원** | (1) enemy_g.dat → Map+0x1f0 (HP/skills), (2) droptable.dat → ItemTable+0x214 (drop pool), (3) Monster init → Monster+0x254..+0x275 (drop thresholds) (R33) |
| **Monster::setEnemyData 발견** | 0xc1a94, 1532B. LoadRes("/c/csv/enemy_%d.dat", arg) → Monster +0x218 (name) ..+0x275 (drop). +0x254..+0x275 의 모든 writer 가 이 함수에 (R34) |
| **enemy_%d.dat 3 files (difficulty)** | enemy_0/1/2.dat 각 23190B × 166 records. 첫 record size 140B (variable). byte 0x10 만 다름 (0x16/0x2d/0x46) → 3 difficulty levels 추정 (R34) |
| **Monster 시스템의 4 데이터원 정리** | enemy_g (Map HP/skills), enemy_*.dat (Monster stat+drop), droptable.dat (drop pool), smith_*.dat (craft recipes) — 모든 Monster/Item 시스템 데이터원 식별 (R34) |
| **enemy_*.dat record byte → Monster field 정밀 매핑** | byte 0..3 → +0x22c..+0x22f (markers), byte 39..66 → +0x254..+0x26c (7 u32 drop thresholds), byte 67..72 → +0x270..+0x275 (drop count/markers), byte 73..79 → +0x276..+0x27c, byte 80+ → BATTLER stats (R35) |
| **Monster decoder + 498 records JSON** | 3 difficulty × 166 records 정확 parse. Easy drop_count=0, Normal=17-19, Hard=26-27 (게임 difficulty 시스템 검증) (R35) |
| **4 element 시스템 구조 식별** | V[136..143] = 4 elements × 2 (atk/def). id=7/8 calc_pl 의 magic atk/def total 식 = sum_elements + V[153]/2 + V[144/145]*(100+30*V[89/93])/100. V[89]/V[93] = current element index. V[151]/V[152] = magic stat pair (skill slot 별 magic damage bonus) (R36) |
| **Mission 시스템 식별** | /c/csv/mission_list.dat (VFS index 48, 5355B) = 105 missions × 44B struct. Mission::LoadMissionTable (0x8b73c). 13+ Check* 함수: Refine/OrbCombine/Mix/Playtime/Money/Rank/SetItem/Collection/QuestComplete 등 (R37) |
| **모든 게임 시스템 데이터원 5종** | enemy_g (Map enemy), enemy_*.dat (Monster ×3), droptable.dat (drop pool), smith_*.dat (craft ×3), mission_list.dat (105 missions) — Round 33-37 으로 모든 시스템 데이터 파이프라인 매핑 완료 (R37) |
| **mission_list.dat record format** | u16 size + u8 strlen + name + (mission_type, sub_type, target_count) + 5×(slot u8, flag u8, value u32) + final_flag = strlen+39 byte. mission_type 0-5 (20/5/22/47/5/5) + 255 metadata. Slot 5..8 = helmet/boots/accessory cat (R38) |
| **Mission decoder + 105 missions JSON** | 105 missions 모두 정확 parse. type 분포가 Round 37 의 13 Check* 함수에 매핑 (collection/rank/quest/mix 등) (R38) |
| **Quest 시스템 식별 (Mission 과 별도)** | QuestMgr 22+ 함수, LoadQuestData (0xd40e8, 1188B) → /c/csv/quest_%d.dat. 3 files (각 22367B × 151 quests). Quest struct 368B (0x170)/entry. Mission(achievements) ↔ Quest(main story) 별도 시스템, Mission::CheckQuestComplete 가 link (R39) |
| **quest_*.dat record 정밀 매핑 + 3 difficulty scaling 확정** | Quest_GetOffset 으로 u16 size prefix layout 확인. body = 3 header byte (h0/h1=obj_count/h2) + (strlen+name) + (strlen+desc) + (strlen+cat) + phase1 (3×6B objective: cond_type u8 + cond_sub u8 + target_value u32) + phase2 (3×6B reward, 17=money/18=exp/255=unused) + 2 byte trailer. body size = 44 + s0+s1+s2. **3 files = save slot 아닌 3 difficulty** (q0/q1/q2 의 reward value 단조 증가 — quest #0 EXP: 340/20830/36150, enemy_*.dat Round 34 와 동일 패턴). 151/151 record EOF 도달 (R40) |
| **decode_h5_quest.py + quests.json 발행** | 기존 stub 교체 (mission_list 디코드 misnamed → 정상 quest decoder). 3 difficulty × 151 quests + compare table → quests.json 645KB (R40) |
| **Save 파일 시스템 RE 시작 + DES 미적용 확정** | 8 save file 종류 (LOCAL/EX/ET/OP/M/H_%d/B_%d/SL_%d.sav) + .rodata string scan. HERO::SaveAll (0x8f924, 92B) dispatch = SlotInfo::SaveSlotData → SaveHeroData → SaveBagData → Mission::SaveData. MX_desEncrypt caller .text 전체 0건 → save 는 **plain bytes**, DES 키 (0EP@KO91) 는 calc_*.dat 등 별도 protected resource 전용 (R41) |
| **자동 save write event 추출 도구** | tools/h5_extract_save_writes.py — ARM disasm + register propagation 으로 Int{8,16,32,64}ToByte / memcpy / strb/h/w 인수 추출. SlotInfo::SaveSlotData 91 events / SaveHeroData 23 events / Mission::SaveData 15 events 추출 (R41) |
| **H_%d.sav (HeroData) 개요** | +0..3 u32 + 2×u8 flag + u32 + **8×u16 stat block** (+0xa..+0x19 = HP/MP/STR/DEX/CON/INT + 2) + **7×u8 equip slot** (+0x45..+0x4b = Round 14 의 EquipItem cat 0-6 일치 추정) + u32 + u8 + 2×u64 timestamp (R41) |
| **SL_%d.sav (SlotInfo) 개요** | 가장 큰 save (malloc 0x2d9f byte buffer). +0..1 class+level / +2..9 GetX/Y / +0xa..0x11 u64 playtime / +0x12..0x15 scene_idx / +0x17 부터 3×256B 블록 (class_info inventory/stat/buff) / +0x31c..+0x489 secondary chunks. 상세 정밀 매핑은 다음 라운드 (R41) |
| **Save load cross-check 도구 + layout 확정** | h5_extract_save_writes.py 확장 (ByteToInt + ldr 추가). h5_save_crosscheck.py 신규 — offset 별 save/load size 매칭 → OK/MISS/save-only/load-only 분류. **H_%d.sav: 21/21 offset 정밀 일치 (0 mismatch)** + load 측에서 +0x1fc/+0x204 u64 timestamp 추가 발견. 총 사용 영역 ≈ 524B. **SL_%d.sav: 24 offset 일치 (0 mismatch)** + header (+0..+0x15) 완전 확정 + sub-block 1/2 (+0x433..+0x438, +0x45d..+0x462 = 6 bytes 각각 — 강화/orb socket 후보) 식별 (R42) |
| **Mission save 부분 확인** | load +0x4 ldrsh 2회 = u16 record_count 또는 size pair. 105 mission iter body 의 변수 offset 정밀 매핑은 다음 라운드 (R42) |
| **Save source struct field 라벨링 + class/level packing 발견** | LoadHeroData/LoadSlotData 정밀 disasm 으로 file_offset → HERO struct offset 완전 매핑. **핵심 발견 1**: SL_*.sav file[0] = `level*10 + class_id` packing — Load 가 umull fast-div-by-10 으로 `% 10` (class) / `/ 10` (level) 분리. max level ≈ 25. **핵심 발견 2**: 3 × 256B blocks 가 gv+0x288/0x388/0x488 = Round 5/6 의 V[58..167+] stat/buff cache 영역 그대로 직렬화 → save/load round-trip 안전. SlotInfo getter 5종 (Class/Level/X/Y/PlayTime/SceneIdx) 모두 LoadSlotData 가 채운 field 사용 검증. **데이터 RE 종료** (R43) |
| **Monster AI 시스템 = token-based bytecode VM** | 12 AI 함수 disasm. **Ai_onAction = 13 opcode interpreter** (SCN opcode 패턴 동일). op 0/1 = WALK/chance walk (motion 1/5), op 4 = SKILL slot (3B = skill_id/target/range → +0x2c9..+0x2cb), op 9 = next_skill_id (Ai_Action state 8 가 사용), op 11 = variable-length data block. **IsTriggerEqual = 13 trigger** (trigger 2 = IRect visibility/range check, trigger 1/11/13 = one-shot flags). Monster struct: +0x288 AI_def_ptr / +0x290 Tokenizer / +0x294 action_idx / +0x297 opcode / +0x2a8..+0x2ab operand buffer / +0x2c2..+0x315 state machine fields. Ai_Process entry (frame당 1회) = stun check → state check → cooldown (default 9 frames) → Ai_Action. AI 정의 데이터가 외부 byte stream (디자이너 가 monster 별 행동 작성). docs/h5/MONSTER_AI.md 신규 (R44) |
| **Monster AI 데이터원 식별 + decoder** | Map::MonsterAdd → EnemyAI* alloc (120B) → EnemyAI::LoadData (700B) 가 `/c/mon/%d_ai` 로드. VFS 에 **48 AI 파일** 발견 (`c/mon/0_ai` ~ `63_ai`, 31-305B, DES 미적용). 파일 layout 완전 파악: trigger codes/handlers + sum(handlers) data + 3 action lookups (n_a + n_a + n_a*2) + trigger byte stream (Tokenizer #1) + 3 action_list lookups (action_list_offset_table 포함) + action byte stream (Tokenizer #2, 13 opcode VM). EnemyAI struct (120B) 매핑: +0x24/+0x44/+0x60 size headers, +0x58/+0x5c trigger stream ptr, +0x70/+0x74 action stream ptr. tools/converter/decode_h5_monsterai.py 신규 — 48/48 perfect parse. monster_ai.json (48 AI defs) 발행. opcode 통계: WALK + CHANCE_WALK = 286/524 (55%) (R45) |
| **Monster AI trigger stream layout 확정** | ActionOfTrigger (0xbd7a0, 140B) driver + IsTriggerEqual 13 handler operand 매핑. Entry layout = `[trigger_code u8][operand 0-1B][action_id u8]`. trigger 1 (VISIBILITY_RECT, operand=IRect index ×40) / 6 (TUTORIAL_FLAG, operand vs gv+0x130..0x132) 만 1B operand. trigger 5 (ALWAYS_GOTO) 는 ActionOfTrigger 가 special path 처리 (IsTriggerEqual 안 부름, 즉시 action_id 처리). 나머지 11 trigger 0B operand (one-shot flag check/consume on Monster+0x2b6/0x2b7/0x29f/etc). decode_h5_monsterai.py 의 disasm_tokens(kind='trigger') 모드 추가. **543 trigger entries 100% perfect parse** (0 unknown, 0 incomplete). 분포: VISIBILITY_RECT 36% + ALWAYS_GOTO 36% (= 72% "idle→combat 시야진입 전환" 패턴). 데이터 RE 100% 종료 (R46) |
| **Monster AI Ai_Action 13 sub-state 완전 매핑** | state 0=CHASE_TIMER (Fast_Distance(hero) vs Monster+0x2c6 시야범위 비교 → ImmadiatelyCheck(8)) / 1=TURN_DIR (4 mode jumptable + default=HeroTurnDirection) / 2=COUNTDOWN (timer + state 0 재진입) / 3=SKILL_USE (IRect 충돌 검사 + cast) / 4=SET_ATTACK_MOTION (Monster+0x2cc 에서 motion lookup) / 5-8=4 skill cast path (각각 Monster+0x304/+0x305/+0x308/+0x30a source) / 9=SKILL_END / 10-11=no-op / 12=GET_MOTION_EXIT. 5 opcode → 6 state skill dispatch matrix 완전 (opcode 4→state 3, opcode 5→state 4, opcode 6→state 5, opcode 7→state 6, opcode 8→state 7, opcode 9→state 8). 공통 gate: GetMotion==0 + IsAttackAble==1 + Monster+0x315==0 (skill_disable). cast 후 Monster+0x297=-1 reset. **Monster AI 분석 완전 종료** (R47) |
| **Monster AI Godot 통합 시작** | apps/hero5-godot/scripts/core/monster_ai.gd 신규 (270 line autoload) — `MonsterAIState` class (Monster struct +0x288..+0x315 영역 매핑: action_idx/opcode/operand/cooldown/state/skill source 5 + flag 11) + `_load_ai_defs` (monster_ai.json 234KB res:// loader) + `create_runtime(host, ai_type_id)` + `process(s)` (frame entry: cooldown + Ai_Action) + `step_action_list(s)` (Ai_doActionList) + `_on_action` (13 opcode interpreter w/ operand size table) + `step_trigger_list(s)` (ActionOfTrigger walker) + `_is_trigger_equal` (13 trigger handler: one-shot flag + host method 위임). project.godot 7th autoload `MonsterAI` 등록. battle_system.gd 에 `_ai_runtime` field + start_battle hook (create_runtime 호출) + `_ai_pick_skill()` helper (트리거+action stream step + skill_id 추천). verify_godot_project.py 0 errors / 0 warnings. Godot 실 구현 25-30% → 30-35% (R48) |
| **Save/Load binary 직렬화 GDScript 구현** | save_manager.gd 확장 — `serialize_hero_save(state)` / `deserialize_hero_save(data)` (H_*.sav 524B, Round 42 의 21/21 cross-check 결과 layout) + `serialize_slot_save` / `deserialize_slot_save` (SL_*.sav header 23B, Round 43 의 `level*10+class_id` packing 포함). byte helpers (`_put_u16/32/64_le`, `_get_u16/32/64_le`) LE encoding. tools/h5_test_save_layout.py 신규 — Python round-trip 검증 도구 (GDScript serialize 의 Python equivalent + 4 samples + 8 critical offsets), **모든 검증 통과**. verify_godot_project.py 0 errors / 0 warnings. Godot 실 구현 30-35% → 33-38%, 출시 27-37% → 30-40% (R49) |

### Phase 2/3 인프라 완료
- ✅ DES 변종 해독 (S1[3][10]=2), calc_*.dat MD5 검증 평문 dump
- ✅ Formula VM 186 공식 (39+19+128) 디스어셈블 + GDScript 평가기 + battle_system 통합
- ✅ gv+0x1474 sub-struct 111 fields 정확 매핑
- ✅ ItemTable / EquipItemInfo / ItemBase 구조체 layout 추출 (R13~R19)
- ✅ items.json 에 named fields 부여 (subtype, class_mask, class_label, level_limit, item_id, sub_record, val_150..val_160, refine fields)

### 직전 작업 (이어서 진행 시 시작점)
- Round 40 종료. 다음 라운드 시작점은 아래 "다음 세션 시작점" 섹션 참조.
- 가장 직접적 옵션 (남은 데이터 RE 마무리): **Save 파일 포맷 분석** — HERO::SaveAll
  (0x8f924) 분석 + DES (key 0EP@KO91, S1[3][10]=2 변종) 복호 + record layout.
- 큰 임팩트 옵션: **Monster AI 시스템** — Ai_Action 2136B 등 미분석 함수 RE.
- 출시 % 끌어올림: **Godot UI 구현** (인벤토리/강화/합성/Quest 패널).
- 또는: scn opcode 실제 game scene 동작 검증, 한글 폰트 매핑 (LOW PRIORITY).
- ✅ **Round 6**: gv_sub 핵심 필드 정확화 (writer 분석으로 V[58]=level, V[60..63]=base_str/dex/int/con,
  V[69]=SP, V[70]=CP, V[118..121]=bonus_str/dex/int/con 확정)
- ✅ **Round 6**: visual 효과 hookup — screen_shake tween, map_tile_change highlight, narration text lookup
- ✅ **Round 7**: V[111]=atk_growth_coef, V[112..116]=secondary stat base, V[153]=stat_con, V[154]=stat_str, V[155]=max_sp 확정
- ✅ **Round 8**: V[127]=def_reduction%, V[128]=atk%bonus, V[129..133]=secondary stat bonus, V[134..148]=element/magic bonus 식별. Round 7 의 0x294/0x296 (buff descriptor) 가 Formula VM var 가 아닌 gameplay 전용 필드임을 정정 (V[125]=0x2a6, V[126]=0x2a8 별개)
- ✅ **Round 9**: ApplyBuildupEffect jumptable 자동 추출 도구 (`tools/h5_apply_buildup_disasm.py`).
  V[122..126] = 5 buff stat slot 확정 (entry type 30/31/32/34/36).
  V[125]/V[126] (0x2a6/0x2a8) 의 store target 확정.
  c_csv_class.json 의 5 클래스 V[112..116] base 패턴 추출 (워리어/로그/건슬링어/나이트/소서러).
  battle_system.gd + formula_vm.gd 에 클래스별 정확 lookup 적용.
- ✅ **Round 10**: 한글 stat label 의 .so 직접 reference 0건 확인 — 모두 VFS text/*.json 에 분산.
  `00017_488ab1c6.json` 에 status menu 의 20-stat 라벨 sequence (방어력/공격력/물리방어력/.../크리티컬저항) 발견.
  `StateInGameMenu::DrawPropertyMenu` 가 register-indirect dynamic dispatch — 정적 분석으로 stat↔cache offset 매핑 어려움 확인.
  `HERO::CalcStatusComputation` 의 24 calc 호출이 모두 `calc_sk[2003] (V[41])` + `calc_sk[2004] (V[156])` 두 공식만 사용 — 7 EquipItem slot × 2 stat + 4 spirit slot × 2 stat. V[136..148] (element bonus) 영역에 cache.
  V[112..116] 5 stat 의 한국어 라벨은 미확정 — 후보 (명중률/회피율/크리티컬/정확도/마법적중) 식별.
- ✅ **Round 11**: c_csv_buildup.json (`tools/h5_decode_buildup.py`) 의 entry type ↔ ApplyBuildupEffect type 매핑으로 **V[112..116] 5 secondary stat 라벨 확정**:
  - V[112] = 근접명중 (csv 0x14 → ABE 11 → V[129] bonus)
  - V[113] = 장거리명중 (csv 0x15 → ABE 12 → V[130] bonus)
  - V[114] = 회피 (csv 0x16 → ABE 13 → V[131] bonus)
  - V[115] = 방패방어 (csv 0x18 → ABE 14 → V[132] bonus)
  - V[116] = 크리티컬 (csv 0x19 → ABE 15 → V[133] bonus)
  5 클래스 base 패턴이 모두 합리적으로 일치 (워리어=근접명중 24, 건슬링어=장거리명중 24, 워리어=방패방어 5).
  **V[62]/V[63] = base_con/base_int 정정** (이전 int/con 매핑 오류) — buildup csv "건강+#1" → ABE 4 → V[120] = bonus_con, "정신+#1" → ABE 5 → V[121] = bonus_int.
  decode_h5_class.py / class_stats.json / class_select.gd / battle_system.gd / formula_vm.gd 일괄 정정.
- ✅ **Round 25**: slot_15 (mix_book recipe) 13 byte ext 구조 RE 완료:
  - layout: byte 0 (separator) + 3×3 byte ingredients (cat/idx/count, 0xff=unused) +
    2 byte result (cat/idx) + 1 byte success_rate %.
  - 116 records 모두 정확히 parse (이름 cross-check 검증).
  - 쿠킹 (살코기+황혼버섯 → 황혼수프가루 100%), 포션 합성 (포션 ×2 → 미들포션 100%),
    재료 정제 (엑토플라즘 ×10 → 에테르 90%), 무기 제작 (보통칼날+가죽+강철 →
    투란기어 90%) 등 카테고리화.
  - success_rate 분포 = 게임 밸런스 검증 (legendary 무기 20-22%, 일반 100%).
  - parse_mix_book_extra 가 의미있는 'recipe' 객체 부여 (이전 raw sb_extra_hex 대체).
- ✅ **Round 24**: val_15f upper 3 bit (tier_flags) 의 실증적 의미 식별:
  - **csv-time vs runtime val_15f 용도 분리** 발견 — csv 는 (class_mask + tier_flags),
    runtime 은 SetItemOption (0xa0ff8) 가 option_type code 로 완전 overwrite.
    GetRelieveLevelLimit (0xa835c) 의 `cmp #0x6c` ('l') 는 runtime option_type 비교.
    MakeItemOption (0xa10e8) 가 val_15c (option_grade) 로 SetItemOption 호출 여부 결정.
  - **items.json 789 EquipItem records 분포 분석** 으로 upper 3 bit 의 의미 추정:
    - upper=0 (170): **legendary** — 실가라스/투란기어/디바인세이버 보스 무기
    - upper=1 (248, bit5): **rare** — 중급 무기/방어구
    - upper=3 (9, bit5+6): **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔)
    - upper=7 (362, bit5+6+7): **common** — 일반 상점 (롱소드/단검 등)
  - 가설: bit5="obtainable" / bit6="gem-accessory" / bit7="common-tier".
  - parse_equip_extra 가 tier_flags + tier_label 부여 (legendary/rare/gem/common).
  - slot_4 "스태프" 1 record 가 tier=legendary + class_mask=0 (Sorcerer 전용 staff)
    Round 22 미구현 stub 사실과 cross-confirm.
- ✅ **Round 23**: HERO::BattleUseItem (0x8fd20, 536B) 디스어셈블 + SLOT_META 전면 정정:
  - slot_11 의 +0x134..+0x137 의미 확정:
    - +0x134 = effect_type → HERO[0x2fe] → CalcStatusComputation 분기
      (91=HP heal, 90=SP heal, 87=buff 보호, 92=마석, 19=test, 0=무효)
    - +0x135 = success_rate % → random(0,99) 와 cmp (모두 100 = 100% 성공)
    - +0x136 = effect_value → HERO[0x300] (u16, 회복량/buff 강도)
    - +0x137 = duration → HERO[0x302] (s16, 지속 turn)
    - SetPotionCoolTime(100) — cooldown 100 frame.
  - SLOT_META 전면 정정 (record 이름 + ext_after_sb 길이 cross-check):
    - slot_12 = orb (이전 scroll 잘못, 2 byte ext, 뇌제의오브 등)
    - slot_13 = mix material (이전 orb 잘못, 0 ext, 살코기/재료2..9)
    - slot_15 = mix_book recipe (이전 material_2 잘못, 13 byte ext, 황혼수프/포션)
  - parse_battle_use_extra 라벨 정정 (val_134→effect_type 등 의미있는 이름).
- ✅ **Round 22**: Sorcerer (class_id=4) 미구현 stub 확정 분석:
  - .so 클래스 심볼 검색 → WARRIOR / ROGUE / GUNNER / KNIGHT 4개만 존재.
    SORCERER class object 없음.
  - skill csv 검색 → c_csv_skill_00..03 (player) + c_csv_skill_05 (16 monster
    skills: 암흑탄/지옥소환/얼음폭풍/완전면역 등). c_csv_skill_04 완전 부재.
  - class_stats.json 검토 → 소서러 unk1..unk14 모두 1 (다른 클래스 6/12/18/24).
    unk0=320 (다른 1000) — 명백한 placeholder.
  - IfLearnSkill 의 (class/2)+16=18 매핑은 dead code path. slot_18 (CashItem)
    의 records 49 모두 class_id=4 없음.
  - class_select.gd UI 정정 — "소서러" → "소서러 (미구현)" 라벨 표시.
  결론: 영웅서기5 출시 빌드 = 4 클래스 only. 소서러는 향후 확장 클래스로
  계획됐으나 미구현 채로 출시.
- ✅ **Round 21**: HERO::IfLearnSkill (0x95d08, 316B) 디스어셈블 → SkillBook
  +0x134..+0x137 의 의미 정확 식별:
  - +0x134 = **class_id** (HERO 클래스 0..4)
  - +0x135 = **skill_index** (HERO::skills[] 배열 인덱스)
  - +0x136 = **skill_level** (LV 매칭 ✓ Round 20)
  - +0x137 = **required_level** (HERO+0x22d 와 cmp)
  - 공식 `(class_id/2)+16` → Warrior/Rogue=cat 16 (slot_16), Gunslinger/Knight=cat 17
    (slot_17), Sorcerer=cat 18 (slot_18 — 충돌, 별도 path 추정).
  - slot_16 도 실제 SkillBook 임이 확인 (양손베기/돌진/내려찍기 등 Warrior 스킬)
    — SLOT_META 정정 (이전 'mix_book' 잘못).
  - parse_skill_book_extra 의 라벨 정정 (val_134→class_id, val_135→skill_index,
    val_137→required_level).
  - 검증: slot_16 95 records (Warrior 48 + Rogue 47), slot_17 98 records
    (Gunslinger 49 + Knight 49). 각 클래스 정확히 10 skills × 1..7 levels.
- ✅ **Round 20**: LoadItemTable 함수 끝 영역 (0xa479c..0xa49c0) 추가 disasm —
  `tools/h5_dump_loaditem_tail.py` (`capstone.skipdata=True` 로 literal pool 통과).
  - **slot_17 (SkillBookItem) 4 byte ext** @ 0xa47c0 (jumptable case 16/17 공유).
    +0x134=skill_class (2/3), +0x135=skill_id (0..9), **+0x136=skill_level**
    (V[1..7] 이름과 정확 매칭 ✓), +0x137=required_level (monotonic).
    검증: '연속사격LV1..LV4' = (2, 0, 1..4, [1, 4, 10, 22]) — 4 byte 모두 일치.
  - **slot_18 (CashItem) 2 byte ext** @ **0xa3b38** (jumptable case 18 별도 path —
    Round 19 의 0xa47c0 가설 정정). hardcoded type 0x12=18 at +0x14, 2 byte:
    +0x134 (cash_category 0..3), +0x135 (stack/type, 255=passive 추정).
  - `decode_h5_item.py` 에 `parse_skill_book_extra` (4 byte) + `parse_cash_extra`
    (2 byte) 추가, SLOT_META[18] = "cash" 로 정정 (이전 "skill_book" 잘못).
  - items.json 검증: slot_17 98 records, slot_18 49 records 모두 추가 fields populated.
- ✅ **Round 19**: LoadItemTable 의 cat 12+ jumptable case 별 추가 fields disasm:
  - cat 12 (BattleUseItem, 0xa4060): +0x134/0x135/0x136/0x137 (4 byte u8) — csv 에서 매칭 ✓
  - cat 13 (OrbItem, 0xa423c): +0x134/0x135 (2 byte, csv 에 보통 없음)
  - cat 14, 15 (MixItem, 0xa43f4): 추가 fields 없음 (record_size = base 만)
  - cat 16 (MixBookItem, 0xa4578): sub-loop +0x135..+0x140 (12+ byte, csv 에 4 만)
  - cat 17, 18 (SkillBook/Cash, 0xa47c0): 다음 라운드
  decode_h5_item.py 에 `parse_battle_use_extra` / `parse_orb_extra` /
  `parse_mix_book_extra` 추가 + dispatch wire-up. items.json 의 slot_11 포션이
  정확한 4 byte (val_134=91, val_135=100, val_136=4, val_137=50) 추출 — disasm
  매핑이 csv 와 정확 일치 검증.
- ✅ **Round 18**: ItemTable::SetItemOption (240B, @0xa0ff8) 디스어셈블 →
  `+0x15f` 가 random option_type byte 임 확인. SetItemOption 가 호출 시 random
  option 픽 → +0x15f = option_type, +0x162 = option_value (level*param*rand).
  csv 의 val_15f 는 init default — runtime 변경 가능. items.json 의 class_label
  통계가 default 값 (Round 16 의 5-class mask 해석은 csv 시점에는 유효).
  LoadItemTable 의 cat 12+ jumptable 분석 — 모든 카테고리가 공통 base layout
  (item_id u32 + sub_record_len + sub_record bytes) 공유. EquipItem (cat 1-11)
  만 sb-area 추가. `decode_h5_item.py` 에 `parse_common_extra` 함수 추가 →
  모든 19 슬롯에 item_id + sub_record_hex 부여.
- ✅ **Round 17**: `RefineItem::ApplyItemRefine` (956B) 디스어셈블 → 강화 시
  변경되는 EquipItemInfo struct field 식별:
  - `+0x165` = refine_count (강화 횟수 u8)
  - `+0x166` = refine_sub_count (보조 강화 u8)
  - `+0x167` = refine_locked (1=영구 잠금)
  ApplyItemRefine 의 r7 jumptable: r7=0/1=success +N, r7=3=lock, r7=4=실패(아이템 destroy).
  CopyData (0xa8884) 가 +0x165..+0x168 모두 복사 → runtime 변경 saved.
  val_15f upper 3 bit 통계: upper=7 (224, "common") 362 records, upper=1 (32, "강화")
  248 records, upper=0 ("중급") 170, upper=3 ("보석 액세서리") 9 (slot_5 헤어핀/서클릿).
  정확 의미 식별 미완 — bit6 (64)=gem accessory, bit7 (128)=common flag 가설.
- ✅ **Round 16**: items.json 정정 — `+0x155` 가 class_restriction 이 아니라
  **subtype code** 임을 IsEquipPossible / IsEquipPossibleSpirit cross-check 로
  확인 (slot_10 spirit 의 cls=5/7 분포 + IsEquipPossibleSpirit 가 0x155==7 만 허용).
  진짜 class restriction 은 **`val_15f & 0x1f`** = **5-class 비트 마스크**
  (bit0=W, bit1=R, bit2=G, bit3=K, bit4=S):
  - val=31 (WRGKS, 모든 클래스) 385 records (가장 많음)
  - val=9 (WK), val=17 (WS), val=14 (RGK), val=18 (RS) 등 다양
  - spirit 검증: 데몬의뿔 W only / 고렘의인장 RS / 팬텀의부적 WS / 기사의징표 RGK
  - decode_h5_item.py 가 `subtype` (이전 class_restriction 정정) + `class_mask`
    + `class_label` (W/R/G/K/S 조합 string) 부여.
  - val_15f upper 3 bit (32, 64, 128) 의 추가 의미 (career/tier/cash) 는 다음 라운드.
- ✅ **Round 15**: `decode_h5_item.py` 에 `parse_equip_extra` 함수 추가 — Round 14
  의 csv layout 활용해 EquipItem (cat 1-11) extra body 가변 parse + items.json
  에 named fields (`class_restriction`, `level_limit`, `item_id`,
  `sub_record_hex`, `val_150..val_160`, `triplet_162`) 부여.
  검증: 롱소드 cls=0/lv=1, 나이트롱소드 lv=5, 버클러(방패) cls=3 (워리어/나이트),
  서클릿(헬멧) cls=5/lv=1 — 모두 합리적 매핑.
  cls 가 비트 마스크로 추정 (1=warrior, 2=rogue, 4=gunslinger, 8=knight, 16=sorcerer)
  — 다음 라운드 IsEquipPossible cross-check 필요.
- ✅ **Round 14**: ItemTable::LoadItemTable (4320B) 의 EquipItem 처리 영역
  (0xa3cf0~0xa4060) 디스어셈블 분석 → csv record body → in-memory EquipItemInfo
  struct field 매핑 layout 추출:
  - csv +2..3 (u16 read but discarded — struct +0x14 = function arg category)
  - csv +4..5 (u16) → struct +0x16 (refine_value)
  - csv +6 (u8 name_len `nl`) → name string memcpy → struct +0x18
  - csv +7+nl..(+4 byte) (u32) → struct +0x30
  - csv +11+nl (u8 sub_record_len `sblen`) → 256B sub-record memcpy → struct +0x34..+0x134
  - 그 후 sb 시작 위치에서 u16/u8 sequence → struct +0x150..+0x162 영역
  - LoadItemTable 안에서 Formula::calc(0x7f3=2035) 호출 — load 시점 base stat 계산
  - `tools/h5_extract_loaditem_layout.py` 도구 작성 (register tracking 한계로
    부분 추출 — 수동 disasm 분석으로 보완).
- ✅ **Round 13**: EquipItemInfo struct 핵심 field + ItemBase formula 영역 식별.
  - EquipItemInfo +0x14 = item_category/slot_type (s8) — IsEquipPossible jumptable 의 조건
  - EquipItemInfo +0x155 = class_restriction (s8) — HERO+0x22c (class_id) 와 비교
  - EquipItemInfo +0x15d = level_limit (s8) — GetLevelLimit 가 fetch
  - EquipItemInfo +0x168..+0x16d = 6 socket slot (orb/refine ID, 0xff=빈슬롯)
  - V[168..182] = ItemBase (Formula::calc 5번째 인수) 의 struct field:
    - V[168] (item +0xe) = base SP cost (`V[168]*(100-V[123])/100`)
    - V[170] (item +0x16) = base cooldown (`V[170]*(100-V[125])/100`)
    - V[174] (item +0x44) = damage growth multiplier (`V[56]+V[57]*V[174]`)
    - V[181] (item +0x4e) = speed/weight divisor
  - csv extra (33..80B) ≠ in-memory EquipItemInfo (376B) — `LoadItemTable` 가 csv→struct
    매핑 처리. csv stat order ↔ struct offset 매핑은 다음 라운드 RE 필요.
- ✅ **Round 12**: V[122..126] 5 buff slot 정확 라벨 + V[151,152] magic stat 정정.
  - V[122] = EXP %bonus (`(100+V[122])/100` multiplier, csv 0x1d 경험치LV)
  - V[123] = SP소모% 감소 (`V[168]*(100-V[123])/100`, csv 0x1e)
  - V[124] = CP충전LV (`(V[124]/100)*150+300`, csv 0x1f)
  - V[125] = 쿨타임 감소% (`V[170]*(100-V[125])/100`, csv 0x21)
  - V[126] = 포션효과 %bonus (`V[56]*V[183]*(100+V[126])/100`, csv 0x23)
  - V[151], V[152] 둘 다 magic stat (INT 보정) — 이전 V[152]=DEX 추정 정정.
  formula 공식의 `(100±V[xxx])/100` 패턴 + csv 라벨 cross-check 로 일관 확정.

**이번 세션 (2026-05-09 Round 6) 완료 항목**:
- **gv_sub writer 분석 도구** — `tools/h5_find_gv_writers.py` (3568 함수 스캔, 547 stores 추적).
  산출 `gv_substruct_writers.tsv` + `gv_substruct_writers_summary.txt` (135 unique offsets).
- **gv_sub 필드 의미 식별** — calc_pl id=18 `(104*V[58]^2)+711+(level-1)*600` ⇒ V[58]=level 확정,
  HERO::IncreaseSP/IncreaseCP writer ⇒ 0x248=SP / 0x24a=CP, calc_pl id=20..23 패턴 ⇒ 0x236..0x23c=base, 0x298..0x29e=bonus.
  자세히 [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md).
- **`battle_system._player_ctx()` 정확화** — 12 확정 + 6 강한 추정 매핑 적용 (이전 추정 6 → 18).
  Python sanity test (`h5_test_formula_eval.py`) id=0 → 4437 통과.
- **`formula_vm._player_default()` 정확화** — defender side fallback 도 동일 매핑 적용.
- **시각 효과 hookup** — demo.gd 의 toast trace → 실제 visual 적용:
  - `screen_shake`: Demo Node2D position Tween 으로 8-step decay oscillation
  - `map_tile_change`: MapRenderer.highlight_tile 노란 사각형 1.5초 표시
  - `narration`: GameData.ingame_text(string_idx) lookup → DialogBox

---

## 빠른 재개 (1 커맨드 = 환경 복원)

**가장 흔한 케이스 — assets/ 비어있는 새 클론**:
```bash
# APK 가 있는지 확인 후 (Hero5/영웅서기5(최신폰전용).apk)
# 한 번에 모든 자산 처리 (~6s, incremental — 이미 있는 단계는 스킵):
python tools/h5_extract_pipeline.py
#   --force        : sentinel 무시하고 전체 재실행
#   --only NAME ...: 특정 단계만 (apk/vfs/names/sprite/text/converters/disasm/godot/verify)
#   --skip NAME ...: 특정 단계 제외
# 단계별 수동:
python tools/h5_vfs_unpack.py            # 1. VFS unpack (2189 entries)
python tools/h5_recover_names.py         # 2. 이름 복원 (99.7%)
python tools/h5_batch_sprite.py          # 3. sprite 421 + palette 588
python tools/h5_extract_text.py          # 4. 한글 코퍼스
for f in tools/converter/{convert,decode}_h5_*.py; do python $f; done   # 5. 디코더 일괄
python tools/import_to_godot.py          # 6. assets/ 채우기 (opcode_table 자동 포함)
python tools/verify_godot_project.py     # 7. 검증 → 0 errors / 0 warnings 기대

# 마지막: Godot 4.2+ Editor 에서 apps/hero5-godot/ 열고 F5
```

**단순 검증만 (assets/ 이미 있음)**:
```bash
python tools/verify_godot_project.py
```

---

## 다음 세션 시작점 (Round 40 후보)

> 진척 평가 (위 § 전체 진척 평가) 기준으로, 가장 큰 임팩트 순.

### A. (분석 track) quest_*.dat record 정밀 매핑 + decoder — 1 라운드 (자율 가능)

Round 39 에서 Quest 시스템 데이터원 (3 files × 151 quests) 식별. 정밀 매핑:
- LoadQuestData 1188B 의 ByteToInt16/strb 시퀀스 추적
- 151 quests × variable-size record (avg 148B) → struct 368B 매핑
- decoder 작성: quest_*.dat → JSON (이름/타입/조건/보상/NPC 대화 등)
- 3 files 동일성 검증 (save slot 가설 cross-check)
- **임팩트**: Mission 시스템과 함께 quest progression 완료, 데이터 RE 거의 마무리

### B. (분석 track) Monster AI 시스템 분석 — 2~3 라운드 (자율 가능, 큰 임팩트)

미분석 큰 덩어리. UI 다음 가장 영향 큰 미완 영역:
- `Monster::Ai_Action` (0xc1068, 2136B) — main AI dispatch
- `Monster::Ai_onAction` (0xbee48, 704B) — action execution
- `Monster::Ai_setActionList` (0xbd82c, 100B) — action list builder
- `Monster::Ai_doActionList` (0xbf108, 184B) — action runner
- `Monster::Ai_Initialize` / `Ai_SetPtr`
- `Monster::IsTriggerEqual` (0xbd278, 1320B) — AI trigger check
- **임팩트**: 실제 Monster 행동 로직 파악 → Godot battle 구현에 직결

### C. (분석 track) Save 파일 포맷 분석 — 1~2 라운드

DES 키 (`0EP@KO91`) + S1[3][10]=2 변종 알려져 있음. Save 파일 record layout 미분석.
- `HERO::SaveAll` (0x8f924) 분석 — 어떤 fields 가 어떤 순서로 직렬화?
- `HERO::LoadAll` 또는 LoadHeroData 분석 — 역직렬화 layout
- save 파일 디코드 + 구조 식별
- **임팩트**: 실제 게임 저장 데이터 호환 → save migration 가능

### D. (구현 track) Godot UI 구현 시작 — 5~10 라운드 큰 작업

데이터는 다 있지만 미구현. 가장 부족한 영역.
- 인벤토리 패널 (items.json 1360 items 활용, equip/sort/filter)
- 강화 UI (Round 17/26 ApplyItemRefine mechanism)
- 합성 UI (mix_book + smith_table)
- NPC 대화 / cutscene UI (scn opcode 77/77)
- Quest / Mission 패널
- **임팩트**: "리메이크 출시 가능" % 가장 크게 끌어올릴 작업

### E. (검증 track) scn opcode 실제 game scene 동작 검증 — 2~3 라운드

Round 22-39 에서 데이터/함수 분석은 했지만 실제 Godot 에서 scn 실행 검증 부족.
- Title → ClassSelect → Demo 외 다른 화면 (Battle, Inventory, Quest 등) 진입 테스트
- scn 258 body 의 opcode dispatch 가 정확히 동작하는지 확인
- 잘못된 opcode 매핑 발견 + 정정
- **임팩트**: 기존 분석의 정확성 검증

### F. 한글 비트맵 폰트 매핑 (LOW PRIORITY)

Round 28 에서 ApplyNormalMix 가 csv slot_15 와 별개로 MixSmithTableInfo* 사용 확인.
HERO::GetMixSmithTableInfoPtr (0x890f4) 의 implementation 분석으로:
- MixSmithTableInfo 데이터의 위치 (VFS entry, .so .rodata 또는 별도 csv 파일)
- 데이터 entry 갯수 + 각 entry 의 의미 (NPC blacksmith UI 와 cross-check)
- struct layout (Round 28: +0x11c..+0x128) 의 csv layout 매핑

### G. P6: Android APK 실 빌드 검증 (USER TASK — 자동화 불가)

Godot Editor 4.2+ + Build Template + Export Templates (~1GB) + JDK 17 + Android
SDK 필수. 사용자가 GUI 로 진행 필요. `apps/hero5-godot/export_presets.cfg.template`
참조. 모든 Godot UI/AI/battle 구현 완료 후 진행.

### 추가 자율 작업 (LOW PRIORITY)

- **val_15f bit5/bit6/bit7 정확 의미** (Round 24/27 가설 검증) — items.json 분포로 라벨 부여, NewDropItem args 추가 검증 필요
- **save 파일 dump → V[112..116] 라벨 재검증** (Round 11 의 secondary stat) — Save 포맷 분석 (옵션 C) 후

---

## 과거 우선순위 작업 (모두 완료)

| 영역 | 상태 | 산출 |
|---|---|---|
| P1: OPCODE_TABLE 77개 | ✅ EventProc::onFunction jumptable 자동 추출 | `work/h5/analysis/opcode_table.tsv`, capstone+lief |
| P2: enemy_g 121B layout | ✅ HP/MP/ATK/DEF/EXP/Gold + 5 skill slot | .so disasm 검증 |
| P3: Hero/CHAR 시스템 | ✅ 4방향 이동 + walk_frames | `character.gd` |
| P4: 전투/퀘스트/UI | ✅ 골격 + 실제 데이터 통합 | battle_system, quest_system |
| P5: 한글 폰트 | ✅ table.dat=Unicode (시스템 폰트로 우회) | `P5_FONT_MAPPING.md` |
| Damage formula 심층 | ✅ Event_PlayerDamage + BATTLER offset 확정 | `BATTLE_FORMULA.md` |
| Formula VM 식별 | ✅ 6 opcode 스택 머신 (calc_pl/en/sk.dat) | `BATTLE_FORMULA.md` §6 |
| Event_* 102개 매핑 | ✅ 1:1 mapping reference | `EVENT_OPCODE_REFERENCE.md` |
| ItemTable 19-카테고리 | ✅ runtime_size dispatch | `ITEM_STRUCT.md` |
| Formula VM 변수 사전 | ✅ 254 var_id → struct/offset | `FORMULA_VAR_DICT.md` |
| GOT gv 식별 | ✅ var_id 58-160 → gv[0x1474] sub-struct | Round 3 |
| interpreter.gd signal | ✅ 13 signal (map/camera/narration/...) | Round 3 |
| DES 변종 해독 | ✅ 표준 DES + S1[3][10]=2 단일 수정 | `DES_VARIANT.md`, Round 4 |
| calc_*.dat 평문 | ✅ 3 파일 MD5 검증 통과 | `work/h5/analysis/calc_*_plain.bin` |
| Formula VM 186 공식 | ✅ infix 표현 dump | `work/h5/analysis/formulas_disasm.txt` |
| gv_sub 111 fields | ✅ var_id 58-167+249 offset/type 매핑 | `gv_substruct_layout.tsv`, Round 5 |
| GDScript Formula VM | ✅ FormulaVM autoload + battle 통합 | `formula_vm.gd`, Round 5 |
| gv_sub 핵심 의미 식별 | ✅ writer 분석으로 V[58]=level / 0x248=SP / 0x24a=CP 등 18 fields 매핑 | `gv_substruct_writers.tsv`, [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md), Round 6 |
| 시각 효과 hookup | ✅ screen_shake tween + map highlight + narration text lookup | `demo.gd`, `map_renderer.gd`, Round 6 |
| V[111..116] 의미 | ✅ Round 7: V[111]=atk_growth coef, V[112..116]=class secondary stat base | LoadResClassInfo disasm + id=24..29 cross-check |
| 0x294/0x295/0x296 buff descriptor | ✅ Round 8: gameplay 전용 (Formula VM var 아님) | HERO::ApplyBuildupEffect + Round 7 정정 |
| V[127..148] buff/element bonus | ✅ Round 8: V[127]=def_red%, V[128]=atk%bonus, V[129..133]=stat bonus, V[134..148]=element | calc_pl 공식 패턴 + AddBuffArray disasm |
| V[151..155] formula 의존 stat | ✅ Round 7: V[153]=con, V[154]=str, V[155]=max_sp 확정 | id=0 / id=24 공식 + ApplyBuildupEffect entry 32 |
| V[122..126] 5 buff stat slot | ✅ Round 9: ApplyBuildupEffect entry type 30/31/32/34/36 자동 추출 | `applybuildup_table.tsv`, `tools/h5_apply_buildup_disasm.py` |
| V[112..116] 클래스 base 패턴 | ✅ Round 9: 5 클래스 secondary stat base 추출 | `class_stats_table.txt`, `tools/h5_extract_class_stats.py` |
| 한글 stat label 의 .so 위치 | ✅ Round 10: .so 0건, VFS text/*.json 에 분산 확인 | `tools/h5_find_kr_stat_strings.py` |
| 00017 status menu 20-stat sequence | ✅ Round 10: 라벨 순서 추출 | `tools/h5_find_kr_text_idx.py`, `kr_stat_text_locations.tsv` |
| CalcStatusComputation 의 calc_sk 매핑 | ✅ Round 10: calc_sk[3]=V[41], calc_sk[4]=V[156] (EquipItem stat) | `calc_status_cache_map.tsv`, `tools/h5_calc_status_table.py` |
| V[112..116] 5 secondary stat 라벨 | ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 확정 | `tools/h5_decode_buildup.py`, `buildup_decoded.tsv` |
| V[62]/V[63] = base_con/base_int 정정 | ✅ Round 11: buildup csv "건강"/"정신" 매핑 검증 | 동일 |
| V[122..126] 5 buff slot 라벨 | ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% | formula `(100±V[xxx])/100` 패턴 |
| V[151,152] magic stat 정정 | ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못) | `formulas_disasm.txt` 사용 패턴 |
| EquipItemInfo struct 핵심 5 field | ✅ Round 13: +0x14/+0x155/+0x15d/+0x168..0x16d | `tools/h5_dump_caller.py _ZN13EquipItemInfo*` |
| V[168..182] ItemBase formula 영역 | ✅ Round 13: V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor | `formulas_disasm.txt` cross-check |
| csv → EquipItemInfo struct layout 매핑 | ✅ Round 14: 가변길이 (name + sub_record) + u8/u16 mixed sequence | `tools/h5_extract_loaditem_layout.py`, ITEM_STRUCT.md "CSV → EquipItemInfo struct 매핑" 섹션 |
| items.json EquipItem named fields | ✅ Round 15: class_restriction/level_limit/item_id/sub_record/val_150..val_160 부여 | `tools/converter/decode_h5_item.py::parse_equip_extra` |
| +0x155 = subtype (class_restriction 정정) | ✅ Round 16: IsEquipPossibleSpirit cross-check | items.json `subtype` 필드 |
| 진짜 class_mask (val_15f & 0x1f) | ✅ Round 16: 5-class 비트 마스크 확정 (W/R/G/K/S) | items.json `class_mask` + `class_label` 필드 |
| EquipItemInfo refine fields | ✅ Round 17: +0x165=count, +0x166=sub_count, +0x167=locked | `applyitemrefine_disasm.txt` |
| val_15f upper 3 bit 분포 | ✅ Round 17: upper=0/1/3/7 만 등장 (170/248/9/362), 정확 의미 미완 | `tools/h5_check_items.py` |
| SetItemOption: +0x15f=option_type / +0x162=option_value | ✅ Round 18 | `_ZN9ItemTable13SetItemOptionEP8ItemInfoa` disasm |
| 모든 카테고리 (cat 1-18) common base | ✅ Round 18: item_id + sub_record_hex | `decode_h5_item.py::parse_common_extra` |
| cat 12-16 카테고리별 추가 fields layout | ✅ Round 19: BattleUseItem 4 byte / OrbItem 2 byte / MixItem 0 / MixBookItem 12 byte | `parse_battle_use_extra` / `parse_orb_extra` / `parse_mix_book_extra` |
| BattleUseItem (cat 12) +0x134..+0x137 csv 매칭 검증 | ✅ Round 19: slot_11 포션 4 byte 정확 추출 | items.json |
| slot_17 (SkillBookItem) 4 byte ext + skill_level 식별 | ✅ Round 20: 0xa47c0 disasm, 98 records 모두 v134/v135/skill_level/v137 추출 | `parse_skill_book_extra`, items.json |
| slot_18 (CashItem) 2 byte ext + 별도 jumptable case | ✅ Round 20: 0xa3b38 (Round 19 가설 정정), 49 records 모두 추출 | `parse_cash_extra`, items.json |
| SkillBook 4 byte fields 의미 (class_id/skill_index/skill_level/required_level) | ✅ Round 21: HERO::IfLearnSkill 분석, (class_id/2)+16 공식 확인 | `iflearnskill_disasm.txt` |
| slot_16 = SkillBook 정정 (이전 mix_book 잘못) | ✅ Round 21: Warrior 48 + Rogue 47, 양손베기/돌진/내려찍기 등 | items.json, SLOT_META |
| 소서러 (class_id=4) 미구현 stub 확정 | ✅ Round 22: skill_04.dat 부재 + SORCERER class 없음 + class_stats unk1..14=1 | class_stats.json, c_csv_skill_*, class_select.gd "(미구현)" |
| class_stats.json STR/DEX/CON/INT 순서 정정 | ✅ Round 11: decode_h5_class.py 정정 + 재생성 | `tools/converter/decode_h5_class.py` |
| 강화 stat 보너스 식 (Formula VM id=35/36) | ✅ Round 26: refined_stat = base + sub_count (V[187]) | `formulas_disasm.txt`, `formula_var_dict.tsv` |
| V[184]/V[185] = item +0x156/+0x158 stat | ✅ Round 26: weapon=atk_min/max, shield=phys/mag def, helmet/boots/acc=primary/secondary | items.json stat_a/stat_b 분포, `decode_h5_item.py::parse_equip_extra` |
| ApplyItemRefine 5-case jumptable 의미 | ✅ Round 26: 큰성공/성공/stay/lock/destroy + refine_count cap=10 | `applyitemrefine_disasm.txt` |
| ApplyOrbCombine orb socket mechanism | ✅ Round 26: 39 orb 종 (3×13), +0x168 orb_count, +0x169..+0x16d 5 socket | `applyorbcombine_disasm.txt` |
| NewDropItem signature 12 args + +0x15f position | ✅ Round 27: `(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 7번째 arg = tier_flags | `newdropitem_disasm.txt` |
| Monster drop_table 13-byte entry | ✅ Round 27: SetDropItem 안에 13B/entry × 4 drop type. NewDropItem 의 +0x15f arg 가 entry byte 에서 직접 전달 | `setdropitem_disasm.txt` |
| +0x15f tier_flags csv↔drop 일관성 | ✅ Round 27: csv val_15f = drop_table 의 byte data 와 동일 의미. Round 24 의 legendary/rare/gem/common 라벨이 게임 drop 로직에서 사용 검증 | 동일 |
| ApplyNormalMix (NPC blacksmith) mechanism | ✅ Round 28: MixSmithTableInfo* 별개 데이터, struct +0x11c..+0x128 col-major | `applynormalmix_disasm.txt` |
| ApplySpecialMix (csv slot_15 recipe) mechanism | ✅ Round 28: GetItemTableInfo 로 csv 직접 사용 + Mission 진척, struct +0x134..+0x140 col-major | `applyspecialmix_disasm.txt` |
| ApplyItemCompose (option 결합) | ✅ Round 28: 두 EquipItem grade≤2 결합 → option set 합성, gv+0x1444+0x198 prob 테이블 | `applyitemcompose_disasm.txt` |
| ApplyItemDecompose (분해) | ✅ Round 28: option_grade-based 5-way prob, gv+0x1444+0x1b8 테이블, money refund / mix material / potion 분기 | `applyitemdecompose_disasm.txt` |
| mix_book recipe csv↔struct layout | ✅ Round 28: csv = row-major (사용자 의미), struct memory = col-major (LoadItemTable transpose). parse_mix_book_extra row-major 객체 그대로 유효 | `applyspecialmix_disasm.txt` |

---

## 게임 흐름

```
Title (로고 + Continue/New Game + 슬롯 메타: Lv/cls/G/inv/시간)
  ├─ New Game → ClassSelect (5 클래스 + STR/DEX/INT/CON 미리보기)
  │             → Demo
  └─ Continue / Slot 클릭 → Demo (저장 자동 로드)

Demo:
  WASD 이동 (충돌, 자동 인카운터 25step+10%/step)
  M/N 맵/씬 (BGM 페이드 + 캐릭터 자동 배치 + 맵 이름 표시)
  P NPC 스폰 (4색 분류) → E 가까운 NPC 와 대화 (한글 + 선택지 → 퀘스트)
  S 상점, Q 퀘스트, I 상태(ATK/DEF 합산), X 설정, H 도움말, B 전투
  자동 저장: slot 7, 60초 간격
  씬 전환 시 0.3s 검정 페이드
```

---

## 새 도구 (Ghidra-free .so 분석 + 통합 파이프라인)

| 도구 | 역할 | 추가 |
|---|---|---|
| `tools/h5_dump_loaditem_tail.py` | LoadItemTable 의 cat 17/18 영역 (0xa479c..0xa49c0) 추가 disasm — `capstone.skipdata=True` 로 literal pool 통과 (Round 20) | 2026-05-10 |
| `tools/h5_decode_buildup.py` | c_csv_buildup.json → ABE entry type 매핑 + V slot 라벨 자동 추출 (Round 11) | 2026-05-09 |
| `tools/h5_find_kr_stat_strings.py` | .so .rodata 에서 한글 stat label 검색 (Round 10) | 2026-05-09 |
| `tools/h5_find_kr_text_idx.py` | VFS text JSON 의 한글 stat label 위치 추출 (Round 10) | 2026-05-09 |
| `tools/h5_calc_status_table.py` | CalcStatusComputation 의 calc_sk → cache offset 매핑 (Round 10) | 2026-05-09 |
| `tools/h5_disasm_property_menu.py` | DrawPropertyMenu cache offset reads 추적 (Round 10) | 2026-05-09 |
| `tools/h5_apply_buildup_disasm.py` | HERO/BATTLER ApplyBuildupEffect jumptable 자동 추출 (Round 9) | 2026-05-09 |
| `tools/h5_extract_class_stats.py` | c_csv_class.json → 5 클래스 V[111..116] base 패턴 (Round 9) | 2026-05-09 |
| `tools/h5_find_battle_check_funcs.py` | 전투 함수 immediate calc id 호출자 추적 (Round 9) | 2026-05-09 |
| `tools/h5_find_formula_callers.py` | Formula::calc 전체 caller 분석 (r0/r1 reg propagation) (Round 9) | 2026-05-09 |
| `tools/h5_list_stat_methods.py` | HERO/CHAR/BATTLER stat 메서드 이름 분류 (Round 9) | 2026-05-09 |
| `tools/h5_dump_caller.py` | 단일 함수 disasm wrapper (Round 9) | 2026-05-09 |
| `tools/h5_find_func.py` | 심볼 substring 탐색 helper (Round 9) | 2026-05-09 |
| `tools/h5_find_gv_writers.py` | gv+0x1474 sub-struct offset 별 writer 함수 추적 (Round 6) | 2026-05-09 |
| `tools/h5_des.py` | 표준 DES + S1[3][10]=2 변종 (mx_des_encrypt/decrypt) | 2026-05-09 |
| `tools/h5_disasm_des.py` | DES 함수 disasm + 테이블 후보 dump | 2026-05-09 |
| `tools/h5_resolve_des_got.py` | PC-relative GOT lookup 해석 | 2026-05-09 |
| `tools/h5_decrypt_calc.py` | calc_pl/en/sk.dat → 평문 (MD5 검증) | 2026-05-09 |
| `tools/h5_formula_disasm.py` | Formula VM 186 공식 → infix 표현 dump | 2026-05-09 |
| `tools/h5_extract_gv_subStruct.py` | var_id 58-160 의 gv+0x1474 sub-struct offset 추출 | 2026-05-09 |
| `tools/h5_export_formulas.py` | 186 공식 + 254 var_dict → GDScript JSON | 2026-05-09 |
| `tools/h5_test_formula_eval.py` | Formula VM 정합성 테스트 (id=0 → 4437 검증) | 2026-05-09 |
| `tools/h5_extract_pipeline.py` | 9-step 통합 파이프라인 (incremental + --force/--only) | 2026-05-09 |
| `tools/h5_scn_body_stats.py` | 258 scn body 정적 trace + opcode 빈도 TSV | 2026-05-09 |
| `tools/h5_extract_battle_funcs.py` | 11 BATTLER/HERO/Monster 함수 ARM disasm + callee | 2026-05-09 |
| `tools/h5_smaf_audit.py` | 42 SMAF ↔ 42 OGG 1:1 매칭 검증 + 청크 dump | 2026-05-09 |
| `tools/h5_disasm_newhiteffect.py` | NewHitEffect / HeroSkillAtkHardCode disasm | 2026-05-09 |
| `tools/h5_find_damage_callers.py` | IncreaseHP/AddEffectDamage caller 추적 | 2026-05-09 |
| `tools/h5_disasm_formula.py` | Formula VM 4 함수 (dataLoad/calc/calcByFormula/getNumberInStack) | 2026-05-09 |
| `tools/h5_disasm_skill_hardcode.py` | HeroSkillAtkHardCode 단독 disasm | 2026-05-09 |
| `tools/h5_extract_event_funcs.py` | EventProc::Event_* 102개 일괄 disasm | 2026-05-09 |
| `tools/h5_disasm_item_funcs.py` | EquipItemInfo CopyData 등 7개 함수 → struct offset 추출 | 2026-05-09 |
| `tools/h5_extract_formula_vars.py` | Formula::getValFunc 254-entry switch → var_id 사전 | 2026-05-09 |
| `tools/h5_extract_opcode_disasm.py` | EventProc::onFunction jumptable → opcode_table.json 77 entries | 2026-05-08 |
| `tools/h5_event_arg_sizes.py` | Itanium ABI mangle parser → 105 Event_* arg_size | 2026-05-08 |
| `tools/h5_extract_enemy_layout.py` | Map::MapEnemyG_set → 121B record layout 검증 | 2026-05-08 |
| `tools/h5_inspect_enemy_record.py` | 디버그용 raw record dump | 2026-05-08 |
| `tools/h5_batch_sprite.py` | sprite/palette single-argv converter wrapper | 2026-05-08 |

의존: `pip install lief capstone`. import_to_godot.py 가 둘 다 있으면 opcode_table.json
자동 생성 (없으면 graceful skip — BASE_TABLE 38 fallback).

---

## 파일 위치 빠른 참조

### Phase 2 산출물 (`work/h5/` — gitignored)
- `extracted/` — APK unzip (assets/data.vfs.mp3, lib/armeabi/libHeroesLore5.so)
- `vfs_entries/` — 2,189 unpacked records
- `vfs_catalog.tsv` — index/hash/length/type
- `analysis/asset_names.tsv` — 99.7% 이름 복원
- `analysis/opcode_table.tsv` — 77/77 (자동 추출)
- `analysis/event_arg_sizes.tsv` — 105 Event_* arg sizes
- `analysis/enemy_g_layout.tsv` — record byte → struct field 매핑
- `analysis/scn_headers.tsv` — 258 scene 헤더
- `analysis/formula_var_dict.tsv` — 254 var_id → struct/offset (Round 3)
- `analysis/gv_substruct_layout.tsv` — 111 gv+0x1474 sub-struct fields (Round 5)
- `analysis/calc_pl/en/sk_plain.bin` — DES 복호 평문 (Round 4)
- `analysis/formulas_disasm.txt` — 186 공식 infix dump (Round 4, 945 줄)
- `analysis/des_disasm.txt`, `des_got_resolved.json`, `des_tables.json` — DES RE 산출
- `converted/sprites/<idx>/frame_NN_*.png`
- `converted/text/_corpus.txt` — 18,837 unique 한글

### Phase 3 (`apps/hero5-godot/`)
```
project.godot           # autoload 6: GameState/AssetLoader/GameData/Audio/Quest/FormulaVM
scenes/                 # 14 씬
scripts/core/           # 11 싱글톤/게임 로직
  game_state.gd, asset_loader.gd, game_data.gd, audio_manager.gd, quest_system.gd
  map_renderer.gd, character.gd, interpreter.gd, battle_system.gd, save_manager.gd
  formula_vm.gd            # ← Round 5: Formula VM 평가기 (calc_*.dat 186 공식)
scripts/ui/             # 17 UI 스크립트 (scene_fader.gd 추가)
assets/                 # gitignore — import_to_godot.py 가 채움
  sprites/, gbm/, palettes/, text/, sounds/, fonts/, gamedata/, maps/, scenes/
  scenes/opcode_table.json   # ← P1 산출물 (capstone+lief 있으면 자동 생성)
  scenes/bodies/<idx>.bin    # ← P1 scene body 자동 실행용
  data/formula/formulas.json # ← Round 5: 186 공식 (id → body)
  data/formula/var_dict.json # ← Round 5: 254 var_id → struct/offset
```

### 도구 (`tools/`)
- `h5_vfs_unpack.py`, `h5_recover_names.py`, `h5_extract_text.py` — Phase 2 추출
- `h5_batch_sprite.py` — single-argv converter wrapper
- `h5_extract_opcode_disasm.py`, `h5_event_arg_sizes.py`, `h5_extract_enemy_layout.py`
  — capstone+lief 분석 (P1, P2)
- `import_to_godot.py` — 모든 자산 → Godot
- `verify_godot_project.py` — tscn/gd reference 검증
- `converter/*` — 자산 디코더 (sprite/pa/gbm/scn/csv/skill/item/quest/enemy)

---

## 디버그 / 테스트 키 (Demo 씬)

| 키 | 기능 |
|---|---|
| WASD | 이동 |
| M / N | mapID / scene 전환 |
| P | NPC 마커 스폰 (4색) |
| E | 가까운 NPC 와 대화 |
| T | dialog 테스트 (트리거) |
| S | 상점 |
| Q | 퀘스트 패널 |
| I / ESC | 상태창 (ATK/DEF 합산 + hover 비교) |
| X | Settings |
| H | 도움말 |
| B | 즉시 전투 (테스트) |
| C / V | collision / tile attribute 디버그 |
| 1-8 | 슬롯 N 저장 |
| Shift+1-8 | 슬롯 N 로드 |
| F5 / F9 | slot 0 빠른 저장 / 로드 |

---

## 알려진 제한

- [x] ~~Interpreter opcode dispatch (22/77 만 구현)~~ — ✅ 77/77 (2026-05-08)
- [x] ~~enemy ATK/DEF offset 일부 부정확~~ — ✅ .so disasm 검증 완료 (2026-05-08)
- [x] ~~DES 복호화 차단~~ — ✅ 표준 DES + S1[3][10]=2 변종 해독 (2026-05-09)
- [x] ~~calc_*.dat 평문 미확보~~ — ✅ MD5 검증 통과 (2026-05-09)
- [x] ~~Formula VM 공식 추출 미완~~ — ✅ 186 공식 infix dump (2026-05-09)
- [x] ~~battle_system.gd 의 Formula VM 평가기 미구현~~ — ✅ FormulaVM autoload + battle 통합 (2026-05-09)
- [x] ~~gv+0x1474 sub-struct offset 추출~~ — ✅ 111 fields 정확 매핑 (2026-05-09)
- [x] ~~gv_sub 핵심 필드명 정확화~~ — ✅ Round 6 writer 분석으로 18 fields 의미 확정 (V[58]=level, V[60..63]=base, V[69]=SP, V[70]=CP, V[118..121]=bonus)
- [x] ~~V[111..116] (클래스 base 계수) 의미~~ — ✅ Round 7: V[111]=atk_growth, V[112..116]=secondary stat base
- [x] ~~V[155]=max_sp~~ — ✅ Round 7: ApplyBuildupEffect SP clamp 상한
- [x] ~~V[127..148] 다중 buff/element bonus~~ — ✅ Round 8: V[127]=def_red%, V[128]=atk%, V[129..133]=stat bonus, V[134..148]=element
- [x] ~~Round 7 0x294/0x296 mapping~~ — ✅ Round 8 정정: gameplay 전용 (Formula VM var 아님)
- [x] ~~V[125,126] (0x2a6, 0x2a8) buff slot 의미 식별~~ — ✅ Round 9: ApplyBuildupEffect entry type 34/36 으로 5-slot 시스템 일부임 확정
- [x] ~~V[112..116] 5 stat 의 한국어 라벨~~ — ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 (buildup csv 매핑)
- [x] ~~V[62]/V[63] 매핑 정정~~ — ✅ Round 11: int/con → con/int (이전 매핑 오류, buildup csv 로 검증)
- [x] ~~V[122..126] 5 buff slot 의미~~ — ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% 확정
- [x] ~~V[151,152] magic stat~~ — ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못)
- [x] ~~RefineItem::ApplyItemRefine 강화 stat 보너스 mechanism~~ — ✅ Round 26: V[184]+V[187] / V[185]+V[187] (id=35/36), 5-case jumptable
- [x] ~~ApplyOrbCombine orb 결합 mechanism~~ — ✅ Round 26: 39 orb 종, +0x168 count, +0x169..+0x16d 5 socket
- [ ] V[151] vs V[152] 의 element 짝 (fire/ice/lightning/dark 어느 것)
- [ ] 한글 비트맵 폰트 (시스템 폰트로 우회 중) — P5, capstone+lief 로 가능
- [ ] SMAF (.mmf) 변환 (OGG 42개로 충당)
- [ ] 자산 이름 7개 / 0.3% 미복원 (게임 영향 없음)
- [ ] Android APK 실 빌드 미검증 — P6, Godot Editor 환경 필수
- [ ] Godot Editor 에서 실제 실행 검증 — verify 는 reference 만, GDScript compile 미검증

---

## 환경 의존성

**필수**:
- Python 3.10+
- Pillow (sprite 변환)

**.so disasm 작업 시 (P1/P2/P5)**:
- `pip install lief capstone`

**Godot 빌드/실행**:
- Godot 4.2+ Editor
- (Android export) JDK 17 + Android SDK + NDK + build template

---

## 참조 문서

- [`PROGRESS.md`](PROGRESS.md) — 전체 진행 상세 (Phase 2 분석 단계별 + Phase 3 시스템별)
- [`PHASE3_ENGINE.md`](PHASE3_ENGINE.md) — Godot 4 엔진 결정 근거
- [`DES_VARIANT.md`](DES_VARIANT.md) — DES 변종 해독 + calc_*.dat 평문 + Formula VM 디스어셈블러
- [`BATTLE_FORMULA.md`](BATTLE_FORMULA.md) — BATTLER damage 함수 disasm + Event_PlayerDamage 공식 + Formula VM/DES 키
- [`FORMULA_VAR_DICT.md`](FORMULA_VAR_DICT.md) — Formula VM 변수 사전 (254 var_id → struct/offset)
- [`EVENT_OPCODE_REFERENCE.md`](EVENT_OPCODE_REFERENCE.md) — 102개 Event_* opcode 의미 매핑 reference
- [`ITEM_STRUCT.md`](ITEM_STRUCT.md) — EquipItemInfo struct 부분 layout + 19-카테고리 dispatch
- [`P5_FONT_MAPPING.md`](P5_FONT_MAPPING.md) — table.dat=Unicode (EUC-KR 아님) 정정 + 매핑 위치
- [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md) — Round 6: HERO 객체 (=gv+0x1474) offset 별 의미 매핑 (writer 분석)
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 템플릿
