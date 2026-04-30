---
name: jar-to-android-migration
description: 피처폰용 J2ME(MIDP/CLDC) JAR 파일을 최신 Android 기기에서 실행 가능한 형태로 변환하는 작업 가이드. 디컴파일·전략 선택·API 매핑·빌드·검증의 전 과정을 다룬다. JAR 분석, MIDlet, RecordStore, Canvas, Display, Connector 등 javax.microedition 처리, 모던 Android 제약(스코프드 스토리지, targetSdk, 64bit) 대응 시 사용한다.
---

# J2ME JAR → 최신 Android 마이그레이션 가이드

## 0. 전제 이해

J2ME(피처폰) JAR는 다음 스택 위에서 동작했습니다.

- **CLDC** (Connected Limited Device Configuration) — JVM 서브셋
- **MIDP** (Mobile Information Device Profile) — UI/저장/네트워크 API
- 선택적 JSR: 라이브러리 (예: JSR-184 3D, JSR-135 Media, JSR-75 PIM/FileConnection)

핵심 패키지:
```
javax.microedition.midlet      // MIDlet 라이프사이클
javax.microedition.lcdui       // Canvas, Display, Form, Command, Image
javax.microedition.lcdui.game  // GameCanvas, Sprite, TiledLayer (MIDP 2.0+)
javax.microedition.rms         // RecordStore (영속 저장)
javax.microedition.io          // Connector, HttpConnection
javax.microedition.media       // Player, Manager
```

이 API들은 Android에 **존재하지 않습니다**. Dalvik/ART는 표준 JVM의 서브셋이며 MIDP는 별개 표준입니다. 따라서 어떤 형태로든 **호환 레이어 또는 에뮬레이션**이 필요합니다.

## 1. 전략 선택

| 전략 | 설명 | 장점 | 단점 | 추천 상황 |
|---|---|---|---|---|
| **A. 임베디드 에뮬레이터** | J2ME 에뮬레이터 코어를 Android 앱에 묶고 원본 JAR을 그대로 로드 | 코드 수정 0 | 라이선스(GPL/LGPL) 전염, 성능, JSR 호환성 문제 | 소스 없음 + 단일 게임 포팅 |
| **B. 호환 레이어(shim)** | `javax.microedition.*` API를 Android 위에 다시 구현한 라이브러리에 원본 소스를 재컴파일 | 네이티브 성능, 디버깅 가능 | 디컴파일·shim 구현 비용 | 소스 또는 양호한 디컴파일 결과가 있을 때 |
| **C. 수동 포팅** | 디컴파일 후 Android 네이티브 앱으로 재작성 | 결과물 품질 최고, 모던 UX 적용 가능 | 작업량 최대 | 장기 유지보수 대상 |
| **D. 하이브리드** | 일부는 shim, UI/입력은 네이티브 재작성 | 균형 | 설계 부담 | 게임이 아닌 유틸/도구 앱 |

**1차 결정 기준**: 원본 소스의 가용성 → JAR 안의 manifest와 사용 JSR → 결과물 라이선스 정책.

## 2. 단계별 워크플로우

### 2.1 정찰 (Recon)
1. JAR 추출
   ```bash
   unzip app.jar -d app_extracted
   cat app_extracted/META-INF/MANIFEST.MF
   ```
   `MIDlet-1`, `MicroEdition-Profile`(예: `MIDP-2.0`), `MicroEdition-Configuration`(예: `CLDC-1.1`)을 기록.

2. JAD 파일이 있다면 함께 보존 — 필수 메타데이터(JAR 크기, 실행 진입점)가 들어있음.

3. 디컴파일 — 다음 중 하나를 사용:
   - **JADX** (가장 빠름, GUI/CLI 모두): `jadx -d out app.jar`
   - **CFR**: 가독성 우수, 람다 복원 강함
   - **Procyon**: 오래된 컴파일러 출력에 강함

   여러 도구를 병행해 결과를 교차 비교하면 누락 줄임.

4. **API 사용 인벤토리** 작성 — Grep으로 import 수집:
   ```bash
   grep -rh "import javax.microedition" out/ | sort -u > used-apis.txt
   ```
   `used-apis.txt`가 호환 레이어 범위를 결정합니다.

### 2.2 전략 확정
인벤토리를 보고 1장의 전략 표에서 선택. 일반적으로 **B(shim) 또는 D(하이브리드)** 추천. C는 비용 대비 가치가 매우 높을 때만.

