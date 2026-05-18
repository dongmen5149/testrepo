# Hero3 Ghidra — FUN_9a008 = 7-mode script bytecode interpreter + MD5 algorithm for save record verification (Round 53)

> **세션**: 2026-05-18, Round 53
> **이전 Round**: [ghidra-818f0-leaves-and-record-comparator-2026-05-18.md](ghidra-818f0-leaves-and-record-comparator-2026-05-18.md) (Round 52)
> **재현 도구**: `tools/recon/decode_9a008_nested_jts.py` / `dump_9a008_jt1_leaves.py` / `disasm_save_load_helpers.py` / `disasm_439a0_dominant_helper.py`

## 한 줄 요약

Round 52 의 "FUN_9a008 = sparse state machine" 가설을 정정 + 확장. **FUN_9a008 = 7-mode script bytecode interpreter** — 7개 mode 마다 mode-specific sub-JT (size 0xf/0x10/0x11/0xd/0x1e/0xd/0xb, 합 = **122 sub-opcodes**). MD5 알고리즘이 binary 에 존재 — **FUN_5613c (Init) / FUN_56164 (Update) / FUN_561dc (Final) / FUN_5610c (wrapper)** — magic constants 0x67452301/0xefcdab89/0x98badcfe/0x10325476 발견. **FUN_77c78 정정 = MD5-verified save record reader** (R52 의 "name compare" → "16-byte digest compare"). **FUN_99a9c = ObjectB storage iterator** (vtable[+0x7c] size + vtable[+0x80] read). **ObjectB methods 12 → 14**. **FUN_439a0 = script opcode dispatcher** (task[+0x9bb4] bit flags + task[+0x9cbc] callback queue + task[+0x29e] interpreter flag).

## 1. FUN_9a008 = 7-mode script bytecode interpreter (2TA)

`tools/recon/decode_9a008_nested_jts.py` + `dump_9a008_jt1_leaves.py` 결과:

### 1.1 JT_1 — outer dispatcher (7 entries, cmp #6)

```
JT_1 base @ 0xacbd0 (= sl + 0xffff9f90), 7 entries, self-relative pattern
```

