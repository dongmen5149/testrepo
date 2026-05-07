## 상태/인벤토리 패널 (간단 placeholder).
##
## 우측에서 슬라이드인. ESC 키로 토글.
## 실제 캐릭터 클래스/스킬/아이템 데이터는 csv (class.dat, skill_NN.dat,
## item_NN.dat) 에서 로드 — 추후 실 데이터 연결.
class_name StatusPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var hp_label: Label = $BG/HP
@onready var sp_label: Label = $BG/SP
@onready var lvl_label: Label = $BG/LVL
@onready var gold_label: Label = $BG/Gold
@onready var inv_list: ItemList = $BG/Inventory

var _state: Dictionary = {
	"hp": 100, "max_hp": 100,
	"sp": 50, "max_sp": 50,
	"level": 1, "exp": 0,
	"gold": 0,
	"inventory": [],
}
var _shown: bool = false


func _ready() -> void:
	visible = false
	_apply()


func toggle() -> void:
	_shown = not _shown
	visible = _shown
	if _shown: _apply()


func set_state(s: Dictionary) -> void:
	for k in s:
		_state[k] = s[k]
	if visible: _apply()


func _apply() -> void:
	hp_label.text = "HP %d / %d" % [_state["hp"], _state["max_hp"]]
	sp_label.text = "SP %d / %d" % [_state["sp"], _state["max_sp"]]
	lvl_label.text = "Lv %d  EXP %d" % [_state["level"], _state["exp"]]
	gold_label.text = "Gold %d" % _state["gold"]
	inv_list.clear()
	for item in _state["inventory"]:
		inv_list.add_item(str(item))
