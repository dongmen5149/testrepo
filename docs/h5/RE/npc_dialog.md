# NPC Dialog 시스템 — RE 결과 (Round 68)

> R67 의 `disasm_h5_dialog_motion.py` PASS 1 summary 결과에서
> `cmp r2, #7` / `cmp r1, #5` 두 dispatch 가 식별됨 (R67 §하단). 본 라운드는
> `DIALOG_INFO::DialogWindow_Proc` (@0x71b48) / `EventProc::Event_DialogWindow`
> (@0x6eb38) / `EventProc::Event_SituateDialogText` (@0x73030) 3 종을 ARM full
> disasm + jumptable decode 로 state machine + DIALOG_INFO struct layout 을 확정.

## 1. 핵심 발견

1. **`cmp r2, #7` = main state byte 0..7 jumptable** — `DialogWindow_Proc` 진입
   직후 `ldrsb r2, [r0, #0x2b]` 로 읽어서 `addls pc, pc, r2, lsl #2` 하는 8-way
   분기. R67 PASS 1 summary 가 추정했던 "state byte = +0x29" 는 **틀림**. 실제는
   **+0x2b** 가 main state 이고, +0x29 는 sub-step counter, +0x2d/+0x2f 는
   animation curve key.
2. **state 0, 1, 3, 6 은 트랜잭션 없는 polled idle states** — state 0 만 `r0=0`
   (게임 진행 가능), 1/3/6 은 `r0=1` (대화창 활성, 입력 대기). 즉 외부 코드는
   `DialogWindow_Proc()` 의 return 값으로 "busy" 만 검사한다.
3. **state 2, 4, 5, 7 은 4-step 애니메이션 phase** — 각 state 마다 별도 데이터
   pool (struct +0x10/+0x14/+0x18, +0x1c/+0x20/+0x24, +0x28/+0x2c/+0x30,
   +0x34/+0x38/+0x3c) 에서 sprite 좌표·해상도·color 를 ld 한 뒤 sub-step counter
   `+0x29` 를 +1 증가시킨다. counter==4 도달 시 `SetDialogWindow` 로 다음
   state 로 전환.
4. **state 5/7 만 `Graphic::RestorePal` + `Graphic::ChangeHSB` 호출** — 색 보정
   (fade-in 또는 텍스처 변형) 단계 = "fade transition" 으로 추정.
5. **`Event_DialogWindow` 는 DIALOG_INFO 와 무관하게 매 frame 호출되는 NPC face
   + textbox + name box renderer** — `cmp r3, #0xfd` 분기로 npc_id < 0xfd 일
   때만 `TextMgr::GetNpcNameText(r3)` + `GMenu::NameBox` 추가 그리기.
6. **`Event_SituateDialogText` 는 NPC 슬롯 record (+0xb0 byte index, 60B per
   record) 초기화 + `Interpreter::Strings::getString` 으로 텍스트 lookup +
   `Graphic::GetWidth/GetHeight` 로 화면 좌표 자동 계산** — sub-state +0xdf 가
   0/2/5 일 때 각각 다른 `SetDialogWindow(a, b)` 트랜잭션 트리거.

## 2. DIALOG_INFO struct layout (recovered)

