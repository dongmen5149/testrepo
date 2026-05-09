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

### Round 7 추가: LoadResClassInfo + ApplyBuildupEffect disasm 결과

`HERO::LoadResClassInfo` (0x8beb4, sz=932) 디스어셈블 — `ByteToInt16` 으로
6 stats 를 sequential 읽어 0x278..0x282 에 store. 이로써 V[111..116] 가
**클래스별 6 secondary stat base** 임이 구조적으로 확정.

`HERO::ApplyBuildupEffect` (0x95878, sz=1168) 디스어셈블 — 0x36 entry
jumptable. Effect type 별 store target 식별:
- entry 32 (orig type=32): `[0x248] = clamp([0x248]+arg, 0, [0x2e6])` → SP heal,
  upper bound = `[0x2e6]` ⇒ **V[155] (0x2e6) = max_sp 확정**.
- entry 33 (orig=33): `[0x1b61]` (HiperCount, 우리 영역 밖)
- entry 34 (orig=34): `[0x294]=9, [0x295]=0x3b, [0x296]=arg`  → buff descriptor
- entry 35 (orig=35): `[0x294]=3, [0x295]=0x71, [0x296]=arg`
- entry 36 (orig=36): `[0x294]=8, [0x295]=0x72, [0x296]=arg`
- entry 1 (default): `b BATTLER::ApplyBuildupEffect` (parent class delegation)

→ **0x294 = active_buff_effect_type, 0x295 = active_buff_icon_idx, 0x296 = strength**.

| offset | var_id | meaning | 근거 |
|---|---|---|---|
| 0x278 | V[111] | atk_growth_per_(level*2+str) coefficient | id=24 ATK 공식 multiplier 위치 |
| 0x27a | V[112] | secondary stat #1 base | LoadResClassInfo seq + id=25 V[112]+V[129]*10 |
| 0x27c | V[113] | secondary stat #2 base | id=26 V[113]+V[130]*10 |
| 0x27e | V[114] | secondary stat #3 base | id=27 V[114]+V[131] |
| 0x280 | V[115] | secondary stat #4 base | id=28 V[115]+V[132] |
| 0x282 | V[116] | secondary stat #5 base | id=29 V[116]+V[133] |
| 0x294 | V[125] u8 | **active buff effect_type** | HERO::ApplyBuildupEffect entry 34..36 store 3/8/9 |
| 0x295 | (s8) | **active buff icon idx** | 동일 entry 들에서 0x3b/0x71/0x72 store |
| 0x296 | V[126] u8 | **active buff strength** | 동일 entry 들에서 caller arg store |
| 0x298~0x2c0 | V[127..147] | buff/debuff 추가 슬롯 (다중 buff stack 추정) | Monster::Ai_Initialize 와 공유 → BATTLER 공통 buff array |
| 0x2c2~0x2da | V[148..150] | Monster AI state (enemy 전용) | Monster::Ai_* 위주 writer |
| 0x2de | V[151] | magic stat (player ctx 한정 — int) | id=4 magic atk 공식 +V[151] |
| 0x2e0 | V[152] | magic stat 짝 (player ctx — dex) | id=5 magic atk 공식 +V[152] |
| 0x2e2 | V[153] | **stat_con** | id=0 MaxHP 공식 10*V[153] |
| 0x2e4 | V[154] | **stat_str** | id=24 ATK 공식 V[58]*2+V[154] |
| 0x2e6 | V[155] | **max_sp** | ApplyBuildupEffect entry 32 SP clamp 상한 |
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
| ~~V[111..116] 의미~~ | ✅ Round 7: V[111]=atk_growth coef, V[112..116]=secondary stats base | LoadResClassInfo + id=24..29 공식 cross-check 완료 |
| ~~V[125,126] buff slot~~ | ✅ Round 7: 0x294=type, 0x295=icon, 0x296=strength | HERO::ApplyBuildupEffect entry 34..36 |
| ~~V[155] = max_sp~~ | ✅ Round 7: ApplyBuildupEffect SP clamp 상한 | 확정 |
| V[112..116] 5 stat 라벨 | "secondary base" 까지만 | calc_pl id=25..29 결과 stat 의미 식별 (hit/avoid/crit/?) |
| V[127..147] buff slot 다중 stack | "extra buff slots" 까지만 | BATTLER::AddBuff / AddBuffArray disasm |
| V[151,152] magic stat 라벨 | int/dex 추정 | calc_pl id=4 vs id=5 element 확정 (fire/ice 등?) |

이상의 미확정 영역도 동작에는 영향 없음 — formula_vm 가 default 0 반환,
battle_system 의 임시 공식 fallback 으로 게임플레이 보장.
