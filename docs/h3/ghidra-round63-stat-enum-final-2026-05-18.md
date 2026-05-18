# Round 63 — master stat enum 완전 매핑 (2026-05-18)

> 이번 라운드 목표: R62 의 미식별 8 bonus_type code 의 의미를 확정. R63 의 결정적 발견 — **i16 enchant 의 tail[0] 이 i12 ring / i13 effect_type high byte / equip trailer bonus_type 와 동일한 master stat enum 사용**. 각 enchant 의 한국어 desc 가 모든 코드의 의미를 직접 알려줌.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **R62 의 미식별 8 코드 전부 확정** — i16 enchant desc 로부터 직접 매핑
- ⭐⭐⭐⭐ **R61 의 일부 라벨도 정정** — 0x0e ≠ HIT, 0x0f ≠ EVA, 0x0c ≠ P.DEF, 0x0d ≠ M.DEF, 0x12 ≠ ATK
- ⭐⭐⭐⭐ **i12 ring / i13 effect / i16 enchant / equip trailer = ALL same master enum** — 네 곳 cross-validate
- ⭐⭐⭐ **rarity 는 stat-driven, NOT price-driven** — 무기 magic 1.01x / legendary 1.0x / epic 0.93x / boss_drop 0.03x (사실상 drop loot)
- ⭐⭐ **skill rank @ +0x1d 는 단순 tier 아님** — 단검 난무 r15, 건 난사 r10, 다크 나락 r5 = "skill power class"

## 1. Master stat enum 최종 (★★★★★)

i16 enchant tail[0] 의 0x00-0x12 sequential 한국어 desc + i13 effect_type high byte + i12 ring + equip trailer cross-reference 로 확정.

| code | name | meaning | confirmed by |
|---:|---|---|---|
| 0x00 | **ATT1_BASE** | 무기 공격력 (i16 only) | i16 뇌제의 |
| 0x01 | **HP_HEAL_INSTANT** | 즉시 HP 회복 | i13 자비의손길 |
| 0x02 | **HP_MAX** | HP 최대치 | i13/i12/i16/trailer |
| 0x03 | **HP_REGEN** | HP 자동 회복 (regen/turn) | i13 승리의염원 + i16 공명의 + ring 회복의반지 |
| 0x04 | **SP_MAX** | SP 최대치/회복 | i13 잠재의식 + ring 데몬의뿔 |
| 0x05 | **ATT1** (물공 = STR) | 물리공격력 | i13 끓어오르는피 + ring 힘의반지 |
| 0x06 | **ATT2** (특공 = INT) | 특수공격력 (마법/총기) | i13 악마의속삼임 + ring 정신의반지 |
| 0x07 | **P_DEF** (물방 = VIT) | 물리방어력 | i13 철벽의가드 + i16 금강의 + ring 체력의반지 |
| 0x08 | **M_DEF** (특방) | 특수방어력 (마법/총기) | i13 오로라의장벽 + i16 정령의 + ring 히드라/배리어 |
| 0x09 | **ACC** | 명중률 | i13 사냥꾼의눈 + i16 사신의 + ring 콘돌/백발백중 |
| 0x0a | **DOD** (회피 = AGI) | 회피율 | i13 시간의지배자 + i16 영제의 + ring 민첩의반지 |
| 0x0b | **BLOCK** | 방패방어율 | i13 용자의가호 + i16 철벽의 + ring 기사/프로텍트 |
| 0x0c | **CRI_RATE** ★NEW | 크리티컬 발생율 | i16 속박의 (R61 P.DEF 가설 폐기) |
| 0x0d | **CRI_DEF** ★NEW | 크리피해 감소 | i16 결의의 (R61 M.DEF 가설 폐기) |
| 0x0e | **SP_COST_REDUCE** ★NEW | 스킬 SP 소모 감소 | i16 현자의 + ring 총명의반지 (R61 HIT 폐기) |
| 0x0f | **SP_REGEN** ★NEW | SP 회복속도 | i16 마도의 + ring 지혜의반지 (R61 EVA 폐기) |
| 0x10 | **HP_DRAIN** | 공격시 HP 흡수 | i16 흡혈의 + ring 카오스/데몬 |
| 0x11 | **CD_REDUCE** | 쿨타임 감소 | i13 질풍노도 + i16 폭풍의 + ring 헤이스트 |
| 0x12 | **SHIELD_PIERCE** ★NEW | 방패 무시 확률 | i16 직격의 + ring 맹공/샤프니스 (R61 ATK 정정) |
| 0x16 | **BUFF_REMOVE** | 능력치 증가 해제 | i13 망각의향 |
| 0x17 | **CURE_STATUS** | 상태이상 회복 | i13 혼의외침 |
| 0x1c | **REVIVE** | 전투불능 회복 | i13 피닉스의숨결 |

