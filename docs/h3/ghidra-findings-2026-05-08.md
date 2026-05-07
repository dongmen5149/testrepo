# Ghidra GUI 세션 결과 — 2026-05-08

> §4.4 _scn opcode dispatcher 추적 시도. dispatcher 못 찾았으나 **§4.3 cif animation 거의 완전 해독** + §4.1 후속 단서 확보.

---

## 핵심 발견 — §4.3 Boss/Enemy cif Decoder

### `FUN_00098ef8 @ 0x98ef8` — Boss/Enemy cif cell decoder

```c
void FUN_00098ef8(int slot_ctx, int param_2, char anim_id, char frame_id, short *cell_idx_ptr)
{
  // 1. Initialize buffers (param_1 + 0x1c, +0x24)
  *(int *)(param_1 + 0x1c) = **(int **)(param_1 + 0x18) + 8;
  iVar2 = FUN_0009889c(param_1, anim_id, frame_id);  // frame data getter
  if (frame_id < 0) FUN_0009975a();

  // 2. Bound check cell_idx
  if (((int)(char)iVar2 < (int)*cell_idx_ptr) || (*cell_idx_ptr < 0)) {
    *cell_idx_ptr = (short)DAT_00098fa8;
  }

  // 3. 3D index: anim_id × frame_id × cell_idx → cell offset
  // stride: anim 0x4b8 (1208), frame 0x32 (50), cell 4 byte
  iVar2 = *(int *)((frame_id * 0x32 + (int)*cell_idx_ptr) * 4 + anim_id * 0x4b8 + ... + 8);

  // 4. Skip 0x7f sentinel cells (4-byte stride)
  while (true) {
    if (max_cells <= local_34) { FUN_0009975a(); return; }
    bVar1 = *(byte *)(local_2c + ...);
    if (bVar1 != 0x7f) break;
    local_2c = local_2c + 4;
    local_34 = local_34 + 1;
  }

  // 5. Decode cell flag byte
  bVar3 = bVar1 >> 5 & 3;        // bits 5-6: orientation? (0/1/2)
  local_47 = bVar1 & 0x1f;       // bits 0-4: cell ref / type (5 bits)
  if (in_stack_00000010 != 0) {  // alt mode
    if (local_47 == 4) local_47 = 8;
    else if (local_47 == 5) local_47 = 9;
  }
  if ((bVar1 & 0x80) != 0) FUN_0004ad10();  // bit 7: special flag

  // 6. dispatch to render based on local_47
  if (local_47 == 6) FUN_0004ad10();
  if (local_47 == 7) FUN_0004ad10();
  if (local_58 == 0) FUN_0004ad10();
  FUN_0004ad10();  // tail call (Ghidra noreturn 분류)
}
```

### 매핑된 boss/enemy cif 포맷 가설

기존 PROGRESS.md §4.3 의 미해독:
> "boss0=`7f00ffff` sentinel(229회), e000=17byte stride, e001=`8000` sentinel"

이번 세션으로 확정:

| 포맷 | 셀 stride | sentinel | 디코더 함수 |
|---|---|---|---|
| **boss/enemy cif** (e000/e001 등) | **4 byte** | `0x7f` | `FUN_00098ef8 @ 0x98ef8` |
| **셀 byte 구조** | `[cell_byte (1B), data×3 (3B)]` | sentinel cell = `7f ?? ?? ??` (skip) |
| **non-sentinel cell byte 분해** | `bit 7` = special flag (abort) <br> `bits 5-6` = orientation 0/1/2 <br> `bits 0-4` = cell ref / type | |

→ `tools/converter/bake_hero_walkcycle.py` 의 `find_frames` heuristic 을 hero 외 (boss/enemy) 에 적용할 때, `0x7f` sentinel skip + 4-byte stride 적용 가능.

### ⚠️ 2026-05-08 추가 검증: boss decoder 는 h4-h11 walk-cycle 에 적용 불가

