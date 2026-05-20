# Hero3 R109 계획 — MapWalkScene 타일 그래픽 wiring (2026-05-20 작성)

> **다음 세션 시작 시 이 문서대로 Phase 1 부터 시작**.

## 0. 배경 — "타일 디코딩"이 사실은 wiring 작업

베타 출시 진척도 평가 (2026-05-20 세션) 중 핵심 사실 정정:

- **BM `type=0x0c` 디코더는 이미 구현** — Ghidra `FUN_00010fe4 @ 0x10fe4` line 4847-4851 분석으로 *8-bit dense palette indexed, byte value 0 = transparent (skip)* 가 `tools/converter/convert_bm_v2.py` 에 반영됨 (`asset-formats.md` §_bm 갱신).
- **타일 sheet PNG 317개 추출 완료** — `assets/sprites_hd/map/`:
  - `obj_*_bm/` 44 sheet (object/decoration sprite, multi-frame 가변 크기)
  - `theme_*_bm/` 47 sheet (terrain tile sheet, 16×(N×16) 세로 strip 추정)
- **`_mp` 파싱 134/135 완료** — `assets/maps/mapNN_mp.json` 가 `meta_header_hex`, `palette`, `layer_0`, `layer_1`, `extras_records` 모두 노출.
- **MapWalkScene 만 미통합** — `grep sprites_hd/map MapWalkScene.kt` = 0 hit. `colorForTile()` 색상 그리드 fallback 그대로.

따라서 R109 = "타일 디코딩 30-50 dev day" 의 무거운 분석 작업이 **아니라**, **`_mp.meta_header_hex` ↔ tile sheet 매핑식 발견 + BitmapFactory wiring** 의 10~16 dev day wiring 작업.

베타 fidelity 진척도 영향: 그래픽 30% → 70% → 전체 ~40% → ~45%로 상향.

## 1. 입력 자료 (이미 존재)

```
android/app/src/main/assets/sprites_hd/map/
  ├─ obj_0_bm/   frame_00_32x16_tc.png, frame_01_16x16_tc.png, ...
  ├─ obj_1_bm/   …
  ├─ …
  ├─ obj_43_bm/
  ├─ theme_0_bm/   frame_00_16x480_tc.png  ← 16×480 = 30 row, terrain tile sheet 추정
  ├─ theme_1_bm/
  ├─ …
  └─ theme_46_bm/

android/app/src/main/assets/maps/
  ├─ map0_mp.json   (NEOSOLTIA)
  │   { "version":2, "meta_header_hex":"02 ?? ?? ?? ??", "name":"NEOSOLTIA",
  │     "width":W, "height":H, "palette_count":26,
  │     "palette":[34,35,36,...,61,1],
  │     "layer_0":[...W*H ints...], "layer_1":[...],
  │     "extras_records":[...] }
  ├─ map1_mp.json
  ├─ …
  └─ map99_mp.json  (134개 총)

tools/converter/
  ├─ convert_bm_v2.py   ← BM 0b/0c 디코더 (검증 완료)
  └─ convert_mp.py      ← _mp → JSON (134/135 파싱 성공)
```

## 2. 작업 가설

| ID | 가설 | 검증 방법 |
|---|---|---|
| H1 | `theme_*_bm` = terrain tile sheet (layer_0 용). 각 sheet 가 16×(N×16) 세로 strip 으로 N개 16×16 tile. | `theme_0_bm/frame_00 = 16×480` 이 30 row → 30 tile 1:1 |
| H2 | `obj_*_bm` = 개별 object/NPC sprite (layer_1 + extras 용). multi-frame, 각 frame 이 별도 oblect. | obj_0_bm 의 5 frame 가변 크기 (32×16 / 16×16 / 44×39) — 격자 아닌 sprite |
| H3 | `_mp.meta_header_hex[3]` 또는 `meta4` = theme sheet 선택 ID (0..46) | 134 맵 × 47 sheet brute-force cross-tab → fit 검증 |
| H4 | `_mp.palette[i]` (1..255) = theme sheet 내 tile row index (또는 obj sprite frame index) | NEOSOLTIA palette `[34..61, 1]` 26개 ↔ theme_X_bm 의 row 인덱스 1:1 |
| H5 | `layer_0[ty*W + tx]` = palette 인덱스. 즉 `tile_id = palette[ layer_0[i] ]` 로 row 결정. | 시각 검증 (시작 마을 의 도로/풀밭 등 명확한 패턴) |

H1~H5 모두 자동 검증 가능. 실패 시 fallback = Ghidra 에서 `_mp` 로딩 함수 disasm.

## 3. 4-Phase 작업 절차

