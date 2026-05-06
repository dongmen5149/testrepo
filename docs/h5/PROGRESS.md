# Hero5 (영웅서기5) 진행 상황

> Hero3/4와 다른 트랙. 기존 Android APK 가 존재하지만 32-bit 전용이라 현대 폰 미지원.
> 전략 = **A. 자산 추출 + 엔진 재구현** (Hero3/4 인프라 재사용 가능).

업데이트: 2026-05-06 — Phase 1 완료 + Phase 2-A.1~3 (프로브 + _pa 확정 + 미매칭 클러스터링) 완료.

---

## 1. 원본 / 폴더 레이아웃

| 경로 | 내용 |
|---|---|
| `Hero5/영웅서기5(최신폰전용).apk` | 원본 APK (17 MB, 2020-11-03) — **수정 금지** |
| `work/h5/extracted/` | APK unzip 결과 (DEX, .so, assets) |
| `work/h5/vfs_entries/` | **VFS 언팩 결과 2189개** (00000_xxxx.ogg/bin/txt) |
| `work/h5/vfs_catalog.tsv` | 인덱스 / 오프셋 / 해시 / 길이 / 타입 |
| `work/h5/analysis/` | Ghidra 로그, 디컴파일 결과, 분석 스크립트 |
| `work/h5/ghidra_project/Hero5.gpr` | Ghidra 프로젝트 (재실행 시 -overwrite 주의) |
| `tools/h5_vfs_unpack.py` | VFS 언팩커 |
| `tools/ghidra/DecompileHero5Keys.java` | 핵심 함수만 디컴프 (재실행 가능) |

`tools/_game.py` 의 `h5.binary_name` 은 `lib/armeabi/libHeroesLore5.so` 로 갱신됨.

---

## 2. 바이너리 핵심 사실

- **엔진**: Midas (한빛 / EA Mobile Korea 자체엔진) — Hero3/4와 동일 계보
- **APK 패키지**: `co.kr.eamobile.HeroesLore5` v01.00.08, minSdk=23 (Android 6.0)
- **JNI 진입 클래스**: `co.kr.eamobile.CletEntry` (DEX 의 MidasActivity 는 래퍼/라이프사이클)
- **JNI exports (18개)**: nativeInitKernel → nativeInitVFS → nativeInitDisplay → nativeStartApp → nativeLoop … (완전 표준)
- **그래픽**: `libGLESv1_CM` = **OpenGL ES 1.x 고정 파이프라인** (DEX 쪽 EGL_OPENGL_ES2_BIT 는 EGL config 일 뿐)
- **ABI**: armeabi (ARMv5TE) 32-bit only — 현대 Android (특히 14+) 차단
- **debug_info / 심볼 보존**: stripped 안 됨 → Ghidra 가 함수명 그대로 인식 (Hero3/4 보다 분석 쉬움)
- **DRM**: SKT TAD SDK + 통신사 IAP — **리메이크 시 전부 제거**

---

## 3. VFS (`assets/data.vfs.mp3`) — 100% 풀림

**포맷** (little-endian, no header, no encryption):
```
[entry] uint32 hash | uint32 length | bytes data[length]
… 끝까지 반복
```

근거: `MIDASKernelManager::getAssetSizeFromVFS` 디컴프 (`work/h5/analysis/key_funcs.c` 라인 440~). `loadAssetFromVFS` 도 단순 `fread` — VFS 레벨에서는 암호화 없음.

**언팩 결과** (2026-05-06 sniffer 보정 후):
- 총 2,189 entries / 16,399,297 bytes 모두 소진 (잔여 0)
- ogg 42 / **smaf 42** / txt 1 / bin 2,104 (Midas 자체 포맷)
- 초기 sniffer 가 `MMMD` 미인식 → 사운드가 84개임이 드러남 (Hero3 의 `_mf` 와 동일한 SMAF/MMF)

재실행: `python tools/h5_vfs_unpack.py`

---

## 4. DES 키 / 암호화 위치 (열려 있는 채널)

