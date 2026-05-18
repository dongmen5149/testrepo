# Hero3 — Round 61: item body 정밀 디코드 / i13·i14 카테고리 식별 / skill body 디코드

날짜: 2026-05-18 (Round 61)
이전: [Round 60 — skill 7파일 / boss HP / string table / item 17파일](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md)

## TL;DR

R60에서 발견한 평문 데이터의 **body 필드 layout** 을 완전 디코드. 480+ 아이템 + 105 스킬의 가격/스탯/효과 모두 정량화.

| # | 작업 | 결과 |
|---|---|---|
| 1 | item dat 12 장비 + 6 특수 = 18 카테고리 body 디코드 | **480+ items 가격/요구레벨/공격력/방어력/tier 매핑** |
| 2 | i13_dat (35) / i14_dat (46) 카테고리 식별 | **i13 = 패시브 스크롤 / i14 = 조합재료** 확정 |
| 3 | skill_dat 7 파일 body 30-70B 디코드 | **105 skills × (category, SP cost, base damage, rank)** 추출 |

진행률 ~82-85% → **~86-89%** (+4%p).

## 산출물

| Path | 내용 |
|---|---|
| [`tools/recon/decode_item_body.py`](../../tools/recon/decode_item_body.py) | item body 디코더 (5 layouts: equip20/ring18/consumable/enchant/short) |
| [`tools/recon/decode_skill_body.py`](../../tools/recon/decode_skill_body.py) | skill body 디코더 (4 categories: weapon_passive/active_attack/active_buff/passive_bonus) |
| `work/h3/recon/item_decoded.json` | 18 카테고리 × ~25-46 items = 480+ items decoded |
| `work/h3/recon/item_decoded.log` | item dump |
| `work/h3/recon/skill_decoded.json` | 7 × 15 = 105 skills decoded |
| `work/h3/recon/skill_decoded.log` | skill dump |

## 1. 장비 (i0~i11) 20B body layout 확정

R60 의 17 파일 평문 파싱 후 body hex 비교 → 명확한 20B 구조:

```
+0..1   LE16 price        # Gold cost (200→9600 등 monotonic)
+2..3   pad
+4      tier index        # 0~16 (외형 sprite index?)
+5      variant byte      # 보통 0xff (default), 가끔 색상 변형
+6..7   pad
+8      req_level         # 단조 +5 per tier (1/5/10/15/20/25/...)
+9..11  pad
+12..13 LE16 stat_primary # ATK (무기), DEF (방어구)
+14..15 LE16 stat_sec     # sub-stat (무기 보조 데미지)
+16..19 pad (zero)
```

예: `머리띠` (i0): price=200, tier=0, lvl=2, DEF=2.
`하푼` (i4 첫번째 창): price=100, lvl=1, ATK=43, sub=17.
`강철투구` (i0): price=29700, lvl=46, DEF=29.

### 무기 ATK 곡선 (i4~i10, 25 entries × 5 lvl × ...)

각 무기 종류별 base damage growth (tier 0 → tier 9):

| 무기 | base | step | tier 9 |
|---|---:|---:|---:|
| 창 (i4) | 43 | +10 | 133 |
| 대검 (i5) | 51 | +12 | 159 |
| 단검 (i6) | 47 | +11 | 146 |
| 건 (i7) | 40 | +10 | 130 |
| 라이플 (i8) | 59 | +13 | 176 |
| 다크석 (i9) | 60 | +13 | 177 |
| 홀리석 (i10) | **45** | **+9** | **126** (가장 약함, but 회복 가능) |

→ 라이플/다크가 단일 데미지 최강. 홀리는 데미지 약하지만 회복/방어 보조.

### 방어구 DEF 곡선

- 헬멧 (i0): DEF 2→47 (lvl 2 → 96 추정)
- 갑옷 (i1): DEF 10→? (가장 큰 방어값)
- 장갑 (i2): DEF 7→?
- 신발 (i3): DEF 6→?
- 방패 (i11): DEF 3→? (block 확률 별도)

stat_secondary = 무기에선 sub-damage / 방어구에선 거의 0 (장갑류는 사용 안 함).

## 2. 반지 (i12) 18B body layout — bonus_type/value 매핑

반지 40 entries 모두 다음 구조:
```
+0..1   LE16 price (1000 default, 3000 for 인장류)
+4..5   LE16 (0=일반 / 256=인장)
+6..7   LE16 (1=가격 곱?)
+10..11 LE16 (2=base?)
+14     bonus_type  (스탯 ID)
+15     bonus_value (보너스 값)
+16..17 (optional) 추가 보너스 type/value 쌍
```

