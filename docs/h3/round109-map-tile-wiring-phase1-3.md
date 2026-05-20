# Hero3 Round 109 — MapWalkScene 타일 그래픽 wiring (Phase 1~3) — 2026-05-20

> R109 4-Phase 중 Phase 1 (데이터 cross-tab) + Phase 2 (매핑 식 자동 발견) + Phase 3 (Android wiring) 완료. Phase 4 (시각 회귀) 는 anchor 4개로 검증 완료, 134 map 전체 PNG 일괄 렌더 산출.
>
> 다음 작업 = R110 (사운드 정책 결정 / obj layer 통합 / NPC 자동 배치 중 택일).

## 0. TL;DR

- **매핑 식 발견**: `meta_header_hex` 의 첫 byte = theme sheet ID. `theme_<id>_bm/frame_00_*.png` 을 16×16 strip 으로 split → `layer_0[i] >> shift` 가 row index. shift 는 `(layer_0.max() >> s) < rows` 가 최초 성립하는 s.
- **데이터 검증**: 134/134 map 모두 일관적으로 렌더됨. anchor 4개 (NEOSOLTIA / SECRET_ROOM / BOSS_TOWN / GUARDIAN_CAVE_1) 가 시각적으로 합리적인 결과 (요새 / 던전 / 동굴 구조).
- **Android wiring**: [`MapWalkScene.kt`](../../android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt) 에 `themeId/themeShift/themeTileCache` + `loadThemeTiles()` + drawBitmap 통합. 색상 fallback 도 보존 (graceful degrade).
- **회귀**: `:app:testDebugUnitTest` / `:engine-core:testDebugUnitTest` 둘 다 BUILD SUCCESSFUL. `compileDebugKotlin` 성공.

## 1. Phase 1 — 데이터 cross-tab 산출

### 1.1 [`tools/recon/dump_tile_sheets.py`](../../tools/recon/dump_tile_sheets.py)

99 sheets:
- theme_*_bm: 47 (id 0..46)
- obj_*_bm: 44 (id 0..43)
- sprObj0..6_bm + sprObj_0_bm: 8 (legacy spr objects)

theme sheet 의 첫 PNG (`frame_00_16xH_tc.png`) strip_rows 분포: min=1 max=32. 16×16 tile 의 세로 strip.

### 1.2 [`tools/recon/dump_map_meta_xref.py`](../../tools/recon/dump_map_meta_xref.py)

134 maps. 핵심 통계:
- `palette`: min∈[0..3], max∈[1..216]
- `layer_0` max: 74..255 across maps
- `layer_1` max: 64..255
- `meta_bytes` 길이: 67 maps × 4 bytes + 67 maps × 5 bytes (이분법)
- byte 별 unique 값:
  - byte[0]: 0..46, 23 unique  ← **theme sheet ID 후보**
  - byte[1]: 1..46, 22 unique
  - byte[2]: 1..45, 16 unique
  - byte[3]: 1..71, 8 unique
  - byte[4]: 65..70 (67 map 에만 존재)
- `meta4` field: scattered 0..209 (28 unique)
- **`1` 의 첫 등장 위치**: byte[1]에 9 map, byte[2]에 63 map, byte[3]에 62 map → **`1` 은 sheet ID 리스트의 종결 marker** 추정.

따라서 meta_header 구조:
```
[sheet_id_1, sheet_id_2, (sheet_id_3?), 0x01, terminator_byte]
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        terminator + 65..70 또는 71
```

## 2. Phase 2 — 매핑 식 자동 발견

### 2.1 [`tools/recon/find_map_to_sheet_mapping_v2.py`](../../tools/recon/find_map_to_sheet_mapping_v2.py)

각 map 의 layer_0 전체 값을 후보 theme sheet 의 row count 대비 `>> shift` 적합도 검사. 100% 적합 (모든 값이 sheet 안에 들어감) 한 byte 위치 카운트:

| byte 위치 | theme 적합 count | obj 적합 count |
|---|---|---|
| byte[0] | **134/134** | 133/134 |
| byte[1] | 133/134 | 127/134 |
| byte[2] | 134/134 | 132/134 |
| byte[3] | 67/134 | 67/134 (4-byte 한정) |

