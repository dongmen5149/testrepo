# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-09 (Polish 라운드 + 심층 데미지/Formula VM 분석 + 102개 Event_* opcode 1:1 매핑 + 아이템 struct 부분 추출 + DES 키 식별)

---

## 30초 요약

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 작업 (P1/P2/P3/P4)** 완료. Title → ClassSelect → Demo 흐름이 동작
가능한 Godot 4 프로젝트 (`apps/hero5-godot/`). 38 GDScript / 14 씬 / 5 싱글톤 /
**OPCODE_TABLE 77/77 (.so ARM disasm 자동 추출, Ghidra 불필요)**.

**verify_godot_project.py: 0 errors / 0 warnings.**

이번 세션 (2026-05-09) 완료 항목:
- **통합 파이프라인** — `tools/h5_extract_pipeline.py` 신규. 새 클론에서 1
  커맨드(=9 단계 6.1s)로 APK unzip → VFS → names → sprite → text → converter →
  .so disasm → import_to_godot → verify 전체. incremental sentinel + `--force`/`--only`/`--skip`.
- **scn body 정적 trace** — `tools/h5_scn_body_stats.py` 가 258 body 를 interpreter.gd
  와 동일 규칙으로 정적 dispatch. opcode 빈도 TSV + 미정의/잘림 보고. 254/258 end-marker,
  31 미정의 (24 distinct, 모두 1-4 회) — dispatch 정확도 정량 확인.
- **BATTLER damage disasm** — `tools/h5_extract_battle_funcs.py` 가 11개 핵심 함수
  ARM disasm + callee 추출 (max 39 callee = `HERO::NewHitEffect`). **`Event_PlayerDamage`
  완전 추출** = % of max_hp 데미지, 100% 만 즉사 허용. BATTLER 멤버 offset 확정:
  +0xf0 cur_hp / +0x180 max_hp / +0x210 spirit_buffer. → `docs/h5/BATTLE_FORMULA.md`.
- **SMAF audit** — `tools/h5_smaf_audit.py` 로 42 SMAF ↔ 42 OGG 가 **완전 1:1 매칭**
  증명. SMAF→OGG 변환 작업 영구 클로즈 (OGG 만으로 모든 BGM/SFX 충당).
- **P5 폰트 매핑 정정** — table.dat 가 EUC-KR 이 아니라 **Unicode BMP** (0x8861-0xD3B7,
  Hanja 773 + Hangul 1246 + 기타 331). `convert_h5_fnt2png.py` 정정 +
  `docs/h5/P5_FONT_MAPPING.md` 작성. 581-glyph 매핑은 `_midas_funcFntInvalidate`
  내부 — 시스템 폰트 우회로 게임 무관.

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

## 다음 우선순위 작업

### P5: 한글 자모 인코딩 정밀 — ✅ 부분 완료 (2026-05-09)
정정 사항: table.dat 는 EUC-KR 이 아니라 **Unicode BMP**. 자세히 `docs/h5/P5_FONT_MAPPING.md`.
- ✅ table.dat → Unicode codepoint list (Hanja 773 + Hangul 1246 + 기타 331).
- ✅ 폰트 그리기 호출 경로 추적 (`MX_fntDrawString` → `_midas_funcFntInvalidate`).
- ⏳ 581-glyph 매핑 자체는 `_midas_funcFntInvalidate` 디스어셈블 시 추출 가능.
- 게임 영향 0 — Noto Sans CJK KR 시스템 폰트로 충분.

### P6: Android APK 실 빌드 검증 — 사용자 직접 진행 필요
- Godot Editor 4.2+ + Install Android Build Template + Export Templates (~1GB) +
  JDK 17 + Android SDK + NDK 필수.
- `apps/hero5-godot/export_presets.cfg.template` 참조 (arm64-v8a, min SDK 23, target 34).
- 이 머신에서 자동화 불가 — 사용자가 GUI 로 진행 필요.

