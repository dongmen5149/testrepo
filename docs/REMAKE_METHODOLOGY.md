# 리메이크 방법론 (Remake Methodology)

> 이 저장소에서 "리메이크" 라는 단어가 의미하는 것 — 그리고 영웅서기 시리즈가 실제로 어떻게 진행되었는지의 기록.

---

## 1. "리메이크" 의 정의

**최신 Android 와 iPhone 에서, 사용자가 앱스토어에서 바로 다운받아 실행할 수 있는 형태로 다시 만드는 것.**

즉 다음은 **리메이크가 아니다**:

- ❌ PC 에뮬레이터에서 원본 JAR/APK 를 돌리는 것
- ❌ Java/Kotlin shim 으로 원본 바이너리를 흉내 내는 것
- ❌ 안드로이드 구버전 (예: API 23) 만 지원하는 빌드
- ❌ 사이드로딩 전용 APK (Play Store 업로드 불가)
- ❌ 개발자 PC 에서만 실행되는 데모

리메이크의 결과물은 다음을 모두 만족해야 한다:

| 항목 | 요구사항 |
|---|---|
| **Android** | Google Play Store 업로드 가능. `targetSdk` 가 Play 정책 최신 (현 시점 34+). 64-bit ABI 필수. 스코프드 스토리지 / 백그라운드 제한 / 권한 모델 모두 준수 |
| **iOS** | App Store 업로드 가능. 최신 Xcode 빌드 통과, 최신 iOS 지원 (실기 + TestFlight + 심사) |
| **모노레포 + 게임별 별도 출시** | 각 게임은 독립 번들 (`com.hanbit.hero3` / `com.hanbit.hero4` / `com.hanbit.hero5`). 공유 엔진은 KMM commonMain |
| **사용자 경험** | 가상 키패드 + 한국어 + 추후 i18n. 원본 화면비 보존 + 레터박스 스케일. HD 자산 슬롯-인 |
| **법적 준비** | 한빛소프트 / 원 저작권자와의 라이선스/권리 정리. SKT TAD SDK·통신사 IAP·DRM 코드는 **모두 제거** |

이 기준에 부합하지 않으면 "프로토타입" 이거나 "분석 산출물" 이지 리메이크라고 부르지 않는다.

---

## 2. 핵심 전략 — Strategy C (자산 추출 + 엔진 재구현)

원본 바이너리는 다음 중 하나의 형태로 묶여 있다:

| 형태 | 내용물 | 예시 |
|---|---|---|
| **JAR (피처폰 시대)** | SKT GVM/Clet 환경의 **ARM Thumb 네이티브 .bin** + Java/WIPI bytecode + 자산 | `Hero3/0103EFD4.jar`, `Hero4/010100D4.jar` |
| **APK (스마트폰 초기)** | DEX (Java) + native `.so` (ARMv5TE 32-bit) + VFS 컨테이너 + DRM | `Hero5/영웅서기5(최신폰전용).apk` |

두 형태 모두 **에뮬레이터/shim 으로 우회 불가**:

- JAR 의 `client.binNNNNNN` 은 ARM Thumb 네이티브 코드 (Java VM 위에서 도는 게 아님). SKT GVM 런타임이 없으면 실행 불가, 그 런타임은 더 이상 사용 가능하지 않음
- APK 의 `.so` 는 32-bit ARMv5TE only — 현대 64-bit Android 에서 차단. 또한 OpenGL ES 1.x 고정 파이프라인이라 modern GLES/Vulkan 환경과 비호환
- 양쪽 다 통신사 DRM (SKT TAD 등) 이 박혀 있어 그대로는 출시 불가

따라서 **"원본 바이너리 그대로 돌리는 모든 경로는 비현실적"** — 이것이 모든 게임에 공통되는 출발점.

대신 다음을 한다:

1. 원본에서 **자산만 추출** (스프라이트, 팔레트, 맵, 대사, 사운드, 시나리오 스크립트, 폰트)
2. 원본 바이너리를 정찰·디스어셈블해 **자산 포맷과 게임 로직을 문서화**
3. 그 문서를 입력으로 **모던 Kotlin/Compose Multiplatform 엔진을 새로 작성**
4. 동일한 자산 + 동일한 시나리오 + 새 엔진 = "원본과 같은 게임" 인 척하는 다른 코드베이스

세이브 데이터는 호환되지 않는다 (원본의 RecordStore 포맷과 새 저장 포맷이 다름).

---

## 3. 공통 워크플로우 (모든 게임)

```
[원본 아카이브] → [언팩] → [자산 변환] → [정찰/디스어셈블]
                                              ↓
                                   [포맷·로직 문서화]
                                              ↓
                                  [엔진 재구현 (KMM)]
                                              ↓
                          [Android 빌드] + [iOS 빌드] → [스토어 업로드]
```

### Phase A — 자산 변환 (자동화 가능)
- 원본 → JSON / PNG / OGG 로 변환
- 게임별 `tools/converter/` 의 디코더가 처리
- 결과: `work/<id>/converted/` + Android 모듈 `assets/` 에 배포

### Phase B — 바이너리 정찰
- ASCII / EUC-KR 문자열 추출 → 함수 위치 추정
- Ghidra GUI 로 핵심 함수 디컴파일
- 자산 포맷 미해독 부분을 풀어서 Phase A 디코더 보강
- 게임 로직 (스탯·전투·이벤트) 의미 추출

### Phase C — 엔진 재구현
- Kotlin + Compose Multiplatform commonMain
- 240×320 (피처폰) 또는 320×480 (초기 스마트폰) 가상 캔버스 + 레터박스
- 가상 키패드 (소프트웨어 D-Pad)
- Scene 시스템 (MainMenu / MapWalk / Battle / Dialogue / Inventory / ...)
- 한국어 기본 + i18n hook

### Phase D — 출시
- Android: Play Store, 게임당 별도 Bundle ID
- iOS: App Store, 동일 코드베이스에서 ComposeUIViewController 마운트
- TestFlight beta → 심사 → 정식 출시

---

## 4. JAR 케이스 vs APK 케이스 — 작업이 어떻게 갈리는가

같은 "엔진 재구현" 이지만 **시작 지점의 난이도와 도구 선택이 완전히 다르다**.

### 4.1 JAR (피처폰 — Hero3, Hero4)

| 단계 | 내용 | 난이도 |
|---|---|---|
| 언팩 | `unzip` 한 번 | 자동 |
| 자산 식별 | 디렉터리 명이 `/hero/`, `/boss/`, `/map/` 등 카테고리 구분되어 있음. 하지만 포맷은 사문화된 한빛 내부 포맷 (`_bm`, `_cif`, `_pa`, `_mp`, `_scn`, `_dat` 등) | 중-고 |
| 자산 디코딩 | RGB565 팔레트 + 4-bit/8-bit 인덱스 + 마법 바이트 (0x0b/0x0c) + LE 헤더. **Ghidra 로 native 디코더를 분석해야 함** (예: Hero4 `FUN_00010fe4`) | 고 |
| 바이너리 정찰 | `client.binNNNNNN` 은 **순수 ARM Thumb 코드, 심볼 stripped, ELF 섹션 없음 (raw flat)**. Capstone + 수동 디스어셈블 | **최고** |
| 시나리오 스크립트 | `_scn` opcode 시퀀스 — 자체 가상 머신. opcode 의미를 한 개씩 역공학 | 고 |
| 텍스트 인코딩 | EUC-KR | 자동 |
| 사운드 | Yamaha SMAF/MMF — 모던 OS 미지원 → OGG/MP3 변환 필요 | 미해결 |
| 화면 | 240×320 4-bit 또는 8-bit 인덱스 컬러 | 자동 |
| 진행상황 (Hero3) | Phase A ✅ + Phase B 1차 완료 + Android 8개 씬 + i18n + HD ✅ + Phase C/D 대기 |
| 진행상황 (Hero4) | Phase A ✅ + Phase B 일부 (`_PAL`/`_EXD`/`_MAP_M extras` 미해독) + Android 모듈 placeholder + Phase C 대기 |

