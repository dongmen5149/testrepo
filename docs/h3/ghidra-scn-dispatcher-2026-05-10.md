# §4.4 후속 — 2026-05-10 세션 (state[0x94] 재해석 + 3 entry caller 한계 확정)

> 2026-05-09 PM 후반-3 의 자동 분석 ceiling 도달 후, 사용자 GUI 동행 분석 세션.
> **결과**: main loop 추적 자체는 미해결이지만, **`state[0x94]` 의 정체가 mode/battle 이 아닌 3-페이지 UI 탭 인덱스**로 재해석됨. PROGRESS 의 다수 가설 정정 필요.

---

## 1. 사용자 GUI 협업 진행 — 단계별 결과

### 1A. 함수 포인터 hex 검색 (Search → Memory) — ❌ 0건

3 entry 의 thumb-bit-set 주소 (`0x6619d` / `0x8b2e9` / `0x8dcd9`) 와 thumb-bit-clear 주소 (`0x6619c` / `0x8b2e8` / `0x8dcd8`) 모두 6번 검색 → **6건 모두 0건**.

→ 함수 포인터가 정적 데이터에 박혀 있지 않음. **런타임 동적 주입** 확정.

### 1B. 바이너리 시작 (`0x00000000`) 관찰

```
0x00000000: Reset(undefined1*)        04 e0 c0 46  strbmi  lr,[param_1],r4
0x00000004: UndefinedInstruction      24 02 04 20  andcs   r0,r4,r4,lsr #0x4    XREF[3]: 9092c(R), 90976(R)
0x00000008: SupervisorCall            01 00 02 00  andeq   r0,r2,r1             Entry Point
0x0000000c: PrefetchAbort             ...
```

- 표준 ARM 예외 벡터 슬롯 라벨이 자동 부여됨
- 그러나 바이트 (`04 e0 c0 46` 등) 는 정상 ARM 분기 명령이 아님 → SKT GVM 펌웨어가 표준 예외 벡터를 안 씀
- **이상한 점**: `UndefinedInstruction` (0x4) 을 `0x9092c`, `0x90976` 두 곳에서 **읽음** (R). 코드가 예외 벡터 주소를 읽는 건 매우 드뭄. 향후 분석 단서로 메모.

### 1C. GOT 베이스 (`0xb2c40`) 확정 ⭐

```
DAT_000b2c40                    XREF[20+]
  ← FUN_00000f9c:00000fae(R)
  ← FUN_00000f9c:00000fd4(W)         ← 쓰기!
  ← FUN_00000ffc:0000100e(R)
  ← FUN_00000ffc:00001054(W)         ← 쓰기!
  ← FUN_000010c0:000010d6(R)
  ← FUN_000010f4:0000110e(R)
  ← FUN_000010f4:000011a2(R)
  ← FUN_000238b4:000238b8(*)
  ← FUN_0005b828:0005b82c(*)
  ← FUN_0006b8e8:0006b8ec(*)
  ← FUN_0007e3b4:0007e3e6(*)
  ← FUN_0007e4c4:0007e4ea/518/52e(*)
  ← FUN_00097f44:00097f5c(*)
  ← FUN_000983e8:00098410(*)
  ← FUN_0009f8c0:0009f8c6(*)
  ← FUN_000a2628:000a2640(*)
  ← FUN_000a38a8:000a38ac(*)
  ← FUN_000a38dc:000a38e0(*)
  ... [more]
```

- **20+ 함수가 GOT base 접근** → `0xb2c40` 가 진짜 GOT 시작
- 4 매우-작은-주소 함수 (`0xf9c / 0xffc / 0x10c0 / 0x10f4`) 가 GOT 슬롯에 **쓰기** 수행 → KVM/GVM API wrapper

### 1D. 4 low-address 함수 디컴파일 — file/resource API 확정

| 함수 | 정체 |
|---|---|
| `FUN_00000f9c` | **resource open** — `FUN_00099a9c(param_1, &uStack_14)` 호출, state=2 셋, 핸들 저장 |
| `FUN_00000ffc` | **resource close** — 핸들 → `FUN_000a42a0()` (veneer) → 0 클리어 |
| `FUN_000010c0` | **record count getter** — `FUN_000997b4(handle+8, 0)` short 반환 |
| `FUN_000010f4` | **record-by-index reader** — bounds check + sequential seek (`FUN_0009979c`) + read |

→ **이건 main loop 가 아닌 GVM 파일 시스템 API 래퍼**. 매니저 단서 없음.

### 1E. 3 entry XREF 직접 확인 (Listing 창)