가설: "h4-h11 broken bake 도 boss-style 0x7f sentinel decoder 로 해결 가능"
→ **검증 결과 가설 빗나감**:

```
h0:  0x7f count = 0
h4:  0x7f count = 3   (sentinel 으로 안 쓰임)
h5:  0x7f count = 0
h6:  0x7f count = 0
h7:  0x7f count = 0
h8:  0x7f count = 0
h9:  0x7f count = 15  (분포 보고 sentinel 가능성 점검 필요)
h10: 0x7f count = 0
h11: 0x7f count = 0
```

대신 발견한 것: **h0 vs h4-h11 walk-cycle 구조 자체 가 다름**:
- h0: 4 group × 8 frame 동일-lead 구조 (`0a020b`×8, `0a0501`×8, `0a0208`×8, `0a2208`×8)
- h4-h11: 4-5 frame 짧은 그룹들 흩어짐, 동일-lead 8 frame 그룹 0건

→ h4-h11 walk-cycle 인코딩 미해독. cif 헤더 또는 외부 인덱스 분석 필요.

조치: `bake_hero_walkcycle.py` 에 `has_h0_walkcycle_structure()` check 추가. h4-h11 자동 skip → broken PNG 생성 방지. 단위 테스트 3건 추가 ([test_analyze_cif.py](../../tools/recon/test_analyze_cif.py)).

### Helper 함수

- **`FUN_0009889c`** — animation slot 데이터 getter (anim_id, frame_id 입력, frame_count + data ptr 반환). `param_1 + 0x4b8 * anim_id` 같은 인덱싱 헬퍼.
- **`FUN_0004ad10`** — Ghidra noreturn 분류 (실제로는 tail-call 또는 panic). 분기 끝마다 호출됨.

### 사용처 (4 callers, 모두 렌더링)

| 주소 | 정체 |
|---|---|
| `0x33016` | UI/menu drawer (status 화면, 캐릭터 + 3 item list 그림) |
| `0x410b0` | sprite drawer wrapper (단일 호출) |
| `0x41172` | **animation frame stepper / tick handler** — `frame_idx++` 매 tick, `frame_count` 와 비교 wrap |
| `0x4ac40` | virtual method dispatch + draw |

### `UndefinedFunction_00041172` — Animation Tick Handler 발췌

```c
do {
  cVar5 = *(char *)(iVar4 + DAT_0004138c + 1);
  if (-1 < cVar5) {
    ...
    bVar1 = *(byte *)(iVar8 + DAT_00041390 + 3);     // 현재 frame_idx
    *(byte *)(iVar8 + DAT_00041390 + 3) = bVar1 + 1; // ++
    iVar3 = FUN_0009889c(slot, anim_id, frame_id);   // 다음 frame 데이터
    if (frame_count_check == 0) {
      FUN_000a42a0();    // wrap to 0 (반복 애니메이션)
      // 또는 *(byte *)(iVar7 + 3) = 0;  (one-shot)
    }
  }
  iStack00000014++;
  pcVar6++;
} while (iStack00000014 < frame_count);
```

→ §4.3 의 timing 데이터 (`frame_count` 와 `frame_idx` per slot) 가 어떻게 동작하는지 확정.

---

## 부수 발견 — §4.1 후속 (HD blender)

### `FUN_00014e68` — HD/Blending sprite drawer

