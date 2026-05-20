# Hero4 Round 88 — `_H_BS` + `_H_SA` 환수 progression / ability slot 정밀화

> R86 동반 발견 두 파일 (`_H_BS` 136B + `_H_SA` 960B) 의 정확한 layout 식별.
> R86 가설 ("17 × 8B", "24 × 40B") 모두 **stride 방향이 반전**되어 있었음을 정정.

## TL;DR

| 파일 | R86 가설 | R88 실제 |
|---|---|---|
| `_H_BS` | 17 레벨 × 8B | **5 환수 × 27B + 1B 패딩** |
| `_H_SA` | 24 slots × 40B | **40 records × 24B** (1 헤더 + 24 ability + 15 summon-tier) |

- `_H_BS` 는 환수당 5 stat + 3 learn-skill_id 가 핵심 페이로드
- `_H_SA` 는 **8 unique ability × 3 tier × 24** + **5 summon × 3 tier × 15** 의 2 영역으로 구성
- 모든 summon-tier `value_le16 = tier × 10` 의 강건한 ratio 관계 확인

## `_H_BS` 레코드 (27B × 5)

```
bytes[0-2]:   19 00 [summon_id]
bytes[3-7]:   5 stat (HP/SP/ATK/DEF/MAG 추정)
bytes[8-10]:  fe 00 00 (sentinel)
byte[11]:     learn_count (2|3)
byte[12]:     cost / EXP marker
bytes[13-23]: padding (간헐적 ability tier 값)
bytes[24-26]: 3 sequential skill_ids = 환수가 학습하는 active skill ID
```

### 5 환수 stat + skill ID 매트릭스

| # | 환수 | 5 stats | learn IDs | cost |
|---|---|---|---|---|
| 0 | 베놈       | [21, 14, 18, 7, 5]    | 6, 7, 8    | 15 |
| 1 | 헤지호그   | [18, 13, 17, 12, 0]   | 9, 10, 11  | 0 |
| 2 | 그래비티   | [14, 19, 21, 6, 20]   | 12, 13, 14 | 0 |
| 3 | 쇼커       | [25, 10, 14, 11, 246] | 15, 16, 17 | 40 |
| 4 | 세이프가드 | [14, 15, 13, 18, 0]   | 18, 19, 20 | 0 |

- learn IDs 는 5 환수 × 3 = **15 sequential skill (id 6-20)** 형태로 깔끔히 분배
- 쇼커 byte[7]=246 (= signed -10) — penalty stat 가능성
- 베놈 byte[7]=5 가 `_H_SS` 첫 skill_id 5 와 일치 (basic_attack 매핑 후보)

## `_H_SA` 레코드 (24B × 40)

```
rec[0]      (24B): file header — [22, 100, 100, 1, 34, ...] 글로벌 max stat 추정
rec[1..24]  (24): 8 unique ability × 3 tier 카탈로그 (type=0x0b)
rec[25..39] (15): 5 summon-group × 3 tier 성장 (type=0x0835)
```

### Ability slot 카탈로그 (24 = 8 × 3)

각 entry: `16 00 00 00 00 00 00 0b [skill_id] [tier_value] 00 00 [bonus_id] [bonus_value]`

| skill_id | tiers | bonus_id |
|---|---|---|
| 12 | 10, 20, 30 | 18 |
| 16 | 10, 20, 30 | 17 |
| 15 | 10, 20, 30 | 19 |
| 21 | 5, 10, 15 | — |
| 37 | 20, 40, 60 | — |
| 13 | 10, 20, 30 | — |
| 18 | 10, 20, 30 | — |
| 22 | 10, 25, 40 | — |

skill_id ∈ {12, 13, 15, 16, 18, 21, 22, 37} — `_H_SS` 의 environment buff 영역과 ID 공간 공유 추정 (R87 global passive 91-94 와는 별개 카테고리).

### Summon-group 성장 테이블 (15 = 5 × 3)

각 entry: `16 00 00 00 00 00 00 08 35 [LE16 value] [tier] [group_id] [count] ... [optional signed-4B]`

| group_id | tier 1 | tier 2 | tier 3 |
|---|---|---|---|
| 0  | 400 @ lvl 40 | 600 @ 60 | 800 @ 80 |
| 64 | 300 @ 30     | 450 @ 45 | 600 @ 60 |
| 78 | 340 @ 34     | 510 @ 51 | 680 @ 68 |
| 38 | 340 @ 34     | 510 @ 51 | 680 @ 68 |
| 75 | 300 @ 30     | 450 @ 45 | 600 @ 60 |

**불변량**: `value_le16 = tier × 10` 정확히 일치 (5 group × 3 tier = 15/15).
group_id=64 entry 들에는 추가 signed-4B 필드 (= -30/-50/-70) 존재 → penalty/cost.

group_id 매핑 가설 (5 환수 매핑 후보):
- 0 (베놈), 64 (헤지호그), 78 (그래비티), 38 (쇼커), 75 (세이프가드)
- 검증은 R89 dialogue cross-ref 으로 보강 가능

## R86 가설 정정 요약

| 항목 | R86 추정 | R88 확정 | 차이 |
|---|---|---|---|
| _H_BS shape | 17 × 8B | 5 × 27B + 1B | record count / stride 둘 다 다름 |
| _H_SA shape | 24 × 40B | 40 × 24B | stride 방향 반전 |
| `_H_BS` 의미 | 레벨업 stat increment | 환수당 base stat + 학습 skill ID | "increment" 가설 폐기 |
| `_H_SA` 의미 | 24 ability slot | 24 ability + 15 summon-tier | 영역 분할 발견 |

## R87 cross-reference

`_H_BS` 의 learn skill ID (6-20) 는 R87 `_H_SS` 의 5 환수 × 5 logical skills 와 직접 연결:
- 각 환수는 자기 영역 3 active skill_id (basic_attack 제외) 를 `_H_BS` 에 등록
- basic_attack 은 byte[7] 의 stat byte (베놈=5) 로 시작 ID 표시 가능성

R87 의 `_H_SS` global passive skill_id `91-94 (0x5b-0x5e)` 와 `_H_SA` ability skill_id `{12..37}` 은 **ID 공간 disjoint** → 별개 카테고리.

## 산출

- `tools/converter/parse_h4_summon_progression.py` (신규)
- `work/h4/converted/h4_summon_progression.json` (12.5KB)
- `docs/h4/round88-summon-progression.md` (이 문서)

## 다음 후보 (정밀화 자동 트랙 남은 항목)

1. **23B stat block field 5+ 추가 의미 확정** (R87 후속) — pos 0 type catalog, pos 4 flag
2. **Q_REPAY idx ↔ R70 quest name 매핑** (R85 후속) — 200 - 128 = 72 차이 해소
3. **보스 phase stat 강화율 정량** (R80 후속) — 오토마톤 5 phase 비교
4. **dialogue corpus 환수 등장 빈도** (R87 후속) — 베놈/헤지호그 × 35,752 대사
5. **`_H_SA` group_id ↔ 5 환수 매핑 검증** (R88 후속) — dialogue cross-ref 으로 확인
