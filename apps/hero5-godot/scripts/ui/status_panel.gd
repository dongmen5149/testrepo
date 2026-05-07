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
@onready var stat_points_label: Label = $BG/StatBox/StatPointsLabel
@onready var str_btn: Button = $BG/StatBox/StrBtn
@onready var dex_btn: Button = $BG/StatBox/DexBtn
@onready var int_btn: Button = $BG/StatBox/IntBtn
@onready var con_btn: Button = $BG/StatBox/ConBtn

# filter / sort
var _filter: String = "all"
var _sort: String = "default"  # default / name / price
@onready var all_btn: Button = $BG/FilterBox/AllBtn
@onready var weapon_btn: Button = $BG/FilterBox/WeaponBtn
@onready var armor_btn: Button = $BG/FilterBox/ArmorBtn
@onready var potion_btn: Button = $BG/FilterBox/PotionBtn
@onready var misc_btn: Button = $BG/FilterBox/MiscBtn
@onready var sort_btn: Button = $BG/FilterBox/SortBtn

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
	inv_list.item_selected.connect(_on_item_hover)
	str_btn.pressed.connect(func(): GameState.allocate_stat("str"))
	dex_btn.pressed.connect(func(): GameState.allocate_stat("dex"))
	int_btn.pressed.connect(func(): GameState.allocate_stat("int"))
	con_btn.pressed.connect(func(): GameState.allocate_stat("con"))
	all_btn.pressed.connect(func(): _set_filter("all"))
	weapon_btn.pressed.connect(func(): _set_filter("weapon"))
	armor_btn.pressed.connect(func(): _set_filter("armor"))
	potion_btn.pressed.connect(func(): _set_filter("potion"))
	misc_btn.pressed.connect(func(): _set_filter("misc"))
	sort_btn.pressed.connect(cycle_sort)
	_apply()


func _set_filter(f: String) -> void:
	_filter = f
	_apply()


func _matches_filter(name: String) -> bool:
	if _filter == "all": return true
	if _filter == "weapon":
		return ("검" in name or "소드" in name or "액스" in name or "총" in name or "창" in name)
	if _filter == "armor":
		return ("갑옷" in name or "투구" in name or "장화" in name or "방패" in name)
	if _filter == "potion":
		return ("포션" in name or "수프가루" in name)
	if _filter == "misc":
		# 위 카테고리에 속하지 않으면 misc
		var is_w = ("검" in name or "소드" in name or "액스" in name)
		var is_a = ("갑옷" in name or "투구" in name or "장화" in name)
		var is_p = ("포션" in name or "수프가루" in name)
		return not (is_w or is_a or is_p)
	return true


## 단일 클릭 = hover → 툴팁 + stat 비교.
func _on_item_hover(idx: int) -> void:
	var inv: Array = _state["inventory"]
	var equipment: Array = _state.get("equipment", [])
	var inv_idx = idx - equipment.size() - 1
	if inv_idx < 0 or inv_idx >= inv.size(): return
	var item_name := str(inv[inv_idx])
	# items.json 에서 검색해서 stats[7] 추출
	var item_atk = _find_item_attack(item_name)
	if item_atk < 0:
		stat_points_label.tooltip_text = ""
		return
	# 현재 무기와 비교
	var cur_weapon = GameState.equipped_item(GameState.SLOT_WEAPON)
	var cur_atk = _find_item_attack(str(cur_weapon)) if cur_weapon else 0
	var diff = item_atk - cur_atk
	var sign = "+" if diff >= 0 else ""
	stat_points_label.tooltip_text = "%s\nATK %d (%s%d)" % [item_name, item_atk, sign, diff]


func _find_item_attack(name: String) -> int:
	if name.is_empty() or name == "(없음)": return -1
	for slot in range(10):
		var arr = GameData.items_in_slot(slot)
		var idx = arr.find(name)
		if idx >= 0:
			var data = GameData.item_stat(slot, idx)
			return int(data.get("attack", 0))
	return -1


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
	if stat_points_label:
		var pts = GameState.stat_points
		stat_points_label.text = "+%d" % pts
		var disabled = pts <= 0
		str_btn.disabled = disabled
		dex_btn.disabled = disabled
		int_btn.disabled = disabled
		con_btn.disabled = disabled
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
	# 인벤토리 항목들 (필터 + 정렬)
	inv_list.add_item("--- 인벤토리 (%s, %s) ---" % [_filter, _sort])
	var filtered: Array = []
	for item in inv:
		var name = str(item)
		if _matches_filter(name):
			filtered.append(name)
	# 정렬
	if _sort == "name":
		filtered.sort()
	elif _sort == "price":
		filtered.sort_custom(func(a, b): return _find_item_price(a) > _find_item_price(b))
	for name in filtered:
		inv_list.add_item(name)


func _find_item_price(name: String) -> int:
	for slot in range(19):
		var arr = GameData.items_in_slot(slot)
		var idx = arr.find(name)
		if idx >= 0:
			var data = GameData.item_stat(slot, idx)
			return int(data.get("price", 0))
	return 0


## 필터 버튼이 정렬 cycle 도 겸함 (Misc 길게 = price 정렬 등 단축)
func cycle_sort() -> void:
	match _sort:
		"default": _sort = "name"
		"name": _sort = "price"
		_: _sort = "default"
	_apply()
