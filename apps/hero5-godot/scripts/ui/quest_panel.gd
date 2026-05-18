## 퀘스트 진행 UI (Round 56 강화).
##
## Round 40 의 quests.json schema 활용:
##   - by_difficulty.q0/q1/q2 (각 151 quests) — 난이도 선택 가능
##   - quest.objectives = phase1 의 3×6B (cond_type/cond_sub/target_value)
##   - quest.rewards    = phase2 의 3×6B (17=money, 18=exp, 255=unused)
##   - quest.description / category
##
## UI 구성:
##   - 좌측: 활성/완료 ItemList
##   - 우측: 선택된 quest 의 detail card
##       * 제목 + 카테고리
##       * description (autowrap)
##       * 목표 (objectives) 라인 + 진척
##       * 보상 (rewards) 라인
##   - 하단: 난이도 토글 (Easy/Normal/Hard) + 닫기
class_name QuestPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var active_list: ItemList = $BG/ActiveList
@onready var completed_list: ItemList = $BG/CompletedList
@onready var title_label: Label = $BG/Detail/TitleLabel
@onready var category_label: Label = $BG/Detail/CategoryLabel
@onready var desc_label: Label = $BG/Detail/DescLabel
@onready var objectives_label: Label = $BG/Detail/ObjectivesLabel
@onready var rewards_label: Label = $BG/Detail/RewardsLabel
@onready var progress_label: Label = $BG/Detail/ProgressLabel
@onready var diff_btn: Button = $BG/DiffBtn
@onready var close_btn: Button = $BG/CloseButton
@onready var info: Label = $BG/Info

var _selected_qid: int = -1


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)
	active_list.item_selected.connect(_on_active_selected)
	completed_list.item_selected.connect(_on_completed_selected)
	diff_btn.pressed.connect(_cycle_difficulty)
	_update_diff_label()
	_clear_detail()


func toggle() -> void:
	visible = not visible
	if visible: _refresh()


func _cycle_difficulty() -> void:
	Quest.current_difficulty = (Quest.current_difficulty + 1) % 3
	_update_diff_label()
	# 선택된 quest 가 있으면 detail 만 갱신 (이름/objective/reward 가 difficulty 별)
	if _selected_qid >= 0:
		_show_detail(_selected_qid)
	_refresh_lists()


func _update_diff_label() -> void:
	var d = Quest.current_difficulty
	diff_btn.text = ["난이도: 쉬움", "난이도: 보통", "난이도: 어려움"][d]
	diff_btn.modulate = [
		Color(0.7, 1, 0.7, 1),
		Color(1, 1, 0.7, 1),
		Color(1, 0.7, 0.7, 1),
	][d]


func _refresh() -> void:
	_refresh_lists()
	if _selected_qid >= 0:
		_show_detail(_selected_qid)


func _refresh_lists() -> void:
	active_list.clear()
	completed_list.clear()
	var active: Array = []
	var completed: Array = []
	for qid in Quest._state.keys():
		var status = Quest._state[qid]
		var name = Quest.quest_name(qid)
		if status == Quest.STATUS_ACTIVE:
			active.append([qid, name])
		elif status == Quest.STATUS_COMPLETED:
			completed.append([qid, name])
	for entry in active:
		var i = active_list.add_item("[#%d] %s" % entry)
		active_list.set_item_metadata(i, entry[0])
	for entry in completed:
		var i = completed_list.add_item("[#%d] %s ✓" % entry)
		completed_list.set_item_metadata(i, entry[0])
	if active.is_empty() and completed.is_empty():
		info.text = "진행 중인 퀘스트가 없습니다. NPC 와 대화하여 시작하세요."
	else:
		info.text = "활성: %d  완료: %d" % [active.size(), completed.size()]


func _on_active_selected(idx: int) -> void:
	var qid = int(active_list.get_item_metadata(idx))
	_show_detail(qid)


func _on_completed_selected(idx: int) -> void:
	var qid = int(completed_list.get_item_metadata(idx))
	_show_detail(qid)


func _show_detail(qid: int) -> void:
	_selected_qid = qid
	var name = Quest.quest_name(qid)
	if name.is_empty():
		_clear_detail()
		return
	title_label.text = "[#%d] %s" % [qid, name]
	category_label.text = "[%s]" % Quest.quest_category(qid)
	var desc = Quest.quest_description(qid)
	desc_label.text = desc if not desc.is_empty() else "(설명 없음)"

	# 목표
	var obj_lines: Array[String] = []
	var objectives = Quest.quest_objectives(qid)
	if objectives.is_empty():
		obj_lines.append("  (조건 없음 — 자유 진행)")
	else:
		for obj in objectives:
			obj_lines.append("  • " + Quest.objective_label(obj))
	objectives_label.text = "🎯 목표:\n" + "\n".join(obj_lines)

	# 보상
	var rew_lines: Array[String] = []
	var rewards = Quest.quest_rewards(qid)
	if rewards.is_empty():
		rew_lines.append("  (보상 없음)")
	else:
		for r in rewards:
			rew_lines.append("  • " + Quest.reward_label(r))
	rewards_label.text = "🎁 보상:\n" + "\n".join(rew_lines)

	# 진척 (kill counts 등 — 첫 5 quest 만 placeholder)
	var prog = Quest.quest_progress_text(qid)
	if not prog.is_empty():
		progress_label.text = "📊 진척:\n" + prog
	else:
		var status = Quest._state.get(qid, Quest.STATUS_INACTIVE)
		match status:
			Quest.STATUS_ACTIVE: progress_label.text = "📊 진행 중"
			Quest.STATUS_COMPLETED: progress_label.text = "📊 완료 ✓"
			_: progress_label.text = ""


func _clear_detail() -> void:
	_selected_qid = -1
	title_label.text = "(퀘스트 선택)"
	category_label.text = ""
	desc_label.text = ""
	objectives_label.text = ""
	rewards_label.text = ""
	progress_label.text = ""
