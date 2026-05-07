# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-08 (P3 + P4 + P1 완료, 자산 환경 처음부터 복원)

---

## 30초 요약

**Phase 2 (자산 추출/분석)** + **Phase 3 (Godot 게임 시스템)** + **P1 (Interpreter
opcode dispatch 77/77)** 모두 완료. Title → ClassSelect → Demo 흐름이 완비된
Godot 4 프로젝트 (`apps/hero5-godot/`) 가 동작 가능한 상태. 37 GDScript / 14 씬 /
5 싱글톤 / **OPCODE_TABLE 77/77 (.so ARM disasm 자동 추출)**.

이번 세션 큰 성과:
- 자산 환경을 이 머신에서 처음부터 복원 (APK → VFS → 변환 → Godot import).
- **opcode_table 77/77 자동 추출** — Ghidra 없이 capstone + lief 로 완성.
- BASE_TABLE 의 추측 매핑 (Quest 0x31~0x42, Scene_ChangeBgm) → 실제 (0x29~0x2d) 로
  검증·수정. PROGRESS.md 의 일부 hint 가 추측이었음을 .so disasm 으로 확정.

verify_godot_project.py: **0 errors / 0 warnings** (처음 달성).

남은 큰 미해결: enemy ATK/DEF offset 정확도 (P2, BATTLER setter 추적 필요),
한글 자모 인코딩 (P5, Graphic::DrawText 디컴파일), Android APK 실 빌드 (P6, Editor 필요).

---

## 빠른 재개 (3 커맨드)

```bash
# 1. 자산 임포트 (assets/ 디렉토리 비어있을 때만)
python tools/import_to_godot.py

# 2. 정합성 체크
python tools/verify_godot_project.py
# → ✓ all references resolve  (0 warnings)

# 3. Godot 4.2+ Editor 에서 apps/hero5-godot/ 열고 F5
```

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
  S 상점, Q 퀘스트, I 상태, X 설정, H 도움말, B 전투
  자동 저장: slot 7, 60초 간격
