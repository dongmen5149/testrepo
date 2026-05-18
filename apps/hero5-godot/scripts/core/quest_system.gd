## Quest 진행 시스템.
##
## quests.json (Round 40 decoder 산출: by_difficulty.q0/q1/q2 × 151 quests) 사용.
## Interpreter 의 Quest opcode (QuestStatus / QuestSwitch / QuestQSwitch /
## QuestBoss) 와 연결.
##
## 데이터 schema (decode_h5_quest.py — Round 40):
##   {
##     "by_difficulty": {
##       "q0": [{idx, name, description, category, h0, h2, obj_count,
##               objectives: [{type, sub, value, kind}×3],
##               rewards:    [{type, sub, value, kind}×3], trailer, ...}×151],
##       "q1": [...×151], "q2": [...×151]
##     },
##     "reward_type_table": {17: "money", 18: "exp", 255: "unused"},
##     "cond_type_table": {17: "cond_17", 18: "cond_18", 255: "unused"},
##     "compare": [...]
##   }
extends Node

signal quest_started(quest_id: int, name: String)
signal quest_completed(quest_id: int)
signal quest_status_changed(quest_id: int, status: int)

# status: 0=inactive, 1=active, 2=completed, 3=failed
const STATUS_INACTIVE := 0
const STATUS_ACTIVE := 1
const STATUS_COMPLETED := 2
const STATUS_FAILED := 3

# Reward type codes (phase2 byte 0) — Round 65 RE 확정 (docs/h5/RE/quest_reward_types.md)
# QuestRewardData @0xd458c 분석: type 0-16 모두 ItemTable::NewItemToBagEx(cat=type, idx=sub, qty=value)
# 즉 reward.type = item category (= items.json slot 번호), sub = idx, value = quantity
const REWARD_TYPE_MONEY := 17     # BagItem::IncreaseMoney(value)
const REWARD_TYPE_EXP := 18       # HERO+0x230 += value
const REWARD_TYPE_HP := 19        # HERO+0x234 += value (stat[0]=HP) — disasm only
const REWARD_TYPE_INT := 20       # HERO+0x246 += value (stat[5]=INT) — disasm only
const REWARD_TYPE_UNUSED := 255
# type 0..16 = item slot (cat). R65 RE 로 확정.
const REWARD_TYPE_ITEM_MAX := 16  # type ≤ 16 = item dispatch

# slot → 한국어 라벨 (items.json _meta.category_dispatch kind 와 1:1)
const REWARD_SLOT_LABEL := {
	0: "무기A", 1: "무기B", 2: "무기C", 3: "무기D",
	4: "갑옷", 5: "헬멧", 6: "부츠",
	7: "액세서리A", 8: "액세서리B", 9: "방패",
	10: "영혼석", 11: "포션", 12: "오브",
	13: "재료", 14: "퀘스트 아이템", 15: "합성서",
	16: "스킬북",
}

# Condition type codes (phase1 byte 0) — Round 60 RE 확정 (docs/h5/RE/quest_cond_types.md)
const COND_TYPE_ITEM_HOLD_A := 13     # bag item count (variant A) — 8 quests
const COND_TYPE_ITEM_HOLD_B := 14     # bag item count (variant B) — 38 quests, default handler
const COND_TYPE_MONSTER_KILL := 17    # kill N of monster_id (QuestCheck event 0x11)
const COND_TYPE_QUEST_SWITCH := 18    # quest switch state (Event_QuestSwitch arg)
const COND_TYPE_UNUSED := 255

# 어느 difficulty 로 quest detail 표시할지 (0/1/2 = easy/normal/hard).
# UI 가 변경 가능. data 는 모든 difficulty 가 동시에 메모리에 있음.
var current_difficulty: int = 0

var _difficulty_data: Array = [[], [], []]   # 3 arrays of 151 quest dicts
var _state: Dictionary = {}                  # quest_id → status

# 처치 카운트 추적: { quest_id: { monster_id: count } }
var _kill_counts: Dictionary = {}
# 처치 목표: { quest_id: { monster_id: target } }  — quest 데이터에서 로드 가능
var _kill_targets: Dictionary = {}


func _ready() -> void:
	_load_quests()


func _load_quests() -> void:
	var p := "res://assets/gamedata/quests.json"
	if not FileAccess.file_exists(p):
		push_warning("quests.json not found")
		return
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if not (data is Dictionary): return
	# 신규 Round 40 schema
	var by_diff = data.get("by_difficulty", {})
	if by_diff is Dictionary and not by_diff.is_empty():
		_difficulty_data[0] = by_diff.get("q0", [])
		_difficulty_data[1] = by_diff.get("q1", [])
		_difficulty_data[2] = by_diff.get("q2", [])
	else:
		# Legacy schema (Round 39 이전): {quests: [{name, extra_hex}]}
		var legacy = data.get("quests", [])
		_difficulty_data[0] = legacy
		_difficulty_data[1] = legacy
		_difficulty_data[2] = legacy
	print("[Quest] loaded %d / %d / %d quests (q0/q1/q2)" % [
		_difficulty_data[0].size(), _difficulty_data[1].size(), _difficulty_data[2].size()])


## 현재 difficulty 의 quest 배열.
func quests() -> Array:
	return _difficulty_data[current_difficulty]


func quest_count() -> int:
	return quests().size()


