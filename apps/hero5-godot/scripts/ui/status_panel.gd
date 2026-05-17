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
@onready var atkdef_label: Label = $BG/AtkDef
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


## items.json 의 kind (Round 51) 기반 정확한 filter 분류.
## 한국어 substring 매칭 (Round 50 이전) → items.json `slot`/`kind` 직접 사용.
func _matches_filter(name: String) -> bool:
	return GameData.item_matches_filter(name, _filter)


## 단일 클릭 = hover → 툴팁 + items.json 기반 풍부 정보.
##
## Round 51 신규 정보:
##   - tier_label (legendary/rare/gem/common) — Round 24 의 val_15f upper 3 bit
##   - class_label (W/R/G/K/S) — Round 16 의 val_15f lower 5 bit 5-class mask
##   - level_limit — Round 13 +0x15d
##   - refine_count + sub_count — Round 17/26 강화 mechanism
##   - skill_book: class_id/skill_index/skill_level/required_level — Round 21
##   - potion: effect_type/success_rate/duration — Round 23
func _on_item_hover(idx: int) -> void:
	var inv: Array = _state["inventory"]
	var equipment: Array = _state.get("equipment", [])
	var inv_idx = idx - equipment.size() - 1
	if inv_idx < 0 or inv_idx >= inv.size(): return
	var item_name := str(inv[inv_idx])
	stat_points_label.tooltip_text = _format_item_tooltip(item_name)


## item 의 모든 의미 있는 fields 를 multi-line tooltip 으로 포매팅.
func _format_item_tooltip(item_name: String) -> String:
	var info: Dictionary = GameData.item_lookup(item_name)
	if info.is_empty(): return item_name
	var lines: Array = [item_name]
	var category: String = info.get("category", "?")
	var kind: String = info.get("kind", "?")
	if category == "equip":
		var stat_a: int = info.get("stat_a", 0)
		var stat_b: int = info.get("stat_b", 0)
		var stat_label = "ATK" if kind.begins_with("weapon") else "DEF"
		if stat_b > 0 and stat_b != stat_a:
			lines.append("%s %d~%d" % [stat_label, stat_a, stat_b])
		elif stat_a > 0:
			lines.append("%s %d" % [stat_label, stat_a])
		var lvl: int = info.get("level_limit", 0)
		if lvl > 0:
			lines.append("필요 Lv %d" % lvl)
		var cls: String = info.get("class_label", "")
		if not cls.is_empty():
			lines.append("클래스 %s" % cls)
		var tier: String = info.get("tier_label", "")
		if not tier.is_empty():
			lines.append("등급 %s" % tier)
		var ref_n: int = info.get("refine_count", 0)
		var sub_n: int = info.get("sub_count", 0)
		if ref_n > 0 or sub_n > 0:
			lines.append("강화 +%d (sub %d)" % [ref_n, sub_n])
		# 장착 시 stat 비교
		var slot = GameData.equip_slot_for_kind(kind)
		if slot >= 0:
			var cur = GameState.equipped_item(slot)
			if cur != null and str(cur) != item_name:
				var cur_info = GameData.item_lookup(str(cur))
				var cur_a: int = cur_info.get("stat_a", 0)
				var diff = stat_a - cur_a
				var sign_s = "+" if diff >= 0 else ""
				lines.append("현재 %s%d" % [sign_s, diff])
	elif kind == "potion":
		var et: int = info.get("effect_type", 0)
		var ev: int = info.get("effect_value", 0)
		var sr: int = info.get("success_rate", 100)
		var et_str = {91: "HP", 90: "SP", 87: "buff", 92: "마석"}.get(et, "효과 %d" % et)
		lines.append("%s +%d (%d%%)" % [et_str, ev, sr])
		var dur: int = info.get("duration", 0)
		if dur > 0:
			lines.append("지속 %d 턴" % dur)
	elif kind in ["skill_book_wr", "skill_book_gk"]:
		var cid: int = info.get("class_id", 0)
		var sidx: int = info.get("skill_index", 0)
		var slvl: int = info.get("skill_level", 1)
		var rlvl: int = info.get("required_level", 0)
		var class_arr = GameData.class_names()
		var class_str = class_arr[cid] if cid < class_arr.size() else "?"
		lines.append("%s 스킬 #%d Lv%d" % [class_str, sidx, slvl])
		if rlvl > 0:
			lines.append("필요 Lv %d" % rlvl)
	if info.get("price", 0) > 0:
		lines.append("가격 %d G" % info["price"])
	return "\n".join(lines)