### Phase 1 — 데이터 cross-tab 검증 (2~3 dev day)

```bash
# 신규 스크립트 1
python tools/recon/dump_tile_sheets.py \
  --in android/app/src/main/assets/sprites_hd/map \
  --out work/h3/tile_sheets.json
# 산출 형식:
#   { "theme_0_bm": { "frame_count":1, "frames":[{"w":16,"h":480,"type":"0c","rows":30}] },
#     "obj_0_bm":   { "frame_count":5, "frames":[{"w":32,"h":16,...}, ...] }, ... }
```

```bash
# 신규 스크립트 2
python tools/recon/dump_map_meta_xref.py \
  --in android/app/src/main/assets/maps \
  --out work/h3/map_meta_xref.json
# 산출 형식:
#   { "map0": {"meta_hex":"02 ?? ?? ?? ??", "name":"NEOSOLTIA", "palette":[...],
#              "palette_max":61, "palette_min":1, "layer0_uniq_count":N, ... } ... }
```

검증 산출:
- theme sheet 의 (w, rows) 분포
- map 별 palette range 분포 (1..255)
- 134 map × meta byte 변동 패턴
- layer_0 값 ↔ palette 인덱스 정합성 (sanity: `layer_0 의 모든 값 < palette_count`)

### Phase 2 — 매핑 식 자동 발견 (3~5 dev day)

```bash
# 신규 스크립트 3
python tools/recon/find_map_to_sheet_mapping.py \
  --maps work/h3/map_meta_xref.json \
  --sheets work/h3/tile_sheets.json \
  --out work/h3/map_sheet_mapping.json
# 알고리즘:
#   1. 가설 H3 후보: meta[0..4] 각 byte 가 theme sheet ID 일 확률 계산
#      (palette_max ≤ sheet.rows 인 sheet 만 후보)
#   2. 가설 H4 후보: palette 값이 sheet.rows 범위 안인 sheet 만 통과
#   3. 134 map 모두 단일 sheet 로 fit 되는 byte 위치 찾기
#      (예: meta[3] 이 모든 map 에서 정확한 sheet ID 일 가능성)
#   4. obj sheet 도 동일 알고리즘 (layer_1 의 unique 값 ↔ obj sheet frame 개수)
```

산출:
- `map_sheet_mapping.json`: `{ "map0": {"theme_sheet":"theme_X_bm", "obj_sheet":"obj_Y_bm"} ... }`
- 매핑 식 docstring (1-line summary).
- Fail-safe: 자동 발견 fit ratio 가 < 90% 이면 fallback 가이드 (Ghidra `FUN_00010ea4` 인접 함수 disasm).

만약 자동 발견이 불완전하면:
- **Fallback A**: Ghidra 에서 `_mp` 로딩 함수 disasm (이미 `FUN_00010fe4/0x10ea4` 가 BM 로더이므로 인접 함수에서 _mp 로더 발견 가능).
- **Fallback B**: 원작 에뮬레이터 (DeSmuME/Mednafen) 에서 NEOSOLTIA / BOSS_TOWN / SECRET_ROOM 진입 후 tile 시각 비교로 sheet ID 수동 매핑 (3-5개 anchor 맵, 1-2 시간).

### Phase 3 — MapWalkScene 렌더 통합 (3~5 dev day)

기존 `colorForTile(tileId, layer)` 색상 fallback → BitmapFactory + drawBitmap 로 교체.

```kotlin
// android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt

// Phase 2 결과 (build-time embed 또는 assets/map_sheet_mapping.json runtime load)
private object MapSheetMapping {
    fun themeSheetFor(mapId: Int): String = ...   // 예: "theme_4_bm"
    fun objSheetFor(mapId: Int): String = ...
}

// theme sheet 캐싱 — 16x16 tile bitmap 리스트로 split
private val themeTileCache = mutableMapOf<String, List<Bitmap>>()

private fun loadThemeTiles(sheetName: String): List<Bitmap> = themeTileCache.getOrPut(sheetName) {
    val root = "${settings.spritesDir()}/map/$sheetName"
    val frameNames = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
    val sheetBmp = context.assets.open("$root/${frameNames.first()}").use {
        BitmapFactory.decodeStream(it)
    }
    val tilePx = sheetBmp.width  // 16 (SD) or 64 (HD = 4x)
    (0 until sheetBmp.height / tilePx).map { row ->
        Bitmap.createBitmap(sheetBmp, 0, row * tilePx, tilePx, tilePx)
    }
}

// 기존 colorForTile() 4곳 호출처를 drawTile() 로 교체
private fun drawTile(canvas: Canvas, mapId: Int, paletteIdx: Int, sx: Float, sy: Float) {
    val themeName = MapSheetMapping.themeSheetFor(mapId)
    val tiles = loadThemeTiles(themeName)
    val rowIdx = currentMap.palette.getOrNull(paletteIdx) ?: return
    val bmp = tiles.getOrNull(rowIdx) ?: return
    val dst = Rect(sx.toInt(), sy.toInt(), (sx + tilePx).toInt(), (sy + tilePx).toInt())
    canvas.drawBitmap(bmp, null, dst, null)
}

// layer_1 (obj/collision) 도 동일 패턴, MapSheetMapping.objSheetFor + obj_X_bm/frame_N.png 직접 사용
```

