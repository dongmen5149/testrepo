## 퀘스트 진행 UI.
##
## active_quests + completed_quests 를 ItemList 로 표시.
class_name QuestPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var active_list: ItemList = $BG/ActiveList
@onready var completed_list: ItemList = $BG/CompletedList
@onready var info: Label = $BG/Info
@onready var close_btn: Button = $BG/CloseButton


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)
	active_list.item_selected.connect(_on_active_selected)
	completed_list.item_selected.connect(_on_completed_selected)


func toggle() -> void:
	visible = not visible
	if visible: _refresh()


func _refresh() -> void:
	active_list.clear()
	completed_list.clear()
	var active = []
	var completed = []
	for qid in Quest._state.keys():
		var status = Quest._state[qid]
		var name = Quest.quest_name(qid)
		if status == Quest.STATUS_ACTIVE:
			active.append([qid, name])
		elif status == Quest.STATUS_COMPLETED:
			completed.append([qid, name])
	for entry in active:
		active_list.add_item("[#%d] %s" % entry)
	for entry in completed:
		completed_list.add_item("[#%d] %s ✓" % entry)
	if active.is_empty() and completed.is_empty():
		info.text = "진행 중인 퀘스트가 없습니다.\nNPC 와 대화하여 시작하세요."
	else:
		info.text = "활성: %d  완료: %d" % [active.size(), completed.size()]


func _on_active_selected(idx: int) -> void:
	# 활성 quest_id 찾기 (enumerate)
	var active_qids: Array = []
	for qid in Quest._state.keys():
		if Quest._state[qid] == Quest.STATUS_ACTIVE:
			active_qids.append(qid)
	if idx < active_qids.size():
		var qid = active_qids[idx]
		var prog = Quest.quest_progress_text(qid)
		info.text = "%s\n%s" % [Quest.quest_name(qid), prog if not prog.is_empty() else "진행 중"]
	else:
		info.text = active_list.get_item_text(idx)


func _on_completed_selected(idx: int) -> void:
	info.text = completed_list.get_item_text(idx)
