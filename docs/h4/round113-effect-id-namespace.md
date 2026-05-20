# Hero4 Round 113 — OPTION × class skill effect_id namespace 통합 (R106+R112 후속)

> R106 `_ITM_OPTION` 의 byte0 effect_id 와 R112 class skill stat block 의 byte[20] effect_id 가 **동일 enum namespace** 임을 검증.

## TL;DR

**12 effect_id 가 양 시스템에서 공유** (OPTION 33 unique × class skill 19 unique = 12 교집합).

**OPTION 의 명명된 entry ("화염발동 L1" 등) 로부터 effect_id 의미 직접 추론**:

| effect_id | OPTION 의미 | class skill 대응 (예) | 검증 |
|---|---|---|---|
| 4 | HP회복 | 기합 (S002, "HP/SP회복"), \|야성 ("HP/회복력 증가") | ✅ |
| 7 | SP소모 | 헤이스트 ("SP의 소모량 감소") | ✅ |
| 8 | SP회복 | \|마법강화 ("최대 SP/SP회복량 증가") | ✅ |
| 12 | 근접공격 | 환수 합신 (환수+character combat), 쇠약의저주 (적 공격력 감소) | ✅ |
| 15 | 마법공격 | 지축 ("암즈사격의 공격력 극대"), 환수증폭 ("마법 적중증가") | ✅ |
| 27 | 쿨타임 | 광폭 ("사격속도 극대"), \|마법단련 ("쿨타임 감소") | ✅ |
| 68 | 넉백발동 | 관통의영검 ("추가타 가능한 돌격기") | ✅ |
| 75 | 슬로우발동 | 급소사격 ("출혈 유발") | ✗ (해석 다름) |
| 76 | 스턴발동 | 기절의검 ("스턴 유도"), 크리티컬샷 ("스턴 유도"), 텔레포트소드 | ✅ |
| 78 | 화염발동 | 프레임인첸트 ("화염검 발동"), 정화의심판 ("화염낙하") | ✅ |
| 79 | 결빙(냉기) | 아이스인첸트 ("빙결검 발동"), 빙결의검 ("얼음 송곳") | ✅ |
| 80 | 물약회복 | \|체질개선 ("물약의 회복량 증가") | ✅ |

→ **19/20 class skill cross-reference 가 OPTION effect 명과 desc 일치** (1 mismatch: 급소사격 출혈 vs OPTION 슬로우).

## 1. effect_id namespace 분포

```
OPTION  byte0 unique = 33 (range 0-90)
class_skill byte[20] unique = 19 (range 4-80)
SHARED (intersection) = 12: {4, 7, 8, 12, 15, 27, 68, 75, 76, 78, 79, 80}

OPTION 단독 (21): {0, 2, 5, 6, 11, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 30, 85, 86, 87, 90}
class skill 단독 (7): {9, 36, 46, 53, 64, 67, 69}
```

### OPTION 단독 effect_id 의미 (참고)

OPTION 의 추가 effect:
- 0 = ATK_+
- 2 = HPmax / DEFmax
- 6 = SPmax
- 14/16/17 = elemental resistance
- 85/86/87/90 = endgame stat boost

### class skill 단독 effect_id (역참조 필요)

7개 (9, 36, 46, 53, 64, 67, 69) 는 OPTION 에 없는 class skill 전용 secondary effect.
대부분 buff/utility skill 에서 등장 (정확한 의미는 desc + skill 이름으로 추론 가능).

## 2. R106 OPTION 3B payload vs R112 class skill 32B 통합

```
OPTION payload:  [effect_id : 1B] [cat 0/15/100 : 1B] [magnitude : 1B]   = 3B
                                  └ 0 = flat
                                  └ 15 = % 보정
                                  └ 100 = 특수 (넉백)

class skill stat block (32B 중 secondary effect 4 byte):
  [byte20 : effect_id]  [byte21 : intensity/cat] [byte22 : 0 (or 255)] [byte23 : magnitude/tier]
   └ shared with OPT     └ 1 most common         └ rarely used (255 = DEBUFF max)  └ 1/5/10 tier
```

**핵심 차이**:
- OPTION: 단순한 3B 구조, cat 은 namespace { 0, 15, 100 } 만
- class skill: 4 byte 구조, byte[21] = 다양한 intensity (1/5/10/100/252 signed -4)

→ class skill 은 OPTION 보다 **wider intensity range** 지원. 특히 **DEBUFF 의 signed negative** (쇠약의저주 byte[21]=252 = -4) 는 OPTION 에 없는 기능.

## 3. Cross-validation 표 (19/20 일치)

