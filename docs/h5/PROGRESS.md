# Hero5 (영웅서기5) 진행 상황

> Hero3/4와 다른 트랙. 기존 Android APK 가 존재하지만 32-bit 전용이라 현대 폰 미지원.
> 전략 = **A. 자산 추출 + 엔진 재구현** (Hero3/4 인프라 재사용 가능).

업데이트: 2026-05-07 — **Phase 2-B 완료** (자산 이름 99.3% 복원). Ghidra caller 분석 → .so format strings → 패턴 brute-force.

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

#### 2-A.4 sprite 디코더 — ✅ 완료 (2026-05-06)

`tools/h5_frame_inspect.py` 의 bpp 분석으로 인코딩 확정:

**Outer 구조** (모든 sprite-like 클러스터 100% 일관, 409 파일 검증):
```
u32 frame_count
per frame: u32 frame_length + frame_payload[frame_length]
```

**Frame payload (type=0x14)**:
```
u8  type        // 0x14 = 표준 sprite frame
u8  palcnt      // = variant byte (0x02..0x10) — 팔레트 색 개수
u16 width  LE
u16 height LE
bytes palette[palcnt * 2]              // RGB565 LE, index 0 = 투명
bytes pixels[ ceil(w/2) * h ]          // 4-bit packed, high nibble first, 행단위 패딩
```

**검증**:
- `01252 frame[0]` w=16 h=19 var=0x0f → palette 30B + pixels 152B = 182B ✓
- `00181 frame[0]` w=65 h=22 var=0x0b → palette 22B + pixels 726B = 748B ✓
- 일괄 디코딩 결과: **426 파일 / 4,268 frame / 3,798 렌더링 (89%, 유효 sprite 100%)** / 0 에러
- 샘플 검증: `frame_00_16x19_pal15.png` → 284/304 opaque, 15 unique colors
- type=0x18 검증: `00177 frame[0]` 120x27 pal122 → 2,764/3,240 opaque, 108 unique colors

**type 바이트 의미 확정** (4가지 모두 지원):
- `0x04`, `0x14`: 4-bit packed (행단위 패딩)
- `0x08`, `0x18`: 8-bit indexed (byte-aligned)
- high nibble `0x1` vs `0x0` 의 게임 의미는 미확정 (UI vs character 추정)

**스킵 470개 = 의도적 1×1 더미 stub 전부.** 유효 sprite 미해독 0건.

산출:
- `tools/converter/convert_h5_sprite.py` — 정식 디코더
- `work/h5/converted/sprites/<file>/frame_NN_*.png` — 3,517 프레임
- `tools/h5_frame_inspect.py` — bpp/variant 분석기
- `work/h5/analysis/frame_bpp_distribution.txt`

#### 2-A.5 잔여 분류 + 한글 텍스트 추출 — ✅ 완료 (2026-05-06)

도구: `tools/h5_residual_classify.py` + `tools/h5_extract_text.py`.

**잔여 1,121개 카테고리화** (sprite/_pa/sound 제외):

| 카테고리 | 파일 | 바이트 | 비고 |
|---|---:|---:|---|
| OTHER | 508 | 158K | 50–500B 범위, 다양한 헤더 |
| LARGE_RAW | 288 | 2.4M | >1KB, 19 19 마커 없음 |
| LARGE_ANIM | 177 | 2.7M | >500B, 19 19 마커 다수 |
| TINY_META | 104 | 2.4K | ≤50B, hitbox/offset 추정 |
| MID_SCRIPT | 31 | 447K | 19 19 마커 + 한글 텍스트 다수 |
| SMALL_SCRIPT | 13 | 3.4K | 19 19 마커 포함 짧은 스크립트 |

산출: `work/h5/analysis/residual_categories.txt`

