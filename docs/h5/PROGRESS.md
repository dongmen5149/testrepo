# Hero5 (영웅서기5) 진행 상황

> Hero3/4와 다른 트랙. 기존 Android APK 가 존재하지만 32-bit 전용이라 현대 폰 미지원.
> 전략 = **A. 자산 추출 + 엔진 재구현** (Hero3/4 인프라 재사용 가능).

업데이트: 2026-05-08 — **Phase 2 + Phase 3 핵심 시스템 모두 구현 완료**.
Godot 프로젝트 (`apps/hero5-godot/`) 에 Title→ClassSelect→Demo 전체 흐름,
전투/퀘스트/상점/세이브/HUD/이펙트 통합. 다음 세션 빠른 재개 — [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

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

### 6.1 현재 상태 한눈에 (2026-05-10, Round 24 종료)

**최근 (Round 6~19) 누적 발견 — Formula VM 변수 라벨 / EquipItemInfo struct / 카테고리 별 layout**:

| 영역 | 라운드 | 핵심 결과 |
|---|---|---|
| Formula VM gv stat | R6~12 | V[58]=level, V[60..63]=str/dex/con/int (R11 정정), V[111..116]=근접명중/장거리명중/회피/방패방어/크리티컬, V[122..126]=5 buff slot (EXP%/SP감소%/CP충전/쿨타임/포션효과), V[151..155]=magic/con/str/max_sp |
| ApplyBuildupEffect entry table | R9 | jumptable 자동 추출 (`tools/h5_apply_buildup_disasm.py`), 56 entry × 2 함수 |
| EquipItemInfo struct field | R13~17 | +0x14=subtype, +0x155=class subtype, +0x15d=level_limit, +0x15f & 0x1f = 5-class mask (W/R/G/K/S), +0x165..+0x167=refine fields, +0x168..+0x16d=6 socket |
| ItemBase struct (Formula VM 5번째 인수) | R13 | V[168..182] = SP cost / cooldown / damage growth / divisor 등 |
| LoadItemTable csv 매핑 | R14/18/19/20/21 | 가변 layout (name + sub_record) + u8/u16 mixed sequence. cat 12-18 모든 카테고리별 추가 fields 추출. R21: slot_16 도 SkillBook 임이 확인 (Warrior+Rogue) |
| items.json named fields | R15/16/19/20/21 | subtype / class_mask / class_label / level_limit / item_id / sub_record / val_134..val_167 / triplet_162 / sub_record_hex / **class_id, skill_index, skill_level, required_level** (slot_16, slot_17) |
| HERO::IfLearnSkill 분석 | R21 | (class_id/2)+16 → ItemTable category 공식. SkillBook +0x134..+0x137 의미 (class_id/skill_index/skill_level/required_level) 확정 |

**전체 진행 (Phase 2/3 완료 항목)**:


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
| DES key | ✅ `0EP@KO91` 추출 (MX_desInit caller @ 0x001688b0) | `tools/ghidra/DumpDes.java` |
| **DES 변종 해독** | ✅ 표준 DES + S1[3][10]=2 단일 수정 — `mx_des_decrypt(body, key)` MD5 검증 통과 | `tools/h5_des.py`, `tools/h5_decrypt_calc.py`, [`DES_VARIANT.md`](DES_VARIANT.md) |
| **calc_*.dat 평문** | ✅ 3개 파일 MD5 검증 통과 (calc_pl 1584B, calc_en 624B, calc_sk 4680B) | `work/h5/analysis/calc_*_plain.bin` |
| **Formula VM 디스어셈블러** | ✅ 186 공식 (39+19+128) infix 표현 dump, size mismatch 0 | `tools/h5_formula_disasm.py`, `work/h5/analysis/formulas_disasm.txt` |
| Fixed-size csv | ✅ enemy_g (166×121B), npc_g (81×27B) → JSON | `tools/converter/decode_h5_fixed.py` |
| GameState 통합 | ✅ 싱글톤 + state_changed signal + battle 보상 적용 + quick save/load | `apps/hero5-godot/scripts/core/game_state.gd` |
| enemy_g 121B layout | ✅ HP/MP/ATK/DEF/EXP/Gold + 5×16B skill slot 추출 (15/166 valid) | `tools/converter/decode_h5_enemy.py` |
| Walk-cycle 애니 | ✅ 4방향 walk_frames + stand_frames 시퀀스 자동 전환 | `character.gd` |
| Interpreter 핸들러 | ✅ 확장 (Camera/Effect/Move/Teleport/Quest/Warp 등 +15 종) | `interpreter.gd` |
| Android export 가이드 | ✅ arm64-v8a 64bit, min SDK 23 / target 34 설정 템플릿 | `apps/hero5-godot/export_presets.cfg.template`, `README.md` |
| MVP 정합성 검증 | ✅ tscn/gd reference 체크, 0 errors / 0 warnings | `tools/verify_godot_project.py` |
| enemy 정확도 | ✅ stride 공식 수정 (4 + i × 121), 75/166 valid HP/MP 확인 | `tools/converter/decode_h5_enemy.py` |
| NPC table | ✅ 81 × 27B 디코딩 + Demo E 키 인터랙션 | `tools/converter/decode_h5_npc.py` |
| Quest 데이터 | ✅ 105 quest 이름 + 72 tree 노드 (mission_list + questTree) | `tools/converter/decode_h5_quest.py` |
| GameData API 확장 | ✅ skills_for_class / items_in_slot / drop_table / shop_inventory / smith_recipes / enemy_stats | `apps/hero5-godot/scripts/core/game_data.gd` |
| 전투 시스템 — 실데이터 | ✅ enemy_table HP 기반 + 클래스 스킬 이름 표시 (양손베기/돌진/...) | `battle_system.gd` |
| Skill 분석 | ✅ 215 스킬 (5×43) 이름 + type + 한글 설명 분리 | `tools/converter/decode_h5_skill.py` |
| Item 디코드 | ✅ 19 슬롯, 1,360 명명 아이템 (포션/스킬북/장비), price=stats[0] | `tools/converter/decode_h5_item.py` |
| Quest tree | ✅ 72 노드 (대부분 root sequential, type=5) | quests.json |
| 사운드 hookup | ✅ Audio 싱글톤 + Event_Scene_ChangeBgm 핸들러, demo 자동 BGM | `apps/hero5-godot/scripts/core/audio_manager.gd` |
| Drop/Shop/Smith/Quest text/Rewards | ✅ 252+9+96+453+285 record 추출 | `tools/converter/decode_h5_misc.py` |
| Quest 진행 시스템 | ✅ Quest 싱글톤 + start/complete + Interpreter QuestStatus 핸들러 | `apps/hero5-godot/scripts/core/quest_system.gd` |
| Title slot 선택 | ✅ New Game / Continue + slot list 표시 | `apps/hero5-godot/scripts/ui/title.gd` |
| Skill 템플릿 resolver | ✅ `#NN` → stats_u16[NN] 치환 (예: 재사용대기 9초, 공격력 120%) | `game_data.gd::resolve_skill_desc` |
| Equipment 슬롯 | ✅ 6 슬롯 (무기/방어구/투구/장화/악세×2) + equip/unequip API | `game_state.gd` |
| Inventory UI 확장 | ✅ 장비 슬롯 표시 + 인벤토리 분리 | `status_panel.gd` |
| Combat 정밀 | ✅ MP 코스트 + cooldown + damage_pct (skill stat 사용) | `battle_system.gd` |
| Map NPC 스폰 | ✅ npc_table flags[0,2,3] = sprite/x/y → 마커 + 라벨 | `map_renderer.gd::spawn_npcs` (P키) |
| Item stat 정밀 | ✅ slot_0 무기 stats[7]=ATK, stats[0]=price 확정 | `game_data.gd::item_stat` |
| Damage popup | ✅ Tween 으로 -N 숫자 떠오름 + 페이드아웃 | `damage_popup.gd` |
| Dialog 선택지 | ✅ show_choices() + Quest 트리거 (NPC 분기 데모) | `dialog_box.gd::show_choices` |
| Scene → Hero 위치 | ✅ scene 헤더 startX/Y 로 캐릭터 tile 좌표 자동 배치 + BGM 전환 | `demo.gd::_apply_scene` |
| 상점 UI | ✅ ShopPanel — 무기 4 슬롯 × 4 offer 구매/판매 + 골드 차감 | `apps/hero5-godot/scripts/ui/shop_panel.gd` |
| 레벨업 자동 | ✅ STR/DEX/INT/CON 클래스별 분배 + lvl 5/10/15... 스킬 해금 | `game_state.gd::add_battle_reward` |
| NPC 가까움 감지 | ✅ Manhattan 거리 기반 nearest_npc(px, py, dist) | `map_renderer.gd::nearest_npc` |
| 다중 세이브 슬롯 | ✅ Title 에 slot 버튼 자동 생성 + Demo 1-8 저장 / Shift+1-8 로드 | `title.gd`, `demo.gd` |
| 레벨업 popup | ✅ DamagePopup으로 "LEVEL UP! → N" + dialog 알림 + 해금 스킬 표시 | `demo.gd::_on_level_up` |
| 장비 stat 자동 적용 | ✅ equipment_bonus / total_attack/defense → 전투에 반영 | `game_state.gd` |
| Quest UI | ✅ 활성/완료 분리 ItemList + 정보 패널 (Q키) | `quest_panel.gd/.tscn` |
| BGM cross-fade | ✅ 0.3+0.3s tween 으로 부드러운 전환 | `audio_manager.gd::_fade_swap` |
| 클래스 선택 화면 | ✅ Title → New Game → Class Select → Demo (5 클래스 + stat) | `apps/hero5-godot/scenes/class_select.tscn` |
| NPC sprite 텍스처 | ✅ sprite_id → sprites/imgN/NNN/frame_00 자동 검색 (없으면 색박스) | `map_renderer.gd::_try_load_npc_sprite` |
| 포션/장비 사용 | ✅ inv 더블클릭 → 포션 사용 (HP+30) / 무기/방어구 자동 장착 | `status_panel.gd::_use_item` |
| 세이브 메타 확장 | ✅ play_time/class_id/stats/equipment/unlocked_skills/quest 포함 | `save_manager.gd::make_payload` |
| Sprite name → dir 매핑 | ✅ 405 sprite_index.json + AssetLoader.sprite_dir() API | `tools/import_to_godot.py`, `asset_loader.gd` |
| Title 로고 자동 | ✅ `c/sp/imgcom/title.mgr` → 자동 첫 frame 로딩 | `title.gd` |
| Stat 분배 UI | ✅ Status panel +STR/+DEX/+INT/+CON 버튼, 레벨업당 +3 점수 | `status_panel.gd`, `game_state.gd::allocate_stat` |
| Battle 적 sprite | ✅ enemy flags_a[0]=sprite_id 로 첫 frame 표시 | `battle_ui.gd::_load_enemy_sprite` |
| Quest 보상 자동 | ✅ complete 시 gold + exp + 미들포션 자동 지급 | `quest_system.gd::_grant_reward` |
| Quest 처치 카운트 | ✅ on_enemy_killed → 카운트/목표 추적 + 자동 complete | `quest_system.gd::on_enemy_killed` |
| Map warp trigger | ✅ collision 0x40-0x7F = 다음 scene 인덱스, hero.moved signal 연동 | `map_renderer.gd::check_warp` |
| NPC 한글 대사 | ✅ quest_text.json 의 한글 발췌 → NPC 대화로 표시 (3 episodes) | `game_data.gd::quest_dialogue` |
| 이펙트 애니메이션 | ✅ EffectAnim.spawn_at() — c/sp/imgcom/eff frame 시퀀스, 12fps | `effect_anim.gd` |
| HUD | ✅ 상단 HP/SP bar + Lv + Gold (state_changed 자동 갱신) | `apps/hero5-godot/scripts/ui/hud.gd` |
| 슬롯 삭제 UI | ✅ Title 에서 우클릭/Shift+클릭 → AcceptDialog 확인 → delete | `title.gd::_confirm_delete` |
| NPC 색상 분류 | ✅ flags[6] 따라 일반/적대/상인/퀘스트 4 색 modulate | `map_renderer.gd` |
| Inventory 필터 | ✅ 전체/무기/방어/포션/기타 5 탭 | `status_panel.gd::_matches_filter` |
| HP/SP 회복 | ✅ 비전투시 2초마다 max/50 HP, max/30 SP 회복 | `game_state.gd::_process` |
| 장비 비교 툴팁 | ✅ inv hover 시 ATK 값 + 현재 무기 대비 차이 표시 | `status_panel.gd::_on_item_hover` |
| Mini-map | ✅ 우상단 64×64 collision + warp + hero/NPC 마커 | `minimap.gd/.tscn` |
| Settings 패널 | ✅ BGM/SFX 볼륨 슬라이더 + FPS/Fullscreen 토글 | `settings_panel.gd` (X키) |
| 자동 적 인카운터 | ✅ 25 step 후 10% 확률 (UI 열림 시 skip) | `demo.gd::_on_hero_moved` |
| 자동 저장 | ✅ slot 7 (AUTO_SLOT) 60초 간격 + oldest_slot() API | `save_manager.gd::auto_save`, `game_state.gd` |
| Tile attribute 디버그 | ✅ V키 토글 — tile_id 별 색상 + 숫자 표시 | `map_renderer.gd::_draw` |
| Quest 보상 정밀 | ✅ rewards.json 의 6B record (type byte) → gold/exp/item 분기 | `quest_system.gd::_grant_reward` |
| Battle turn 표시 | ✅ "턴 N — 플레이어/적이름" + 색 변경 + 버튼 비활성화 | `battle_system.gd`, `battle_ui.gd` |
| Inventory 정렬 | ✅ default/name/price cycle (정렬 버튼) | `status_panel.gd::cycle_sort` |
| Quest 토스트 | ✅ 시작/완료 시 우상단 잠시 + 페이드 | `apps/hero5-godot/scripts/ui/toast.gd` |
| Settings 영구 저장 | ✅ user://config.cfg (BGM/SFX/FPS/fullscreen) | `settings_panel.gd::_save_config` |
| 도주 % 표시 | ✅ flee_chance() (HP%/DEX/turn 기반) → 버튼 라벨 실시간 갱신 | `battle_system.gd`, `battle_ui.gd` |
| Help 패널 | ✅ H 키 — 모든 단축키 BBCode 표시 | `help_panel.gd/.tscn` |
| Map 이름 표시 | ✅ 씬 진입 시 화면 중앙 큰 라벨 2초 + 페이드 | `demo.gd::_show_map_name` |
| 메뉴 별 BGM | ✅ Title bgm_00, ClassSelect bgm_01, Demo mapID%21 | `title.gd`, `class_select.gd` |
| ATK/DEF 합산 표시 | ✅ Status panel 에 total + 장비 보너스 분리 표시 | `status_panel.gd::_apply`, `status_panel.tscn` |
| 방어구 hover 비교 | ✅ 무기/방어구/포션 자동 분류, 슬롯별 ATK 또는 DEF diff | `status_panel.gd::_on_item_hover` |
| Battle 결과 popup | ✅ 승리 시 EXP/Gold/획득 아이템 패널 + 확인 버튼 (4초 자동 닫힘) | `battle_ui.gd::_show_victory_popup` |
| Battle drop | ✅ enemy stats exp/gold + 25% drop_table roll, items 배열 emit | `battle_system.gd::_finish/_roll_drops` |
| 씬 전환 fade | ✅ Title↔ClassSelect↔Demo 0.3s 검정 fade-out / fade-in | `scripts/ui/scene_fader.gd` |
| OPCODE_TABLE 확장 | ✅ 77/77 — BASE_TABLE 38 + 외부 opcode_table.json 자동 머지 (.so disasm 추출) | `interpreter.gd::BASE_TABLE/_try_load_external` |
| Dispatch 정리 | ✅ 중복 case 제거, Quest/Situate/Scene 핸들러 정렬, 외부 JSON 활성화 시 자동 매칭 | `interpreter.gd::_dispatch` |
| Scene body 자동 실행 | ✅ import 시 .scn body 11B 이후를 `assets/scenes/bodies/<idx>.bin` 저장, run_intro 가 step() 호출 | `import_to_godot.py::import_scn_index`, `demo.gd::_run_intro` |
| Quest opcode 핸들러 | ✅ 0x29 Boss / 0x2a QSwitch / 0x2b Status / 0x2c Switch — `.so disasm 검증` | `demo.gd::_on_quest_*` |
| Opcode 77/77 추출 (Ghidra-free) | ✅ ARM disasm + jumptable 추적 → opcode_table.tsv/json 자동 생성 | `tools/h5_extract_opcode_disasm.py`, `apps/hero5-godot/assets/scenes/opcode_table.json` |
| Event 함수 mangle 분석 | ✅ 105 Event_* 식별자 → arg_size 자동 룩업 (Itanium ABI demangle) | `tools/h5_event_arg_sizes.py`, `analysis/event_arg_sizes.tsv` |
| BASE_TABLE 매핑 수정 | ✅ Quest 0x31~0x42 추측 → 정확한 0x29~0x2d (.so 검증), Scene_ChangeBgm dead entry 제거 | `interpreter.gd::BASE_TABLE` |
| 자산 환경 복원 | ✅ APK 재추출 + VFS 2189 unpack + 99.7% 이름 + 421 sprite / 588 pal / 258 scn body | tools 전체 |
| enemy_g layout 검증 | ✅ Map::MapEnemyG_set + ByteToInt16 disasm — HP/MP/ATK/DEF/EXP/Gold offset 0x0c~0x16 LE u16 확정 | `tools/h5_extract_enemy_layout.py`, `decode_h5_enemy.py` |
| Battle 정확도 | ✅ enemy DEF 데미지 차감 + EXP/Gold 검증된 stat 사용 + sentinel(65535) 자동 fallback | `battle_system.gd::_stat_or/_finish` |
| .fnt 분석 | ⚠ 헤더만 (HNF eng=8×11/92 chars, kor=16×11/580 chars) | `tools/converter/convert_h5_fnt.py` |
| SMAF 변환 | ⚠ 미구현 (외부 도구 필요), OGG 42개로 대체 가능 | `tools/converter/convert_h5_smaf.py` |
| TINY_META 파서 | ✅ 7/356 strict match (kind 3·5 변형 확정) | `tools/converter/convert_h5_meta.py` |
| Ghidra 프로젝트 | ✅ 함수 19개 디컴파일 | `work/h5/ghidra_project/Hero5` |

### 6.2 완료된 우선순위 작업 (2026-05-08 일괄 완료)

> Phase 2 (자산 추출/디코딩) + Phase 3 (Godot 엔진 + 게임 시스템) + 모든 우선순위
> 작업 완료. 현재 상태와 다음 작업은 [SESSION_HANDOFF.md](SESSION_HANDOFF.md) 참조.

**[P2] enemy_g 121B layout — ATK/DEF 정확도** — ✅ 완료 (2026-05-08)
- `Map::MapEnemyG_set` 디스어셈블 + `StaticUtil::ByteToInt16` 분석으로 121B record 의
  byte layout 100% 확정. 도구: `tools/h5_extract_enemy_layout.py`.
- 기존 PROGRESS hint (HP@0x0c, MP@0x0e, ATK@0x10, DEF@0x12 LE u16) 가 **이미 정답**
  이었음을 .so disasm 으로 검증. 추측 → 검증 끝.
- 추가 발견: stat5/stat6 = EXP@0x14, Gold@0x16 (LE u16). flags_b 영역은 0x18..0x23
  (12 byte). 5× skill slot 시작은 0x24 (기존 코드의 0x27 보다 3 byte 당김).
- 65535 sentinel 처리 통합: `battle_system._stat_or()` 가 invalid 값 자동 fallback.
- 결과: HP 75/166 valid (PROGRESS 핸드오프와 정확히 일치), ATK 7/166, DEF 4/166.
  나머지는 enemy_g 의 sparse 영역 — 게임이 사용 안 함.

**[P1] Interpreter opcode 자동 dispatch** — ✅ 77/77 완료 (2026-05-08)
- ARM disasm + jumptable 추적으로 `EventProc::onFunction` 의 77 case 모두 자동 추출
  (`tools/h5_extract_opcode_disasm.py`, capstone + lief). Ghidra 불필요.
- 산출: `apps/hero5-godot/assets/scenes/opcode_table.json` (77 entries) — interpreter.gd
  의 외부 로더가 자동 머지 → BASE_TABLE 38 ↔ 외부 77.
- **BASE_TABLE 의 잘못된 추측 매핑 수정** (.so disasm 으로 검증):
  - Quest 계열 0x31~0x42 → 실제 0x29~0x2d (PROGRESS hint 가 추측이었음)
  - `Event_Scene_ChangeBgm` 은 실제로 dispatch table 에 없음 — BGM 변경은
    `demo._apply_scene` 의 `Audio.play_bgm` 직접 호출로만 처리.
- demo.gd `set_handler` 호출 정확한 op 로 수정 (0x29/0x2a/0x2b/0x2c).
- demo.gd `_run_intro` 가 dead `Interp.new()` 대신 멤버 `_interp` 사용 + `body_path`
  존재 시 `step(bytes, 64)` 자동 실행. import 가 .scn body 258개를
  `assets/scenes/bodies/<idx>.bin` 으로 export.
- Itanium C++ ABI mangle 파서 (`tools/h5_event_arg_sizes.py`) 로 105 Event_* 함수의
  arg_size 모두 추출 — `Eh`=1, `Ehh`=2, `Eaht`=4 등.

**[자산 환경 복원] 이 머신에서 처음부터 추출** — ✅ 완료 (2026-05-08)
- APK 압축 풀기 → `work/h5/extracted/` (assets, lib/armeabi/libHeroesLore5.so).
- VFS unpack 2189 entries (path D: → C: 수정).
- 자산 이름 99.7% 복원 (.so 의 sprintf format-string 기반).
- sprite 421 + palette 588 + sound 42 + scn 258 + 한글 코퍼스 18,837 변환.
- import_to_godot.py 로 Godot assets/ 완전 채움 — verify **0 errors / 0 warnings** 처음 달성.
- import 도구 확장: vfs/asset_names 매칭 시 .scn body 258개 자동 export.
- 신규 도구: `tools/h5_batch_sprite.py` (single-file argv converter 의 batch wrapper).

**[P3] Stats UI 합산 표시 + 장비 비교 패널** — ✅ 완료 (2026-05-08)
- Status panel 의 ATK/DEF 총합 라벨 추가 (`status_panel.gd::_apply`).
- 인벤 hover 비교: `_item_kind()` 로 무기/방어구/포션 분류 후 슬롯별 ATK/DEF diff
  표시 (방어구 = SLOT_ARMOR/HELMET/BOOTS 자동 매핑).

**[P4] Battle 결과 화면 + 메뉴 페이드** — ✅ 완료 (2026-05-08)
- 승리 popup: 중앙 패널에 EXP/Gold/획득 아이템 리스트 + 확인 버튼 (4초 자동 닫힘).
  drop_table 25% 확률 + enemy stats exp/gold 우선 사용.
- 씬 전환 fade: `SceneFader.change_scene()` (out 0.3s) +
  `SceneFader.fade_in()` (in 0.3s). Title/ClassSelect/Demo 진입 시 자동 fade-in.
- pre-existing 버그 수정: demo.gd 의 `_battle_ui.has_signal()` 호출이
  `_battle_ui` 인스턴스화 전이라 항상 nil — connect 위치를 인스턴스화 직후로 이동.

### 6.2.1 다음 우선순위 (남은 작업)

**[Round 24 — 2026-05-10 완료]** val_15f upper 3 bit (tier_flags) 의미 식별
- ✅ **핵심 발견: csv val_15f vs runtime val_15f 용도 분리**
  - csv load: lower 5 bit = class_mask, upper 3 bit = tier_flags
  - runtime: SetItemOption (0xa0ff8) 가 +0x15f 를 option_type code 로 덮어씀
  - GetRelieveLevelLimit (0xa835c) 의 `cmp #0x6c` 는 runtime option_type 비교
  - MakeItemOption (0xa10e8) 가 val_15c (option_grade) 로 SetItemOption 호출 여부 결정
- ✅ **upper 3 bit 의 실증적 의미 (items.json 789 EquipItem 분포 분석)**:
  - upper=0 (170 records, no flags): **legendary** — 실가라스/투란기어/디바인세이버 등 보스/named 무기
  - upper=1 (248, bit5): **rare** — 중급 무기/방어구
  - upper=3 (9, bit5+6): **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔 등 9종 only)
  - upper=7 (362, bit5+6+7): **common** — 일반 상점 아이템 (롱소드/단검 등)
