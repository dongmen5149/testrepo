# Hero5 Formula VM 변수 사전 (var_id → struct.field)

원본: `tools/h5_extract_formula_vars.py` → `work/h5/analysis/formula_var_dict.tsv`
디스어셈블 대상: `Formula::getValFunc` (0x758d0, 6372B, 254-entry switch).

각 var_id 는 Formula 바이트코드의 즉시값 또는 변수 fetch 시 사용. calc/calcByFormula
에서 callee-saved 레지스터로 전달되는 컨텍스트:
- **`r5` = skill** (HeroSkillInfo*)
- **`r6` = defender** (CHAR*)
- **`fp` = item** (ItemBase*)
- **`r7` = defender** (or attacker if defender is player — auto-flip)
- **`sl`, `sb`** = HeroSkillInfo 보조 포인터들

---

## var_id 매핑 (전체 254개 중 의미 있는 240+)

### 1-60: skill struct 필드 (`HeroSkillInfo`)
| var_id | offset | 크기 | 추정 의미 |
|---:|---:|---|---|
| 1 | +0x00 | 4B (ldr) | skill_id |
| 2 | +0x04 | 4B (ldr) | unknown ptr/handle |
| 3 | +0x08 | 2B (s16) | stat[0] |
| 4-19 | +0x0a..+0x28 | 2B 각각 | stat[1..15] |
| 20-31 | +0x66..+0x7c | 2B | stat[16..27] |
| 32-39 | +0x7e..+0x8c | 2B | stat[28..35] |
| 40 | +0x90 | 4B (ldr) | special |
| 41-47 | +0x98..+0xa6 | 2B | stat[36..42] |
| 48-60 | +0xa8..+0xb6 | 2B | stat[43..55] |

### 58-66, 111-160: 전역 state (GOT 경유)
패턴: `ldr r2, [pc, #X] ; mov r3, #0x1440 ; add r3, r3, #0x34 ; ldr r2, [r4, r2] ; ldr/ldrsh r0, [r2, r3]`

전역 singleton 포인터 (예: GameState, HeroData, BagItem) 의 포인터를 GOT 에서 받아,
구조체 내 offset (0x1474 + delta) 의 필드를 읽음. delta 는 PC-relative immediate 의
하위 비트로 인코딩.

→ 정확한 의미는 GOT entry 풀이가 필요하나, 추정: **player.gold / player.exp /
player.lv / player.cur_hp / player.max_hp / player.cur_mp / player.max_mp /
player.atk / player.def / player.dex / hero level** 등.

- **id 58-60**: 4B fields (likely u32 total values: gold, exp, ?)
- **id 61-110**: 1-2B fields (level, stat, achievement counters)
- **id 111-160**: continued — 더 많은 player/hero state.

### 161-167: 짧은 거리 GOT (게임 모드 플래그?)
2 entries 사용 (id=163, 252). `ldrb r0, [sl, #0x22d/0x27d]` — sl 이 skill 포인터의
구조체 안 +0x22d / +0x27d 필드 (1B). 추정: **skill type/category bitmask**.

### 168-182: item struct (`ItemBase*`, fp 레지스터)
| var_id | offset | 크기 | 추정 의미 |
|---:|---:|---|---|
| 168 | +0x0e | s16 | item.atk_value |
| 169 | +0x12 | s16 | item.def_value |
| 170 | +0x16 | s16 | item.stat[0] |
| 171 | +0x1a | s16 | item.stat[1] |
| 172 | +0x20 | s16 | item.stat[2] |
| 173 | +0x24 | s16 | item.stat[3] |
| 174-177 | +0x44..+0x47 | s8 | option byte (4슬롯) |
| 178-180 | +0x48..+0x4c | s16 | option value |
| 181 | +0x4e | s8 | item flag |
| 182 | +0x50 | s16 | item field |

### 184-191: HeroSkillInfo 깊은 offset (sl, sb 레지스터)
- id=184: `[sb, +0x156]` (sb 의 +0x156 — 4B align 후 0x158)
- id=185: `[sb, +0x158]`
- id=186-188: `[sb, +0x165 ~ 0x168]` (1B fields — flag/category)
- id=190-191: `[sb, +0x16e/0x170]`

