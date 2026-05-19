# Hero4 Round 87 — `_H_SS` 환수 시스템 stat block 정밀화

> R86 에서 발견한 환수 시스템의 전체 구조를 byte 단위로 분해 + 23B stat block 의 field 의미 식별.

## TL;DR

`_H_SS` (1624B) 의 전체 layout 을 6 section 으로 분해. **5 환수 × 5 logical skills + 4 global passive + 1 boss-like + 1 section divider = 29 의미 단위**.

- 환수당 7 raw entries → 5 logical skills (3 paired pattern + 2 standalone)
- 4 global summoner passives 의 skill ID `91-94` (= 0x5b-0x5e) 식별
- 23B stat block 의 field offset 의미 5종 확인 (type / damage / element / strength / animation)
- `망각의 저주` 는 boss-tier 단일 entry (skill_id=66, type=7 status)

## 전체 file layout (1624B)

| Section | offset | size | 내용 |
|---|---|---|---|
| 0. File header | 0x000-0x001 | 2B | `0x25 0x00` |
| 1. Boss-like entry | 0x002-0x024 | 35B | `[nlen=0x0b][name="망각의 저주"][23B data]` |
| 2. 5 환수 summary | 0x025-0x0c4 | 160B (가변 stride 32/36/42B) | 5 환수 metadata |
| 3. Zero padding | 0x0c5-0x0d6 | 18B | 모두 0 |
| 4. 환수A공격 divider | 0x0d7-0x0f7 | 33B | `[nlen=09][name="환수A공격"][23B data]` |
| 5. Skill entries | 0x0f8-0x056b | ~1140B | 5 환수 × 7 entries (35) + 4 환수[B-E]공격 divider |
| 6. Global passives | 0x056c-0x065f | ~244B | 4 paired entries (short stats + long desc) |

## Section 1: Boss-like 첫 entry

```
0x000: [25][00] [0b][망각의 저주 11B][00*23]
                          └─ 23B data block: 00 00 05 00 00 07 00 42 00 00 ...
                                                          ^^      ^^
                                                          type=7  strength=0x42(66)
```

추정: 보스급 status effect / 잊혀진 마법. type=7 (status, 환수 status 효과와 동일).

## Section 2: 5 환수 Summary (variable stride)

각 entry: `[01][cost=2d][size_marker][00][nlen][name:nlen B][padding][09 03 29][summon_id:1B][padding]`

| # | offset | nlen | name | total | summon_id |
|---|---|---|---|---|---|
| 0 | 0x025 | 4 | 베놈 | 32B | 0 |
| 1 | 0x045 | 8 | 헤지호그 | 36B | 1 |
| 2 | 0x069 | 8 | 그래비티 | 36B | 2 |
| 3 | 0x08d | 4 | 쇼커 | 32B | 3 |
| 4 | 0x0ad | 10 | 세이프가드 | 42B | 4 |

stride = 28 + nlen (이름 길이에 비례 가변). signature `09 03 29` 다음 byte = summon_id.

## Section 5: 환수당 7 skill entries → 5 logical skills

각 entry: `[nlen:1B][name:nlen B][data_block]`

| Entry type | nlen | data_size | 역할 |
|---|---|---|---|
| Long descriptor | 20-28B | 2B (`cost + 0x00`) | UI 표시 텍스트 ("기본공격력 강화", "원거리 뇌격 강화" 등) |
| Short active | 4-8B | 23B (stat block) | 실제 게임 mechanic (뇌격, 맹독 등) |
| Medium aura | 11B (`{element}의 오러`) | 23B (stat block) | passive aura |

**Logical skill 5종 모델** (per 환수):

1. **basic_attack** — long_desc + short_active (예: 베놈의 기본공격력 강화 / 뇌격)
2. **ranged_status** — long_desc + short_active (예: 베놈의 원거리 뇌격 강화 / 맹독)
3. **effect_boost** — long_desc only (예: 뇌격의 중독 효과 강화)
4. **aura** — medium_active only (예: 저주의 오러)
5. **on_summon_buff** — long_desc only (예: 소환시 소환자의 저주 증가)

세이프가드 (heal-class) 만 약간 변형: skill 2 가 회복 효과 + 실드 (스턴/맹독 자리 대체), skill 3 가 회복시 마법방어 증가 효과 (on_heal trigger).

### 5 환수 × 5 skills 매트릭스

| 환수 | basic | ranged | effect_boost | aura | on_summon |
|---|---|---|---|---|---|
| 베놈 | 뇌격 | 맹독 | 중독 효과 강화 | 저주의 오러 | 저주 증가 |
| 헤지호그 | 뇌격 | 되돌리기 | 반사화 저주 효과 강화 | 강화의 오러 | HP/SP증가 |
| 그래비티 | 뇌격 | 슬로우 | 슬로우 저주 효과 강화 | 마법의 오러 | 저항 증가 |
| 쇼커 | 뇌격 | 스턴 | 스턴 효과 강화 | 마력의 오러 | SP회복증가 |
| 세이프가드 | 회복 | 실드 | 회복 효과 강화 | 보호의 오러 | 방어력 증가 |