### Polish + 심층 분석 — ✅ 모두 완료 (2026-05-09)
- ✅ **scene body 실행 trace** — `tools/h5_scn_body_stats.py` (258/258 dispatch 99%+ 정확).
- ✅ **damage formula 분석 (심층)** — Event_PlayerDamage 100% 추출 + BATTLER offset 확정.
  `HERO::NewHitEffect`/`HeroSkillAtkHardCode` 는 시각 이펙트와 KnockBack/Snatch 로직만.
  실제 데미지는 **`TargetEffect::ProcDemageCalc` → `Formula::calc()` (스택 기반 VM)**.
- ✅ **Formula VM 식별** — 공식이 외부 데이터 (`calc_pl/en/sk.dat`, DES 암호화) 에 인코딩.
  6 opcode (XOR/MOD/DIV/MUL/SUB/ADD) 의 스택 머신. 자세히 `BATTLE_FORMULA.md` §6.
- ✅ **DES 키 발견** — `'0EP@KO91'` (`onStartApp` 의 `MX_desInit` 인자 추적).
- ✅ **SMAF → OGG 변환** — 변환 불필요 (1:1 매칭).
- ✅ **Event_* opcode 102개 1:1 매핑** — `docs/h5/EVENT_OPCODE_REFERENCE.md`.
  4B stub 13개 식별 (DRM 잔재). interpreter.gd 핸들러 disasm-confirmed semantics 로 보강.
- ✅ **EquipItemInfo struct 부분 layout** — `docs/h5/ITEM_STRUCT.md` (CopyData offset 분석).

### 후속 자율 가능 작업 (남은 가치)
- DES 키 변환 검증 → calc_*.dat 평문 확보 → Formula VM 디스어셈블러 작성 → 정확한 공식
  추출 → battle_system.gd 100% 재현. (`BATTLE_FORMULA.md` §6 참조)
- `Formula::getValFunc` (6372B) 변수 ID 사전 추출 → 어떤 ID 가 ATK/DEF/Lv 인지 매핑.
- `ItemTable::GetItemTableInfo` (288B) → ItemInfo struct 완전 매핑.
- `_midas_funcFntInvalidate` → kor.fnt 581 ↔ Unicode 매핑 (게임 영향 0).
- interpreter.gd `_dispatch` 핸들러 → 실제 GameState/MapRenderer/Quest 호출 채우기
  (`EVENT_OPCODE_REFERENCE.md` §4 가이드 참조).

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
- `converted/sprites/<idx>/frame_NN_*.png`
- `converted/text/_corpus.txt` — 18,837 unique 한글

### Phase 3 (`apps/hero5-godot/`)
```
project.godot           # autoload 5: GameState/AssetLoader/GameData/Audio/Quest
scenes/                 # 14 씬
scripts/core/           # 10 싱글톤/게임 로직
  game_state.gd, asset_loader.gd, game_data.gd, audio_manager.gd, quest_system.gd
  map_renderer.gd, character.gd, interpreter.gd, battle_system.gd, save_manager.gd
scripts/ui/             # 17 UI 스크립트 (scene_fader.gd 추가)
assets/                 # gitignore — import_to_godot.py 가 채움
  sprites/, gbm/, palettes/, text/, sounds/, fonts/, gamedata/, maps/, scenes/
  scenes/opcode_table.json   # ← P1 산출물 (capstone+lief 있으면 자동 생성)
  scenes/bodies/<idx>.bin    # ← P1 scene body 자동 실행용
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
- [`BATTLE_FORMULA.md`](BATTLE_FORMULA.md) — BATTLER damage 함수 disasm + Event_PlayerDamage 공식 + Formula VM/DES 키
- [`EVENT_OPCODE_REFERENCE.md`](EVENT_OPCODE_REFERENCE.md) — 102개 Event_* opcode 의미 매핑 reference
- [`ITEM_STRUCT.md`](ITEM_STRUCT.md) — EquipItemInfo struct 부분 layout
- [`P5_FONT_MAPPING.md`](P5_FONT_MAPPING.md) — table.dat=Unicode (EUC-KR 아님) 정정 + 매핑 위치
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 템플릿
