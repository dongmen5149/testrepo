## 강화(Refine) 패널 — Round 17/26 의 ApplyItemRefine mechanism Godot 구현.
##
## 원본 mechanism (libHeroesLore5.so::RefineItem::ApplyItemRefine, @0xa292c):
##   5-case jumptable (gv+0x1444+0x130 prob 테이블 + Rand(0,9999)):
##     case 0 = 큰성공 — refine_count += 1, sub_count += 2
##     case 1 = 성공  — refine_count += 1, sub_count += 1
##     case 2 = 재료소비 — no change (변화 없음, 골드/재료만 소모)
##     case 3 = lock  — +0x167 = 1 (영구 잠금)
##     case 4 = destroy — item 파괴
##   refine_count cap = 10.
##
## stat 식 (Round 26 Formula VM id=35/36):
##   refined_stat = base_stat + sub_count  (V[187] = item+0x166)
##
## prob 분포: 강화 단계가 높을수록 실패/lock/destroy 확률 증가. Godot 측에서는
## 합리적 default 분포 사용 (.so 의 정확한 prob 테이블은 별도 RE 필요).
class_name RefinePanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var item_select: ItemList = $BG/ItemSelect
@onready var current_label: Label = $BG/Current
@onready var preview_label: Label = $BG/Preview
@onready var gold_cost_label: Label = $BG/GoldCost
@onready var refine_btn: Button = $BG/RefineBtn
@onready var close_btn: Button = $BG/CloseBtn
@onready var result_log: Label = $BG/ResultLog

signal closed
signal refined(inv_idx: int, result_case: int)

var _selected_inv_idx: int = -1
var _shown: bool = false

# Round 26 의 5-case 결과 라벨
const CASE_NAME := ["큰성공", "성공", "재료소비", "lock", "destroy"]

# refine_count 별 default prob 분포 (1000 분의 N). 실제 .so prob 테이블 미적용.
# 각 row = [큰성공, 성공, 재료소비, lock, destroy]. 합 = 1000.
# refine 0~4 = 안전, 5~7 = 중간, 8~10 = 위험.
const REFINE_PROB := [
	[ 200, 700, 100,   0,   0],  # +0 → +1
	[ 150, 700, 150,   0,   0],  # +1 → +2
	[ 100, 700, 200,   0,   0],  # +2 → +3
	[  80, 620, 280,  20,   0],  # +3 → +4
	[  60, 540, 340,  50,  10],  # +4 → +5
	[  40, 460, 380,  90,  30],  # +5 → +6
	[  30, 370, 410, 130,  60],  # +6 → +7
	[  20, 280, 430, 170, 100],  # +7 → +8
	[  10, 200, 440, 200, 150],  # +8 → +9
	[   5, 145, 440, 210, 200],  # +9 → +10
]

# refine_count 별 골드 비용 (단순 등비).
const REFINE_COST := [50, 100, 200, 400, 800, 1500, 3000, 6000, 12000, 25000]


func _ready() -> void:
	visible = false
	item_select.item_selected.connect(_on_item_selected)
	refine_btn.pressed.connect(_on_refine_pressed)
	close_btn.pressed.connect(toggle)


## 외부에서 호출 — 패널 표시/숨김 토글.
func toggle() -> void:
	_shown = not _shown
	visible = _shown
	if _shown:
		_refresh_item_list()
	else:
		closed.emit()


## 인벤토리에서 강화 가능한 (equip 카테고리) 아이템만 리스트.
func _refresh_item_list() -> void:
	item_select.clear()
	_selected_inv_idx = -1
	result_log.text = ""
	for i in GameState.inventory.size():
		var name = str(GameState.inventory[i])
		var info = GameData.item_lookup(name)
		if info.get("category", "") != "equip": continue
		var ref = GameState.get_refine(i)
		var label = "%s +%d" % [name, int(ref.get("refine_count", 0))]
		if ref.get("locked", false):
			label += " 🔒"
		# ItemList 의 metadata 로 inv_idx 저장
		var idx = item_select.add_item(label)
		item_select.set_item_metadata(idx, i)
	_apply_preview()