**한글 텍스트 일괄 추출** (453 파일에서 EUC-KR 추출, lead byte 0xB0–0xC8 한글 영역만):
- **46,173 string occurrences / 18,837 unique strings** (한자 false-positive 제거 후)
- 검증 어휘:
  - 캐릭터/직업: 웨이드(107), 슈르츠(64+79), 아일린(58), 나이트(75), 워리어(62), 건슬링어(69), 한손검(59), 양손검(68)
  - 장소: 센트럴(84), 콜크리크(72), 모이투라(60)
  - 몬스터/시스템: 고블린(76), 퀘스트(415), 스킬북(200), 아이템(170), 크리티컬(92), 조합법을(117), 재사용대기(57)
- 산출: `work/h5/converted/text/<file>.json` + `_corpus.txt`

**대표 발견**:
- `00055/00056/00057_641e4*.bin` = **메인 퀘스트 대사 코퍼스** (각 22KB, 동일/거의동일 — i18n 후보)
- "센트럴의 지하도에 자리잡은 고블린들을 퇴치해야…" 류 RPG 표준 퀘스트 대사 검출

#### 2-A.6 한글 필터 개선 + TINY_META 구조 단서 — ✅ 완료 (2026-05-06)

- 한글 추출 필터 개선: lead byte 0xB0–0xC8 한정 → false-positive 제거 (75K→46K, 36K→19K unique).
- TINY_META 구조 후보 발견: `(u16 count, u16 N) + 짧은 prefix record + count개 × 7-byte main record`.
  각 main record = `05 00 XX XX XX XX XX` 패턴, 0x2A–0x2D 마커 빈출.
  → **애니메이션 프레임 타이밍 / 히트박스** 후보. 정확한 의미는 Ghidra 필요.

#### 2-A.7 Hash 함수 복원 + 자산 이름 매칭 시도 — ✅ 부분 완료 (2026-05-07)

`tools/ghidra/DecompileHero5Keys.java` 의 PAT 확장으로 `MIDASKernelManager::hash` 디컴파일 성공.

**해시 함수 = DJB2-like** (`work/h5/analysis/key_funcs.c:479-502`):
```python
def hash_hero5(name: str) -> int:
    h = 0x1505                              # = 5381
    for c in name.encode():
        h = (c + h * 0x21) & 0xFFFFFFFF     # mul = 33
    return h
```

`AndroidService::getUniqueAssetNameFromID` 도 디컴파일했으나 **JNI 브리지** — 실제 이름 테이블은 Java DEX 의 `CletEntry.getUniqueAssetNameFromID(int)` 메소드 내에 있음.

**자산 이름 매칭 시도 결과**: `tools/h5_recover_names.py` 로 `classes.dex` 의 4,046 문자열 + 변형(.bin/.png/.dat 추가, 0–199 numeric suffix, 대소문자) 시도 → 직접 매칭 0건. 1건만 누적 brute-force 에서 false-positive (`IAP_PARITY_BIT148`).
**결론**: 자산 이름은 DEX 메소드 바이트코드 내 switch/case 또는 `resources.arsc` 에서 런타임 구성됨. **jadx/baksmali 없이는 추가 진전 불가**.

산출:
- `tools/h5_recover_names.py` — hash + DEX string 매처 (jadx로 더 많은 후보 확보 시 재실행)
- `work/h5/analysis/asset_names.tsv` — 1건 false-positive
- `work/h5/analysis/key_funcs.c:479-502` — hash 함수 디컴파일

#### 2-A.8 DEX 메소드 분석 — ✅ 완료 (2026-05-07)

`tools/h5_dex_extract_names.py` (순수 Python DEX 파서, 의존성 없음) 으로 `classes.dex` 의
모든 메소드를 walk 하며 const-string 시퀀스 + 메소드 dump 생성.

**핵심 발견** — `getUniqueAssetNameFromID` 는 **양쪽 모두 stub**:
- `Lco/kr/eamobile/CletEntry;::getUniqueAssetNameFromID` (7 code units): `setContentView` 호출 후 return.
- `Lco/kr/eamobile/resource/MidasAssetManager;::getUniqueAssetNameFromID` (13 code units): `getResources/finish` 호출 후 return null.
- → 자산 이름 → ID 매핑은 **빌드 타임에 계산되어 native binary 에만 존재**, Java 측엔 없음.

