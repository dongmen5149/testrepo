# Hero3 Ghidra — task[0xa848] sub-struct layout + FUN_85edc/85fc8 function pointer tables + FUN_818f0 letter input trigger (Round 48)

> **세션**: 2026-05-18, Round 48
> **이전 Round**: [ghidra-objectB-method60-and-task-a848-distribution-2026-05-17.md](ghidra-objectB-method60-and-task-a848-distribution-2026-05-17.md) (Round 47)
> **재현 도구**: `tools/recon/analyze_a848_proper_writes.py` (register tracking) / `tools/recon/extract_a848_fp_tables.py` / `tools/recon/analyze_818f0_letter_trigger.py` / `tools/recon/disasm_85edc_85fc8.py`

## 한 줄 요약

Round 47에서 task[0xa848] = "current screen/menu state" 중앙 필드 가설 확정. Round 48에서 **sub-struct field layout 추출** (≥0x5c bytes, +0x00/+0x01/+0x02/+0x04/+0x0c/+0x58) + **+0x01/+0x02 = function pointer table 인덱스** + **+0x0c = save/render 공유 sub-state** + **FUN_818f0 = 74-entity iteration loop** + **letter input trigger 조건** (context flag byte 비제로).

## 1. task[0xa848] sub-struct field layout

### 1.1 정정: BL FUN_85578c 후의 `str r2, [r3]` 패턴

Round 47 초기 분석에서 34 callers 의 BL 직후 패턴이 `str r2, [r3]` 로 보였음 (18 사이트). **정정**: r3는 사실 **로컬 stack frame pointer** (대개 r7-N), str은 &task[0xa848] 포인터를 로컬 변수에 저장하는 **prelude pattern**. 실제 task[0xa848] sub-field access는:

1. r0 = FUN_85578c() = &task[0xa848]
2. `adds r2, r0, #0` → r2 = &task[0xa848] (사본)
3. `str r2, [r7-N]` → 로컬 stack[-N] = &task[0xa848] (포인터 캐싱)
4. 이후 `adds r2, r7, #M; str r2, [r2]` 등에서 r2 가 재할당될 수 있음 → 실제 access 는 stack 에서 다시 로드한 후 일어남

따라서 **HIGH ENCAPSULATION + LOCAL CACHING pattern**: FUN_85578c는 단순 `&task[0xa848]` 게터이고, 대부분 callers는 포인터를 로컬에 stash한 뒤 함수 내내 multi-field deferred access 한다.

### 1.2 정확한 sub-struct field map

`tools/recon/analyze_a848_proper_writes.py` 의 register propagation tracker로 BL 후 32 instr 윈도우에서 r0/r2/r3 등 tracked register 의 immediate offset access만 집계:

| Offset | Type | R | W | Sites | 추정 의미 |
|---|---|---|---|---|---|
| **+0x00** | word | 1 | _ | 0x579b8 (LDR) | primary state (sister entry read) |
| **+0x01** | u8 | 2 | _ | 0x85f5c, 0x86016 (LDRB, sign-ext) | **sub-state byte index #1** (FP table 1 dispatch) |
| **+0x02** | u8 | 2 | 1 | 0x85f88, 0x85fea (R) + 0x862f4 (W) | **sub-state byte index #2** (FP table 2 dispatch) |
| **+0x04** | word | 1 | _ | 0x5706e (LDR r4) | secondary pointer field |
| **+0x0c** | word | 2 | 4 | 0x57040, 0x57084 (FUN_56f3c save/load), 0x575fc/57602/579a8/57bcc (FUN_57394 render) | **save+render 공유 sub-state** (rendering target?) |
| **+0x58** | word | 1 | _ | 0x85eba | sub-struct member at large offset |

**Struct 크기**: ≥0x5c bytes (0x58+4)

**Note**: 18 사이트가 7th indirect entry cluster (FUN_86058 영역, 0x85xxx-0x90xxx) 에 있으며 모두 `str r2, [r7-N]` 로 포인터를 로컬에 stash 후 deferred access 패턴. 즉시 access 패턴이 보이지 않아 본 분석에서는 cnt 0 이지만, 함수 본문 전반의 `ldr Rx, [r7-N]` 후 `ldr/str Ry, [Rx, #M]` 패턴까지 추적하면 추가 field 가 드러날 가능성 있음. Round 49 후속 작업.