```c
if (uVar5 == 0xb) { uVar14 = FUN_00015b8c(...); }   // BM type 0x0b (4-bit) drawer
if (uVar5 == 0xc) {
  if (iVar4 == 1) iVar4 = FUN_00015a2c();
  if (iVar4 == 2) iVar4 = FUN_000158c6();
  if (iVar4 == 3) {
    // RGB565 mask + palette double lookup
    uVar9 = palette[*pixel];
    iVar7 = (palette[*pixel] & 0xf800) >> 0xb;       // R5
    *(int *)... = (palette[*pixel] & 0x3e0) >> 5;    // G5 (오 5 bits만 사용)
    uVar5 = (palette[*pixel] & 0xf) << 1 |           // B5 (재배치)
            (palette[*pixel] & 0x20000) >> 0x11;     // alpha bit?
    // 두 번째 palette lookup (HD up-scale)
    if (color_mode < 0xff) {
      iVar4 = DAT_00015a28;       // HD palette
      uVar10 = palette2[lookup1];
      uVar11 = palette2[lookup2];
      uVar9  = palette2[lookup3];
    }
    *puVar8 = (uVar10 & 0x1f) << 0xb |
              (uVar11 & 0x1f) << 5 |
              (uVar9 & 0x1e) >> 1 |
              (uVar9 & 1) << 0x11;
  }
  if (iVar4 == 4) { ... }
}
```

핵심:
- BM type byte (0x0b/0x0c) 분기 — `FUN_00010fe4` 와 같은 진입
- transformation mode (0~7+) — sprite 회전/플립 8가지 → FUN_0001a568 / FUN_00015a2c / FUN_000158c6 등 변환 sub
- **palette 2회 lookup** (RGB565 → 인덱스 → RGB565 다시) — HD upscale 또는 dynamic palette swap (캐릭터 색 변환?)
- alpha bit (`0x20000`) 재배치 — non-standard RGB565 (RGBA 16+ 비트?)

→ §4.1 의 BM 디코더 (`FUN_00010fe4`) 와 별개의 **HD/blending pipeline**. 추후 sprites_hd 자동 생성 도구 만들 때 이 함수 알고리즘 이식 가능.

### Helper 함수

- **`FUN_00015b8c`** — BM type 0x0b (4-bit dense) 의 transform-aware drawer
- **`FUN_000182c4`** — sprite transform/rotation sub (FUN_00015b8c 가 호출)
- **`FUN_00015a2c`, `FUN_000158c6`** — transformation mode 1/2 의 변환 함수 (회전/플립)
- **`FUN_0001a568`** — sprite rotation degree dispatcher (`0x5a=90°`, `0xb4=180°`, `0x10e=270°`)

---

## §4.4 _scn opcode dispatcher — 미해결

### 시도한 접근 + 결과

1. **디버그 문자열 xref** (`onEventMessageOkKey @ 0xa6888`) — 0건 (PIC + GOT indirection)
2. **다른 단서 문자열** (`eventManager`, `Event_freeID`, `loadDataID`) — 모두 References 0건
3. **`all_decompiled.c` 패턴 grep** — 5개 후보 추렸으나 모두 dispatcher 가 아닌 sprite/UI 류:
   - FUN_000182c4 → sprite transform sub
   - FUN_000186c8 → references 0건
   - FUN_00098ef8 → **boss decoder** (§4.3 unblocking)
   - FUN_00014e68 → **HD blender** (§4.1 후속)
4. **boss decoder caller 4개** — 모두 렌더링 (UI drawer, sprite wrapper, animation tick, virtual draw)

### 근본 원인

"작은 정수 다중 비교 + while 루프" 패턴이:
- BM type byte (0x0b/0x0c) 분기
- transformation mode (0~7) 분기
- UI item index (0~3) 루프
- animation frame index 증가

→ 모두 동일한 패턴. grep 만으로 dispatcher 와 decoder/drawer 구분 불가능.

§4.1 풀 때 운 좋게 `& 0x3f` (RGB565 G mask) 라는 **dispatcher 와 무관한 표지** 가 있었음. §4.4 는 그런 표지가 없음.

### 다음 시도 방향 (다음 세션)

1. **caller chain 거꾸로** — main loop / event pump 에서 시작해 좁힘
   - `Window → Function Call Trees` 사용
   - `_start` 또는 main 함수에서 출발 → reachable functions 그래프
