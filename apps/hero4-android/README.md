# Hero4 Android (apps/hero4-android)

영웅서기4 (환영의검) Android 앱 모듈. 모노레포 구조 (옵션 A) 의 일부.

## 현재 상태 (Phase 1-A 완료)

- ✅ Gradle 프로젝트 스켈레톤 (com.hero4.remake)
- ✅ 자산 배포 완료 (`app/src/main/assets/`):
  - sprites: 209 PNG (BM frames)
  - palettes: 196 _PAL JSON (Hero4 8byte/color)
  - strings: 5 _TXT JSON
  - dialogue_corpus.json (4,078 대사)
  - asset_catalog.json (97 maps + 30 sprite dirs)
- ⏳ Phase 3 대기: Hero3 엔진을 KMM commonMain 으로 분리하여 마운트

## Phase 3 작업

1. Hero3 `android/app/src/main/java/com/hero3/remake/engine/` 를
   `engine/` (KMM commonMain) 으로 옮기기 (게임-agnostic 부분만)
2. Hero3 게임-specific 부분 (캐릭터 스탯/맵 데이터/시나리오) 은 `games/hero3/` 로
3. Hero4 도 같은 commonMain 엔진 사용, 게임 콘텐츠는 `games/hero4/`
4. 이 모듈의 `MainActivity` 가 commonMain `GameView` 마운트

## 빌드 (스켈레톤만 — 의미 있는 게임 화면은 Phase 3 후)

```
cd apps/hero4-android
./gradlew assembleDebug
```
