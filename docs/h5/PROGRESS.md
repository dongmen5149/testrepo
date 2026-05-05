# Hero5 (영웅서기5) 진행 상황

> Hero3/4와 다른 트랙. 기존 Android APK 가 존재하지만 64-bit 폰 미지원.

## 원본
- `Hero5/영웅서기5(최신폰전용).apk` (17 MB, 2020-11-03)
- 이미 Android 포팅된 버전 (한빛소프트가 직접 했거나 외주). 단:
  - **`lib/armeabi/libHeroesLore5.so` 만 존재** (32-bit ARMv5)
  - v7a / v8a 미포함 → 현대 64-bit Android 폰에서 실행 불가
  - 대상 SDK 매우 낮음 (2020년 시점, ARMv5 호환성 우선)
- `classes.dex` + `libHeroesLore5.so` 분리 구조 (Java 진입점 + 네이티브 게임 로직)
- `assets/data.vfs.mp3` (16 MB) — 자산 VFS (mp3 라벨링이지만 obfuscated 컨테이너)

## 가능한 경로

### A. **콘텐츠만 추출 + 엔진 재구현** (Hero3/4와 동일 전략)
- `data.vfs.mp3` VFS 포맷 리버싱 → 자산 추출
- `libHeroesLore5.so` 게임 로직 분석 (참조용)
- 공유 엔진 위에 Hero5 콘텐츠 추가 (engine-h5 또는 동일 engine)

### B. **`.so` 재컴파일 / ABI 추가** (소스 없으므로 사실상 불가)
- 원본 C/C++ 소스 없음 → 무리

### C. **호환 레이어** (armeabi → arm64 라이브러리 wrapping)
- houdini 같은 binary translation은 모바일에서 사용 불가
- 비추

→ **A 경로** 가 유일한 합리적 선택.

## 다음 마일스톤
- [ ] APK 추출 → `work/h5/extracted/`
- [ ] `data.vfs.mp3` 헤더 분석 (시그니처, 인덱스 테이블)
- [ ] `classes.dex` 분석 (Smali → Java 디컴파일) — VFS 로딩 함수 식별
- [ ] `libHeroesLore5.so` IDA/Ghidra import (참조용)

Hero5 작업은 Hero3/4 자산 변환이 안정화된 후 시작.
