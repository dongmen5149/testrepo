# Hero3 Round 110e — extras_records sprite catalog investigation (DEFERRED) — 2026-05-20

> R110e 의 원래 범위 ("frame_4 대형 건물 배치") 는 **데이터상 도달 불가능** 으로 확인. extras_records 의 sprite 출처 (global decoration catalog) 가 미해독 상태. 다음 작업 권장 변경.

## 0. TL;DR

- **frame_4 (≥80px) 은 NEOSOLTIA obj_6_bm 의 case 에서 거대한 풀숲/덤불** — 건물 아님. obj sheet 별로 frame_4 의 의미가 다름 (BOSS_TOWN: 16×9 작은 벽 조각, NEOSOLTIA: 80×63 덤불, etc.).
- **layer_1 max=192=3<<6** 으로 frame_idx 4 는 layer_1 미경유 확인 ([R110a](round110a-obj-layer-wiring.md) 검증).
- **extras_records** 가 placement marker 역할이지만 id range 0..215 (162 unique) vs obj sheet 의 5 frame 으로 직접 매핑 불가능.
- **sprObj0..6_bm + sprObj_0_bm = 8 별도 sheet** (tree / 작은 나무 / 큰 건물 / 가로등 / 탑 / 텐트 / 버섯류) 존재하지만, extras_records.id 와의 정확한 매핑 규칙 미발견.
- 3 hypothesis (H1: 모든 extras→frame_4, H2: 모든 extras→sprObj0, H3: id-range 휴리스틱) 모두 NEOSOLTIA 에서 시각적으로 의미 없는 결과.
- **결론**: extras_records 의 sprite 출처 결정 = 추가 RE 필요 (10~20 dev day, Ghidra disasm 의존). 본 라운드 scope 초과.

## 1. 분석 산출

### 1.1 extras_records 전역 통계 (134 maps, 7620 records)

```
type distribution: [(0, 4521), (128, 2588), (64, 221), (192, 149), (32, 141)]
top 30 ids: [(62, 1093), (63, 474), (123, 321), (65, 268), (64, 267),
              (122, 263), (153, 238), (209, 228), (2, 190), ...]
id range: 0..215, unique: 162
```

ID 62, 63 = 풀/덤불 가장 많음 (1567 total). 그 외 IDs scattered.

### 1.2 NEOSOLTIA (map0) extras 82개

| type | id | count | 추정 |
|---|---|---|---|
| 0 | 2 | 16 | 보물상자? 특수마커 |
| 0 | 35 | 10 | 가구/장식 |
| 128 | 35 | 7 | NPC |
| 0 | 39 | 6 | 가구 |
| 128 | 45 | 6 | NPC |
| 0/128 | 37/36/42 | 변동 | 가구 / NPC 혼재 |

type=0 vs type=128 가 같은 id 에 공존 = bitmask flag 일 가능성 (128=high bit, "interactive"?).

### 1.3 frame_4 시각 inspection

```
obj_6_bm/frame_04_80x63_tc.png      = 거대한 풀숲 (NEOSOLTIA 의 forest decoration)
obj_41_bm/frame_04_16x9_tc.png      = 작은 벽 ramp 조각 (BOSS_TOWN)
sprObj0_bm/frame_00_60x39_tb.png    = 트리/덤불 (어두운 변종)
sprObj_0_bm/frame_00_60x39_tc.png   = 트리 (밝은 변종)
sprObj2_bm/frame_00_90x31_tc.png    = 큰 건물 (가장 큰 sprite)
```

**핵심**: frame_4 의 의미는 obj sheet 별로 다름. 통일된 "big building" slot 아님.

### 1.4 placement hypothesis 시각 검증 ([`tools/qa/render_extras_candidates.py`](../../tools/qa/render_extras_candidates.py))

| 가설 | NEOSOLTIA 결과 |
|---|---|
| H1: 모든 extras → frame_4 | 거대 덤불이 좌상단 하나만 보임 (clipping 발생, 의미 부족) |
| H2: 모든 extras → sprObj0 (tree) | 좌상단 area 에 트리 cluster (extras 위치 자체가 좌상단 집중) |
| H3: id range 휴리스틱 | sprite 가 무작위로 보이는 cluster, 시각적 의미 없음 |

세 가설 모두 **원작 NEOSOLTIA 의 마을 layout 과 부합하지 않음**. extras_records 의 sprite 출처 규칙은 더 깊은 RE 필요.

## 2. 깊은 RE 필요 항목 (R111+ 또는 R110d/c 후 재시도)

1. **global decoration sprite catalog 파일 식별** — `tools/recon/` 또는 Ghidra 에서 `0x215` 또는 `162 entries` 상수 grep. 162 unique id 가 정확히 어디서 와서 어떤 sprite 로 매핑되는지.
2. **type bitmask 의미** — type ∈ {0, 32, 64, 128, 192}. 0/128 dominant, 32/64/192 가 minor. 각 의미 (collision / interaction / animation / NPC distinction).
3. **NPC sprite 매핑** — `_mp.extras_records` type=128 + 특정 id range 이 NpcRegistry 의 NPC 와 매핑되는가? 현 NpcRegistry 19 NPC vs 추정 수백 NPC 격차.
4. **frame_4 reachability** — layer_1 미경유. extras_records 의 어떤 (type, id) 가 frame_4 를 trigger 하는가?

## 3. 본 라운드 변경 사항

- **MapWalkScene.kt**: 변경 없음. extras_records 는 기존 `colorForDecoId(id)` 색상 dot 그대로.
- **신규 도구**: [`tools/qa/render_extras_candidates.py`](../../tools/qa/render_extras_candidates.py) — 3 hypothesis 시각 비교. 미래 가설 추가 가능.
- **베타 fidelity**: 변동 없음 (R110a 후 ~46% 유지).

## 4. 다음 권장 작업 (사용자 선택)

R110e 가 단기간에 해결 어려우므로 다른 트랙 우선:

1. ⭐⭐⭐⭐⭐ **R110b 사운드 트랙** (10-15 dev day) — SMAF→OGG 33곡 + MediaPlayer 통합. **사용자 신뢰도 정책 재결정 필요** ([Round 73 stale 가이드](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md)). 베타 fidelity 가장 큰 단일 임팩트 (+10%p 가능).
2. ⭐⭐⭐⭐ **R110c MapGraph 자동화** (10-15 dev day) — `_mp.extras_records` 의 exit 정보 추출. 현 4 edge placeholder → 수십 edge. 게임 플레이 진행 가능성 ↑.
3. ⭐⭐⭐ **R111: extras_records 의 global decoration catalog RE** (20-30 dev day) — Ghidra 분석 의존. R110e 의 deferred 항목들 해소.

## 5. 산출 artifact

```
tools/qa/render_extras_candidates.py   (3 hypothesis renderer)
work/h3/qa/extras_renders/              (NEOSOLTIA / SECRET_ROOM / BOSS_TOWN × H1/H2/H3 = 9 PNG)
docs/h3/round110e-extras-investigation.md   (본 문서)
```

## 6. 참고

- R109 (theme layer): [round109-map-tile-wiring-phase1-3.md](round109-map-tile-wiring-phase1-3.md)
- R110a (obj layer): [round110a-obj-layer-wiring.md](round110a-obj-layer-wiring.md)
- R109 plan §6 (NPC 자동 배치 미정): [r109-plan-map-tile-wiring.md](r109-plan-map-tile-wiring.md)