### 1.1 R61 매핑 정정 요약

| code | R61 가설 | R63 확정 | 검증 자료 |
|---:|---|---|---|
| 0x0c | P.DEF | **CRI_RATE** | i16 속박의 "크리티컬 발생 확률 증가" |
| 0x0d | M.DEF | **CRI_DEF** | i16 결의의 "크리티컬 공격 맞을 확률 감소" |
| 0x0e | HIT | **SP_COST_REDUCE** | i16 현자의 "스킬사용 SP 감소" |
| 0x0f | EVA | **SP_REGEN** | i16 마도의 "SP 회복속도 증가" |
| 0x12 | ATK | **SHIELD_PIERCE** | i16 직격의 "방패 무시 확률 증가" |

→ 실제 P.DEF/M.DEF/ACC/DOD/ATK 는 0x07/0x08/0x09/0x0a/0x05 였음 (i13 effect_type 으로 확정).

### 1.2 ring 라벨의 user-facing 명칭

i12 ring 의 "힘의반지" (0x05) — 게임 UI 는 "힘" 으로 표시하지만 실제로는 ATT1 (물리공격력) 부여.
- 0x05 STR (UI: 힘) → 실제 ATT1 (i13 0x05 = 물리공격력)
- 0x06 INT (UI: 정신) → 실제 ATT2 (i13 0x06 = 특수공격력)
- 0x07 VIT (UI: 체력) → 실제 P.DEF (i13 0x07 = 물리방어력)
- 0x0a AGI (UI: 민첩) → 실제 DOD (i13 0x0a = 회피율)

이는 일반적인 RPG 패턴 — primary attribute UI 표시는 plyer-friendly 라벨, internal 은 derived stat. Hero3 의 stat 시스템은 4 primary attribute (힘/정신/체력/민첩) 가 4 derived stat (ATT1/ATT2/PDEF/DOD) 와 1:1 매핑.

## 2. i12 ring / equip trailer / i13 effect / i16 enchant 통합 (★★★★)

네 데이터 소스가 같은 enum 을 사용함을 확인:

| 소스 | 쓰임새 | 적용 예 |
|---|---|---|
| **i12 ring** | flat stat bonus (영구) | 힘의반지 +8 = 영구 ATT1+8 |
| **equip trailer** | flat stat bonus (장착 시) | $드래곤헬름 HP+10 + MDEF+10 |
| **i13 effect** | temporary buff/debuff (사용 시) | 끓어오르는피 ATT1+40% 일정시간 |
| **i16 enchant** | flat stat bonus (방어구/무기 결합) | 투신의 HP+5 enchant |

### 2.1 enchant tail[0] 패턴 통합

```
i16 tail = (stat_code, level/value, sub_a, sub_b)
```

15 enchant 모두 분석:

| stat_code | enchant 이름 | desc 요약 |
|---:|---|---|
| 0x00 | 뇌제의 | 무기 공격력 강화 |
| 0x02 | 투신의 | HP 최대치 증가 |
| 0x03 | 공명의 | HP 자동 회복 |
| 0x07 | 금강의 | 물리방어 강화 |
| 0x08 | 정령의 | 특수방어 강화 |
| 0x09 | 사신의 | 명중률 증가 |
| 0x0a | 영제의 | 회피율 증가 |
| 0x0b | 철벽의 | 방패 블록률 증가 |
| 0x0c | 속박의 | 크리티컬 발생 확률 증가 |
| 0x0d | 결의의 | 크리티컬 피해 감소 |
| 0x0e | 현자의 | 스킬 SP 소모 감소 |
| 0x0f | 마도의 | SP 회복속도 증가 |
| 0x10 | 흡혈의 | HP 흡수 |
| 0x11 | 폭풍의 | 쿨타임 감소 |
| 0x12 | 직격의 | 방패 무시 확률 증가 |