| offset | type | 의미 | 근거 |
|---:|---|---|---|
| +0x24 | ptr | sprite/buffer handle (RestorePal/ChangeHSB 인자) | state 5/7 의 `ldr r1, [r4, #0x24]` 직후 두 helper 호출 |
| +0x28 | byte | direction flag (`cmp ip/lr, #0` → `rsbeq` 로 x 좌표 부호 반전) | state 4/5/7 의 `ldrb ip, [r0, #0x28]` |
| +0x29 | byte | **sub-step counter** (0→1→2→3→4) | state 2/4/5/7 진입 후 `add r2, r2, #1; strb r2, [r4, #0x29]`. 또한 `cmp r3, #4 / bne 0x71c10` 로 step 종료 검사 |
| +0x2a | byte | (예약/unused — 본 함수에서 직접 r/w 안 보임) | gap |
| +0x2b | **byte** | **main state** (0..7 jumptable index) | `ldrsb r2, [r0, #0x2b]; cmp r2, #7; addls pc, pc, r2, lsl #2` |
| +0x2c | byte (signed) | next state / dialog speaker hint | state 2 의 `ldrsb r1, [r4, #0x2c]; cmp r1, #5; beq 0x71ec0` 그리고 `SetDialogWindow(r0=this, r2=*+0x2c)` |
| +0x2d | byte | animation curve key A (sp[-0xc + (step*2)] 에서 ld 후 strb) | 각 phase 의 `ldrsb r5, [r1, #-0xc]; strb r3, [r4, #0x2d]` |
| +0x2f | byte | animation curve key B (sp[-0xb + (step*2)] 에서 ld 후 strb) | `ldrsb r1, [r1, #-0xb]; strb r1, [r4, #0x2f]` |
| +0x34 | u16 | dialog box x coord (animated; rsbeq 시 부호 반전) | `strh r3, [r4, #0x34]` (모든 phase) |
| +0x36 | u16 | dialog box y coord | `strh r1, [r4, #0x36]` |

**Phase data pool offsets** (struct +0x10..+0x3c, 4 phase × 12 byte 씩):

| state | data pool offsets | 호출 helper |
|---:|---|---|
| 2 | +0x10 / +0x14 / +0x18 | (없음, 좌표만 계산) |
| 4 | +0x1c / +0x20 / +0x24 | (없음, 좌표만 계산) |
| 5 | +0x28 / +0x2c / +0x30 | `Graphic::RestorePal` + `Graphic::ChangeHSB` |
| 7 | +0x34 / +0x38 / +0x3c | `Graphic::RestorePal` + `Graphic::ChangeHSB` |

(주의: 위 +0x2c 는 **phase data pool entry** 이고, struct field +0x2c "main state hint" 와는 다른 의미. struct offset 이 겹친 것은 우연 — phase 5 의 data pool 의 시작은 0x28 인데 +0x2c 위치는 데이터 word 의 2번째 요소다.)

## 3. State machine 전체 흐름

```
                       ┌──────────────────────────────┐
                       │ state 0 : INACTIVE (r0=0)    │
                       │  외부 코드: "대화 끝남"        │
                       └──────────────────────────────┘
                                  ▲
                                  │ SetDialogWindow(0, …)
                                  │
   ┌─── Event_SituateDialogText 호출 ─────────┐
   │ (text 셋업 + SetDialogWindow(1,2) 또는    │
   │  (4,2) 또는 (6,5))                       │
   │                                          ▼
┌──┴───────────┐  step=4  ┌─────────────────────────┐
│ state 2/4    │ ───────▶ │ state 1/3/6 : IDLE      │
│ FADE-IN      │          │  (r0=1, 외부=busy)      │
│ animation    │          └─────────────────────────┘
└──────────────┘                     │
        │ phase 2 의 +0x2c=5 ⇒       │ (외부 trigger:
        │ state 7 로 점프             │  버튼 입력 등)
        │ (코드 0x71ec0)              ▼
        │                  ┌──────────────────────────┐
        │ phase 4 의 +0x29=4 ⇒       │
        │ state 2 종료 (SetDialogWindow) │
        ▼                  ▼
┌─────────────────────────────────────┐
│ state 5/7 : FADE-OUT (HSB 변형)     │
│  RestorePal + ChangeHSB             │
│  step=4 → state 0 (또는 다음 단계)   │
└─────────────────────────────────────┘
```

**주요 정리**:
- main state byte (+0x2b) 는 **렌더 phase index**.
- sub-step (+0x29) 은 **0..4 의 animation tick** (phase 마다 4-frame transition).
- phase 마다 phase data pool (struct +0x10..+0x3c) 에서 좌표·HSB 인자를 ld.
- phase 2 종료 시 `+0x2c == 5` 면 phase 7 로 점프 (특수 transition).
- phase 5 종료 시 phase 2 의 finalize 와 동일 분기 (0x71cd0 = SetDialogWindow).

