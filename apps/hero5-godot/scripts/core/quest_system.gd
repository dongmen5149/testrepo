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

# 처치 카운트 추적: { quest_id: { monster_id: count } }
var _kill_counts: Dictionary = {}
# 처치 목표: { quest_id: { monster_id: target } }  — quest 데이터에서 로드 가능
var _kill_targets: Dictionary = {}


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
	# 기본 목표: 첫 5개 quest 는 monster 처치형 (qid % 75 의 enemy 3마리)
	if qid >= 0 and qid < 5:
		var target_monster = qid % 75
		_kill_targets[qid] = {target_monster: 3}
		_kill_counts[qid] = {target_monster: 0}
	quest_started.emit(qid, quest_name(qid))
	quest_status_changed.emit(qid, STATUS_ACTIVE)


## 적 처치 알림 — 활성 퀘스트의 카운트 갱신, 목표 달성 시 자동 완료.
func on_enemy_killed(monster_id: int) -> void:
	for qid in _kill_targets.keys():
		if _state.get(qid, STATUS_INACTIVE) != STATUS_ACTIVE: continue
		var targets: Dictionary = _kill_targets[qid]
		if monster_id not in targets: continue
		var counts: Dictionary = _kill_counts.get(qid, {})
		counts[monster_id] = int(counts.get(monster_id, 0)) + 1
		_kill_counts[qid] = counts
		# 모든 목표 달성?
		var all_done = true
		for mid in targets:
			if int(counts.get(mid, 0)) < int(targets[mid]):
				all_done = false; break
		if all_done:
			complete(qid)


func quest_progress_text(qid: int) -> String:
	if qid not in _kill_targets: return ""
	var targets: Dictionary = _kill_targets[qid]
	var counts: Dictionary = _kill_counts.get(qid, {})
	var lines: Array = []
	for mid in targets:
		lines.append("  몬스터 #%d: %d/%d" % [
			mid, int(counts.get(mid, 0)), int(targets[mid])])
	return "\n".join(lines)


func complete(qid: int) -> void:
	_state[qid] = STATUS_COMPLETED
	quest_completed.emit(qid)
	quest_status_changed.emit(qid, STATUS_COMPLETED)
	# 자동 보상 지급: rewards.json 의 tier 0 entry 사용
	_grant_reward(qid)


## 보상 지급 — rewards.json 의 6B record 사용 (type-byte 분기).
##   현재 가설: byte[0] 가 reward_type (0x06+=item, 0x0d=gold, 0x0f=exp),
##   byte[1..3] 가 value (LE u24).
##   기본값: gold = qid×50+100, exp = qid×30+50.
var _rewards_cache: Array = []


func _grant_reward(qid: int) -> void:
	if _rewards_cache.is_empty():
		var p := "res://assets/gamedata/rewards.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_rewards_cache = JSON.parse_string(f.get_as_text()) or []

	var gold_reward = qid * 50 + 100
	var exp_reward = qid * 30 + 50
	var item_to_grant := ""

	# rewards tier 0 의 qid 번째 record 가 있으면 사용
	if _rewards_cache.size() > 0:
		var tier = _rewards_cache[0]
		var recs: Array = tier.get("records", [])
		if qid < recs.size():
			var hex = recs[qid].get("extra_hex", "")
			if hex.length() >= 4:
				var reward_type = int(hex.substr(0, 2), 16)
				var value_lo = int(hex.substr(2, 2), 16)
				var value_hi = int(hex.substr(4, 2), 16) if hex.length() >= 6 else 0
				var value = value_lo | (value_hi << 8)
				match reward_type:
					0x0d:  # gold 추정
						gold_reward = max(gold_reward, value * 10)
					0x0f:  # exp 추정
						exp_reward = max(exp_reward, value * 5)
					0x06, 0x07, 0x08, 0x11:  # item 추정
						# value 를 item 인덱스로 슬롯 0..3 에서 검색
						var slot = reward_type - 0x06
						var arr = GameData.items_in_slot(slot)
						if value < arr.size() and not arr[value].is_empty():
							item_to_grant = arr[value]

	GameState.gold += gold_reward
	GameState.add_battle_reward(exp_reward, 0)
	if item_to_grant.is_empty():
		item_to_grant = "미들포션"  # fallback
	GameState.inventory.append(item_to_grant)
	GameState.state_changed.emit()


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