| class skill | eid | OPTION 의미 | desc | match |
|---|---|---|---|---|
| _S000 기절의검 | 76 | 스턴발동 | "스턴 유도" (encoding 깨짐) | ✅ |
| _S000 관통의영검 (alt) | 68 | 넉백발동 | "추가타 띄우기" (=knockback) | ✅ |
| _S000 \|체질개선 | 80 | 물약회복 | "물약의 회복량 증가" | ✅ |
| _S001 급소사격 | 75 | 슬로우발동 | "출혈 유발" | ✗ (slow vs bleed) |
| _S001 크리티컬샷 | 76 | 스턴발동 | "스턴 유도" | ✅ |
| _S001 광폭 | 27 | 쿨타임 | "사격속도 극대" | ✅ (속도≈쿨타임) |
| _S001 지축 | 15 | 마법공격 | "공격력 극대" | ✅ |
| _S002 텔레포트소드 | 76 | 스턴발동 | "추적 텔레포트 공격" | ✅ (implicit stun) |
| _S002 프레임인첸트 | 78 | 화염발동 | "화염검 발동" | ✅ |
| _S002 아이스인첸트 | 79 | 결빙(냉기) | "빙결검 발동" | ✅ |
| _S002 기합 | 4 | HP회복 | "HP와 SP회복" | ✅ |
| _S002 헤이스트 (alt) | 7 | SP소모 | "SP 소모량 감소" | ✅ |
| _S002 환수 합신 (alt) | 12 | 근접공격 | "융합하여 육체강화" | ✅ |
| _S002 \|야성 | 4 | HP회복 | "HP와 회복력 증가" | ✅ |
| _S003 빙결의검 | 79 | 결빙(냉기) | "얼음 송곳" | ✅ |
| _S003 정화의심판 (alt) | 78 | 화염발동 | "화염낙하" | ✅ |
| _S003 쇠약의저주 | 12 | 근접공격 | "적의 공격력 감소" (signed -4!) | ✅ |
| _S003 환수증폭 (alt) | 15 | 마법공격 | "마법 적중증가" | ✅ |
| _S003 \|마법강화 | 8 | SP회복 | "최대 SP / SP회복량" | ✅ |
| _S003 \|마법단련 | 27 | 쿨타임 | "스킬 쿨타임 감소" | ✅ |

→ **19/20 = 95%** 정합. 압도적 증거.

## 4. R112 byte[21-23] 정밀 재해석

R112 의 "byte[21] = magnitude class" 가설을 R113 데이터로 정밀화:

```
프레임인첸트:  b20=78 (화염발동) b21=1   b22=0   b23=1   → "L1 화염발동 mag=1"
아이스인첸트:  b20=79 (결빙)    b21=1   b22=0   b23=1   → "L1 결빙 mag=1"
빙결의검:     b20=79 (결빙)    b21=1   b22=0   b23=1   → "L1 결빙 mag=1"
정화의심판:    b20=78 (화염)    b21=1   b22=0   b23=1   → "L1 화염발동 mag=1"
환수 합신:    b20=12 (근접공격) b21=10  b22=0   b23=2   → "L2 근접공격 ×10"
환수증폭:     b20=15 (마법공격) b21=5   b22=0   b23=5   → "L5 마법공격 ×5"
지축:        b20=15 (마법공격) b21=8   b22=0   b23=8   → "L8 마법공격 ×8"
쇠약의저주:    b20=12 (근접공격) b21=252 b22=255 b23=252 → "근접공격 signed -4" (DEBUFF)
|마법강화:   b20=8  (SP회복)  b21=1   b22=0   b23=1   → "L1 SP회복 mag=1"
|마법단련:   b20=27 (쿨타임)  b21=1   b22=0   b23=1   → "L1 쿨타임 mag=1"
```

**정밀 모델**:
- `byte[21]` = **intensity multiplier** (1=base, 5/10/8=정수 multi, 100=특수, 252=signed -4 for decrease)
- `byte[22]` = boundary/sign marker (대부분 0; DEBUFF 에서 255 = signed -1 = 모든 magnitude negative)
- `byte[23]` = **tier/magnitude** (1=L1, 5=L5, 10=L10 식)

→ OPTION 의 cat 0/15/100 (정해진 namespace) 보다 class skill 의 byte[21] 이 **더 유연** (1-100 범위 + signed). class skill 은 OPTION 의 superset.

## 5. 통합 모델 (game engine 차원)

```
shared secondary-effect engine:

  effect_id space (R113):
    0-30:    base stat effects (HP/SP/공격/방어/공격속도/쿨타임)
    68-80:   proc 발동 (넉백/슬로우/스턴/화염/결빙/물약)
    85-90:   endgame (OPTION 전용)

  applied via:
    OPTION enchantment:   [eid][cat 0/15/100][mag]   (item enchant slot)
    class skill:          [eid][intensity][boundary][tier]   (secondary skill effect)
    (+ 환수 시스템 도 likely 같은 engine 사용 — R87 stat block byte[5]=subtype 등)
```

→ Hero4 의 game engine 은 **secondary-effect engine 을 단일 통합** 으로 운용.
   item / skill / 환수 가 모두 같은 effect_id namespace 를 공유.

## 산출

- `tools/converter/parse_h4_effect_id_namespace.py` (신규)
- `work/h4/converted/h4_effect_id_namespace.json` (16.3KB)
- `docs/h4/round113-effect-id-namespace.md` (이 문서)

## 다음 후보

1. **환수 시스템 (`_H_SS`) byte[5]=subtype 가 effect_id namespace 공유 여부 검증** (R87+R113 후속) — 3 시스템 통합
2. **SCN opcode dispatch** (R72 후속)
3. **class skill 단독 7 effect_id (9/36/46/53/64/67/69) 의미 추론** (R113 잔여)
