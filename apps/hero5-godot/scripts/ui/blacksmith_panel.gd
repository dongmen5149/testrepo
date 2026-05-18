## NPC 대장간(Blacksmith) 패널 — Round 28/32 의 ApplyNormalMix mechanism Godot 구현.
##
## 원본 mechanism (libHeroesLore5.so::RefineItem::ApplyNormalMix, @0xa75bc):
##   smith_0/1/2.dat 의 MixSmithTableInfo 사용 (csv slot_15 mix_book 과 별개).
##   HERO+0x1d00 = MixSmithTable_ptr. 총 288 NPC blacksmith recipes.
##   각 recipe 13-byte = mix_book 과 동일 layout (cat/idx/count×3 + result + sr=75%).
##
## mix_panel 과의 차이:
##   - 데이터원: smithtable.json (NPC blacksmith) vs items.json slot_15 (recipe book)
##   - success_rate: 모두 75% 고정 (mix_book 은 90~100% 또는 20~22%)
##   - 진입: NPC 대화 흐름 (Round 8 의 npc_table) — 키 J 로 데모 토글
##   - grouping: smith_0(기본 96)/smith_1(세트 96)/smith_2(고급 96) 별 탭 필터
##
## UI 구성:
##   - 상단: 탭 (기본/세트/고급/전체)
##   - 좌측: recipe 리스트 (결과 이름 + 등급)
##   - 우측: 선택된 recipe 의 재료 + 결과 + 성공률
##   - 아래: 제작 버튼 (재료 부족 시 disabled) + 닫기 + 로그
class_name BlacksmithPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var recipe_list: ItemList = $BG/RecipeList
@onready var result_label: Label = $BG/Result
@onready var ingredients_label: Label = $BG/Ingredients
@onready var success_label: Label = $BG/Success
@onready var craft_btn: Button = $BG/CraftBtn
@onready var close_btn: Button = $BG/CloseBtn
@onready var log_label: Label = $BG/Log
@onready var filter_btn: Button = $BG/FilterBtn
@onready var tab_btn: Button = $BG/TabBtn

signal closed
signal crafted(smith_id: int, idx: int, success: bool)

var _selected_recipe_idx: int = -1  # _filtered_recipes 의 index
var _shown: bool = false
var _filter_only_craftable: bool = false
var _current_tab: int = 3  # 0/1/2 = smith_id, 3 = 전체
var _filtered_recipes: Array = []


func _ready() -> void:
	visible = false
	recipe_list.item_selected.connect(_on_recipe_selected)
	craft_btn.pressed.connect(_on_craft_pressed)
	close_btn.pressed.connect(toggle)
	filter_btn.pressed.connect(_toggle_filter)
	tab_btn.pressed.connect(_cycle_tab)


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


func _cycle_tab() -> void:
	_current_tab = (_current_tab + 1) % 4
	tab_btn.text = ["탭: 기본", "탭: 세트", "탭: 고급", "탭: 전체"][_current_tab]
	_refresh_recipe_list()


## smith_all (288) 또는 smith_table(_current_tab) 결과 → _filter_only_craftable 적용.
func _refresh_recipe_list() -> void:
	recipe_list.clear()
	_selected_recipe_idx = -1
	log_label.text = ""
	var src: Array
	if _current_tab == 3:
		src = GameData.smith_all()
	else:
		src = GameData.smith_table(_current_tab)
		for r in src:
			r["_smith_id"] = _current_tab
			r["_grade"] = ["기본", "세트", "고급"][_current_tab]
	_filtered_recipes = []
	for rec in src:
		var parsed = GameData.parse_smith_recipe(rec)
		if parsed.is_empty(): continue
		var craftable = _can_craft(parsed)
		if _filter_only_craftable and not craftable:
			continue
		_filtered_recipes.append(rec)
		var result: Dictionary = parsed["result"]
		var result_name = str(result.get("name", ""))
		if result_name.is_empty(): result_name = "(slot_%d #%d)" % [result["cat"], result["idx"]]
		var sr = int(parsed.get("success_rate", 75))
		var prefix = "✓ " if craftable else "  "
		var grade = str(rec.get("_grade", ""))
		var idx = recipe_list.add_item("%s[%s] %s  %d%%" % [prefix, grade, result_name, sr])
		if not craftable:
			recipe_list.set_item_custom_fg_color(idx, Color(0.6, 0.6, 0.6, 1))
	_apply_preview()


func _on_recipe_selected(idx: int) -> void:
	_selected_recipe_idx = idx
	_apply_preview()


## 선택된 recipe 의 재료 + 결과 + 성공률 preview.
func _apply_preview() -> void:
	if _selected_recipe_idx < 0 or _selected_recipe_idx >= _filtered_recipes.size():
		result_label.text = "(레시피 선택)"
		ingredients_label.text = ""
		success_label.text = ""
		craft_btn.disabled = true
		return
	var rec: Dictionary = _filtered_recipes[_selected_recipe_idx]
	var parsed = GameData.parse_smith_recipe(rec)
	if parsed.is_empty(): return
	var result: Dictionary = parsed["result"]
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
	success_label.text = "성공률 %d%% (NPC 대장간)" % sr
	craft_btn.disabled = not all_have


func _can_craft(parsed: Dictionary) -> bool:
	for ing in parsed.get("ingredients", []):
		var name = str(ing.get("name", ""))
		var need = int(ing["count"])
		if name.is_empty(): return false
		if GameState.inventory_count(name) < need: return false
	return true


## 제작 — Round 28 의 ApplyNormalMix 동작.
##   성공: 재료 소비 + 결과 아이템 inventory 추가
##   실패: 재료만 소비 (NPC 대장간 정책)
func _on_craft_pressed() -> void:
	if _selected_recipe_idx < 0 or _selected_recipe_idx >= _filtered_recipes.size(): return
	var rec: Dictionary = _filtered_recipes[_selected_recipe_idx]
	var parsed = GameData.parse_smith_recipe(rec)
	if parsed.is_empty(): return
	if not _can_craft(parsed):
		log_label.text = "재료 부족"
		return
	for ing in parsed["ingredients"]:
		GameState.consume_inventory(str(ing["name"]), int(ing["count"]))
	var sr = int(parsed["success_rate"])
	var roll = randi() % 100
	var smith_id = int(rec.get("_smith_id", 0))
	var orig_idx = int(rec.get("idx", 0))
	if roll < sr:
		var result: Dictionary = parsed["result"]
		var result_name = str(result.get("name", ""))
		if result_name.is_empty(): result_name = "(slot_%d #%d)" % [result["cat"], result["idx"]]
		GameState.inventory.append(result_name)
		GameState.state_changed.emit()
		log_label.text = "✓ 성공 — %s 획득 (roll %d / %d)" % [result_name, roll, sr]
		crafted.emit(smith_id, orig_idx, true)
	else:
		log_label.text = "✗ 실패 — 재료 소비됨 (roll %d / %d)" % [roll, sr]
		crafted.emit(smith_id, orig_idx, false)
	# 선택 유지하고 list 만 refresh
	var saved = _selected_recipe_idx
	_refresh_recipe_list()
	if saved < _filtered_recipes.size():
		recipe_list.select(saved)
		_selected_recipe_idx = saved
		_apply_preview()
