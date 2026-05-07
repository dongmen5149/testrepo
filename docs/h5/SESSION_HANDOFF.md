# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

업데이트: 2026-05-08 (P1+P2+P3+P4 완료, 자산 환경 처음부터 복원, .so Ghidra-free 분석)

---

## 30초 요약

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 작업 (P1/P2/P3/P4)** 완료. Title → ClassSelect → Demo 흐름이 동작
가능한 Godot 4 프로젝트 (`apps/hero5-godot/`). 38 GDScript / 14 씬 / 5 싱글톤 /
**OPCODE_TABLE 77/77 (.so ARM disasm 자동 추출, Ghidra 불필요)**.

**verify_godot_project.py: 0 errors / 0 warnings.**

이번 세션 완료 항목:
- **P1 OPCODE_TABLE 77/77** — capstone+lief 로 `EventProc::onFunction` jumptable 추적,
  외부 `opcode_table.json` 자동 생성·로드. PROGRESS hint 의 추측 매핑(Quest, ChangeBgm)
  을 .so disasm 으로 검증·정정.
- **P2 enemy_g 121B layout** — `Map::MapEnemyG_set` + `ByteToInt16` disasm 으로
  HP/MP/ATK/DEF/EXP/Gold offset 모두 검증. 75/166 valid HP (PROGRESS와 일치).
- **P3 Stats UI ATK/DEF** 합산 + 무기/방어구/포션 hover 비교 툴팁.
- **P4 Battle 결과 popup** + Title↔ClassSelect↔Demo 0.3s fade 전환.
- **자산 환경 처음부터 복원** — APK → VFS 2189 → 99.7% 이름 → sprite 421 / pal 588
  / sound 42 / scn body 258 / 한글 18,837 → import_to_godot 통합 실행.

---

## 빠른 재개 (1 커맨드 = 환경 복원)

**가장 흔한 케이스 — assets/ 비어있는 새 클론**:
```bash
# APK 가 있는지 확인 후 (Hero5/영웅서기5(최신폰전용).apk)
# 한 번에 모든 자산 처리:
python tools/h5_extract_pipeline.py     # ← 다음 세션에 이걸 먼저 만들 것 (TODO)
# 또는 단계별:
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

## 다음 우선순위 작업 (즉시 진행 가능)

### P5: 한글 자모 인코딩 정밀 — capstone+lief 로 가능
- 목표: `kor.fnt` 의 581 glyph 와 `table.dat` 의 2350 EUC-KR codepoint 매핑.
- 방법: `tools/h5_extract_opcode_disasm.py` 와 동일한 패턴으로 `Graphic::DrawText`
  / `Strings::draw` / `Font::lookup` 함수 자동 분석.
- **현 상태 영향 없음** — 시스템 폰트(Noto Sans CJK KR)로 우회 중. polish 작업.
- 우선순위: 낮음 (게임 기능 영향 X).

### P6: Android APK 실 빌드 검증 — 외부 환경 필요
- Godot Editor 4.2+ + Install Android Build Template + Export Templates (~1GB) +
  JDK 17 + Android SDK + NDK 필수.
- `apps/hero5-godot/export_presets.cfg.template` 참조 (arm64-v8a, min SDK 23, target 34).
- 이 머신에서 자동화 불가 — 사용자가 GUI 로 진행 필요.

### 다른 가치 있는 polish (자율 진행 가능)
- **scene body 실행 trace** — 258 .scn body 자동 실행 시 어떤 opcode 가 빈번한지
  통계 dump (interpreter.gd 에 stats 모드 추가).
- **damage formula 정확도** — `BATTLER` 클래스의 데미지 계산 함수 disasm 으로
  정확한 공식 추출.
- **SMAF → OGG 변환** — vgmstream 또는 자체 SMAF 디코더 (.mmf 42개).

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

## 이번 세션 새 도구 (Ghidra-free .so 분석)

| 도구 | 역할 |
|---|---|
| `tools/h5_extract_opcode_disasm.py` | EventProc::onFunction jumptable → opcode_table.json 77 entries |
| `tools/h5_event_arg_sizes.py` | Itanium ABI mangle parser → 105 Event_* arg_size |
| `tools/h5_extract_enemy_layout.py` | Map::MapEnemyG_set → 121B record layout 검증 |
| `tools/h5_inspect_enemy_record.py` | 디버그용 raw record dump |
| `tools/h5_batch_sprite.py` | sprite/palette single-argv converter wrapper |

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
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 템플릿