| 함수 | XREF |
|---|---|
| `FUN_0006619c` | 0건 (XREF 라벨 없음) |
| `FUN_0008b2e8` | 0건 |
| `FUN_0008dcd8` | 0건 (Ghidra GUI 에는 인식돼 있으나 헤드리스 export 누락) |

→ **이전 세션 결론 재확인**: 모두 indirect call 만으로 진입.

---

## 2. 핵심 발견 ⭐⭐ — `state[0x94]` 의 정체 재해석

### 2A. `FUN_0006619c` 디컴파일 깨끗 확인

```c
void FUN_0006619c(int param_1) {
  iVar2 = param_1 + DAT_00066240;     // state 포인터 보정
  iVar1 = FUN_0000d53c();              // screen ptr getter
  uVar3 = *(undefined4 *)(iVar1 + 0x48);   // screen.x
  uVar4 = *(undefined4 *)(iVar1 + 0x4c);   // screen.y
  FUN_00075470();
  FUN_00062d1c(*(int *)(iVar2 + 0x94),     // state[0x94] = mode/page selector
               (short)((short)uVar3 + -0xb0 >> 1),   // (screen.x - 176) / 2
               (short)((short)uVar4 + -0xa0 >> 1));  // (screen.y - 160) / 2
  return;
}
```

- 매 프레임 entry → `FUN_00062d1c(state[0x94], screen_offset_x, screen_offset_y)` 호출
- 화면 중앙 보정값 `-0xb0/2 = -88`, `-0xa0/2 = -80` → 240×320 화면 기준 (240/2=120, 320/2=160 에 가까움)

### 2B. `FUN_00070f34` 발견 — 키 입력 핸들러 ⭐

`+ 0x94)` 와 `= 2` 패턴 grep 으로 1건 발견 → 분석 결과:

```c
void FUN_00070f34(int param_1, int param_2) {
  iVar1 = param_1 + DAT_000711ec;       // ★ FUN_0006619c 와 동일 패턴 (state 보정)
  
  if (state[0x94] == 1 && param_2 == 0x2a) {       // page=1 + '*' 키
    *(undefined4 *)(iVar1 + 0x9c) = 0xc;
    *(undefined1 *)(iVar1 + 0x460) = 1;
  }
  else if (param_2 == -0x10) {                     // -16 (special key)
    if (...some-conditions...) {
      *(undefined4 *)(iVar1 + 0x94) = 0;           // page = 0
    }
  }
  else if (param_2 == 0x31) {                      // '1' 키 (ASCII)
    iVar2 = state[0x94] - 1;
    if (iVar2 < 0) state[0x94] = 2;                // page-- with wrap (-1 → 2)
  }
  else if (param_2 == 0x33) {                      // '3' 키
    iVar2 = state[0x94] + 1;
    if (2 < iVar2) state[0x94] = 0;                // page++ with wrap (3 → 0)
  }
  else {
    FUN_00064048();                                // default key handler
  }
}
```

### 2C. 결정적 의미 — `state[0x94]` 는 **3-페이지 UI 탭 인덱스**

키 '1' / '3' 으로 0 → 1 → 2 → 0 순환. **mode/battle/menu 분기가 아님**.

→ PROGRESS.md 의 기존 해석 다수 정정:
- ❌ 기존: "mode 0 = NPC dispatcher / mode 1 = menu/dialog / mode 2 = battle"
- ✅ 정정: **"page 0 / page 1 / page 2 = 한 화면 안의 3개 탭"** — 같은 UI 의 다른 뷰
- ❌ 기존: `FUN_00060ab4` (mode 2, 9KB) = battle 또는 cutscene 추정
- ✅ 정정 추정: **3번째 탭 페이지 UI** — 7KB 임베디드 데이터 = UI 레이아웃 데이터로 잘 맞음
- ✅ 진짜 battle 트리거는 **별도 위치** (state[0x94] 추적은 의미 없음)

### 2D. `FUN_0006619c` ↔ `FUN_00070f34` paint/key 짝 가설

같은 state 구조 (offset 0x94 / 0x9c / 0x460) + 같은 보정 패턴 (`param_1 + DAT_xxxxx`):
- `FUN_0006619c(state)` = paint/tick callback (매 프레임)
- `FUN_00070f34(state, key)` = key event callback

→ **둘 다 GVM framework 콜백 함수**. 같은 매니저가 호출할 가능성 매우 높음.

→ 그러나 `FUN_00070f34` 의 BL caller 도 0건 (재확인) — main loop 추적 한계는 동일.

