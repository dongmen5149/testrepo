# Ghidra GUI 분석 가이드

> 이 문서는 Ghidra 처음 사용하는 사람을 위한 자기충족 가이드.
> 다음 세션에서 "왜 해야 하지?", "뭘 해야 하지?" 질문이 다시 와도 이 문서만 읽으면 답이 됨.

---

## 1. 왜 해야 하나 — 배경

영웅서기3 Android 리메이크는 원본 JAR(`Hero3/0103EFD4.jar`)에서 자산을 꺼내 변환·재활용한다. 자산 변환은 대부분 끝났지만 **4가지 핵심 포맷의 정확한 디코딩이 미완료**다. 이걸 해결하려면 원본 게임의 ARM 바이너리(`client.bin64000`)에서 디코더 함수의 동작을 읽어내야 한다.

### 미완 4종 (PROGRESS §4)

| ID | 미완 항목 | 영향 |
|---|---|---|
| §4.1 | `_bm` type 0x0c sparse pixel 포맷 | 맵 타일 47개 + 오브젝트 44개가 noise/색상 그리드 placeholder. **맵이 원본처럼 안 보임** |
| §4.2 | `_mp` extras 영역 (NPC/exit/event 배치) | 134개 맵 모두 NPC·출구·이벤트 트리거 위치를 수동 정의해야 함. 현재 5맵만 사용 |
| §4.3 | `_cif` animation timing 데이터 | 캐릭터가 정적 frame 한 장만 나옴. 원본의 4방향 걷기/공격/사망 모션 없음 |
| §4.4 | `_scn` opcode 매핑 | 이벤트 스크립트가 대사만 표시. 사운드 트리거/플래그 set/분기/컷씬 명령 모두 미실행 |

### 왜 자동화가 안 되나 (이미 시도함)

자동 헤드리스 분석으로 1470 함수 모두 디컴파일은 됐는데 **디버그 문자열(예: `frameBuf is NULL`)에서 사용 함수를 추적할 수 없음**. 이유:

- 바이너리는 GCC `-fpic` 컴파일 (Position Independent Code) + GOT 기반 간접 참조
- GOT base = `0xb2c40` (식별 완료)
- 그러나 GOT 안에 디버그 문자열의 직접 포인터가 없음 → string-table indirection 또는 load-time relocation 으로 추정
- Ghidra의 자동 reference analyzer 가 이 indirection chain 을 못 따라감

→ **사람이 GUI에서 코드 동작 패턴을 보고 판단하는 게 가장 빠름.** Ghidra의 강점이 인터랙티브 분석이고, 헤드리스 자동화로 이 종류의 추적은 본질적으로 불리.

### 한 진입점만 풀려도 큰 가치

§4.1 (비트맵 디코더) 하나만 풀어도:
- theme 47 + obj 44 = 91개 BM 파일이 진짜 픽셀로 렌더링
- `tools/converter/convert_bm_v2.py` 디코더 한 줄 패치로 즉시 반영
- MapScene/MapWalkScene 이 placeholder 색상 그리드에서 **진짜 게임 월드 화면**으로 바뀜

---

## 2. 환경 — 이미 준비됨

이미 셋업 완료 (다음 세션에서 다시 깔 필요 없음):

