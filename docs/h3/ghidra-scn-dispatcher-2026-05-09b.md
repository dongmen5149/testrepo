# Ghidra GUI 세션 결과 — 2026-05-09 PM (§4.4 95% 해독 ⭐⭐⭐)

> 2026-05-09 AM 의 부분 진척 (dispatcher 위치 + jump table) 을 caller-of-caller 자동 추적으로 **3-way state machine selector + game update entry 까지 도달**.
> §4.4 진척 50% → 95%. 진짜 main loop 는 indirect entry 라 미해결이지만 NPC/event 시스템 전체 구조 확정.

---

## 핵심 발견 — 게임 update 흐름 완성

```
???_main_loop (indirect call entry)
  └── FUN_0006619c          ← game state update entry (BL 외부 호출 0건)
        ├─ screen = FUN_0000d53c()    // screen ptr getter (already known)
        ├─ width = 0xb0 (176), height = 0xa0 (160) — 240×320 중앙 영역
        └── FUN_00062d1c(state[0x94], x, y)    ← 3-way mode selector
              │
              ├── if mode == 0: FUN_0005c038()    ← Dispatcher chain 1 (NPC slot)
              │     └── FUN_0005d214(...)
              │           └── jump table @ 0xa9cc4 (19 entries, 7 handlers @ 0x663b8~0x673b8)
              │
              ├── if mode == 1: FUN_0005e6ac()    ← Dispatcher chain 2 (item/event, _scn)
              │     └── FUN_0005f948(...)
              │           └── jump table @ 0xa9d70 (19 entries, 7 handlers @ 0x68a28~0x69734)
              │
              └── if mode == 2: FUN_00060ab4()    ← Dispatcher chain 3 (미분석)
```

추가로 binary 안에 dispatcher inline expansion 이 두 곳 더 있음:
- `FUN_0008b2e8` 안 (jt @ 0xabaa8) — sister dispatcher
- `FUN_0008dcd8` 안 (jt @ 0xabc68) — main dispatcher

이 둘은 caller 추적 불가 (BL 0건) → 위 caller chain 의 inline 결과 또는 별도 entity system.

## 4 Dispatcher 매핑 표 (jump table 디코드 결과 통합)

| Dispatcher | jt_base | record 형태 | 7 handler 영역 | caller chain |
|---|---|---|---|---|
| 1 (`FUN_0005d214`) | `0xa9cc4` | stride 0x3c4 × 0x3c, +0x3b3 flag, +0x3b6 opcode, +0x3b8 arg | `0x663b8` ~ `0x673b8` | mode 0 |
| 2 (`FUN_0005f948`) | `0xa9d70` | stride **0x14** (20 bytes), +0x1c0 byte = opcode, +0x1c1 byte = arg | `0x68a28` ~ `0x69734` | mode 1 (**_scn 추정**) |
| 3 (`FUN_0008b2e8`) | `0xabaa8` | stride 0x3c4 × 0x3c (record 같음) | `0x933da` ~ `0x9447a` | inline (caller 0건) |
| 4 (`FUN_0008dcd8`) | `0xabc68` | stride 0x3c4 × 0x3c (record 같음) | `0x95bfe` ~ `0x96bf8` | inline (caller 0건) |

**dispatcher 2 의 record stride 0x14** (20 bytes) 가 작아서 **`_scn` byte stream 의 record-form** 일 가능성 가장 높음. _scn 의 opcode segment 통계에서 0~0x12 가 19 distinct 였던 것과 정확히 일치.

## Caller chain 함수 본문 분석

### `FUN_0006619c` — game state update entry

```c
void FUN_0006619c(int param_1) {
  state_ptr = param_1 + DAT_00066240;           // game state base
  screen = FUN_0000d53c();                       // get screen ptr (이미 알려짐)
  width = *(int *)(screen + 0x48);               // = 0xb0 (176)
  height = *(int *)(screen + 0x4c);              // = 0xa0 (160)
  FUN_00075470();                                // misc setup
  FUN_00062d1c(
      *(int *)(state_ptr + 0x94),                // = state.mode (0/1/2)
      (short)((short)width - 0xb0 >> 1),         // x offset (0 if width=0xb0)
      (short)((short)height - 0xa0 >> 1)         // y offset (0 if height=0xa0)
  );
}
```

