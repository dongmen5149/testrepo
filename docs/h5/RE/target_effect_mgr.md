# TargetEffectMgr / TargetEffect VFX 시스템 RE (Round 80)

> R73 에서 ProcHeroSkill 이 `TargetEffectMgr::NewTargetEffect` 를 11 회 호출하며
> `effect_type {4, 7, 8}` 을 distinct 값으로 사용하는 것을 발견. 본 라운드는 5
> overload chain 의 wrapper 구조 + 실 구현 (slot allocator) + Effect 베이스
> 클래스 setter + post-init registration dispatch 를 확정한다.

## 1. 함수 시그니처 (5 overload)

`_ZN15TargetEffectMgr15NewTargetEffectE...` 의 5 변종 = **default arg 채움 wrapper chain**:

| 주소 | 크기 | 시그니처 (인자 수) | 호출 |
|---|---|---|---|
| `0x62d40` | 100B | `(this, char a, int b, HSI*, SPRITE*, char×4, char×2)` (11) | tail-call `_+s` (sets short s = 0) |
| `0x62cd4` | 108B | `(..., short s, char×2)` (13) | tail-call `_+sai` (sets char a = 0, int i = 0) |
| `0x62c54` | 128B | `(..., short s, char a, int i)` (14) | tail-call `_full` (default char×2) |
| `0x62bcc` | 136B | `(..., short s, char a, int i, ushort h)` (15) | tail-call `_full` (parallel) |
| **`0x62a34`** | **408B** | **`(..., char×4)` (17 args + this) — 실 구현** | — |

## 2. `_full` 실 구현 (@0x62a34, 408B)

### 2.1 인자 분배 (entry sequence)

```
r0 (this = TargetEffectMgr) → r5
r1 (char a effect_type)    → r8
r2 (int b)                 → r7
r3 (HeroSkillInfo*)        → sl
arg 5 (sp+0x98, SPRITE*)
arg 6 (sp+0x9c, char)      → sb
arg 7..18 → sp+0x44..+0x68 (재정렬)
arg 17 (sp+0xcc, char)     → r6  ★ post-init 분기 key
```

### 2.2 Slot allocator loop (@0x62ab0..0x62ad8)

```cpp
int fp = 0;
do {
    Effect* slot = (Effect*)(this + fp * 0x284);   // 0x284 = 644B per slot
    fp += 1;
    if (slot->IsEmpty())                            // bl 0x610d8 returns 1 if active==0
        goto found_slot;                            // r0 != 0 → not empty, retry
} while (fp != 100);
return NULL;                                        // out of slots
```

→ **TargetEffectMgr 는 100 슬롯 × 0x284 byte = 64,400 byte 배열**.

### 2.3 Slot 초기화

found slot (r4) 에 대해 `bl 0x62840 = TargetEffect::NewTargetEffect (base)` 호출 →
17 args 그대로 패스 → slot field 25+ 채움 (§3).

### 2.4 Post-init dispatch on `r6` (arg 17)

```cpp
switch (arg17) {
    case 0: register_to_manager(global_ptr + 0x15e0); break;  // type 0 manager
    case 1: register_to_manager(global_ptr + 0x15d8); break;  // type 1 manager
    case 2: register_to_manager(global_ptr + 0x15e4); break;  // type 2 manager
    default: /* no registration */ break;
}
return slot;
```

manager 등록 함수 = `bl 0xabb94`. 3 manager 채널 (global +0x15d8/+0x15e0/+0x15e4) 가
별도 update 큐 또는 render 큐로 추정.

**R73 의 effect_type 4/7/8 은 arg 1 (r1 → r8)**, 본 r6 (arg 17) 과 다른 개념.

## 3. TargetEffect::NewTargetEffect (base @0x62840, 500B)

slot field 초기화. 핵심 stores:

| field | 출처 | 의미 (추정) |
|---|---|---|
| `+0x11` (u8) = 1 | hard-coded | active flag (`IsEmpty` 검사 대상) |
| `+0x12` (u8) | `Effect::SetEffectType` (bl 0x610f4 with r1=arg `a`) | **★ effect_type — R73 의 4/7/8 저장 위치** |
| `+0x13` (u8) | arg sp+0x58 (r7) | 부속 char field |
| `+0x14` (u16) | `Effect::SetEffectFrame` (bl 0x61114) | 시작 frame |
| `+0x16` (u16) | `Effect::SetEffectLastFrame` (bl 0x61124) | 마지막 frame |
| `+0x18` (u32) | `Effect::SetEffectValue` (bl 0x61134) | numeric value (damage 등) |
| `+0x1c` (u32) | arg sp+8 | int b (`SetEffectFrame` 전 인자) |
| `+0x20` (ptr) | arg from sp+0x50 (r5) | SPRITE* (source sprite) |
| `+0x24` (u8) | r8 (arg sp+0x54) | 부속 char |
| `+0x8c..+0x8f` | args | 4 char 묶음 (좌표 또는 hit info?) |
| `+0x90` (u16) | arg sp+0x10 | short (offset 등) |
| `+0x92, +0x94 (u32)` | args | char + int (캐스터 ID 등) |
| `+0x9c..+0x9f` | args | 4 char (스킬 메타) |
| `+0xa0..+0xa7` (2×ptr) | `bl 0x8c7d4/+0x8c7ec` | sprite/anim ptrs (sprite manager getter) |
| `+0xc0` (u8) = 0 | hard-coded | counter (ProcTargetEffectSkill 에서 +1 함) |
| `+0x18c..+0x253` (200B) | `memset 0` | work area (per-frame state) |
| `+0x254, +0x260` = 0 | hard-coded | 0 init |
| `+0x264` (u8) | sb (arg sp+0x88) | 부속 |
| `+0x278..+0x281` | 0/0xFF mix | state flags |
| `+0x279` (u8) | `bl 0xda4b0(SPRITE, char×2)` result, else 0 | sprite-derived char |
| `+0x27a, +0x27b` | sb + 1 | spawn flags |