| 항목 | 상태 |
|---|---|
| JDK 21 | `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\` (시스템 `JAVA_HOME`) |
| Ghidra 12.0.4 | `D:\ghidra_12.0.4_PUBLIC\` (시스템 `GHIDRA_INSTALL_DIR`) |
| 분석할 바이너리 | `d:\testrepo\work\extracted\client.bin64000` (735KB) |
| Ghidra 프로젝트 | `d:\testrepo\work\ghidra_proj\Hero3.gpr` (자동 분석 완료, 1470 함수 식별) |
| 헤드리스 스크립트 | `d:\testrepo\tools\ghidra\` (Java 스크립트 4종) |
| 전체 디컴파일 결과 | `d:\testrepo\work\ghidra_out\all_decompiled.c` (2.5MB, 참고용) |

### Ghidra 실행 방법

```
D:\ghidra_12.0.4_PUBLIC\ghidraRun.bat
```

더블클릭 → Ghidra 메인 창 (Project Manager) 5~30초 로딩.

---

## 3. 목표 — 4가지 진입점 단서

| 우선순위 | 진입점 단서 (디버그 문자열 / 함수 이름) | 위치 (file offset) | 풀면 해결되는 것 |
|---|---|---|---|
| **§4.1 (가장 추천)** | `frameBuf is NULL` | `0xa61c8` | type 0x0c sparse pixel 포맷 (가장 시각 영향 큼) |
| §4.2 | `Event_freeID`, `loadDataID` | `0xa6e54`, `0xa6efc` | _mp extras 자동 NPC/exit 배치 |
| §4.3 | `Hero_Free`, `freeBossType` | `0xa6e8c`, `0xa6e70` | _cif 4방향 애니메이션 timing |
| §4.4 | `onEventMessageOkKey`, `eventManager` | `0xa6888`, `0xa6ad8` | _scn 이벤트 스크립트 opcode dispatch |

→ **§4.1 부터 시도.** 가장 시각 영향 크고, 비트맵 디코더는 패턴이 명확함 (RGB565 + row/col 루프).

---

## 4. 단계별 작업 — §4.1 비트맵 디코더 찾기

### Step 1: 프로젝트 열기

1. `ghidraRun.bat` 실행 → Ghidra 메인 창
2. 좌측 트리에 `Hero3` 프로젝트가 보이면 펼치기 (없으면 `File → Open Project → d:\testrepo\work\ghidra_proj\Hero3.gpr`)
3. `client.bin64000` 더블클릭 → **CodeBrowser** 창이 열림 (메인 분석 창)
4. "Analyze?" 다이얼로그가 뜨면 **No** (이미 분석 완료됨)

### Step 2: 화면 구성 이해 (3분)

CodeBrowser 창 = 5개 영역:

```
┌──────────────────────────────────────────────────────┐
│  메뉴 / 툴바                                         │
├─────────────┬───────────────────┬───────────────────┤
│             │                   │                   │
│ Symbol Tree │  Listing          │  Decompiler       │
│ (좌측)      │  (중앙, 어셈블리) │  (우측, C 코드)   │
│             │                   │                   │
│ ─ Functions │  0x12abc LDR r0   │  void FUN_12abc() │
│ ─ Strings   │  0x12abe BL ...   │  {                │
│ ─ ...       │                   │    ...            │
├─────────────┴───────────────────┴───────────────────┤
│  Console / Bookmarks (하단)                         │
└──────────────────────────────────────────────────────┘
```

- **Listing 창**(중앙)과 **Decompiler 창**(우측)은 동기화됨. 한 쪽 클릭하면 다른 쪽도 자동 점프
- **Symbol Tree**(좌측)에서 함수/문자열 검색
- 키 단축키:
  - `Ctrl+Shift+E` — Search Program Text
  - `G` — Go to address (예: `0xa61c8` 입력)
  - `Ctrl+L` — Rename label/function (찾은 함수 이름 바꾸기)
  - 함수 우클릭 → 다양한 옵션

### Step 3: 디버그 문자열로 점프

방법 A (주소로 직접):
1. `G` 키 누르기 → 입력창에 `0xa61c8` 입력 → Enter
2. Listing 창이 그 주소로 점프. `ds "====> frameBuf is NULL"` 같은 줄이 보임

방법 B (텍스트 검색):
1. `Window → Defined Strings` 메뉴 클릭
2. 새로 열린 창에서 `Filter` 박스에 `frameBuf` 입력
3. 결과에서 더블클릭

### Step 4: 참조하는 코드 찾기

문자열 라벨(`s_====>_frameBuf_is_NULL_xxxxx` 같은 이름)을 **우클릭 → References → Show References to Address**.

→ 새 창에 참조 목록.

**시나리오 A — 참조가 보임**:
```
Reference Address     | Type  | From
00012abc              | DATA  | FUN_00012a00
```
더블클릭 → 그 함수로 점프. **Step 5로**.

**시나리오 B — 참조가 0건**:
PIC indirection 때문에 자동 추적 실패. **Step 6 (수동 추적)으로**.

### Step 5: 후보 함수 검증 (시나리오 A)

Decompiler 창(우측)을 본다. 비트맵 디코더라면 다음 패턴이 보여야 함:

```c
void FUN_xxxxx(int *frameBuf, byte *src, int width, int height) {
    if (frameBuf == NULL) {
        // 여기서 "frameBuf is NULL" 출력
    }
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            // 픽셀 unpack 로직 — 16비트 단위 읽기, mask·shift
            ushort pixel = *(ushort*)(src + ...);
            if (pixel == 0xf81f) continue;  // 투명 마젠타 스킵
            *frameBuf++ = ...;
        }
    }
}
```

핵심 표지:
- 16비트 read (`*(ushort*)` / `& 0xffff`)
- `0xf81f` 또는 `0x1ff8` 상수 비교 (RGB565 투명 마젠타)
- `<< 16`, `>> 11`, `& 0x1f`, `& 0x3f` 같은 RGB565 분리 마스크
- nested loop (row × col)
- 출력 버퍼 (`*frameBuf++ = ...`)

확신 들면 **Step 7로**.

### Step 6: 수동 추적 (시나리오 B — 참조 못 찾음)

이게 진짜 사람의 일. 두 가지 접근:

**접근 1: 함수 이름 필터**

1. Symbol Tree (좌측) → `Functions` 펼치기
2. Filter 박스에 `bm`, `frame`, `pixel`, `decode`, `draw`, `blit` 등 입력
3. 후보 함수 클릭 → Decompiler 창에서 Step 5의 패턴 확인

**접근 2: 0xf81f 상수 검색**

1. `Search → Memory...` (또는 `Search → For Direct References`)
2. "Hex Sequence": `1f f8` (LE) 또는 `f8 1f` 입력
3. 코드 영역에서 매치되는 곳 찾으면 그 주변 함수가 디코더 후보

**접근 3: 비슷한 동작 패턴 함수 훑기**

`d:\testrepo\work\ghidra_out\all_decompiled.c` (1470 함수 모두 디컴파일됨, 2.5MB) 를 텍스트 에디터로 열어서:
- `for` 루프 nested
- 16비트 마스크 (`& 0xffff`, `>> 8`)
- 매개변수 4개 정도 (frameBuf, src, width, height 추정)

검색 키워드 예시: `pixel`, `bitmap`, `frameBuf`, `0xffff`, `0x1f`, `0x3f`.

### Step 7: 결과 기록

확신되는 함수를 찾으면 다음을 기록:

1. **함수 시작 주소** (예: `0x00012abc`)
2. **함수 이름** (Ghidra 자동 명칭, 예: `FUN_00012abc`)
3. **Decompiler C 코드 전체 복사** — 우측 Decompiler 창에서 `Ctrl+A → Ctrl+C` → 텍스트 파일에 붙여넣기
4. **선택**: 함수 이름을 의미있게 변경 (`L` 키 → `decode_bm_0c` 등). 이건 본인 분석 진행에 도움됨

이 정보를 **다음 세션에 가져와서 알려주면**, AI가 디코더 알고리즘을 이해해 [tools/converter/convert_bm_v2.py](../tools/converter/convert_bm_v2.py) 에 반영함.

---

## 5. 다른 진입점 (§4.2~4.4)

§4.1 와 동일한 패턴. 검색할 디버그 문자열만 다름:

| 진입점 | 디버그 문자열 / 위치 | 함수 패턴 (Decompiler에서 찾을 단서) |
|---|---|---|
| §4.2 | `Event_freeID` @ `0xa6e54` | NPC/event 데이터 free 함수. 그 호출자가 _mp extras 파서 |
| §4.3 | `Hero_Free` @ `0xa6e8c` | 캐릭터 데이터 free 함수. 그 호출자가 _cif 파서/실행기 |
| §4.4 | `onEventMessageOkKey` @ `0xa6888` | OK 키 입력 핸들러. switch 문 또는 jump table 가까이가 opcode dispatch |

§4.4 의 `eventManager` 는 매니저 객체 디버그 메시지라 직접 디스패처는 아니지만 그 객체를 사용하는 함수들이 인터프리터 후보.

---

## 6. 막히면 / 결과 전달

- **30분 이상 진척 없으면**: 화면 캡처 + Decompiler C 코드를 저에게 가져오면 같이 추론
- **함수를 찾았다고 확신하면**: 위 Step 7 형식으로 정리해 알려주기
- **이번 세션은 패스하고 싶으면**: §B 보류. §A 대사 번역(~10분, ~$0.66) 또는 §C 사운드 디코더 도구 확보로 전환

---

## 7. 학습 자료 (Ghidra 처음이면)

- 공식 Beginner 튜토리얼: `D:\ghidra_12.0.4_PUBLIC\docs\GhidraClass\Beginner\` 폴더 (PDF 여러 개)
- Ghidra Snippets: https://github.com/HackOvert/GhidraSnippets/blob/master/README.md
- 핵심 단축키만 외워도 됨:
  - `G` — Go to address
  - `Ctrl+Shift+E` — Search text
  - `L` — Rename
  - `;` — Add comment
  - `Ctrl+E` — Edit function signature

처음 1시간은 어떤 도구든 적응 시간. 익숙해지면 분석 속도가 급격히 올라감.

---

## 8. 진척 체크리스트

```
[ ] Ghidra 메인 창 열기 (ghidraRun.bat)
[ ] Hero3 프로젝트 열고 client.bin64000 CodeBrowser 진입
[ ] 0xa61c8 주소로 점프 (G 키)
[ ] "frameBuf is NULL" 문자열 라벨 우클릭 → References to Address
    [ ] 시나리오 A: 참조 발견 → Step 5
    [ ] 시나리오 B: 0건 → Step 6 (수동 추적)
[ ] 후보 함수 식별 (RGB565 + row/col 루프 패턴)
[ ] 함수 주소 + Decompiler C 코드 복사
[ ] 결과를 다음 세션에 가져오기
```
