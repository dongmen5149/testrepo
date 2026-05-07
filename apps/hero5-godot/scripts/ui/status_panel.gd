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
	"equipment": [-1, -1, -1, -1, -1, -1],
}
var _shown: bool = false
const SLOT_NAMES := ["무기", "방어구", "투구", "장화", "악세1", "악세2"]


signal item_used(item_name: String)

func _ready() -> void:
	visible = false
	inv_list.item_activated.connect(_on_item_activated)
	_apply()


## 더블클릭/엔터로 아이템 사용 (포션 등).
func _on_item_activated(idx: int) -> void:
	# idx 0..5 = 장비 슬롯 (장착/해제)
	# idx 6 = 구분선
	# idx 7+ = 인벤 항목
	var inv: Array = _state["inventory"]
	var equipment: Array = _state.get("equipment", [])
	if idx >= 0 and idx < equipment.size():
		# 장비 슬롯 클릭 → 해제
		GameState.unequip(idx)
		return
	var inv_idx = idx - equipment.size() - 1  # -1 for "--- 인벤토리 ---" 구분선
	if inv_idx < 0 or inv_idx >= inv.size(): return
	var item_name := str(inv[inv_idx])
	_use_item(item_name, inv_idx)


func _use_item(item_name: String, inv_idx: int) -> void:
	# 포션류 자동 식별 (이름에 "포션" 또는 "수프가루")
	if "포션" in item_name or "수프가루" in item_name:
		var heal := 30
		GameState.hp = min(GameState.max_hp, GameState.hp + heal)
		# 인벤에서 1개 제거
		GameState.inventory.remove_at(inv_idx)
		GameState.state_changed.emit()
		item_used.emit(item_name)
		return
	# 무기/방어구 자동 장착 (이름에 "검" / "소드" 등)
	if "검" in item_name or "소드" in item_name or "액스" in item_name:
		GameState.inventory.append(item_name)  # keep
		GameState.equip(GameState.SLOT_WEAPON, GameState.inventory.size() - 1)
		return
	if "갑옷" in item_name or "투구" in item_name or "장화" in item_name:
		var slot = GameState.SLOT_ARMOR
		if "투구" in item_name: slot = GameState.SLOT_HELMET
		elif "장화" in item_name: slot = GameState.SLOT_BOOTS
		GameState.equip(slot, inv_idx)
		return


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
	# 장비 먼저
	var equipment: Array = _state.get("equipment", [])
	var inv: Array = _state["inventory"]
	for slot in range(min(SLOT_NAMES.size(), equipment.size())):
		var idx = int(equipment[slot])
		var name = "(없음)"
		if idx >= 0 and idx < inv.size():
			name = str(inv[idx])
		inv_list.add_item("[%s] %s" % [SLOT_NAMES[slot], name])
	# 인벤토리 항목들
	inv_list.add_item("--- 인벤토리 ---")
	for item in inv:
		inv_list.add_item(str(item))
