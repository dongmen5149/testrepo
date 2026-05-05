# Hero4 다음 단계

Phase A (자산 변환) 종료. 이 문서는 사용자 (또는 다음 세션 Claude) 가 진행해야 할 작업을 우선순위 순으로 정리.

---

## 🟢 즉시 자동 가능 (사용자 트리거만 필요)

### A1. 대사 영어 번역 — Claude API 키 필요

```bash
export ANTHROPIC_API_KEY=...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
```

- 입력: `work/h4/converted/dialogue_corpus.json` (4,078 lines, 3,743 unique)
- 출력: `work/h4/converted/dialogue_translations_en.json`
- Hero3 와 동일한 system prompt + 1h prompt caching 으로 비용 절감
- 추정 비용: ~$0.30 (Hero3 $0.66 보다 적음, 대사 수 1/6 수준)
- system prompt 의 캐릭터 사전은 Hero3 인물 (리츠/케이/일레느 등) 기준 — Hero4 캐릭터 (수레바퀴섬/매도우힐/뮤리아스 NPC 등) 로 갱신 권장 (`tools/i18n/translation_dict.py`)

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

### A4. `tools/recon/find_xrefs.py` Hero4 용 TARGETS 갱신

현재 `find_xrefs.py`, `find_pic_xrefs.py`, `find_base.py` 의 `TARGETS` 가 Hero3 string offset 이라 Hero4 에 noise. 자동화 추가:

1. `tools/recon/extract_strings.py` 가 결과를 JSON 으로 dump 하도록 옵션 추가
2. file path string (`/H4/...`, `/MAP/...`) 들의 offset 자동 추출
3. game-aware TARGETS 로 변환

이렇게 하면 Hero4 GOT base 도 자동 추정 가능 → Phase B GUI 작업의 1단계 자동화.

### A5. `_TILE_030` 분석

다른 헤더 prefix (`01 00 00 00 8d 00 00 00` + frame header) 인 단일 파일. file header 8 byte 추가 컨테이너로 추정. 헤더 디코드 후 일반 single-frame BM 디코더로 처리 가능.

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
| _PAL secondary RGB 의미 | `/H4/PAL/_H_%03d_PAL`, `Alpha Palette Index Not Found` |
| _EXD payload entry struct | `/H4/EXD/_H_%03d_EXD` |
| _MAP_M_ extras 영역 (NPC/exit/event) | `/MAP/M/_MAP_M_%03d` |
| HDAT entry layout | (정확한 string 미확인 — file enum 으로 로드 가능) |

**예상 시간**: 1~2주 (Hero3 Ghidra 작업과 비슷한 수준).

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

## 📋 권장 진행 순서

다음 권장 순서 (의존관계 + 가치 큰 것 부터):

1. ✅ **A1** (대사 번역) — API 키만 있으면 30분
2. ✅ **A4** (find_xrefs game-aware) — 자동 30분
3. ✅ **A2** (Ghidra 프로젝트 셋업) — 사용자 GUI 30분
4. **B** (Ghidra 분석) — _PAL secondary 우선, 그 다음 _EXD/_MAP_M_extras (1~2주)
5. **C+D 결정** — Mac 보유 여부 + Phase C 시작 시기 결정
6. **C** (KMM 리팩터, 2~4주)
7. **D** (iOS, 1주)
8. **E** (SMAF 변환) — Phase D 출시 전까지 진행

A5 (`_TILE_030`), A3 (Hero4 dictionary) 는 시간 날 때 짬.

---

## 🚧 의도적으로 미해결로 둔 것

- `OBJ/{000,001,002}/` 247 single-frame BM 의 인덱스 의미 — PNG 변환은 됐으나 무엇을 가리키는지 (지역별? 이벤트별?) Phase B 에서 _MAP_M_ extras 와 같이 풀릴 가능성
- HDAT entry layout — 그룹 분류만. 게임 wiring 단계에서 정확한 의미 필요 시 Phase B 확장
- Hero5 별도 트랙 — `docs/h5/PROGRESS.md` 참조. Hero3+Hero4 안정화 후
