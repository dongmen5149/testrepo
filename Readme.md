# Hero Saga Remake (영웅서기 리메이크)

한빛소프트의 SK텔레콤 피처폰 RPG **영웅서기 시리즈** 를 모던 Android + iOS 로 리메이크.
모노레포 구성, 게임별 별도 출시.

## 게임

| ID | 작품 | 원본 | 상태 |
|---|---|---|---|
| `h3` | 영웅서기3 - 운명의수레바퀴 (2008) | `Hero3/0103EFD4.jar` (SKT GVM/Clet) | 자산 변환 + Android 8개 씬 + i18n + HD 완료 |
| `h4` | 영웅서기4 - 환영의검 (2009) | `Hero4/010100D4.jar` (SKT GVM/Clet) | 1차 dry-run 완료 (호환률 ~80%) |
| `h5` | 영웅서기5 (2020 Android 포팅) | `Hero5/영웅서기5(최신폰전용).apk` | 진행 전 — 64-bit ABI 추가 필요 |

> 작업을 이어서 할 때: 게임별 [`docs/<id>/PROGRESS.md`](docs/h3/PROGRESS.md) 를 먼저 확인.

## 디렉토리

| 경로 | 내용 |
|---|---|
| `Hero3/`, `Hero4/`, `Hero5/` | 원본 아카이브 (수정 금지) |
| `tools/_game.py` | 게임별 path/binary 설정 (game-aware 모듈) |
| `tools/converter/` | 자산 변환기 (txt/pa/bm/cif/mp/scn → JSON·PNG) — Hero3/4 공유 |
| `tools/recon/` | 네이티브 바이너리 정찰 (capstone Thumb) — `HERO_GAME` env 로 게임 선택 |
| `tools/i18n/`, `tools/hd/` | 다국어 / HD 업스케일 — game-aware |
| `tools/ghidra/` | Ghidra 스크립트 |
| `work/{h3,h4,h5}/` | 게임별 추출/변환 산출물 (gitignore) |
| `docs/{h3,h4,h5}/` | 게임별 진행 문서 |
| `docs/asset-formats.md` | 공유 자산 포맷 분석 (Hero3/4 공통) |
| `android/` | Hero3 Android 클라이언트 (Phase 3에서 `engine/` + `apps/hero3-android` 로 분리 예정) |

## 사용법

```bash
# 게임 선택은 환경변수 또는 인자
export HERO_GAME=h3       # default

# 자산 변환
python tools/converter/convert_all.py work/h3/extracted work/h3/converted

# Hero4 변환
python tools/converter/convert_all.py work/h4/extracted work/h4/converted
```

`tools/recon/`, `tools/i18n/`, `tools/hd/` 의 스크립트들은 `HERO_GAME` 환경변수에 따라 자동으로 게임별 경로 사용.

## 전략

자세한 결정 근거: [`docs/asset-formats.md`](docs/asset-formats.md). 요지:

- 원본 (Hero3/4) 바이너리는 ARM Thumb 네이티브 (Java 바이트코드 X) → 에뮬레이터·shim 불가능
- 자산만 재활용하고 엔진 재구현 (**Strategy C**)
- 240×320 가상 캔버스 + letterbox 스케일 → HD 자산 슬롯인 가능
- 한국어 베이스 + i18n 확장
- 세이브 호환 X
- **Phase 3**: Hero3+Hero4 공유 엔진을 KMM commonMain 으로 분리, Android+iOS 동시 출시. 출시 자체는 게임별 별도 패키지/스토어 리스팅.
- Hero5 는 별도 트랙 (이미 Android 포팅 존재, ABI 호환성 문제 — `docs/h5/PROGRESS.md` 참조)