### 1.3 +0x00 에 쓰여지는 값 추적 (정정 후)

기존 `str r2, [r3]` 18 사이트는 사실 stack store 였으므로 "state value = 1/0x10/0x14/...." 해석은 **잘못된 데이터** (실제로는 stack 오프셋). 정정된 직접 write 는 거의 없음. +0x00 은 1개의 read 만 확인됨.

## 2. task[0xa848]+0x01, +0x02 = function pointer table 인덱스

### 2.1 FUN_85edc (236B, 2 BL FUN_85578c)

```
; head: prologue, GOT setup, args r0/r1 to local
0x85ef6: bl context_getter      ; r0 → local[-0xc]
0x85f02: bl screen_ptr_getter   ; r0 → r2 = screen ptr
; 첫 graphics call (draw_rect-like)
0x85f0a-48: rect (r0=screen, r1=#?, r2=#?, r3=#0xb0, stack=#0xa0, ...)
0x85f4a: bl 0xa42a4             ; veneer call (likely draw_rect)

; byte1 dispatch
0x85f4e: ldr r3, [pc, #0x70]    ; r3 = literal 0xab4 (GOT offset)
0x85f50: add r3, sl              ; r3 = GOT + 0xab4 = 0xb36f4
0x85f52: ldr r3, [r3]            ; r3 = *0xb36f4 = 0xc1fa0 (FP table 1 base)
0x85f54: adds r4, r3, #0         ; r4 = FP table 1 base
0x85f56: bl FUN_85578c          ; r0 = &task[0xa848]
0x85f5c: ldrb r3, [r3, #1]      ; r3 = task[0xa848]+0x01 byte
0x85f5e-60: lsls/asrs (sign-ext to signed int)
0x85f62: lsls r3, r3, #2         ; r3 *= 4
0x85f64: adds r2, r3, r4         ; r2 = FP_table_1 + idx*4
0x85f70: ldr r2, [r2]            ; r2 = FP_table_1[idx] (function ptr)
0x85f72-74: adds r0=local[-4], r1=local[-8]
0x85f76: bl 0xa429c              ; veneer indirect call → FP_table_1[idx](r0, r1)

; byte2 dispatch (same pattern with +0x02 byte → FP table 2)
0x85f7a: ldr r3, [pc, #0x48]    ; literal 0xaec
0x85f80: adds r4, r3, #0         ; r4 = FP table 2 base (0xc1fe0)
0x85f82: bl FUN_85578c
0x85f88: ldrb r3, [r3, #2]      ; r3 = task[0xa848]+0x02 byte
0x85f8a-90: sign-ext + *4 + add → FP_table_2[idx2]
0x85fa2: bl 0xa429c              ; indirect call → FP_table_2[idx2](r0, r1)
```

**Pattern**: `func_table[task[0xa848].sub_byte](arg0, arg1)` — 2-단 sequential dispatch.

### 2.2 FUN_85fc8 (120B, 2 BL FUN_85578c)

```
; byte2 dispatch
0x85fdc: ldr r3, [pc, #0x58]    ; literal 0xaf4
0x85fe2: r4 = FP table 2' base (0xc1f60)
0x85fe4: bl FUN_85578c
0x85fea: ldrb r3, [r3, #2]      ; task[0xa848]+0x02
0x85fec-f0: sign-ext + *4 + add
0x85ffc: bl 0xa429c              ; FP_table_2'[idx2](r0)
0x86000-04: r3 = return; if (r3 == 0) skip;
0x86006: b 0x8602c               ; non-zero return → return early

; byte1 dispatch (only if byte2 dispatch returned 0)
0x86008: ldr r3, [pc, #0x30]    ; literal 0xabc
0x8600e: r4 = FP table 1' base (0xc1fc0)
0x86010: bl FUN_85578c
0x86016: ldrb r3, [r3, #1]      ; task[0xa848]+0x01
0x8601c-1e: sign-ext + *4 + add
0x86028: bl 0xa429c              ; FP_table_1'[idx1](r0)
0x8602c: epilogue
```

**Pattern**: 조건부 sub-state dispatch — byte2 path 가 truthy 반환하면 byte1 dispatch 스킵.

