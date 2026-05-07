## 클래스 선택 화면 (New Game 진입 시).
##
## class.dat 의 5 클래스 (워리어/로그/건슬링어/나이트/소서러) + 능력치
## 표시. 선택하면 GameState.class_id 설정 후 demo 씬으로.
extends Control

@onready var info_label: Label = $Info
@onready var stat_label: Label = $StatLabel
@onready var class_list: ItemList = $ClassList
@onready var start_btn: Button = $StartButton

var _classes: Array = []
var _selected: int = 0


func _ready() -> void:
	_load_classes()
	_populate()
	class_list.item_selected.connect(_on_select)
	start_btn.pressed.connect(_on_start)
	if not _classes.is_empty():
		class_list.select(0)
		_on_select(0)
	# 클래스 선택 BGM (bgm_01 다른 곡)
	Audio.play_bgm(1)
	SceneFader.fade_in(self)


func _load_classes() -> void:
	var p := "res://assets/gamedata/class_stats.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Array: _classes = data


func _populate() -> void:
	class_list.clear()
	for cls in _classes:
		class_list.add_item(cls.get("name", "?"))


func _on_select(idx: int) -> void:
	_selected = idx
	if idx >= _classes.size():
		stat_label.text = ""
		return
	var cls = _classes[idx]
	stat_label.text = "STR %d  DEX %d  INT %d  CON %d" % [
		cls.get("STR", 0), cls.get("DEX", 0),
		cls.get("INT", 0), cls.get("CON", 0)]


func _on_start() -> void:
	if _selected >= _classes.size(): return
	var cls = _classes[_selected]
	GameState.class_id = _selected
	GameState.stat_str = int(cls.get("STR", 12))
	GameState.stat_dex = int(cls.get("DEX", 8))
	GameState.stat_int = int(cls.get("INT", 10))
	GameState.stat_con = int(cls.get("CON", 6))
	# 클래스별 시작 HP/SP
	GameState.max_hp = 100 + GameState.stat_con * 5
	GameState.hp = GameState.max_hp
	GameState.max_sp = 30 + GameState.stat_int * 2
	GameState.sp = GameState.max_sp
	SceneFader.change_scene(self, "res://scenes/demo.tscn")