2. ~~Ghidra Script `FindOpcodeDispatch.java` 헤드리스~~ — ❌ Hero5 전용 (Event_* symbol 가정), Hero3 에 미적용
3. **_scn 통계 기반** — `analyze_scn_segments.py` 의 가장 흔한 byte 와 `cmp r0, #0xXX` 패턴 매칭
4. **간접 진입** — §4.2 _mp loader (`loadDataID @ 0xa6efc`) 가 _scn 도 같이 로드할 가능성. _scn 로더 함수 잡으면 그 caller 가 dispatcher 호출자

### 2026-05-08 추가 시도 (자동 식별)

`all_decompiled.c` 에서 Python heuristic 강화 시도:
- Renderer 강 필터링 (RGB565 mask 0xf800/0x7e0/0x3e0 등)
- byte read 빈도 + 평균 callee size + opcode-like comparisons
- UNRECOVERED_JUMPTABLE 분석 — 355 함수 산재, 식별 단서 X (ARM 일반 패턴)

**최강 후보 도달**: `FUN_00019b5a` — 39 byte-reads, 11 opcodes, avg callee 269 chars. 검증 결과 **또 sprite drawer** (4-bit type 0x0b, transformation mode 0~7).

→ **결론**: Hero3 binary 는 sprite engine 코드가 dominant. _scn dispatcher 는 자동 식별 불가능 확정. GUI 인터랙티브 caller-chain 분석 외 답 없음.

---

## 액션 — 코드/문서 반영

### 즉시 가능 (이번 세션 후속)

1. **§4.3 boss/enemy cif decoder 도구** 작성:
   ```python
   # tools/converter/bake_boss_cif.py 신규
   # - 0x7f sentinel skip + 4-byte stride
   # - cell byte 분해 (>>5&3 orientation, &0x1f cell_ref, &0x80 special)
   # - h4-h11 broken bake 의 추가 액션 frame 도 시도 가능 (frame group lead 가 다름)
   ```
2. **PROGRESS.md §4.3 업데이트** — boss/enemy decoder 진입점 확정 표시
3. **`tools/recon/analyze_cif.py`** 에 boss/enemy 모드 추가 (sentinel 0x7f 인식)

### 다음 세션

1. §4.4 새 접근 시도 (위 다음 시도 방향 4가지 중 1~2개)
2. h4-h11 boss-style decoder 적용 후 walk-cycle 재베이크 시도

---

## 함수 정리 표 (참고용)

| 주소 | 정체 | §섹션 |
|---|---|---|
| `0x10ea4` | BM mini-header parser | §4.1 ✅ |
| `0x10fe4` | BM 0x0c/0x0b dense palette decoder | §4.1 ✅ |
| `0x14e68` | **HD/blending sprite drawer** | §4.1 후속 ⭐ |
| `0x158c6` | sprite transform mode 2 | §4.1 후속 |
| `0x15a2c` | sprite transform mode 1 | §4.1 후속 |
| `0x15b8c` | BM 0x0b transform-aware drawer | §4.1 후속 |
| `0x182c4` | sprite transform sub | §4.1 후속 |
| `0x1a568` | sprite rotation dispatcher (90/180/270°) | §4.1 후속 |
| `0x33016` | UI menu drawer (calls boss decoder) | renderer |
| `0x410b0` | sprite drawer wrapper | renderer |
| `0x41172` | **animation tick handler** (frame_idx++) | §4.3 ⭐ |
| `0x4ac40` | virtual draw + boss decoder | renderer |
| `0x9889c` | animation slot data getter | §4.3 ⭐ |
| `0x98ef8` | **boss/enemy cif cell decoder** | §4.3 ⭐⭐ (핵심) |
| `0x4ad10` | tail-call panic (Ghidra noreturn) | runtime |
| `0xa6888` | `onEventMessageOkKey()` 디버그 문자열 | §4.4 진입점 (xref 0건) |
| `0xa6ad8` | `eventManager` 디버그 문자열 | §4.4 진입점 (xref 0건) |

⭐ = 이번 세션 발견. ✅ = 이전 세션 (2026-05-06).