VFS 자체는 평문이지만 **별개 레이어에 DES**가 있음:
- 심볼: `KEY4ENCRYPT` `KEY4REAL` `__DES_KEY__` (모두 .bss → 런타임 초기화)
- 함수: `MX_desInit` / `MX_desEncrypt[PKCS7]` / `MX_desDecrypt[PKCS7]`
- 호출 진입점: `StaticUtil::LoadDecryptFile` / `SaveEncryptFile` / `LoadResDecrypt`

용도 추정: 세이브 파일, 일부 보호된 리소스, 네트워크. 자산 추출 자체에는 **현재 불필요**.

키 추출이 필요해지면: `MX_desInit(char*)` 호출자 추적 → 인자 문자열 찾기 (Ghidra `References to MX_desInit`).

---

## 5. 다음 단계 (우선순위 순)

### Phase 2-A. .bin 포맷 정체 파악

#### 2-A.1 호환성 프로브 — ✅ 완료 (2026-05-06)

`tools/h5_bin_probe.py` 가 2,104개 .bin 에 Hero3/4 파서를 try-except 적용.

산출:
- `work/h5/analysis/bin_probe_matrix.tsv` (파일별 hit 매트릭스)
- `work/h5/analysis/bin_probe_summary.txt` (집계 + 매직 분포)

결과 요약:
| 포맷 | hit | 비고 |
|---|---:|---|
| smaf (`MMMD`) | 42 | ✅ Hero3 와 동일, 변환 그대로 적용 가능 |
| _pa (팔레트) | 557 | ⚠ 후보 강함. `count*4+1==len` 이 다양한 size(53/41/49…)에서 통계적으로 매칭. 색 인코딩(RGBA8888 vs RGB565)은 시각 검증 필요 |
| _cif | 144 | ⚠ 약한 시그니처(`19 19` 마커). false-positive 비율 별도 검증 필요 |
| _mp | 63 | ⚠ 첫 바이트 0x02/0x03 만으로 매칭. parse_mp 가 통과했다면 layout 은 호환 가능성 있음 |
| _txt | 0 | Hero5 스트링은 다른 포맷 |
| _bm | 0 | ❌ Hero3/4 의 `0x1f 0xf8` 프레임 마커 부재 → 스프라이트는 별도 reverse 필요 |
| **미매칭** | **1,341 (62%)** | Hero5 자체 포맷 (스프라이트/애니/맵/폰트 등). 지배 매직 `07 00 00 00`, `0d 00 00 00`, `01 00 01 00` → uint32 entry-count container 추정 |

#### 2-A.2 _pa 인코딩 확정 — ✅ 완료 (2026-05-06)

도구: `tools/h5_pa_swatch.py` (시각화) + 4-byte 위치별 엔트로피 분석.

**결정**: Hero5 _pa = `uint8 count + count × (RGB565 LE pair)` = 총 `2*count` 색.
- 근거: byte[0]/byte[2] (low byte) 와 byte[1]/byte[3] (high byte) 의 분포가 짝지어진 LE uint16 패턴.
- 검증: 557/557 candidate 모두 파싱 성공, 자연스러운 게임 팔레트 (블루-퍼플, 빨강 그라디언트 등).
- Hero3 의 RGBA8888 와는 다른 인코딩 → 별도 파서 `tools/converter/convert_h5_pa.py` 추가.

산출:
- `tools/converter/convert_h5_pa.py` — 정식 파서
- `work/h5/analysis/pa_swatches/_index.html` — 202 샘플 컨택트시트

#### 2-A.3 _mp/_cif 거짓양성 / 미매칭 클러스터링 — ✅ 완료 (2026-05-06)

**_mp 거짓양성 확정**: 63 매칭 중 sane 20개, 그러나 **이름 있는 게 0개**. Hero3 _mp 는 항상 ASCII 맵 이름(NEOSOLTIA 등)을 가짐. → Hero5 맵은 별도 포맷.

