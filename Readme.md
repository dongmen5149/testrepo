# Hero3 Remake

원본 한국 SK텔레콤 GVM/Clet 피처폰 게임 **"영웅서기3-운명의수레바퀴"** (한빛소프트, 2008)를 모던 Android로 리메이크.

> 📋 **작업을 이어서 할 때 가장 먼저 읽기**: [`docs/PROGRESS.md`](docs/PROGRESS.md) — 진행 상황 + 다음 우선순위 정리

## 디렉토리

| 경로 | 내용 |
|---|---|
| `Hero3/` | 원본 JAR + 세이브 (수정 금지) |
| `docs/PROGRESS.md` | **진행 상황 & 다음 우선순위 (핸드오프 문서)** |
| `docs/asset-formats.md` | 자산 포맷 분석 리포트 |
| `tools/converter/` | Python 자산 변환기 (txt/pa/bm/cif/mp/scn → JSON·PNG) |
| `tools/hd/` | HD 리마스터 파이프라인 (scale4x) |
| `tools/recon/` | client.bin64000 정찰 도구 (capstone Thumb) |
| `android/` | Android Kotlin 클라이언트 (스켈레톤 + SpriteGallery + MapScene) |
| `work/` | 추출/변환 중간 산출물 (gitignore) |

## 작업 흐름

1. **자산 변환** — `tools/converter/convert_all.py` 로 원본 → PNG/JSON 변환
2. **Android 자산 배포** — `tools/converter/prepare_android_assets.py` 로 `android/app/src/main/assets/` 채움
3. **Android 빌드** — [`android/README.md`](android/README.md) 참조

## 진척 요약

- ✅ 1,272개 원본 자산 인벤토리
- ✅ 변환 완료: `_txt` (9 → JSON), `_pa` (216 → JSON), `_bm` (479 → **3,131 frame PNG**), `_cif` (103 → JSON), `_mp` (134 → JSON), `_scn` (244 → JSON, **26,415 대사 추출**)
- ✅ HD 리마스터: 3,131 sprite scale4x 4× 업스케일
- ✅ Android 8개 씬 (Title/MainMenu/Status/Inventory/Dialogue/Settings/SpriteGallery/Map) + Scene 스택 + Locale override
- ✅ i18n: UI 어휘 196개 100% 영어 번역 + 자산 카탈로그
- ⚠️ 보류 (Ghidra 필요): type 0x0c sparse 픽셀, `_scn` opcode, `_mp` extras (NPC/exit), `_cif` animation timing, SMAF 사운드

**다음 작업**: [`docs/PROGRESS.md` ⚡ 다음 세션](docs/PROGRESS.md) 섹션 참조 (3가지 추천 + 4가지 추가 옵션).

## 전략

자세한 결정 근거: [`docs/asset-formats.md`](docs/asset-formats.md). 요지:

- 원본 바이너리는 ARM Thumb 네이티브 (Java 바이트코드 X) → 에뮬레이터·shim 불가능
- 자산만 재활용하고 엔진 재구현 (Strategy C)
- 240×320 가상 캔버스 + letterbox 스케일 → HD 자산 슬롯인 가능
- 한국어 베이스 + i18n 확장
- 세이브 호환 X