| idx | leaf addr | first 10 inst pattern |
|---|---|---|
| 0 | 0x9a056 | (special: contains JT_2 prologue dispatch) |
| 1 | 0x9a556 | common setup + sub-JT (cmp #0x10, 17 entries) @ 0xffffa000 |
| 2 | 0x9aabe | common setup + sub-JT (cmp #0x11, 18 entries) @ 0xffffa0c8 |
| 3 | 0x9b258 | common setup + sub-JT (cmp #0xd, 14 entries) @ 0xffffa318 |
| 4 | 0x9b7e6 | common setup + sub-JT (cmp #0x1e, 31 entries) @ 0xffffa3ec ★ largest |
| 5 | 0x9bce6 | common setup + sub-JT (cmp #0xd, 14 entries) @ 0xffffa490 |
| 6 | 0x9bfc8 | common setup + sub-JT (cmp #0xb, 12 entries) @ 0xffffa4c8 |

각 leaf 의 공통 setup pattern:
```c
ptr1 = *r0;                                       // (sp[0x38] = first arg)
sub_obj = ptr1 + (sp[0xc] >> 0x15);               // arithmetic offset
inner = sub_obj[+0x10];                            // chained deref
script_state = *inner;                             // bytecode state struct
*script_state[+0xc] = *(script_state[+8]) + 8;    // ★ advance instruction pointer by 8
```

The `inner[+8] = ip_ptr; inner[+0xc] = next_ip_target; *ip_ptr += 8` pattern = **PC advance in a bytecode VM** (each instruction = 8 bytes).

### 1.2 JT_2 — inner sub-JT in JT_1[0] (16 entries, cmp #0xf)

```
JT_2 base @ 0xacbec (= sl + 0xffff9fac), 16 entries
```

| idx | leaf addr | 비고 |
|---|---|---|
| 0, 1 | 0x9a07e | default/exit path (epilogue at 0x9a07e: `add sp, #0x44; pop`) |
| 2, 3 | 0x9a076 | early-state path |
| 4 | 0x9a0dc | |
| 5, 6 | 0x9a11e | |
| 7 | 0x9a154 | |
| 8 | 0x9a196 | |
| 9 | 0x9a1d8 | |
| 10 | 0x9a290 | |
| 11, 12 | 0x9a35c | |
| 13 | 0x9a436 | |
| 14 | 0x9a49e | |
| 15 | 0x9a4fa | |

→ 16 entries, **12 distinct targets** (4 paired/shared).

### 1.3 전체 opcode count

| mode (JT_1 idx) | sub-JT size | leaves dispatched |
|---|---|---|
| 0 | 16 (cmp #0xf) | 12 distinct |
| 1 | 17 (cmp #0x10) | ~13 distinct (추정) |
| 2 | 18 (cmp #0x11) | ~14 distinct (추정) |
| 3 | 14 (cmp #0xd) | ~10 distinct (추정) |
| 4 | 31 (cmp #0x1e) | ~20-30 distinct (추정) ★ |
| 5 | 14 (cmp #0xd) | ~10 distinct (추정) |
| 6 | 12 (cmp #0xb) | ~10 distinct (추정) |
| **총합** | **122 sub-opcode slots** | **추정 ~80-100 unique leaf handlers** |

→ **NOT a sparse state machine** (R52 가설 정정). FUN_9a008 = **multi-mode script bytecode interpreter**. Round 35 의 16.3KB FUN_8e89e SCN bytecode interpreter (62 cmp + 121 BL) 보다 **mode 수가 많고 opcode density 가 낮은 별도 interpreter**.

### 1.4 정체 가설

함수 args (5개):
- r0 (sp[0x38]) = "interpreter context" ptr (NPC/scene script state)
- r1 (sp[0x34]) = opcode array ptr
- r2 (byte) = primary index (s8, -4..+10 effective range)
- r3 (byte) = secondary state byte
- sp[0x60] (byte) = tertiary state byte

`r1[r2]` = sbyte opcode (값 - 4 = mode key for JT_1, ∈ [0..6]).

mode 4 가 31 entries 로 가장 크므로 **default/main script mode** 일 가능성. mode 0 이 별도 처리 (JT_2 prologue 진입 → mode 0 = "in-place sub-dispatch") = **special initialization mode**.

호출자: **Round 14의 NPC table query (FUN_25f30) 와 같은 NPC 시스템 경로에서 호출** 가능성. arg=-5 letter input mode 4 (`task[+0xac78] = 3` state) 의 후속 처리에서 FUN_9a008 호출 trail 검증 필요 (Round 54 작업).

**원래 R52의 "전투 시스템 후보" 가설 폐기**. FUN_9a008 = **NPC/scene script interpreter** (R35 의 SCN 과 별개의 두 번째 script 시스템). 진짜 전투 시스템 위치 **여전히 미확정** — 별도 검색 필요.

## 2. MD5 알고리즘 in Hero3 (2TB+2TC)

**핵심 발견**: `tools/recon/disasm_save_load_helpers.py` 의 FUN_5613c (76B 짜리 짧은 함수) literal pool 에:

```
0x56154: LIT 0x67452301
0x56158: LIT 0xefcdab89
0x5615c: LIT 0x98badcfe
0x56160: LIT 0x10325476
```

→ **MD5 magic constants (A, B, C, D)** 정확히 일치. (RFC 1321 §3.3 Step 3)

### 2.1 MD5 함수 trio + wrapper

```c
// FUN_5613c (76B): MD5_Init
void MD5_Init(MD5_CTX* ctx) {                          // ctx 0x14B layout: [count_lo, count_hi, A, B, C, D]
    ctx->count[0] = 0;                                  // [0x10]
    ctx->count[1] = 0;                                  // [0x14]
    ctx->state[0] = 0x67452301;                         // [0x00] A
    ctx->state[1] = 0xefcdab89;                         // [0x04] B
    ctx->state[2] = 0x98badcfe;                         // [0x08] C
    ctx->state[3] = 0x10325476;                         // [0x0c] D
}

// FUN_56164: MD5_Update (called with ctx, data, len)
// FUN_561dc: MD5_Final (called with out16, ctx)

// FUN_5610c (88B): MD5 wrapper
void md5(void* data /*r0*/, int len /*r1*/, uint8_t* out16 /*r2*/) {
    MD5_CTX ctx;                                        // 0x58B stack
    MD5_Init(&ctx);
    MD5_Update(&ctx, data, len);
    MD5_Final(out16, &ctx);
}
```

### 2.2 FUN_77c78 정정 — MD5-verified save record reader

R52 의 "16-byte name compare" 해석 → **16-byte MD5 digest compare** (정정):

```c
ObjectB* FUN_77c78(int record_handle /*r0*/) {
    FUN_4ad10();                                          // task (unused)
    ObjectB_master = *GOT[+0x18];

    uint8_t* digest_a = ObjectB_master.vtable[+0x54](0x10);  // 16B output for MD5
    if (!digest_a) return NULL;

    int actual_size;
    void* record = FUN_99a9c(record_handle, &actual_size);
    if (!record) {
        ObjectB_master.vtable[+0x58](NULL);                  // no-op destroy
        return NULL;
    }

    int payload_size = actual_size - 0x10;                    // record has 16B trailing MD5
    void* new_obj = ObjectB_master.vtable[+0x54](actual_size);
    void* payload = (new_obj + 8);                            // skip 8B header
    void* record_body = record + 0x18;                        // body starts at +0x18

    FUN_9f624(payload, record_body, payload_size);             // memcpy (tiny veneer, 6B)
    FUN_d060(payload, payload_size);                           // preprocess (16-elem array reverse)
    FUN_5610c(payload, payload_size, digest_a /* or record+8 ? */);  // ★ MD5 computation

    void* digest_b = record + 8;                               // record's stored MD5 hash @ +8 (16B)

    int mismatch = 0;
    for (int i = 0; i <= 0xf; i++) {                            // 16-byte digest compare
        if ((int8)digest_b[i] != (int8)digest_a[i]) mismatch = 1;
    }

    if (mismatch) {                                            // hash mismatch (tampered/corrupted)
        ObjectB_master.vtable[+0x58](digest_a);
        ObjectB_master.vtable[+0x58](record);
        ObjectB_master.vtable[+0x58](new_obj);
        return NULL;
    } else {                                                   // hash verified — return verified record
        ObjectB_master.vtable[+0x58](digest_a);
        ObjectB_master.vtable[+0x58](record);
        return new_obj;
    }
}
```

**의미**: 피처폰 게임의 **save data tampering 방지**. RecordStore 안의 데이터가 외부 변조되지 않았는지 MD5 hash 로 검증. 변조 발견 시 record 폐기.

### 2.3 FUN_d060 preprocessing (148B)

```c
void FUN_d060(uint8_t* buf /*r0*/, int len_arg /*r1*/) {
    sub_obj = ***GOT[+0x68];                              // triple deref
    flag = (byte)*GOT[+0x70];                              // single byte flag
    if (flag != 0) {
        // ★ reverse 16-elem array, stride 0x30 bytes
        for (i = 0; i <= 7; i++) {
            uint8_t* lo = buf + i * 0x30;
            uint8_t* hi = buf + (0xf - i) * 0x30;
            for (j = 0; j < 0x30; j++) {
                swap(lo[j], hi[j]);                         // in-place byte swap
            }
        }
        *GOT[+0x70] = 0;                                     // reset flag
    }
    if (len_arg >= 0) {
        FUN_d0f4(buf, len_arg >> 3, ...);                    // call helper with len/8
    }
}
```

**의미**: payload 가 "16-element × 48B array" 형식인 경우 endian-reversal (mobile/JVM 호환 변환). 신규 GOT slot 발견: **GOT[+0x68]** (triple-deref struct base), **GOT[+0x70]** (flag byte ptr).

## 3. FUN_99a9c = ObjectB storage iterator (2TB)

`tools/recon/disasm_save_load_helpers.py` 의 FUN_99a9c (144B):

```c
void* FUN_99a9c(int record_handle /*r0*/, int* out_size /*r1*/) {
    ObjectB_master = *GOT[+0x18];                          // r6 = ObjectB ptr-ptr

    void* size_method = ObjectB_master.vtable[+0x7c];      // ★ method [+0x7c] = "get record size"
    int size_local;
    int err = size_method(record_handle, &size_local);

    if (err == -0xc) {                                     // -12 = end of storage iteration
        *out_size = NULL;
        return 0;
    }

    void* alloc = ObjectB_master.vtable[+0x54];             // R51 alloc
    void* buf = alloc(size_local);
    if (!buf) {
        ObjectB_master.vtable[+0x58](NULL);                  // free NULL
        *out_size = NULL;
        return 0;
    }

    void* read_method = *(ObjectB_master + 0x80);            // ★ ObjectB[+0x80] = "read record"
    err = read_method(record_handle, buf, size_local);

    if (err == -0x12) {                                       // -18 = read failure
        ObjectB_master.vtable[+0x58](buf);                     // free buf
        *out_size = NULL;
        return 0;
    }

    *out_size = size_local;                                    // success
    return buf;
}
```

**ObjectB.vtable[+0x7c] + ObjectB[+0x80]** 신규 method 2개 발견 → **ObjectB known methods 12 → 14**.

Method signatures (추정):
- **`int vtable[+0x7c](int handle, int* size)`** — get next record's size (returns 0 / -12)
- **`int (ObjectB+0x80)(int handle, void* buf, int size)`** — read record contents (returns 0 / -18)

이 두 method 는 **JVM RecordStore** 인터페이스 매핑 가능성 (MIDP javax.microedition.rms.RecordStore.getNextRecordID/getRecord).

## 4. FUN_439a0 = script opcode dispatcher (2TD)

2372B function, **FUN_9a008 의 dominant helper (7 calls)**.

```c
void* FUN_439a0(void* r0_ctx, int r1, int r2, int r3, int sp[0x64], int sp[0x68], int sp[0x6c]) {
    save_args();
    task = FUN_4ad10();
    sp[0x1c] = *r0 + 8;                                       // skip header
    sp[0x28] = task + 0xb4;                                    // task[+0xb4] sub-struct (= FUN_9a008 의 sub-ctx)

    int8_t guard_byte = (int8)task[+0x29e];                    // ★ NEW: task[+0x29e] = interpreter active flag
    if (guard_byte <= 0) {
        FUN_44280();                                            // re-init/abort path
    }

    sp[0x24] = &task[+0x9bb4];                                  // R24 bit flag cluster ptr
    task_cbqueue = &task[+0x9cbc];                              // R40 callback queue cluster ptr

    // ... 12 BLs total: FUN_44280, FUN_44260, FUN_4ad10x2, FUN_7a474, FUN_7a49c, FUN_47a14x2,
    //                   FUN_44534, FUN_445b8, FUN_20b68, FUN_47a74
    // 20 cmps: cmp #0 (9x), cmp #6 (6x), cmp #7 (2x), cmp #0x10 (2x), cmp #0xa0 (1x)
}
```

**역할**: FUN_9a008 의 mode-leaf 마다 호출되는 **opcode execution helper**.
- task[+0x9bb4] (R24 bit flags) → script execution gating
- task[+0x9cbc] (R40 callback queue) → frame callback scheduling
- task[+0x29e] (신규) → interpreter active/idle flag
- cmp #6 (6x) = state value 6 처리 frequent — **state 6 = entity backup restore (Round 52)** 와 연결

**신규 helper 5개 발견 (FUN_439a0 호출 trail)**:
- FUN_44280 (re-init)
- FUN_44260
- FUN_44534
- FUN_445b8
- FUN_47a14 / FUN_47a74 / FUN_7a474

## 5. ObjectB vtable methods 업데이트 (12 → 14)

| offset | role | round 발견 |
|---|---|---|
| +0x00 | ? | R20 |
| +0x08 | dominant reader | R28 |
| +0x0c | event handler | R41 |
| +0x10 | graphics primitive | R44 |
| +0x18 | ? | R20 |
| +0x44 | ? | R22 |
| +0x4c | ? | R22 |
| +0x50 | ? | R20 |
| +0x54 | **alloc(size_t)** | R51 |
| +0x58 | destructor | R47/R50 |
| +0x60 | new method | R47 |
| +0x70 | system time getter (64-bit) | R51 |
| **+0x7c** | **`int getRecordSize(handle, *size)`** ★ | R53 |
| **+0x80** | **`int readRecord(handle, *buf, size)`** ★ | R53 |

`+0x7c` 와 `+0x80` 의 negative error codes (-12, -18) 는 **JVM RecordStore API 에러 코드 추정**:
- -12 = INVALID_RECORD_ID_EXCEPTION 또는 RECORD_STORE_NOT_OPEN
- -18 = RECORD_STORE_FULL_EXCEPTION 또는 다른 IO 에러

## 6. 신규 GOT slots + task fields (Round 53)

### 신규 GOT slots

| slot | 의미 |
|---|---|
| `GOT[+0x68]` | triple-deref struct (FUN_d060 의 buf source) |
| `GOT[+0x70]` | flag byte ptr (FUN_d060 의 endian-reversal trigger) |

**known GOT slots**: R52 의 23 → R53 추가 2 → **25**

### 신규 task_struct field

| field | size | 의미 |
|---|---|---|
| `task[+0x29e]` | sbyte | interpreter active flag (FUN_439a0, 가능한 cooperative scheduling) |
| `task[+0xb4]` | sub-struct base | FUN_9a008 sub-ctx (R52 confirmed, R53 FUN_439a0 도 동일 base) |

## 7. 정정/폐기 사항

| 가설 | 라운드 | 결과 |
|---|---|---|
| FUN_9a008 = sparse state machine | R52 | **폐기** → 7-mode bytecode interpreter (122 sub-opcodes) |
| FUN_9a008 = battle 시스템 후보 | R51-52 | **폐기** → script interpreter (R35 SCN 과 별개) |
| FUN_77c78 = behavior installer | R51 | **폐기** → MD5-verified save record reader |
| FUN_77c78 의 16B compare = name | R52 | **정정** → 16B MD5 digest compare |
| 전투 시스템 = FUN_9a008 | R51-52 | **폐기** — 새로 검색 필요 |

## 8. 전투 시스템 검색 다음 단계

현재 R47-53 의 어느 함수도 명확한 "전투" 패턴 (HP/damage/공격력/방어력 산술) 을 보이지 않음. 가능성:
1. **FUN_8e89e (R35 16.3KB SCN interpreter)** — 일부 opcode 가 전투 효과 (HP 변경) 일 가능성. 본문 정밀 미진행.
2. **별도 large function** — binary 내 미발견 큰 함수 후보 (1KB+). `tools/recon/find_large_functions.py` 같은 도구 필요.
3. **task[+0x9bb4] bit flag field** 의 사용처 — Round 24 의 "dominant flag field". HP/MP 비트 가능성.
4. **FUN_47a14, FUN_47a74** (R53 FUN_439a0 callees) — 본문 미분석. 후보.

## 9. 다음 라운드 (Round 54) 권장 작업

1. **FUN_9a008 JT_1[4] (31-entry sub-JT) 디코드** — mode 4 = 가장 큰 mode, dominant 가능성
2. **FUN_439a0 의 12 BL targets 본문** — FUN_44280/44260/44534/445b8/47a14/47a74
3. **FUN_561dc (MD5_Final) + FUN_56164 (MD5_Update)** 본문 검증 — MD5 알고리즘 완전 확인
4. **arg=+55/+57 의 분기 본문** — `local[-0x5c, -0x64]` 의미 (menu hotkey 가설)
5. **task[+0x29e] writers + readers wide-scan** — interpreter 생명주기 파악
6. **FUN_8e89e (R35 SCN interpreter) opcode 본문 정밀** — 전투 효과 opcode 후보

## 부록 — 산출 스크립트 + raw output

| 스크립트 | 역할 |
|---|---|
| `decode_9a008_nested_jts.py` | JT_1 (7 entries) + JT_2 (16 entries) 디코드 |
| `dump_9a008_jt1_leaves.py` | 7 JT_1 leaf 의 첫 30 inst dump |
| `disasm_save_load_helpers.py` | FUN_99a9c/9f624/d060/5610c 4 helpers full disasm |
| `disasm_439a0_dominant_helper.py` | FUN_439a0 prologue 50 inst + 전체 cmp/BL 통계 |

raw output: `work/h3/round53_9a008_jt1.txt`, `work/h3/round53_save_helpers.txt`, `work/h3/round53_439a0.txt`.
