# Hero5 (영웅서기5) Android 빌드 가이드 (Round 86)

> R86: Distribution build preset 작성 + 빌드 절차 문서화. Godot Editor + Android SDK
> 환경이 필요한 사용자 작업이지만 preset / 가이드는 자율 작성.

## 1. 사전 요구사항

| 도구 | 권장 버전 | 설치 위치 (Windows) |
|---|---|---|
| Godot Engine | 4.2.x LTS (또는 4.3+) | `C:\Godot\` |
| JDK | OpenJDK 17 (Adoptium/Microsoft) | 메모리 `[reference-jdk-paths]` 참조 |
| Android SDK | API 34 (Android 14) | `%LOCALAPPDATA%\Android\Sdk` |
| Android NDK | r23c+ | `%LOCALAPPDATA%\Android\Sdk\ndk\23.2.x` |
| Build Tools | 34.0.0+ | (SDK 내부) |
| Platform Tools | latest (adb 포함) | (SDK 내부) |

**기존 메모리**: [reference-jdk-paths.md](../../C:\Users\Ryu\.claude\projects\d--testrepo\memory\reference_jdk_paths.md):
- 현재 PC: `C:\Program Files\Microsoft\jdk-21\` (JDK 21)
- 집 PC: `C:\Program Files\Adoptium\jdk-21\`
- JDK 21 → JDK 17 호환 OK (Gradle 8.x 가 17 권장이지만 21 작동)

## 2. Godot Editor 초기 설정

1. **Editor 열기**: Godot Engine → `apps/hero5-godot/project.godot` import
2. **Android Build Template 설치**:
   - Menu: `Project → Install Android Build Template`
   - `apps/hero5-godot/android/build/` 디렉토리 자동 생성 (필요시 `git clean -fd android/`)
3. **Editor Settings → Export → Android**:
   - `Android SDK Path`: `%LOCALAPPDATA%\Android\Sdk` (Windows) 또는 `~/Library/Android/sdk` (macOS)
   - `Debug Keystore`: 자동 생성 (Editor 가 build/build.gradle 에서 동작)
   - `Debug Keystore User`: `androiddebugkey` (default)
   - `Debug Keystore Password`: `android` (default)
   - `Java SDK Path` (Godot 4.3+): JDK 17/21 경로

## 3. Export Preset (이미 작성됨, R86)

`apps/hero5-godot/export_presets.cfg` 에 2 preset 포함:

### Preset 0: Android (Debug)
- `export_path="../../build/Hero5-debug.apk"` (repo root 의 `build/` 폴더)
- `gradle_build/use_gradle_build=true` (custom Android build 사용)
- `gradle_build/min_sdk=23` (Android 6.0)
- `gradle_build/target_sdk=34` (Android 14)
- `architectures/arm64-v8a=true` (64-bit only)
- `package/unique_name="kr.eamobile.heroeslore5.remake"`
- `package/name="Hero5 Remake"`
- `version/code=1, version/name="0.1.0-alpha"`
- Permissions: 모두 false (싱글 플레이, 외부 통신 없음)
- Immersive mode: true (시스템 바 숨김)

### Preset 1: Android (Release)
- 동일 설정 + `compress_native_libraries=true` (size 절감)
- Release 빌드는 Keystore 필요 (사용자가 별도 생성, §4)

## 4. Release Keystore 생성 (1회)

Release 빌드는 self-signed keystore 필요:

```powershell
# JDK 의 keytool 사용 (PATH 에 추가되어 있어야 함)
keytool -genkey -v -keystore $env:USERPROFILE\hero5-release.keystore `
        -alias hero5 -keyalg RSA -keysize 2048 -validity 10000
# 비밀번호 + 정보 입력 (Common Name 등). 신중하게 보관.
```

생성 후 Godot Editor:
- Project → Export → "Android (Release)" 선택
- Options 탭:
  - `Keystore → Release`: 위 경로 (`%USERPROFILE%\hero5-release.keystore`)
  - `Keystore → Release User`: `hero5`
  - `Keystore → Release Password`: (생성 시 입력값)

`.keystore` 파일은 git ignore (R86 .gitignore 갱신).

## 5. 빌드 절차

### Debug APK
1. Godot Editor → `Project → Export...`
2. Preset 선택: `Android (Debug)`
3. `Export Project` 클릭 → 파일 다이얼로그에서 경로 확인
4. 빌드 진행 (gradle 다운로드 + 컴파일, 첫 빌드 5-10분, 이후 30s-2분)
5. 산출물: `build/Hero5-debug.apk`

### Release APK
- 위와 동일, preset = `Android (Release)` 선택
- 빌드 시간 더 김 (R8 minification + native lib compression)
- 산출물: `build/Hero5-release.apk`

### 실 디바이스 설치
```powershell
# adb (Android SDK platform-tools) 사용
adb install build\Hero5-debug.apk
# 또는 USB 디버깅 켜진 폰 → Godot Editor 의 "One-click Deploy" 아이콘 (📱)
```

## 6. 검증

설치 후 확인 사항:
- 앱 아이콘 (R86 icon.svg) 표시 — launcher 에 "Hero5 Remake"
- Title scene 진입 + BGM 재생 (Audio.play_bgm(0))
- New Game → ClassSelect (5 클래스, Sorcerer R83 "매직 — 기본+정령 스킬만") → Demo
- Demo 진입 + map 표시 + hero 스폰 + AI tick 동작
- B 키 전투 → fade in (R85) → battle UI → fade out → 보상
- Map warp tile → fade transition (R84)
- F10 → quit-to-title popup (R82)
- Hero HP=0 → GameOver scene (R82) → Continue/Title

## 7. 알려진 이슈 / R87+ 추적

- **Audio SMAF playback** (Audio 카테고리 A=20%): SMAF (.mmf) → MIDI/WAV 변환 미완. 일단 stub bgm (Godot 의 generic audio) 사용.
- **Save device round-trip**: 실 디바이스에서 quick_save → 추출 → Python crosscheck 검증 미완. 메모리 `[reference-h5-des-blocker]` 의 NDK runner 실행이 별도 차단.
- **Sorcerer active skill**: c_csv_skill_04 부재 → 기본 + 정령만 (R83 활성화). 완전 활성화 R87+.

## 8. R86 산출물 요약

| 파일 | 역할 |
|---|---|
| `apps/hero5-godot/export_presets.cfg` | Debug + Release 2 preset, gradle build, arm64-v8a 64-bit |
| `apps/hero5-godot/icon.svg` | App icon (검 + 별 + HERO 5 로고) — 사용자가 별도 교체 가능 |
| `apps/hero5-godot/.gitignore` | export_presets.cfg commit 허용, *.keystore ignore |
| `docs/h5/BUILD_ANDROID.md` | 본 문서 — 빌드 절차 + keystore + 디바이스 설치 |
| `tools/h5_test_export_preset.py` | preset 정합성 검증 (필수 옵션 + version + permissions) |

**진척률 영향**: G 카테고리 (출시 보완) 35% → ~55% (Distribution build 0→60). 종합 +1.6%p 예상.
