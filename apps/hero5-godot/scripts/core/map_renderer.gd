## Map 렌더러.
##
## mapID 가 주어지면 4개 레이어 합성:
##   - tile_NNN.gbm : 배경 타일
##   - obj_NNN.gbm  : 오브젝트 (집/나무 등)
##   - fgi_NNN.gbm  : 전경 (캐릭터 위에 표시되는 요소)
##   - face_NN.gbm  : NPC/캐릭터 얼굴 (UI 다이얼로그용)
##
## 원본은 OpenGL ES 1.x 로 BlitImage 했지만 Godot 4 는 Sprite2D 노드로 충분.
class_name MapRenderer
extends Node2D

@export var map_id: int = 0:
	set(value):
		map_id = value
		_rebuild()

var _tile_sprite: Sprite2D
var _obj_sprite: Sprite2D
var _fgi_sprite: Sprite2D

# collision data (tools/converter/convert_h5_collision.py 산출)
var _col_width: int = 0
var _col_height: int = 0
var _col_data: PackedByteArray = []
const TILE_SIZE := 32  # Map::MapSetData 의 0x20 (= 32)


func _ready() -> void:
	_tile_sprite = Sprite2D.new(); _tile_sprite.centered = false
	_obj_sprite = Sprite2D.new(); _obj_sprite.centered = false
	_fgi_sprite = Sprite2D.new(); _fgi_sprite.centered = false
	add_child(_tile_sprite)
	add_child(_obj_sprite)
	add_child(_fgi_sprite)
	_rebuild()


func _rebuild() -> void:
	if not _tile_sprite: return
	_tile_sprite.texture = _try_load("tile", map_id)
	_obj_sprite.texture  = _try_load("obj",  map_id)
	_fgi_sprite.texture  = _try_load("fgi",  map_id)
	_load_collision()


func _load_collision() -> void:
	var meta_path := "res://assets/maps/%02d.json" % map_id
	var col_path := "res://assets/maps/%02d.col.bin" % map_id
	_col_data = PackedByteArray()
	_col_width = 0
	_col_height = 0
	if not FileAccess.file_exists(meta_path) or not FileAccess.file_exists(col_path):
		return
	var meta_f := FileAccess.open(meta_path, FileAccess.READ)
	var meta = JSON.parse_string(meta_f.get_as_text())
	if meta is Dictionary:
		_col_width = int(meta.get("width", 0))
		_col_height = int(meta.get("height", 0))
	var col_f := FileAccess.open(col_path, FileAccess.READ)
	_col_data = col_f.get_buffer(col_f.get_length())


## 스폰된 NPC 위치 캐시 (인터랙션 거리 체크용).
##   {idx, tile_x, tile_y, sprite_id}
var spawned_npcs: Array = []


## (px, py) 의 N tile 이내 가장 가까운 NPC 반환 (없으면 -1).
func nearest_npc(px: int, py: int, max_tile_dist: int = 2) -> int:
	if spawned_npcs.is_empty(): return -1
	var tx = px / TILE_SIZE
	var ty = py / TILE_SIZE
	var best_dist = max_tile_dist + 1
	var best_idx = -1
	for npc in spawned_npcs:
		var dx = abs(int(npc.tile_x) - tx)
		var dy = abs(int(npc.tile_y) - ty)
		var d = dx + dy  # Manhattan
		if d < best_dist:
			best_dist = d
			best_idx = int(npc.idx)
	return best_idx


## NPC 스폰 (npc_table.json 의 flags[2..3] = tile x,y).
##   현재 mapID 와 무관하게 첫 N 개 valid NPC 를 표시 (demo).
func spawn_npcs(parent: Node2D, max_count: int = 8) -> void:
	spawned_npcs.clear()
	# 기존 NPC 제거
	for c in parent.get_children():
		if c.name.begins_with("NPC_"):
			c.queue_free()
	var p := "res://assets/gamedata/npc_table.json"
	if not FileAccess.file_exists(p): return
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if not data is Array: return
	var spawned := 0
	for r in data:
		if spawned >= max_count: break
		var flags = r.get("flags", [])
		if flags.size() < 4: continue
		var sprite_id = int(flags[0])
		var tx = int(flags[2])
		var ty = int(flags[3])
		if sprite_id == 0xFF or tx == 0xFF or ty == 0xFF: continue
		if tx == 0 and ty == 0: continue
		# NPC 종류 분류 (flags[6] = npc type 추정)
		# flags[6] != 0xFF 이면 적대적/특수 NPC, 아니면 일반 NPC
		var npc_type := int(flags[6]) if flags.size() > 6 else 0xFF
		var npc_color: Color
		if npc_type == 0xFF: npc_color = Color(0.4, 0.8, 1.0, 0.85)  # 일반 (cyan)
		elif npc_type < 30: npc_color = Color(1.0, 0.4, 0.4, 0.85)   # 적대 (red)
		elif npc_type < 60: npc_color = Color(1.0, 0.85, 0.3, 0.85)  # 상인 (yellow)
		else: npc_color = Color(0.5, 1.0, 0.5, 0.85)                  # 퀘스트 (green)
		# 실제 sprite 텍스처 시도
		var marker: Node2D
		var tex = _try_load_npc_sprite(sprite_id)
		if tex:
			var spr = Sprite2D.new()
			spr.texture = tex
			spr.modulate = npc_color  # 색조 반영
			spr.centered = false
			spr.position = Vector2(tx * TILE_SIZE + 4, ty * TILE_SIZE)
			marker = spr
		else:
			var rect = ColorRect.new()
			rect.color = npc_color
			rect.size = Vector2(TILE_SIZE * 0.8, TILE_SIZE * 0.8)
			rect.position = Vector2(tx * TILE_SIZE, ty * TILE_SIZE)
			marker = rect
		marker.name = "NPC_%d" % r.get("idx", 0)
		parent.add_child(marker)
		# label
		var lbl := Label.new()
		lbl.text = "N%d" % r.get("idx", 0)
		lbl.position = Vector2(tx * TILE_SIZE, ty * TILE_SIZE - 12)
		lbl.add_theme_font_size_override("font_size", 9)
		parent.add_child(lbl)
		spawned_npcs.append({
			"idx": int(r.get("idx", 0)),
			"tile_x": tx, "tile_y": ty,
			"sprite_id": sprite_id,
			"npc_type": npc_type,
		})
		spawned += 1