**brute-force 한계 검증** — `tools/h5_recover_names_v2.py`:
- pool: DEX strings (4,046) + libHeroesLore5.so 식별자 (6,529 unique) = 8,313개
- 변형 (확장자 17종 × 대소문자 × path-sep + numeric suffix 0–999 + 30 prefix × 0–999):
  추정 총 ~30M candidate hash 평가
- 결과: **5건 매칭 (`version.txt` 1건만 진짜)**, 나머지 4건은 32-bit DJB2 충돌 false-positive
- 결론: 8K base × 변형으론 32-bit hash space 충분히 못 메움. **이름 리스트 자체가 native binary 안에 packed 되어 있을 가능성 높음** — Ghidra 로 `loadAssetFromVFS` caller 추적 시 string array 발견 여부 확인 필요.

산출:
- `tools/h5_dex_extract_names.py` — DEX 메소드 파서 + 명령어 dump
- `tools/h5_recover_names_v2.py` — 확장 brute-force
- `work/h5/analysis/dex_const_strings.tsv` — 449 메소드 × const-string 시퀀스
- `work/h5/analysis/asset_name_candidates.txt` — 1,236 unique const-string 값
- `work/h5/analysis/so_strings.txt` — 6,529 unique .so 식별자 후보

#### 2-A.9 TINY_META 정식 파서 — ✅ 완료 (2026-05-07)

`tools/converter/convert_h5_meta.py`. 가설(2-A.6) 검증 후 **kind=row-width 파라미터** 발견 (kind=3, 5 두 종 확인).

**확정 포맷**:
```
u16 total_count
u16 kind                              ; row payload width parameter
prefix row [kind bytes]:
   [0]=kind, [1]=body_count, [2:]=prefix_payload
body_count rows × (kind+2) bytes each:
   [0]=kind, [1]=subtype (보통 0x00), [2:kind+2]=payload (0xff = 빈 슬롯, 0x2a-0x2d = field marker)
```

총 파일 사이즈 = `4 + kind + body_count × (kind+2)`.

검증:
- 00075/76/78 (30B): total=4, kind=5, body=3 → 4+5+21=30 ✓
- 00077 (44B): total=6, kind=5, body=5 → 4+5+35=44 ✓
- 00080 (32B): total=6, kind=3, body=5 → 4+3+25=32 ✓ (kind=3 케이스)

**결과**: ≤50B bin 후보 356개 중 **7개 strict match** (kind 5×6 + kind 3×1). 나머지 349개는 다른 mini-format (`0100`, `09ee`, `0b6a` 등 별도 시그니처). residual 의 TINY_META 카테고리(104) 중 일부만이 이 표준형식이고 나머지는 다른 small-record container.

산출:
- `tools/converter/convert_h5_meta.py` — 파서
- `work/h5/analysis/tiny_meta.tsv` — row-level dump
- `work/h5/analysis/tiny_meta_summary.txt` — 통계

#### 2-A.10 자산 이름 99.3% 복원 — ✅ 완료 (2026-05-07)

**돌파구**: Ghidra 로 `loadAssetFromVFS` caller 추적 → `getAssetSizeFromVFS(this, assetname, ...)`
가 **string 직접 사용** 확인 → 이름이 native binary 안에 sprintf format-string 으로 박혀 있음.