## 4. 외부 helper 함수 확정

| 주소 | 심볼 | 의미 |
|---:|---|---|
| 0x438e0 | `BFont::SetColorFixed(byte)` | 고정 텍스트 색 |
| 0x438e8 | `BFont::HanFontHeight()` | 한글 폰트 줄 높이 |
| 0x44370 | `BFont::DrawTextField(...)` | 텍스트 필드 그리기 (대사 본문) |
| 0x445b4 | `BFont::SetColor(int)` | 텍스트 색 |
| 0x52098 | `Graphic::GetFB()` | 프레임버퍼 획득 |
| 0x520c8 | `Graphic::GetWidth()` | 화면 가로 |
| 0x520d0 | `Graphic::GetHeight()` | 화면 세로 |
| 0x59400 | `Graphic::RestorePal(GbmImage*)` | 팔레트 복원 |
| 0x5f000 | `Graphic::ChangeHSB(GbmImage*, h, s, b)` | 색조/채도/명도 변환 |
| 0x6ab40 | **`DIALOG_INFO::SetDialogWindow(byte, byte)`** | state 전환 (main, sub) |
| 0x72f54 | `DIALOG_INFO::SetFacePosition(byte, byte)` | NPC 얼굴 위치 |
| 0x82248 | `GMenu::NameBox(...)` | NPC 이름 박스 |
| 0x8245c | `GMenu::DrawDialogBox(...)` | 대사창 박스 그리기 |
| 0x9e540 | `Interpreter::Strings::getString(id, *)` | 문자열 lookup |
| 0x1431a0 | `TextMgr::GetNpcNameText(id)` | NPC 이름 텍스트 |

## 5. `Event_DialogWindow` (@0x6eb38) 의 매 frame 렌더 순서

1. `BFont::SetColor(0xff000000 invert)` ⇒ 외곽선 색 셋업
2. `Graphic::GetFB()` ⇒ frame buffer 획득
3. NPC record (`+0xc0..+0xc8` 의 halfword 좌표 + `+0xd4` text ptr) 추출
4. `GMenu::DrawDialogBox(...)` ⇒ 검은 박스 그리기
5. `BFont::SetColor(...)` + `BFont::SetColorFixed(1)` 로 본문 색 셋업
6. `Graphic::GetFB()` + `BFont::DrawTextField(x, y, w, h, ..., text_ptr, ...)` ⇒ 대사 본문
7. (NPC 2 가 있는 경우 5-6 반복 — 두 번째 NPC 사이드)
8. `+0xb0 = npc_id` 가 `< 0xfd` 이면:
    - `Graphic::GetFB()` 다시 획득
    - `TextMgr::GetNpcNameText(npc_id)` 로 이름 텍스트 fetch
    - `GMenu::NameBox(x, y, w, h, ..., name_text, ...)` 로 이름 박스 그리기
9. 반환

(반복 호출되는 함수 — DialogWindow_Proc 의 phase 가 active 인 동안 frame 당 1회)

## 6. `Event_SituateDialogText` (@0x73030) — dialog 시작 트리거

서명 (mangled `Event_SituateDialogTextEhahh`):
```cpp
void EventProc::Event_SituateDialogText(
    unsigned char  npc_index,   // r1
    char           npc_slot,    // r2 — record array index
    char           font_color,  // r3
    unsigned char  string_id    // sp[0x28]
);
```

흐름:
1. record_base = `this + npc_slot * 0x3c`
2. record\[+0xb0\] = npc_slot 자체 (역참조용 backref)
3. record\[+0xbb\] = font_color (sl)
4. record\[+0xbc\] = 3 (text size — 한글 3-pixel 폭?)
5. record\[+0xbe\] = 1, +0xc0 = 0 (scroll counters)
6. `Interpreter::Strings::getString(string_id, &out_len)` → record\[+0xd4\] = ptr
7. `Graphic::GetWidth/Height()` 로 화면 크기 ld → record\[+0xcc, +0xce\] 계산
8. record\[+0xc6\] = +0xcc - 0x10, record\[+0xca\] = height - +0xce 등 좌표 계산
9. `DIALOG_INFO::SetFacePosition(record_offset, ...)` 호출
10. sub_state byte record\[+0xdf\] 검사:
    - `==0` → `SetDialogWindow(1, 2)`  (첫 dialog 시작)
    - `==5` → `SetDialogWindow(4, 2)`  (다른 종류 dialog 시작)
    - `==2` 그리고 `+0xd8 != 0` → `SetDialogWindow(6, 5)`  (page 넘김 등)
    - 그 외 → 좌우 배치만 셋업하고 종료