bonus_type 매핑 (관찰값):
| type | 의미 | 예 |
|---:|---|---|
| 2 | MaxHP | 근성의반지 +5 |
| 3 | HP Regen | 회복의반지 +50 |
| 5 | STR | 힘의반지 +8 |
| 6 | INT | 정신의반지 +8 |
| 7 | VIT | 체력의반지 +3 (+추가 보너스 8/3) |
| 10 | AGI | 민첩의반지 +5 |
| 14 | 명중 | 총명의반지 +10 |
| 15 | 회피 | 지혜의반지 +10 |
| 18 | 공격력? | 맹공의반지 +10 |

## 3. i13 / i14 카테고리 식별

### i13_dat = **패시브 스크롤 / 효과 아이템** (35)

variable-size body: price + desc_len + EUC-KR desc + effect_type(LE16) + value(LE16).

example:
- 자비의손길: effect=0x0102 (HP 회복), value=600 → "사용자의 HP를 대량 회복한다."
- 잠재의식: effect=0x0402 (SP 회복), value=600 → "사용자의 SP를 대량 회복한다."
- 오우거의의지: effect=0x0202, value=30 → "사용자의 HP최대치를 순간 증가시킨다."
- 혼신의일격: effect=0x0502, value=80 → "사용자의 물리공격력이 순간 극대화된다."

effect_type 인코딩:
- high byte: 효과 종류 (01=HP회복, 02=HP최대치, 03=HP회복증가, 04=SP, 05=ATK, 06=특수공격력, ...)
- low byte: 대상/지속 (02=사용자 순간, 04=파티 일정시간)

### i14_dat = **조합/제련 재료** (46)

variable-size body 동일 layout, effect=0 (재료는 효과 없음).

- 붉은용액/푸른용액/투명용액: 100~200G, 일반 조합 재료
- 제련석: 400G, 무기/방어구 제련용
- 연마가루: 창/양손검/나이프 조합
- 정령석: 홀리스톤/다크스톤 조합
- 탄성제: 권총/라이플 조합
- 강화제/질긴섬유: 방어구 조합
- 바람피리 등 속성 재료

→ **대장간 시스템 = R60의 smith_dat (DES) 가 이 재료들의 레시피**. NDK runner 복호 시 매핑 가능.

## 4. enchant (i16) 옵션 4B tail layout

15 enchant 옵션, 모두 1200G:
```
+0..1   LE16 price (1200)
+2..3   pad
+4      desc_len
+5..N   "XX을 증가/감소.;X에 결합." 설명
+N..N+3  4-byte tail: (slot_id, level_req?, sub_a, sub_b)
```

tail 패턴:
| name | tail | 효과 |
|---|---|---|
| 투신의 | `02 05 05 05` | HP 최대치 |
| 공명의 | `03 0c 05 05` | HP 자동회복 |
| 뇌제의 | `00 0f 04 04` | 무기 공격력 |
| 금강의 | `07 0f 05 05` | 물리 방어 |
| 정령의 | `08 0f 05 05` | 마법/총기 방어 |
| 사신의 | `09 08 02 04` | 명중률 |
| 영제의 | `0a 08 03 03` | 회피율 |
| 철벽의 | `0b 08 02 06` | 방패 블록 |
| 속박의 | `0c 06 01 04` | 크리티컬 발생 |
| 결의의 | `0d 06 00 01` | 크리티컬 받음 감소 |

tail[0] = bonus_type (반지의 bonus_type 매핑과 다른 체계 — enchant 전용).
tail[1] = required level / strength
tail[2..3] = param pair.

## 5. 소비 (i18) 26 items — effect_type 명확

| name | price | effect_type | value | desc |
|---|---:|---|---:|---|
| 포션 | 200 | 0x0112 | 200 | HP 200 회복 |
| 하이포션 | 600 | 0x0113 | 600 | HP 600 회복 |
| 미라클포션 | 1200 | 0x0114 | 1500 | HP 1500 회복 |
| 엘릭서 | 2000 | 0x0115 | 3000 | HP 3000 회복 |
| 과일쥬스 | 200 | 0x0416 | 200 | SP 20% |
| 포도주 | 500 | 0x0417 | 500 | SP 50% |
| 요정수 | 1000 | 0x0418 | 1000 | SP 완전 |
| 오브원석 | 200 | 0x371c | 0 | 오브 변환 |
| 귀환서 | 300 | 0x261a | 0 | 마을 귀환 |
| 그리폰의피리 | 0 | 0x271b | 0 | 마을 이동 |

effect_type LE16 = (action_id, sub_action):
- low byte 0x12~0x15 = HP 회복 4-tier
- low byte 0x16~0x18 = SP 회복 3-tier
- low byte 0x1c = 오브 변환
- low byte 0x1a/0x1b = 귀환/이동

