# Hero4 다음 단계

Phase A (자산 변환) 종료. 이 문서는 사용자 (또는 다음 세션 Claude) 가 진행해야 할 작업을 우선순위 순으로 정리.

> 사용자 컨텍스트: "리메이크" 정의는 [`../REMAKE_METHODOLOGY.md`](../REMAKE_METHODOLOGY.md) 참조 — 최종 산출물은 Play Store + App Store 직배포.

---

## ⏭ "영웅서기4 이어서 진행해줘" 라고 했을 때 — 빠른 셀렉터

다음 세션에서 사용자가 별다른 지시 없이 "Hero4 이어서" 라고만 말하면 **이 순서로 판단**:

1. **API 키 (`ANTHROPIC_API_KEY`) 가 환경에 있나?** → **A1 (대사 영어 번역)** 즉시 진행 (~30분, ~$0.30, 자동)
2. **Mac + Ghidra 환경 사용자가 대기 중인가?** → **A2 (Ghidra 프로젝트 셋업)** 안내 후 **Phase B** 진입
3. **둘 다 아니면** → **A3 (Hero4 캐릭터 사전 보강)** 자동 진행. 이건 코드 작성만으로 끝나고 즉시 검증 가능 → 그 다음 사용자에게 다음 결정 요청 (Mac/iOS 가능 여부)
4. **사용자가 "Phase C 시작" 명시** → [Phase C](#c-phase-c--hero3-엔진-kmm-분리--hero4-콘텐츠-wiring) 의 1단계 (Hero3 engine 디렉터리 검토 + KMM 모듈 스켈레톤 생성)

이미 풀린 (= 다시 안 해도 되는) 항목:

- ~~A4 (recon game-aware)~~ ✅ 완료 — 2026-05-07
- ~~A5 (`_TILE_030`)~~ ✅ 완료 — 2026-05-07

---

## 🟢 즉시 자동 가능 (사용자 트리거만 필요)

### A1. ~~대사 영어 번역~~ ⛔ **DES key 발굴 후 가능**

```bash
export ANTHROPIC_API_KEY=...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

- 입력: `work/h4/converted/dialogue_corpus.json` (4,078 lines, 3,743 unique)
- 출력: `work/h4/converted/dialogue_translations_en.json`
- Hero3 와 동일한 system prompt + 1h prompt caching 으로 비용 절감
- 추정 비용: ~$0.30 (Hero3 $0.66 보다 적음, 대사 수 1/6 수준)
- system prompt 의 캐릭터 사전은 Hero3 인물 (리츠/케이/일레느 등) 기준 — Hero4 캐릭터 (수레바퀴섬/매도우힐/뮤리아스 NPC 등) 로 갱신 권장 (`tools/i18n/translation_dict.py`)

> ⛔ **현재 차단**: Hero4 SCN 이 DES 암호화 되어 있어 corpus 가 garbage. Phase B 에서 DES key 8 bytes 발굴 → SCN re-decrypt → corpus 재생성 후에 번역해야 의미 있음. 자세한 내용은 [Phase B](#b-phase-b--ghidra-gui-분석) 참조.

### A2. Ghidra 프로젝트 락 해제 + Hero4 프로젝트 생성

`work/h3/ghidra_proj/*.lock` 파일이 잠겨 있어서 작업 중 work/ 이동 불가. Ghidra 가 열려있으면 닫고:

```bash
# 락 파일 정리 (Ghidra 닫은 후)
rm work/h3/ghidra_proj/*.lock work/h3/ghidra_proj/*.lock~
```

새 Hero4 Ghidra 프로젝트:
```
File > New Project > work/h4/ghidra_proj/Hero4
File > Import > work/h4/extracted/client.bin387872
Language: ARM:LE:32:Cortex (gcc)
```

### A3. Hero4 caracter 사전 보강 (선택)

`tools/i18n/translation_dict.py` 에 Hero4 zone 이름 추가 (translate_dialogues 가 잘 번역하도록):
```python
PLACES_H4 = {
    '수레바퀴섬': 'Wheel Island',  # 또는 'Cartwheel Isle'
    '매도우힐': 'Meadow Hill',
    '이름없는섬': 'Nameless Isle',
    '뮤리아스': 'Murias',           # 켈트 신화 도시 그대로
    '핀디아스': 'Findias',
    '팔리아스': 'Falias',
    '아눈섬': 'Annwn Isle',
    '검은바위섬': 'Blackrock Isle',
    '은바위섬': 'Silverrock Isle',
    '해적소굴': 'Pirate Den',
    # ...
}
```

Hero3 PLACES 와 합치거나 게임별 분리 (`select(game).places`).

### ~~A4. `tools/recon/find_xrefs.py` Hero4 용 TARGETS 갱신~~ ✅ 완료 (2026-05-07)

[extract_strings.py](../../tools/recon/extract_strings.py) `--json` 옵션 + [_targets.py](../../tools/recon/_targets.py) 헬퍼로 풀림. 3 스크립트 모두 game-aware. 발견:
- code/data 경계 ≈ 0x77000
- 핵심 라벨 4개: `frameBuf is NULL`, `Alpha Palette Index Not Found`, `java/lang/NullPointerException`, `(null)`
- **Hero4 binary 는 LDR+ADD T1 인접 PIC 패턴이 거의 없음** → Phase B 에서 다른 추적 전략 (32-bit LDR.W 또는 Ghidra 자체 xref) 필요

### ~~A5. `_TILE_030` 분석~~ ✅ 완료 (2026-05-07)

컨테이너 prefix `01 00 00 00 <size LE32>` 감지. [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 의 `decode_h4_tile` 에서 prefix stripping 후 inner BM 으로 재진입. 결과: 16×16 dark blue placeholder. h4_tile=276→277.

---

## 🟡 사용자 결정 필요

### B. Phase B — Ghidra GUI 분석

상세: [`ghidra-guide.md`](ghidra-guide.md)

**선결**:
- JDK 21 + Ghidra 12.x 설치 (Hero3 와 동일 환경)
- A2 (Ghidra 프로젝트 생성) 완료
- A4 (Hero4 GOT base 추정) 완료 권장

**우선순위 함수** (string xref 기반):

| 풀리는 미해독 | 키 string |
|---|---|
| ⭐ **DES key (8 bytes)** | `/DAT/_DAT_DES` 로딩 함수 + 그 호출자 (SCN 복호화 진입점) |
| _PAL secondary RGB 의미 | `/H4/PAL/_H_%03d_PAL`, `Alpha Palette Index Not Found` |
| _EXD payload entry struct | `/H4/EXD/_H_%03d_EXD` |
| _MAP_M_ extras 영역 (NPC/exit/event) | `/MAP/M/_MAP_M_%03d` |
| HDAT entry layout | (정확한 string 미확인 — file enum 으로 로드 가능) |

**예상 시간**: 1~2주 (Hero3 Ghidra 작업과 비슷한 수준).

> ⚠️ **2026-05-07 발견**: Hero4 SCN 파일은 **DES 암호화** (high-entropy 바이트). `work/h4/extracted/DAT/_DAT_DES` (824 bytes) 가 표준 DES 알고리즘 테이블 (PC-1, E-box, P-box, S1-S8) 을 그대로 담고 있음을 확인. 따라서 SCN/대사 corpus 가 현재 garbage 로 디코딩됨 ([apps/hero4-android/app/src/main/assets/dialogue_corpus.json](../../apps/hero4-android/app/src/main/assets/dialogue_corpus.json) 의 `曝삑킴`, `承孼` 류). **A1 (대사 영어 번역) 는 DES key 발굴 후로 미뤄야 함.** 키는 binary (`client.bin387872`) 안 8 bytes 상수로 추정.

### C. Phase C — Hero3 엔진 KMM 분리 + Hero4 콘텐츠 wiring

[Phase D 와 묶인 결정](#phase-d).

**작업 큰 그림**:
1. `android/` (Hero3 단일) → `apps/hero3-android/` + `shared/` (KMM commonMain)
2. `shared/commonMain/` 에 Hero3 의 Scene/UiKit/GameView/Settings/InputController 등 (~30 클래스)
3. `expect/actual` 추상화: Settings, AssetReader, Locale
4. `android.graphics.Canvas` → Compose Multiplatform `Canvas` 마이그레이션
5. Hero4 게임 콘텐츠를 같은 엔진 위에 마운트 — `games/hero4/` 안의 자산/시나리오를 `apps/hero4-android/MainActivity` 가 읽어 `GameView` 마운트

**예상 시간**: 2~4주 (가장 큰 리팩터링).

**위험**:
- Hero3 가 현재 사용자 검증된 빌드 — 분리 전 git tag 권장 (`v0.1-pre-kmm`)
- Canvas API 마이그레이션 시 게임 화면이 일시적으로 깨질 수 있음. 단계적 진행 (한 Scene씩 commonMain 으로 이전 + 검증)

### D. Phase D — iOS 출시 (Phase C 와 묶임)

**4 옵션 비교** (이전 답변 정리):

| | Compose Multiplatform | LibGDX | KMM+네이티브 | Godot |
|---|---|---|---|---|
| Hero3 코드 재활용 | **~90%** | ~30% | ~50% | 0% |
| 2D 픽셀 RPG 적합 | 양호 (Skia) | 우수 | 양호 | 우수 |
| 학습 곡선 | 낮음 (Kotlin only) | 중간 | 높음 (Kotlin+Swift) | 중간 |
| 시간 비용 | ~3주 | ~6주 | ~8주 | ~12주 |

**추천: Compose Multiplatform** — Hero3 의 Kotlin/Canvas 코드와 가장 잘 호환, 1 코드베이스, 2026 시점 iOS 안정화.

**선결**:
- Apple Silicon Mac (M1+) — iOS 빌드 / 시뮬레이터 / 실기 테스트 모두 필수
- Apple Developer 계정 ($99/년)
- Phase C 완료 (commonMain 엔진)

**작업**:
1. `apps/hero3-ios/`, `apps/hero4-ios/` Xcode 프로젝트 + Swift App entry + `ComposeUIViewController(GameRoot())` 마운트
2. iOS Simulator 검증 (가상 키패드, 한국어 한글 렌더, 사운드)
3. 실기 (TestFlight) 테스트
4. App Store 제출 (게임당 별도 Bundle ID `com.hanbit.hero3` / `com.hanbit.hero4`)

---

## 🔴 외부 도구 / 데이터 필요

### E. SMAF/MMF → OGG 변환

`work/h4/extracted/SND/*_MMF` 41개 (Hero3 와 동일 Yamaha SMAF 포맷). Android `MediaPlayer` 가 SMAF 직접 지원 안 함 → OGG/MP3 변환 필요.

옵션:
1. **Yamaha SMAF SDK** (공식) — 변환 도구 제공, 라이센스 검토
2. **MIDI 추출 → 사운드폰트로 OGG 렌더** — 무료, 음색이 다를 수 있음
3. **수동 재녹음** — 가장 충실하지만 시간 비용 큼

Hero3 도 동일 보류 상태. 두 게임 동시 진행하면 효율적.

### F. iOS 출시 인프라

- Apple Developer 가입
- App Store Connect 메타데이터 등록 (게임당)
  - 카테고리: Games > Role Playing
  - 등급: Apple 등급 심사 (12+ 또는 9+ 추정)
  - 한국어 + 영어 listing 텍스트 / 스크린샷
- TestFlight beta 테스터 모집

---

## 📋 권장 진행 순서 (2026-05-07 갱신)

| # | 작업 | 자동/수동 | 시간 | 상태 |
|---|---|---|---|---|
| 1 | **A4** (recon game-aware) | 자동 | 30분 | ✅ 완료 |
| 2 | **A5** (`_TILE_030`) | 자동 | 30분 | ✅ 완료 |
| 3 | **A1** (대사 번역) | 자동 (API 키) | 30분 | ⏳ 대기 |
| 4 | **A3** (Hero4 dictionary) | 자동 | 15분 | ⏳ 대기 (A1 전에 권장) |
| 5 | **A2** (Ghidra 프로젝트 셋업) | 사용자 GUI | 30분 | ⏳ 대기 |
| 6 | **B** (Ghidra 분석) | 사용자 + Claude | 1~2주 | ⏳ 대기 |
| 7 | **C+D 결정** (Mac/KMM 시점) | 사용자 결정 | — | ⏳ 대기 |
| 8 | **C** (KMM 리팩터) | Claude | 2~4주 | ⏳ Hero3 와 묶임 |
| 9 | **D** (iOS 출시) | 사용자 + Claude | 1주 | ⏳ 출시 인프라 |
| 10 | **E** (SMAF→OGG 변환) | 외부 도구 | — | ⏳ Phase D 전까지 |

다음 자동 진행 가능 한 것 = **A3** (코드만으로 가능). 그 다음 사용자 결정 필요.

---

## 🚧 의도적으로 미해결로 둔 것

- `OBJ/{000,001,002}/` 247 single-frame BM 의 인덱스 의미 — PNG 변환은 됐으나 무엇을 가리키는지 (지역별? 이벤트별?) Phase B 에서 _MAP_M_ extras 와 같이 풀릴 가능성
- HDAT entry layout — 그룹 분류만. 게임 wiring 단계에서 정확한 의미 필요 시 Phase B 확장
- Hero5 별도 트랙 — `docs/h5/PROGRESS.md` 참조. Hero3+Hero4 안정화 후
