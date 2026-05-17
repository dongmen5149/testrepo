## 합성(Mix) 패널 — Round 25/28 의 ApplySpecialMix mechanism Godot 구현.
##
## 원본 mechanism (libHeroesLore5.so::RefineItem::ApplySpecialMix, @0xa6ed4):
##   csv slot_15 의 mix_book recipe 를 직접 사용.
##   각 recipe = byte 0 separator + 3×3 byte ingredients (cat/idx/count) +
##                2 byte result (cat/idx) + 1 byte success_rate %.
##   116 records (Round 25 검증).
##   Mission::CheckMissionMix 호출로 mission 진척.
##
## UI 구성:
##   - 좌측: 116 recipe 리스트 (결과 아이템 이름 + 성공률)
##   - 우측: 선택된 recipe 의 재료 표시 (이름 × 필요/보유) + 결과 + 비용
##   - 아래: 실행 버튼 (재료 부족 시 disabled)
class_name MixPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var recipe_list: ItemList = $BG/RecipeList
@onready var result_label: Label = $BG/Result
@onready var ingredients_label: Label = $BG/Ingredients
@onready var success_label: Label = $BG/Success
@onready var mix_btn: Button = $BG/MixBtn
@onready var close_btn: Button = $BG/CloseBtn
@onready var log_label: Label = $BG/Log
@onready var filter_btn: Button = $BG/FilterBtn

signal closed
signal mixed(recipe_idx: int, success: bool)

var _selected_recipe_idx: int = -1
var _shown: bool = false
var _filter_only_craftable: bool = false


func _ready() -> void:
	visible = false
	recipe_list.item_selected.connect(_on_recipe_selected)
	mix_btn.pressed.connect(_on_mix_pressed)
	close_btn.pressed.connect(toggle)
	filter_btn.pressed.connect(_toggle_filter)


func toggle() -> void:
	_shown = not _shown
	visible = _shown
	if _shown:
		_refresh_recipe_list()
	else:
		closed.emit()


func _toggle_filter() -> void:
	_filter_only_craftable = not _filter_only_craftable
	filter_btn.text = "필터: 제작가능만" if _filter_only_craftable else "필터: 전체"
	_refresh_recipe_list()


## items.json slot_15 의 116 recipe 를 list. _filter_only_craftable 가 true 면
## 재료가 모두 있는 recipe 만 표시.
func _refresh_recipe_list() -> void:
	recipe_list.clear()
	_selected_recipe_idx = -1
	log_label.text = ""
	var recipes = GameData.mix_recipes()
	for i in recipes.size():
		var rec: Dictionary = recipes[i]
		var parsed = GameData.parse_recipe(rec)
		if parsed.is_empty(): continue
		var result = parsed["result"]
		var result_name = str(result.get("name", ""))
		if result_name.is_empty(): result_name = "(slot_%d #%d)" % [result["cat"], result["idx"]]
		var sr = int(parsed.get("success_rate", 100))
		var craftable = _can_craft(parsed)
		if _filter_only_craftable and not craftable:
			continue
		var prefix = "✓ " if craftable else "  "
		var idx = recipe_list.add_item("%s%s  %d%%" % [prefix, result_name, sr])
		recipe_list.set_item_metadata(idx, i)
		if not craftable:
			recipe_list.set_item_custom_fg_color(idx, Color(0.6, 0.6, 0.6, 1))
	_apply_preview()


func _on_recipe_selected(idx: int) -> void:
	_selected_recipe_idx = int(recipe_list.get_item_metadata(idx))
	_apply_preview()


## 선택된 recipe 의 재료 + 결과 + 비용 preview.
func _apply_preview() -> void:
	if _selected_recipe_idx < 0:
		result_label.text = "(레시피 선택)"
		ingredients_label.text = ""
		success_label.text = ""
		mix_btn.disabled = true
		return
	var recipes = GameData.mix_recipes()
	if _selected_recipe_idx >= recipes.size(): return
	var parsed = GameData.parse_recipe(recipes[_selected_recipe_idx])
	if parsed.is_empty(): return
	var result = parsed["result"]
	var result_name = str(result.get("name", ""))
	if result_name.is_empty(): result_name = "(slot_%d #%d)" % [result["cat"], result["idx"]]
	result_label.text = "결과 → %s" % result_name
	var lines: Array[String] = ["재료:"]
	var all_have := true
	for ing in parsed["ingredients"]:
		var name = str(ing.get("name", ""))
		var need = int(ing["count"])
		if name.is_empty(): name = "(slot_%d #%d)" % [ing["cat"], ing["idx"]]
		var have = GameState.inventory_count(name)
		var mark = "✓" if have >= need else "✗"
		if have < need: all_have = false
		lines.append("  %s %s × %d / %d" % [mark, name, need, have])
	ingredients_label.text = "\n".join(lines)
	var sr = int(parsed["success_rate"])
	success_label.text = "성공률 %d%%" % sr
	mix_btn.disabled = not all_have


## 재료 모두 있는지 — _refresh_recipe_list 의 필터 + _apply_preview 의 버튼 disable.
func _can_craft(parsed: Dictionary) -> bool:
	for ing in parsed.get("ingredients", []):
		var name = str(ing.get("name", ""))
		var need = int(ing["count"])
		if name.is_empty(): return false
		if GameState.inventory_count(name) < need: return false
	return true


## 실행 — Round 25 의 success_rate 로 random roll.
## 성공: 재료 소비 + 결과 아이템 inventory 추가.
## 실패: 재료만 소비 (Round 28 의 ApplySpecialMix 동작).
func _on_mix_pressed() -> void:
	if _selected_recipe_idx < 0: return
	var recipes = GameData.mix_recipes()
	if _selected_recipe_idx >= recipes.size(): return
	var parsed = GameData.parse_recipe(recipes[_selected_recipe_idx])
	if parsed.is_empty(): return
	if not _can_craft(parsed):
		log_label.text = "재료 부족"
		return
	# 재료 소비
	for ing in parsed["ingredients"]:
		GameState.consume_inventory(str(ing["name"]), int(ing["count"]))
	# success roll
	var sr = int(parsed["success_rate"])
	var roll = randi() % 100
	if roll < sr:
		# 성공 — inventory 에 결과 추가
		var result = parsed["result"]
		var result_name = str(result.get("name", ""))
		if result_name.is_empty(): result_name = "(slot_%d #%d)" % [result["cat"], result["idx"]]
		GameState.inventory.append(result_name)
		GameState.state_changed.emit()
		log_label.text = "✓ 성공 — %s 획득 (roll %d / %d)" % [result_name, roll, sr]
		mixed.emit(_selected_recipe_idx, true)
	else:
		log_label.text = "✗ 실패 — 재료 소비됨 (roll %d / %d)" % [roll, sr]
		mixed.emit(_selected_recipe_idx, false)
	_refresh_recipe_list()
	# 선택 복원
	for i in recipe_list.item_count:
		if int(recipe_list.get_item_metadata(i)) == _selected_recipe_idx:
			recipe_list.select(i)
			_apply_preview()
			break