→ sb 가 또 다른 HeroSkillInfo 변종 포인터 (skill-equip-spirit?). 구체적 의미 미상.

### 192-251: defender struct (CHAR* 또는 BATTLER*, r6 레지스터)
**skill 영역과 거의 동일한 offset 구조 (0x00, 0x04, 0x08-0x28, 0x66-0xb6).**
| var_id | offset | 크기 | 의미 |
|---:|---:|---|---|
| 192 | +0x00 | 4B | (object header / type) |
| 193 | +0x04 | 4B | (vtable 또는 sprite ptr) |
| 194-209 | +0x08..+0x28 | 2B | defender stat[0..15] |
| 210-251 | +0x66..+0xb6 | 2B | defender 추가 stats |

> ⚠ skill (var_id 1-60) 과 defender (var_id 192-251) 가 **같은 offset 구조**. 따라서
> `HeroSkillInfo` 와 `CHAR/BATTLER` 가 부분적으로 동일한 stat 블록을 공유 (Mixin?).

### 251-252: 동적 OBJECT 타입 분기
- id=251: `mov r0, r7 ; bl OBJECT::GetObjectType` → 객체 타입 반환.
- id=252: 위 + offset 0x27d 1B 읽기.

### 0, 248-253: 기본 / 특수 케이스
- id=0: `r0 = 0; return` (기본값).
- id=248-249: 음수 상수 반환 (`mvn r0, #0x31` → `r0 = -50`).
- id=250+: 다양한 fallback.

---

## 활용 가이드

calc_*.dat 평문이 있으면 (DES 복호 후) 각 공식의 바이트코드를 디스어셈블해서:

```
[u8 body_len, u8 body_count, 4B lower_bound, 4B upper_bound,
 body_count × {u8 var_id_or_op, 4B operand}]
```

각 instruction 의 첫 바이트가 var_id (이 표 참조) 면 fetch, 아니면
operator (0x11 ADD / 0x12 SUB / 0x13 MUL / 0x14 DIV / 0x15 MOD / 0x16 XOR).
operand 4 바이트는 즉시값 (스택에 push).

> ⚠ 정정 (2026-05-09): 위 opcode 가 실제 jumptable 기반 정확한 매핑.
> 초기 추정과는 반대였음 — `tools/h5_formula_disasm.py` 가 186 공식 모두 정상 파싱
> (size mismatch 0 건) 으로 검증.

또한 첫 바이트 `op` 의 처리:
- `op == 0`: 4B operand 를 그대로 스택에 push (즉시값)
- `op == 0x0c`: 4B operand 를 var_id 로 보고 `getValFunc` 호출, 결과 push
- 그 외 (0x10 비트 미설정): 사실상 무시 (`getNumberInStack` 가 0 반환)

→ 각 공식이 어떤 stat 을 어떻게 조합하는지 100% 추출 가능.

**~~현재 격차~~ 해결 (2026-05-09)**: DES 복호화 완성. `tools/h5_des.py` 가 평문을
돌려주고, `tools/h5_formula_disasm.py` 가 186 공식 전부 디스어셈블 (`work/h5/analysis/
formulas_disasm.txt`). 자세히 [`DES_VARIANT.md`](DES_VARIANT.md).

원인: 비표준 DES 라기보단 **표준 DES 의 S1[3][10] 한 entry (3→2) 만 수정** 된 변종.
+ `MX_desEncrypt` / `MX_desDecrypt` 의 키 reversal + input swap 호출 규약이 직관 반대로
보였을 뿐 결국 표준 DES encrypt/decrypt 와 동치.

---

## 후속 단계

1. ✅ **DES 복호화 완성** — `tools/h5_des.py` (S1[3][10]=2 수정), MD5 검증 통과.
2. **GOT 매핑**: 전역 singleton 위치 (id 58-160 의 PC-relative 풀이) 에서 정확한
   필드명 (player.gold/exp/atk/def 등) 식별 — 미해결.
3. ✅ **calc_pl/en/sk.dat 디스어셈블러** — 186 공식 모두 사람이 읽을 수 있는 infix
   표현으로 dump 완료.

남은 작업: GOT entry → 전역 변수 의미 매핑 + battle_system.gd 의 Formula VM 평가기 구현.