func quest_dict(qid: int) -> Dictionary:
	var arr = quests()
	if qid < 0 or qid >= arr.size(): return {}
	return arr[qid]


func quest_name(qid: int) -> String:
	return str(quest_dict(qid).get("name", ""))


func quest_description(qid: int) -> String:
	return str(quest_dict(qid).get("description", ""))


func quest_category(qid: int) -> String:
	return str(quest_dict(qid).get("category", ""))


## phase1 의 3 objectives 중 unused (type=255) 제외.
## 각 entry: {type, sub, value, kind}.
func quest_objectives(qid: int) -> Array:
	var arr: Array = quest_dict(qid).get("objectives", [])
	var out: Array = []
	for e in arr:
		if int(e.get("type", 255)) == COND_TYPE_UNUSED: continue
		out.append(e)
	return out


## phase2 의 3 rewards 중 unused (type=255) 제외.
## 각 entry: {type, sub, value, kind}.
func quest_rewards(qid: int) -> Array:
	var arr: Array = quest_dict(qid).get("rewards", [])
	var out: Array = []
	for e in arr:
		if int(e.get("type", 255)) == REWARD_TYPE_UNUSED: continue
		out.append(e)
	return out


## 사람이 읽을 수 있는 reward 라벨 (UI 표시용). Round 65 RE 반영.
##
## type ≤ 16 = item (cat=type, idx=sub). items.json 에서 이름 조회.
## type 17 = money, 18 = exp, 19 = HP, 20 = INT, 255 = unused.
func reward_label(reward: Dictionary) -> String:
	var t = int(reward.get("type", 255))
	var s = int(reward.get("sub", 0))
	var v = int(reward.get("value", 0))
	if t == REWARD_TYPE_MONEY: return "💰 골드 +%d" % v
	if t == REWARD_TYPE_EXP:   return "⭐ 경험치 +%d" % v
	if t == REWARD_TYPE_HP:    return "❤ HP +%d" % v
	if t == REWARD_TYPE_INT:   return "🔮 INT +%d" % v
	if t == REWARD_TYPE_UNUSED: return ""
	if t >= 0 and t <= REWARD_TYPE_ITEM_MAX:
		var item_name = GameData.item_name_at(t, s) if GameData else ""
		var slot_label = REWARD_SLOT_LABEL.get(t, "?")
		if item_name and item_name != "" and not item_name.begins_with("("):
			if v > 1:
				return "🎁 %s × %d" % [item_name, v]
			return "🎁 %s" % item_name
		# fallback: slot label
		return "🎁 [%s] #%d × %d" % [slot_label, s, v]
	return "보상[type=%d, sub=%d, val=%d]" % [t, s, v]


## 사람이 읽을 수 있는 objective 라벨 (UI 표시용).
## Round 60 RE 확정 매핑 (docs/h5/RE/quest_cond_types.md).
func objective_label(obj: Dictionary) -> String:
	var t = int(obj.get("type", 255))
	var s = int(obj.get("sub", 0))
	var v = int(obj.get("value", 0))
	match t:
		COND_TYPE_UNUSED: return ""
		COND_TYPE_ITEM_HOLD_A: return "[수집A] 아이템 #%d × %d개 보유" % [s, v]
		COND_TYPE_ITEM_HOLD_B: return "[수집B] 아이템 #%d × %d개 보유" % [s, v]
		COND_TYPE_MONSTER_KILL: return "[사냥] 몬스터 #%d × %d 처치" % [s, v]
		COND_TYPE_QUEST_SWITCH: return "[퀘스트 스위치] slot %d → state %d" % [s, v]
	return "조건 [type=%d, sub=%d] → 목표 %d" % [t, s, v]


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
	# 자동 보상 지급: quests.json 의 rewards 사용 (Round 40)
	_grant_reward(qid)


## quests.json 의 quest_rewards(qid) 를 GameState 에 적용. Round 65 RE 반영.
##
## type ≤ 16 = item (inventory append). 17 = money. 18 = exp. 19/20 = stat boost. 255 = unused.
func _grant_reward(qid: int) -> void:
	var rewards = quest_rewards(qid)
	var gold_gain = 0
	var exp_gain = 0
	for r in rewards:
		var t = int(r.get("type", 255))
		var s = int(r.get("sub", 0))
		var v = int(r.get("value", 0))
		if t == REWARD_TYPE_MONEY: gold_gain += v
		elif t == REWARD_TYPE_EXP: exp_gain += v
		elif t == REWARD_TYPE_HP:
			GameState.max_hp += v
			GameState.hp = min(GameState.hp + v, GameState.max_hp)
		elif t == REWARD_TYPE_INT:
			GameState.stat_int += v
		elif t == REWARD_TYPE_UNUSED: pass
		elif t >= 0 and t <= REWARD_TYPE_ITEM_MAX:
			# item reward (cat=type, idx=sub, qty=value)
			var item_name = GameData.item_name_at(t, s) if GameData else ""
			if item_name and item_name != "" and not item_name.begins_with("("):
				var qty = max(1, v)
				for _i in range(qty):
					GameState.inventory.append(item_name)
	# 미정의 / 빈 보상의 경우 최소 default 지급 (UX)
	if gold_gain == 0 and exp_gain == 0:
		gold_gain = qid * 50 + 100
		exp_gain = qid * 30 + 50
	GameState.gold += gold_gain
	GameState.add_battle_reward(exp_gain, 0)
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