- ✅ 가설: bit5 = "obtainable", bit6 = "gem-accessory", bit7 = "common-tier"
- ✅ slot_4 (armor) 1 record "스태프" 가 tier=legendary + class_mask=0 인 점이 Round 22
  Sorcerer 미구현 stub 사실과 cross-confirm (Sorcerer 전용 staff 인데 사용 가능 클래스 0개)
- ✅ `decode_h5_item.py::parse_equip_extra` 에 `tier_flags` (정수 0/1/3/7) +
  `tier_label` (legendary/rare/gem/common) string 부여.
- ⏸ 정확한 비트 의미는 더 disasm 필요 (NewDropItem / DropTable cross-check).
  현재 라벨은 records 분포 기반 실증적 추정.

**[Round 23 — 2026-05-10 완료]** HERO::BattleUseItem 분석 + SLOT_META 전면 정정
- ✅ **HERO::BattleUseItem (0x8fd20, 536B) 디스어셈블** → slot_11 의 4 byte fields
  의미 정확 식별:
  - `+0x134` = **effect_type** (HERO[0x2fe] 에 저장 → CalcStatusComputation 분기)
    - 91 (0x5b) = HP heal, 90 (0x5a) = SP heal, 87 (0x57) = buff (보호의 부적)
    - 92 (0x5c) = 마석, 19 (0x13) = test (포션9), 0 = 제련석 (무효)
  - `+0x135` = **success_rate %** (random(0,99) 와 비교, 모든 records 100)
  - `+0x136` = **effect_value** (HERO[0x300] u16: HP/SP 회복량 또는 buff 강도)
    - 포션 LV1/2/3: 4/10/20, 퀵포션: 40/100/160, 엘릭서: 250
  - `+0x137` = **duration** (HERO[0x302] s16: HP buff=50, SP instant=1, 보호의부적=120)
  - 사용 후 SetPotionCoolTime(100) — 100 frame cooldown.
