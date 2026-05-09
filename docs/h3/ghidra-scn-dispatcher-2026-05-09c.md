# Ghidra 자동 분석 후속 — 2026-05-09 PM 후반-2 (§4.4 종합 정리)

> 2026-05-09 PM 의 95% 진척에 이어 1A/1B/1C/1E 자동 분석 완료.
> dispatcher 2 가 _scn parser 가 아니라 **menu/dialog UI handler** 임을 capstone 디스어셈블로 확인 (재해석).
> 3 game system entry (`FUN_0006619c`, `FUN_0008b2e8`, `FUN_0008dcd8`) 모두 PIC indirect call — main loop 는 미도달.

---

## 1A — dispatcher 2 (`FUN_0005f948`) handler 6개 capstone 분석

handler 영역: `0x68a28 ~ 0x6a000` (총 7 distinct case label).

각 handler 의 BL/BLX targets 통계:

| handler | size | BL count | 주요 호출 함수 |
|---|---|---|---|
| 0x00~0x0c default | 1268 B | 23 | `0x3ecfc` (sprite text), `0x99764` (sound), `0x77b70` (?) |
| 0x0d | 304 B | 7 | `0x3ecfc`, `0x99764`, `0x77b70`, `0x39ad0`, `0x69d68` |
| 0x0e | 384 B | 0 | (capstone 디스어셈블 실패 — 데이터 영역 가능성) |
| 0x0f | 592 B | 16 | 반복 패턴 × 2: `0x3ecfc → 0x99764 → 0xa42a4 → 0x77b70 → 0xd53c → 0x9fd64 → 0x69d68` |
| 0x10 | 454 B | 19 | dense — `0x99764(#0x71)` sound + 반복 sprite/text drawing |
| 0x11 | 338 B | 9 | 단순 sprite/text + sound 한 번 |
| 0x12 | (~ 추정 700 B) | (다수) | (마지막, 분석 미완) |

### 핵심 함수 호출 패턴

| 호출 함수 | 기능 추정 |
|---|---|
| `FUN_0003ecfc` (sprite text drawing) | UI 텍스트 렌더링 (이미 알려진 utility) |
| `FUN_00099764(arg)` | **sound trigger** (예: `arg=0x71` = sound ID 113) |
| `FUN_0000d53c` | screen ptr getter (이미 알려짐) |
| `FUN_0009fd64` | UI buffer/state utility |
| `FUN_000a42a4` | UI sync/wait utility |
| `FUN_00077b70` | text/string utility |

→ **dispatcher 2 = menu/dialog state machine** (각 handler 가 UI 한 phase 처리). _scn parser 가 아님.

### 재해석 — 진짜 _scn parser

`_scn` 의 byte-stream opcode dispatcher 는 발견된 4 dispatcher 와 별개 위치에 있을 가능성. 19-opcode 매칭은 컴파일러가 같은 dispatcher 패턴 (0~0x12 jump table) 을 여러 sub-system 에 사용한 것 (NPC/menu/battle/UI 모두 0~0x12 enum 으로 처리).

→ §4.4 _scn 자체 해독은 다음 세션 과제. 현재 발견은 게임 update flow 전체 구조 + 3 game state machine.

---

## 1B — NPC slot record offset grep (자동 한계)

dispatcher 1 (`FUN_0005d214`) 과 dispatcher tail (`0x8e89e`) 본문 grep 결과:

| offset | type | 의미 |
|---|---|---|
| `+0x3b3` | byte | 활성 flag (이미 확정) |
| `+0x3b6` | short | opcode (이미 확정) |
| `+0x3b8` | short | arg (이미 확정) |
| `+0x1e/+0x20/+0x22` | byte | 다른 record (stride 0x3c) inner offset |

→ **dispatcher 코드 자체에는 NPC 좌표 access 없음**. 좌표는 handler 영역 (`0x95bfe~0x96bf8` 등, Ghidra 미인식) 또는 NPC init 함수에 있음. capstone 으로 handler 디스어셈블 시 해당 access 보일 가능성. 다음 세션 과제.

---

## 1C — `FUN_00060ab4` (mode 2 entry, 9KB)