세부:
- **HD/SD 토글 호환**: Settings 의 `spritesDir()` 이 `sprites/` / `sprites_hd/` 결정 — 기존 hero/enemy sprite 로딩 패턴 그대로.
- **메모리 관리**: 134 맵 × 91 sheet 모두 미리 로드하면 OOM 위험. `themeTileCache` 가 lazy load + 맵 이동 시 stale entry 정리.
- **fallback**: 매핑 lookup 실패 시 기존 `colorForTile()` 호출 → degrade gracefully (placeholder 보존).

### Phase 4 — 시각 검증 + 회귀 (2~3 dev day)

```bash
# 신규 스크립트 4
python tools/qa/render_all_maps.py \
  --maps android/app/src/main/assets/maps \
  --tiles android/app/src/main/assets/sprites_hd/map \
  --mapping work/h3/map_sheet_mapping.json \
  --out work/h3/qa/map_renders
# 134 map 각 PNG 렌더 → 일괄 시각 확인.
```

원작 비교:
- NEOSOLTIA (map0): 도시 도로 / 건물 / NPC 위치
- BOSS_TOWN: 보스 마을 구조
- GUARDIAN_CAVE_1: 동굴 통로
- SECRET_ROOM: 비밀 방 단순 구조

unit test (engine):
- `MapWalkSceneTest` 가능하면 (Android Bitmap 의존이라 instrumented test 필요할 수 있음)
- 또는 Phase 1/2 의 mapping 결정성 만 commonTest 에서 검증.

## 4. R110 ~ 후속 (참고)

타일 wiring 이 끝나면 시각 fidelity 가 70% → ~90% 수준으로 점프. 그 다음 베타 critical-path:

1. **사운드 정책 결정** — SMAF→OGG 33곡 변환 + `SfxBus.play()` MediaPlayer/SoundPool 통합 (10~15 dev day). 사용자 신뢰도 정책 재확인 필요.
2. **MapGraph 자동 생성** — `_mp.extras_records` 의 exit 정보 추출로 134 맵 모두 연결 (10~15 dev day).
3. **NPC 자동 배치** — `_mp.extras_records` 안의 NPC marker → 원작 위치에 배치 (20~30 dev day).
4. **Dialogue 통합 + 번역** — 9,740 라인 → scn_v2 245 event trigger 연결 + LLM 한↔영 번역 (10~30 dev day).
5. **출시 패키징** — ic_launcher 5종 + release keystore + ProGuard + Play Console metadata (3~5 dev day).

## 5. 다음 세션 빠른 시작

```bash
# 1) git pull / 현재 상태 확인
git log --oneline -5
# 마지막 commit 기대값: R108 — Party debuff render UI ... (d14053c3) 또는 docs(h3) commit

# 2) Phase 1 시작
mkdir -p tools/recon work/h3
$EDITOR tools/recon/dump_tile_sheets.py     # 본 문서 §3 Phase 1 참고
$EDITOR tools/recon/dump_map_meta_xref.py

# 3) 결과 확인
python tools/recon/dump_tile_sheets.py --in android/app/src/main/assets/sprites_hd/map --out work/h3/tile_sheets.json
python tools/recon/dump_map_meta_xref.py --in android/app/src/main/assets/maps --out work/h3/map_meta_xref.json
cat work/h3/tile_sheets.json | jq '.theme_0_bm'
cat work/h3/map_meta_xref.json | jq '.map0'
```

## 6. 참고 docs

- [SESSION_HANDOFF.md](SESSION_HANDOFF.md) — R109 가이드 + 베타 진척도 평가
- [asset-formats.md](../asset-formats.md) §_bm / §_mp — 자료 포맷 (R109 직전 0x0c stale 정정 완료)
- `tools/converter/convert_bm_v2.py` — 0b/0c 디코더 reference (Ghidra FUN_00010fe4 분석 반영)
- `tools/converter/convert_mp.py` — _mp 파서 reference
- Round 73 [DES 성공 + SMAF pipeline](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md) — 사운드 트랙 stale 가이드 (정책 재검토 필요)
