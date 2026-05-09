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
| 0x23a | V[62] | s16 | **base_con** ✅ Round 11 정정 | calc_pl id=22: `V[62]+V[120]`. buildup csv "건강+#1" (csv 0x03 → ABE 4 → V[120]) 로 검증 |
| 0x23c | V[63] | s16 | **base_int** ✅ Round 11 정정 | calc_pl id=23: `V[63]+V[121]`. buildup csv "정신+#1" (csv 0x04 → ABE 5 → V[121]) 로 검증 |
| 0x248 | V[69] | s16 | SP (cur) | HERO::IncreaseSP writer |
| 0x24a | V[70] | s16 | CP (cur) | HERO::IncreaseCP writer |
| 0x298 | V[118] | s16 | bonus_str | calc_pl id=20 (V[60]+V[118]). buildup "근력+#1" → ABE type 2 |
| 0x29a | V[119] | s16 | bonus_dex | calc_pl id=21. buildup "민첩+#1" → ABE type 3 |
| 0x29c | V[120] | s16 | **bonus_con** ✅ Round 11 정정 | calc_pl id=22. buildup "건강+#1" → ABE type 4 |
| 0x29e | V[121] | s16 | **bonus_int** ✅ Round 11 정정 | calc_pl id=23. buildup "정신+#1" → ABE type 5 |

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
| 0x27a | V[112] | **근접명중 (melee_hit) base** ✅ Round 11 | csv 0x14→ABE 11→V[129]. id=25 V[112]+V[129]*10 (% rate). 워리어 24 / 건슬링어 6 = 근접 클래스 우세 |
| 0x27c | V[113] | **장거리명중 (ranged_hit) base** ✅ Round 11 | csv 0x15→ABE 12→V[130]. id=26 V[113]+V[130]*10. 건슬링어 24 / 워리어 18 = 원거리 클래스 우세 |
| 0x27e | V[114] | **회피 (avoid) base** ✅ Round 11 | csv 0x16→ABE 13→V[131]. id=27 V[114]+V[131] flat. 워리어 24 / 로그 18 = 회피 우세 |
| 0x280 | V[115] | **방패방어 (block) base** ✅ Round 11 | csv 0x18→ABE 14→V[132]. id=28 V[115]+V[132] flat. 워리어 5 / 나이트 4 = 방패 클래스 우세 (작은 unit %) |
| 0x282 | V[116] | **크리티컬 (crit) base** ✅ Round 11 | csv 0x19→ABE 15→V[133]. id=29 V[116]+V[133] flat. 모두 0 / 소서러 1 = 아이템/buff 로 획득하는 stat |
| 0x294 | (gameplay only) | **active buff effect_type** (Formula VM var 아님) | HERO::ApplyBuildupEffect entry 34..36 store 3/8/9 |
| 0x295 | (gameplay only) | **active buff icon idx** | 동일 entry 들에서 0x3b/0x71/0x72 store |
| 0x296 | (gameplay only) | **active buff strength** | 동일 entry 들에서 caller arg store |
| 0x2a0 | V[122] | **EXP/경험치 % bonus** ✅ Round 12 | csv 0x1d "경험치LV". 공식 `(100+V[122])/100` multiplier (id=29 와 별개 EXP 공식) |
| 0x2a2 | V[123] | **SP소모량 감소%** ✅ Round 12 | csv 0x1e "강공태세효과/SP소모". 공식 `V[168]*(100-V[123])/100` reduction |
| 0x2a4 | V[124] | **CP 충전 LV (정수)** ✅ Round 12 | csv 0x1f "CP충전LV". 공식 `(V[124]/100)*150 + 300` 또는 `2+(V[124]/100)` |
| 0x2a6 | V[125] | **쿨타임 감소%** ✅ Round 12 | csv 0x21 "쿨타임 #1%감소". 공식 `V[170]*(100-V[125])/100` reduction |
| 0x2a8 | V[126] | **포션효과 % bonus** ✅ Round 12 | csv 0x23 "포션효과+#1%". 공식 `V[56]*V[183]*(100+V[126])/100` multiplier |
| 0x2aa | V[127] s8 | **defense_reduction_percent (0..99)** | calc_pl 공식: (100-(V[127]/2)*V[83]*15)/100 데미지 감쇠 |
| 0x2ac | V[128] | **atk_percent_bonus** | id=24 ATK 공식 (100+V[128])/100 buff multiplier |
| 0x2ae | V[129] | **근접명중 bonus** ✅ Round 11 | id=25 V[112]+V[129]*10. csv 0x14 "근접명중+#1" → ABE 11 |
| 0x2b0 | V[130] | **장거리명중 bonus** ✅ Round 11 | id=26 V[113]+V[130]*10. csv 0x15 "장거리명중+#1" → ABE 12 |
| 0x2b2 | V[131] | **회피 bonus** ✅ Round 11 | id=27 V[114]+V[131]. csv 0x16 "회피+#1" → ABE 13 |
| 0x2b4 | V[132] | **방패방어 bonus** ✅ Round 11 | id=28 V[115]+V[132]. csv 0x18 "방패방어+#1" → ABE 14 |
| 0x2b6 | V[133] | **크리티컬 bonus** ✅ Round 11 | id=29 V[116]+V[133]. csv 0x19 "크리티컬+#1" → ABE 15 |
| 0x2b8, 0x2ba | V[134], V[135] | 마법 ATK 짝 (element 1, 2) | id=4,5: V[6/7]+(V[134]+V[135])/2+V[151/152] |
| 0x2bc~0x2ca | V[136..143] | 8 element bonus (4 pair) | id=7,8: 4-element grouped sums |
| 0x2cc, 0x2ce | V[144], V[145] | main element bonus | id=7,8: V[144/145]*(100+30*V[89/93])/100 |
| 0x2d0, 0x2d2, 0x2d4 | V[146..148] | sub-stat (255-bound) | id=16 V[146]+V[148]+...+V[154]/5 |
| 0x2de | V[151] | **magic stat 1 (= INT)** ✅ Round 12 | id=4 magic atk1 +V[151], id=9 V[151]/5, id=N V[151]/12, V[151]*V[56]/100 |
| 0x2e0 | V[152] | **magic stat 2 (= INT)** ✅ Round 12 | id=5 magic atk2 +V[152], id=10 V[152]/5, id=11 V[152]/V[13], V[152]/12 |
| 0x2e2 | V[153] | **stat_con** | id=0 MaxHP 공식 10*V[153] |
| 0x2e4 | V[154] | **stat_str** | id=24 ATK 공식 V[58]*2+V[154] |
| 0x2e6 | V[155] | **max_sp** | ApplyBuildupEffect entry 32 SP clamp 상한 |
| 0x2fc | V[249] | (formula_vm 내장 -50 패널티) | special penalty constant |