---

## 3. 기각된 가설 (2026-05-09 PM-3 까지의 분석 정정)

| 가설 (이전) | 현재 평가 |
|---|---|
| `FUN_00062d1c` 가 game state machine 의 mode selector | ⚠ 부분 맞음. 실제로는 **3-페이지 UI 의 페이지 dispatcher** (battle/dialog 같은 큰 분기 아님) |
| mode 2 (`FUN_00060ab4`) = battle/cutscene/map transition | ❌ 기각. **3번째 탭 페이지** 일 가능성 (UI 레이아웃 데이터 기반) |
| dispatcher 1 (NPC dispatcher) — 19 opcode 가 NPC 행동 | 재검토 필요. 페이지 0 의 컨텐츠 — 게임 화면 내 19개 UI 요소 일 수도 |
| dispatcher 2 (`FUN_0005f948`) = menu/dialog UI handler | ✅ 유지. 단 "menu/dialog 모드 진입" 이 아니라 **페이지 1 탭 컨텐츠** 라는 위상 |
| 3 entry indirect caller 추적 가능 (Ghidra GUI) | ❌ 한계. Ghidra Script 작성 (`BLX register` 패턴 + `MOVW/MOVT FUN_xxx` 조합 검색) 이 필요 |

---

## 4. 다음 세션 권장 — 정정된 우선순위

### A) **state[0x94] 재해석 반영** ✅ (이번 세션 완료)
- 본 문서 + PROGRESS.md ⚡ 섹션 갱신

### B) **3-page UI 검증** [자동 가능]
- `FUN_00060ab4` 의 7KB 임베디드 데이터를 UI 레이아웃으로 해석 시도
- `tools/recon/parse_mode2_ui_data.py` 신규 작성: 4-byte aligned word stream → coord/sprite-id 패턴 매칭

### C) **진짜 battle 트리거 식별** [신규 우선순위]
- `state[0x94]` 가 battle 분기 아님 → 다른 state offset 또는 별도 entry function 추적
- 후보: `iVar1 + 0x460` (FUN_00070f34 에서 셋) 같은 boolean flag
- 또는 `FUN_00064048` (default key handler) 분석

### D) **main loop Ghidra Script** [낮은 우선순위]
- ROI 낮아짐 (state[0x94] 재해석으로 main loop 의 가치 감소)
- 시도하려면: `BLX register` 명령어 + 직전 ~10 instr 안에 `LDR Rn, [pc, #x]` 또는 `MOVW/MOVT` 로 FUN_0006619c 주소 만드는 패턴 검색
- 1~2 시간, 성공 보장 X

### E) **사용자 블로커 작업** ⭐ 권장 (게임 체감 영향 큼)
- **SMAF→OGG 변환** — `smaf2midi` 등 도구 검색, 33개 BGM/SFX 활성
- **대사 LLM 번역** — `ANTHROPIC_API_KEY` 셋 → `translate_dialogues.py` 실행 (~$0.66, 9,741 대사)

---

## 5. 사용된 도구 / 분석 자료

- Ghidra 12.0.4 GUI (`ghidraRun.bat`)
- `c:/gameRemake/testrepo/work/ghidra_proj/Hero3.gpr`
- `c:/gameRemake/testrepo/work/ghidra_out/all_decompiled.c` (1470 함수, 469k 줄)
- 검색 도구: Grep, Read

## 6. 핵심 교훈

1. **PIC 바이너리에서 indirect call 의 caller 추적은 정적 분석 ceiling**. Ghidra 자동 + GUI XREF 모두 0건. Script + 패턴 매칭이 마지막 카드지만 ROI 낮음.
2. **PROGRESS 가설은 자주 검증 필요**. "mode 0/1/2 = 게임 시스템 분기" 가설을 4 세션 동안 끌고 왔으나 키 입력 핸들러 1개 발견으로 즉시 기각. **빠른 가설 정정 절차** 가 분석 효율에 핵심.
3. **사용자 GUI 협업의 가치**: hex 검색 / 화면 캡처 같은 단순 작업도 자동 분석이 못 본 단서 (예: 0xb2c40 의 20+ XREF 분포) 를 시각화. 다만 GUI 작업의 ROI 가 낮은 단계는 일찍 인지하고 우회.
4. **자동 디컴파일 export (all_decompiled.c) 의 한계**: Ghidra GUI 에 인식된 함수가 export 에 누락될 수 있음 (예: `FUN_0008dcd8`). GUI 만 본 분석은 export grep 으로 검증 필요.
