# §4.4 _scn opcode dispatcher — Ghidra 상세 walkthrough

> 영웅서기3 의 가장 큰 미해독 항목. 풀면 _scn opcode dispatch + 분기/플래그/사운드 트리거 + NPC 위치 (§4.2 잔여) + 4가지가 동시에 풀린다.
>
> 이 문서는 Ghidra 처음 사용자도 막히지 않게 화면 상태 그대로 묘사한 step-by-step. ghidra-gui-guide.md 의 일반 가이드를 §4.4 에 특화한 버전.

---

## 0. 진입 직전 체크 (3분)

### 환경 (이미 셋업)

| 항목 | 경로 |
|---|---|
| Ghidra 12.0.4 launcher | `C:\Users\viewe\Downloads\ghidra_12.0.4_PUBLIC_20260303\ghidra_12.0.4_PUBLIC\ghidraRun.bat` |
| JDK 21 | `C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot\` |
| 분석 대상 | `c:\gameRemake\testrepo\work\h3\extracted\client.bin64000` (719KB) |
| 프로젝트 | `c:\gameRemake\testrepo\work\ghidra_proj\Hero3.gpr` (자동 분석 완료, 1470 함수) |

### 미리 확보된 단서

이번 세션에서 사전 분석으로 확인한 것:
- **디버그 문자열 모두 raw binary 에 살아있음**:
  - `0xa6888`: `onEventMessageOkKey()`
  - `0xa6ad8`: `eventManager->_prevScreenCover : `
  - `0xa6e54`: `Event_freeID`
  - `0xa6e70`: `freeBossType`
  - `0xa6e8c`: `Hero_Free`
  - `0xa6efc`: `;;;;;; loadDataID :: `
- 그러나 `all_decompiled.c` 에는 위 문자열 0건 — Ghidra 자동 xref 가 PIC + GOT indirection 로 못 따라감 (이게 막혀서 사람의 GUI 분석 필요)
- §4.1 BM decoder 풀 때 (`FUN_00010fe4`) 도 같은 상황이었고 **`& 0x3f` grep → 패턴 매칭** 으로 우회했음

### 목표 산출물

- **opcode → 동작 매핑 표** (예: `0x10` = sound_play, `0x12` = jump, `0x14` = set_flag, ...)
- 또는 **dispatcher 함수 주소** (예: `FUN_00012abc`) + 그 함수의 Decompiler C 코드 전체
- 결과는 `tools/converter/convert_scn.py` 와 [scn-format.md](../scn-format.md) 같은 파일에 반영

---

## 1. Ghidra 실행 + CodeBrowser 진입 (3분)

### 1-1. Launcher 실행

탐색기에서 더블클릭:
```
C:\Users\viewe\Downloads\ghidra_12.0.4_PUBLIC_20260303\ghidra_12.0.4_PUBLIC\ghidraRun.bat
```

검은 콘솔 창이 잠깐 뜨고, 5~30초 후 **Ghidra 메인 창** (Project Manager) 이 뜸.

> 만약 "JDK 경로를 묻는 다이얼로그" 가 뜨면: `Browse...` 클릭 → `C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot` 폴더 선택 → OK.

### 1-2. Hero3 프로젝트 열기

좌측 트리에 `Hero3` 가 이미 보임. 안 보이면:
- `File` 메뉴 → `Open Project...`
- 다이얼로그에서 `c:\gameRemake\testrepo\work\ghidra_proj` 로 이동 → `Hero3.gpr` 선택 → OK

### 1-3. CodeBrowser 진입

좌측 트리 `Hero3` 펼치기 → `client.bin64000` 더블클릭 (또는 우클릭 → `Open in Default Tool`).

5~10초 후 **CodeBrowser 창** (메인 분석창) 이 뜬다.

> "Analyze?" 다이얼로그가 뜨면 **No** (이미 분석 완료됨)

### 1-4. 화면 구성 확인

CodeBrowser 창에 5 영역이 있음:
```
┌──────────────────────────────────────────────────────┐
│  메뉴 바 (File, Edit, ..., Search, ..., Window)       │
├─────────────┬───────────────────┬───────────────────┤
│ Symbol Tree │  Listing          │  Decompiler       │
│ (좌)        │  (중앙, 어셈블리) │  (우, C 코드)     │
│             │                   │                   │
│ ─Functions  │  0001a568 LDR ... │  void FUN_0001a568│
│ ─Strings    │  0001a56c BL ...  │  {                │
│ ─Labels     │   ...             │     ...           │
├─────────────┴───────────────────┴───────────────────┤
│  Bookmarks / Console (하단, 작음)                   │
└──────────────────────────────────────────────────────┘
```

만약 Decompiler 창이 안 보이면: `Window` 메뉴 → `Decompiler` 클릭.

### 1-5. 핵심 단축키 외우기 (1분)

| 키 | 동작 |
|---|---|
| `G` | Go to address (예: `0xa6888` 입력 → Enter) |
| `Ctrl+Shift+E` | Search Program Text (메뉴 `Search > Program Text...`) |
| `L` | 현재 라벨/함수 이름 변경 (분석 진행하며 의미있는 이름 붙이기) |
| `;` | 현재 줄에 코멘트 추가 |
| `Ctrl+L` | Search Decompiler text |
| `F2` | 현재 항목 rename (별도 단축키) |

---

## 2. Step 1 — 디버그 문자열로 점프 (5분)

### 2-1. `onEventMessageOkKey` 문자열 위치로 이동

CodeBrowser 어디든 클릭한 후 **`G` 키 누르기**.

다이얼로그가 뜸. 입력창에 `0xa6888` 입력 → Enter.

Listing 창 (중앙)이 그 주소로 점프. 다음 같은 줄이 보일 것:
```
 (offset 0xa6888)  ds   "onEventMessageOkKey()"
```
( `ds` = "defined string" 어셈블리 의사명령 )

### 2-2. 문자열에 라벨 보기

Listing 창에서 그 줄을 보면 옆에 라벨이 있음. 예: `s_onEventMessageOkKey()_000a6888`.

### 2-3. References to Address — 시나리오 분기

라벨(또는 그 줄) **우클릭 → References → Show References to Address**.

새 창 (References to ...) 이 뜬다.

#### 시나리오 A — 참조 1건 이상

표에 `Reference Address | Type | From` 같은 행이 보임. **다행** — 그 행 더블클릭 → 호출하는 함수 (`FUN_xxxxxxxx`) 로 점프.

→ **Step 3 (함수 검증) 으로 넘어감.**

#### 시나리오 B — 참조 0건 (가장 가능성 높음)

표가 비어있음. PIC + GOT indirection 때문에 자동 추적 실패.

→ **Step 4 (패턴 grep 우회) 로 넘어감.**

> §4.1 풀 때도 똑같은 상황이었음. 디버그 문자열 자체로는 함수를 못 찾음. 사람이 패턴으로 찾아야 함.

---

## 3. Step 2 (백업) — 다른 단서 문자열도 점검 (2분)

이왕 들어왔으니 다른 단서들도 한번 보고 가자. `G` 키로 다음 주소들 차례로 확인:

| 주소 | 문자열 | 시나리오 A 면 추적할 것 |
|---|---|---|
| `0xa6888` | `onEventMessageOkKey()` | 키 입력 핸들러 — opcode dispatcher 의 호출 진입점 가능성 |
| `0xa6ad8` | `eventManager->_prevScreenCover : ` | eventManager 객체 내부 디버그 — opcode 처리 직접 함수는 아닐 것 |
| `0xa6e54` | `Event_freeID` | 이벤트 데이터 free 함수 — 그 호출자가 _mp 또는 _scn 파서 |
| `0xa6efc` | `;;;;;; loadDataID :: ` | _mp 데이터 로더 — §4.2 직접 진입점 |

각각 우클릭 → References → Show References to Address. 시나리오 A 가 하나라도 있으면 그것부터 추적.

---

## 4. Step 3 — 패턴 grep 우회 (15~30분, 가장 가능성 높은 경로)

자동 xref 가 0건일 때 §4.1 풀 때 썼던 방법.

### 4-1. 사전 식별된 후보 함수 목록 (이번 세션 분석)

`all_decompiled.c` 에서 미리 후보를 좁혀둠. opcode dispatcher 패턴 = 작은 정수 상수와의 다중 비교 + while 루프 + 함수 포인터 호출.

다음 함수들을 **순서대로** Decompiler 에서 열어보고 패턴 검증:

| 후보 | 위치 | 크기 | 특징 |
|---|---|---|---|
| `FUN_000186c8` | `0x186c8` | 14k | distinct opcodes 7 + fp call 4 (가장 유력) |
| `FUN_000182c4` | `0x182c4` | 7k | distinct opcodes 7, 적당한 크기 |
| `FUN_00018d08` | `0x18d08` | 7k | distinct opcodes 7 |
| `FUN_000190f8` | `0x190f8` | 10k | distinct opcodes 7 + fp call 1 |
| `FUN_00098ef8` | `0x98ef8` | 1.8k | 작아서 빠르게 봄, 진짜 dispatcher 일지 |

**열기 방법**: `G` 키 → 주소 입력 (예: `0x186c8`) → Enter → 우측 Decompiler 가 자동으로 그 함수 표시.

### 4-2. dispatcher 패턴 식별

opcode dispatcher 라면 다음 형태가 보여야 함:

```c
void FUN_xxxxx(int *script_ptr, ...) {
    while (...) {  // 또는 do { ... } while
        opcode = *script_ptr;       // 1바이트 읽기
        script_ptr++;               // 또는 script_ptr += N

        if (opcode == 0x01) { ... handler1 ... }
        else if (opcode == 0x02) { ... handler2 ... }
        // ...많은 분기
        else if (opcode == 0x14) { ... handler20 ... }

        // 또는 switch 문 (Ghidra가 if-else로 풀었을 가능성)
    }
}
```

또는 함수 포인터 테이블 형태:
```c
(*(code **)(jump_table + opcode * 4))(script_ptr);
```

핵심 표지:
- **단일 byte read** (`*pbVar`, `(byte *)`, `(uint)*pbVar`, `cVar1 = *pcVar`) 가 시작
- **포인터 advance** (`script_ptr++`, `script_ptr = script_ptr + N`)
- **많은 작은 정수와의 비교** (`== 1`, `== 2`, `== 0x10`, ...)
- **루프** (`while`, `do`, `for`)

### 4-3. 검증된 함수 발견 시 — opcode 매핑 추출

각 분기 안에서 어떤 일이 일어나는지 본다:
- `script_ptr` 가 N 바이트 advance? → opcode 길이 N
- 다른 함수 호출 (예: `play_sound`, `set_flag`) → 그게 handler

표 만들기:
| opcode | length | handler | 추정 동작 |
|---|---|---|---|
| 0x01 | 3 | FUN_xxx | sound trigger? |
| 0x02 | 5 | FUN_yyy | jump to script offset? |
| ... | | | |

### 4-4. 이름 변경 (선택, 분석 진행에 도움)

확신 들면 **`L` 키** 로 함수 이름 변경:
- `FUN_000186c8` → `scn_dispatch`
- 분기 안 호출되는 함수들도 같이 (예: `FUN_xxx` → `op_play_sound`)

---

## 5. Step 4 (백업) — 추가 우회 방법

Step 3 의 후보 5개를 다 봤는데 아무것도 dispatcher 처럼 안 생겼으면:

### 5-1. Symbol Tree 키워드 검색

좌측 Symbol Tree → `Functions` 펼치기 → 상단 Filter 박스에:
- `event` / `script` / `interp` / `parse` / `exec` / `dispatch` / `run`

이런 키워드 입력. 매칭되는 함수 클릭 → Decompiler 에서 패턴 확인.

### 5-2. Search → Memory (상수 검색)

`Search` 메뉴 → `For Direct References...` 또는 `Memory...` 클릭.
- "Hex Sequence" 모드
- 입력: 추정되는 opcode jump table 의 첫 두 바이트 (예: 짧은 함수 주소 패턴)

또는 _scn 파일 자체에 자주 등장하는 byte 값을 binary 안에서 찾기:
- `tools/recon/analyze_scn_segments.py` 결과의 가장 흔한 opcode 와 매칭

### 5-3. all_decompiled.c 직접 텍스트 검색

`c:\gameRemake\testrepo\work\ghidra_out\all_decompiled.c` (469k 줄) 를 VS Code 등에서 열고:
- 정규식 검색: `(==|!=) (0x1[0-9a-f]|0x2[0-9a-f])` 가 5건 이상 있는 함수
- "함수 시작 주소 + while + byte 비교 다중" 패턴

```powershell
# PowerShell 에서 빠르게 후보 추리기
Select-String -Path "c:\gameRemake\testrepo\work\ghidra_out\all_decompiled.c" `
              -Pattern "FUN_[0-9a-f]+" | Select-Object -First 10
```

(이번 세션에서 이미 해서 §4-1 의 5개 후보 추렸음)

---

## 6. Step 5 — 결과 가져오기 (5분)

뭘 찾았든 다음 형태로 정리해서 다음 세션에 가져옴:

### 6-1. Dispatcher 함수 발견 시

```
=== §4.4 dispatcher candidate ===
function: FUN_000186c8 @ 0x000186c8
matched pattern: while loop + 7 distinct byte opcodes + 4 fp calls

decompiler output:
[우측 Decompiler 창에서 Ctrl+A → Ctrl+C → 여기 붙여넣기]
```

### 6-2. opcode 매핑 추출 시

```
=== §4.4 opcode table ===
opcode 0x01 (3 bytes): handler FUN_xxx — guess: sound_play
opcode 0x02 (5 bytes): handler FUN_yyy — guess: jump_offset
opcode 0x10 (1 byte):  inline       — guess: end_of_script
...
```

### 6-3. 30분 시도 후 막힘

Decompiler 화면 캡처 + `eventManager` 주변 디스어셈블리 캡처 → 가져오면 같이 추론.

---

## 7. 진척 체크리스트

```
[ ] 1-1 Ghidra 실행
[ ] 1-2 Hero3 프로젝트 열기
[ ] 1-3 client.bin64000 CodeBrowser 진입
[ ] 2-1 G 키 → 0xa6888 점프
[ ] 2-3 References to Address — 시나리오 A or B
[ ] (시나리오 A) 호출자 함수로 점프 → Step 3 패턴 검증
[ ] (시나리오 B) §4-1 후보 5개 차례로 검증
    [ ] FUN_000186c8 (가장 유력)
    [ ] FUN_000182c4
    [ ] FUN_00018d08
    [ ] FUN_000190f8
    [ ] FUN_00098ef8
[ ] dispatcher 후보 발견 → opcode 분기 추출
[ ] 결과 정리 (§6) 후 다음 세션에 전달
```

---

## 8. 막히면

- **30분 시도해도 dispatcher 안 보임**: §4-1 후보 외에 §5 의 키워드 검색 / 상수 검색 시도
- **후보 함수가 진짜 dispatcher 인지 헷갈림**: 그 함수의 Decompiler C 코드 통째로 가져와서 같이 봄
- **이번 세션은 패스**: §4.4 는 시간이 좀 걸림. 대신 SMAF→OGG (외부 도구 받기) 또는 LLM 대사 번역 (~$0.66) 으로 전환 가능

성공 사례 참고: §4.1 풀 때 (`docs/h3/PROGRESS.md` §"2026-05-06 세션 작업 압축") 6단계로 풀었음. 같은 패턴.
