# Hero5 Godot 4 Remake (Phase 3 Scaffold)

영웅서기5 (Heroes Lore 5) Android 리메이크 — Godot 4 LTS 기반.

## 빠른 시작

1. **자산 임포트** (저장소 루트에서):
   ```bash
   python tools/import_to_godot.py
   ```
   → `apps/hero5-godot/assets/` 채워짐 (sprites/gbm/text/sounds/palettes/scenes).

2. **Godot 4 에서 열기**: Godot 4.2+ 실행 → "Import" → 이 디렉토리 선택.

3. **F5 (Run)** → 검증 씬 표시.
   - ←/→ 키로 face_NN 이미지 토글
   - 한글 코퍼스 5줄 프리뷰 표시

## 디렉토리

```
apps/hero5-godot/
├── project.godot
├── scenes/
│   └── main.tscn          # 검증 씬 (face 토글 + 한글)
├── scripts/
│   ├── core/
│   │   ├── asset_loader.gd  # VFS 경로 → res:// 매핑
│   │   └── game_state.gd    # 전역 상태 싱글톤
│   └── ui/
│       └── main_scene.gd
└── assets/                  # import_to_godot.py 가 채움 (.gitignore 가능)
    ├── sprites/<file>/frame_NN_*.png   # 3,798 frames
    ├── gbm/<sub>/<name>.png            # 342 map tiles/faces
    ├── palettes/<id>.json              # RGB565 → JSON RGBA
    ├── text/<file>.json                # 한글 코퍼스
    ├── sounds/<id>.ogg                 # 42 OGG
    └── scenes/index.json               # 258 .scn 메타데이터
```

## Android APK 빌드

1. **Godot 4.2+ Editor** 설치 + 열기 → 이 디렉토리 import.
2. **Project → Install Android Build Template** (gradle build 사용).
3. **Editor Settings** → Export → Android:
   - Java SDK Path = JDK 17 설치 경로 (현재 PC: `C:/Program Files/Microsoft/jdk-21`)
   - Android SDK Path = Android SDK
   - Debug Keystore = (자동 생성된 것 사용)
4. **Project → Export → Add → Android**:
   - `export_presets.cfg.template` 의 설정 참조 (특히 arm64-v8a 만 ✓, min SDK 23, target 34)
5. **Export Project** → `build/Hero5.apk` 생성.

원본 APK 32-bit (armeabi) → **리메이크는 arm64-v8a 64-bit** (현대 Android 14+ 지원).

## 다음 작업 (Phase 3 본 구현)

- [ ] Interpreter opcode → 이벤트 매핑 (현재 164개 opcode 식별, 의미 미해독)
- [ ] Map 렌더러: tile/fgi/obj 레이어 합성 (mapID → tile_NN.gbm + fgi_NN.gbm + obj_NN.gbm)
- [ ] CHAR/HERO 캐릭터 시스템 (스프라이트 + 4방향 이동 애니메이션)
- [ ] 한글 폰트 (kor.fnt 임포트 또는 시스템 폰트 대체)
- [ ] SMAF → OGG 변환 (현재 OGG 만 임포트)
- [ ] 세이브/로드 (원본 DES 암호화 제거 후 평문 JSON)

## 알려진 제한

- 자산 이름 7개 (0.3%) 미복원 — 게임 진행 영향 없음.
- Interpreter opcode 의미 미해독 → 이벤트/대사 자동 실행은 별도 분석 필요.
- DRM/IAP/통신사 SDK 전부 제거됨.

## 참조

- 분석 진행: [`docs/h5/PROGRESS.md`](../../docs/h5/PROGRESS.md)
- 엔진 결정: [`docs/h5/PHASE3_ENGINE.md`](../../docs/h5/PHASE3_ENGINE.md)
