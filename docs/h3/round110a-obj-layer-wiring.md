# Hero3 Round 110a — MapWalkScene obj layer wiring (Phase 1~4) — 2026-05-20

> R110a: layer_1 obj sprite 통합. R109 (theme = layer_0) 의 자연스러운 후속.

## 0. TL;DR

- **매핑 식**: `layer_1[i] >> 6 = frame_idx` in `obj_<byte[0]>_bm` (즉 theme sheet 와 동일 ID). 134 maps 의 99%+ layer_1 value 가 정확히 `frame_idx << 6` (low 6 bits = 0).
- **anchor**: bottom-center — sprite 의 (width/2, height) 점이 tile 의 (mid, bottom) 에 정렬. NEOSOLTIA/BOSS_TOWN/SECRET_ROOM/GUARDIAN_CAVE_1 모두 시각 검증 통과.
- **Android wiring**: `MapWalkScene.kt` 에 `objFrameCache` + `loadObjFrames()` 추가. Layer 1 render loop 가 색상 placeholder → drawBitmap 으로 교체 (graceful fallback 유지).
- **회귀**: `:app:testDebugUnitTest` / `:engine-core:testDebugUnitTest` 모두 BUILD SUCCESSFUL.

## 1. layer_1 raw 분포 분석

134 map 중:
- **layer_1 max = 192** (=3<<6): 125 maps
- layer_1 max = 255: 8 maps
- layer_1 max = 64: 1 map

NEOSOLTIA (map0) layer_1: 597 nonzero / 875 tiles (68%). **4 distinct values: 64/128/192/(6)**.

| 값 | count | decomp (>>6, &63) |
|---|---|---|
| 128 | 466 | (2, 0) |
| 192 | 75 | (3, 0) |
| 64 | 55 | (1, 0) |
| 6 | 1 | (0, 6) ← 단일 outlier |

→ `frame_idx = value >> 6`, low 6 bits 는 거의 항상 0.

**134-map 스캔**: 56 maps 가 100% 정합 (모든 nonzero 가 frame<<6), 78 maps 가 1-2개 outlier (보통 1 occurrence). 약 99%+ 정합.

## 2. obj sheet 구조

44 obj_*_bm sheets, 분포:
- 5 frames per sheet: 39 sheets (대다수)
- 4 frames: 3 sheets
- 2 frames: 1 sheet
- 52 frames: 1 sheet (이상치)

각 frame 은 **개별 sprite** (uniform strip 아님). 크기 변동:
- 16×16: 모든 sheet 에 1개씩 (44개) — 통상 wall/block frame
- 16×32, 32×16, 24×32, 80×63 등 — 건물 / 가구 / 기둥

NEOSOLTIA의 `obj_6_bm`:
```
frame_00 24x32  tb (건물?)
frame_01 10x42  tc (가로등?)
frame_02 16x16  tc (벽 / 길)
frame_03 9x15   tc (작은 장식)
frame_04 80x63  tc (대형 건물 — layer_1 4<<6=256 > 255 이라 layer_1 미경유)
```

layer_1 max 가 192=3<<6 인 이유: frame 4 (큰 건물) 는 layer_1 로 배치 안 됨. 추정 위치 = `extras_records` 또는 별도 map data.

## 3. 시각 검증 (Phase 3)

[`tools/qa/render_map_with_obj.py`](../../tools/qa/render_map_with_obj.py) 가 anchor 4개 × {bottom_center, top_left} = 8 PNG 산출 (`work/h3/qa/obj_renders/`).

| map | 결과 |
|---|---|
| map0 NEOSOLTIA (35x25) | 풀밭 + 건물 외곽 + 가로등 + 작은 장식 — 마을 layout 명확 |
| map44 SECRET_ROOM (30x20) | 외곽 돌벽 + 던전 내부 구조 + 입구 — dungeon room 명확 |
| map126 BOSS_TOWN (20x20) | castle/palace 외벽 + 중앙 courtyard + 문/창문 — 정확 |
| map118 GUARDIAN_CAVE_1 (30x35) | 동굴 통로 + 천연 장애물 — 정확 |

**bottom_center** 가 정답 — 가로등/기둥 같은 tall sprite 가 tile 바닥에 서 있음. top_left 는 tile 상단부터 뜨여 어색.

