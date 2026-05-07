## 우상단 미니맵 — collision 데이터 + 플레이어/NPC 위치 표시.
class_name MiniMap
extends CanvasLayer

const MAP_SIZE := Vector2(64, 64)
const MAP_POS := Vector2(248, 36)

var _map_renderer: Node2D = null
var _hero: Node2D = null
@onready var canvas: Control = $Canvas


func _ready() -> void:
	canvas.draw.connect(_redraw)


func bind(map_renderer: Node2D, hero: Node2D) -> void:
	_map_renderer = map_renderer
	_hero = hero


func _process(_dt: float) -> void:
	if _map_renderer and _hero:
		canvas.queue_redraw()


func _redraw() -> void:
	if _map_renderer == null: return
	var col_data: PackedByteArray = _map_renderer._col_data
	var col_w = _map_renderer._col_width
	var col_h = _map_renderer._col_height
	if col_w == 0 or col_h == 0:
		canvas.draw_rect(Rect2(Vector2.ZERO, MAP_SIZE), Color(0, 0, 0, 0.5))
		return
	# 배경
	canvas.draw_rect(Rect2(Vector2.ZERO, MAP_SIZE), Color(0, 0, 0, 0.6))
	# tile 별 색
	var sx = MAP_SIZE.x / float(col_w)
	var sy = MAP_SIZE.y / float(col_h)
	for ty in col_h:
		for tx in col_w:
			var idx = ty * col_w + tx
			if idx >= col_data.size(): break
			var v = col_data[idx]
			var c: Color
			if v == 0 or v == 2: c = Color(0.2, 0.5, 0.2, 0.8)  # 통과 (녹)
			elif v >= 0x40 and v < 0x80: c = Color(1, 0.9, 0.2, 0.9)  # warp
			else: c = Color(0.4, 0.2, 0.1, 0.8)  # 막힘
			canvas.draw_rect(Rect2(tx * sx, ty * sy, max(1, sx), max(1, sy)), c)
	# 플레이어 마커
	if _hero:
		var px = _hero.position.x / 32.0 * sx
		var py = _hero.position.y / 32.0 * sy
		canvas.draw_circle(Vector2(px, py), 2, Color.YELLOW)
	# NPC 마커
	for npc in _map_renderer.spawned_npcs:
		var nx = int(npc.tile_x) * sx
		var ny = int(npc.tile_y) * sy
		canvas.draw_circle(Vector2(nx, ny), 1.5, Color(0.4, 0.8, 1))
