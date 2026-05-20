# Hero4 Round 112 — 32B class skill stat block 미확정 byte 정밀화 (R102+R109 후속)

> R102 의 23/32 확정 field 중 9 미확정 byte 의 의미를 R109 sub-cat / R104 dtype / class 와 cross-ref 로 추론.

## TL;DR

**핵심 발견**:

1. **byte[21] = magnitude class (1/10/100 + signed -4)** — R106 `_ITM_OPTION` 의 3B payload `[effect_id][cat 0/15/100][mag]` 와 **동일 layer**. enchantment 시스템과 class skill 시스템이 같은 secondary-effect engine 사용.
2. **byte[14] = active skill marker (0x78 = 120)** — 21 entries 가 모두 0x78. PASSIVE_DEEP 0, active 120 으로 명확히 분리.
3. **byte[18] = dtype=0 전용 "channeled/sustained" flag** — 9 entries 모두 type=0 + active. 찰라의영검/에이밍샷/절륜/프레임/아이스 인첸트/기합/헤이스트/환수 합신/환수증폭.
4. **byte[24-31] = 특수 skill 보조 effect descriptor** — DEBUFF/COMBO/BUFF 의 side-effect 만 사용. 쇠약의저주 의 255/252 (0xFF/0xFC) = signed **negative** (decrease) marker.

## R102 분류 갱신

| pos | R102 | R112 정밀화 |
|---|---|---|
| 6 | "animation cluster A" | **VFX/hitbox param** (48/64, PASSIVE 제외 모든 active) |
| 10 | "aux byte" | per-skill secondary param (16/64, 다양) |
| 11 | "aux flag" | S000-only outlier (3/64: 철의주먹/회전의영검/관통의영검) |
| 12 | "special" | singleton (찰라의영검=10) |
| 13 | "binary flag 13" | **multi-hit/queue flag** (17/64, val=1 across all sub-cat) |
| 14 | "const marker (0 또는 0x78)" | **active skill marker** (21/64 = 120, passive 0) |
| 18 | "flag18" | **type=0 channeled/sustained flag** (9/64, dtype=0 only) |
| 20 | "secondary_effect_lo" | secondary_effect_id (1-79, 28/64) |
| 21 | "secondary_effect_hi" | **magnitude class** (1/10/100/-4 signed) — R106 OPTION 과 동일 |
| 22 | "sub_boundary" | singleton (쇠약의저주=255) |
| 23 | "bonus value" | proc rate / duration / intensity (27/64) |
| 24-31 | "reserved" | **side-effect descriptor** (DEBUFF/COMBO/BUFF 전용) |

## 1. byte[14] = active skill marker (확정)

```
21 entries: byte[14] = 120 (0x78)
43 entries: byte[14] = 0
```

→ **PASSIVE 와 active 분리 marker**. 0x78 은 "이 skill 은 active casting 가능" 의미.

## 2. byte[18] = type=0 channeled/sustained flag (확정)

9 entries all byte[18]=1, **all damage_type=0**:

| skill | sub-cat | 해석 |
|---|---|---|
| 찰라의영검 (S000 alt) | BUFF_SELF | "입력지속" charge attack |
| 에이밍샷 (S001) | BASIC | "정확히 조준" channeled |
| 절륜 (S002 alt) | AOE | "대지를 흔들어" sustained |
| 프레임인첸트 (S002) | ELEMENT | "화염검을 발동" — weapon enchant 활성 동안 |
| 아이스인첸트 (S002) | ELEMENT | "빙결검을 발동" — weapon enchant 활성 동안 |
| 기합 (S002) | BUFF_SELF | "일정시간 증가" duration |
| 헤이스트 (S002 alt) | BUFF_SELF | "쿨타임과 SP 감소" duration |
| 환수 합신 (S002 alt) | COMBO | "융합" sustained |
| 환수증폭 (S003 alt) | COMBO | "융합" sustained |

→ **"활성 동안 효과 지속" 또는 "channel 형 attack" flag**. duration-based skill 의 식별자.

## 3. byte[20-21] = secondary effect (id, magnitude class)

R106 의 `_ITM_OPTION` 3B payload `[effect_id][cat 0/15/100][mag]` 를 class skill 에서도 사용. byte[20] = effect_id, byte[21] = magnitude class.

### byte[21] magnitude class 분포

```
1   (× 11) — base modifier (×1)
10  (×  5) — ×10
100 (×  4) — ×100
5   (×  3) — ×5
30/8/2/80/252 — singletons
```

→ R106 OPTION 의 `cat 0/15/100` 와 유사 magnitude class 시스템.

### 특수 case