## 4. Android wiring ([MapWalkScene.kt](../../android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt))

### 4.1 추가 항목

```kotlin
/** R110a: obj sheet ID → frame_idx → 가변 크기 sprite bitmap. lazy load. */
private val objFrameCache: MutableMap<Int, Map<Int, Bitmap>> = mutableMapOf()

private fun loadObjFrames(objId: Int): Map<Int, Bitmap>? {
    if (objId < 0) return null
    objFrameCache[objId]?.let { return it }
    val dir = "${settings.spritesDir()}/map/obj_${objId}_bm"
    return runCatching {
        val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
        if (files.isEmpty()) return@runCatching null
        val framePat = Regex("frame_(\\d+)_")
        val map = mutableMapOf<Int, Bitmap>()
        for (f in files) {
            val m = framePat.find(f) ?: continue
            val idx = m.groupValues[1].toInt()
            map[idx] = context.assets.open("$dir/$f").use { BitmapFactory.decodeStream(it) }
        }
        map.toMap()
    }.getOrNull()?.also { objFrameCache[objId] = it }
}
```

### 4.2 Layer 1 render 교체

```kotlin
val objFrames = if (m.themeId >= 0) loadObjFrames(m.themeId) else null
for (ty in ty0 until ty1) {
    for (tx in tx0 until tx1) {
        // ...
        val sprite = objFrames?.get(tileId shr 6)
        if (sprite != null) {
            val sx = px + (tilePx - sprite.width) / 2     // bottom-center
            val sy = py + (tilePx - sprite.height)
            canvas.drawBitmap(sprite, sx.toFloat(), sy.toFloat(), null)
        } else {
            // R109 와 동일 fallback
            tilePaint.color = colorForTile(tileId, layer = 1)
            canvas.drawRect(...)
        }
    }
}
```

Top-down loop 순서로 그려 perspective overlap (남쪽 sprite 가 북쪽 위에) 자동.

### 4.3 회귀

```
./gradlew.bat :app:compileDebugKotlin            → BUILD SUCCESSFUL
./gradlew.bat :app:testDebugUnitTest             → BUILD SUCCESSFUL
./gradlew.bat :engine-core:testDebugUnitTest     → BUILD SUCCESSFUL
```

## 5. 베타 출시 진척도 영향

- 그래픽 영역: R109 후 90% → R110a 후 **~95%**.
- 전체 베타 fidelity: R109 후 44% → **~46%** (+ 2%p, 가중치 10%).

## 6. 미해결 / 후속 (R110b+)

1. **Frame 4 (≥80px) 대형 건물 배치** — layer_1 미경유. `extras_records` 의 type=0/128/id-N 의미 정확 해독 필요.
2. **`extras_records` decoration table** — 전 map 공유 글로벌 sprite catalog 인지, 또는 map-specific 인지. 현재 `colorForDecoId(id)` 의 hardcoded palette 가 정답인지 확인 필요.
3. **콜리전 체크** — 현 `isWalkable()` 는 `layer_1[i] == 0` 만 검사. obj 가 큰 sprite 라면 다중 tile collision 필요.
4. **Animation** — `frame_04_*_tb.png` 의 `tb` (transparency black) suffix vs `tc` 차이. 정적 sprite 아닌 animated 가능성.
5. **sprObj*_bm 8 sheets** — 별도 NPC sprite sheet 추정. layer_1 미경유. extras_records 의 NPC 마커 와 매핑 가능성.

## 7. 산출 artifact

```
tools/qa/render_map_with_obj.py        (anchor 4 × 2 anchor = 8 PNG)
work/h3/qa/obj_renders/                (시각 검증 결과)
android/.../MapWalkScene.kt            (objFrameCache + loadObjFrames + drawBitmap loop)
```

## 8. 참고

- R109: [round109-map-tile-wiring-phase1-3.md](round109-map-tile-wiring-phase1-3.md)
- BM 디코더: [`tools/converter/convert_bm_v2.py`](../../tools/converter/convert_bm_v2.py)
- _mp 파서: [`tools/converter/convert_mp.py`](../../tools/converter/convert_mp.py)