`.so` 의 모든 format string 스캔 (`tools/h5_recover_names.py` pass 1):
```
c/calc/calc_<region>.dat       c/csv/<table>.dat / enemy_/item_/quest_/skill_/etc
c/csv2/help_<region>.dat        c/font/{eng,kor}.fnt + table.dat + type.dat
c/img/<ui>.mgr                  c/sp/img{0..6}/%03d.mgr
c/sp/cif/%03d.cif               c/sp/ext/%03d.ext
c/sp/imgcom/<named>.mgr         c/sp/empty/empty.mgr
c/sp/pal/%03d.pal (557개)       c/map/{face_%02d, obj_%03d, fgi_%03d, tile_%03d}.gbm
c/map/seaani_%03d.pal           c/map/%05d.scn (5-digit numeric scenes)
c/map/(md)%02d                   c/map_sp/{fgi%03d, ms%03d, ms_img%02d.mgr, %03d.ext}
c/mon/%d_ai                     c/par/{p%03d, ps%03d, pimg%02d.mgr, pinfo.dat}
c/snd/{bgm_%02d, eff_%02d}.{ogg,mmf}
c/iconpal/{226..232}_%03d.pal   c/ep/ep_%d/s%d_%03d.scn
```

**결과 진행**:
| 단계 | 매칭 | 누적% |
|---|---:|---:|
| pass 1 (.so suffix slice) | 78 | 3.6% |
| pass 2 (sprite/pal numeric) | 1,205 | 55.0% |
| pass 3 (map/snd/par/mon/ep + map %05d.scn) | 2,171 | 99.2% |
| pass 4–7 (iconpal/csv/named) | 2,174 | **99.3%** |

**잔여 15개**: 짝지어진 동일 크기 (1141/1142, 1644/1645) i18n 추정 + 큰 파일 (37KB) + 작은
isolated bins. 후속 작업으로 보류.

**False-positive 위험**: 32-bit DJB2 충돌 가능성 있으나, 패턴이 매우 구조적
(c/<dir>/<numbered>) 이고 90% 이상이 연속 인덱스 클러스터로 매칭되어 매우 낮음.

산출:
- `tools/h5_recover_names.py` — 통합 복원기 (pass 0–7)
- `tools/h5_dex_extract_names.py` — DEX 파서 (CletEntry/MidasAssetManager 분석 확인)
- `tools/ghidra/FindAssetNameTable.java` — caller XREF + .rodata string-array 스캐너
- `tools/ghidra/DecompileNameLookup.java` — `getUniqueAssetNameFromID` JNI 브리지 본문
- `work/h5/analysis/asset_names.tsv` — **2,174 / 2,189 (99.3%) 복원된 이름**
- `work/h5/analysis/asset_callers.c` — caller 디컴파일
- `work/h5/analysis/name_lookup.c` — JNI 브리지 + hash 함수

**핵심 발견 (PROGRESS 6.2 [P1] 가설 수정)**:
- `MidasAssetManager.assetNameFromNumericHash` (Java Hashtable) 는 **DEX 에서 절대 populate 안 됨**
- C++ `AndroidService::getUniqueAssetNameFromID` 는 JNI 로 빈 Hashtable 을 lookup 하므로 **항상 null 반환**
- → 게임 코드는 native side 에서 **string literal 직접 사용** (`MC_knlGetResourceID(name)` 등)
- → 이름 → ID 매핑은 빌드 타임에만 존재, 런타임에는 hash 만 사용

#### 2-A.11 .scn 포맷 분석 — ✅ 헤더 완료 (2026-05-07)

`EventProc::Scene_Init @ 0x000823a8` 디컴파일 (`work/h5/analysis/scn_loader.c`) 으로
.scn 파일 로드 흐름 확정:

1. **경로 생성**: `MC_knlSprintk(buf, "/c/map/%05d.scn", mapNum)` 또는
   `"/c/ep/ep_%d/s%d_%03d.scn"` (mode 따라 분기).
2. **로드**: `StaticUtil::LoadRes(path, &size)` — `loadAssetFromVFS` 의 사용자 래퍼.
3. **헤더 파싱** (11 bytes, sequential cursor):
   ```
   u8 flag1, flag2, state, mapID, dialogID, b5, startX, startY, startDir, b9, b10
   ```
