## 타이틀 화면.
extends Node2D

@onready var logo: Sprite2D = $Logo
@onready var start_button: Button = $UI/StartButton


func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
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


func _on_start_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/demo.tscn")


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_on_start_pressed()