### 2.3 4개의 function pointer table 주소

| 함수 | byte | GOT offset | GOT 슬롯 | FP table base | 비고 |
|---|---|---|---|---|---|
| FUN_85edc | +0x01 | 0xab4 | 0xb36f4 | **0xc1fa0** | binary 외부 (GVM-injected) |
| FUN_85edc | +0x02 | 0xaec | 0xb372c | **0xc1fe0** | binary 외부 |
| FUN_85fc8 | +0x02 | 0xaf4 | 0xb3734 | **0xc1f60** | binary 외부 |
| FUN_85fc8 | +0x01 | 0xabc | 0xb36fc | **0xc1fc0** | binary 외부 |

**FP table cluster**: 0xc1f60-c1fe0 영역 (≥0x80 bytes spanning 4 tables, 각 ~0x20-0x40 bytes = 8-16 entries each).

**Binary 범위 (file 끝 0xb39d0)** 밖이므로 GVM firmware 가 런타임 주입하는 함수 포인터 테이블. 실제 dispatch target 함수는 binary 내부 코드일 것 (GVM 이 binary 코드의 일부를 가리키도록 셋업).

## 3. FUN_000818f0 letter input trigger context

### 3.1 entity iteration loop 구조

```
; 0x81920-22: r5 = r7 - 0xa (local slot)
; 0x81924-2a: 3개의 context_getter BL → r4, r3 등 context ptrs
; 0x8192c-44: context+pc-rel-offset 에서 byte 추출하여 local[-0xa]에 저장
;   - 0x81930: ldr r0, [pc, #0x380]  ; pc-rel literal (large offset → 외부 table)
;   - 0x81934: ldrb r3, [r3]
;   - 0x81938: asrs (sign-ext)
;   - 0x8193a: r3 += r4
;   - 0x8193c: ldr r1, [pc, #0x378]  ; 또 다른 pc-rel literal
;   - 0x8193e: r3 += r1
;   - 0x81940: ldrb r3, [r3, #2]
;   - 0x81942: strb r3, [r5]         ; local[-0xa] = byte from indexed table

; letter input GUARD
0x81944: bl 0x4ad10                  ; 3번째 context_getter
0x8194a: ldr r2, [pc, #0x370]
0x8194c: r3 += r2
0x8194e: ldrb r3, [r3]                ; r3 = context_flag_byte
0x81950: cmp r3, #0
0x81952: beq 0x81964                  ; flag == 0 → 스킵

; letter input CALL (조건 충족 시)
0x81954-58: r3 = local[-4] (현재 entity ptr); r0 = #2 (sub-mode); r1 = r3
0x8195c: bl FUN_3a86c                 ; letter input subsystem 호출!
0x81960: bl FUN_82df4                 ; post-call helper

; loop continuation
0x81964-78: r3 = local[-4] + 0x10 → local[-4] (entity ptr 증가, stride 0x10)
0x81972-7a: r1 = stack[-0x6c] (loop counter)
0x8197a: cmp r1, #0x49 (73)
0x8197c-7e: if r1 > 0x49 → bl 0x82df4 (escape)
0x81982-8a: r3 = loop counter
0x8198c-90: r3 = sl + literal[r3*4]    ; JT base + idx*4 = JT entry
0x81992: ldr r2, [r3]
0x81994-98: sl-rel adjust
0x8199a: mov pc, r3                    ; INDIRECT JT JUMP
```

### 3.2 핵심 finding

**FUN_000818f0 = 74-entity iteration loop**:
- 카운터 stack[-0x6c], 0..0x49 (74개)
- 각 entity stride 0x10 bytes (`adds r3, #0x10` at 0x81968)
- 각 entity 마다 context_getter 호출 후 일부 flag bytes 검사

**letter input trigger 조건**: 어떤 context byte (context + pc-rel literal offset) 가 비제로일 때, current entity 가 letter input subsystem 을 발동.

**호출 인자**:
- r0 = #2 (sub-mode, FUN_3a86c의 cmp #0xf range guard 안에서 의미 있는 값)
- r1 = current entity ptr (loop iterator의 stride 0x10 entity record)

**Post-call**: 0x81960 `bl FUN_82df4` — letter input 완료 후 entity state 정리 helper.