### Round 9 추가: ApplyBuildupEffect 자동 entry table + V[122..126] buff slot 확정

`tools/h5_apply_buildup_disasm.py` 가 jumptable 패턴을 자동 인식하여 56개 entry
type 의 store target 을 추출. HERO/BATTLER 두 함수 모두 동일 entry table.

| entry type | offset | var_id | 의미 |
|---:|---:|---:|---|
| 2 | 0x298 | V[118] | bonus_str  (s16 add) |
| 3 | 0x29a | V[119] | bonus_dex |
| 4 | 0x29c | V[120] | bonus_int |
| 5 | 0x29e | V[121] | bonus_con |
| 10 | 0x2ac | V[128] | atk_percent_bonus |
| 11..15 | 0x2ae..0x2b6 | V[129..133] | secondary stat #1..#5 bonus |
| 30 | 0x2a0 | V[122] | **buff stat slot #1** |
| 31 | 0x2a2 | V[123] | **buff stat slot #2** |
| 32 | 0x2a4 | V[124] | **buff stat slot #3** |
| 34 | 0x2a6 | V[125] | **buff stat slot #4** ✅ Round 9 확정 |
| 36 | 0x2a8 | V[126] | **buff stat slot #5** ✅ Round 9 확정 |
| 38 | 0x2aa | V[127] | def_reduction% (s8 strb) |
| 39 | 0x295 | — | active buff icon idx (descriptor strb) |
| 42..45 | (bl) | — | EquipItem-specific bonus (`bl GetEquipItem`) |
| 46 | 0x248 | V[69] | SP heal (clamp [0,V[155]]) |
| 47 | 0x1b61 | — | HiperCount |
| 48..50 | 0x294/0x295/0x296 | — | active buff descriptor (effect_type/icon/strength) |
| 51 | 0x1ac | — | special flag (s8 strb) |
| 52 | (bl) | — | Spirit (`bl GetSpiritInfoPtr` → +0xe write) |
| 54 | 0x24a | V[70] | CP set to 3000 (full) |

