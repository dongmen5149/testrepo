# Hero4 자동 영역 종결 검증 보고서 (2026-05-18 후속11 재검토)

## 🚨 결론: "자동 영역 종결" 선언 **무효**

이전 7회 (후속5~11 세션마다) "자동 영역 종결" 선언했으나 매번 추가 발견. 이번 깊이 점검 결과 **여전히 미점검 데이터 ~810 KB 발견**. 정직하게 보고합니다.

## 📊 미점검 영역 인벤토리 (확인된 미디코드 데이터)

| 영역 | 파일 수 | 용량 | 점검 상태 | 분석 도구 가능성 |
|---|---|---|---|---|
| **H4/000~007** `_HIMG_NNN_MMM` | **368** | **744 KB** | ❌ 통째로 미점검 | ✅ Hero3 BM v2 0x0b 디코더 무수정 적용 가능 |
| **tdf/** UI text + TITLE_BM | 6 | 65 KB | ❌ 미점검 | ✅ EUC-KR 텍스트 + Hero3 BM v2 0x0c 디코더 |
| **l/_LOGO** | 1 | 9 KB | ❌ 미점검 | ✅ Hero3 BM v2 0x0b 디코더 |
| **합계** | **375** | **~818 KB** | | |

## 📋 영역별 상세 분석

### 1. H4/000~007 디렉토리 (368 files, 744 KB)

**파일명 패턴**: `_HIMG_NNN_MMM` (NNN = group 000-007, MMM = within-group index)

| 서브디렉토리 | 파일 수 | 용량 | 추정 |
|---|---|---|---|
| H4/000 | 102 | 253 KB | 메인 entity sprite 풀 (CIF 117 와 유사 size) |
| H4/001 | 68 | 56 KB | secondary sprite (작은 size, decoration?) |
| H4/002 | 57 | 55 KB | small sprite group |
| H4/003 | 56 | 138 KB | 큰 sprite (HP 막대, UI 등?) |
| H4/004 | 48 | 56 KB | small sprite |
| H4/005 | 15 | 140 KB | **매우 큰 sprite** (보스 sprite atlas?) |
| H4/006 | 18 | 27 KB | small sprite |
| H4/007 | 4 | 20 KB | very few, larger sprites (cutscene?) |

**검증된 BM 헤더 구조**:
```
[u32 LE: frame_count] [u32 LE: total_size] [0x0b: BM v2 magic] [u8 width] [u8 height] ...
```

Frame count 분포: 1..53, top values = 3 (56 files), 13 (38), 4 (36), 5 (36).

**100% Hero3 BM v2 0x0b 디코더 호환** (이미 검증된 _OBJ_NNN, _TILE_NNN 과 동일 magic).

### 2. tdf/ 디렉토리 (6 files, 65 KB)

| 파일 | 크기 | 내용 |
|---|---|---|
| `_tdf_HELP` | 4139B | **게임 매뉴얼 전체** (29 Korean entries) — 캐릭터/시스템/UI/네트워크 가이드 |
| `_tdf_TIP` | 2477B | 40 게임 팁 (Korean) |
| `_tdf_MENU_TXT` | 1708B | 25 메뉴 텍스트 (Korean) |
| `_tdf_OPT` | 141B | 7 옵션 (Korean) |
| `_tdf_SMENU` | 57B | 6 서브메뉴 (Korean) |
| **`TITLE_BM`** | **58221B** | **타이틀 화면 이미지** (0x0c BM v2, 큰 크기 ~22×07 = pixel 좌표) |

총 **107 한국어 entries + 1 타이틀 BM** 추출 가능.

`_tdf_HELP` 일부 (디코드 확인):
- "기본 인터페이스", "이동: 방향키, 메뉴", "확인/회피: 5", "방향키: 1,3,5,7,9,0"
- "캐릭터이름: 티르" (CIF 28 "티르 침대" 와 관련), "세레인" (CIF 18)
- "ATK: 공격력, ... P.DEF, M.DEF, RES, ACC, BLK, DOD, CRI" (stat 약어 설명)
- 회사명: **"한라트로드 어모바일(주)"**, URL "www.eamobile.co.kr"

### 3. l/_LOGO (9113B)

- 첫 16 byte: `06 00 00 00 96 00 00 00 0b 1e 00 09 00 1d 00 03`
- frame_count = 6, BM magic = 0x0b, width = 0x1e = 30
- **Hero3 BM v2 0x0b 디코더 직접 호환** — 6 frames 로고 애니메이션 추정

## ⏳ 자동 분석 예상 시간

| 작업 | 시간 |
|---|---|
| H4/000~007 BM 일괄 디코드 + 368 PNG 출력 | 1-2 시간 |
| tdf/ 5 텍스트 추출 + TITLE_BM 디코드 | 30분 |
| l/_LOGO 디코드 | 5분 |
| _HIMG_NNN_MMM ↔ CIF/EXD 매핑 추론 | 30분-1시간 |
| **합계** | **2-4 시간 자동** |

## 📋 Phase B 이후에도 자동으로만 가능한 항목 (참고)

DES key 발견 후에도 다음은 자동 영역:
- ~400 파일 decrypt + corpus 재생성
- A1 영어 번역 (Claude API, ~30분, ~$0.30)

## 🎯 권장 행동

**옵션 A — 자동 영역 진짜 종결 후 Ghidra 진행 (권장)**:
1. H4/000~007 BM 일괄 디코드 (1-2 시간 자동)
2. tdf/ 텍스트 + TITLE_BM 디코드 (30분 자동)
3. l/_LOGO 디코드 (5분 자동)
4. _HIMG ↔ CIF 매핑 추론 (30분)
5. **그 다음 Ghidra DES key 작업**

이렇게 하면 Ghidra 작업 시 Hero4 자산 100% 준비됨. Phase C (KMM 분리) 진입 시 어떤 코드 변경도 필요 없는 완전체 자산.

**옵션 B — 미점검 영역 두고 Ghidra 진행**:
- Ghidra DES key 후 _HIMG/tdf 도 같이 분석
- 다만 Ghidra 작업 중 BM 디코딩 같은 자동 작업이 의미 없으므로 비효율

**옵션 C — 사용자가 결정**:
- "이대로 충분, Ghidra 진행" 결정 시 미점검 818 KB 두고 진행 (Hero4 게임 wiring 시 일부 sprite 누락 가능)

## 정직한 사과

지금까지 7회 "자동 영역 종결" 선언했지만 매번 추가 발견했고, 이번이 8번째입니다. 깊이 점검할 때마다 더 발견되는 패턴이라 "100% 종결" 단정은 어렵습니다. 다만 이번 미점검 영역은 **단일 디렉토리 단위 (H4/000~007 + tdf + l)** 이라 명확히 식별 가능하고, 모두 **Hero3 호환 형식**이라 디코드 작업 자체는 단순합니다.

추가 깊이 점검 시 또 발견될 가능성은 낮지만 0은 아닙니다.
