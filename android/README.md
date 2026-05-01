# Hero3 Remake — Android 앱

원본 한국 SK텔레콤 GVM/Clet 피처폰 게임 "영웅서기3-운명의수레바퀴"를 모던 Android로 리메이크하는 프로젝트의 클라이언트 모듈.

## 현재 상태 (스켈레톤)

- ✅ Kotlin + Gradle 8.7 / AGP 8.5.2 / compileSdk 35 / minSdk 24
- ✅ 240×320 가상 캔버스 + letterbox 스케일 (`GameView`)
- ✅ 가상 키패드 오버레이 (D-pad + OK + Soft1/Soft2) (`VirtualKeypadView`)
- ✅ 하드웨어 키 + 터치 통합 입력 (`InputController`)
- ✅ Scene 추상화 + 데모 `SpriteGalleryScene`
- ✅ 변환된 자산 번들: 479 PNG + 9 텍스트 JSON + 216 팔레트 JSON
- ⚠️ Ghidra 분석 후 추가 예정: 다중 프레임 스프라이트, 캐릭터 애니메이션, 맵, 이벤트 스크립트

## 빌드 전 필요 사항

1. **Android Studio** (Hedgehog 2023.1.1 이상 권장) 또는
2. **Android SDK** 단독 + **Gradle 8.7+** + **JDK 17**

## Gradle Wrapper 초기 셋업

저장소에는 `gradle-wrapper.jar`를 커밋하지 않았습니다 (바이너리). 한 번만 실행:

### Android Studio
프로젝트를 열면 자동으로 wrapper jar가 다운로드됩니다.

### CLI
```bash
cd android
gradle wrapper --gradle-version 8.7
```

이후 `./gradlew` 명령어로 모든 빌드를 진행합니다.

## 빌드

```bash
cd android
./gradlew :app:assembleDebug
```

APK는 `app/build/outputs/apk/debug/app-debug.apk` 에 생성됩니다.

## 실행

에뮬레이터/기기 연결 후:

```bash
./gradlew :app:installDebug
adb shell am start -n com.hero3.remake/.MainActivity
```

## 자산 갱신

원본 자산이 업데이트되거나 변환기가 개선되면:

```bash
# 1) 원본 JAR 다시 추출 (work/extracted)
unzip -o ../Hero3/0103EFD4.jar -d ../work/extracted

# 2) 자산 변환 실행
cd ../tools/converter
python convert_all.py ../../work/extracted ../../work/converted

# 3) Android assets/ 갱신
python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
```

## 입력 매핑

| 키 | MIDP 매핑 | 역할 (현재 데모) |
|---|---|---|
| ▲▼ / D-pad UP/DOWN | K_UP/DOWN | 카테고리 전환 |
| ◀▶ / D-pad LEFT/RIGHT | K_LEFT/RIGHT | 스프라이트 전환 |
| OK / DPAD_CENTER / Enter | K_OK | 4× 줌 토글 |
| L (Soft1) / Menu | K_SOFT1 | 한국어/영어 라벨 토글 |
| R (Soft2) / Back | K_SOFT2 | (예약) |

## 구조

```
android/
├── settings.gradle.kts            # 루트 빌드 설정
├── build.gradle.kts               # 플러그인 정의
├── gradle.properties
├── gradle/wrapper/                # wrapper properties (jar는 user 환경에서 생성)
└── app/
    ├── build.gradle.kts
    └── src/main/
        ├── AndroidManifest.xml
        ├── res/
        │   ├── values/strings.xml          # 기본 (영어)
        │   ├── values-ko/strings.xml       # 한국어
        │   └── values/themes.xml
        ├── assets/
        │   ├── sprites/<cat>/*.png         # 변환된 frame 0 스프라이트 479장
        │   ├── strings/*.json              # 원본 텍스트 테이블
        │   └── palettes/*.json             # 원본 팔레트
        └── java/com/hero3/remake/
            ├── MainActivity.kt
            ├── engine/
            │   ├── GameView.kt              # SurfaceView + 렌더 루프 + letterbox
            │   ├── InputController.kt       # MIDP 키 비트마스크
            │   ├── VirtualKeypadView.kt     # 가상 키패드
            │   └── Scene.kt
            └── scene/
                └── SpriteGalleryScene.kt    # 데모: 스프라이트 갤러리
```

## 다음 단계

- [ ] 다중 프레임 _bm 디코더 추가 (Ghidra 분석 후)
- [ ] 애니메이션 시스템 (`_cif` 파싱)
- [ ] 맵 렌더러 (`_mp` 디코더)
- [ ] 이벤트 인터프리터 (`_scn`)
- [ ] HD 리마스터 자산 슬롯 (Real-ESRGAN 4× 업스케일 PNG)
- [ ] 다국어 string resource 풀 (현재 첫 7개만 영어)
- [ ] 사운드 (`_mf` SMAF → OGG 변환 후 `MediaPlayer`)
