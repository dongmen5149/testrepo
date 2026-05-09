# §4.4 후속 — 2026-05-10 PM-2 세션 (mode 2 재분석 + default key handler + Ghidra PIC 실패 패턴 발견)

> 2026-05-10 AM-1 의 `state[0x94]` 재해석 후속.
> 자동 우선순위 **2F (mode 2 의 7KB literal pool 해석)** 와 **2G (battle 트리거 별도 추적)** 일괄 진행.
> 가장 큰 발견: **`state[0x94]=2` UI 함수는 9KB code (data 0%)** + **Ghidra 가 1470 함수 중 402 PIC 함수 디컴파일 실패** (~27%).

---

## 1. 2F 결과 — mode 2 (FUN_00060ab4) 정정

### 1A. 이전 가설 (2026-05-09 PM-3)

> "9KB 함수는 1.5KB 코드 + 7KB 임베디드 데이터 풀 (UI 레이아웃 추정)"

`tools/recon/disasm_mode2_fn.py` 가 **768 instr 에서 멈춤** → 잔여 7KB 를 데이터로 추정.

### 1B. 정정 — 9KB 가 100% 코드 ⭐

신규 도구 [`tools/recon/parse_mode2_ui_data.py`](../../tools/recon/parse_mode2_ui_data.py) 의 **auto-skip walker** 로 재분석:

```
=== FUN_00060ab4 (0x2268 bytes / 8.6 KB) ===
code_blocks: 3 (auto-detected)
  0x00060ab4 ~ 0x000610d4  (1568 bytes)
  0x000610d6 ~ 0x000623dc  (4870 bytes)
  0x000623de ~ 0x00062d1c  (2366 bytes)
data gaps: 2, total 4 bytes (0.0% of region)
```

- **8.6KB 중 100% 코드** — 이전 분석은 capstone 첫 실패 지점 (단순 alignment 2 byte) 에서 멈춰 잔여를 데이터로 오인
- 2 byte alignment 구간 2건 (0x610d4~0x610d6, 0x623dc~0x623de) — Thumb 정렬 패딩
- **"7KB literal pool = UI 레이아웃 데이터"** 가설은 **기각**

### 1C. 진짜 정체 — page 2 UI rendering function

| 통계 | 값 | 의미 |
|---|---|---|
| BL count | 54 (이전 16 → 정정) | 직접 함수 호출 |
| top BL `0x0000d53c` | 29x | screen ptr getter (FUN_0006619c 와 동일) |
| top BL `0x0009fd64` | 23x | (미식별, 자주 호출 helper) |
| top BL `0x0003ecfc` | 18x | sprite text drawing (dispatcher 2 와 공유) |
| top BL `0x000a42a4` | 17x | veneer (indirect call) |
| top BL `0x00099764` | 15x | sound trigger |
| PC-rel LDR | 207 sites | inline literal pool 다수 |
| cmp #imm 분포 | 거의 없음 (`0x0:4, 0x7:4, 0x3:3` 등) | switch 패턴 부재 |

→ **scene/UI 렌더링 함수**: drawText 18+ 회 + sound 15 회 + 화면 포인터 29 회. switch 부재 → **순차 실행 UI**.

### 1D. 부수 발견 — color/state field offsets

PC-rel LDR 의 207 literal 카테고리:

| 카테고리 | 개수 | 예시 |
|---|---|---|
| negative_signed_offset | 111 | `-280, -282, -288, -290, -296, -298` (state 구조체 음수 GOT-rel offset) |
| medium_int | 47 | `0x4d8, 0x4dc, 0x4e0, 0x4fc, 0x7ac, 0x7b0, 0x7b4, 0x7b8` (state 필드 offset) |
| got_slot_offset | 9 | `0x9c70, 0x9c71, 0x9c84, 0x9c85, 0x9e28, 0xa218, 0xa38c, 0xa3ac` (GOT 슬롯) |
| small_int | 24 | `0x1, 0x1e, 0x46, 0x8e` (count, flag) |
| 색상 상수 | 2 | `0x00ffffff` (white), `0x00fff000`, `0x00341708` (RGB888) |