- ✅ SLOT_META 전면 정정 — record 이름 + ext_after_sb 길이 cross-check 결과
  다수 mismatch 발견:
  - slot_12: scroll → **orb** (뇌제의오브/금강의오브, 2 byte ext)
  - slot_13: orb → **mix material** (살코기/재료2..9, 0 ext)
  - slot_15: material_2 → **mix_book recipe** (황혼수프/포션, 13 byte ext)
- ✅ `parse_battle_use_extra` field 라벨 정정 — val_134→effect_type, val_135→
  success_rate, val_136→effect_value, val_137→duration. 의미있는 이름으로.
- ✅ dispatch 정리 — slot_12 (orb) 가 이전에 잘못 battle_use parser 받았던 것
  수정. slot_15 (mix_book) 가 이전 slot_16 위치에서 정정.

**[Round 22 — 2026-05-10 완료]** Sorcerer (class_id=4) 미구현 stub 확정
- ✅ .so 바이너리 클래스 심볼 검색 — 4 player class object 만 존재:
  WARRIOR / ROGUE / GUNNER / KNIGHT. **SORCERER class 없음**.
- ✅ skill csv 검색 — `c_csv_skill_00..03` (4 player class, 각 43 skills) +
  `c_csv_skill_05` (16 monster/boss skills: 암흑탄/지옥소환/얼음폭풍/완전면역 등).
  **`c_csv_skill_04` 완전 부재**.
