# Hero5 Godot 4 Remake (Phase 3)

영웅서기5 (Heroes Lore 5) Android 리메이크 — Godot 4 LTS 기반.
원본 APK (32-bit armeabi) → **리메이크 arm64-v8a 64-bit** (현대 Android 14+ 정식 지원).

## 빠른 시작

1. **자산 임포트** (저장소 루트에서, 한 번만):
   ```bash
   python tools/import_to_godot.py
   ```
   → `apps/hero5-godot/assets/` 채워짐.

2. **검증** (선택):
   ```bash
   python tools/verify_godot_project.py
   ```
   → tscn/gd 의 모든 `res://` 참조 무결성 체크.

3. **Godot 4.2+** 에서 import → F5 (Run).
   타이틀 → New Game → 클래스 선택 → Demo.

## 게임 흐름

```
Title (로고 + Continue/New Game + 슬롯 메타)
  ├─ New Game → ClassSelect (5 클래스 + STR/DEX/INT/CON)
  │             → Demo
  └─ Continue / Slot 클릭 → Demo (저장 자동 로드)
```

## Demo 컨트롤

| 키 | 기능 |
|---|---|
| WASD / 방향키 | 이동 (충돌 + 자동 인카운터) |
| M / N | mapID / scene 전환 (BGM 페이드 + 캐릭터 자동 배치) |
| P | NPC 마커 스폰 (4색 분류) |
| E | 가까운 NPC 대화 (한글 + 선택지) |
| T | dialog 테스트 |
| S | 상점 (구매/판매) |
| Q | 퀘스트 패널 (활성/완료 + 처치 카운트) |
| I | 상태창 (장비 슬롯 + 인벤 필터/정렬 + 스탯 분배) |
| X | Settings (BGM/SFX 볼륨 / FPS / 전체화면) |
| H | 도움말 |
| B | 즉시 전투 (테스트) |
| C / V | collision / tile attribute 디버그 |
| 1-8 / Shift+1-8 | 슬롯 N 저장 / 로드 |
| F5 / F9 | slot 0 빠른 저장 / 로드 (자동 저장은 slot 7, 60s 간격) |

## 구현된 시스템

| 영역 | 구현 |
|---|---|
| **Map** | 4-layer 합성 (tile/obj/fgi/face), collision 67/67, NPC sprite 자동, warp trigger, mini-map |
| **캐릭터** | 4방향 walk-cycle, 충돌, hero CHAR 클래스 매핑 |
| **전투** | turn 표시, ATK/DEF (장비 stat 합산), skill MP/cooldown, damage popup, 적 sprite, 이펙트 애니, 도주 % 미리보기 |
| **레벨업** | 자동 stat 분배 (클래스별) + 수동 +3 점수 + Lv 5/10/.../40 스킬 해금 |
| **인벤** | 장비 6슬롯 + 더블클릭 사용 (포션/장비) + 5 카테고리 필터 + name/price 정렬 + 비교 툴팁 |
| **상점** | 무기 4슬롯 × 4 offer 구매/판매 + 골드 차감/환불 |
| **퀘스트** | 105 mission + 진행도 (처치 카운트) + 보상 정밀 (rewards.json type-byte 분기) + 토스트 |
| **사운드** | BGM cross-fade + 메뉴별 BGM (Title/ClassSelect/Demo) + SFX |
| **세이브** | 8 슬롯 + 자동저장 (slot 7) + Title 메타 표시 + 우클릭 삭제 |
| **UI** | HUD (상단 HP/SP/Lv/Gold) + dialog 선택지 + 토스트 + 도움말 |
| **Settings** | user://config.cfg 영구 저장 |

자산 카운트:
- 3,798 sprite frames / 342 map gbm / 588 palettes / 453 text JSON / 42 OGG
- 215 스킬 / 1,360 아이템 / 105 퀘스트 / 81 NPC / 75 valid 적 / 67 maps
- 77 opcode 매핑 + 22 Interpreter 핸들러

## 디렉토리

```
apps/hero5-godot/
├── project.godot              # autoload 5개 (GameState/AssetLoader/GameData/Audio/Quest)
├── scenes/                    # 14 씬 (title, class_select, demo, dialog/status/quest/shop/settings/help/battle/...)
├── scripts/
│   ├── core/                  # 싱글톤 + map_renderer/character/interpreter/battle/save_manager
│   └── ui/                    # title/demo/dialog/status/shop/quest/battle/hud/minimap/settings/help/toast/effect/popup
└── assets/                    # import_to_godot.py 가 채움 (.gitignored)
    ├── sprites/<idx_hash>/frame_NN_*.png
    ├── gbm/<sub>/<name>.png
    ├── palettes/<id>.json
    ├── text/<file>.json
    ├── sounds/<id>.ogg
    ├── fonts/{eng,kor}.png + eucKR_index.json
    ├── gamedata/{class_stats,enemy_table,npc_table,items,skills,quests,drops,shops,smiths,quests_text,rewards}.json
    ├── maps/<id>.{json,col.bin,tile.bin}
    ├── scenes/index.json
    └── sprite_index.json       # VFS name → dir mapping
```

## Android APK 빌드

1. **Godot 4.2+ Editor** 열기 → 이 디렉토리 import.
2. **Project → Install Android Build Template** (gradle build).
3. **Editor Settings → Export → Android**:
   - Java SDK Path = JDK 17 (현재 PC: `C:/Program Files/Microsoft/jdk-21`)
   - Android SDK / Debug Keystore 설정
4. **Project → Export → Add → Android** — `export_presets.cfg.template` 참조
   (arm64-v8a 만 ✓, min SDK 23, target 34, gradle build)
5. **Export Project** → `build/Hero5.apk`.

## 알려진 제한 / TODO

- [ ] **Interpreter opcode 의미 매핑 후속** — 77 opcode dispatch 는 console log + 22 핸들러만. 게임 자체 .scn 자동 실행은 미구현 (수동 데모 트리거).
- [ ] **자모 인코딩** — table.dat 의 0x88+ codepoint 가 표준 EUC-KR 아님. 시스템 폰트 (Noto CJK KR) 사용 권장. bitmap 폰트 PNG 시트는 reference.
- [ ] **SMAF (.mmf)** 변환 미구현. OGG 42개 우선 사용. 외부 smaf2mid + timidity + ffmpeg 파이프라인 권장.
- [ ] **자산 이름 7개 (0.3%)** 미복원 — 빌드시 동적 이름 추정. 게임 진행 영향 없음.
- [ ] **DRM / IAP / 통신사 SDK** 전부 제거. Godot In-App Purchasing 신규 도입 미정.
- [ ] **enemy_g 121B layout 의 ATK/DEF 위치 정확도** — stat3/stat4 일부 0xFFFF, BATTLER 추가 분석 시 정정.
- [ ] **opcode dispatch 자동 실행** — `EventProc::onFunction` switch 의 모든 케이스를 GDScript handler 로 1:1 변환 (현재 22 종 / 77 종).

## 참조

- 분석 진행: [`docs/h5/PROGRESS.md`](../../docs/h5/PROGRESS.md)
- 엔진 결정: [`docs/h5/PHASE3_ENGINE.md`](../../docs/h5/PHASE3_ENGINE.md)
- 다음 세션 빠른 재개: [`docs/h5/SESSION_HANDOFF.md`](../../docs/h5/SESSION_HANDOFF.md)