**확정**:
- V[125] (0x2a6), V[126] (0x2a8) 는 buff system 의 추가 stat slot.
- V[122..126] = 5 buff slot — secondary stat (V[112..116]) 짝일 가능성
  높음 (slot 수 일치), 단 정확한 stat 라벨 식별은 미완 (V[112..116] 라벨
  의존).
- `HERO::InitStatusComputation` 가 0x298..0x2b6 영역 (V[118..133]) 전부 0 reset
  → 이는 매 stat recalc 마다 buff/temp bonus 가 리셋되고 active buff 들이
  ApplyBuildupEffect 로 다시 합산된다는 의미.

### Round 9 추가: V[112..116] 클래스별 base 값

`tools/h5_extract_class_stats.py` 로 5 클래스의 LoadResClassInfo 시퀀스 추출
(idx 14 = V[111] atk_growth, idx 15..19 = V[112..116] secondary base):

| 클래스    | V[112] | V[113] | V[114] | V[115] | V[116] |
|---|---:|---:|---:|---:|---:|
| 워리어    | 24 | 18 | 24 |  5 | 0 |
| 로그      | 12 | 12 | 18 |  3 | 0 |
| 건슬링어  |  6 | 24 |  6 |  2 | 0 |
| 나이트    | 18 |  6 | 12 |  4 | 0 |
| 소서러    |  1 |  1 |  1 |  1 | 1 |

**패턴 분석** (정확 라벨 미확정 — 추정):
- V[112]: 워리어 우세 → melee accuracy / block
- V[113]: 건슬링어 우세 → long-range hit / speed
- V[114]: 워리어/로그 우세 → avoid / crit
- V[115]: 워리어 우세 + 작은 unit (5/3/2/4/1) → block rate (% 단위)
- V[116]: 모두 0 (소서러만 1) → magic-related stat

정확 라벨 식별은 status menu UI 함수 한글 string 매핑이 필요 (다음 라운드).

### Round 12 추가: V[122..126] / V[151,152] 라벨 정확화 (formula 패턴 분석)

`tools/h5_decode_buildup.py` 의 csv 매핑 + formulas_disasm.txt 의 공식 사용 패턴 cross-check.

V[122..126] 5 buff slot 의 정확 라벨 (이전 라운드 "buff slot #N" 으로 임시) 확정:

| V slot | 공식 패턴 | 의미 |
|---|---|---|
| V[122] | `(100+V[122])/100` × big_value | **EXP 경험치 % bonus** |
| V[123] | `V[168]*(100-V[123])/100` | **SP 소모량 감소 %** |
| V[124] | `(V[124]/100)*150+300`, `2+(V[124]/100)` | **CP 충전 LV** (정수 단위) |
| V[125] | `V[170]*(100-V[125])/100` | **쿨타임 감소 %** |
| V[126] | `V[56]*V[183]*(100+V[126])/100` | **포션효과 % bonus** |

5 stat 모두 `(100±V[xxx])/100` 패턴 — 이는 % multiplier/reduction 의 표준 형식.
ApplyBuildupEffect 가 V slot 에 add s16 (누적 buff stack) 으로 store.
csv 0x1d/0x1e/0x1f/0x21/0x23 의 한국어 라벨과 모두 일관 매핑.

