# Hero4 Round 77 — BSDAT 49B stat field mapping

> R76 Track B 의 "BSDAT body = stat block" 가설 위에서 LE16 field 의미 추정.

## TL;DR

49B 보스 body (13 entries × 3 stages) 의 stat layout 추정:

| pos | LE16 값 범위 | role 추정 | 근거 |
|---|---|---|---|
| 0 | byte | tier/type marker | 모든 entry 에서 stage-invariant |
| 1 | (0x29 marker + byte[2]) | sprite/animation ID | byte[1] 자주 0x29 |
| 4 | 62 → 314 | **level_req** | 작은 monotonic 증가, weapon DAT level 곡선과 유사 |
| 6-16 | mostly constants | layout/string pointer | 8 positions 가 모든 stage 동일 |
| 17-18 | 1348 → 4942 | **EXP reward** | medium 증가 (×2.5 stage) |
| 29-30 | 0 → 1300 | **MP_max** | 0 이 종종 등장 (마법 없는 보스) |
| **31-32** | 173 → 1270 | **HP_max** | ✓ |
| **33-34** | == 31-32 | **HP_cur** | max == current 페어 |
| 35-36 | 57 → 588 | **DEF** 또는 secondary stat | 작은 페어 |
| 37-38 | == 35-36 | DEF 페어 / 또는 다른 stat | 페어 중복 |
| 40-41 | 4721 → 34046 | **gold reward** | 가장 큰 값 (×7 stage) |
| 42-43 | 변동 | drop item id / secondary | |
| 44-48 | mostly constants | 종료 marker | |

## 강한 증거

### max/current pair: pos[31-34]

브리안 stage 1/2/3: HP `173/396/970` at pos[31-32] **AND** at pos[33-34] (정확히 같은 값). 누아다도 `310/538/1298` 페어. 게임 엔진의 max-HP/current-HP 저장 패턴 ('현재 hp = 최대 hp' 으로 초기화) 와 정확히 일치.

### gold-like value: pos[40-41]

루칸 stage 1/2/3: `6045/10494/27134` — typical 보스 보상 gold 수준 (메인 보스). ×4.5 stage scaling.

### level_req: pos[4]

브리안 `62/154/239` — weapon DAT 의 lvl 1→max 곡선과 직접 매칭. byte 범위 (< 256) 도 적합.

## 정정/주의

- **pos[1]** 은 stat 가 아닐 가능성 — byte[1] 이 자주 `0x29` (= 41) 로 고정되거나 entry 식별자 marker. R76 분석에서 LE16 monotonic 으로 잘못 잡힌 케이스.
- **pos[2-3]** 도 marker (0x19/0x05/0x0d 등 작은 값) 가능.
- 단순 LE16 일관성 신뢰 가능한 정밀 stat 은 **pos[31,33,35,37,40]** (페어 + monotonic 모두 만족).
- 13개 entry 중 일부는 `pos[17] == 0` (브리안 변종, 케프네스) — EXP 0 보스 = 강제 패배/이벤트 보스 가능성.

## 105B 메인 보스 (루칸/래비)

stage-invariant constants 54 positions (49B 의 8 대비 6.7배) — 메인 보스는 **더 많은 고정 메타데이터** (장면 ID, dialog ref, animation script 등) 보유. 추가 entry 샘플 확보 후 별도 분석 필요.

## 후속 트랙

1. ⭐ **ESDAT 0x3f opcode dispatch** (R76 보류 항목) — 471 entries, script-like
2. 105B 메인 보스 stat field 정밀 (entry 샘플 부족 — 다른 _BSDAT 그룹 검색?)
3. trans 검증: `gold_reward` 값을 Android 게임 로직에 매핑 시 정합성 확인

## 산출

- `tools/analysis/bsdat_stat_fields.py`
- `work/h4/converted/h4_bsdat_stat_fields.json`
- `docs/h4/round77-bsdat-stat-fields.md` (이 문서)