**JAR 케이스의 핵심 어려움**: 원본 바이너리에 **심볼이 없고 ELF 헤더도 없다**. 함수 경계를 string xref 만으로 추정해야 함. 그래서 `tools/recon/extract_strings.py` + `find_xrefs.py` + `find_pic_xrefs.py` + `find_base.py` 가 게임-aware 로 동작해야 한다 (현재 그렇게 되어 있음).

### 4.2 APK (스마트폰 초기 — Hero5)

| 단계 | 내용 | 난이도 |
|---|---|---|
| 언팩 | `unzip` (APK = ZIP) | 자동 |
| 자산 식별 | `assets/data.vfs.mp3` 라는 **단일 컨테이너 (VFS)** 안에 모든 자산이 인덱스+오프셋으로 패킹. 확장자 `.mp3` 는 위장 | 중 |
| VFS 언팩 | 헤더에서 인덱스 테이블 파싱 → 2189개 entry 추출 → 해시/타입으로 ogg/bin/txt 분류 | 자동 (`tools/h5_vfs_unpack.py`) |
| 자산 디코딩 | 텍스트는 UTF-8/EUC-KR 혼재. 사운드는 OGG 그대로 (변환 불필요). 스프라이트/맵은 자체 포맷 (Midas 엔진) | 중 |
| 바이너리 정찰 | **`.so` 는 ELF + debug symbol 보존됨.** Ghidra 가 함수명 그대로 인식. JNI export 18개 (`nativeInitKernel`, `nativeStartApp`, `nativeLoop` 등) 가 분석 진입점 | **중** (JAR 보다 쉬움) |
| 시나리오 스크립트 | Midas 엔진 자체 포맷이지만 심볼이 살아 있어서 함수 의미 빠르게 식별 | 중 |
| 텍스트 인코딩 | UTF-8 / EUC-KR 혼재 — 75,284 추출 / 35,931 unique | 자동 |
| 사운드 | OGG — 그대로 사용 가능 | 자동 |
| 화면 | OpenGL ES 1.x 고정 파이프라인 — Compose Multiplatform 으로 재현 시 텍스처/매트릭스 변환 작업 필요 | 중 |
| ABI 차단 | armeabi (ARMv5TE 32-bit) — 현대 Android 14+ 차단. **원본 .so 재사용 경로는 막힘** → JAR 케이스와 동일하게 자산만 재활용 | 결정적 |
| DRM | SKT TAD SDK + 통신사 IAP 모듈 — 전부 제거 | 자동 |
| 진행상황 (Hero5) | Phase 2-A 완료 (sprite 3,798 frame + 텍스트 75,284개). VFS 100% 풀림. Phase B (Midas 함수 분석) 대기 |

**APK 케이스의 핵심 어려움이 JAR 보다 낮은 이유**:
1. 디버그 심볼이 살아 있어 Ghidra 가 함수명을 안다
2. 사운드는 이미 OGG (변환 불필요)
3. 자산이 VFS 한 덩어리라 unpack 도구만 한 번 만들면 끝
4. JNI export 가 표준 패턴 (`nativeInit*`, `nativeLoop`, `nativeOn*Touch`) — 진입점 탐색이 짧음

**그럼에도 자산만 재활용하는 이유**: 32-bit ABI 차단 + DRM + GLES1 의존성. 원본 `.so` 를 그대로 묶어 출시하면 Play Store 가 거부하고, 거부를 피해도 사용자 폰에서 안 돈다.

### 4.3 차이 요약 (한 표)

