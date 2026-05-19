# HERO::LoadResSkillInfo / LoadResClassSkillInfo — file layout RE (Round 77)

> R75 의 `GameData.skill_info(class_id, skill_id)` 는 R72/R73 disasm 으로 추정된
> byte offset 을 사용했다. R77 은 `HERO::LoadResSkillInfo` (@0x8bba4, 784B) 와
> `HERO::LoadResClassSkillInfo` (@0x9b308, 48B) 를 ARM full disasm 하여 **실제
> skill 파일 byte layout** 과 **HeroSkillInfo 88B struct 의 file-loaded 영역 vs
> runtime-state 영역** 을 확정한다.

## 1. 함수 시그니처

```cpp
void HERO::LoadResSkillInfo(this, char arg);   // @0x8bba4, 784B
void HERO::LoadResClassSkillInfo(this);        // @0x9b308, 48B
```

`LoadResClassSkillInfo` 는 호출 wrapper:
```cpp
void HERO::LoadResClassSkillInfo(this) {
    LoadResSkillInfo(this, this->class_id);   // class skills (43개)
    LoadResSkillInfo(this, 5);                // spirit/shared skills (16개)
    LoadResSkillIcon(this);                   // 아이콘 로드 (tail-call)
}
```

`arg` 는 dispatch key 이자 array start index 결정:
- `arg == 5`: r7 starts at 0x2b(43), fp=0x3b(59) → 슬롯 **43..58** 로드 (spirit 16개)
- `arg != 5`: r7 starts at 0, fp=0x2b → 슬롯 **0..42** 로드 (class 43개)

**총 59 슬롯** (R70 의 HERO+0x348 88B×59 배열과 일치).

## 2. 외부 helper

| 주소 | 역할 |
|---|---|
| `0x14e4ec` | filename builder (arg = class_id → filename) |
| `0x144e80` | 파일 로드 (returns buffer ptr in r0) |
| `0x1437ec` | **read u16 BE** (`u16 read_u16(char* buf, int offset)`) |
| `0xabd18` | `malloc(size, 0)` |
| `0x31504` | `memset` |
| `0x3130c` | `memcpy` |
| `0x14cfa4` | 파일 버퍼 free |

## 3. 파일 layout (per record)

레코드 헤더 3 byte + name + 0x30 byte stats + desc string.

```
record offset    size  의미
─────────────  ─────  ──────────────────────────────────────────
+0x00..+0x01      2  u16, 첫 bl 0x1437ec 결과 → discard (skill_id 또는 magic)
+0x02             1  name_len
+0x03..(+name)  N=name_len  name string (entry+0x04 에 malloc 후 memcpy)
+0x03+N         0x30  stats area (아래 §4)
+0x33+N        Mdsc  description string (entry+0x40 에 malloc 후 memcpy)
                     Mdsc = stats_area[0x2f] (desc_len byte)
```

레코드 총 크기 = `3 + name_len + 0x30 + desc_len` byte.

## 4. Stats area (0x30 byte) → HeroSkillInfo entry 매핑

stats_base = `record + 3 + name_len`.
sub-rel 은 stats_base 기준 offset.

| sub-rel | type | → entry+offset | 의미 (R70/R72/R73 cross-ref) |
|---|---|---|---|
| 0x00 | u8 | +0x08 | flag (R70 의 +0x0a 가설은 +0x0a 였음 — 별도) |
| 0x01 | u8 | +0x09 | |
| 0x02 | u8 | +0x0a | flag (R70 의 +0x0a) |
| 0x03 | u8 | +0x0b | |
| 0x04 | u8 | +0x0c | |
| 0x05..0x06 | u16 | +0x0e | |
| 0x07 | u8 | +0x10 | |
| 0x08..0x09 | u16 | +0x12 | |
| 0x0a | u8 | +0x14 | |
| 0x0b..0x0c | u16 | +0x16 | |
| 0x0d | u8 | +0x18 | |
| 0x0e..0x0f | u16 | +0x1a | |
| 0x10 | u8 | +0x1c | mode (R70 의 +0x1c/+0x1d) |
| 0x11 | u8 | +0x1d | mode (R72 의 +0x1c alternate path flag) |
| 0x12 | u8 | +0x1e | |
| 0x13..0x14 | u16 | +0x20 | |
| 0x15 | u8 | +0x22 | |
| 0x16..0x17 | u16 | +0x24 | |
| 0x18 | u8 | +0x26 | |
| 0x19 | u8 | +0x27 | |
| **0x1a** | **u8** | **+0x28** | **★ effect_type — R70/R72 JT1 5-way dispatch key** |
| 0x1b | u8 | +0x29 | effect2 (R70) |
| 0x1c | u8 | +0x2a | formula_arg (R70) |
| 0x1d | u8 | +0x2b | |
| 0x1e | u8 | +0x2c | |
| 0x1f | u8 | +0x2d | |
| 0x20 | u8 | +0x2e | |
| 0x21 | u8 | +0x2f | |
| 0x22..0x23 | u16 | +0x32 | u16 cluster #1 (R70 4×u16 primary/secondary) |
| 0x24..0x25 | u16 | +0x36 | u16 cluster #3 |
| **0x26** | **u8** | **+0x30** | **★ behavior / dynamic Formula id — R72/R73 case 5 shock skill** |
| 0x27..0x28 | u16 | +0x34 | u16 cluster #2 |
| 0x29..0x2a | u16 | +0x38 | u16 cluster #4 |
| **0x2b** | **u8** | **+0x3a** | **★ special dispatch — R72 cmp 0x34/0x37 special handler trigger** |
| 0x2c | u8 | +0x3b | |
| **0x2d** | **u8** | **+0x3c** | **★ Formula id 1 — R72 confirmed** |
| **0x2e** | **u8** | **+0x3d** | **★ Formula id 2 — R72 confirmed** |
| 0x2f | u8 | (desc_len, not stored in entry) | description length |