V[151], V[152] = **둘 다 magic stat (INT 보정)** 확정:

| V slot | 사용 공식 | 패턴 |
|---|---|---|
| V[151] | id=4 magic atk1, id=9 V[151]/5, V[151]/12, V[151]*V[56]/100 | element 1 magic atk 보정 |
| V[152] | id=5 magic atk2, id=10 V[152]/5, V[152]/V[13], V[152]/12, V[152]*(500+V[248])/500 | element 2 magic atk 보정 |

이전 라운드의 V[152]=DEX 추정은 잘못 — magic atk 보정 stat 이므로 INT (또는 derived
magic stat). 두 V slot 의 차이는 element pair (id=4 vs id=5 의 magic atk1/2 짝)
이지만 둘 다 INT 기반으로 추정.

### Round 11 추가: c_csv_buildup.json → V[112..116] 정확 라벨 확정 + V[62]/V[63] 정정

`tools/h5_decode_buildup.py` 가 buildup csv 의 모든 entry decode + ABE 매핑 자동 추출.
extra_hex 형식: `[ffff sentinel] [type:u8] [sub:u8] [val:u16]` × N entries.

**csv type N → ApplyBuildupEffect type N+1 매핑** (csv 0x01..0x04, 0x14..0x19 영역):

| csv type | kr label | ABE type | V slot | cache offset | 의미 |
|---:|---|---:|---|---:|---|
| 0x01 | 근력+#N | 2 | V[118] | 0x298 | bonus_str |
| 0x02 | 민첩+#N | 3 | V[119] | 0x29a | bonus_dex |
| 0x03 | **건강**+#N | 4 | V[120] | 0x29c | **bonus_con** ✅ |
| 0x04 | **정신**+#N | 5 | V[121] | 0x29e | **bonus_int** ✅ |
| 0x14 | 근접명중+#N | 11 | V[129] | 0x2ae | secondary bonus #1 |
| 0x15 | 장거리명중+#N | 12 | V[130] | 0x2b0 | secondary bonus #2 |
| 0x16 | 회피+#N | 13 | V[131] | 0x2b2 | secondary bonus #3 |
| 0x18 | 방패방어+#N | 14 | V[132] | 0x2b4 | secondary bonus #4 |
| 0x19 | 크리티컬+#N | 15 | V[133] | 0x2b6 | secondary bonus #5 |

이 매핑으로 V[112..116] 5 secondary stat 라벨 확정:
- V[112] = 근접명중 base (워리어 24, 건슬링어 6)
- V[113] = 장거리명중 base (건슬링어 24, 워리어 18)
- V[114] = 회피 base (워리어 24, 로그 18)
- V[115] = 방패방어 base (워리어 5, 나이트 4 — 작은 unit %)
- V[116] = 크리티컬 base (모두 0 / 소서러 1 — 아이템 획득 stat)

**V[62]/V[63] 정정 (이전 라운드 매핑 오류)**:
한국어 "건강" = CON, "정신" = INT. csv 매핑으로 V[120] = bonus_con, V[121] = bonus_int.
calc_pl id=22 `V[62]+V[120]` 의 V[62] 는 base_con (이전 base_int 오류).
calc_pl id=23 `V[63]+V[121]` 의 V[63] 는 base_int (이전 base_con 오류).

c_csv_class.json 의 워리어 STR/DEX/INT/CON = 12/8/10/6 라벨링도 디코더 잘못 —
실제 데이터 byte sequence 는 STR/DEX/CON/INT (워리어 12 STR / 8 DEX / 10 CON / 6 INT).

5 클래스 base 패턴이 이 정정으로 더 자연스러움:
- 워리어: STR 12, DEX 8, **CON 10**, INT 6  (탱커, CON 두 번째 강함)
- 로그:   STR 6, DEX 10, **CON 8**, INT 12  (도적, INT 도 높음)
- 건슬링어: STR 8, DEX 12, **CON 6**, INT 10
- 나이트: STR 10, DEX 6, **CON 12**, INT 8  (방패 탱커, CON 가장 강함)
- 소서러: STR 6, DEX 8, **CON 8**, INT 14  (마법사, INT 압도)