4. **타일/이미지**: 별도 `c/map/{face,obj,fgi,tile,seaani}_NN.gbm` 파일을
   `mapID` 인덱스로 `Map::LoadData` / `Map::LoadImage` 가 로드.
5. **나머지 body**: `Interpreter::open(scn_buf+11, &cursor, flag1, flag2)` —
   이벤트 스크립트 바이트코드. opcode 정의는 `Token::*` / `Interpreter::execute`
   추가 분석 필요 (Phase 3 진입 후 우선과제).

**결과** (`tools/converter/convert_h5_scn.py`):
- 258/258 .scn 파일 헤더 파싱 성공 (100%)
- 67개 unique mapID → 실제 맵 데이터 세트 67개, 시나리오 258개
- 모두 state=1 → flag2 매직 분기 ('mmonUiC1Ev' 호환) 적용됨
- body 평균 276B (대사+이벤트 스크립트)

산출:
- `tools/ghidra/FindSceneLoader.java`, `DumpScnRef.java`, `DumpInterpreter.java`
- `work/h5/analysis/scn_loader.c` — Scene_Init 본문
- `work/h5/analysis/scn_headers.tsv` — 258개 헤더 dump
- `work/h5/analysis/scn_summary.txt` — mapID/body-size 분포

#### 2-A.12 다음 단계 (Phase 2 마무리)

1. ~~DEX 디컴파일러~~ → **차단 확정** (2-A.8). Java 메소드는 stub. 다음 단계는 **native binary 안의 string array 추적** — Ghidra 에서 `loadAssetFromVFS` 의 caller 들이 참조하는 .rodata 영역 string-pointer 배열을 찾아야 함.
2. ~~TINY_META 정식 파서~~ → 완료 (2-A.9). 다음: **payload 의 5 슬롯 의미 확정** — Ghidra 로 `MIDASKernelManager` 내 7-byte record 를 `fread` 하는 함수 검색.
3. **MID_SCRIPT/LARGE_ANIM 의 19 19 마커 의미** — 청크 분리자/프레임 표지자/end-of-record 후보.
4. **`loadAssetFromVFS` caller 분석** — `assetID` 가 어디서 어떤 컨텍스트로 오는지 → 파일 용도 분류 + 이름 테이블 위치 후보.
5. **Phase 3 진입** — 엔진 결정 (Unity 권장) + 자산 임포트 파이프라인.

### Phase 2-B. 자산 파일명 복원 — ⚠ 부분 완료
- ✅ Hash 함수 복원 (DJB2-like, 2-A.7 참조)
- ✅ `AndroidService::getUniqueAssetNameFromID` 디컴파일 (JNI 브리지로 확인)
- ❌ 이름 테이블은 Java DEX 내부 → **jadx/baksmali 필요**

### Phase 2-C. JNI 호출 흐름 → 게임 루프 정리
`Java_..._nativeLoop` 와 `MIDASKernelManager::timerLoop` 부터 시작. 60fps tick / event handling / render 호출 순서를 그래프로.

### Phase 3. 리메이크 엔진 결정 + 재구현 — ✅ 스캐폴드 완료 (2026-05-07)
**상세는 [PHASE3_ENGINE.md](PHASE3_ENGINE.md) + [apps/hero5-godot/README.md](../../apps/hero5-godot/README.md).**
- 엔진: **Godot 4** 확정.
- 자산 임포트 파이프라인: `tools/import_to_godot.py` — 5,000+ 자산 자동 변환.
  - sprites: 3,798 frame PNG
  - gbm: 342 map/face/obj/fgi 이미지
  - palettes: 588 JSON RGBA
  - text: 453 한글 JSON
  - sounds: 42 OGG (SMAF 미포함)
  - scenes: 258 .scn 메타 인덱스
- 검증 씬: `apps/hero5-godot/scenes/main.tscn` — face 토글 + 한글 코퍼스 표시.