**미매칭 1,341개 → 578 distinct magic 으로 클러스터링** (`tools/h5_unknown_cluster.py`, 산출 `work/h5/analysis/unknown_clusters.txt`).

지배 클러스터들의 공통 헤더 구조 (큰 발견):
```
uint32 frame_count        // magic = LE 표현 → 1/4/6/7/12/13/17 등
uint32 total_length
uint8  0x14               // sprite-like 클러스터 거의 전부에서 상수
uint8  variant            // 0x0b — 0x10 (bit-depth / palette index 추정)
uint16 width   LE
uint16 height  LE
... pixel data ...
```

**Hero3 `_bm` 와의 관계**:
- magic `0d000000` 샘플 00760 의 offset 14 에 Hero3 의 frame marker `1f f8` 그대로 존재
- Hero5 sprite = **8-byte outer wrapper (count+length) + Hero3 _bm 계열 inner format**
- 단, Hero5 는 팔레트가 분리되어 별도 _pa 파일로 존재 (Hero3 는 frame 내부에 팔레트 임베디드)

#### 2-A.4 다음 단계 (우선순위 순)

1. **Hero5 sprite 디코더 작성** — outer wrapper 8 byte 스킵 후, frame 별 `(0x14, variant, w, h)` 헤더를 파싱하고 pixel 데이터를 별도 _pa 파일과 결합해 PNG 출력. 대상 클러스터: `07/0d/04/11/0c/06/01000000` (200+ 파일).
2. **sprite ↔ palette 매칭 규칙** — 같은 인덱스 그룹? hash 인접성? 게임 코드의 `getUniqueAssetNameFromID` 로 매핑 복원.
3. **소수 클러스터 분류** — `01640201`(27), `02000100`(21), `01000100`(43) 등 작은 사이즈 그룹은 애니메이션 스크립트 / 폰트 / 데이터 테이블 후보.
4. **Ghidra 분석 재개** — `MIDASKernelManager::loadAssetFromVFS` 호출자 추적해서 `(asset_id) → reader_fn` 디스패치 테이블. Hero5 는 심볼 보존되어 함수명으로 포맷 판별 쉬움.

### Phase 2-B. 자산 파일명 복원
현재는 `00000_<hash>.bin` 형태. 원본 이름 복원하려면:
- `AndroidService::getUniqueAssetNameFromID` 디컴파일 → 이름 테이블 위치
- `_midas_*` 문자열 섹션 dump → 매핑 후보
- hash 함수 재현 (`MIDASKernelManager::hash` 디컴파일) → 이름 추측 시 검증용

### Phase 2-C. JNI 호출 흐름 → 게임 루프 정리
`Java_..._nativeLoop` 와 `MIDASKernelManager::timerLoop` 부터 시작. 60fps tick / event handling / render 호출 순서를 그래프로.

### Phase 3. 리메이크 엔진 결정 + 재구현
- **권장 Unity 2022 LTS** (Android arm64 + iOS 동시 빌드)
- ES 1.x → Unity URP 변환 시 fixed-function 컬러/조명 재현 주의
- IAP / SDK 의존성 전부 제거 후 Unity IAP 로 교체

---

## 6. 다음 세션 즉시 재개 체크리스트

```
1. cd d:/testrepo && python tools/h5_vfs_unpack.py     # 결과 확인
2. cat work/h5/vfs_catalog.tsv | head                  # 카탈로그 점검
3. less work/h5/analysis/key_funcs.c                   # 디컴파일 17개
4. less work/h5/analysis/so_quick.txt                  # 심볼/JNI 목록
```

Ghidra GUI 로 보고 싶으면:
```
D:/ghidra_12.0.4_PUBLIC/ghidraRun.bat
→ Open project → D:/testrepo/work/h5/ghidra_project/Hero5
```

추가 함수 디컴파일 필요시 `tools/ghidra/DecompileHero5Keys.java` 의 `PAT` 정규식 확장 후:
```
D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat \
  D:/testrepo/work/h5/ghidra_project Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath D:/testrepo/tools/ghidra \
  -postScript DecompileHero5Keys.java
```
