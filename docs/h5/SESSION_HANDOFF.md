# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-10 (Round 15 — decode_h5_item.py 의 parse_equip_extra 추가로 items.json 에 named fields 부여 (class_restriction/level_limit/item_id/sockets))

---

## 30초 요약

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 작업 (P1~P4) + DES 해독 + Formula VM 통합** 완료.
Title → ClassSelect → Demo 흐름 동작 가능한 Godot 4 프로젝트 (`apps/hero5-godot/`).
38 GDScript / 14 씬 / **6 싱글톤 (FormulaVM 추가)** / OPCODE_TABLE 77/77.

**verify_godot_project.py: 0 errors / 0 warnings.**

**현재 상태**:
- ✅ DES 변종 완전 해독 (S1[3][10]=2 단일 수정), calc_*.dat MD5 검증 평문 dump
- ✅ Formula VM 186 공식 (39+19+128) 디스어셈블 + GDScript 평가기 + battle_system 통합
- ✅ gv+0x1474 sub-struct 111 fields 정확 매핑
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

## 다음 세션 시작점 (가장 임팩트 큰 후속 작업)

### 1. class_restriction 비트 마스크 의미 확정 (자율 가능, 작은 임팩트)

Round 15 에서 items.json 에 class_restriction 부여. cls 값의 비트 마스크 가설
(1=W, 2=R, 4=G, 8=K, 16=S) 을 IsEquipPossible disasm 의 0x155 비교 패턴 분석으로
검증. items.json 에 cls 별 한글 라벨 (e.g. "W+K") 부여 가능.

### 2. RefineItem::ApplyItemRefine (956B) + ApplyOrbCombine (1208B) 디스어셈블

강화/orb 결합 시 어느 struct field 가 변경되는지 추적. socket slot
(struct +0x168..+0x16d) 의 read/write 패턴 + level_limit / refine_value
(+0x16) 변경 패턴 식별.

### 3. 비-EquipItem (cat 12+) parse 추가 (자율 가능)

decode_h5_item.py 의 parse_equip_extra 와 같은 방식으로 BattleUseItem (cat 12),
OrbItem (13), MixItem (14-15), MixBookItem (16), SkillBookItem (17-18) 의 csv
layout 분석. LoadItemTable 의 idx 12..18 jumptable case 디스어셈블 필요.

### 2. V[151] vs V[152] 의 element 차이 식별 (자율 가능, 작은 임팩트)

Round 12 에서 V[151], V[152] 둘 다 INT-magic stat 확정. id=4 / id=5 의 두
magic atk 가 어떤 element (fire/ice/lightning/dark 등) 짝인지 식별.
calc_pl id=7, id=8 의 V[136..143] 4-element bonus 영역과 cross-check 가능.

### 3. Save 데이터 구조 검증 (선택)

save 파일 dump 후 0x278..0x282 (V[111..116]) 영역의 game-saved 값을 game UI
표시값과 매칭해서 V[112..116] 라벨 (Round 11) 을 다시 확인 가능.

### 3. 한글 비트맵 폰트 매핑 (LOW PRIORITY — 게임 영향 없음)

`_midas_funcFntInvalidate` 디스어셈블로 581 glyph index ↔ Unicode 매핑 추출.
시스템 폰트 (Noto Sans CJK KR) 로 우회 중이므로 게임 동작에 영향 없음 — 폰트 충실도 향상 only.

### 4. P6: Android APK 실 빌드 검증 (USER TASK)

자동화 불가. Godot Editor 4.2+ + Build Template + Export Templates (~1GB) + JDK 17 + Android SDK 필수.
사용자가 GUI 로 진행 필요. `apps/hero5-godot/export_presets.cfg.template` 참조.

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
| class_stats.json STR/DEX/CON/INT 순서 정정 | ✅ Round 11: decode_h5_class.py 정정 + 재생성 | `tools/converter/decode_h5_class.py` |

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