#### 다음 본구현 작업
- [ ] Interpreter opcode → 이벤트 매핑 (164 opcode 의미 매핑)
- [ ] Map 렌더러 (tile/fgi/obj 레이어 합성)
- [ ] CHAR/HERO 시스템 (4방향 애니메이션)
- [ ] kor.fnt 임포트 / 한글 폰트
- [ ] SMAF → OGG 변환

---

## 6. 다음 세션 즉시 재개 체크리스트

### 6.1 현재 상태 한눈에 (2026-05-07 기준)

| 영역 | 상태 | 산출물 |
|---|---|---|
| VFS 언팩 | ✅ 2,189/2,189 (100%) | `work/h5/vfs_entries/` + `vfs_catalog.tsv` |
| 사운드 (ogg + SMAF) | ✅ 84/84 | `*.ogg`, `*.smaf` (SMAF→OGG 변환 추후) |
| 팔레트 _pa | ✅ 557 파싱 (RGB565 LE pair) | `tools/converter/convert_h5_pa.py` |
| 스프라이트 | ✅ 426 파일 / 3,798 PNG (유효 100%) | `tools/converter/convert_h5_sprite.py`, `work/h5/converted/sprites/` |
| 한글 코퍼스 | ✅ 18,837 unique strings | `work/h5/converted/text/_corpus.txt` |
| Hash 함수 | ✅ DJB2 (init=0x1505, mul=0x21) | `tools/h5_recover_names.py` |
| 자산 이름 복원 | ✅ 2,182 / 2,189 (99.7%) — .so format-string + region 변형 | `tools/h5_recover_names.py`, `work/h5/analysis/asset_names.tsv` |
| Anim/Script 파서 | ✅ 300 파일 record 분리 (sentinel 19 19 + 20 20) | `tools/converter/convert_h5_anim_script.py` |
| .scn 헤더 파서 | ✅ 258/258 파일 — 11B 헤더 + Interpreter 바이트코드 | `tools/converter/convert_h5_scn.py` |
| .scn body 디스어셈블 | ✅ 258 파일, 164 unique opcode | `tools/converter/disasm_h5_scn.py` |
| .gbm 디코더 | ✅ 342/342 (100%) — 4/8-bit indexed → PNG | `tools/converter/convert_h5_gbm.py` |
| Opcode 매핑 | ✅ 77/77 — `EventProc::onFunction` switch 분석 | `tools/h5_extract_opcode_table.py`, `work/h5/analysis/opcode_table.tsv` |
| Map 렌더러 | ✅ 4-layer (tile/obj/fgi/face) Sprite2D 합성 | `apps/hero5-godot/scripts/core/map_renderer.gd` |
| 캐릭터 시스템 | ✅ 4방향 이동 + 자동 frame 애니메이션 (CHAR 클래스 매핑) | `apps/hero5-godot/scripts/core/character.gd` |
| Interpreter 실행기 | ⚠ 골격만 (77 opcode dispatch + console log, dialog/move 실제 처리 후속) | `apps/hero5-godot/scripts/core/interpreter.gd` |
| 타이틀/데모 씬 | ✅ Title → Demo (map+character+interp) 흐름 | `apps/hero5-godot/scenes/title.tscn`, `demo.tscn` |
| 맵 데이터 (md)NN | ✅ 67 파일 헤더+섹션 인덱스 (10–14 sections per file) | `tools/converter/convert_h5_mapdata.py` |
| Interpreter 핸들러 | ✅ Teleport/Direction/Delay/ChangeBgm/TileChange + set_handler 훅 | `apps/hero5-godot/scripts/core/interpreter.gd` |
| 세이브/로드 | ✅ 평문 JSON, 8 slot, version 관리 | `apps/hero5-godot/scripts/core/save_manager.gd` |
| 한글 폰트 | ✅ eng=95×(8×11), kor=581×(16×11) PNG 시트 변환 | `tools/converter/convert_h5_fnt2png.py` |
| Dialog UI | ✅ typewriter 효과 + 한글 표시 + Interpreter 연결 | `apps/hero5-godot/scripts/ui/dialog_box.gd` |
| Status/Inventory UI | ✅ HP/SP/Lv/Gold/인벤토리 패널 (ESC/I 토글) | `apps/hero5-godot/scripts/ui/status_panel.gd` |
| Map Collision | ✅ 67/67 (md) → JSON+col.bin+tile.bin, MapRenderer 통합 | `tools/converter/convert_h5_collision.py` |
| CSV 게임 데이터 | ✅ 85 .dat → JSON (record format 확정), GameData 싱글톤 | `tools/converter/convert_h5_csv.py`, `scripts/core/game_data.gd` |
| 전투 시스템 | ✅ 골격 (4 액션: 공격/스킬/방어/도망) | `apps/hero5-godot/scripts/core/battle_system.gd` |
| Class stats 디코딩 | ✅ 5 클래스 STR/DEX/INT/CON 추출 (워리어/로그/건슬링어/나이트/소서러) | `tools/converter/decode_h5_class.py` |
| 전투 UI | ✅ Enemy/Player HP bar + 4 action 버튼 + 로그 | `apps/hero5-godot/scenes/battle.tscn` |
| Collision 디버그 | ✅ 통과/막힘 오버레이 (C 키 토글) | `MapRenderer.show_collision_debug` |
| 한글 자모 조합 | ⚠ 게임 자체 인코딩 (표준 EUC-KR 아님), 추가 RE 필요 | — |
| .fnt 분석 | ⚠ 헤더만 (HNF eng=8×11/92 chars, kor=16×11/580 chars) | `tools/converter/convert_h5_fnt.py` |
| SMAF 변환 | ⚠ 미구현 (외부 도구 필요), OGG 42개로 대체 가능 | `tools/converter/convert_h5_smaf.py` |
| TINY_META 파서 | ✅ 7/356 strict match (kind 3·5 변형 확정) | `tools/converter/convert_h5_meta.py` |
| Ghidra 프로젝트 | ✅ 함수 19개 디컴파일 | `work/h5/ghidra_project/Hero5` |