- ✅ class_stats.json 검토 — 소서러 entry STR/DEX/CON/INT 는 있지만 unk1..unk14
  모두 1 (다른 4 클래스는 6/12/18/24 등 다양). unk0=320 (다른 1000) — 명백한
  placeholder.
- ✅ IfLearnSkill 의 `(class/2)+16=18` 매핑은 dead code path — Sorcerer 가
  실제로 호출돼도 cat 18 (CashItem) 에 학습 가능한 records 없음.
- ✅ class_select.gd UI 정정 — "소서러" → "소서러 (미구현)" 라벨 표시.
  사용자가 선택 시 빈 스킬셋으로 시작하는 문제 인지 가능.
- 결론: **영웅서기5 출시 빌드는 4 클래스 only**. 소서러는 향후 확장 클래스로
  계획됐으나 미구현 채로 출시. cat 18 매핑은 placeholder, slot_18 은 실제로
  cash shop 용도로 재활용.

**[Round 21 — 2026-05-10 완료]**
- ✅ **HERO::IfLearnSkill (0x95d08, 316B) 디스어셈블** → SkillBook +0x134..+0x137
  4 byte fields 의 정확 의미 식별:
  - `+0x134` = **class_id** (0..4 — Warrior/Rogue/Gunslinger/Knight/Sorcerer)
  - `+0x135` = **skill_index** (HERO::skills[] 배열 인덱스, 클래스별 0..9 = 10 skills)
  - `+0x136` = **skill_level** (1..7, 이름 LV 와 정확 매칭)
  - `+0x137` = **required_level** (HERO+0x22d 와 cmp)
- ✅ IfLearnSkill 의 ItemTable category 공식 발견:
  ```
  category = (class_id / 2) + 16   ; signed div, round-toward-zero
  ```
  → Warrior(0)/Rogue(1) → cat 16 (slot_16),
    Gunslinger(2)/Knight(3) → cat 17 (slot_17),
    Sorcerer(4) → cat 18 (slot_18 = CashItem ?? — 별도 path 추정)
- ✅ **slot_16 의 정체 정정** — 기존 SLOT_META 가 'mix_book' 이라 라벨링했으나
  실제 records 모두 Warrior+Rogue 스킬북 (양손베기LV1..3, 돌진LV1..4, 내려찍기LV1..7,
  어깨치기LV1..4, 회전베기 등). SLOT_META[16] 을 `skill_book` 으로 변경.
- ✅ `parse_skill_book_extra` 의 라벨 정정 — val_134/val_135/val_137 을 의미있는
  이름 (`class_id`/`skill_index`/`required_level`) 으로 변경. 기존 `skill_level` 유지.
- ✅ items.json 검증 통계:
  - slot_16: 95 records, class_id=0 (Warrior, 48) + class_id=1 (Rogue, 47)
  - slot_17: 98 records, class_id=2 (Gunslinger, 49) + class_id=3 (Knight, 49)
  - 각 클래스 정확히 10 skills (skill_index 0..9), 각 skill 1..7 levels