## 디버그 오버레이 토글 (collision 가시화).
@export var show_collision_debug: bool = false:
	set(value):
		show_collision_debug = value
		queue_redraw()


func _draw() -> void:
	if not show_collision_debug or _col_data.is_empty():
		return
	for ty in _col_height:
		for tx in _col_width:
			var idx = ty * _col_width + tx
			if idx >= _col_data.size(): break
			var v = _col_data[idx]
			var color: Color
			if v == 0 or v == 2:
				color = Color(0, 1, 0, 0.2)   # 통과
			else:
				color = Color(1, 0, 0, 0.4)   # 막힘
			draw_rect(Rect2(tx * TILE_SIZE, ty * TILE_SIZE,
					TILE_SIZE, TILE_SIZE), color, true)


## (x, y) 픽셀 좌표 → collision 값 (0 = 통과, 그 외 = 막힘).
## CHAR 의 _physics_process 가 부르는 collision_at(int, int) API.
func collision_at(px: int, py: int) -> int:
	if _col_width == 0 or _col_data.is_empty():
		return 0  # 데이터 없으면 통과
	var tx := px / TILE_SIZE
	var ty := py / TILE_SIZE
	if tx < 0 or tx >= _col_width or ty < 0 or ty >= _col_height:
		return 1  # 범위 밖 = 막힘
	var idx := ty * _col_width + tx
	if idx >= _col_data.size():
		return 1
	# Map::MoveTileCheck: 통과 = (val == 0 || val == 2)
	var v := _col_data[idx]
	if v == 0 or v == 2:
		return 0
	return v


## warp tile 감지 — collision value 가 0x40+ 범위면 다음 scene id (간이 룰).
##   원본은 별도 warp table 사용하지만, 우리는 high collision 값을 warp 마커로.
signal warp_triggered(target_scene: int)


func check_warp(px: int, py: int) -> int:
	if _col_data.is_empty(): return -1
	var tx := px / TILE_SIZE
	var ty := py / TILE_SIZE
	if tx < 0 or tx >= _col_width or ty < 0 or ty >= _col_height:
		return -1
	var idx := ty * _col_width + tx
	if idx >= _col_data.size(): return -1
	var v := _col_data[idx]
	# 0x40-0x7F 범위 = warp marker (룰 가설)
	if v >= 0x40 and v < 0x80:
		var target_scene = v - 0x40
		warp_triggered.emit(target_scene)
		return target_scene
	return -1


func _try_load(prefix: String, idx: int) -> Texture2D:
	for digits in [3, 2]:  # try 3-digit then 2-digit
		var fmt := "res://assets/gbm/map/%s_%0*d.png" % [prefix, digits, idx]
		if FileAccess.file_exists(fmt):
			return load(fmt)
	return null


## 캐릭터/NPC 페이스 이미지 (대화 UI 용).
static func get_face(idx: int) -> Texture2D:
	var p := "res://assets/gbm/map/face_%02d.png" % idx
	if FileAccess.file_exists(p):
		return load(p)
	return null


## sprite_id 로 NPC 첫 frame 텍스처 시도 (img0/NNN/frame_00_*.png).
func _try_load_npc_sprite(sprite_id: int) -> Texture2D:
	for cat in range(7):
		var dir := "res://assets/sprites/img%d/%03d" % [cat, sprite_id]
		if not DirAccess.dir_exists_absolute(dir): continue
		var d := DirAccess.open(dir)
		if d == null: continue
		d.list_dir_begin()
		var fname := d.get_next()
		while fname != "":
			if fname.begins_with("frame_00") and fname.ends_with(".png"):
				return load(dir + "/" + fname)
			fname = d.get_next()
	return null
