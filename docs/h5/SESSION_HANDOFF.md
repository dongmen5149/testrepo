# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-09 (Round 7 — V[111..116] / V[125,126] / V[151..155] 의미 추가 확정)

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
- ✅ **Round 7**: V[111]=atk_growth_coef, V[112..116]=secondary stat base, V[125,126]=buff descriptor (type/strength), V[153]=stat_con, V[154]=stat_str, V[155]=max_sp 확정

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

### 1. V[112..116] 5 stat 라벨 식별 (자율 가능, 작은 임팩트)

V[112..116] = 5 secondary stat base 까지만 확정. 각 stat 이 hit/avoid/crit/block/speed 중
무엇인지 calc_pl 결과 stat 사용처 (계산된 값을 어디서 fetch 하는지) 추적 필요.

### 2. V[127..147] 다중 buff stack 의미 (자율 가능, 작은 임팩트)

BATTLER::AddBuff / AddBuffArray (이미 symbol 있음) 디스어셈블로 buff slot 별 의미 식별.
`HERO::ApplyBuildupEffect` 는 단일 buff descriptor 만 식별 — 다중 stack 영역 미해결.

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
| V[125,126] buff descriptor | ✅ Round 7: 0x294=type, 0x295=icon, 0x296=strength | HERO::ApplyBuildupEffect entry 34..36 |
| V[151..155] formula 의존 stat | ✅ Round 7: V[153]=con, V[154]=str, V[155]=max_sp 확정 | id=0 / id=24 공식 + ApplyBuildupEffect entry 32 |

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
- [x] ~~V[125,126] buff descriptor~~ — ✅ Round 7: 0x294=type, 0x295=icon, 0x296=strength
- [x] ~~V[155]=max_sp~~ — ✅ Round 7: ApplyBuildupEffect SP clamp 상한
- [ ] V[112..116] 5 stat 라벨 (hit/avoid/crit/...) 식별
- [ ] V[127..147] 다중 buff stack slot 별 의미 (AddBuff/AddBuffArray disasm)
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