- ⏸ Sorcerer (class_id=4) → cat 18 매핑이 CashItem 와 충돌. slot_18 에 class_id=4
  records 없음 — Sorcerer 는 별도 메커니즘 (출시 후 추가 클래스 또는 다른 학습 path)
  으로 추정. 다음 라운드 분석 가능.

**[Round 20 — 2026-05-10 완료]**
- ✅ LoadItemTable 함수 끝 영역 (0xa479c..0xa49c0, 548B) 추가 disasm —
  capstone `skipdata=True` 옵션으로 invalid instruction (literal pool / jumptable
  data) 통과. 새 도구 `tools/h5_dump_loaditem_tail.py` 추가.
- ✅ **slot_17 (SkillBookItem) layout 식별** — jumptable case 16/17 모두
  0xa47c0 으로 분기 (동일 코드 path). record_size=0x138 (312B), 4 byte ext:
  - `+0x134` = u8 skill_class (2 = Gunslinger 계열, 3 = Knight 계열)
  - `+0x135` = u8 skill_id (within class, 0..9)
  - `+0x136` = u8 **skill_level** — '연속사격LV1..LV4' → val=1, 2, 3, 4 정확 매칭 ✓
  - `+0x137` = u8 required_level (LV1..4 = 1, 4, 10, 22 monotonic)
- ✅ **slot_18 (CashItem) layout 발견** — jumptable case 18 → **0xa3b38** 별도
  코드 path (Round 19 가 0xa47c0 으로 추정한 것이 정정됨). hardcoded type 0x12=18
  at +0x14, 2 byte ext:
  - `+0x134` = u8 cash_category (val ∈ {0, 1, 2, 3})
  - `+0x135` = u8 stack/type (val ∈ {0..5, 255} — 255 = passive 추정)
- ✅ `decode_h5_item.py` 에 새 parsers 추가:
  - `parse_skill_book_extra` (slot_17, 4 byte): val_134 / val_135 / **skill_level** / val_137
  - `parse_cash_extra` (slot_18, 2 byte): val_134 / val_135
- ✅ SLOT_META 정정 — slot_18 = `cash` category (이전: skill_book 잘못).
- ✅ items.json 검증:
  - slot_17: 98 records 모두 4 byte fields populated. v134=2 (49 records,
    Gunslinger 계열) + v134=3 (49 records, Knight 계열). 클래스 별 10 skill ID.
  - slot_18: 49 records 모두 2 byte fields populated. v135=255 (31 records,
    passive 추정) + v135∈{0..5} (18 records, active/limited 추정).
- ✅ ITEM_STRUCT.md "Round 20" 섹션 + `parse_skill_book_extra` /
  `parse_cash_extra` parser docstring 업데이트.

**[Round 19 — 2026-05-10 완료]**
- ✅ LoadItemTable 의 cat 12+ jumptable case 별 sb 영역 (struct +0x134..+0x140)
  추가 fields layout 추출:
  - cat 12 (BattleUseItem, 0xa4060): +0x134/0x135/0x136/0x137 (4 byte u8) — slot_11
    포션 csv 와 정확 일치 (val_134=91, 135=100, 136=4, 137=50) ✓
  - cat 13 (OrbItem, 0xa423c): +0x134/0x135 (2 byte, csv 에 보통 없음 — record_size 가 base 만 cover)
  - cat 14, 15 (MixItem, 0xa43f4): 추가 fields 없음
  - cat 16 (MixBookItem, 0xa4578): sub-loop +0x135..+0x140 (12+ byte, csv 에 4 만)
  - cat 17, 18 (SkillBook/Cash, 0xa47c0): 함수 끝 영역 — dump_caller size 부족
- ✅ `decode_h5_item.py` 에 카테고리별 parser 추가:
  - `parse_battle_use_extra`: val_134/135/136/137
  - `parse_orb_extra`: val_134/135
  - `parse_mix_book_extra`: sb_extra_hex (raw 12+ byte)
- ✅ parse_items() 에 SLOT_META[cat]['category'] 별 dispatch 적용:
  - 'equip' (cat 1-11) → parse_equip_extra
  - 'battle_use' (cat 11/12) → parse_battle_use_extra
  - 'orb' (cat 13) → parse_orb_extra
  - 'mix_book' (cat 16) → parse_mix_book_extra

**[Round 18 — 2026-05-10 완료]**
- ✅ `ItemTable::SetItemOption` (240B, @0xa0ff8) 디스어셈블 → `+0x15f` 가
  **random option_type byte** 임을 확인. 함수가 random `option_table[i]` 픽:
  - `+0x15f` (offset+0x15f) = option_type (option_table[i].byte 0)
  - `+0x162` = option_value (level_limit * option_param * randint(0x50,0x78) / 32)
  csv 의 val_15f 는 init default — runtime 변경 가능. items.json 의 class_label
  통계 (Round 16 의 5-class mask 해석) 는 csv 시점에 유효.
- ✅ `LoadItemTable` 의 cat 12+ jumptable cases (0xa4060/0xa423c/0xa43f4/0xa4578/
  0xa47c0) 분석 → 모든 카테고리가 **공통 base layout** 공유:
  - record_size=0x138 (BattleUseItem/Orb), 0x134 (Mix), 0x144 (MixBook), 0x138 (SkillBook/Cash)
  - 공통: csv +2 (read+discarded), +4 (u16 → struct +0x16), +6 (strlen),
    name → struct +0x18, u32 → struct +0x30, sub_record_len + memcpy → struct +0x34..+0x134
  - EquipItem (cat 1-11) 만 sb-area (struct +0x150..+0x167) 추가
  - 다른 카테고리는 struct +0x134.. 에 카테고리별 추가 fields (4..N byte)
- ✅ `decode_h5_item.py` 에 `parse_common_extra` 함수 추가 — 모든 카테고리에
  `item_id` (u32) + `sub_record_len` + `sub_record_hex` 부여. 검증: 19 슬롯
  모두 첫 record 에 새 필드 적용 (롱소드/포션/살코기/양손베기LV1/창고확장 등).

**[Round 17 — 2026-05-10 완료]**
- ✅ `RefineItem::ApplyItemRefine` (956B, @0xa292c) 디스어셈블 → 강화 시
  변경되는 EquipItemInfo struct field 식별:
  - `+0x165` = refine_count (강화 횟수, u8)
  - `+0x166` = refine_sub_count (보조 강화, u8)
  - `+0x167` = refine_locked (1=영구 잠금, u8)
  ApplyItemRefine 의 r7 jumptable 결과:
  - r7=0/1: 강화 +1 success — +0x165 += 1, +0x166 += 1 또는 +2
  - r7=3: refine lock 적용 — +0x167 = 1
  - r7=4: 강화 실패 — `EquipItem::ClearEquipItem` (아이템 destroy)
- ✅ `EquipItemInfo::CopyData` (0xa8884) 가 +0x165, +0x166, +0x168 모두 복사 →
  runtime 강화 결과가 saved 형태로 보존.
- ✅ val_15f upper 3 bit (`>>5`) 분포 통계 추출 (`tools/h5_check_items.py`):
  - upper=0 (no upper bit) — 170 items (중급/희귀 무기)
  - upper=1 (32, bit5) — 248 items (강화/보스 무기 — 스톰브링거/캘라보그)
  - upper=3 (96, bits5+6) — 9 items (slot_5 헤어핀/서클릿 보석 액세서리)
  - upper=7 (224, all) — 362 items (common 기본 아이템 — 롱소드/서클릿)
- ⏸ upper 3 bit 의 정확 의미 식별 미완 — bit6=gem accessory, bit7=common flag
  가설. ItemTable::SetItemOption / DropTable 분석으로 확정 가능 (다음 라운드).

