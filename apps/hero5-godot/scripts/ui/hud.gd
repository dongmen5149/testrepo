## 화면 상단 HUD — HP/SP/Lv/Gold 미니바.
##
## GameState.state_changed 시 자동 갱신.
class_name HUD
extends CanvasLayer

@onready var hp_bar: ProgressBar = $HUD/HPBar
@onready var sp_bar: ProgressBar = $HUD/SPBar
@onready var hp_label: Label = $HUD/HPLabel
@onready var sp_label: Label = $HUD/SPLabel
@onready var lv_label: Label = $HUD/LvLabel
@onready var gold_label: Label = $HUD/GoldLabel


func _ready() -> void:
	GameState.state_changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	hp_bar.max_value = GameState.max_hp
	hp_bar.value = GameState.hp
	hp_label.text = "HP %d/%d" % [GameState.hp, GameState.max_hp]
	sp_bar.max_value = GameState.max_sp
	sp_bar.value = GameState.sp
	sp_label.text = "SP %d/%d" % [GameState.sp, GameState.max_sp]
	lv_label.text = "Lv.%d" % GameState.level
	gold_label.text = "%dG" % GameState.gold