state 필드 offsets 는 4 byte 간격 연속체 (`0x4d8/0x4dc/0x4e0`, `0x7ac/0x7b0/0x7b4/0x7b8`) → **per-page UI 상태 구조체** 의 인접 필드들.

---

## 2. 2G 결과 — `FUN_00064048` (default key handler) 분석

### 2A. Ghidra 의 misleading 디컴파일 ⚠

`all_decompiled.c` 23744:
```c
void FUN_00064048(void) {
  /* WARNING: Subroutine does not return */
  FUN_0004ad10();
}
```
→ 처음 보면 단순 stub.

### 2B. 실제 — 2KB PIC 함수

신규 도구 [`tools/recon/disasm_default_key_handler.py`](../../tools/recon/disasm_default_key_handler.py) capstone 분석:

```
=== FUN_00064048 (default key handler, 0x80a bytes / 2.0 KB) ===
code_blocks: 3, total decoded: 2054 bytes (99.8%)
  0x00064048 ~ 0x000643ac  ( 868 bytes)
  0x000643ae ~ 0x000643be  (  16 bytes)
  0x000643c0 ~ 0x00064852  (1170 bytes)
```

prologue (0x64048):
```
b0 b5 57 46  push {r4-r5, r7, lr}; mov r7, r10
80 b4 6f 46  push {r7}; mov r7, sp
8f b0 d6 4a  sub sp, #0x3c; ldr r2, [pc, #0x358]
92 46 fa 44  mov r10, r2; add r10, pc       ← GOT base setup
```

→ **진짜 PIC 함수** (60-byte stack frame + GOT base 셋업). Ghidra 분석 실패.

### 2C. 정체 — state machine 이 아님 ⚠

| 통계 | 값 | 결론 |
|---|---|---|
| BL count | 54 calls | 호출 많음 |
| top BL `0x0004ad10` | 29x | GOT context getter (PIC pattern) |
| top BL `0x0007e150` | 10x | **byte buffer append** (FUN_0007e150 디컴파일 확인) |
| top BL `0x00075b98` | 6x | (또 다른 stub-처럼-보이는 PIC 함수) |
| top BL `0x0007e890` | 4x | **ring buffer flush** (FUN_0007e890 디컴파일 확인) |
| top BL `0x0007e184` | 2x | **buffer memcpy read** |
| **cmp #imm 분포** | **7 distinct values, mostly == 0** | **state machine 아님** |

→ **double-buffer / ring-buffer 시스템에 byte 를 직렬화하는 함수**. 게임 상태 머신 분기 구조 부재.

### 2D. `FUN_0007e150 / FUN_0007e890 / FUN_0007e184` 발견

Ghidra 디컴파일에서 정확히 보임 — GVM SDK 의 **이벤트 큐 / 명령 직렬화 API**:

```c
// byte buffer append
void FUN_0007e150(byte b) {
  iVar2 = *(int *)**(int**)(GOT_xxx);  // 컨텍스트 버퍼
  sVar1 = *(short *)(iVar2 + 8);        // 현재 size
  *(short *)(iVar2 + 8) = sVar1 + 1;    // size++
  *(byte *)(iVar2 + sVar1 + 0xc) = b;   // 데이터에 byte 추가
}

// memcpy from buffer (deserialize N bytes)
undefined8 FUN_0007e184(uint *dst, uint n) {
  iVar1 = *(int *)**(int**)(GOT_xxx);
  uVar2 = thunk_FUN_0009f628((uint *)(iVar1 + *(short *)(iVar1 + 8) + 0xc), dst, n, 8);
  *(short *)(iVar1 + 8) += (short)n;
  return uVar2;
}

// ring buffer flush + swap
void FUN_0007e890(void) {
  // 현재 버퍼를 cyclic slot 에 저장 → 새 버퍼 할당 → swap → cleanup
}
```

**구조체 layout**: `[+0:status, +1:idx_mod_4, +8:size, +0xc:data...]`

→ event queue / command stream / save serializer 중 하나. 정확한 용도는 호출 컨텍스트로 추가 식별 필요.

### 2E. 결론 — `FUN_00064048` 은 battle trigger 도 state machine 도 아님