| 비교축 | JAR (Hero3/4) | APK (Hero5) |
|---|---|---|
| 패키지 포맷 | ZIP (피처폰 JAR) | ZIP (Android APK) |
| 코드 형태 | ARM Thumb raw flat binary | ELF `.so` (32-bit) + DEX |
| 심볼 | **없음** (stripped) | **있음** (debug info 보존) |
| 자산 레이아웃 | 카테고리별 디렉터리 | 단일 VFS 컨테이너 |
| 사운드 | SMAF/MMF (변환 필요) | OGG (그대로) |
| 그래픽 | 4-bit/8-bit indexed RGB565 | OpenGL ES 1.x |
| 텍스트 인코딩 | EUC-KR | EUC-KR + UTF-8 혼재 |
| 화면 해상도 | 240×320 | 480×800 (디바이스별) |
| 모던 OS 차단 사유 | SKT GVM 런타임 사라짐 | 32-bit ABI + GLES1 |
| Phase B 난이도 | **고** (string xref → 함수 경계 추정) | **중** (JNI export + 심볼) |
| 공유 엔진 적합성 | Hero3/4 동일 한빛 내부 엔진 → 대부분 코드 공유 | Midas 엔진 — Hero3/4 와 다른 trail. 자산 포맷·시나리오 VM 별도 |

---

## 5. 영웅서기 시리즈 진행 기록

### Hero3 (영웅서기3 - 운명의수레바퀴, 2008, JAR)
- ✅ 자산 변환 100% (txt/pa/bm/cif/mp/scn/dat)
- ✅ Phase B Ghidra 분석 1차 완료 — `_bm` 의 0x0c 8-bit dense 포맷 풀림 (`FUN_00010fe4`)
- ✅ Android 클라이언트 ([android/](../android/)) 8개 씬 동작 (MainMenu, MapWalk, Battle, Dialogue, Inventory, Status, Skill, Shop 등)
- ✅ i18n hook (한국어 기본, 영어 번역 ~$0.66 비용으로 4 hour caching 으로 일괄 번역 완료)
- ✅ HD 자산 (4× scale4x 업스케일)
- ⏳ Phase C: KMM commonMain 분리 대기 — 이후 Hero4 가 같은 엔진을 공유
- ⏳ Phase D: iOS — Phase C 후
- 보류: SMAF/MMF → OGG 변환

### Hero4 (영웅서기4 - 환영의검, 2009, JAR)
- ✅ Phase A 자산 변환 종료: txt=5, pa=196, bm 30+200, cif=148, scn=350 (4,078 대사), dat=26, h4_map=97, exd=117, h4_tile=277
- ✅ `_PAL` 8byte/color 포맷 풀림 (Hero3 의 4byte 의 2배 — primary + secondary RGB)
- ✅ `_MAP_M_` 헤더 버전 일반화 + body = Hero3 `_mp` 와 동일
- ✅ `_TILE_030` 컨테이너 prefix (`01 00 00 00 <size>`) 풀림
- ✅ `tools/recon/*` game-aware 자동화 (`extract_strings.py --json` + `_targets.py` 헬퍼)
- ✅ Hero4 zone 이름 = 켈트 신화 Tuatha Dé Danann 패러디 (뮤리아스/핀디아스/팔리아스) 확인
- ✅ Hero4 Android 모듈 스켈레톤 ([apps/hero4-android/](../apps/hero4-android/)) — 자산 699 file 배포, MainActivity 는 placeholder
- ⏳ Phase B 미해독: `_PAL` secondary RGB 의미, `_EXD` payload entry struct, `_MAP_M_` extras (NPC/exit/event), HDAT entry layout
- ⏳ 대사 영어 번역 (A1) — API 키 대기
- ⏳ Phase C: Hero3 와 같은 commonMain 엔진 마운트 대기
- 발견: `client.bin387872` 안에 WIPI/JLet API 임베드 (`org/kwis/msp/lcdui/*`) — Clet+KTF 호환 빌드