## 23B stat block field layout (R87 핵심 발견)

active skill 의 23B stat block 을 5 환수 비교로 field 의미 식별:

| 위치 | 의미 | 베놈 뇌격 | 헤지호그 뇌격 | 그래비티 뇌격 | 쇼커 뇌격 | 세이프가드 회복 |
|---|---|---|---|---|---|---|
| 0 | `type` (basic=20) | 0x14 | 0x14 | 0x14 | 0x14 | 0x14 |
| 3 | `damage` | 44 | 200 | 144 | 44 | 244 |
| 4 | flag | 1 | 0 | 1 | 1 | 1 |
| 5 | `element` (const) | 2 | 2 | 2 | 2 | 2 |
| 6 | flag (special) | 0 | 0 | 0 | 0 | 2 |
| 7 | `speed/cooldown` | 53 | 53 | 53 | 53 | 61 |
| 8 | `range/cost` | 120 | 100 | 160 | 140 | 100 |
| 10 | `animation_id` | 4 | 4 | 5 | 5 | 20 |
| 1-2, 9, 11-22 | zero padding | | | | | |

### Status effect (skill 2 active) 의 23B stat block

| 위치 | 맹독 | 되돌리기 | 슬로우 | 스턴 |
|---|---|---|---|---|
| 5 (type) | 0x07 | 0x07 | 0x07 | 0x07 |
| 6 (reflect_flag) | 0 | 3 | 0 | 0 |
| 7 (strength/duration) | 85 | 86 | 75 | 76 |
| 8 (cost) | 1 | 1 | 1 | 1 |
| 10 (anim) | 1 | 1 | 1 | 1 |

→ type=7 = "status proc", 되돌리기는 reflect 특수 flag (위치 6 = 3).

### Aura 의 stat block (참고)

aura 도 23B 인데 type 가 다름. 추후 R88 에서 정밀화.

## Section 6: 4 Global Passives (소환사 본인 강화)

각 entry pair: `[short_name:8-10B + 23B stats]` + `[long_name:18-20B + ~2B desc]`

| short_name | long_name | skill_id (stat[7]) |
|---|---|---|
| 마법력강화 | 소환수의 마법력 강화 | 0x5b = **91** |
| 교감도강화 | 소환수의 방어력 강화 | 0x5c = **92** |
| 체력강화 | 소환수의 체력 강화 | 0x5d = **93** |
| 정신강화 | 소환수의 교감도 강화 | 0x5e = **94** |

→ skill_id 91-94 가 환수 전체 강화 스킬. type=12 (passive), const param=3, lvl=2.

흥미: `정신강화` (short) ↔ `소환수의 교감도 강화` (long) — short 이름과 long 이름의 stat 매칭이 어긋남. 게임 내 표시 vs 실제 효과 분리.

## R86 가설 검증

| R86 가설 | R87 결과 |
|---|---|
| 5 환수 (베놈/헤지호그/그래비티/쇼커/세이프가드) | ✅ 확인 (summon_id 0-4) |
| 환수당 5 스킬 | ✅ 확인 (raw 7 entries → logical 5 skills) |
| 4 글로벌 강화 = 소환사 패시브 | ✅ 확인 (skill_id 91-94) |
| 망각의 저주 = 보스급 추가 환수? | ⚠ 환수 아님 — 단일 boss-tier status entry (type=7, str=66) |

## 캐릭터 mode 연결 (R86 후속)

R86 의 "소환사 = 3번째 character class 가능성" 가설:

- R69 의 4 skill set (S000-S003) + `_H_SS` (29 skills) = 5번째 skill catalog
- 환수 명령 = `소환술` → R69 S003 단도+마법 의 "환수흡수" 와 직접 매칭

→ **S003 (단도+마법) = 소환사 class** 가 가장 유력. _ITM_03 weapon 가 단도+소환 분기일 가능성 (R81 미해결 매트릭스).

## 산출

- `tools/converter/parse_h4_summon_system.py` (신규)
- `work/h4/converted/h4_summon_system.json` (26KB)
- `tools/converter/build_h4_catalog.py` (`summon_system` field 추가)
- `work/h4/converted/h4_catalog.json` (74.9KB, R87 통합)
- Android 자산 `apps/hero4-android/app/src/main/assets/h4_summon_system.json` (배포)
- `docs/h4/round87-summon-stat-detail.md` (이 문서)

## 다음 후보 (정밀화 자동 트랙 남은 항목)

1. **`_H_BS` 17 레벨 stat increment** (136B = 17 × 8B) — 환수 레벨업 progression
2. **`_H_SA` 24 slot ability mapping** (960B = 24 × 40B) — slot 별 ability 매핑
3. **23B stat block field 5+ 추가 의미 확정** — pos 0 (type id 카탈로그), pos 4 flag 의미
4. **dialogue corpus 환수 등장 빈도** (베놈/헤지호그/... × 35,752 대사)
5. **Q_REPAY idx ↔ R70 quest name 매핑** (R85 후속) — 200 - 128 = 72 차이 해소
6. **보스 phase stat 강화율 정량** (R80 후속) — 오토마톤 5 phase 비교