| 항목 | 결과 |
|---|---|
| 진짜 함수 시작 | `0x60ab4` (push {r4,r5,r6,r7,lr} 확인) |
| 함수 끝 (다음 push) | `0x62d1c` (= `FUN_00062d1c` 시작) |
| 크기 | **약 9KB** (큰 함수) |
| Ghidra 디컴파일 | panic stub (`FUN_0004ad10()`) 만 — 본문 못 풀음 |
| 추정 | 또 다른 NPC/event sub-system 또는 battle/cutscene system. 본문은 capstone 또는 사용자 GUI `Clear Code Bytes + Re-disassemble` 후 분석 필요 |

`FUN_00062d1c` (3-way selector) 가 `param_1 == 2` 일 때 이 함수 호출 — game state mode 2 의 사용처 미확인.

---

## 1E — Dispatcher 3/4 inline 위치 caller chain

`FUN_0008b2e8` 와 `FUN_0008dcd8` 의 dispatcher inline 위치 추적:

| dispatcher | jump table call site | 호출 BL 위치 | 호출자 함수 |
|---|---|---|---|
| dispatcher 3 (jt 0xabaa8) | `FUN_0008d5e4` | BL @ `0x8c19c` | **`FUN_0008b2e8`** 안 |
| dispatcher 4 (jt 0xabc68) | `FUN_0008ff18` | BL @ `0x8eb80` | **`FUN_0008dcd8`** 안 |

→ dispatcher 3, 4 가 진짜로 sister (`FUN_0008b2e8`) 와 main (`FUN_0008dcd8`) 안에서 호출됨. 두 함수 자체의 BL caller 는 0건 → indirect call 로만 진입.

---

## 종합 — 3 Game System Entry (모두 indirect call)

```
???_indirect_main_loop  (PIC indirect, Ghidra 추적 불가)
  ├ FUN_0006619c          ← game update entry (UI center calc + 3-way mode selector)
  │  └ FUN_00062d1c       ← 3-way selector
  │    ├ mode 0 → FUN_0005c038 → FUN_0005d214 (NPC dispatcher 1, record 0x3c4×0x3c)
  │    │                          └ jump table @ 0xa9cc4
  │    ├ mode 1 → FUN_0005e6ac → FUN_0005f948 (menu/dialog dispatcher 2, record 0x14)
  │    │                          └ jump table @ 0xa9d70
  │    └ mode 2 → FUN_00060ab4 (9KB, 미해독)
  │
  ├ FUN_0008b2e8           ← sister entry (record 0x3c4)
  │  └ inline @ 0x8c19c → FUN_0008d5e4 → jump table @ 0xabaa8
  │
  └ FUN_0008dcd8           ← main entry (record 0x3c4)
     └ inline @ 0x8eb80 → FUN_0008ff18 → jump table @ 0xabc68
```

**3 entries 가 모두 PIC indirect call 진입** — game framework 가 함수 포인터로 frame 마다 호출. main loop 는 RAM dynamic init 추적이 필요 (사용자 GUI / Ghidra Script).

---

## 자동화 도구 (이번 세션 추가)

| 도구 | 목적 |
|---|---|
| `tools/recon/disasm_dispatcher2_handlers.py` | dispatcher 2 의 7 handler capstone 디스어셈블 + BL targets 추출 |
| `tools/recon/find_npc_record_offsets.py` | NPC slot record 안의 모든 offset access 추출 + 좌표 후보 식별 |

---

## 미해결 — 다음 세션 우선순위

| 우선 | 작업 | 자동/수동 |
|---|---|---|
| ⭐ A | NPC handler 영역 (`0x95bfe~0x96bf8`, `0x933da~0x9447a`) capstone 디스어셈블 → 좌표 offset 발견 | **자동 가능** |
| ⭐ B | `FUN_00060ab4` (mode 2) capstone 본문 디스어셈블 → 미해독 sub-system 식별 | **자동 가능** |
| C | `FUN_0006619c` / `FUN_0008b2e8` / `FUN_0008dcd8` indirect caller (main loop) 추적 | 사용자 GUI / Ghidra Script |
| D | 진짜 _scn byte stream parser 위치 발견 — 다른 dispatcher 패턴 검색 (byte 단위 opcode) | 자동 시도 가능 |
| E | dispatcher 1 의 6 unique handler (`0x663b8 ~ 0x673b8`) 디컴파일 — NPC behavior 의미 | 자동 가능 |
