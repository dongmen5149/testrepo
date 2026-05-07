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