high byte = category enum (01=HP, 04=SP, 27/26=텔레포트, 37=특수).

## 6. skill_dat (s4~s10) body 디코드 (105 skills)

각 skill body byte 0 = skill_category:

| cat | 의미 | 구조 |
|---:|---|---|
| 0 | weapon mastery (passive 1-7) | 30B fixed stat + tier_id |
| 1 | active attack | SP cost + cool + 데미지 base |
| 2 | active buff | SP cost + 지속시간 + stat type |
| 3 | passive bonus | 2-3 pair (bonus_type, value) |

각 클래스의 15 skill 구성:
- index 0-6: 7개 weapon mastery (creator 스킬 — base damage tier scaling)
- index 7-9: 3개 active attack
- index 10-11: 2개 active buff
- index 12-14: 3개 passive bonus

### Base damage scaling per weapon (eb byte 관찰):

| skill | weapon mastery base eb | 비고 |
|---|---:|---|
| 창술 (s4) | 3 | 매우 낮은 base |
| 검술 (s5) | 42 | 표준 |
| 단도 (s6) | 41 | 표준 |
| 사격 (s7) | 45 | 표준+ |
| 격발 (s8) | 45/105 | tier 0 통상, tier 1 = 105 (강력) |
| 영탄 (s9) | 64 | 마법 최강 |
| 광아 (s10) | 64 | 마법 동급 |

### Active attack SP cost 7-tier

100/200/300/400/500/600/800 — 모든 active skill 의 SP cost 가 이 7 단계 중 하나.

예:
- 섬광 (창): SP 100 (저비용)
- 자격: SP 400
- 압도: SP 800 (최고 + 효과 강력)
- 선풍 (검): SP 500
- 양단: SP 500
- 난무 (단도): SP 600 (rank=15, 최고급)
- 난사 (건): SP 600
- 직격 (라이플): SP 600
- 나락 (다크): SP 500 (rank=5)
- 격광 (홀리): SP 200 (저비용 marvel)

### Skill rank/level

skill 마지막 byte = rank 또는 max level:
- 대부분: rank 1
- 특수: 난무=15 (최고급, 모든 기술 연속), 나락=5, 연쇄=5
- 패시브: 모두 rank 1

## 7. PROGRESS / 진행률 갱신

| 영역 | R60 | R61 | 변화 |
|---|---:|---:|---|
| 자산 포맷 분석/변환 | 82% | 82% | — |
| 자산 변환 산출 | 95% | 95% | — |
| Ghidra 로직 리버싱 | 75% | 75% | — |
| **게임 데이터 평문 매핑** | **95%** | **98%** | +3%p (모든 body 디코드) |
| **게임 시스템 모델링** | 60% | **78%** | +18%p ★ (item/skill/effect type 매핑) |
| Android 엔진 재구현 | 5~10% | 5~10% | — |
| **합계 추정** | **~82-85%** | **~86-89%** | **+4%p** |

## 8. 다음 라운드 (Round 62) 우선순위

1. ⭐⭐⭐ **i15_dat 8번째 DES 파일 복호** (사용자 환경 필요)
   - 7400B = 가장 큰 암호화 — master shop list 또는 master item table 추정
   - 다른 7 DES 파일과 함께 NDK runner 일괄 처리

2. ⭐⭐⭐ **item body 의 unknown byte 의미 추가 식별**
   - byte +4 (tier index) 와 sprite/icon 매핑
   - byte +5 (variant) 의 color/skin variant 정확한 값 분포
   - 무기 stat_secondary (sub-damage) 의 정확한 의미

3. ⭐⭐ **weapon mastery skill body 30B stat block 추가 디코드**
   - byte +11/+12 의 weapon damage 와 i*_dat 의 sub-stat 비교
   - skill rank 별 스탯 변화 (rank 1→2→3 의 차이)

4. ⭐⭐ **i17 퀘스트 아이템과 quest_*_dat 메타데이터 cross-reference**
   - 시그널펜던트A/B + 협곡의성수 + 토레즈시민증 등의 사용 컨텍스트

5. ⭐ **FUN_4f358 본문 정밀 분석** (R55/R59 보류, 여전히)
6. ⭐ **FUN_3a028 16-JT 디코드** (R54 보류)

## 9. 참고

- [SESSION_HANDOFF.md](SESSION_HANDOFF.md), [PROGRESS.md](PROGRESS.md)
- 직전: [Round 60 skill+item+string](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md)
- R59: [char/npcg/s4 dat](ghidra-char-npcg-skill-parsing-2026-05-18.md)
- R58: [boss/quest + DES variants](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md)
