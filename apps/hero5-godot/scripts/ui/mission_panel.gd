## Mission 진척 UI (Round 58).
##
## Mission singleton (autoload) 의 105 missions 표시.
## 데이터: mission.json (Round 37/38 decoder)
##
## UI 구성:
##   - 상단: 탭 (전체 / 진행중 / 완료 / 미시작)
##   - 좌측: mission 리스트 (type 라벨 + 이름 + 완료 표시)
##   - 우측: 선택된 mission detail
##       * 제목 + 타입 라벨
##       * 5 sub_conditions 의 (slot/sub_flag/target_value) + 현재 진척
##       * target_count / 완료 표시
##   - 하단: 필터 cycle 버튼 + 닫기
class_name MissionPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var mission_list: ItemList = $BG/MissionList
@onready var title_label: Label = $BG/Detail/TitleLabel
@onready var type_label: Label = $BG/Detail/TypeLabel
@onready var summary_label: Label = $BG/Detail/SummaryLabel
@onready var conds_label: Label = $BG/Detail/CondsLabel
@onready var filter_btn: Button = $BG/FilterBtn
@onready var close_btn: Button = $BG/CloseBtn

const FILTER_LABELS := ["탭: 전체", "탭: 진행중", "탭: 완료", "탭: 미시작"]
var _filter: int = 0  # 0=전체 1=진행중 2=완료 3=미시작
var _selected_mid: int = -1
var _filtered_ids: Array[int] = []


func _ready() -> void:
	visible = false
	mission_list.item_selected.connect(_on_mission_selected)
	filter_btn.pressed.connect(_cycle_filter)
	close_btn.pressed.connect(func(): visible = false)
	Mission.mission_progress_changed.connect(_on_mission_progress)
	Mission.mission_completed.connect(_on_mission_completed)


func toggle() -> void:
	visible = not visible
	if visible: _refresh()


func _cycle_filter() -> void:
	_filter = (_filter + 1) % FILTER_LABELS.size()
	filter_btn.text = FILTER_LABELS[_filter]
	_refresh()


func _refresh() -> void:
	mission_list.clear()
	_filtered_ids.clear()
	for mid in Mission.mission_count():
		var status = _status_of(mid)
		if not _filter_matches(status): continue
		_filtered_ids.append(mid)
		var name = Mission.mission_name(mid)
		var type_lbl = Mission.mission_type_label(mid)
		var mark = ""
		match status:
			"completed": mark = " ✓"
			"in_progress": mark = " …"
			"not_started": mark = ""
		var idx = mission_list.add_item("[%s] %s%s" % [type_lbl, name, mark])
		if status == "completed":
			mission_list.set_item_custom_fg_color(idx, Color(0.6, 1, 0.6, 1))
		elif status == "in_progress":
			mission_list.set_item_custom_fg_color(idx, Color(1, 0.95, 0.6, 1))
	if _selected_mid >= 0:
		_show_detail(_selected_mid)
	else:
		_clear_detail()


func _filter_matches(status: String) -> bool:
	match _filter:
		0: return true
		1: return status == "in_progress"
		2: return status == "completed"
		3: return status == "not_started"
	return true


func _status_of(mid: int) -> String:
	if Mission.is_completed(mid):
		return "completed"
	var rec = Mission.mission_dict(mid)
	var subs: Array = rec.get("sub_conditions", [])
	for i in subs.size():
		if Mission.get_progress(mid, i) > 0:
			return "in_progress"
	return "not_started"


func _on_mission_selected(idx: int) -> void:
	if idx < 0 or idx >= _filtered_ids.size(): return
	_show_detail(_filtered_ids[idx])


func _show_detail(mid: int) -> void:
	_selected_mid = mid
	var rec = Mission.mission_dict(mid)
	if rec.is_empty():
		_clear_detail()
		return
	title_label.text = "[#%d] %s" % [mid, rec.get("name", "")]
	var mtype = int(rec.get("mission_type", 255))
	var sub_type = int(rec.get("sub_type", 0))
	type_label.text = "타입: %s (mt=%d, st=%d, target_count=%d)" % [
		Mission.mission_type_label(mid), mtype, sub_type,
		int(rec.get("target_count", 0))]
	summary_label.text = "📊 %s" % Mission.progress_summary(mid)
	if Mission.is_completed(mid):
		summary_label.text += "   ✓ 완료"
		summary_label.modulate = Color(0.6, 1, 0.6, 1)
	else:
		summary_label.modulate = Color(1, 1, 0.8, 1)

	# sub_conditions 표시
	var subs: Array = rec.get("sub_conditions", [])
	var lines: Array[String] = []
	for i in subs.size():
		var sc: Dictionary = subs[i]
		var slot = int(sc.get("slot", 255))
		var sub_flag = int(sc.get("sub_flag", 255))
		var tgt = int(sc.get("target_value", 0))
		if slot == 255 and sub_flag == 255: continue   # placeholder
		var cur = Mission.get_progress(mid, i)
		var mark = "✓" if cur >= tgt else " "
		var sc_str = "[%s] sub#%d: " % [mark, i]
		if slot != 255: sc_str += "슬롯%d  " % slot
		if sub_flag != 255: sc_str += "ID%d  " % sub_flag
		sc_str += "%d / %d" % [cur, tgt]
		lines.append(sc_str)
	if lines.is_empty():
		lines.append("(특수 조건 — final_flag 참조)")
	conds_label.text = "조건:\n" + "\n".join(lines)


func _clear_detail() -> void:
	_selected_mid = -1
	title_label.text = "(미션 선택)"
	type_label.text = ""
	summary_label.text = ""
	conds_label.text = ""


func _on_mission_progress(mid: int) -> void:
	if not visible: return
	_refresh()
	if mid == _selected_mid:
		_show_detail(mid)


func _on_mission_completed(_mid: int, _name: String) -> void:
	if not visible: return
	_refresh()
