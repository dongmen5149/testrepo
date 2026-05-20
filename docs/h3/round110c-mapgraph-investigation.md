# Hero3 Round 110c — MapGraph 자동화 조사 (DEFERRED) — 2026-05-20

> R110c 원래 범위 (`_mp.extras_records` exit 정보로 134 map 자동 연결) 는 **데이터상 가능하지 않음**. exit 정보는 미해독 `_scn` opcode 스트림에 있음. 물리 추론 (edge walkability) 도 비-symmetric 매칭이 4건 뿐이라 신뢰성 부족.

## 0. TL;DR

- **현 MapGraph**: 8 hardcoded edges (4 pairs). 134 map 중 12 map 만 연결.
- **`_mp.extras_records` 에 exit 정보 없음** ([`tools/converter/convert_mp.py`](../../tools/converter/convert_mp.py) 의 주석 명시: "NPC 위치는 extras 가 아니라 _scn opcode 스트림에 있는 것으로 추정 (§4.4 미해독)").
- **물리 추론 시도**: 각 map 의 4 edge 에서 walkable layer_1 tile 스캔 → 그룹화 → cross-map 매칭.
  - 268 walkable openings 발견 (134 map 전체)
  - 61 map 이 fully enclosed (45%, room/dungeon)
  - 정밀 휴리스틱 (axis match + run length match ±1 + start ±1) 적용해도 **50 unique-match + 32 ambiguous + 158 unmatched**
  - **EXACT 매칭 (run length AND start 정확 일치): 4건 만**
  - **Symmetric (양방향 exact): 0건**
- **결론**: 자동 MapGraph 가 신뢰 가능 수준에 도달 못함. 정확한 자동화 = `_scn` opcode 디코드 후 가능 (R111+ scope).

## 1. 분석 결과

### 1.1 134 map edge 통계

```
fully enclosed (no walkable edge tiles):       61 / 134 (45%)
total exit-openings (distinct walkable runs): 268
```

### 1.2 휴리스틱 적용 (refined)

[`tools/recon/discover_map_edges.py`](../../tools/recon/discover_map_edges.py):

1. wildcard map (90%+ 모든 edge tiles walkable, ex SECRET_ROOM) 제외 — 그렇지 않으면 모든 map 이 그 map 으로 매칭됨.
2. axis 동등성 (N/S → width 같음, W/E → height 같음) ±2 tile 허용.
3. run 길이 ±1 tile 허용.
4. run 시작 위치 ±1 tile 허용.

결과:
- **unique-match: 50 edges** (다중 후보 없음, 1:1 매칭)
- **ambiguous: 32** (2+ 후보)
- **unmatched: 158** (매칭 없음)

### 1.3 EXACT 매칭 (run length & start 동일)

50 unique-match 중 EXACT 4건:

| from | name | side | to | name | run |
|---|---|---|---|---|---|
| 22 | HOLY_ALTER_2 | W | 111 | BEAST_FOREST_1 | [15, 15] |
| 79 | ENZARK_BEACON_4 | E | 122 | GUARDIAN_CAVE_5 | [10, 11] |
| 86 | LOWEN_PLAIN_1 | E | 97 | SMALL_FACTORY_1 | [15, 16] |
| 118 | GUARDIAN_CAVE_1 | E | 13 | SMALL_CAVE_3 | [6, 6] |

**Symmetric** (양방향 자동 발견): **0 건**.

→ 양방향 신뢰 가능한 자동 edge 가 없음. 임의의 4건 도 단방향 검출이라 정확도 검증 불가능.

## 2. 왜 작동하지 않는가

1. **건물/방 진입 = door tile 이지 edge walkability 아님**. ROOM_TENER (map1) 는 0 walkable edge 이지만 hardcoded `Edge(0, E, 1)` 로 NEOSOLTIA 의 building 으로 진입. door 위치는 `_scn` opcode 의 trigger 가 처리.
2. **wildcard map (SECRET_ROOM 같은)** 이 모든 edge 가 walkable 이라 naive overlap matching 에서 모든 짝과 매칭. → 45 false positive.
3. **map 간 width/height 불일치**. NEOSOLTIA 35×25 ↔ NEMESIS_FOREST_5 50×30 — 인접 map 의 dimension 이 달라서 같은 x 좌표에 exit 있을 수가 없음.
4. **hardcoded edges 자체가 비-geometric**: `Edge(0, S, 10)` → map0 S exit @ x=10 (1 tile) ↔ map10 N entry @ x=10 — 그러나 map10 의 N edge 는 모두 막혀 있음. 즉 hardcoded data 도 physical walkability 와 어긋남.

## 3. 본 라운드 변경 사항

- **MapGraph.kt 무변경**. 기존 8 hardcoded edges 그대로.
- **신규 도구**: [`tools/recon/discover_map_edges.py`](../../tools/recon/discover_map_edges.py) — 향후 `_scn` decode 후 cross-validate 용. JSON 산출 (`work/h3/map_edges.json`) 는 134 map 의 walkable edge 통계 포함.
- **베타 fidelity**: 변동 없음 (R110a 후 ~46% 유지).

## 4. 정확한 R110c 완성을 위한 선결 작업

1. ⭐⭐⭐⭐⭐ **`_scn` opcode 스트림 디코드** (10-20 dev day, Ghidra) — NPC, exit, event trigger 정보가 모두 여기 있음. 디코드되면 R110c/R110d/R110e 동시 해결 가능. 핵심 함수: 직접 본 적 없음, MD/Ghidra 분석 필요.
2. (대안) **사용자 정의 edge 직접 추가** — 원작 게임 플레이 기억 기반 사용자가 데이터 입력. UI 흐름에 익숙한 사람만 가능.

## 5. 산출 artifact

```
tools/recon/discover_map_edges.py        (134 map 의 walkable edge 분석 + pair matching)
work/h3/map_edges.json                   (분석 결과 — 50 unique + 32 ambiguous + 158 unmatched)
docs/h3/round110c-mapgraph-investigation.md   (본 문서)
```

## 6. 권장 다음 작업

R110a 후 R110b/c/d/e 4개 트랙 모두 RE 추가 작업 필요한 상태:

| 트랙 | 막힘 원인 | 다음 단계 |
|---|---|---|
| R110b 사운드 | 사용자 정책 (SMAF→OGG 변환 신뢰도) | 사용자 결정 → MediaPlayer 통합 (10-15 dev day) |
| R110c MapGraph | `_scn` opcode 미디코드 | Ghidra `_scn` interpreter 분석 |
| R110d NPC 배치 | extras_records id → sprite catalog 미해독 + `_scn` 미디코드 | R110e + R110c 의 RE 작업 양쪽 필요 |
| R110e extras catalog | 162 unique id 의 global sprite catalog 미해독 | Ghidra disasm |

**가장 큰 단일 임팩트**: R110b (사운드, 사용자 정책 필요).
**자동 가능한 차선**: **R111 = `_scn` opcode 디코드** — 이게 풀리면 R110c + R110d + 일부 R110e 까지 풀림. 단, 20-30 dev day 분석 필요.

## 7. 참고

- R110a (obj layer): [round110a-obj-layer-wiring.md](round110a-obj-layer-wiring.md)
- R110e (extras catalog): [round110e-extras-investigation.md](round110e-extras-investigation.md)
- _mp parser: [`tools/converter/convert_mp.py`](../../tools/converter/convert_mp.py)
- `_scn` 위치: ghidra-round73 등 (`scn_v2`, 245 event trigger 가 미디코드 상태)