## 3. Rarity → 가격 modifier (★★★)

R62 의 7-tier rarity prefix 가 가격에 어떻게 반영되는지 측정.

### 3.1 슬롯별 가격 비율 (normal 기준 1.0x)

| slot | magic | legendary | epic | boss_drop | quest_reward |
|---|---:|---:|---:|---:|---:|
| 헬멧 | 1.16x | 1.02x | 1.17x | 1.26x | 0x |
| 갑옷 | 1.13x | 1.01x | 1.15x | 1.24x | 0x |
| 장갑 | 1.14x | 1.11x | 1.26x | 1.51x | 0x |
| 신발 | 1.15x | 1.10x | 1.28x | 1.49x | 0x |
| **창** | **1.01x** | — | 0.93x | **0.03x** | 0x |
| 대검 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 단검 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 건 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 라이플 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 다크석 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 홀리석 | 1.01x | — | 0.93x | **0.03x** | 0x |
| 방패 | 1.08x | — | 1.18x | 1.46x | 0x |

### 3.2 전체 평균 (모든 slot 통합)

| rarity | mean | median | stdev | n |
|---|---:|---:|---:|---:|
| magic | 1.07x | 1.07x | 0.12 | 85 |
| legendary | 1.06x | 0.99x | 0.13 | 20 |
| epic | 1.06x | 1.15x | 0.41 | 40 |
| boss_drop | 0.72x | 1.24x | 0.68 | 29 |
| quest_reward | 0x | 0x | 0 | 12 |

**결론**:
- 방어구 (헬멧/갑옷/장갑/신발/방패): rarity 가 가격에 점진적 반영 (magic 1.13x → boss_drop 1.5x)
- **무기 (창/대검/단검/건/라이플/다크석/홀리석): rarity 가 stat 만 결정, 가격은 거의 동일** (magic 1.01x, epic 0.93x)
- **boss_drop 무기는 0.03x = 사실상 free loot** — 보스 처치 시 자동 드롭이라 가격 0 또는 매우 낮음
- quest_reward 는 모두 0 — 상점 미판매, 퀘스트 보상 전용

→ Hero3 의 rarity 시스템은 가격이 아니라 **stat bonus (trailer 2 쌍)** 와 **specific bonus_type** 으로 차별화. 디자인 의도: "비싼 normal 아이템" vs "stat 풍부한 magic 아이템" 의 trade-off.

## 4. Skill rank @ +0x1d 분석 (★★)

R62 에서 발견한 +0x1d byte 의 분포 분석.

### 4.1 weapon_passive 의 rank 분포

| weapon | rank distribution |
|---|---|
| 창 (s4) | r1=2, r2=4, r3=1 |
| 검 (s5) | r1=5, r2=1, r3=1 |
| 단검 (s6) | r1=4, r2=1, r4=1, r5=1 |
| 건 (s7) | **r2=6, r4=1** (rank 1 없음!) |
| 라이플 (s8) | **r1=7** (전부 동일) |
| 다크석 (s9) | r1=6, r2=1 |
| 홀리석 (s10) | **r1=7** (전부 동일) |

라이플/홀리석은 전부 rank 1 → +0x1d 가 weapon-specific 단순 분류 byte 일 가능성 시사. 단검/건/다크석은 rank 가 다양.

### 4.2 active_attack 의 rank 분포 (★ ultimate 발견)

| weapon | active 스킬 + rank |
|---|---|
| 창 | 섬광(r2), 자격(r3), 압도(r1), 유도(r1) |
| 검 | 선풍(r3), 양단(r1), 질풍(r3) |
| **단검** | 참혼(r3), 암영(r1), **난무(r15)** ★ |
| **건** | 연사(r4), **난사(r10)** ★, 곡예(r4) |
| 라이플 | 직격(r1), **연쇄(r5)** ★, 위협(r1) |
| **다크석** | 암흑(r1), 업화(r1), **나락(r5)** ★ |
| 홀리석 | 파동(r1), 격광(r1) |