A를 택할 경우 참고 가능한 오픈소스 에뮬레이터:
- J2ME Loader (GPLv3) — 활발히 유지보수
- JL-Mod — J2ME Loader 포크
- MicroEmulator (LGPL)

> 라이선스 호환성을 반드시 검토. GPL 코어를 정적 링크하면 결과물도 GPL이 됩니다.

### 2.3 Android 프로젝트 셋업
- **빌드 시스템**: Gradle (Kotlin DSL 권장)
- **언어**: 원본 Java 유지 가능. UI 레이어만 Kotlin으로 새로 쓰는 것도 좋음.
- **SDK**:
  - `compileSdk` = 최신
  - `targetSdk` = 최신 (Play Store 정책 충족)
  - `minSdk` = 21 또는 24 (현실적 하한)
- **64-bit only**: J2ME JAR은 순수 자바이므로 native ABI 이슈는 없음. 단, 임베디드 에뮬레이터의 native 코어가 있다면 `arm64-v8a`, `x86_64` 모두 포함.

### 2.4 호환 레이어 구현 (전략 B)

핵심 매핑 테이블:

| MIDP API | Android 매핑 | 주의 |
|---|---|---|
| `MIDlet#startApp/pauseApp/destroyApp` | `Activity#onStart/onPause/onDestroy` | MIDlet은 단일 인스턴스 전제. Android는 재생성 가능 → `ViewModel`로 상태 보존 |
| `Display.getDisplay(midlet).setCurrent(displayable)` | `Activity`에서 `setContentView()` 또는 fragment 교체 | `Displayable` 추상화를 `View`/`Fragment`로 |
| `Canvas#paint(Graphics)` | `View#onDraw(Canvas)` 또는 `SurfaceView` 루프 | 60fps 게임이라면 `SurfaceView` + 별도 렌더 스레드 |
| `Canvas#keyPressed/keyReleased(int)` | `View#dispatchKeyEvent` + 가상 키패드 오버레이 | 피처폰 키코드(`KEY_NUM0`~`KEY_NUM9`, `KEY_STAR`, `KEY_POUND`)를 Android `KeyEvent`로 매핑 테이블 작성 |
| `GameCanvas#getKeyStates()` | 폴링용 비트마스크를 입력 컨트롤러가 유지 | 터치→가상 키 변환 후 동일 비트마스크에 반영 |
| `Image.createImage(name)` | `BitmapFactory.decodeStream(assets.open(name))` | 자원은 `assets/`에 평탄화하여 배치. 경로 슬래시 보존 |
| `Sprite`, `TiledLayer` | 직접 구현 (Android에 없음) | 변환 plumbing이 가장 큰 작업. 기존 J2ME Loader의 구현을 참고 |
| `RecordStore.openRecordStore(name, true)` | `Context.getFilesDir()` 하위 단일 파일 또는 Room | record ID 시멘틱(추가 시 단조 증가, 삭제 후에도 ID 재사용 X) 보존 필수 |
| `Connector.open("http://...")` → `HttpConnection` | OkHttp 또는 `HttpURLConnection` | `usesCleartextTraffic="true"` 또는 network security config로 cleartext 허용 (가능하면 https 강제) |
| `Connector.open("socket://...")` | `java.net.Socket` | 메인 스레드 호출 금지 — `Dispatchers.IO` |
| `Player`(media) | `MediaPlayer` 또는 `ExoPlayer` | MIDI는 ExoPlayer가 미지원 — 별도 신디 라이브러리 필요 |
| `System.getProperty("microedition.platform")` | shim에서 고정 문자열 반환 | 일부 게임이 분기에 사용 |

### 2.5 자원 마이그레이션
- JAR 내부 리소스(이미지, 사운드, 데이터 파일) → `app/src/main/assets/` 로 평탄 복사
- 원본 경로 구조 유지 (코드의 `getResourceAsStream("/sprites/hero.png")` 호환)
- 9-patch나 vector drawable로의 변환은 **하지 않음** — 원본 비트맵을 그대로 쓰고 렌더링 시점에 스케일링

### 2.6 입력 UX
피처폰 키패드를 Android에서 재현하는 두 가지 방법:

1. **가상 키패드 오버레이** (게임에 적합): 화면 하단에 12키 + 방향키 + soft1/2 그래픽. 각 터치 → MIDP 키코드로 변환.
2. **제스처/탭**: 단순 메뉴형 앱은 화면 직접 탭으로 재매핑.

해상도: 원본이 `240x320` 같은 작은 캔버스라면 가상 캔버스에 그린 뒤 디바이스 화면 비율에 맞게 letterbox 스케일.