func _on_item_selected(idx: int) -> void:
	_selected_inv_idx = int(item_select.get_item_metadata(idx))
	_apply_preview()


## 현재 + 다음 단계 stat preview + 비용 + prob 표시.
func _apply_preview() -> void:
	if _selected_inv_idx < 0:
		current_label.text = "(아이템 선택)"
		preview_label.text = ""
		gold_cost_label.text = ""
		refine_btn.disabled = true
		return
	var item_name = str(GameState.inventory[_selected_inv_idx])
	var info = GameData.item_lookup(item_name)
	var ref = GameState.get_refine(_selected_inv_idx)
	var rc: int = int(ref.get("refine_count", 0))
	var sub: int = int(ref.get("sub_count", 0))
	var locked: bool = ref.get("locked", false)
	var base: int = int(info.get("stat_a", 0))
	var cur_stat: int = base + sub
	current_label.text = "%s +%d\n현재 stat %d (base %d + sub %d)" % [
		item_name, rc, cur_stat, base, sub]
	if locked:
		preview_label.text = "잠겨있음 — 강화 불가"
		gold_cost_label.text = ""
		refine_btn.disabled = true
		return
	if rc >= 10:
		preview_label.text = "이미 +10 (최대 단계)"
		gold_cost_label.text = ""
		refine_btn.disabled = true
		return
	# 다음 단계 preview
	var prob = REFINE_PROB[rc]
	var cost = REFINE_COST[rc]
	preview_label.text = "다음 +%d : 성공 %d.%d%% / lock %d.%d%% / destroy %d.%d%%" % [
		rc + 1,
		(prob[0] + prob[1]) / 10, (prob[0] + prob[1]) % 10,
		prob[3] / 10, prob[3] % 10,
		prob[4] / 10, prob[4] % 10,
	]
	gold_cost_label.text = "비용 %d G  (보유 %d G)" % [cost, GameState.gold]
	refine_btn.disabled = GameState.gold < cost


## 강화 실행 — Round 26 의 5-case prob roll + state update.
func _on_refine_pressed() -> void:
	if _selected_inv_idx < 0: return
	var ref = GameState.get_refine(_selected_inv_idx)
	var rc: int = int(ref.get("refine_count", 0))
	if rc >= 10 or ref.get("locked", false): return
	var cost = REFINE_COST[rc]
	if GameState.gold < cost: return
	GameState.gold -= cost
	var prob = REFINE_PROB[rc]
	var roll = randi() % 1000
	var case_idx = 0
	var acc = 0
	for i in 5:
		acc += prob[i]
		if roll < acc:
			case_idx = i
			break
	# Round 26 mechanism 적용
	var new_rc = rc
	var new_sub = int(ref.get("sub_count", 0))
	var new_locked = false
	var item_name = str(GameState.inventory[_selected_inv_idx])
	match case_idx:
		0:  # 큰성공
			new_rc += 1
			new_sub += 2
		1:  # 성공
			new_rc += 1
			new_sub += 1
		2:  # 재료소비
			pass
		3:  # lock
			new_locked = true
		4:  # destroy
			GameState.inventory.remove_at(_selected_inv_idx)
			GameState.clear_refine(_selected_inv_idx)
			# equipment 에서도 제거
			for slot in GameState.SLOT_COUNT:
				if GameState.equipment[slot] == _selected_inv_idx:
					GameState.equipment[slot] = -1
				elif GameState.equipment[slot] > _selected_inv_idx:
					GameState.equipment[slot] -= 1
			result_log.text = "💥 %s 파괴됨..." % item_name
			GameState.state_changed.emit()
			refined.emit(_selected_inv_idx, case_idx)
			_refresh_item_list()
			return
	GameState.set_refine(_selected_inv_idx, new_rc, new_sub, new_locked)
	result_log.text = "%s → %s +%d (sub %d)" % [CASE_NAME[case_idx], item_name, new_rc, new_sub]
	refined.emit(_selected_inv_idx, case_idx)
	_refresh_item_list()
	# 방금 선택된 item 유지
	for i in item_select.item_count:
		if int(item_select.get_item_metadata(i)) == _selected_inv_idx:
			item_select.select(i)
			_apply_preview()
			break
