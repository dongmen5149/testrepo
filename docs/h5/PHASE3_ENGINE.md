# Hero5 Phase 3 — 리메이크 엔진 결정

## 입력 자산 (Phase 2 결과)

| 카테고리 | 파일/항목 | 비고 |
|---|---:|---|
| 스프라이트 PNG | 426 파일 / **3,798 frame** | 4-bit / 8-bit indexed → RGBA8888 PNG |
| 팔레트 _pa | 557 파일 (RGB565 LE) | 외부 분리, 스프라이트가 참조 |
| 사운드 SMAF + OGG | 84 (42+42) | SMAF→OGG 변환 추가 작업 필요 |
| 한글 코퍼스 | 18,837 unique strings | EUC-KR → UTF-8 |
| 자산 이름 | **2,182 / 2,189 (99.7%)** | `c/<dir>/<file>.<ext>` 경로 복원 |
| 애니메이션 스크립트 | 300 파일 (`19 19` / `20 20` sentinel) | 7B 레코드 dominant |
| 맵 scene `c/map/%05d.scn` | 약 285개 | 게임 메인 맵 데이터 |
| 캐릭터/장비/스킬 csv | 30+ | game balance + i18n |

총 변환 자산: **~12 MB**, 텍스트 + 스프라이트가 주류.

---

## 후보 엔진 비교

| 항목 | Unity 2022 LTS | Godot 4 | 자체 Kotlin/Compose |
|---|---|---|---|
| Android arm64 | ✅ 빌드 자동 | ✅ 자동 | ✅ |
| iOS 동시 | ✅ | ✅ | ❌ (Compose Multiplatform 가능하나 미성숙) |
| 2D sprite/anim | ✅ Unity 2D | ✅ AnimatedSprite2D | 직접 Canvas 그리기 필요 |
| 한글 폰트/입력 | ✅ TextMeshPro | ✅ DynamicFont | ✅ 네이티브 |
| 자산 임포트 파이프 | AssetImporter (커스텀 필요) | 직접 로드 (단순) | 직접 로드 |
| Hot-reload / 워크플로 | 우수 (Unity Editor) | 우수 (Godot Editor) | 빌드 사이클 김 |
| 외부 의존 패키지 무게 | 50–100 MB Unity Engine | 30–50 MB | 5–10 MB |
| IAP / 알림 / 광고 | Unity IAP/Ads 풀세트 | Plugin 필요 | 네이티브 직접 |
| 학습/디버깅 비용 | 중 (이미 있는 듯한 가정) | 중 | 낮 (개발자 친숙) |
| 라이선스 | 무료 (~수익 임계 이하) | MIT 완전 자유 | 무료 |

---

## 결정 매트릭스

게임 특성 평가:
- **2D 픽셀 인덱스 그래픽 (4/8-bit)** — 모든 엔진이 충분히 처리.
- **OpenGL ES 1.x fixed-function 원본** — 현대 엔진 어떤 것도 동등하게 표현 가능.
- **싱글플레이 RPG** — 네트워크/실시간 동기 부담 없음.
- **i18n 한국어 메인** — 폰트/EUC-KR 매핑만 정리되면 OK.
- **자산 이름 99.7% 복원 + 명확한 디렉토리 구조** — 변환 파이프라인 만들기 쉬움.

### 권장: **Godot 4** (1순위) / **Unity 2022 LTS** (2순위)

**Godot 4 권장 이유**:
1. **자산 흐름이 단순** — `res://` 경로에 바로 PNG/JSON 넣고 코드에서 `load()`. Unity 의 `.meta` 파일 + AssetImporter 작성 부담 없음.
2. **2D 우선** — TileMap / AnimatedSprite2D / AnimationPlayer 가 1차 시민. Hero5 의 sprite/anim 구조와 1:1 매핑.
3. **빌드 무게 가벼움** — APK 30 MB 안팎 (Unity 80 MB+). 원본 17 MB APK 의 정신 유지.
4. **MIT 라이선스** — 향후 어떤 형태로 배포해도 부담 없음.
5. **현대 GDScript 또는 C#** — 둘 다 지원, 팀 선호 따라 선택.

**Unity 가 나은 경우**:
- 이미 Unity 라이선스/노하우가 있고 IAP/광고 SDK 강제 사용 필요 시.
- iOS 빌드 검증 인프라 (TestFlight, Xcode CI) 가 이미 있을 때.

---

## Phase 3 진입 후 첫 일주일 작업 안내

### 3-A. 프로젝트 스캐폴드
```
apps/hero5-godot/
├── project.godot
├── assets/                 # 자동 생성 컨버터가 채움
│   ├── sprites/<category>/<id>.png
│   ├── palettes/<id>.json
│   ├── sounds/<id>.ogg
│   ├── text/<file>.json    # 한글 코퍼스
│   └── maps/<id>.scn       # 원본 .scn 변환 후 Godot scene
├── scripts/
│   ├── core/                # 게임 루프, 상태 머신
│   ├── ui/                  # 메뉴/HUD
│   └── battle/              # 전투 시스템
└── tests/
```

