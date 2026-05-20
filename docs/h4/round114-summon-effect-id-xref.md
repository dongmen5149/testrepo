# Hero4 Round 114 — 환수 stat block × effect_id namespace 통합 (R87+R89+R113 후속)

> R113 의 effect_id namespace 가 **환수 시스템 (`_H_SS`)** 까지 확장됨을 검증.
> **3-system unified secondary-effect engine** 확정.

## TL;DR

**R89 의 "strength" 라벨 정정**: 환수 STATUS_PROC byte[7] 와 AURA byte[7] 는 단순한 strength 값이 아니라 **OPTION/class skill 과 동일 effect_id namespace**.

**전체 일치율 13/14 = 92.9%** (1 단독 = 망각의저주 boss-only effect_id 66).

| template/subtype | byte[7] 의미 | byte[11] 의미 |
|---|---|---|
| ACTIVE_ATTACK | byte[5]=2 element const, byte[7]=speed | — |
| STATUS_PROC (byte[5]=7) | **effect_id** (75/76/85/86) ✓ | — |
| AURA (byte[5]=11) | **effect_id** (2/8/15/16/25) ✓ | **secondary effect_id** (6/17/30) ✓ |
| SHIELD (byte[5]=6) | literal shield strength (63) | **secondary effect_id** (17 마법방어) ✓ |
| PASSIVE (byte[5]=12) | skill_id (91-94, 별도 namespace) | — |

## 1. STATUS_PROC 검증 — 4/5 매칭

```
베놈   맹독         byte[7]= 85 = 중독 ✓        (poison status proc)
헤지호그 되돌리기      byte[7]= 86 = 데미지반사 ✓   (damage reflect)
그래비티 슬로우        byte[7]= 75 = 슬로우발동 ✓   (= OPTION 슬로우발동, class skill 급소사격)
쇼커   스턴         byte[7]= 76 = 스턴발동 ✓     (= OPTION 스턴발동, class skill 기절의검/크리티컬샷)
(boss) 망각의 저주    byte[7]= 66 = (환수 단독)    boss-only entry
```

5 환수의 핵심 status proc 모두 namespace 일치. R89 가 "strength=85/86/75/76" 으로 라벨한 byte[7] 은 사실 **effect_id**.

## 2. AURA 검증 — 5/5 매칭 + 3/3 secondary 매칭

```
베놈     저주의 오러   byte[7]= 25 = 저주          (curse aura)
헤지호그   강화의 오러   byte[7]=  2 = HPmax         (HP boost) + 2nd byte[11]=6 = Spmax
그래비티   마법의 오러   byte[7]= 15 = 마법공격       (magic atk boost) + 2nd byte[11]=30 = 저항
쇼커     마력의 오러   byte[7]=  8 = SP회복         (SP regen boost)
세이프가드  보호의 오러   byte[7]= 16 = 물리방어       (defense boost) + 2nd byte[11]=17 = 마법방어
```

5 환수 AURA 효과가 **OPTION enchantment 명명과 정확히 일치**:
- 강화의 오러 = HPmax + Spmax buff (HP/SP 동시 강화)
- 마법의 오러 = 마법공격 + 저항 buff (magic dmg + resist)
- 보호의 오러 = 물리방어 + 마법방어 buff (dual defense)

→ 3 환수 (헤지호그/그래비티/세이프가드) 가 secondary buff 동반 (R89 의 가설 정밀화).

## 3. SHIELD 검증 — byte[11] secondary 매칭

```
세이프가드 실드 byte[7]=63 (literal) byte[11]=17 = 마법방어 ✓
```

byte[7]=63 은 effect_id namespace 에 없는 값 → **literal shield strength** (R89 와 일치).
byte[11]=17 = 마법방어 secondary buff → R113 namespace 와 일치.

## 4. PASSIVE 검증 — skill_id 별도 namespace

```
마법력강화 byte[7]=91
교감도강화 byte[7]=92
체력강화   byte[7]=93
정신강화   byte[7]=94
```

byte[7]=91-94 는 effect_id namespace 에 없음. 별도 **skill_id namespace** (이 4개는 글로벌 소환사 패시브 ability).

## 5. 3-System Unified Effect Engine

```
┌──────────────────────────────────────────────────────────┐
│           Hero4 Secondary-Effect Engine (R113+R114)       │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  effect_id namespace (33 unique IDs in OPTION):           │
│   0-25 base stat (HP/SP/공격/방어/저항/명중/회피 등)        │
│   26-30 utility (쿨타임/저주/저항)                          │
│   68-90 proc 발동 (넉백/슬로우/스턴/화염/결빙/물약/중독/반사)│
│                                                            │
│  Used by 3 systems:                                        │
│   1. OPTION (item enchantment) — byte[0] = effect_id      │
│   2. class skill (32B stat block) — byte[20]              │
│   3. 환수 (23B stat block):                                │
│      - STATUS_PROC (byte[5]=7)  → byte[7]                 │
│      - AURA        (byte[5]=11) → byte[7], byte[11]       │
│      - SHIELD      (byte[5]=6)  → byte[11] (2nd only)     │
│      - ACTIVE_ATTACK / PASSIVE: 별도 namespace             │
│                                                            │
│  Cross-validation match rate:                              │
│   class skill ↔ OPTION:   19/20 (95.0%)                   │
│   환수 STATUS_PROC ↔ OPTION: 4/5 (80.0%, 1 boss 단독)      │
│   환수 AURA ↔ OPTION:        5/5 (100.0%)                 │
│   환수 secondary ↔ OPTION:   4/4 (100.0%)                 │
│   TOTAL:                     32/34 (94.1%)                │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

## 6. R89 정정

| R89 가설 | R114 정정 |
|---|---|
| STATUS_PROC byte[7] = strength (값 85/86/75/76 raw) | **effect_id** (중독/반사/슬로우/스턴) — OPTION namespace 공유 |
| AURA byte[7] = aura strength | **effect_id** (HPmax/SP회복/마법공격/물리방어/저주) — OPTION namespace 공유 |
| AURA byte[11] = secondary value | **secondary effect_id** (Spmax/저항/마법방어) — OPTION namespace 공유 |
| SHIELD byte[11] = secondary value | **secondary effect_id** (마법방어) — OPTION namespace 공유 |
| PASSIVE byte[7] = skill_id 91-94 | (확정 유지 — 별도 namespace) |

## 7. R113 잔여: class skill 단독 7 effect_id (9/36/46/53/64/67/69)

R113 에서 class skill 만 사용하는 7 effect_id 의 의미는 R114 환수 데이터로도 추가 정보 없음 (환수에서도 사용 안 함).

추정 (class skill desc 기반):
- 53 = 정화의장벽 (S003 TRAP) → 영역/장벽
- 67 = 더블암즈샷 (S001 MULTI) → 다단공격
- 69 = 회전의영검 (S000 AOE) → 범위공격
- 9 / 36 / 46 / 64 = ?

→ class skill 전용 mechanic effect (item enchantment 으로 부여 불가).

## 산출

- `tools/converter/parse_h4_summon_effect_id_xref.py` (신규)
- `work/h4/converted/h4_summon_effect_id_xref.json` (11.3KB)
- `docs/h4/round114-summon-effect-id-xref.md` (이 문서)

## 다음 후보

1. **SCN opcode dispatch** (R72 후속) — BSDAT body opcode 와 SCN bytecode 매핑
2. **class skill 단독 effect_id 9/36/46/64 의미 정밀화** — R113+R114 잔여
3. 사용자 트랙: Phase C Step 4d, 원작 UI 이식
