## 스킬북(SkillBook) 학습 패널 — Round 21 의 HERO::IfLearnSkill mechanism Godot 구현.
##
## 원본 mechanism (libHeroesLore5.so::HERO::IfLearnSkill, @0xa3b38 path):
##   slot_dispatch = (class_id / 2) + 16  → slot_16 (W/R) or slot_17 (G/K)
##   book.class_id 가 player.class_id 와 일치해야 학습 가능
##   skill_level (1..7) 이 현재 보유 레벨보다 높을 때만 갱신
##
## items.json 의 skill_book 카테고리:
##   slot_16: Warrior(0)+Rogue(1) = 95 books
##   slot_17: Gunslinger(2)+Knight(3) = 98 books
##   각 record: name, class_id, skill_index (0..42), skill_level (1..7), required_level, price
##
## UI 구성:
##   - 좌측: 현재 클래스의 학습 가능 책 리스트 (인벤토리 보유 책만 또는 전체 카탈로그)
##   - 우측: 선택된 책의 상세 (클래스/스킬/레벨/필요레벨/설명) + 보유 레벨
##   - 아래: 학습 버튼 (조건 불충족 시 disabled + 사유) + 인벤토리 필터 토글 + 닫기
class_name SkillBookPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var book_list: ItemList = $BG/BookList
@onready var detail_label: Label = $BG/Detail/DetailLabel
@onready var desc_label: Label = $BG/Detail/DescLabel
@onready var status_label: Label = $BG/Detail/StatusLabel
@onready var learn_btn: Button = $BG/LearnBtn
@onready var filter_btn: Button = $BG/FilterBtn
@onready var close_btn: Button = $BG/CloseBtn
@onready var log_label: Label = $BG/Log

signal closed
signal learned(skill_index: int, new_level: int)

const CLASS_NAMES := ["워리어", "로그", "건슬링어", "나이트", "소서러"]

var _selected_idx: int = -1
var _shown: bool = false
var _filter_inventory_only: bool = true   # 기본: 인벤토리 보유 책만
var _filtered_books: Array = []           # _refresh 후 list 와 동기


func _ready() -> void:
	visible = false
	book_list.item_selected.connect(_on_book_selected)
	learn_btn.pressed.connect(_on_learn_pressed)
	close_btn.pressed.connect(toggle)
	filter_btn.pressed.connect(_toggle_filter)


func toggle() -> void:
	_shown = not _shown
	visible = _shown
	if _shown:
		_refresh()
	else:
		closed.emit()


func _toggle_filter() -> void:
	_filter_inventory_only = not _filter_inventory_only
	filter_btn.text = "필터: 보유 책만" if _filter_inventory_only else "필터: 전체"
	_refresh()


func _refresh() -> void:
	book_list.clear()
	_selected_idx = -1
	log_label.text = ""
	_filtered_books.clear()

	var class_books = GameData.skill_books_for_class(GameState.class_id)
	for rec in class_books:
		if _filter_inventory_only:
			var name = str(rec.get("name", ""))
			if GameState.inventory_count(name) <= 0:
				continue
		_filtered_books.append(rec)
		var detail = GameData.skill_book_detail(rec)
		var have = GameState.get_skill_level(detail["skill_index"])
		var book_lvl = detail["skill_level"]
		var marker = "✓" if have >= book_lvl else ("→" if GameState.can_learn_skill_book(_info_from_rec(rec))["ok"] else "✗")
		var inv = GameState.inventory_count(detail["name"])
		var inv_str = " (인벤×%d)" % inv if inv > 0 else ""
		var idx = book_list.add_item("%s %s%s" % [marker, detail["name"], inv_str])
		if have >= book_lvl:
			book_list.set_item_custom_fg_color(idx, Color(0.6, 0.6, 0.6, 1))
		elif inv == 0 and not _filter_inventory_only:
			book_list.set_item_custom_fg_color(idx, Color(0.8, 0.6, 0.6, 1))

	_apply_preview()