note: stats area 의 u16 가 **인접하지 않은 byte** 다음에 strh 되는 패턴 (예: sub-rel 0x22 u16 → +0x32, 그러나 +0x30 은 sub-rel 0x26 byte) 은 ARM ILP 명령 reorder 의 결과이며, 실제 strh 도착 순서는:
- +0x32 ← rel 0x22 u16
- +0x36 ← rel 0x24 u16  (★ +0x36 이 +0x34 보다 먼저)
- +0x30 ← rel 0x26 u8   (★ byte 가 후속 u16 사이에 끼어 있음)
- +0x34 ← rel 0x27 u16
- +0x38 ← rel 0x29 u16

즉 entry struct 의 영역 +0x30..+0x39 는 **(u8, _, u16, u16, u16, u16)** 가 아니라 **(u8 + pad, u16, u16, u16, u16)** = 1+1+2+2+2+2 = 10 byte 로 packed.

## 5. Entry 88B struct: file-loaded vs runtime-state

| 영역 | byte range | 출처 |
|---|---|---|
| skill_idx | +0x00 | **loop counter r7** (file 의 0x00..0x01 은 discard) |
| name ptr | +0x04..+0x07 | file name 문자열 (malloc) |
| stats (file) | +0x08..+0x3d | file (위 §4) |
| pad | +0x3e..+0x3f | alignment |
| desc ptr | +0x40..+0x43 | file description 문자열 (malloc) |
| **runtime state** | **+0x44..+0x57** | **★ LoadResSkillInfo 에서 채우지 않음** — HERO::InitSkillEmpty (@0x88a20) 또는 ProcHeroSkill 진입 시 초기화 |

**R72/R73 의 가설 정정 (R77)**:
| R72/R73 claim | R77 실 검증 |
|---|---|
| `+0x44 knockback_idx` (R69) | file 로드 안 됨 — runtime 또는 별도 init source |
| `+0x46 shock count` (R73) | file 로드 안 됨 — runtime |
| `+0x48 max_combo` (R72) | file 로드 안 됨 — runtime 또는 hard-coded |
| `+0x4a SP delta s16` (R72) | file 로드 안 됨 — runtime |
| `+0x4c` | file 로드 안 됨 — runtime |
| `+0x4e class 3 threshold` (R73) | file 로드 안 됨 — runtime 또는 hard-coded |

위 6 field 가 ProcHeroSkill 에서 **ldrsb/ldrsh** 로 읽히는 것은 사실이지만 (R72/R73 disasm 확정), 그 값의 source 는 skill 데이터 파일이 아니라 **다른 경로** (별도 init function, hard-coded table, 또는 runtime state). R78+ 에서 InitSkillEmpty (@0x88a20) 와 호출 site 추적 필요.

**확정 file-loaded 영역**: +0x00..+0x43 (skill_idx + name ptr + 0x30 stats + desc ptr).
**확정 runtime 영역**: +0x44..+0x57 (20 byte).

## 6. R75 `GameData.skill_info` API 정확화 영향

R75 의 10 field 노출 중 **file-loaded 영역에 있는 7 field 는 정확** (effect_type/dynamic_formula_id/formula_id_1/formula_id_2/special_dispatch + 2 u16 value):

| R75 field | LoadResSkillInfo 검증 |
|---|---|
| `effect_type` (+0x28) | ✓ stats sub-rel 0x1a |
| `dynamic_formula_id` (+0x30) | ✓ stats sub-rel 0x26 |
| `formula_id_1` (+0x3c) | ✓ stats sub-rel 0x2d |
| `formula_id_2` (+0x3d) | ✓ stats sub-rel 0x2e |
| `special_dispatch` (+0x3a) | ✓ stats sub-rel 0x2b |
| `primary_u16` (+0x32) | ✓ stats sub-rel 0x22 |
| `secondary_u16` (+0x36) | ✓ stats sub-rel 0x24 |
| `kb_idx` (+0x44) | **runtime — file 출처 아님, 재검증 필요** |
| `shock_count` (+0x46) | **runtime — 재검증 필요** |
| `sp_delta` (+0x4a) | **runtime — 재검증 필요** |

→ R78+ 에서 `GameData.skill_info` 의 runtime 3 field 정정 필요. 현재 R75 코드는 "guess" 로 동작 (file 파싱 시 미초기화 0 값 사용).

## 7. 파일명 추정

`bl 0x14e4ec` (filename builder) 는 `arg` 를 받음. arg = class_id (0..4) 또는 5. 따라서 파일 6 개 추정:
- class 0: `skill_class0.dat` (또는 유사)
- class 1: `skill_class1.dat`
- class 2: `skill_class2.dat`
- class 3: `skill_class3.dat`
- class 4: `skill_class4.dat`
- arg 5: `skill_class5.dat` (spirit/shared)

R78+ 에서 VFS dump 로 실제 파일명 + 데이터 검증 필요.

## 8. R77 결론

- HeroSkillInfo 88B = **68B file-loaded (+0x00..+0x43) + 20B runtime (+0x44..+0x57)**
- file-loaded 영역 31 개 field byte/word offset 정확화
- R72/R73 의 6 개 "runtime field" 가설은 **출처가 file 이 아니라는 점만 정정** (값 자체의 의미는 ProcHeroSkill disasm 으로 확정된 채 유지)
- R75 `GameData.skill_info` 7/10 field 정확, 3/10 runtime → R78+ 정정 대상