### 6.2 다음 즉시 작업 — 우선순위 순

**[P1] DEX 디컴파일러 도입 → 자산 이름 복원** (가장 큰 unlock)
```bash
# Option A: jadx (GUI + CLI)
#   https://github.com/skylot/jadx/releases  → jadx-1.5.x.zip 압축 해제
#   jadx work/h5/extracted/classes.dex -d work/h5/dex_decompiled
# Option B: baksmali (smali bytecode)
#   wget https://bitbucket.org/JesusFreke/smali/downloads/baksmali-2.5.2.jar
#   java -jar baksmali-2.5.2.jar d work/h5/extracted/classes.dex -o work/h5/smali

# 추출 후:
grep -rn "getUniqueAssetNameFromID" work/h5/dex_decompiled/  # 또는 smali/
# → 메소드 본문에서 이름 테이블 / switch 케이스 추출
# → tools/h5_recover_names.py 의 candidate 리스트에 주입 후 재실행
python tools/h5_recover_names.py  # 매칭 완료 시 work/h5/analysis/asset_names.tsv 갱신
```

**[P2] TINY_META 7-byte record 파서**
```bash
# 가설: (u16 count, u16 N) + prefix record + count×7-byte main record
# 후보 record: `05 00 XX XX XX XX XX` with 0x2A-0x2D 마커
# 검증 데이터: 104 파일 (work/h5/vfs_entries/ 중 5-50B, _pa 제외)
ls work/h5/vfs_entries/ | head
# 우선 5–10개 파일 hexdump 비교 → record 의미 추정
# → tools/converter/convert_h5_meta.py 작성 (예정)
# → Ghidra: 'MIDASKernelManager::loadFrameMeta' 등 함수 검색해서 디컴파일 추가
```