- **state[0x460] / state[0x9c] 등에 직접 접근 안 함** (state 읽기 +0x1c4/+0x1c0/+0x0a0 등 다른 offset)
- **switch / dispatcher 패턴 부재**
- 호출 패턴은 **이벤트 큐 직렬화** 형태

→ default 키 처리 = "키 이벤트를 큐에 직렬화" 가능성. 진짜 게임 로직은 **다른 frame callback** 에서 큐를 dequeue 처리.

---

## 3. `state[0x460]` 의 진짜 정체 — UI selection highlight ⭐

`state[0x460]` 가 battle trigger 라는 가설로 grep:

```c
// FUN_000729d4 @ 0x729d4 (그리고 비슷한 8개+ 함수)
puVar1 = FUN_0000d53c();   // screen ptr
if (state[0x460] != 0) {
  FUN_0000defc(screen, 0, 0, state[0x70], state[0x74], 0x78, 0, 0, 0);
  // ↑ draw highlight rect at (state[0x70], state[0x74]) size 0x78 (120px wide)
}
FUN_0003ecfc(screen, string_ptr, x+y+1, font, 10, 1, 1);  // draw text
```

- `state[0x460]` **셋되면 highlight 사각형 그림** + **셋 안되면 텍스트만 그림**
- → **메뉴 항목의 "현재 선택됨" 플래그**
- → **battle 트리거 아님**

→ FUN_00070f34 의 `if (state[0x94]==1 && key=='*') { state[0x9c]=0xc; state[0x460]=1; }` 는:
- "page 1 (menu/dialog 페이지) 에서 '*' 키 → 9c 슬롯에 12 셋 + 메뉴 highlight 활성화"
- 즉 **메뉴 선택 인터랙션** 일 뿐.

---

## 4. **402 PIC 함수 Ghidra 분석 실패** ⭐⭐ — 근본 원인 발견

### 4A. 패턴

`all_decompiled.c` 에서 다음 패턴이 **402 함수** 에 등장:

```c
void FUN_xxxxxxxx(void) {
  /* WARNING: Subroutine does not return */
  FUN_0004ad10();
}
```

`FUN_0004ad10` 자체는:
```c
undefined4 FUN_0004ad10(void) {
  return *(undefined4 *)(DAT_0004ad30 + DAT_0004ad2c + 0x4ad22);  // GOT context getter
}
```

### 4B. 의미

- 1470 함수 중 **402 (~27%)** 가 Ghidra 자동 분석에서 본문 추출 실패
- 모두 PIC 패턴 (GOT base 셋업 + 음수 offset literal pool)
- Ghidra 가 prologue 만 인식하고 **control flow 추적 실패** → "Subroutine does not return" 마크 + 단일 stub 호출로 디컴파일

### 4C. 영향 범위

자동 분석 ceiling 의 **진짜 원인**:
- 이전 4 세션 (2026-05-08 ~ 05-10) 동안 "PIC indirect call 추적 한계" 라고 정리해 왔으나, 실제는 **27% 함수 본문이 자동 분석에 보이지 않음**
- `all_decompiled.c` grep 만으로는 이 함수들의 호출/state-access 패턴을 못 봄
- 본 세션에서 발견한 `FUN_00060ab4` (mode 2) 와 `FUN_00064048` (default key) 는 **둘 다 이 402 안에 포함**

### 4D. 향후 분석 권장 패턴

본 세션의 walker 패턴이 **표준 분석 도구**:

```python
def walk_with_skip(data, start, end):
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    instrs, blocks = [], []
    pos = start
    while pos < end:
        chunk = data[pos:end]
        block_first, last_addr, any_emitted = pos, pos, False
        for ins in md.disasm(chunk, pos):
            instrs.append({"addr": ins.address, "mnem": ins.mnemonic, "op_str": ins.op_str, "size": ins.size})
            last_addr = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            blocks.append((block_first, last_addr))
            pos = last_addr
        pos += 2  # ← Thumb alignment skip
        if pos > end: break
    return instrs, blocks
```

- 단일 capstone disasm() 의 멈춤은 거의 항상 **alignment** 이슈 — 2 byte 건너뛰면 다시 진행
- 진짜 데이터 풀은 별도 휴리스틱 필요 (PC-rel LDR target → literal area 식별)

