# Hero3 SMAF → OGG 변환 가이드 (R73)

> 대상: `work/h3/extracted/snd/*_mf` (33 Yamaha SMAF files, magic `MMMD`)
> 결과물: `work/h3/audio/ogg/*.ogg` (Android `MediaPlayer` 재생 가능)
> 자동화 스크립트: `tools/converter/convert_h3_smaf_pipeline.py`

## 0. 도구 체인 한눈에

```
SMAF (.mf) ─[smaf-converter.jar]→ MIDI (.mid)
                                    │
                                    ├─[timidity 또는 fluidsynth]→ WAV (.wav)
                                    │      + SoundFont (FluidR3_GM.sf2)
                                    │
                                    └─[ffmpeg -c:a libvorbis]→ OGG (.ogg)
```

## 1. 필요 도구 (Windows 11 기준)

### 1.1 Java JRE (이미 있음 ✓)

Hero3 repo 환경엔 `Eclipse Adoptium JDK 21` 이 설치되어 있음 (Phase C 빌드용).
명령행 `java` 가 PATH 에 있는지 확인:
```bash
java -version
# openjdk version "21.x.x" 또는 java version "1.8.x" 면 OK
```

### 1.2 smaf-converter.jar (미설치 ✗)

**다운로드**:
- GitHub: https://github.com/antanas-vasiliauskas/smaf-converter
- Releases 페이지 또는 직접 빌드 (`./gradlew jar`)
- **사전 빌드 JAR** 추천 (빌드 없이 즉시 사용)

**배치**:
```
tools/external/smaf-converter.jar
```
또는 환경 변수 `SMAF_CONVERTER_JAR` 로 지정.

**대안 도구**:
- vavi-sound (Java 라이브러리, smaf-converter 의 backend)
- `smaf2midi` (Wohlstand 의 GitHub repo 는 현재 소멸 ✗)

### 1.3 TiMidity++ 또는 FluidSynth (미설치 ✗)

**TiMidity++** (권장, Windows 안정적):
- 다운로드: https://sourceforge.net/projects/timidity/
- Windows binary release
- PATH 등록 또는 `tools/external/timidity.exe`

**FluidSynth** (대안):
```bash
winget install FluidSynth.FluidSynth
# 또는 scoop install fluidsynth
```

**둘 중 하나**만 있으면 됨. pipeline 스크립트가 자동 감지.

### 1.4 SoundFont (.sf2) (미설치 ✗)

**FluidR3_GM.sf2** (130MB, 일반적 GM):
- 다운로드: https://member.keymusician.com/Member/FluidR3_GM/index.html
- 또는: https://sourceforge.net/p/fluidsynth/wiki/SoundFont/

**OmegaGMGS2.sf2** (대안, 더 풍부한 음색):
- 다운로드: 구글 검색 "OmegaGMGS2 sf2"

**배치**:
```
tools/external/FluidR3_GM.sf2
```
또는 환경 변수 `SOUNDFONT_PATH` 로 지정.

### 1.5 FFmpeg (미설치 ✗)

```bash
winget install Gyan.FFmpeg
# 또는 scoop install ffmpeg
```

설치 확인:
```bash
ffmpeg -version
```

## 2. 설치 후 검증

```bash
# pipeline 도구 상태 확인
python tools/converter/convert_h3_smaf_pipeline.py
```

출력 예 (모든 도구 OK 시):
```
[Tool availability]
  ✓ java               = True
  ✓ timidity           = True
  ✓ fluidsynth         = False
  ✓ ffmpeg             = True
  ✓ smaf_jar_exists    = True
  ✓ soundfont_exists   = True

[Stage capability]
  Full pipeline     : True
```

## 3. 일괄 변환 실행

도구 모두 설치 후:
```bash
python tools/converter/convert_h3_smaf_pipeline.py
```

33 파일 자동 변환 → `work/h3/audio/ogg/*.ogg`. 예상 시간 5-10분.

## 4. Android 통합

변환된 OGG 파일을 Android assets 에 배치:
```bash
# bgm 만 (BGM 만 우선)
mkdir -p android/app/src/main/assets/audio/bgm
cp work/h3/audio/ogg/bgm*.ogg android/app/src/main/assets/audio/bgm/

# sd (sound effect) 도 포함
mkdir -p android/app/src/main/assets/audio/sfx
cp work/h3/audio/ogg/sd*.ogg android/app/src/main/assets/audio/sfx/
```

엔진의 `engine-core` 에 audio playback 인터페이스 추가 (Phase C Step 4d 의 일부):
- `engine-core/src/commonMain/.../AudioPlayer.kt` (interface)
- `android/.../platform/AndroidAudioPlayer.kt` (`MediaPlayer` 구현)
- 이후 iOS 의 `AVAudioPlayer` 도 동일 인터페이스

## 5. 품질 / 음색 트레이드오프

| 항목 | 원본 (SMAF, Yamaha MA-3/5 FM 합성) | 변환 (MIDI+SF2) |
|---|---|---|
| 음색 정확도 | 100% (원곡) | **부정확** (SF2 가 다른 instrument) |
| 멜로디/리듬 | 100% | 100% |
| 길이 | 정확 | 정확 |

→ "비슷한 분위기" 의 BGM 재생산. 원음 100% 재현은 vavi-sound 의 FM 합성기 또는 Yamaha SDK 필요.

## 6. 대안 — 원음 보존 (저장 공간↑)

원본 SMAF 가 작고 (수 KB) Android 가 직접 재생 가능하면:
- Android `MediaPlayer` 는 SMAF 직접 지원 안 함
- 단, JNI/NDK 로 vavi-sound 의 FM synth 포팅 가능 (큰 작업)
- 또는 SMAF → MIDI 만 하고 Android `MidiPlayer` (API 23+) 로 재생 (sf2 plus)

현실적 권장: **SMAF → MIDI → WAV → OGG 가 가장 간단**.

## 7. 사용자 환경 작업 흐름

```bash
# 1. 도구 다운로드 (~ 200MB)
#    - smaf-converter.jar (~ 5MB)
#    - timidity bundle (~ 10MB)
#    - FluidR3_GM.sf2 (~ 130MB)
#    - ffmpeg portable (~ 100MB)

# 2. tools/external/ 에 배치
mkdir -p tools/external
mv ~/Downloads/smaf-converter.jar tools/external/
mv ~/Downloads/FluidR3_GM.sf2 tools/external/

# 3. PATH 추가 (timidity, ffmpeg)
export PATH="/c/Tools/timidity:/c/Tools/ffmpeg/bin:$PATH"

# 4. 일괄 변환
python tools/converter/convert_h3_smaf_pipeline.py

# 5. Android assets 복사
cp work/h3/audio/ogg/bgm*.ogg android/app/src/main/assets/audio/bgm/
cp work/h3/audio/ogg/sd*.ogg android/app/src/main/assets/audio/sfx/

# 6. R74 에서 engine-core 에 AudioPlayer interface 추가
```

## 8. 참고

- [Round 73](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md) — pipeline 스크립트 + DES 8/8 success
- `tools/converter/convert_h3_smaf_pipeline.py` — 도구 상태 자동 감지 + 가능한 만큼 변환
- `tools/converter/convert_h3_smaf.py` — R52 의 SMAF 헤더만 분석 (이전 버전)
