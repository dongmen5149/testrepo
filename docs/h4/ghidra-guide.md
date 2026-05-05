# Hero4 Ghidra 분석 가이드

> Hero3 의 [docs/h3/ghidra-gui-guide.md](../h3/ghidra-gui-guide.md) 와 동일한 워크플로우. 차이점은 바이너리 / GOT base / 알려진 string offset.

## 자동 분석으로 이미 얻은 정보

```bash
# 자산 path 전부 확보 (디스어셈블 없이)
HERO_GAME=h4 python tools/recon/extract_strings.py

# 0xf81f magenta literal 위치 10개
HERO_GAME=h4 python tools/recon/find_f81f.py
```

## Ghidra GUI 가 풀어야 하는 것 (자동 안 됨)

Hero4 의 **GOT base 주소** — Hero3 는 `0xb2c40`. Hero4 는 binary 다른 빌드라 다른 값. 사용자 GUI 작업으로 식별 필요.

이게 정해지면 모든 PIC indirect references 가 자동으로 해소되고 다음 분석이 unblocking 됨:
- `_BM` type 0x0c sparse pixel 디코더 함수 (Hero3+Hero4 공통, 둘 다 같이 풀림)
- `_EXD` 캐릭터 데이터 로더 함수 (구조체 layout 확정)
- `_PAL` 8byte/color 의 secondary RGB 의 의미 확정 ("Alpha Palette Index Not Found" 에러 단서)
- `_MAP_M_` extras 영역 (NPC/exit/event 배치) 파서

## 환경 셋업 (Hero3 와 동일)

| 항목 | 위치 |
|---|---|
| JDK 21 | 시스템 `JAVA_HOME` |
| Ghidra 12.x | `GHIDRA_INSTALL_DIR` |
| 분석 바이너리 | `c:/gameRemake/testrepo/work/h4/extracted/client.bin387872` (566 KB) |
| Ghidra 프로젝트 (생성 예정) | `c:/gameRemake/testrepo/work/h4/ghidra_proj/Hero4.gpr` |

## Step-by-step

### 1. New Project 생성
- Ghidra 실행 → File → New Project → Non-Shared Project → 위치 `work/h4/ghidra_proj/`, name `Hero4`

### 2. Binary import
- File → Import File → `work/h4/extracted/client.bin387872`
- Format: **Raw Binary**
- Language: **ARM:LE:32:Cortex** (CodeCompiler: gcc)
- Options → Block Name: `client`
- Base Address: `0x0` (일단 — GOT 추정 후 변경 가능)

### 3. Auto-Analyze
- 더블클릭으로 열기 → 자동 분석 옵션 모두 기본값으로 OK

### 4. GOT base 식별 (핵심 단계)

Hero3 의 `0xb2c40` 추정 방법을 그대로 적용:
1. Search → For Strings 로 `frameBuf is NULL` 또는 `Alpha Palette Index Not Found` 찾기
2. 그 string 의 offset (예: 0x82104 = 'frameBuf is NULL') 메모
3. Memory map / Defined Strings 로 string xref 시도
4. xref 가 없으면 → PIC indirection. 첫 함수 디스어셈블에서 `LDR rN, [pc, #imm]` + `ADD rN, sl` 패턴 찾기 (sl=r10=GOT base register)
5. `tools/ghidra/SetGotBase.java` 의 `GOT_BASE` 상수를 Hero4 추정값으로 수정 → Script Manager 에서 실행

### 5. 핵심 함수 식별 (string xref 기반)

extract_strings 에서 확인한 file path string 들이 모두 **자산 로더 함수의 인자**. 함수 식별 우선순위:

| String | 가리키는 함수 |
|---|---|
| `/H4/PAL/_H_%03d_PAL` | _PAL 로더 → 8byte/color secondary 의 의미 확정 |
| `/H4/CIF/_H_%03d_CIF`, `/H4/EXD/_H_%03d_EXD` | 캐릭터 데이터 로더 |
| `/MAP/M/_MAP_M_%03d` | 맵 로더 (extras 영역 파싱 함수 포함) |
| `'====> Alpha Palette Index Not Found'` | _PAL 의 alpha logic 분기 — **secondary RGB 가 진짜 alpha mask 인지 검증** |
| `'====> frameBuf is NULL'` | Hero3 와 동일 → BM 디코더 진입점 |

### 6. 0x0c sparse pixel 디코더 (Hero3 와 공유)

이게 풀리면 Hero3 미해독 91개 BM (theme 47 + obj 44) + Hero4 31개 TILE 모두 unblocking. **records ÷ cells ≈ 0.51** 통계 (RLE 압축 강력 추정) 단서로 디코딩 함수 식별:
- BM 로더에서 `type == 0x0c` 분기 찾기
- 그 분기의 inner loop 에서 byte/word 읽고 `*frameBuf++ = ...` 패턴 — 이게 RLE expansion 또는 sparse write loop

## Hero3+Hero4 공유 부분 처리

Ghidra 분석은 **Hero3 와 Hero4 따로 두 프로젝트** 로. 같은 한빛 엔진이 두 게임에 진화된 형태라 함수 시그니처는 비슷하지만 offset/주소는 다름. 한쪽에서 찾은 sparse pixel 디코더 알고리즘은 다른 쪽에 그대로 적용 가능 (디코더는 알고리즘 단위로만 공유 — Python `convert_bm_v2.py` 한 곳에 구현하면 양쪽 다 사용).