**TargetEffect struct 총 크기 = 0x284 byte (644 B)**.

## 4. Effect 베이스 클래스 (TargetEffect 의 parent)

`.dynsym` 에서 발견:

| 함수 | 주소 | 동작 |
|---|---|---|
| `Effect::IsEmpty()` | 0x610d8 | `return [+0x11] == 0 ? 1 : 0` (active flag inverted) |
| `Effect::SetEffectType(char)` | 0x610f4 | `[+0x12] = c` |
| `Effect::SetEffectFrame(short)` | 0x61114 | `[+0x14] = s` |
| `Effect::SetEffectLastFrame(short)` | 0x61124 | `[+0x16] = s` |
| `Effect::SetEffectValue(int)` | 0x61134 | `[+0x18] = i` |
| `OBJECT::SetXY(int, int)` | 0xcfda4 | base ctor (좌표 설정) |
| `OBJECT::SetObjectType(char)` | 0xcfdac | TargetEffect 의 ObjectType = 3 |

**Effect 베이스 field layout (TargetEffect 의 +0x10..+0x1b 영역)**:

| offset | type | 의미 |
|---|---|---|
| +0x10 | ? | (앞 OBJECT base) |
| +0x11 | u8 | active flag (1=active, 0=empty) |
| **+0x12** | **u8** | **★ effect_type (R73: 4/7/8 등)** |
| +0x14 | u16 | start frame |
| +0x16 | u16 | end frame (last frame) |
| +0x18 | u32 | numeric value (damage 등) |

## 5. R73 의 effect_type {4, 7, 8} 의미

ProcHeroSkill 의 11 NewTargetEffect 호출에서 arg `a` = effect_type 으로 전달되는 값:
- `4` (immediate, 6 회): 가장 흔한 — 기본 skill VFX
- `7` (immediate, 2 회): 보조 VFX
- `8` (immediate, 1 회): special VFX
- `dynamic` (register, 3 회): skill_info 또는 외부 source 로부터 동적 전달

**의미 추적**: ProcTargetEffectSkill (@0x64a08, 4276B) 가 effect 의 per-frame 처리이지만
이 함수는 `[+0x12]` 직접 안 읽고 **skill_info 기반 처리** (Formula::calc, level cap,
sprite 분기 등). effect_type 은 **render 단계에서 사용** (sprite frame selection, animation
curve 선택 등) — R81+ 에서 sprite 코드 추적 시 매핑 가능.

→ **R80 본 라운드 결론**: effect_type 4/7/8 은 Effect+0x12 에 저장되는 **VFX 카테고리 코드**.
실 의미 (어떤 시각 효과가 나는지) 는 render 단계에서 확인 가능. ProcHeroSkill 의 호출
context 로 보면:
  - case 0/2/4/6 기본 공격 path: type 4 (기본 hit VFX)
  - case 1/7 timestop path: type 7 (시간 정지 VFX)
  - case 5 shock path: type 8 (충격 VFX)
  - dynamic: skill 별 special VFX

## 6. R80 결론

| 항목 | 결과 |
|---|---|
| TEM 5 overload 구조 | 4 wrapper + 1 _full 실 구현 chain |
| _full slot allocator | 100 slot × 0x284B, IsEmpty 검사로 free slot |
| TargetEffect struct | 0x284B, 25+ field 매핑 (§3) |
| Effect 베이스 클래스 | 5 setter (Type/Frame/LastFrame/Value/IsEmpty) 확정 |
| effect_type 저장 위치 | Effect+0x12 (R73 4/7/8 의 위치 확정) |
| post-init r6 dispatch | 0/1/2 → manager 등록 (global +0x15d8/+0x15e0/+0x15e4), 3+ → no-op |
| ProcTargetEffectSkill | per-frame skill 처리, skill_info 기반 (Formula::calc 호출) |

R81+ 추천:
- effect_type 4/7/8 의 sprite/render 단 실 의미 추적 (DrawTargetEffect 또는 유사 함수)
- ProcTargetEffectSkill (4276B) 의 jumptable / 분기 정밀 분석
- TEM 3 manager 채널 (global +0x15d8/+0x15e0/+0x15e4) 의 역할 확정