## item_lookup 의 info 구조와 호환되도록 record 를 변환 (kind/class_id 등 채움).
func _info_from_rec(rec: Dictionary) -> Dictionary:
	var slot = GameData.skill_book_slot_for_class(GameState.class_id)
	var kind = "skill_book_wr" if slot == 16 else "skill_book_gk"
	return {
		"slot": slot,
		"name": str(rec.get("name", "")),
		"kind": kind,
		"category": "skill_book",
		"class_id": int(rec.get("class_id", 0)),
		"skill_index": int(rec.get("skill_index", 0)),
		"skill_level": int(rec.get("skill_level", 1)),
		"required_level": int(rec.get("required_level", 0)),
		"price": int(rec.get("price", 0)),
	}


func _on_book_selected(idx: int) -> void:
	_selected_idx = idx
	_apply_preview()


func _apply_preview() -> void:
	if _selected_idx < 0 or _selected_idx >= _filtered_books.size():
		detail_label.text = "(스킬북 선택)"
		desc_label.text = ""
		status_label.text = ""
		learn_btn.disabled = true
		return
	var rec: Dictionary = _filtered_books[_selected_idx]
	var detail = GameData.skill_book_detail(rec)
	var cid = int(detail["class_id"])
	var class_name = CLASS_NAMES[cid] if cid < CLASS_NAMES.size() else "?"
	var book_lvl = int(detail["skill_level"])
	var have = GameState.get_skill_level(int(detail["skill_index"]))
	var lines: Array[String] = []
	lines.append("📖 %s" % detail["name"])
	lines.append("클래스: %s   필요 Lv.%d   가격: %d G" % [class_name, detail["required_level"], detail["price"]])
	lines.append("스킬 #%d  LV%d  (현재 보유: %s)" % [
		detail["skill_index"], book_lvl,
		"LV%d" % have if have > 0 else "미보유"])
	detail_label.text = "\n".join(lines)
	desc_label.text = detail["desc"] if not str(detail["desc"]).is_empty() else "(설명 없음)"

	# learn 가능 여부
	var info = _info_from_rec(rec)
	var check = GameState.can_learn_skill_book(info)
	var inv = GameState.inventory_count(detail["name"])
	if inv <= 0:
		status_label.text = "⚠ 인벤토리에 책이 없습니다"
		learn_btn.disabled = true
	elif check["ok"]:
		status_label.text = "✓ 학습 가능 — 책 1권 소모"
		learn_btn.disabled = false
	else:
		status_label.text = "⚠ %s" % check["reason"]
		learn_btn.disabled = true


## 학습 — Round 21 의 IfLearnSkill 동작. 책 1권 인벤토리 소비.
func _on_learn_pressed() -> void:
	if _selected_idx < 0 or _selected_idx >= _filtered_books.size(): return
	var rec: Dictionary = _filtered_books[_selected_idx]
	var detail = GameData.skill_book_detail(rec)
	var info = _info_from_rec(rec)
	if GameState.inventory_count(detail["name"]) <= 0:
		log_label.text = "✗ 책이 인벤토리에 없습니다"
		return
	if not GameState.learn_skill_book(info):
		var check = GameState.can_learn_skill_book(info)
		log_label.text = "✗ 학습 실패: %s" % check.get("reason", "?")
		return
	GameState.consume_inventory(str(detail["name"]), 1)
	var new_lvl = int(detail["skill_level"])
	log_label.text = "✓ 학습 완료 — 스킬 #%d → LV%d" % [int(detail["skill_index"]), new_lvl]
	learned.emit(int(detail["skill_index"]), new_lvl)
	# 선택 유지 후 refresh
	var saved = _selected_idx
	_refresh()
	if saved < book_list.item_count:
		book_list.select(saved)
		_selected_idx = saved
		_apply_preview()