**Indirect JT @ 0x8198c-9a**: 루프 끝에서 sl-relative table 통해 분기 (sister loop iterator dispatch). 이는 entity update 가 sub-state 별 다른 처리 경로를 가짐을 시사.

Round 28에서 FUN_000818f0 을 "single-entity state handler"로 분류했었지만, **이번 분석으로 entity iteration loop의 BODY 임이 확정됨** (74-entity loop with stride 0x10 entity records).

## 4. FUN_3d5d0 sound dispatcher 정밀 (37 arms, Round 22의 22-arm 정정)

`disasm_subsystem_func.py 0x3d5d0 0x3e6bc` 결과:

- **37 cmp+branch arms** (Round 22의 "22 arms" 는 shallow scan; full disasm 으로 BST 내부 노드 포함 37개 식별)
- arm immediate distribution: 0x05(2x) / 0x06(1x) / 0x09(2x) / 0x0b(2x) / 0x0e(1x) / 0x0f(2x) / 0x10(2x) / 0x11(1x) / 0x13(2x) / 0x15(1x) / 0x16(1x) / 0x1e(2x) / 0x1f(3x) / 0x20(1x) / 0x65(2x) / 0x69(1x) / 0xba(2x) / 0xbf(2x) / 0xc3(3x) — **19 unique sound IDs**, range [0x05..0xc3] = [5..195]
- BST sparse dispatch pattern (3-way cmp/bgt/bls 트리)
- **21 sound_trigger BL** (모두 r0 indirect, dynamic sound_id)
- 17 helper_9fd64 BL (sound 파일 로딩/언로딩 후보)
- 22 context_getter BL (sound 상태 context 접근)

**Round 45 finding 재확인**: `internal_id = sound_id - 4`, range [4..195]. 본 라운드에서 정밀 arm count = 37 (BST 내부 노드 포함), unique sound IDs = 19개.

Sound dispatcher의 head 패턴 (0x3d5d0-0x3d61e):
1. push prologue + sp-=0x44 (큰 stack frame)
2. r0 (sound_id arg) 를 local[-4]에 stash
3. 2개의 16-bit 리터럴 (pc-rel) 을 local[-6], local[-8]에 strh (likely sound 설정값)
4. local[-0xc], local[-0x10], local[-0x18] 을 0으로 클리어
5. `bl 0x4ad10 (context_getter)` → sound context base
6. context_base + literal_offset + local[-4] (sound_id) 위치에 byte로 sound_id 기록 → **context 의 indexed slot 에 sound_id 마킹**

이는 sound dispatcher 가 단순 switch 가 아니라 **stateful context** (현재 재생 중인 sound 추적) 를 갖는 구조임을 시사.

## 5. FUN_57394 render command buffer 정밀 (3604B)

- **20 graphics_primitive BL** (가장 빈번한 외부 호출)
- **19 byte_append BL** with immediate distribution:
  - r0=#0x5: **6회** (sentinel/opcode prefix 후보 — 모든 byte_append 호출 쌍의 첫 번째)
  - r0=#0x14 / #0x3 / #0x3d / #0x40 / #0x3f: 각 1회 (varied opcodes/lengths)
  - r0=indirect: 6회
- **pair pattern**: `byte_append(#5); byte_append(#var)` — 5는 sentinel, 2nd 값은 op-specific (display list 2-byte encoding)

**task[0xa848]+0x0c 접근**:
- 0x575fc: `ldr r3, [r3, #0xc]` (READ)
- 0x57602: `str r3, [r2, #0xc]` (WRITE)
- 0x579a8: `str r3, [r2, #0xc]` (WRITE)
- 0x57bcc: `ldr r3, [r3, #0xc]` (READ)

총 2 READ + 2 WRITE 가 FUN_57394 내부에 있음. 추가로 FUN_56f3c (save/load, 832B)에도 task[0xa848]+0x0c READ/WRITE 가 있음 (0x57040, 0x57084).

### 5.1 task[0xa848]+0x0c = save+render 공유 sub-state