byte[0]/byte[1]/byte[2] 모두 100% 가까운 적합도 → 데이터만으로는 disambiguate 불가능. **시각 anchor 비교 필요**.

### 2.2 시각 anchor disambiguation ([`tools/qa/render_map_candidates.py`](../../tools/qa/render_map_candidates.py))

4개 anchor map × 3-4 byte 후보 = 14 PNG 렌더 (work/h3/qa/candidate_renders).

| map | byte[0] sheet | byte[1] sheet | byte[2] sheet | byte[3] sheet |
|---|---|---|---|---|
| map0 NEOSOLTIA | theme_6: 균일 grass | theme_7: 노이즈 패턴 | theme_1: yellow town tile | — |
| map44 SECRET_ROOM | **theme_34: 명확한 stone room** ✓ | theme_35: 부서진 패턴 | theme_36: 어두운 갈색 | theme_1: 노란 town tile |
| map126 BOSS_TOWN | **theme_41: 화려한 castle** ✓ | theme_42: sandy room | theme_1: 노란 town tile | — |
| map118 GUARDIAN_CAVE_1 | **theme_38: 동굴 통로** ✓ | theme_15: 분홍 동굴 | theme_16: 어두운 굴 | theme_1: 노란 town tile |

**결정적 disambiguation**: map44/126/118 모두 byte[0] 가 *원작 dungeon/castle/cave 의 시각적 정체성과 일치*. byte[2]=1 이 빈번한 이유는 단순 종결 marker; theme_1_bm 은 우연히 yellow town tile 의 fallback 시각 패턴이라 visually noisy 한 false positive.

map0 NEOSOLTIA 가 byte[0]=theme_6 (균일 grass) 으로 보이는 이유: **town 의 buildings 는 layer_0 terrain 이 아닌 layer_1 obj sheet 에 들어 있음**. 따라서 layer_0 단독 렌더는 풀밭 + 약간의 sand 만 정상.

### 2.3 134 map universal 검증 ([`tools/qa/render_all_maps_byte0.py`](../../tools/qa/render_all_maps_byte0.py))

`byte[0]` 규칙으로 134 map 일괄 렌더. 산출: `work/h3/qa/all_maps/` (134 PNG) + `all_maps_grid.png` (thumbnail 12-column grid).

결과: **134/134 성공, 오류 0**. 다양한 biome (green forest, yellow desert, blue water, brown cave, purple dungeon, red lava) 이 시각적으로 분리 가능. 최종 확정.

### 2.4 최종 매핑 식

```
theme_sheet_id  = meta_header_hex[0..2]  (즉 첫 byte)
theme_sheet_dir = "{spritesDir}/map/theme_{theme_sheet_id}_bm"
tile_pixel      = sheet.width            (보통 16)
rows            = sheet.height / tile_pixel
shift           = smallest s in 0..7 s.t. (layer_0.max() >> s) < rows
row_index       = layer_0[i] >> shift
tile_bitmap     = sheet.crop(0, row_index*tile_pixel, tile_pixel, (row_index+1)*tile_pixel)
```

## 3. Phase 3 — Android wiring

### 3.1 [`MapWalkScene.kt`](../../android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt) 변경 요약

1. `MapData` 에 `themeId: Int = -1`, `themeShift: Int = 0` 추가.
2. `themeTileCache: MutableMap<Int, List<Bitmap>>` 필드 (id 별 lazy load, 메모리 cap 없음 — 134 map × 16×16×rows ≈ 700KB).
3. `parseFirstHexByte(s: String): Int` 헬퍼.
4. `loadThemeTiles(themeId: Int): List<Bitmap>?` — `theme_<id>_bm/frame_00*.png` 을 strip 으로 split.
5. `loadMap()` 가 `meta_header_hex` 의 첫 byte 와 `layer_0.max()` 로 shift 계산.
6. Layer 0 렌더 loop 가 `loadThemeTiles(themeId)?.get(tileId shr shift)` lookup → `canvas.drawBitmap`. 실패 시 기존 `colorForTile()` 색상 grid fallback (graceful degrade).