### 2.7 모던 Android 제약 대응
- **스코프드 스토리지** (Android 11+): 외부 저장소 직접 경로 접근 불가. RecordStore 대체는 **반드시 internal storage**(`Context.getFilesDir()`).
- **백그라운드 제한**: MIDlet의 무한 루프는 Activity가 백그라운드일 때 자동 멈춤 — `onPause`에서 렌더 스레드 일시정지 처리 필수.
- **권한**: `INTERNET` 외에 카메라/마이크/위치 등 JSR 사용분 매핑 시 런타임 권한.
- **edge-to-edge / display cutout**: targetSdk 35+는 edge-to-edge 강제. 캔버스 영역에 inset 처리.
- **back gesture**: 하드웨어 back 키 → MIDP soft2 매핑 시 predictive back과 충돌 주의.

### 2.8 빌드 파이프라인
```
[원본 .jar] → [unzip + decompile] → [Java 소스 + assets]
                                          ↓
                          [Android Gradle 모듈: app]
                                          ↓
                          [shim 모듈: midp-compat]
                                          ↓
                          [./gradlew assembleRelease]
                                          ↓
                                       [.apk/.aab]
```

권장 모듈 구성:
- `:app` — Android `Activity`, 가상 키패드, ViewModel
- `:midp-compat` — `javax.microedition.*` shim (순수 Java/Kotlin)
- `:original` — 디컴파일된 원본 소스 (수정 최소화, shim에 컴파일)

## 3. 검증 매트릭스

| 항목 | 도구/방법 | 합격 기준 |
|---|---|---|
| 빌드 | `./gradlew assembleDebug` | 0 에러 |
| Lint | `./gradlew lint` | 새 critical 0 |
| MIDlet 라이프사이클 | 회전·홈·복귀 시 상태 보존 | RecordStore 잔존, 게임 진행도 유지 |
| 입력 매핑 | 모든 키 12개 + soft 2개 | 원본과 동일 동작 |
| 그래픽 | 픽셀 비교 (동일 입력 후 스크린샷) | 허용 오차 내 |
| 영속성 | 강제 종료 후 재기동 | 데이터 유지 |
| 네트워크 | 원본의 `http://` 호출 | https 우선, cleartext 명시 시에만 허용 |
| 다양 화면 | 360x640, 1080x2400, 폴더블 | 크래시 0, 가독성 유지 |
| API 레벨 | minSdk 21, targetSdk 최신 | 모두 정상 |

## 4. 흔한 함정

- **익명 클래스 디컴파일 깨짐** — Procyon으로 재시도, 그래도 깨지면 수동 복원.
- **`Class.forName` 동적 로딩** — Android에서는 R8/ProGuard에 의해 클래스명이 난독화됨. `keep` 규칙 필요.
- **`Thread.sleep` 기반 게임 루프** — Android에서는 `Choreographer` 또는 `SurfaceView` 렌더 스레드로 교체.
- **MIDP 좌표계는 정수** — Android `Canvas`는 부동소수점. 누적 오차 주의.
- **`Image.getRGB`** — Android `Bitmap.getPixels`로 가능하지만 byte order(ARGB vs ABGR) 주의.
- **`RecordStore` 동시성** — MIDP는 단일 스레드 가정이 흔함. Android 멀티스레드 환경에서 락 추가.

## 5. 참고 (사용자가 제공한 URL을 우선 활용)

researcher 에이전트가 `docs/sources.md`의 URL을 기반으로 조사합니다. 본 문서는 일반 가이드이며, 구체적 라이브러리 버전·API 변경 사항은 항상 사용자가 제공한 최신 자료로 검증하십시오.

## 6. 체크리스트 (요약)

- [ ] JAR/JAD 정찰 및 manifest 보존
- [ ] 디컴파일 (JADX + CFR 교차)
- [ ] `used-apis.txt` 작성
- [ ] 전략 결정 (A/B/C/D) 및 라이선스 검토
- [ ] Android 프로젝트 + `:midp-compat` 모듈 셋업
- [ ] 매핑 테이블의 모든 사용 API 구현
- [ ] 자원을 `assets/`로 평탄 이전 + 경로 호환
- [ ] 가상 키패드 / 입력 매핑
- [ ] RecordStore → internal storage
- [ ] 네트워크 정책 (cleartext, https)
- [ ] 라이프사이클·회전 검증
- [ ] 다양 화면/Android 버전 검증
- [ ] reviewer 에이전트로 최종 리뷰