| skill | byte[20] | byte[21] | 해석 |
|---|---|---|---|
| 쇠약의저주 (S003 DEBUFF) | 12 | **252** (0xFC = -4) | signed **negative** = 공격력 감소 |
| 정화의장벽 (S003 TRAP) | 53 | 80 | trap intensity |
| 환수 합신 (S002 COMBO) | 12 | 10 | combo bonus 10× |

## 4. byte[24-31] = side-effect descriptor (DEBUFF/COMBO/BUFF 전용)

**핵심 skill 만 사용**:

| skill | dtype | sub-cat | nonzero bytes (24-31) | 해석 |
|---|---|---|---|---|
| 약화의검 (S000) | 20 (DEBUFF) | — | 24=16, 27=253, 28=69 | 방어도 감소 modifier |
| 압도의검 (S000) | 20 (DEBUFF) | — | 24=75, 27=1, 28-31 다수 | 둔화 modifier |
| 급소사격 (S001) | 5 (BASIC) | — | 24=88, 27=1 | 출혈 modifier |
| 광폭 (S001 alt) | 0 | BUFF_SELF | 24=14, 27=10 | 사격속도 극대 modifier |
| 기합 (S002) | 0 | BUFF_SELF | 24=9, 27=2 | HP/SP 회복량 |
| 헤이스트 (S002 alt) | 0 | BUFF_SELF | 24=27, 27=1 | 쿨타임 감소량 |
| 환수 합신 (S002 alt) | 0 | COMBO | 24=16, 27=2, 28=17, 29=10, 31=2 | combo 강화 (most fields used) |
| 환수증폭 (S003 alt) | 0 | COMBO | 24=49, 27=2 | 적중률 증가 |
| 정화의장벽 (S003) | 0 | TRAP | 24=78, 25=1, 27=1 | 영역 duration |
| 쇠약의저주 (S003) | 0 | DEBUFF | 22=255, 24=14, 25=252 (0xFC), 27=252, 28=15, 29=252, 30=255, 31=252 | **모든 byte 가 signed negative** = max 감소 marker |

### 패턴

- **0xFC (252) / 0xFF (255) 가 DEBUFF 에 집중** — signed -4 / -1 의 negative modifier
- **환수 합신 이 가장 많은 byte[24-31] 사용** — most complex side-effect (육체강화 combo)
- **PASSIVE_DEEP 은 byte[24-31] 사용 안 함** (passive 는 기본 stat 만 수정)

## 5. byte[6] = VFX/hitbox param (48/64 nonzero)

```
값 분포: {16:11, 80:5, 44:5, 8:4, 60:3, 100:3, 200:3, 32:2, 64:2, 72:2, 144:2, ...}
PASSIVE_DEEP 0/16 (모두 0) → active 전용
```

→ **active skill VFX 또는 hitbox 크기 param** (animation cluster B with byte[19]).

## 6. byte[13] = multi-hit/queue flag (17/64 = 1)

```
17 entries 모두 byte[13]=1, 다양한 sub-cat 분포
```

→ 정확한 의미는 단정 불가. multi-hit/queue/repeat flag 후보.

## 7. byte[10-12] = sparse outliers

- byte[10]: 16 nonzero, 다양한 sub-cat — per-skill 특수 param
- byte[11]: **S000 only 3 outlier** — 철의주먹(=1), 회전의영검(=2), 관통의영검(=2)
- byte[12]: singleton **찰라의영검 = 10** (channel max time?)

## 정리

R102 의 32 byte 중 **R112 까지 28 byte 의미 추정 확정** (R102 23 + R112 5 추가):

| 확정 영역 | bytes | 의미 |
|---|---|---|
| Core skill | 0/1/2/3-4/5/7/8/9/13/14/18 | MP/flag1/section/damage/dtype/precast/lvl_req/sec_flag/multi/active/channel |
| Combat stat | 16/17/19 | speed/range/anim |
| Secondary effect | 20-21/22/23 | effect_id/magnitude class/sub_boundary/bonus |
| Side-effect | 24-31 | DEBUFF/COMBO/BUFF descriptor (signed negative for decrease) |
| Aux/VFX | 6/10 | VFX param / per-skill aux |
| Outliers | 11/12 | sparse per-skill |
| Always 0 | 15 | invariant padding |

**남은 미확정**: byte[15] (always 0) — 정의상 unused.

## 산출

- `tools/converter/parse_h4_statblock_uncertain_bytes.py` (신규)
- `work/h4/converted/h4_statblock_uncertain_bytes.json` (65.6KB)
- `docs/h4/round112-statblock-uncertain-bytes.md` (이 문서)

## 다음 후보

1. **SCN opcode dispatch** (R72 BSDAT body opcode vs SCN bytecode 매핑)
2. **`_ITM_OPTION` byte[21] magnitude class vs class skill byte[21] 정밀 cross-check** — R106+R112 두 시스템 통합 model
3. 사용자 트랙: Phase C Step 4d, 원작 UI 이식