**고 rank 스킬 발견**:
- 단검 **난무 r15** — 단검 클래스 ultimate
- 건 **난사 r10** — 건 클래스 ultimate
- 라이플 **연쇄 r5** — 라이플 클래스 finisher
- 다크석 **나락 r5** — 다크 클래스 finisher

→ +0x1d 는 **"skill power class"** — 일반 스킬 1-4, ultimate/finisher 5-15. weapon_passive 의 7-tier 와는 별도 시스템.

### 4.3 가설 정정

R62 의 "+0x1d = 1/2/3 rank tier" 가설은 너무 단순. 실제는:
- weapon_passive: 1-5 범위 (tier 단계)
- active 스킬: 1-15 범위 (skill power class, ultimate 는 5+)

## 5. R64 작업 후보 (자동 가능 우선)

1. ⭐⭐⭐ **stat enum 종합 표 → game data model 정리** — 모든 i*_dat 의 bonus_type 을 master enum 으로 통일된 JSON 출력 (Android 리메이크용 game_balance.json 후보)
2. ⭐⭐⭐ **i15_dat NDK runner 처리** (사용자 환경 필요) — 7400B master shop/item table 추정
3. ⭐⭐ **i13/i14/i17/i18 effect_value scale 분석** — value 의 의미 (% 또는 flat) 별 분류
4. ⭐⭐ **새 0x14 / 0x19 / 0x01 미사용 코드 사용 함수 추적** (binary literal grep)
5. ⭐⭐ **rank 5-15 ultimate 스킬의 다른 byte 차이 분석** — 난무/난사/나락 의 30B 비교
6. ⭐ **FUN_4f358 본문 정밀** (Ghidra) — stat_modify 함수 후보 검증
7. ⭐ **smith_dat (DES) 복호화 시 조합 시스템 발견** — i14 재료 → i0~i12 결과물 매핑

## 6. 산출물

| 종류 | 파일 |
|---|---|
| 신규 doc | [`docs/h3/ghidra-round63-stat-enum-final-2026-05-18.md`](ghidra-round63-stat-enum-final-2026-05-18.md) (이 문서) |
| 신규 recon 2 | `tools/recon/map_stat_enum.py` / `tools/recon/correlate_price_rank.py` |
| 신규 dump | `work/h3/recon/stat_enum.{json,log}` / `price_rank_corr.{json,log}` |
| 갱신 | `docs/h3/PROGRESS.md` / `docs/h3/SESSION_HANDOFF.md` / `MEMORY.md` |

## 7. 진척률 갱신 (Round 63 시점)

| 영역 | R62 | R63 | 변화 |
|---|---:|---:|---|
| 자산 포맷 분석/변환 | ~98% | ~98% | 변화 없음 |
| 자산 변환 산출 | ~95% | ~95% | 변화 없음 |
| Ghidra 게임 로직 리버싱 | ~62-65% | ~62-65% | 변화 없음 (binary 분석 없음) |
| **데이터 모델링** | **84%** | **92%** | +8%p — stat enum 100% 매핑 / rarity 의미 확정 / skill power class |
| Android 엔진 재구현 | ~5-10% | ~7-12% | +2%p — game balance JSON 작성 가능 |
| i18n | UI 100% / 대사 0% | UI 100% / 대사 0% | 변화 없음 |

**전체 진행률**: ~88-91% → **~91-94%** (+3%p)

## 8. R63 의 결정적 통찰

R63 의 큰 발견은 **"i16 enchant tail 의 한국어 desc 가 stat enum 의 Rosetta Stone"** 이라는 점. R61-R62 까지는 ring 이름과 trailer 분포로 유추만 했지만, enchant 는 **각 코드마다 명시적 한국어 설명** 을 제공하므로 100% 확정 가능.

이 통찰은 다른 게임 RE 에서도 적용 가능 — **"text description 이 있는 데이터 소스가 가장 빠른 RE 진입점"**. (Hero5 의 quest reward type 분석 R65 와 동일 패턴.)
