# Hero3 Ghidra — Round 42 / 2026-05-17 PM-6 (ObjectE 식별 + 5 신규 GOT slots + event caller 분포)

> Round 41 (`ghidra-event-dispatcher-and-wide-scan-2026-05-17.md`) 의 후속 — 공통 handler 의 sl-relative 글로벌 object 정체 + FUN_00024780/24da8 본문 + FUN_0002c6a4 17 callers 매핑.

## 한 줄 요약

⭐⭐⭐ **GOT base = sl base = 0xb2c40** PIC sl-trampoline 계산으로 재검증 (Round 23+33). ⭐⭐⭐ **ObjectE 신규 식별** (GOT[+0x78], 46 sites, 0xDxxx 영역 집중 = FUN_00006334 10KB main state machine area). ⭐⭐ **5 신규 GOT slots**: 0x74, 0x78, 0x140, 0x144, 0x160 = ObjectE 클러스터 + 2개 pending flag ptr. **ObjectB pending flag (GOT[+0x160]) = 114 sites system-wide** (ObjectB 다음으로 많이 사용). ⭐⭐ **FUN_00024780 = ObjectE event handler** (468B, cmp #0xf range guard + cmp #4/5, task[0xa0c0/9e30/a220/9c6c] + GOT[+0x78/0x140/0x74/0x144]). ⭐⭐ **FUN_00024da8 = NPC subsystem state inspector** (600B, BL=1 ctx only, 12 GOT slot literals read-only query, 6 callers). ⭐⭐⭐ **FUN_0002c6a4 17 callers 분포**: 5th + 6th indirect entries + entity update loop (FUN_000818f0) + 2 multi-event sources (FUN_0002ae44, FUN_0003a444 each 4 calls) + **3 indirect entry 후보 (no push prologue <0x800)**.

## 2IA: 공통 handler 의 sl-relative 글로벌 object 정체

### sl 베이스 검증 (PIC trampoline 계산)

`tools/recon/trace_2c9ca_sl_global.py` 출력:

```
FUN_0002cdb4 sl setup:
  literal at 0x0002cdfc = 0x00085e7c
  sl = pc(0x0002cdc4) + 0x00085e7c = 0x000b2c40
  sl - GOT_BASE (0xb2c40) = 0x00000000  ⭐ 완벽 일치

FUN_0002c6a4 sl setup:
  literal at 0x0002ca00 = 0x0008658a
  sl = 0x000b2c40                       ⭐ 동일
```

⭐⭐⭐ **두 함수 모두 sl base = 0xb2c40 = GOT base** (Round 23+33 확정 사실 재검증).

### FUN_0002cdb4 helper 의 GOT slot 사용

| ldr 위치 | literal | resolved | slot 정체 |
|---|---|---|---|
| 0x2cdc2 | 0x160 | GOT[+0x160] | ⭐ pending flag ptr (NEW) |
| 0x2cdce | 0x18 | GOT[+0x18] | ObjectB (Round 21+33 확정) |
| 0x2cdd6 | 0x160 | GOT[+0x160] | (재참조) |
| 0x2cde6 | 0x160 | GOT[+0x160] | (clear at end) |

**FUN_0002cdb4 동작 풀이**:
1. r3 = *GOT[+0x160] (deref pending flag ptr → flag value)
2. r3 = *r3 (double deref) — if null, skip
3. r3 = *GOT[+0x18] = ObjectB ptr
4. r2 = *ObjectB (vtable ptr)
5. r2 = vtable[+0x58] (method pointer)
6. bl veneer 0xa429c (= bx r2) → ObjectB.method58(deref'd pending)
7. *GOT[+0x160] location = 0 (clear pending)

### FUN_0002c6a4 공통 handler 0x2c9ca 의 GOT slot 사용

| ldr 위치 | literal | resolved | slot 정체 |
|---|---|---|---|
| 0x2c9ce | 0x140 | GOT[+0x140] | ⭐ ObjectE pending flag ptr (NEW) |
| 0x2c9da | 0x78 | GOT[+0x78] | ⭐ **ObjectE ptr (NEW)** |
| 0x2c9e2 | 0x140 | GOT[+0x140] | (재참조 = pending data) |
| 0x2c9f2 | 0x140 | GOT[+0x140] | (clear at end) |

**공통 handler 동작 풀이**:
1. r3 = *GOT[+0x140] → if null, skip
2. r2 = *GOT[+0x78] = ObjectE ptr
3. r2 = *ObjectE (vtable)
4. r3 = *(*GOT[+0x140]) (double deref = pending data ptr)
5. r2 = vtable[+0xc] (method ptr)
6. bl veneer 0xa429c → ObjectE.method0c(pending_data)
7. *GOT[+0x140] = 0 (clear)

### Double dispatch 완전 풀이

events 11/16/17/18/19 발생 시:
```
FUN_0002c6a4(event_id)
  ├ event_id - 3 → cmp [3..18] range guard
  ├ branch to 0x2c9ca (공통 handler)
  │   ├ bl FUN_0002cdb4
  │   │   ├ if *GOT[+0x160] != null:
  │   │   │     ObjectB.vtable[+0x58](*GOT[+0x160])
  │   │   └ *GOT[+0x160] = 0
  │   ├ if *GOT[+0x140] != null:
  │   │     ObjectE.vtable[+0x0c](*GOT[+0x140])
  │   └ *GOT[+0x140] = 0
  └ task[0x290] = event_id (마지막 저장)
```

⭐⭐⭐ **두 객체 (ObjectB + ObjectE) 가 같은 event 에 대해 각자 처리**:
- **ObjectB.method58** = 이벤트 첫 단계 처리 (notify)
- **ObjectE.method0c** = 이벤트 두 번째 단계 처리 (handle)

## 2IA-2: 신규 GOT slots wide-scan (system-wide usage)

`tools/recon/scan_new_got_slots.py` 출력:

| slot | sites | 정체 |
|---|---|---|
| **GOT[+0x18]** | **396** ⭐⭐⭐ | ObjectB (시스템 가장 활발) |
| **GOT[+0x160]** | **114** ⭐⭐ | **ObjectB pending flag ptr (NEW Round 42)** |
| **GOT[+0x78]** | **46** ⭐ | **ObjectE ptr (NEW Round 42)** — 0xDxxx 영역 집중 |
| GOT[+0x16c] | 36 | alt task_struct ptr (Round 23) |
| GOT[+0x140] | 9 | ObjectE pending flag ptr (NEW Round 42) |
| GOT[+0x44c] | 8 | ObjectA ptr (Round 20) |
| GOT[+0x128] | 7 | secondary state ptr (Round 22) |
| GOT[+0x29e] | 6 | small flag (Round 22) |
| GOT[+0x444] | 6 | task_ptr (Round 22) |
| GOT[+0xd00] | 6 | StorageCell ptr (Round 22) |
| GOT[+0xd1c] | 6 | ObjectA helper cluster (Round 25) |
| GOT[+0xd04] | 4 | ObjectA helper data #1 |
| GOT[+0xd08] | 4 | ObjectA helper data #2 |

⭐ **GOT[+0x160] 114 sites** = ObjectB pending flag 이 시스템 전반에서 두 번째로 많이 사용 (이벤트 등록 등)
⭐ **GOT[+0x78] 46 sites 모두 0xDxxx 영역** = ObjectE 는 **FUN_00006334 (10KB main state machine, Round 17)** 의 전용 객체로 추정 — 게임 메인 루프의 핵심

### Total GOT slot count: 14 known (9 from Round 33 → 14 Round 42)

```
0x18  : ObjectB ptr ⭐
0x74  : (Round 42 NEW, ObjectE 인접 candidate)
0x78  : ObjectE ptr ⭐ (Round 42 NEW)
0x128 : secondary state ptr
0x140 : ObjectE pending flag ptr (Round 42 NEW)
0x144 : (Round 42 NEW, FUN_00024780 에서 발견)
0x160 : ObjectB pending flag ptr (Round 42 NEW)
0x16c : alt task_struct ptr (147 readers)
0x29e : small flag
0x444 : task_ptr
0x44c : ObjectA ptr
0xd00 : StorageCell ptr
0xd04 : ObjectA helper data #1
0xd08 : ObjectA helper data #2
0xd1c : ObjectA helper cluster
```

## 2IE: FUN_00024780 (468B, FUN_0002ae44 caller)

### 프로파일

- 범위: 0x24780~0x24954 = 468 byte, 198 instr
- 9 cmp arms: cmp #0 (6x), **cmp #0xf** (range guard), cmp #4, cmp #5
- BL = **13 context_getter + 1 screen_ptr_getter** = state-heavy + 약간의 rendering
- 12 PC-rel literals (5 got_slot_offsets + others)

### Literals 풀이

GOT slot offsets:
- **0x78 (ObjectE), 0x140 (ObjectE pending), 0x74, 0x144** = ObjectE 클러스터 4 슬롯 직접 사용

Task fields:
- **0xa0c0** = NPC subsystem mode (Round 39)
- **0x9e30** = sound state adjacent (Round 27 의 0x9e28 인접)
- **0xa220** = sound state cluster (Round 22)
- **0x9c6c** = byte cluster (Round 25)

Other:
- 0x8e4ae = binary_addr (code pointer or data ref)
- 0xffff3bf8 (signed -0xc408) = sl-relative offset (트램폴린)
- 0xffffd8f1 = sl-relative

### 해석

cmp #0xf bhi 0x247cc + cmp #4 + cmp #5 = **input 범위 0..0xf event handler with cases 4/5 specific paths**.
ObjectE 4 슬롯 + NPC subsystem mode + sound state cluster 동시 사용 = **ObjectE 이벤트 처리 함수** (NPC mode 변경 + sound 알림 + 일부 rendering).

caller: 0x48ae8 in FUN_00048xxx (단일 caller, 시스템 hook).

저장: `work/h3/fun_24780_disasm.json`

## 2IF: FUN_00024da8 (600B, 6 callers)

### 프로파일

- 범위: 0x24da8~0x25000 = 600 byte, 292 instr
- 6 cmp arms: cmp #0 (5x), **cmp #0xb** (1x)
- BL = **1 context_getter only** ⭐ (pure read query)
- 12 GOT slot literals + 2 zero literals

### Literals 풀이

Task fields (12 GOT slot literals):
- **0xa0cc** = ⭐ NEW NPC mode adjacent field (Round 42 신규)
- 0x9cd4, 0x9cd8 (multiple): callback queue cursor + stage 2 base (Round 40)
- 0x9ccc: callback queue count 2
- **0x9bc8, 0x9bba**: cluster substructure A 필드 (Round 25)
- 0x9e28: sound state #1 (Round 27)

### 해석

⭐⭐⭐ **FUN_00024da8 = "NPC subsystem state query" 함수** — 다음 시스템 영역을 모두 read:
- NPC subsystem (task[0xa0cc])
- callback queue (0x9cd4/9cd8/9ccc)
- cluster substructure A (0x9bc8/9bba)
- sound state (0x9e28)

BL=1 ctx only = **pure read-only**, 시스템 전반 6 callers 호출 = **central state query function**.

### Callers

- 0x249e0 in FUN_00024954 +0x8c (FUN_00024780 직후 함수)
- 0x253a8, 0x25462 in 0x25xxx 영역
- 0x2af6c, 0x2b43c in 0x2Axxx 영역
- 0x7d54a in 0x7Dxxx 영역

저장: `work/h3/fun_24da8_disasm.json`

## 2IG: FUN_0002c6a4 17 callers 분포 매핑

| Container | offset(s) | 정체 |
|---|---|---|
| **FUN_000241dc** | +0x98 | ⭐ **5번째 indirect entry** (Round 29) |
| **FUN_000245fc** | +0x150 | ⭐ **6번째 indirect entry** mode 7 path (Round 38) |
| **FUN_0002ae44** | +0x40, +0x6a, +0x294, +0x2a6 | secondary state path (**4 calls**) |
| **FUN_0003a444** | +0xd2, +0x226, +0x250, +0x3e4 | ⭐ **NEW** multi-event source (**4 calls**) |
| **FUN_000818f0** | +0xf4 | ⭐⭐ **entity update loop** (Round 28, 5.6KB) |
| FUN_00053e08 | +0x2be | NEW single-event |
| FUN_00086058 | +0x6a | NEW single-event |
| FUN_000933e8 | +0x6c | NEW single-event |
| (no push <0x800) | 0x28ada, 0x28de8, 0x424c2 | ⭐ **3 indirect entry 후보** |

### 핵심 통찰

⭐⭐⭐ **FUN_000818f0 (entity update loop) → FUN_0002c6a4**: **entity update 가 이벤트를 trigger 한다** = 게임 entity 의 상태 변화 (전투/이동/AI 등) 가 이벤트 시스템을 통해 다른 객체에 알림.

⭐⭐ **FUN_0002ae44 + FUN_0003a444 = 각 4 calls multi-event sources**: 두 함수가 시스템 내에서 가장 많은 이벤트 발생기. FUN_0003a444 (NEW) 의 정체 = 다음 라운드 분석 후보.

⭐ **3 indirect entry 후보** (0x28ada, 0x28de8, 0x424c2 — push prologue 0x800 backwards 미발견): 이들이 indirect entry function 이면 **Hero3 indirect entry 7개 이상**으로 확장됨. 추가 확인 필요.

## Round 42 종합 진척

### ✅ 검증 추가

1. **GOT base 0xb2c40 = sl base 재검증** (PIC trampoline 계산)
2. **ObjectE 신규 식별** (GOT[+0x78], 46 sites system-wide, 0xDxxx 영역 집중)
3. **5 신규 GOT slots**: 0x74, 0x78, 0x140, 0x144, 0x160 → **14 known GOT slots** (Round 33 의 9개에서 확장)
4. **공통 handler 동작 완전 풀이**: ObjectB.method58 + ObjectE.method0c 순서로 호출, 각각 자체 pending flag (GOT[+0x160], GOT[+0x140])
5. **FUN_00024780 = ObjectE event handler** + NPC subsystem 통합
6. **FUN_00024da8 = NPC subsystem state inspector** (pure read query, 6 callers)
7. **task[0xa0cc] 신규 field** (NPC mode 인접)
8. **FUN_0002c6a4 17 callers 매핑**: 5th + 6th indirect entries + entity update loop + 2 multi-event sources + 3 indirect entry 후보

### 진척률 (Round 42 시점)

- Ghidra 게임 로직 리버싱: ~32~40% → **~35~42%**
- task_struct 모델: ~37% → **~38%** (task[0xa0cc] 신규)
- GOT 모델: 9 slots → **14 known slots**
- 전체: ~30~40% → **~32~42%**

### ⭐ 다음 라운드 (43) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2JA** | **3 indirect entry 후보 확인** (0x28ada, 0x28de8, 0x424c2) — push prologue 확장 검색 + caller scan | `find_callers_generic.py` + extend backward search |
| ⭐⭐ **2JB** | **FUN_0003a444 본문** (NEW, 4 events trigger) — 어떤 게임 시스템이 multi-event source 인지 | inline disasm |
| ⭐⭐ **2JC** | FUN_000818f0 +0xf4 의 event_id 추적 — entity update 가 trigger 하는 event 종류 | window disasm around 0x819e4 |
| ⭐⭐ **2JD** | event 3 + event 15 specific paths 본문 (2IB/2IC, Round 41 미완) | inline disasm |
| ⭐ **2JE** | ObjectE 의 vtable 구조 (method [+0xc], [+0x58] 외 다른 슬롯) | wide-scan 'GOT[+0x78] readers' |
| ⭐ **2JF** | FUN_00024954 본문 (FUN_00024780 직후, FUN_00024da8 caller +0x8c) | inline disasm |
| ⭐ **2JG** | callback queue stage 1 record sub-struct 구조 | record dump |

### 도구 산출 (Round 42)

- `tools/recon/trace_2c9ca_sl_global.py` (new) — PIC sl-trampoline literal 추적
- `tools/recon/scan_new_got_slots.py` (new) — GOT slot system-wide 사용 wide-scan

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 41 의 [`ghidra-event-dispatcher-and-wide-scan-2026-05-17.md`](ghidra-event-dispatcher-and-wide-scan-2026-05-17.md) 읽기
2. PROGRESS.md 의 **14 known GOT slots** + **ObjectE 신규 식별** 확인
3. **권장 첫 작업: 2JA** — 3 indirect entry 후보 (0x28ada/0x28de8/0x424c2) 확인. 이들이 indirect entry 이면 시스템 진입점이 6개 → 9개로 확장되어 게임 update flow 완성도 크게 올라감.