```

---

## 우선순위 다음 작업

### ~~P1: Interpreter opcode 자동 dispatch~~ — ✅ 77/77 완료 (2026-05-08)
- ARM disasm + jumptable 추적 (`tools/h5_extract_opcode_disasm.py`, capstone+lief).
- 산출 `apps/hero5-godot/assets/scenes/opcode_table.json` (77 entries) — interpreter.gd
  외부 로더가 자동 머지.
- BASE_TABLE 잘못된 추측 (Quest 0x31~0x42, Scene_ChangeBgm) → 정확한 매핑으로 수정.
- demo.gd 의 `set_handler` op 들도 정확하게 (0x29 Boss / 0x2a QSwitch / 0x2b Status /
  0x2c Switch).
- scene body 258 export 완료 → demo 진입 시 step() 자동 실행 동작 가능.

### P2: enemy_g 121B layout 의 ATK/DEF 정확한 offset
- 현재 `decode_h5_enemy.py` 의 stat3/stat4 (offset 16/18) 가 65535 인 record 多.
- 작업: Ghidra 로 `BATTLER::SetAtk` 등 setter 함수의 read offset 추적.
  ```bash
  # Ghidra 추가 dump 예시:
  "D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
    "D:/testrepo/work/h5/ghidra_project" Hero5 \
    -process libHeroesLore5.so -noanalysis \
    -scriptPath "D:/testrepo/tools/ghidra" \
    -postScript DumpMonsterLoad.java
  ```
- 검증: enemy_table.json 의 ATK/DEF 가 5–500 범위 자연수.

### ~~P3: Stats UI ATK/DEF 합산 표시~~ — ✅ 완료 (2026-05-08)
- Status panel 의 `AtkDef` Label 에 total_attack/defense + 장비 보너스 분리 표시.
- 인벤 hover: 무기 → ATK diff vs SLOT_WEAPON, 방어구 → DEF diff vs 해당 슬롯
  (투구/장화/일반 방어), 포션 → "HP +30" 미리보기.

### ~~P4: Battle 결과 화면 + 메뉴 페이드~~ — ✅ 완료 (2026-05-08)
- 승리 popup: EXP/Gold/획득 아이템 리스트 + 확인 버튼 (4초 자동 닫힘).
  enemy stats 의 exp/gold 우선, drop_table 25% 확률 1~2개.
- 씬 전환 fade: `scripts/ui/scene_fader.gd` (CanvasLayer + ColorRect tween).
  Title/ClassSelect/Demo 모두 진입 시 fade_in, 나갈 때 change_scene fade-out.

### P5: 자모 인코딩 정밀
- table.dat 의 0x88+ codepoint 와 581 glyph 매핑 룰.
- `Graphic::DrawText` / `Strings::draw` 추가 디컴파일 필요.
- 우회: 시스템 Noto Sans CJK KR (현재 기본).

### P6: Android APK 실 빌드 검증
- Godot Editor → Install Android Build Template → Export.
- `apps/hero5-godot/export_presets.cfg.template` 참조 (arm64-v8a, min SDK 23, target 34).

---

## 파일 위치 빠른 참조

### Phase 2 산출물 (`work/h5/`)
- `vfs_catalog.tsv` — 2,189 entries
- `analysis/asset_names.tsv` — 99.7% 이름 복원
- `analysis/opcode_table.tsv` — 77 opcode 매핑
- `analysis/*.c` — Ghidra 디컴파일 (scn_loader, opcode_dispatch, monster_load, gbm_loader, des_key, interpreter_core 등)
- `converted/sprites/<idx>/frame_NN_*.png` — 3,798 프레임
- `converted/text/_corpus.txt` — 18,837 unique 한글
- `ghidra_project/Hero5/` — Ghidra 프로젝트

### Phase 3 (`apps/hero5-godot/`)
```
project.godot           # autoload 5: GameState/AssetLoader/GameData/Audio/Quest
scenes/                 # 14 씬
  title, class_select, main, demo,
  dialog_box, status_panel, quest_panel, shop_panel, settings_panel, help_panel,
  battle, hud, minimap, map_test
scripts/core/           # 싱글톤 + 게임 로직
  game_state.gd, asset_loader.gd, game_data.gd, audio_manager.gd, quest_system.gd
  map_renderer.gd, character.gd, interpreter.gd, battle_system.gd, save_manager.gd
scripts/ui/             # UI
  title.gd, class_select.gd, demo.gd, main_scene.gd, map_test.gd,
  dialog_box.gd, status_panel.gd, quest_panel.gd, shop_panel.gd,
  battle_ui.gd, hud.gd, minimap.gd, settings_panel.gd, help_panel.gd,
  damage_popup.gd, effect_anim.gd, toast.gd
assets/                 # gitignore — import_to_godot.py 가 채움
  sprites/, gbm/, palettes/, text/, sounds/, fonts/, gamedata/, maps/, scenes/
  sprite_index.json     # VFS name → dir mapping
```

### 임포트 / 검증 도구 (`tools/`)
- `import_to_godot.py` — 5,500+ 자산 자동 변환
- `verify_godot_project.py` — tscn/gd reference 무결성
- `converter/*` — 모든 디코더
- `ghidra/*.java` — 15개 Ghidra 스크립트

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
| I | 상태창 |
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
- [ ] enemy ATK/DEF offset 일부 부정확 (P2)
- [ ] 한글 비트맵 폰트 (시스템 폰트로 우회 중) (P5)
- [ ] SMAF (.mmf) 변환 (OGG 42개로 충당)
- [ ] 자산 이름 7개 / 0.3% 미복원 (게임 영향 없음)
- [ ] Android APK 실 빌드 미검증 (P6, export 가이드만 작성)

---

## 참조 문서

- [`PROGRESS.md`](PROGRESS.md) — 전체 진행 상세 (Phase 2 분석 단계별 + Phase 3 시스템별)
- [`PHASE3_ENGINE.md`](PHASE3_ENGINE.md) — Godot 4 엔진 결정 근거 + 초기 스캐폴드 계획
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법 + Android 빌드
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 설정 템플릿