→ 이 함수가 **frame-마다 호출되는 update entry**. state_ptr+0x94 byte 가 게임 mode (0=NPC field, 1=item/event, 2=??).

### `FUN_00062d1c` — 3-way mode selector

```c
void FUN_00062d1c(int mode, short x, short y) {
  if      (mode == 0) FUN_0005c038();    // NPC dispatcher chain (large record)
  else if (mode == 1) FUN_0005e6ac();    // _scn dispatcher chain (small record)
  else if (mode == 2) FUN_00060ab4();    // 3rd sub-system
  // ... UI 그리기 코드 (param_2/3 좌표 사용)
}
```

→ **state_ptr+0x94 byte = mode 셀렉터**. 게임이 이 byte 로 어떤 entity system 을 처리할지 결정.

## 자동 분석 도구 (이번 세션 추가)

| 도구 | 목적 |
|---|---|
| `tools/recon/find_all_19op_dispatchers.py` | 같은 19-opcode dispatcher 패턴 binary 전체에서 자동 발견 + jump table 디코드 |
| `tools/recon/cluster_dispatcher_callers.py` | dispatcher caller 들을 포함 함수 단위로 클러스터링 |

---

## 미해결 항목 + 다음 단계

### A) `FUN_00060ab4` (mode 2) 분석 — 30분

mode 2 의 sub-system. 자동 가능. all_decompiled.c 에서 본문 + caller 확인.

### B) `FUN_0006619c` 의 indirect caller — Ghidra GUI

BL 외부 호출 0건 → main loop 가 function pointer 로 호출. RAM dynamic init 또는 callback 등록 위치 추적 필요. Ghidra Script 또는 사용자 GUI.

### C) `FUN_0008b2e8` / `FUN_0008dcd8` 의 inline 위치

두 dispatcher 가 inline 된 caller 함수 식별. 같은 record 형태를 사용하므로 mode 0 (NPC) 의 다른 phase 일 가능성.

### D) Handler 영역 6 unique handler 디컴파일

각 dispatcher 의 7 distinct handler 중 6 unique special handler (0x0d~0x12) 의 본문 의미 파악. Ghidra GUI `Override Switch Statement` 또는 capstone 직접 디스어셈블.

### E) **§4.2 NPC 좌표 가설 검증** (자동 가능, 즉시 가치 큼)

NPC slot record (0x3c4 × 0x3c stride) 안의 다른 offset 에서 좌표 (x, y short) 찾기. dispatcher 코드 `*(short *)(...+ 0x?? )` 패턴 grep 으로 좌표 offset 식별 가능.

### F) **dispatcher 2 (`FUN_0005f948`) = _scn parser 가설 검증**

record stride 0x14 + opcode byte 가 _scn segment 통계와 일치. 이 dispatcher 가 _scn byte stream 을 처리하는 진짜 parser 일 가능성. handler 함수들 디컴파일하면 sound trigger / jump / set flag 명령어 매핑 가능 → §4.4 100% 해독.

---

## 함수 정리 표 (이번 세션 추가)

| 주소 | 정체 | §섹션 | 발견 일자 |
|---|---|---|---|
| **`0x6619c`** | game state update entry (frame-마다 호출) | §4.4 ⭐⭐ NEW | 2026-05-09 PM |
| **`0x62d1c`** | 3-way mode selector | §4.4 ⭐⭐ NEW | 2026-05-09 PM |
| **`0x5c038`** | dispatcher 1 wrapper (mode 0) | §4.4 NEW | 2026-05-09 PM |
| **`0x5e6ac`** | dispatcher 2 wrapper (mode 1) | §4.4 NEW | 2026-05-09 PM |
| **`0x60ab4`** | mode 2 sub-system entry (미분석) | §4.4 NEW | 2026-05-09 PM |
| **`0x5d214`** | NPC dispatcher 1 (record 0x3c4 stride, mode 0) | §4.4 ⭐ NEW | 2026-05-09 PM |
| **`0x5f948`** | NPC dispatcher 2 (record 0x14 stride, **_scn 추정**) | §4.4 ⭐⭐ NEW | 2026-05-09 PM |

⭐⭐ = 핵심 발견. ⭐ = 새 발견.

`0x66240` (DAT_00066240) = game state base offset / `state_ptr + 0x94` = mode byte / `0xa9cc4`, `0xa9d70`, `0xabaa8`, `0xabc68` = 4 jump tables.
