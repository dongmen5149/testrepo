## Map 렌더러 검증 씬.
extends Node2D

@onready var label: Label = $UI/Label

const MapRendererScript = preload("res://scripts/core/map_renderer.gd")

var _map_renderer: Node2D
var _scene_index: Array = []
var _scene_idx: int = 0
var _map_id: int = 0


func _ready() -> void:
	_map_renderer = MapRendererScript.new()
	_map_renderer.map_id = 0
	add_child(_map_renderer)
	_load_scene_index()
	_apply()


func _load_scene_index() -> void:
	var p := "res://assets/scenes/index.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Array:
			_scene_index = data


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_up"):
		_map_id = (_map_id + 1) % 200
		_apply()
	elif event.is_action_pressed("ui_down"):
		_map_id = (_map_id - 1 + 200) % 200
		_apply()
	elif event.is_action_pressed("ui_right") and _scene_index.size() > 0:
		_scene_idx = (_scene_idx + 1) % _scene_index.size()
		_map_id = int(_scene_index[_scene_idx].get("mapID", 0))
		_apply()
	elif event.is_action_pressed("ui_left") and _scene_index.size() > 0:
		_scene_idx = (_scene_idx - 1 + _scene_index.size()) % _scene_index.size()
		_map_id = int(_scene_index[_scene_idx].get("mapID", 0))
		_apply()


func _apply() -> void:
	_map_renderer.map_id = _map_id
	var info := "mapID=%d" % _map_id
	if _scene_index.size() > 0:
		var s = _scene_index[_scene_idx]
		info += "  scene=%s  start=(%d,%d,dir=%d)" % [
			s.get("name", "?"), s.get("startX", 0), s.get("startY", 0),
			s.get("startDir", 0)]
	label.text = info