**csv 0x05..0x13 (HP/SP 관련) 영역**:
ABE 의 default fallthrough 또는 별도 dispatch (HP/SP 회복 함수 등) — secondary stat
영역은 csv 0x14..0x19 의 5 entries 만.

### Round 10 추가: 한글 stat label string 위치 + status menu 표시 순서

**한글 stat label 은 .so 에 직접 없음** — 모두 VFS 의 `vfs_entries/000NN.txt`
(work/h5/converted/text/*.json 에 dump) 파일에 분산. status menu UI 함수가
`ingame_text(string_idx)` 같은 패턴으로 fetch.

`tools/h5_find_kr_stat_strings.py` 결과: .so 의 .rodata 에 0 reference.
`tools/h5_find_kr_text_idx.py` 결과: 한글 stat 라벨이 여러 text 파일에 분산.

**핵심 파일** `00017_488ab1c6.json` 의 first region (offset 142..420) 이
status menu 의 stat 라벨 sequence (총 20 stat):

| seq | offset | 한글 라벨 | 추정 mapping |
|---:|---:|---|---|
| 1 | 193 | 방어력 | Phys DEF (calc_pl id=2 or 3) |
| 2 | 202 | 공격력 | ATK (calc_pl id=24) |
| 3 | 211 | 물리방어력 | PhysDEF |
| 4 | 224 | 마법방어력 | MagDEF |
| 5 | 244 | 명중률 | Hit (id=?) |
| 6 | 253 | 회피율 | Avoid |
| 7 | 262 | 정확도 | Accuracy |
| 8 | 279 | 근접방어 | Melee DEF |
| 9 | 290 | 장거리방어 | Ranged DEF |
| 10 | 303 | 마법공격 | Magic ATK |
| 11 | 314 | 특수방어 | Special DEF |
| 12 | 325 | 특수공격 | Special ATK |
| 13 | 336 | 근접공격 | Melee ATK |
| 14 | 347 | 장거리공격 | Ranged ATK |
| 15 | 360 | 물리회피 | Phys Evade |
| 16 | 371 | 문법저항 | (오타? 마법저항) |
| 17 | 382 | 마법적중 | Magic Hit |
| 18 | 393 | 마법방어 | Magic DEF (중복) |
| 19 | 404 | 크리티컬 | Crit |
| 20 | 415 | 크리티컬저항 | Crit Resist |

20 stat 중 5 개가 V[112..116] 와 매칭되어야 함 (5 secondary stat base).
가장 합리적 후보: **명중률 (5) / 회피율 (6) / 크리티컬 (19) / 정확도 (7) / 마법적중 (17)**
또는 **근접공격 (13) / 장거리공격 (14) / 명중률 / 회피율 / 크리티컬**.
정확 매핑은 DrawPropertyMenu dynamic dispatch 추적 또는 save 데이터 검증 필요.

### Round 10 추가: DrawPropertyMenu 동적 dispatch 확인

`StateInGameMenu::DrawPropertyMenu` (5072B, @0xf05e8) 디스어셈블 결과:
- **Formula::calc 직접 호출 없음** — 이미 cache 된 stat 값을 read 만 함.
- **stat read 가 모두 register-indirect**: `ldr r? , [reg, reg]` 형태.
  cache offset table 이 GOT 또는 literal pool 을 거쳐 동적 lookup —
  정적 분석으로 stat label ↔ cache offset 매핑 어려움.

다음 라운드 단서 — GOT 의 string lookup table + cache offset table 동시 추적
또는 save 파일 직접 분석.

### Round 10 추가: CalcStatusComputation 의 calc_sk 매핑

`tools/h5_calc_status_table.py` 가 자동 추출. CalcStatusComputation 는 24번
호출하지만 **모두 calc_sk id=2003 (=0x7f3, V[41]) + calc_sk id=2004 (=0x7f4, V[156])**
두 공식만 사용 (16 짝 + 4 sentinel + 4 spirit slot):

| seq | formula_id | cache_off | 의미 |
|---:|---:|---:|---|
| 0..15 | 2003/2004 | 0x2bc..0x2d6 | 7 EquipItem slot × 2 stat (V[136..149]) |
| 16..18 | (default) | — | sentinel (item 없을 시 zero) |
| 19..22 | 2003/2004 | 0x17b6..0x17bc | 4 spirit slot × 2 stat (별도 영역) |

`calc_sk[2003]` = `V[41]` (skill+0x98) — clamp [0,500]: melee/close-range bonus
`calc_sk[2004]` = `V[156]` (pc 영역) — clamp [0,100]: long-range bonus
→ EquipItem 별 두 종류 stat bonus 합산. 이는 V[136..148] (element bonus 영역)
와 매칭하며, V[112..116] secondary stat 와는 직접 무관.

### Round 9 추가: HERO::CalcStatusComputation = calc_sk 호출 확인

이 함수는 `Formula::calc(formula_id=0x7f0+N, ..)` 즉 calc_sk 호출자 — EquipItem
slot 별로 stat bonus 를 합산해서 V[134..148] (element bonus 영역) 에 cache.
calc_pl id=25..29 직접 immediate 호출자가 .so 전체에 없음을 확인 →
calc_pl id=25..29 결과는 다른 코드 (TargetEffect::ProcDemageCalc 등) 가
**dynamic formula_id** (`ldrsb r1, [r6, #N]` HeroSkillInfo 의 byte field) 로 호출.

`tools/h5_find_battle_check_funcs.py` 로 전투 핵심 함수의 immediate calc 호출만
추적했을 때 발견된 매핑:
- TargetEffect::ProcDemageCalc → calc_pl id=1, 2, 3 (damage 계산 시 attacker / defender stat fetch)
- HERO::CalcStatusComputation → calc_sk id=2035, 2036 (EquipItem stat bonus)

### Round 8 추가: BATTLER buff array 영역 (참고용 — gv+0x1474 영역 밖)

`BATTLER::AddBuffSkill` (0x4b198) 디스어셈블 — buff array 들이 BATTLER 인스턴스의
다음 offset 들에 위치 (HERO 의 0x294~ 영역과 별개의 lower 영역):

| BATTLER offset | 의미 |
|---|---|
| 0x118 + 3 = 0x11b | active buff state array (3 slot, 1B) — 4F sentinel |
| 0x11c + 2 = 0x11e | val1 array (3*2B short) |
| 0x124            | val2 array (3*2B short) |
| 0x128 + 2 = 0x12a | val3 array (3*2B short) |
| 0x1c8            | BuffMotion sprite ptr array |

이 영역은 Formula VM 가 직접 read 하지 않음 (var_dict 에 없음). gameplay 코드
(`AddBuff`/`BuffEndProc` 등) 가 in-place 관리. UI/effect 시각화에 사용.

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
| ~~V[122..126] buff slot~~ | ✅ Round 9: ApplyBuildupEffect entry type 30..36 자동 추출 | `applybuildup_table.tsv` |
| ~~V[112..116] 5 stat 라벨~~ | ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 확정 | `buildup_decoded.tsv`, `tools/h5_decode_buildup.py` |
| ~~V[62]/V[63] = base_con/base_int~~ | ✅ Round 11: csv "건강"/"정신" 매핑으로 정정 (이전 INT/CON 오류) | buildup csv |
| ~~V[122..126] 5 buff slot 라벨~~ | ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% | formula 공식 패턴 + csv 매핑 |
| ~~V[151,152] magic stat 라벨~~ | ✅ Round 12: 둘 다 magic stat (INT 보정), element 1/2 짝 | formula 사용 패턴 분석 |
| V[151] vs V[152] element 차이 | id=4 vs id=5 의 두 magic atk 가 어떤 element (fire/ice 등) | element 데이터 / damage type 매핑 분석 |

이상의 미확정 영역도 동작에는 영향 없음 — formula_vm 가 default 0 반환,
battle_system 의 임시 공식 fallback 으로 게임플레이 보장.