**[P3] 19 19 마커 의미 (스크립트 디스어셈블)**
```bash
# MID_SCRIPT 31 + LARGE_ANIM 177 파일에서 0x19 0x19 가 청크 분리자로 사용
# 우선 00055_641e44fa.bin (메인 대사 22KB) 의 19 19 위치 분포 분석
python -c "
import pathlib
d=pathlib.Path('work/h5/vfs_entries/00055_641e44fa.bin').read_bytes()
hits=[i for i in range(len(d)-1) if d[i]==0x19 and d[i+1]==0x19]
print(f'{len(hits)} markers, first deltas: {[hits[i+1]-hits[i] for i in range(min(20,len(hits)-1))]}')
"
# → 청크 길이 패턴으로 record 구조 추정
```

**[P4] Phase 3 진입 (엔진 결정)**
- Unity 2022 LTS vs Godot 4 vs 자체 Kotlin/Compose 비교
- 결정 후 `apps/hero5-android/` 또는 `apps/hero5-unity/` 스캐폴드
- Hero3 의 `android/` 디렉토리 구조를 참고

### 6.3 환경 / 도구 빠른 참조

```bash
# VFS 재언팩 (catalog 깨졌을 때만)
python tools/h5_vfs_unpack.py

# 스프라이트 일괄 디코딩
python tools/h5_decode_sprites.py

# 한글 텍스트 일괄 추출
python tools/h5_extract_text.py

# 잔여 카테고리화 / 클러스터링
python tools/h5_residual_classify.py
python tools/h5_residual_cluster.py
```

```bash
# Ghidra 추가 함수 디컴파일
#   tools/ghidra/DecompileHero5Keys.java 의 PAT 정규식에 함수명 추가 후:
"D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
  "D:/testrepo/work/h5/ghidra_project" Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath "D:/testrepo/tools/ghidra" \
  -postScript DecompileHero5Keys.java
# → work/h5/analysis/key_funcs.c 갱신

# Ghidra GUI (수동 분석)
"D:/ghidra_12.0.4_PUBLIC/ghidraRun.bat"
# → Open project → D:/testrepo/work/h5/ghidra_project/Hero5
```

### 6.4 핵심 산출물 인덱스

| 무엇 | 어디 |
|---|---|
| VFS catalog | `work/h5/vfs_catalog.tsv` |
| 디컴파일 코드 (19 함수) | `work/h5/analysis/key_funcs.c` |
| 심볼/JNI/문자열 dump | `work/h5/analysis/so_quick.txt` |
| 스프라이트 PNG | `work/h5/converted/sprites/<file>/frame_NN_*.png` |
| 한글 코퍼스 | `work/h5/converted/text/_corpus.txt` |
| 잔여 카테고리 리포트 | `work/h5/analysis/residual_categories.txt` |
| 미매칭 클러스터 dump | `work/h5/analysis/unknown_clusters.txt` |
| _pa 시각화 컨택트시트 | `work/h5/analysis/pa_swatches/_index.html` |
| 자산 이름 매칭 (1건 FP) | `work/h5/analysis/asset_names.tsv` |

### 6.5 최근 커밋 히스토리 (작업 추적)

```
89a4fdc  Ghidra hash 함수 복원 (DJB2-like)
79759b8  한글 추출 필터 개선 (한자 false-positive 제거)
637b164  잔여 분류 + 한글 텍스트 75,284개 추출
c011eae  sprite 디코더 type=0x04/0x08/0x18 추가 (유효 frame 100%)
fbfaebe  Phase 2-A.4 sprite 디코더 (84% 프레임 렌더링)
8aec053  Phase 2-A.2~3 _pa 인코딩 확정 + 미매칭 클러스터링
c57be91  Phase 2-A.1 bin 포맷 호환성 프로브
6a1c78a  영웅서기5 리메이크 대기중 (Phase 1 시작점)
```