11. string_id == 0xff 면 `SetDialogWindow` 안 부르고 즉시 종료 (placeholder)

## 7. R67 → R68 정정 사항

| 항목 | R67 PASS 1 추정 | R68 확정 |
|---|---|---|
| main state byte | DIALOG_INFO + 0x29 | DIALOG_INFO + **0x2b** (jumptable index) |
| +0x29 의미 | "state byte" | **sub-step counter** (0..4 animation tick) |
| +0x2d / +0x2f | "sub state" | **animation curve key A/B** (sp 의 phase data 에서 ld) |
| `cmp r2, #7` | "state 7가지" | **state 0..7 총 8개** (state 0=inactive 포함) |
| `cmp r1, #5` | (의미 불명) | state 2 finalize 시 `+0x2c == 5` 면 state 7 로 fast-jump |

## 8. Godot 매핑 권장

`apps/hero5-godot/.../scenes/dialog_box.gd` (또는 등가 NPC dialog 컴포넌트) 에
다음 상수 추가 (logical state 매핑):

```gdscript
# DIALOG_INFO::DialogWindow_Proc 의 main state byte (+0x2b) 값
const DIALOG_STATE_INACTIVE       = 0  # 대화 종료, 외부 입력 받음
const DIALOG_STATE_IDLE_ACTIVE    = 1  # 대화 활성 (busy 표시)
const DIALOG_STATE_FADE_IN_A      = 2  # phase A (data pool +0x10..)
const DIALOG_STATE_IDLE_ACTIVE_2  = 3  # state 1 alias
const DIALOG_STATE_FADE_IN_B      = 4  # phase B (data pool +0x1c..)
const DIALOG_STATE_FADE_HSB_A     = 5  # phase C (RestorePal+ChangeHSB)
const DIALOG_STATE_IDLE_ACTIVE_3  = 6  # state 1 alias
const DIALOG_STATE_FADE_HSB_B     = 7  # phase D (RestorePal+ChangeHSB)

# sub-step counter (+0x29) max value before phase finalize
const DIALOG_SUBSTEP_FINAL = 4

# Event_SituateDialogText 의 +0xdf sub_state 값별 SetDialogWindow 인자
const DIALOG_TRIGGER_FIRST  = Vector2i(1, 2)  # sub_state==0
const DIALOG_TRIGGER_TYPE2  = Vector2i(4, 2)  # sub_state==5
const DIALOG_TRIGGER_PAIR   = Vector2i(6, 5)  # sub_state==2 + paired NPC
```

Godot 구현은 `cmp r3, #4 / bne return_busy` 로직만 흉내내면 됨 — 즉 phase 가
active 인 동안 4 frame transition 후 다음 state 로 자동 진입.

## 9. 잔여 미해결 / 다음 라운드

1. `+0x28` direction flag 의 정확한 의미 — left/right 두 NPC 의 face 좌우 대칭?
2. phase data pool (`DIALOG_INFO + 0x10..+0x3c`) 의 4-step animation curve 가
   per-NPC 인지 hardcoded 인지 — data origin (pc-relative pool 의 base) 추적
   필요.
3. `+0x28` 옆 byte (`+0x2a`) 가 정말 unused 인지 — write 가 본 함수에 없지만
   다른 caller 가능.
4. `SetDialogWindow` (@0x6ab40) 의 구현 정밀 분석 (R68 에선 호출자 측만 봄):
   인자 `(byte main, byte sub)` 중 sub 의 의미.