### 3-B. 자산 임포트 파이프라인 (Python → Godot import)
1. `tools/converter/convert_h5_to_godot.py` 작성
   - asset_names.tsv 의 경로 그대로 사용 (`c/sp/img0/000.mgr` → `assets/sprites/img0/000.png`)
   - `convert_h5_sprite.py` 출력을 그대로 사용 (이미 PNG 화 완료)
   - `convert_h5_pa.py` 출력은 JSON 색 배열로 변환 (Godot 에서 ShaderMaterial / Color array)
2. SMAF → OGG 일괄 변환 (Hero3 의 변환기 재활용 가능 시)
3. `c/map/%05d.scn` 디코더 — 가장 큰 미해결 작업. ~285개 맵.

### 3-C. 엔진 부트스트랩
- Godot 프로젝트에 main scene + viewport 설정
- AnimatedSprite2D 로 frame_00..frame_NN 재생 테스트
- 한글 텍스트 표시 테스트 (kor.fnt → Godot DynamicFont)

### 3-D. MVP 목표 (1개월) — ✅ 모두 달성 (2026-05-08)
- ✅ 타이틀 → 클래스 선택 → Demo 흐름
- ✅ 캐릭터 4방향 이동 + 충돌 + walk-cycle
- ✅ Map 4-layer 합성 + collision + warp + NPC sprite
- ✅ 한글 대사 표시 (typewriter + 선택지)
- ✅ 전투 (4 액션 + skill MP/cooldown + damage popup + 이펙트 + 도주 % + turn 표시)
- ✅ 레벨업 (자동 stat + 수동 stat_points + 스킬 해금)
- ✅ 인벤 (장비 6슬롯 + 더블클릭 사용 + 필터/정렬 + 비교 툴팁)
- ✅ 상점 / 퀘스트 / 세이브 / HUD / Mini-map / Settings / 도움말

### 3-E. 본구현 단계별 진척 (2026-05-08)

| 영역 | Phase | 구현 |
|---|---|---|
| 임포트 파이프라인 | ✅ 완료 | `tools/import_to_godot.py` (5,500+ 자산) + `sprite_index.json` |
| 임포트 검증 | ✅ | `tools/verify_godot_project.py` (0 errors) |
| 캐릭터 / Map / 충돌 | ✅ | character.gd / map_renderer.gd (collision 67/67) |
| Interpreter | ⚠ 부분 | 22/77 opcode 핸들러 + 22 종 dispatch |
| 전투 / 스킬 / 적 stat | ✅ | battle_system.gd + 215 skill + 75 valid enemy |
| Quest / 상점 / 인벤 | ✅ | 105 quest + drop 252 + items 1,360 |
| 사운드 (BGM cross-fade) | ✅ | audio_manager.gd, OGG 42개 |
| 세이브 (8 슬롯 + auto) | ✅ | save_manager.gd, 메타 포함 |
| Title / ClassSelect / HUD | ✅ | 14 씬 통합 |
| Settings / 도움말 / 토스트 | ✅ | 영구 저장 (user://config.cfg) |
| Android APK 빌드 | ⚠ | `export_presets.cfg.template` 작성, 실 빌드 미검증 |

---

## 미해결 / 차후 처리

| 우선순위 | 항목 | 상세 |
|---|---|---|
| **P1** | Interpreter opcode 자동 dispatch (실 .scn 실행) | 22/77 → 77/77 확장 |
| P2 | enemy_g 121B layout ATK/DEF 정확한 offset | BATTLER setter 추적 |
| P3 | Status UI ATK/DEF 합산 + 방어구 비교 | total_attack/defense 라벨 |
| P4 | Battle 결과 화면 + 메뉴 페이드 | 보상 popup + 0.3s 전환 |
| P5 | 한글 자모 인코딩 (table.dat → 581 glyph 매핑) | DrawText/Strings::draw 추적 |
| P6 | Android APK 실 빌드 검증 | Godot Editor + device 테스트 |
| 낮음 | scn body opcode 의미 (164 unique) | 이미 22 종 분석 완료 |
| 낮음 | TINY_META 7-byte record 의미 | 7/356 strict match 만 |
| 낮음 | 잔여 7개 자산 이름 (0.3%) | 빌드 타임 동적 이름 추정 |
| 낮음 | SMAF (.mmf) → OGG 변환 | 외부 도구 필요 |

다음 세션 빠른 재개: [SESSION_HANDOFF.md](SESSION_HANDOFF.md)
- **DRM / IAP** — 통신사 SDK 전부 제거. 신규 IAP 는 Phase 3 후반.