---

## 5. 신규 도구 / 산출물

| 도구 | 산출물 | 용도 |
|---|---|---|
| [parse_mode2_ui_data.py](../../tools/recon/parse_mode2_ui_data.py) | `work/h3/mode2_ui_data.json` | mode 2 (FUN_00060ab4) auto-skip 디스어셈블 + literal 카테고리화 |
| [disasm_default_key_handler.py](../../tools/recon/disasm_default_key_handler.py) | `work/h3/default_key_handler.json` | FUN_00064048 디스어셈블 + state offset 추출 |

도구 두 개 모두 **walk_with_skip 패턴 + literal categorization** 을 사용. 향후 다른 402 함수 분석 시 재사용 가능.

---

## 6. PROGRESS.md 갱신 — 정정 사항 일괄

| 기존 가설 (PROGRESS / 이전 docs) | 2026-05-10 PM-2 평가 |
|---|---|
| mode 2 (FUN_00060ab4) = 1.5KB code + 7KB embedded data | ❌ **기각**. 8.6KB 100% code |
| mode 2 의 7KB literal pool = page 2 UI 레이아웃 데이터 | ❌ **기각**. literal pool 은 inline (각 PC-rel LDR 의 작은 풀) |
| FUN_00064048 (default key handler) = 게임 상태 머신 본체 후보 | ❌ **기각**. cmp 분포 부재 + ring buffer 직렬화 패턴 |
| state[0x460] = battle trigger flag 후보 | ❌ **기각**. UI menu item 선택 highlight 플래그 |
| state[0x94] mode 분기 가설 (NPC/menu/battle) | ❌ 이미 2026-05-10 AM 에 기각 (3-페이지 UI 탭) |

새로 확정:
- ✅ mode 2 (FUN_00060ab4) = page 2 UI rendering function (8.6KB, 54 BL, drawText 18x + sound 15x)
- ✅ FUN_00064048 = byte 큐 직렬화 함수 (이벤트 큐 / save / 명령 큐 중 하나)
- ✅ state[0x460] = menu highlight flag (켜지면 0x78 너비 highlight rect 그림)
- ✅ FUN_0007e150/0x7e184/0x7e890 = GVM SDK 의 ring-buffer 이벤트 큐 API
- ⭐ Ghidra 가 **402 PIC 함수 디컴파일 실패** — 자동 분석 ceiling 의 진짜 원인

---

## 7. 다음 세션 권장

자동 진척 가능:
- ⭐ **402 stub 함수 우선순위 분류** — 사이즈 / BL count / 호출 빈도 등으로 ranking
- ⭐ **FUN_0007e150 큐의 producer/consumer 매핑** — 누가 큐에 쓰고 누가 읽는지 → 게임 로직 진입점 후보
- battle trigger 별도 추적 — `state[0x94]` 외 다른 page state field (예 0x60, 0x7c) 추적 + scn opcode 별 실제 핸들러 함수

사용자 블로커 (게임 체감 영향 큼):
- SMAF→OGG 변환 (33개 BGM/SFX)
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 8. 핵심 교훈

1. **Ghidra 디컴파일을 그대로 믿지 말 것**: "Subroutine does not return" + 단일 호출 = PIC 분석 실패 신호. 진짜 함수 크기는 raw bytes / 다음 함수 entry 까지 거리로 확인.
2. **capstone walk_with_skip 패턴 표준화**: 첫 실패 지점에서 단순히 2 byte 건너뛰면 거의 항상 알라인먼트 이슈. data gap 으로 잘못 결론 짓지 말 것.
3. **가설 정정의 가치**: 2026-05-09 PM-3 의 "7KB literal pool = UI 데이터" 가설은 한 세션 만에 정정. 빠른 검증으로 분석 효율 유지.
4. **stub 패턴은 시스템적 문제**: 단일 함수 (FUN_00064048) 의 stub-처럼-보임 → 같은 패턴이 402 곳에 → 진짜는 Ghidra 의 PIC 처리 한계. 단일 함수 트러블슈팅보다 패턴 인식이 더 가치.