**[Round 16 — 2026-05-10 완료]**
- ✅ items.json 의 `class_restriction` (struct +0x155) 매핑이 **잘못됨**을 발견.
  IsEquipPossible / IsEquipPossibleSpirit cross-check 로 +0x155 가 단순 byte 비교
  (== N) 형태 — 즉 **subtype code** (5=weapon, 7=spirit, 0..4=weapon/armor sub-cat).
  slot_10 spirit 의 cls=5 가 17 records 인데 IsEquipPossibleSpirit 는 cls==7 만
  허용 → cls 가 weapon/armor sub-type 분류 임이 확인.
- ✅ **진짜 class restriction = `val_15f & 0x1f`** (struct +0x15f 의 lower 5 bit).
  비트 마스크: bit0=W (워리어), bit1=R (로그), bit2=G (건슬링어), bit3=K (나이트),
  bit4=S (소서러).
- ✅ items.json 통계 검증:
  - val=31 (WRGKS, 모든 클래스) 385 records (가장 많음 — 일반 무기/방어구)
  - val=9 (WK), val=17 (WS), val=14 (RGK), val=18 (RS), val=15 (WRGK) 다양
  - spirit 검증: 데몬의뿔 W / 고렘의인장 RS / 팬텀의부적 WS / 기사의징표 RGK
- ✅ `decode_h5_item.py` 의 fields 업데이트:
  - `class_restriction` → `subtype` 으로 rename (정확)
  - `class_mask` (val_15f & 0x1f) + `class_label` (W/R/G/K/S 조합 string) 추가
- ⏸ val_15f upper 3 bit (값 32, 64, 128) 의 추가 의미는 다음 라운드.

**[Round 15 — 2026-05-10 완료]**
- ✅ `tools/converter/decode_h5_item.py` 에 `parse_equip_extra` 함수 추가 —
  Round 14 의 csv layout 활용해 EquipItem (cat 1-11) extra body 가변 parse.
- ✅ items.json 에 새 named fields 부여 (cat 1-11 only):
  - `item_id` (u32 from extra+0)
  - `sub_record_hex` (variable len byte sequence)
  - `class_restriction` (u8 — 비트 마스크 추정)
  - `level_limit` (u8)
  - `val_150..val_160` (u8/u16 raw stat slots)
  - `triplet_162` (3-byte triplet)
- ✅ 비-EquipItem (cat 12+) 슬롯은 named fields 없음 (별도 layout 필요).
- ✅ 검증 완료: 롱소드 cls=0/lv=1, 나이트롱소드 lv=5, 버클러(방패) cls=3
  (워리어/나이트), 서클릿(헬멧) cls=5/lv=1 — 모두 합리적 매핑.
  cls 비트 마스크 가설: 1=warrior, 2=rogue, 4=gunslinger, 8=knight, 16=sorcerer
  (다음 라운드 IsEquipPossible cross-check).

**[Round 14 — 2026-05-10 완료]**
- ✅ `tools/h5_extract_loaditem_layout.py` — ItemTable::LoadItemTable (4320B,
  @0xa38e0) 디스어셈블 + csv read → struct store 시퀀스 자동 추출 도구.
  EquipItem 영역 (cat 1-11, 0xa3cf0~0xa4060) 분석.
- ✅ csv record body → in-memory EquipItemInfo struct field 매핑 추출:
  - csv +0..1 = record count (loop init)
  - csv +2..3 = u16 read but discarded (struct +0x14 = function arg category)
  - csv +4..5 → struct +0x16 (refine_value u16)
  - csv +6 (u8 name_len `nl`) → 7..6+nl name string memcpy → struct +0x18
  - csv +7+nl..+10+nl (u32) → struct +0x30
  - csv +11+nl (u8 sub_record_len `sblen`) → 256B sub-record memcpy → struct +0x34
  - 그 후 sb 시작 위치에서 u16/u8 mixed sequence → struct +0x150..+0x162
- ✅ LoadItemTable 안에서 `Formula::calc(formula_id=0x7f3=2035)` 호출 — load
  시점 base stat 즉시 계산 패턴 확인.
- ⏸ csv extra (가변 길이) 는 단순 u16 array 와 다름 — items.json 의 stats_u16
  가 부정확. decode_h5_item.py 정확화는 다음 라운드.

**[Round 13 — 2026-05-10 완료]**
- ✅ EquipItemInfo struct 핵심 field 5개 식별 — `tools/h5_dump_caller.py` 로
  CopyData / IsEquipPossible / GetLevelLimit 디스어셈블:
  - +0x14 = item_category/slot_type (s8) — IsEquipPossible jumptable 의 조건
  - +0x155 = class_restriction (s8) — HERO+0x22c (class_id) 와 비교
  - +0x15d = level_limit (s8) — GetLevelLimit 가 fetch
  - +0x168..+0x16d = 6 socket slot (orb/refine ID, 0xff = 빈슬롯)
- ✅ V[168..182] = ItemBase struct (Formula::calc 5번째 인수) field 영역.
  formulas_disasm.txt 와 cross-check 로 사용 패턴 식별:
  - V[168] (item +0xe) = base SP cost (`V[168]*(100-V[123])/100`)
  - V[170] (item +0x16) = base cooldown (`V[170]*(100-V[125])/100`)
  - V[174] (item +0x44) = damage growth multiplier (`V[56]+V[57]*V[174]`)
  - V[181] (item +0x4e) = speed/weight divisor
- ✅ csv extra (33..80B) ≠ in-memory EquipItemInfo struct (376B) 확인.
  csv stat → struct offset 매핑은 `ItemTable::LoadItemTable` (4320B) 디스어셈블
  필요 — 다음 라운드. decode_h5_item.py 에 layout 차이 코멘트 추가.
- ✅ ITEM_STRUCT.md 의 EquipItemInfo 섹션 + ItemBase 섹션 완전 재작성.

**[Round 12 — 2026-05-10 완료]**
- ✅ V[122..126] 5 buff slot 정확 라벨 확정 — formulas_disasm.txt 의
  `(100±V[xxx])/100` 패턴 + buildup csv 라벨 cross-check:
  - V[122] = EXP %bonus (csv 0x1d "경험치LV")
  - V[123] = SP소모량 감소% (csv 0x1e, 공식 `V[168]*(100-V[123])/100`)
  - V[124] = CP충전LV (csv 0x1f, 공식 `(V[124]/100)*150+300`)
  - V[125] = 쿨타임 감소% (csv 0x21)
  - V[126] = 포션효과 %bonus (csv 0x23)
- ✅ V[151], V[152] 둘 다 magic stat (INT 보정) 확정 — 이전 V[152]=DEX 추정 정정.
  formulas_disasm.txt 에서 V[151]/12, V[152]/12, V[152]/V[13], V[151]*V[56]/100
  같은 magic atk 보정 패턴 일관 확인. 둘은 element 1/2 짝 (id=4 vs id=5 magic
  atk1/2). 정확 element (fire/ice 등) 매핑은 다음 라운드.
- ✅ battle_system.gd / formula_vm.gd 의 V[122..126] / V[151,152] 라벨 정정.

**[Round 11 — 2026-05-09 완료]**
- ✅ `tools/h5_decode_buildup.py` — c_csv_buildup.json (111 buildup entries) 의
  extra_hex 형식 (`[ffff][type:u8][sub:u8][val:u16]` × N) decode + ApplyBuildupEffect
  entry type 자동 매핑.
- ✅ **V[112..116] 5 secondary stat 라벨 확정**:
  - V[112] = 근접명중 (csv 0x14 → ABE 11 → V[129] bonus, id=25 *10 multiplier)
  - V[113] = 장거리명중 (csv 0x15 → ABE 12 → V[130], id=26 *10)
  - V[114] = 회피 (csv 0x16 → ABE 13 → V[131], id=27 flat)
  - V[115] = 방패방어 (csv 0x18 → ABE 14 → V[132], id=28 flat)
  - V[116] = 크리티컬 (csv 0x19 → ABE 15 → V[133], id=29 flat)
  - 5 클래스 base 패턴이 합리적 (워리어 근접명중 24, 건슬링어 장거리명중 24,
    워리어 방패방어 5, 모두 크리티컬 0).