### Hero5 (영웅서기5, 2020 Android 포팅, APK)
- 별도 트랙: 이미 Android APK 가 존재하지만 **32-bit only** 라 현대 폰 미지원
- 엔진: **Midas** (한빛/EA Mobile Korea 자체엔진) — Hero3/4 와는 다른 계보
- ✅ APK 언팩 + `lib/armeabi/libHeroesLore5.so` 식별
- ✅ VFS 컨테이너 (`assets/data.vfs.mp3`) 100% 풀림 — 2189개 entry 추출
- ✅ Phase 2-A 완료: sprite 3,798 frame + 한글 텍스트 75,284 개 (35,931 unique) 추출
- ✅ Ghidra 프로젝트 + 핵심 함수 디컴파일 (debug 심볼 보존되어 함수명 그대로 사용 가능)
- ✅ JNI export 18개 매핑 (nativeInitKernel → nativeInitVFS → nativeInitDisplay → nativeStartApp → nativeLoop)
- ⏳ Phase B: Midas 시나리오 VM opcode 의미 분석
- ⏳ Phase C: Hero3/4 와는 별도 엔진 트랙 — 자산 포맷이 다름. 단 Compose Multiplatform 출력 레이어는 공유 가능
- 결정적 차단: armeabi 32-bit + GLES1 + SKT TAD DRM → 원본 `.so` 재사용 경로 폐쇄, 자산만 재활용

---

## 6. 같은 모노레포에서 셋을 함께 굴리는 이유

| 공유 | 게임별 |
|---|---|
| `tools/converter/` (BM/CIF/PAL 디코더) — Hero3/4 거의 100% 공유, Hero5 일부 | 자산 (게임마다 다름) |
| `tools/recon/` — game-aware 모듈로 Hero3/4 binary 둘 다 처리 | 시나리오·스탯·맵 데이터 |
| `tools/i18n/` — 캐릭터 사전·prompt caching 동일 | 출시 번들 (Bundle ID 별도) |
| `tools/hd/` — scale4x 업스케일 동일 | KMM 안에서도 게임별 콘텐츠 모듈 분리 |
| 향후 KMM commonMain 엔진 — Hero3/4 공유 | 게임별 Scene wiring |

세 게임이 **같은 한빛 내부 엔진의 진화형** 이라는 발견 (`'frameBuf is NULL'` 동일 에러 메시지 등) 이 모노레포 결정의 근거. Hero3/4 는 같은 commonMain 을 공유하고, Hero5 는 자산/엔진이 달라 별도 모듈이지만 같은 빌드 시스템·출력 레이어를 쓴다.

---

## 7. 무엇을 하지 않는가

- **에뮬레이터 / shim 으로 원본 실행** — 위 §2 사유로 비현실적
- **세이브 호환** — 원본 RecordStore 포맷 보존 안 함
- **원본 DRM 유지** — SKT TAD / 통신사 IAP 코드는 모두 제거
- **저작권 무시** — 한빛소프트와의 권리 정리는 별개 트랙. 본 저장소는 분석/리메이크 작업물이고 출시 결정은 권리 정리 후
- **게임당 단일 모놀리식 출시** — 게임별 별도 패키지가 원칙

---

## 8. 결과물의 형태

리메이크가 완료되면 사용자는 다음을 보게 된다:

- Google Play Store 에서 "영웅서기3", "영웅서기4", "영웅서기5" 각각 검색해 다운로드
- App Store 에서 동일하게 다운로드
- 설치 후 곧장 실행 — 추가 설정 없음
- 한국어 기본, 영어 토글 가능
- 가상 키패드로 조작 (피처폰 키 매핑을 화면 위 버튼으로)
- 원본보다 크고 선명한 화면 (HD 자산 슬롯-인) + 원본 화면비 보존 레터박스
- 음악은 원본 분위기를 유지하는 OGG (Hero5 는 그대로, Hero3/4 는 SMAF→OGG 변환)
- 원본의 모든 시나리오·맵·전투·아이템·NPC 그대로

이 모든 것을 만족할 때만 "리메이크 완료" 이다.
