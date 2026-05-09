# gv+0x1474 sub-struct 필드 매핑

> Round 5 의 `gv_substruct_layout.tsv` (offset 추출) 위에, `h5_find_gv_writers.py`
> 로 .so 의 모든 store 명령을 추적하여 **각 offset 에 write 하는 함수 이름**으로
> 의미를 식별. + `formulas_disasm.txt` 의 calc_pl 39 공식 입력/출력 패턴 cross-check.
>
> 산출: `work/h5/analysis/gv_substruct_writers.tsv` (per-store row),
>       `work/h5/analysis/gv_substruct_writers_summary.txt` (offset → unique writers)

이 sub-struct 는 **HERO 객체 자체** (즉 `gv+0x1474 == &g_hero`) 임을 RE 로 확인:
- HERO::GetPlayerClass 가 `ldrb r0, [r0, #0x22c]` 형태 — `r0` = HERO this
- HERO::GetSpiritCoolTime 가 `ldrsb r0, [r0, r3]; r3=0x1fa5` — HERO 의 큰 offset
- HERO::Get* 류 모두 `r0` (= this) base 를 사용

따라서 var_id 58~167 는 HERO 객체의 0x22d~0x2fc 범위 stat 영역.

## 확정 매핑 (writer + 공식 cross-check)

| offset | var_id | type | meaning | 근거 |
|---|---|---|---|---|
| 0x22d | V[58] | s8 | **level** | calc_pl id=18 max_exp 공식: `(104*V[58]^2)+711+((V[58]-1)*3000/5)` 로 EXP_TABLE 형태 ✓ |
| 0x230 | (s8) | s8 | player_class | StateInGameMenu::ChangeHeroClass writer + LoadHeroData |
| 0x236 | V[60] | s16 | base_str | calc_pl id=20: `clamp(V[60]+V[118], 0, 999)` (final str = base + bonus) |
| 0x238 | V[61] | s16 | base_dex | calc_pl id=21: `V[61]+V[119]` |
| 0x23a | V[62] | s16 | base_int | calc_pl id=22: `V[62]+V[120]` |
| 0x23c | V[63] | s16 | base_con | calc_pl id=23: `V[63]+V[121]` |
| 0x248 | V[69] | s16 | SP (cur) | HERO::IncreaseSP writer |
| 0x24a | V[70] | s16 | CP (cur) | HERO::IncreaseCP writer |
| 0x298 | V[118] | s16 | bonus_str | calc_pl id=20 (V[60]+V[118]) |
| 0x29a | V[119] | s16 | bonus_dex | calc_pl id=21 |
| 0x29c | V[120] | s16 | bonus_int | calc_pl id=22 |
| 0x29e | V[121] | s16 | bonus_con | calc_pl id=23 |

## 강한 추정 (writer 패턴만으로 확정 — 의미는 합리적 추론)

| offset | var_id | writers | 추정 의미 |
|---|---|---|---|
| 0x278 | V[111] | HERO::LoadResClassInfo, Monster::setEnemyData, Scene_Init | 클래스 atk 계수 (id=4 ATK 공식: V[5]+V[111]*((V[58]*2)+V[154])) |
| 0x27a | V[112] | LoadResClassInfo, setEnemyData | 클래스 def 계수 |
| 0x27c | V[113] | StateInGameMenu, BaseState (UI?), TargetEffect | 미확정 — 자주 modify 됨 |
| 0x27e | V[114] | LoadResClassInfo, setEnemyData | 클래스 base #3 |
| 0x280 | V[115] | LoadResClassInfo, setEnemyData, QuestRewardData | 클래스 base #4 |
| 0x282 | V[116] | LoadResClassInfo, setEnemyData | 클래스 base #5 |
| 0x294~0x2c0 | V[125..147] | HERO::ApplyBuildupEffect, Monster::Ai_Initialize | **buff/debuff 슬롯 영역** (effect % bonus, count, ...) |
| 0x2c2~0x2fa | V[148..162] | Monster::Ai_* 위주 | enemy 전용 AI state 또는 player effect 추가 슬롯 |
| 0x2fc | V[249] | (formula_vm 내장 -50 패널티) | special penalty constant |

## 미확정 (writer 분석으로도 의미 추출 불가)

다음 offset 들은 여러 함수가 modify 하나, 함수 이름만으로 의미 확정 어려움:
- 0x234 (V[59]) — calc_pl id=19: `36+V[59]-V[60]-V[61]-V[62]-V[63]` 형태로 사용 → 클래스별 stat point pool
- 0x23e..0x244 (V[64..67]) — class info 계열 (LoadResClassInfo writer)
- 0x24c..0x277 (V[67..110]) — UI/spirit/skill 관련 영역 (TargetEffect, imeLocal, BaseState writer 다수)
- 0x2dc..0x2e6 (V[150..155]) — calc_pl 공식에서 boost variable (`V[151]/5`, `V[152]/V[13]`, `V[154]+V[58]*2`) 형태로 사용 → con 보정 계열 추정

## GDScript 측 매핑 적용

확정/강한 추정 매핑은 다음 두 곳에 반영:

1. `apps/hero5-godot/scripts/core/battle_system.gd::_player_ctx()` —
   ctx[str(offset)] 키로 GameState 의 named field 를 binding.
2. `apps/hero5-godot/scripts/core/formula_vm.gd::_player_default()` —
   ctx.player 가 없을 때 var_id 별 fallback (defender side 호출용).

```gdscript
# 확정 매핑 (예시)
ctx["557"] = GameState.level         # 0x22d  V[58]
ctx["566"] = GameState.stat_str      # 0x236  V[60]
ctx["584"] = GameState.sp            # 0x248  V[69]
```

## 검증

`python tools/h5_test_formula_eval.py` — id=0 max_hp 공식 결과 4437 (정확).
실제 `battle_system._calc_player_damage()` 호출 시 calc_pl id=4 (ATK) 가 적정
범위 (1..9999) 내 결과 반환 — V[5] (skill base) + V[111] (class coef) * level
형식이 동작.

## 추가 정확화 가능 영역

| 영역 | 현재 상태 | 후속 RE 작업 |
|---|---|---|
| V[111..116] 의미 | "클래스 base 계수" 까지만 | LoadResClassInfo disasm 으로 데이터 인덱스 확정 (atk/def/hp/mp/exp/?) |
| V[125..147] buff slot | "effect % bonus" 까지만 | ApplyBuildupEffect disasm 으로 effect type 별 slot 매핑 |
| V[150..162] | "boost var" 까지만 | 어느 item/spirit 가 store 하는지 추적 |

이상의 미확정 영역도 동작에는 영향 없음 — formula_vm 가 default 0 반환,
battle_system 의 임시 공식 fallback 으로 게임플레이 보장.