- ✅ **V[62]/V[63] = base_con/base_int 정정** — 이전 라운드 매핑 오류 발견.
  buildup csv "건강+#1" (csv 0x03 → ABE 4 → V[120]) = bonus_con 검증.
  "정신+#1" (csv 0x04 → ABE 5 → V[121]) = bonus_int.
  → V[62] = base_con / V[63] = base_int (이전 int/con 으로 잘못 매핑됨).
- ✅ class_stats.json byte sequence 가 STR/DEX/**CON/INT** 순서임 확인 →
  `tools/converter/decode_h5_class.py` 정정 + class_stats.json 재생성 +
  class_select.gd 표시 순서 정정 + battle_system.gd / formula_vm.gd 일괄 정정.
- ✅ 정정된 5 클래스 stat: 워리어 STR12/DEX8/CON10/INT6 (탱커),
  로그 6/10/8/12, 건슬링어 8/12/6/10, 나이트 10/6/12/8 (방패 탱커),
  소서러 6/8/8/14 (마법사 — INT 압도) — 모두 클래스 컨셉과 일치.

**[Round 10 — 2026-05-09 완료]**
- ✅ `tools/h5_find_kr_stat_strings.py` — .so .rodata 에서 한글 stat label 0건 확인.
  → 한글 라벨이 .so 가 아닌 VFS text/*.json 에 분산 (Hero5 의 string indexing
  방식). 정적 .so 분석으로 stat label↔calc_pl id 직접 매핑은 불가능 입증.
- ✅ `tools/h5_find_kr_text_idx.py` — VFS text JSON 에서 stat label sequence 추출.
  핵심: `00017_488ab1c6.json` first region (offset 142..420) 에 status menu 의
  20-stat 표시 라벨 순서 발견 (방어력/공격력/물리방어력/마법방어력/명중률/회피율/
  정확도/근접방어/장거리방어/마법공격/특수방어/특수공격/근접공격/장거리공격/
  물리회피/문법저항/마법적중/마법방어/크리티컬/크리티컬저항).
- ✅ `tools/h5_calc_status_table.py` — `HERO::CalcStatusComputation` 의 24 calc
  호출 자동 추출. **모두 calc_sk[2003]=V[41] + calc_sk[2004]=V[156]** 두 공식만
  사용 (7 EquipItem slot × 2 stat + 4 spirit slot × 2 stat). 결과는 0x2bc..0x2d6
  (V[136..149] element bonus 영역) cache. → V[112..116] 와 직접 무관 확인.
- ✅ `tools/h5_disasm_property_menu.py` — `StateInGameMenu::DrawPropertyMenu` 가
  Formula::calc 직접 호출 0건이며, stat read 가 모두 register-indirect
  (`ldr ?, [reg, reg]`) 형태임 확인. cache offset 이 GOT/literal pool 동적 lookup
  → 정적 매핑 어려움. V[112..116] 5 stat 라벨 정확 식별을 위해 다른 경로
  (save 데이터 / buildup csv / 동적 디버깅) 가 필요.

**[Round 9 — 2026-05-09 완료]**
- ✅ `tools/h5_apply_buildup_disasm.py` — HERO/BATTLER ApplyBuildupEffect
  jumptable 자동 추출 (56 entry × 2). 산출 `applybuildup_table.tsv`.
- ✅ V[122..126] (0x2a0..0x2a8) = 5 buff stat slot 확정. Entry type 30/31/32/34/36.
- ✅ V[125]/V[126] (0x2a6/0x2a8) buff slot 라벨 확정 (이전 미확정).
- ✅ `tools/h5_extract_class_stats.py` — c_csv_class.json 의 5 클래스 secondary
  stat base 추출 (워리어 24/18/24/5/0, 로그 12/12/18/3/0, 건슬링어 6/24/6/2/0,
  나이트 18/6/12/4/0, 소서러 1/1/1/1/1).
- ✅ `tools/h5_find_battle_check_funcs.py` — 전투 핵심 함수의 immediate calc 호출
  추적. ProcDemageCalc → calc_pl id=1,2,3, CalcStatusComputation → calc_sk
  id=2035,2036 (EquipItem stat bonus 합산).
- ✅ HERO::InitStatusComputation (0x95e44) 가 V[118..133] (0x298..0x2b6) 영역
  전부 0 reset 확인 — buff/temp bonus 영역.
- ✅ battle_system.gd::_player_ctx, formula_vm.gd::_player_default 에 V[111..116]
  클래스별 정확 lookup (class_stats.json) + V[122..133] buff/bonus slot 매핑 적용.
- ⏸ V[112..116] 5 stat 의 한국어 라벨 (적중/회피/크리티컬/블록/속도 중 어느 것)
  식별은 status menu UI 함수 한글 string 매핑 RE 가 필요 — 다음 라운드.

**[Polish 라운드 — 2026-05-09 완료]**
- ✅ 통합 파이프라인 `tools/h5_extract_pipeline.py` (9 단계, incremental, ~6s).
- ✅ Scene body opcode 정적 trace `tools/h5_scn_body_stats.py` (258/258, 99%+ dispatch).
- ✅ BATTLER damage disasm `tools/h5_extract_battle_funcs.py` + `docs/h5/BATTLE_FORMULA.md`.
  Event_PlayerDamage 공식 100% 추출, BATTLER offset (0xf0/0x180/0x210) 확정.
- ✅ SMAF↔OGG audit `tools/h5_smaf_audit.py` — 42:42 1:1 → 변환 작업 영구 클로즈.
- ✅ P5 부분 — table.dat = **Unicode BMP** (EUC-KR 아님) 정정. `docs/h5/P5_FONT_MAPPING.md`.

**[P5 잔여] kor.fnt 581 ↔ Unicode 매핑** — 자율 가능, 게임 영향 X
- 다음 단계: `_midas_funcFntInvalidate` (size 미상) 디스어셈블 → codepoint→glyph_index 함수.
- 현재 시스템 폰트(Noto Sans CJK KR)로 충분 — polish 만.

**[P6] Android APK 실 빌드 검증** — 사용자 직접 진행 필요
- Godot Editor 4.2+ + Install Android Build Template + Export Templates (~1GB)
  + JDK 17 + Android SDK + NDK.
- `apps/hero5-godot/export_presets.cfg.template` 참조.
- 이 머신에서 자동화 불가 — 사용자 GUI 진행 필요.

**[후속 자율 가능]**
- `HERO::NewHitEffect` (1712B, 39 callee) → 정공식 (atk × pct − def × ?) + 스킬 multiplier 추출.
- `HeroSkillAtkHardCode` (888B, 37 callee) → 스킬별 분기 (대시/베기/원거리).
- 100B 급 작은 Event_* 함수들 (Event_PlayerDamage 패턴) 같은 방식으로 100% 추출.

### 6.3 환경 / 도구 빠른 참조

#### 새 클론 / assets 비어있을 때 — 처음부터 복원
필수: `Hero5/영웅서기5(최신폰전용).apk` 가 있어야 함.

```powershell
# 1) APK unzip → work/h5/extracted/
$apk = "Hero5\영웅서기5(최신폰전용).apk"; $out = "work\h5\extracted"
New-Item -ItemType Directory -Force -Path $out | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($apk, $out)
```

```bash
# 2) Phase 2 — 자산 추출/디코딩 (Python 3.10+ 필요)
python tools/h5_vfs_unpack.py            # VFS 2189 entries
python tools/h5_recover_names.py         # 99.7% 이름 복원
python tools/h5_batch_sprite.py          # sprite 421 + palette 588
python tools/h5_extract_text.py          # 한글 18,837 unique

# 3) 디코더 일괄 (게임 데이터)
for f in tools/converter/{convert,decode}_h5_*.py; do
  python $f 2>/dev/null
done

# 4) Phase 3 — Godot 임포트 + 검증
python tools/import_to_godot.py          # opcode_table.json 자동 포함 (capstone+lief 있을 때)
python tools/verify_godot_project.py     # → 0 errors / 0 warnings 기대
```

#### .so 분석 도구 (capstone+lief 필요)
```bash
pip install lief capstone

python tools/h5_extract_opcode_disasm.py    # 77/77 opcode → opcode_table.json
python tools/h5_event_arg_sizes.py           # 105 Event_* arg sizes
python tools/h5_extract_enemy_layout.py      # enemy_g 121B layout 검증
```

#### Ghidra (옵션 — capstone 으로 대체 가능)
```bash
# 헤드리스 모드 (script 자동 실행)
"D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
  "D:/testrepo/work/h5/ghidra_project" Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath "D:/testrepo/tools/ghidra" \
  -postScript DecompileHero5Keys.java

# tools/ghidra/*.java — 15개 분석 스크립트 (DES/Scene/Interpreter 등)
# capstone+lief 환경이 있으면 대부분 Python 도구로 대체 가능.
```

#### Ghidra (추가 디컴파일 필요시)
```bash
# 헤드리스 모드 (script 자동 실행)
"D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
  "D:/testrepo/work/h5/ghidra_project" Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath "D:/testrepo/tools/ghidra" \
  -postScript DecompileHero5Keys.java

# tools/ghidra/ 스크립트들:
#   DecompileHero5Keys.java   — DES/VFS/JNI 핵심 함수
#   FindAssetNameTable.java   — loadAssetFromVFS caller
#   DecompileNameLookup.java  — JNI 브리지
#   FindSceneLoader.java      — scene 로더 후보
#   DumpScnRef.java           — .scn 참조 함수
#   DumpInterpreter.java      — Interpreter::doScript
#   DumpInterpreterCore.java  — Token/Scripts/Strings/Event_*
#   FindOpcodeDispatch.java   — onFunction 후보
#   DumpGbm.java              — GbmImage::LoadImage
#   DumpHeroChar.java         — HERO/CHAR 클래스
#   DumpMonsterLoad.java      — Monster/EnemyG_set
#   DumpMapInit.java          — Map::Initialize/LoadData
#   DumpDes.java              — MX_des*
#   DumpDesArg.java           — DES key arg trace
#   FindFieldWrites.java      — this+offset 쓰기 검색

# Ghidra GUI (수동 분석)
"D:/ghidra_12.0.4_PUBLIC/ghidraRun.bat"
# → Open project → D:/testrepo/work/h5/ghidra_project/Hero5
```

### 6.4 핵심 산출물 인덱스

#### Phase 2 (자산 추출 / 분석)
| 무엇 | 어디 |
|---|---|
| VFS catalog | `work/h5/vfs_catalog.tsv` |
| 자산 이름 (2,182 / 99.7%) | `work/h5/analysis/asset_names.tsv` |
| 디컴파일 코드 모음 | `work/h5/analysis/*.c` (19+ 함수, 핵심: scn_loader / opcode_dispatch / monster_load / des_key / gbm_loader / interpreter_core) |
| Opcode 매핑 (77종) | `work/h5/analysis/opcode_table.tsv` |
| 스프라이트 PNG (3,798) | `work/h5/converted/sprites/<file>/frame_NN_*.png` |
| 한글 코퍼스 (18,837 unique) | `work/h5/converted/text/_corpus.txt` |
| _pa 시각화 컨택트시트 | `work/h5/analysis/pa_swatches/_index.html` |
| Map collision/tile 매핑 | `work/h5/analysis/mapdata_index.tsv` |
| Scene 헤더 (258개) | `work/h5/analysis/scn_headers.tsv` |
| Ghidra 프로젝트 | `work/h5/ghidra_project/Hero5/` |

#### Phase 3 (Godot 리메이크)
| 무엇 | 어디 |
|---|---|
| Godot 프로젝트 | `apps/hero5-godot/` |
| 임포트된 자산 (gitignored) | `apps/hero5-godot/assets/` |
| 게임 데이터 JSON (15+ 테이블) | `apps/hero5-godot/assets/gamedata/` |
| Map 데이터 (collision + tile) | `apps/hero5-godot/assets/maps/<id>.{json,col.bin,tile.bin}` |
| Sprite name → dir 매핑 | `apps/hero5-godot/assets/sprite_index.json` |
| Scene 인덱스 | `apps/hero5-godot/assets/scenes/index.json` |
| 임포트 파이프라인 | `tools/import_to_godot.py` |
| 정합성 검증 | `tools/verify_godot_project.py` |
| Android export 가이드 | `apps/hero5-godot/export_presets.cfg.template` |

### 6.5 최근 커밋 히스토리 (작업 추적)

```
9b6174b  도주 % + 도움말 + 맵 이름 + 메뉴별 BGM
7c3d422  turn 표시 + 인벤 정렬 + 토스트 + Settings 영구
d619817  자동 인카운터 + auto-save + tile attr + 퀘 보상 정밀
2aa969e  HP회복 + 장비비교 + minimap + settings
a2ec161  HUD + 슬롯 삭제 + NPC 색상 + 인벤 필터
a058070  quest 처치 카운트 + warp trigger + NPC 한글 + 이펙트 애니
c600e11  sprite 매핑 + Title 로고 + stat 분배 + 적 그래픽 + 퀘스트 보상
9b5072c  클래스 선택 + NPC sprite + 포션/장비 사용 + 세이브 메타
4f3265d  레벨업 알림 + 장비 stat + Quest UI + BGM 페이드
4514bd6  상점 UI + 레벨업 + NPC 정밀 + 다중 세이브
7f9dec3  item stat + damage popup + dialog 분기 + scene 전환
e9eff82  equipment + inventory UI + combat 정밀 + NPC 스폰
2ba8534  drop/shop/smith/quest 데이터 + Quest 시스템 + Title 슬롯 + skill resolver
4c91c65  skill/item/quest tree 디코딩 + 사운드 hookup
6ff31e9  GameData API 확장 + 전투/인벤 실데이터 연동
cd57c8d  MVP 검증 + enemy 정확도 + NPC/quest 데이터
0f9f834  enemy stats + walk-cycle + Interpreter 확장 + Android export
7b6b455  DES key + 고정사이즈 csv + GameState 통합
e675855  stats 디코딩 + 전투 UI + collision 디버그
6af2634  한글 폰트 변환 + Dialog/Status UI
2dc2bfa  맵 데이터 + Interpreter 핸들러 + 세이브 골격
daf4be6  캐릭터 + Interpreter + 타이틀/데모 씬
860f997  opcode 매핑 + Map 렌더러 + 폰트/SMAF 분석
78dafe9  .scn 헤더 파서 + Scene_Init 디컴파일
1f7a4b8  자산 이름 99.7% + anim 파서 + Phase3 결정
fc19f8a  자산 이름 99.3% 복원 (Phase 2-B 완료)
dc59407  DEX 메소드 분석 + TINY_META 파서
89a4fdc  Ghidra hash 함수 복원 (DJB2-like)
79759b8  한글 추출 필터 개선
637b164  잔여 분류 + 한글 텍스트 추출
c011eae  sprite 디코더 type=0x04/0x08/0x18
fbfaebe  Phase 2-A.4 sprite 디코더 (84%)
8aec053  Phase 2-A.2~3 _pa 인코딩 + 미매칭 클러스터링
c57be91  Phase 2-A.1 bin 포맷 호환성 프로브
6a1c78a  영웅서기5 리메이크 시작점
```