Layer 1 (obj/collision) 은 이번 R109 scope 외 — 색상 placeholder 유지. 다음 라운드 / sub-phase 에서 obj_*_bm multi-frame 통합.

### 3.2 회귀

```
./gradlew.bat :app:compileDebugKotlin     → BUILD SUCCESSFUL
./gradlew.bat :app:testDebugUnitTest      → BUILD SUCCESSFUL  (catalog tests)
./gradlew.bat :engine-core:testDebugUnitTest → BUILD SUCCESSFUL  (engine tests)
```

## 4. Phase 4 — 시각 회귀 (anchor 통과)

- map0 NEOSOLTIA, map44 SECRET_ROOM, map126 BOSS_TOWN, map118 GUARDIAN_CAVE_1: byte[0] 후보가 명확한 정답 → §2.2 시각 비교 통과.
- 134 map 전체 thumbnail grid: biome 분리 가능, 무너진 map 없음 → §2.3 universal 통과.
- instrumented test (Android Bitmap loader 의존) 는 시행 안 함 — emulator 셋업 필요. 다음 라운드 후보.

## 5. 베타 출시 진척도 영향 (예상)

R108 시점 그래픽 영역 ~70% → R109 wiring 후 **~90%** (layer_0 + theme sheet 완성). layer_1 obj 통합 시 ~95-97% 도달 가능.

전체 베타 진척도 (가중 평균):
- R108 끝: ~42%
- R109 후 (그래픽 +20%p × 가중치 10% = +2%p): **~44%**

## 6. 다음 R110 후보 (우선순위)

1. ⭐⭐⭐⭐⭐ **R110a obj layer wiring** — `obj_<byte[0]>_bm` multi-frame sprite 를 layer_1 에 통합. 작업량 3-5 dev day (이번 R109 의 약 절반). 그래픽 ~90% → ~95%.
2. ⭐⭐⭐⭐⭐ **R110b 사운드 정책 결정** — SMAF→OGG 33곡 + `SfxBus.play()` MediaPlayer 통합. 사용자 신뢰도 정책 재확인 필요. 10-15 dev day.
3. ⭐⭐⭐⭐ **R110c MapGraph 자동 생성** — `_mp.extras_records` 의 exit 정보로 134 map 모두 연결. 10-15 dev day.

추천: 시각 fidelity 동력 유지 차원에서 **R110a obj layer wiring 부터**.

## 7. 산출 artifact 목록

```
tools/recon/dump_tile_sheets.py          (Phase 1 step 1)
tools/recon/dump_map_meta_xref.py        (Phase 1 step 2)
tools/recon/find_map_to_sheet_mapping.py (Phase 2 v1 — proxy)
tools/recon/find_map_to_sheet_mapping_v2.py (Phase 2 v2 — raw)
tools/qa/render_map_candidates.py        (anchor disambiguation)
tools/qa/render_all_maps_byte0.py        (universal verification)

work/h3/tile_sheets.json
work/h3/map_meta_xref.json
work/h3/map_sheet_mapping.json
work/h3/map_sheet_mapping_v2.json
work/h3/qa/candidate_renders/  (14 PNG)
work/h3/qa/all_maps/           (134 PNG)
work/h3/qa/all_maps_grid.png   (thumbnail grid)
work/h3/qa/all_maps_summary.json

android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt  (수정)
```

work/ 의 산출은 commit 에서 제외 (재현 가능). 필요 시 `python tools/qa/render_all_maps_byte0.py ...` 로 재생성.

## 8. 참고

- 직전 plan: [r109-plan-map-tile-wiring.md](r109-plan-map-tile-wiring.md)
- 이전 round: [SESSION_HANDOFF.md](SESSION_HANDOFF.md) §1
- BM 디코더: [`tools/converter/convert_bm_v2.py`](../../tools/converter/convert_bm_v2.py)
- _mp 파서: [`tools/converter/convert_mp.py`](../../tools/converter/convert_mp.py)