| Function | Site | Mnemonic | 의미 |
|---|---|---|---|
| FUN_56f3c (save/load) | 0x57040 | str | save 시 현재 render target 기록? |
| FUN_56f3c | 0x57084 | str | save 시 또 다른 render state 기록 |
| FUN_57394 (render) | 0x575fc | ldr | 현재 render target 읽기 |
| FUN_57394 | 0x57602 | str | render target 변경 |
| FUN_57394 | 0x579a8 | str | render target 변경 |
| FUN_57394 | 0x57bcc | ldr | render target 읽기 |

**+0x0c 의 의미**: save 와 render 가 동일하게 access 함으로써, 이 필드가 **"현재 rendering target / framebuffer index / display layer"** 같이 save 시 보존해야 하고 render 시 사용하는 값임이 강하게 시사됨.

## 6. 종합 — task[0xa848] = "session/UI context struct"

Round 47의 "current screen/menu state 중앙 필드" 가설이 Round 48 분석으로 더 구체화됨:

```c
struct SessionContext {  // located at task[0xa848], size ≥ 0x5c bytes
    /* +0x00 */ u32 primary_state;         // sister entry 가 read (1 site only)
    /* +0x01 */ u8  sub_state_idx_1;       // FP table 1 dispatch index (FUN_85edc/85fc8)
    /* +0x02 */ u8  sub_state_idx_2;       // FP table 2 dispatch index (FUN_85edc/85fc8)
    /* +0x03 */ u8  _pad;                  // unknown
    /* +0x04 */ void* secondary_ptr;       // FUN_56f3c 가 read
    /* +0x08 */ u32 _pad08;
    /* +0x0c */ u32 render_target_state;   // save (FUN_56f3c) + render (FUN_57394) 공유 ★
    /* +0x10..0x57 */ ... (unknown)
    /* +0x58 */ u32 sub_struct_member;     // 1 read at 0x85eba
    /* +0x5c.. */ ...
};
```

**4 function pointer tables**: byte index dispatch 통한 sub-handler 호출:
- FP_table_idx1 (0xc1fa0): byte1 -> handler[byte1]
- FP_table_idx2 (0xc1fe0): byte2 -> handler[byte2]
- FP_table_idx1' (0xc1fc0): byte1 -> handler' (FUN_85fc8 path)
- FP_table_idx2' (0xc1f60): byte2 -> handler' (FUN_85fc8 path)

전체 binary 외부 (GVM-injected). 이는 Round 31의 "task_struct GVM-injected" finding 과 일관됨.

## 7. 다음 라운드 후속 작업

1. **task[0xa848] full sub-field 추출**: 18 사이트의 deferred stack-cached access 패턴 추적 (`ldr Rx, [r7-N]; ldr Ry, [Rx, #M]`). Round 49 후속.
2. **4 FP tables의 entry 개수 결정**: byte index 범위 확인 → table size 추정.
3. **+0x0c (render+save state) 의 정확한 값 의미**: FUN_57394의 graphics_primitive 호출 인자로 흘러가는지 추적.
4. **FUN_000818f0 entity stride 0x10의 entity record 구조** (74-entity x 0x10 = 1168 bytes 영역).
5. **FUN_3a86c (letter input) 본문 분석**: r0 sub-mode (#2 from FUN_818f0) 의 의미.
6. **Sound dispatcher 21 leaf cases**: BST 흐름 따라가서 각 sound_id 값별로 어떤 sound_trigger 호출이 발동되는지 매핑.

## 부록 — 사용한 도구

- `tools/recon/analyze_a848_substruct.py` (1차 — BL 직후 8 instr only)
- `tools/recon/analyze_a848_state_values.py` (정정 전 — 잘못된 state 추출)
- `tools/recon/analyze_a848_litpool_states.py` (literal pool 디코드)
- `tools/recon/check_a848_litpool_targets.py` (literal target 의 실체 확인)
- `tools/recon/analyze_a848_call_context.py` (BL 컨텍스트 full disasm)
- `tools/recon/analyze_a848_proper_writes.py` (**정정본** — register propagation tracking)
- `tools/recon/analyze_818f0_letter_trigger.py` (FUN_818f0 letter input trigger)
- `tools/recon/disasm_85edc_85fc8.py` (FUN_85edc/85fc8 raw disasm)
- `tools/recon/extract_a848_fp_tables.py` (4 FP table addresses)
- 기존: `tools/recon/disasm_subsystem_func.py`, `tools/recon/analyze_sound_dispatcher.py`