## items.json 의 정확한 kind 반환. 한국어 substring 매칭 (Round 50 이전) 정정.
func _item_kind(name: String) -> String:
	var info = GameData.item_lookup(name)
	if info.is_empty(): return "misc"
	var kind: String = info.get("kind", "misc")
	if kind.begins_with("weapon"): return "weapon"
	if kind in ["armor", "helmet", "boots", "shield", "accessory", "accessory_2", "spirit"]:
		return "armor"
	if kind == "potion": return "potion"
	return "misc"


## items.json 기반 정확한 equip slot 매핑. 폴백 = ARMOR.
func _slot_for_kind(kind: String, name: String) -> int:
	var info = GameData.item_lookup(name)
	var slot = GameData.equip_slot_for_kind(info.get("kind", ""))
	if slot >= 0: return slot
	# fallback (items.json 미발견 시 한국어 substring)
	if kind == "weapon": return GameState.SLOT_WEAPON
	if "투구" in name: return GameState.SLOT_HELMET
	if "장화" in name: return GameState.SLOT_BOOTS
	return GameState.SLOT_ARMOR


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


## items.json 기반 정확한 use logic + class_mask/level_limit 검증 (Round 51).
##
## 검증 실패 메시지는 stat_points_label tooltip 으로 일시 표시 (UI toast 가 정식
## 통로 — 후속 라운드에서 SceneFader/Toast 통합).
func _use_item(item_name: String, inv_idx: int) -> void:
	var info: Dictionary = GameData.item_lookup(item_name)
	var category: String = info.get("category", "")
	var kind: String = info.get("kind", "")
	if category == "battle_use" or kind == "potion":
		# Round 23 의 effect_type/effect_value 사용. fallback = HP +30
		var et: int = info.get("effect_type", 91)
		var ev: int = max(30, info.get("effect_value", 0))
		if et == 91:
			GameState.hp = min(GameState.max_hp, GameState.hp + ev)
		elif et == 90:
			GameState.sp = min(GameState.max_sp, GameState.sp + ev)
		GameState.inventory.remove_at(inv_idx)
		GameState.state_changed.emit()
		item_used.emit(item_name)
		return
	if category == "equip":
		# class_mask / level_limit 검증 (Round 16/13)
		var class_mask: int = info.get("class_mask", 0)
		var class_id: int = GameState.class_id if "class_id" in GameState else 0
		if not GameData.class_mask_allows(class_mask, class_id):
			stat_points_label.tooltip_text = "%s\n클래스 제한 (%s 만)" % [
				item_name, info.get("class_label", "?")]
			return
		var lvl_lim: int = info.get("level_limit", 0)
		if lvl_lim > GameState.level:
			stat_points_label.tooltip_text = "%s\n레벨 부족 (필요 Lv %d)" % [item_name, lvl_lim]
			return
		var slot = GameData.equip_slot_for_kind(kind)
		if slot < 0:
			return
		GameState.equip(slot, inv_idx)
		return
	# 기타 (orb/material/recipe/skill_book/cash) — 후속 라운드 (refine UI 등)


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
	if atkdef_label:
		var bonus = GameState.equipment_bonus()
		var atk_total = GameState.total_attack()
		var def_total = GameState.total_defense()
		var atk_eq = int(bonus.get("attack", 0))
		var def_eq = int(bonus.get("defense", 0))
		atkdef_label.text = "ATK %d (장비+%d)  DEF %d (장비+%d)" % [
			atk_total, atk_eq, def_total, def_eq]
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


## items.json 의 모든 slot 통합 lookup (Round 51). 한국어 substring 매칭 X.
func _find_item_price(name: String) -> int:
	return int(GameData.item_lookup(name).get("price", 0))


## 필터 버튼이 정렬 cycle 도 겸함 (Misc 길게 = price 정렬 등 단축)
func cycle_sort() -> void:
	match _sort:
		"default": _sort = "name"
		"name": _sort = "price"
		_: _sort = "default"
	_apply()
