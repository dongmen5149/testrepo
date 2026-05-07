## Quest 진행 시스템.
##
## quests.json (105 missions + 72 tree) + quests_text.json 사용.
## Interpreter 의 Quest opcode (QuestStatus / QuestSwitch / QuestQSwitch /
## QuestBoss) 와 연결.
extends Node

signal quest_started(quest_id: int, name: String)
signal quest_completed(quest_id: int)
signal quest_status_changed(quest_id: int, status: int)

# status: 0=inactive, 1=active, 2=completed, 3=failed
const STATUS_INACTIVE := 0
const STATUS_ACTIVE := 1
const STATUS_COMPLETED := 2
const STATUS_FAILED := 3

var _quests: Array = []     # mission_list
var _tree: Array = []       # questTree
var _state: Dictionary = {} # quest_id → status


func _ready() -> void:
	var p := "res://assets/gamedata/quests.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Dictionary:
			_quests = data.get("quests", [])
			_tree = data.get("tree", [])
	print("[Quest] loaded %d quests, %d tree nodes" % [_quests.size(), _tree.size()])


func quest_name(qid: int) -> String:
	if qid < 0 or qid >= _quests.size(): return ""
	return _quests[qid].get("name", "")


func start(qid: int) -> void:
	_state[qid] = STATUS_ACTIVE
	quest_started.emit(qid, quest_name(qid))
	quest_status_changed.emit(qid, STATUS_ACTIVE)


func complete(qid: int) -> void:
	_state[qid] = STATUS_COMPLETED
	quest_completed.emit(qid)
	quest_status_changed.emit(qid, STATUS_COMPLETED)


func active_quests() -> Array:
	return [k for k in _state.keys() if _state[k] == STATUS_ACTIVE]


func is_active(qid: int) -> bool:
	return _state.get(qid, STATUS_INACTIVE) == STATUS_ACTIVE


func is_completed(qid: int) -> bool:
	return _state.get(qid, STATUS_INACTIVE) == STATUS_COMPLETED


## save / restore
func to_save() -> Dictionary:
	return _state.duplicate()


func from_save(data: Dictionary) -> void:
	_state = data.duplicate()
