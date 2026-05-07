## 통합 데모: Map + Character + Interpreter (basic).
##
## ① Map 렌더러로 mapID 의 4-layer 합성
## ② Character 가 .scn 헤더의 startX/Y/dir 위치에 스폰
## ③ Interpreter 가 .scn body 의 첫 몇 opcode 를 실행 (현재는 console log)
extends Node2D

const MapRenderer = preload("res://scripts/core/map_renderer.gd")
const Character = preload("res://scripts/core/character.gd")
const Interp = preload("res://scripts/core/interpreter.gd")

@onready var status: Label = $UI/Status

var _map: Node2D
var _hero: Sprite2D
var _scene_index: Array = []
var _scene_idx: int = 0


func _ready() -> void:
	_map = MapRenderer.new()
	add_child(_map)
	_load_scene_index()
	_hero = _spawn_hero()
	add_child(_hero)
	_apply_scene()


func _load_scene_index() -> void:
	var p := "res://assets/scenes/index.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Array: _scene_index = data


func _spawn_hero() -> Sprite2D:
	var c = Character.new()
	# 적당한 캐릭터 sprite 디렉토리 — 첫 sprites/img0/0NN
	c.sprite_dir = "res://assets/sprites/img0/000"
	c.position = Vector2(160, 240)
	return c


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_M:
				_map.map_id = (_map.map_id + 1) % 200
				_update_status()
			KEY_N:
				if _scene_index.size() > 0:
					_scene_idx = (_scene_idx + 1) % _scene_index.size()
					_apply_scene()


func _apply_scene() -> void:
	if _scene_index.size() == 0: return
	var s = _scene_index[_scene_idx]
	_map.map_id = int(s.get("mapID", 0))
	_hero.position = Vector2(
		int(s.get("startX", 160)),
		int(s.get("startY", 240)))
	_update_status()
	_run_intro(s)


func _update_status() -> void:
	if _scene_index.size() == 0:
		status.text = "mapID=%d  (no scene index)" % _map.map_id
		return
	var s = _scene_index[_scene_idx]
	status.text = "scene #%d: %s\nmapID=%d  body=%dB" % [
		_scene_idx, s.get("name", "?"), _map.map_id, s.get("body_len", 0)]


func _run_intro(scene_meta: Dictionary) -> void:
	# 첫 진입 시 Interpreter 가 처음 5개 opcode 만 console 에 dump
	var interp = Interp.new()
	interp.run_intro(scene_meta)
