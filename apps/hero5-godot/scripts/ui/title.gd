## 타이틀 화면.
extends Node2D

const SaveManager = preload("res://scripts/core/save_manager.gd")

@onready var logo: Sprite2D = $Logo
@onready var new_btn: Button = $UI/NewGameButton
@onready var cont_btn: Button = $UI/ContinueButton
@onready var slots: Label = $UI/SlotsLabel


func _ready() -> void:
	new_btn.pressed.connect(_on_new_game)
	cont_btn.pressed.connect(_on_continue)
	_refresh_slots()
	# title sprite 로드 (c/sp/imgcom/title.mgr → assets/sprites/imgcom/title)
	var path := "res://assets/sprites/imgcom/title"
	if DirAccess.dir_exists_absolute(path):
		var d := DirAccess.open(path)
		d.list_dir_begin()
		var fname := d.get_next()
		while fname != "":
			if fname.begins_with("frame_00") and fname.ends_with(".png"):
				logo.texture = load(path + "/" + fname)
				break
			fname = d.get_next()


func _on_new_game() -> void:
	# fresh state — clear GameState
	GameState.current_scene_id = 0
	GameState.map_id = 0
	GameState.player_x = 160
	GameState.player_y = 240
	GameState.hp = 100; GameState.max_hp = 100
	GameState.sp = 50; GameState.max_sp = 50
	GameState.level = 1; GameState.exp = 0
	GameState.gold = 1000
	GameState.inventory = []
	GameState.flags = {}
	get_tree().change_scene_to_file("res://scenes/demo.tscn")


func _on_continue() -> void:
	if GameState.quick_load(0):
		get_tree().change_scene_to_file("res://scenes/demo.tscn")
	else:
		slots.text = "저장된 데이터가 없습니다."


func _refresh_slots() -> void:
	var ss := SaveManager.list_slots()
	if ss.is_empty():
		slots.text = "저장 데이터 없음"
		cont_btn.disabled = true
		return
	cont_btn.disabled = false
	var lines := ["Save slots:"]
	for s in ss:
		var p = s.get("player", {})
		lines.append("  [%d] %s  Lv.%d  %s" % [
			s.get("slot", 0),
			s.get("timestamp", "?"),
			int(p.get("level", 1)),
			"scene #%d" % s.get("scene_id", 0)])
	slots.text = "\n".join(lines)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_on_new_game()
