## Mission 진척 추적 시스템 (Round 58).
##
## mission.json (Round 37/38 decoder 산출, 105 missions) 사용.
## 13 Check* 함수 (Mission::CheckMissionRefine / CheckOrbCombine / CheckMissionMix /
## CheckMissionPlaytime / CheckMissionMoney / CheckMissionRank / CheckMissionSetItem /
## CheckCollection / CheckQuestComplete 등) 의 호출 트리거.
##
## 데이터 schema (decode_h5_mission.py):
##   {
##     "count": 105,
##     "entries": [{idx, name, mission_type, sub_type, target_count, final_flag,
##                  sub_conditions: [{slot, sub_flag, target_value} × 5]}×105]
##   }
##
## mission_type 매핑 (Round 59 RE 확인 — docs/h5/RE/mission_quest_types.md):
##   0 (20)  사냥 — CheckMonsterHunting + HuntingCounting. sub_flag = monster_id
##   1 (5)   특수 처치 — BossCompleteCounting (this[0x22c]==3 boss flag)
##   2 (22)  세트 수집 — CheckMissionSetItem. slot = equip slot (5-8), sub_flag = item_idx
##   3 (47)  누적 도전 — sub_type 으로 sub-dispatch:
##                       sub_type 1 = HeroDie, 2 = Playtime, 4 = BattleUseItem,
##                       6 = Refine, 0xa(10) = OrbCombine, 기타 = generic threshold
##   4 (5)   카테고리 수집 — CheckCollection (sub_type = item category 1/2/3)
##   5 (5)   달성 과제 (Rank) — CheckMissionRank + QuestCompleteCounting (cap 99)
##   255 (1) 튜토리얼 — 첫 quest "여행자" (모든 필드 0xFF)
extends Node

signal mission_started(mission_id: int, name: String)
signal mission_completed(mission_id: int, name: String)
signal mission_progress_changed(mission_id: int)

# mission_type 별 label (UI 표시용)
const TYPE_LABELS := {
	0: "사냥",
	1: "특수 처치",
	2: "세트 수집",
	3: "누적 도전",
	4: "카테고리 수집",
	5: "달성 과제",
	255: "튜토리얼",
}

# Event kind — bump_progress 가 받는 generic 이벤트 종류
const EVENT_MONSTER_KILL := "monster_kill"
const EVENT_ITEM_OBTAINED := "item_obtained"
const EVENT_REFINE_DONE := "refine_done"
const EVENT_ORB_COMBINE := "orb_combine"
const EVENT_MIX_DONE := "mix_done"
const EVENT_PLAYTIME := "playtime"
const EVENT_MONEY := "money"
const EVENT_QUEST_DONE := "quest_done"

# event_kind 가 매칭되는 mission_type (Round 59 RE 결과).
const EVENT_TO_MISSION_TYPES := {
	EVENT_MONSTER_KILL: [0, 1],
	EVENT_ITEM_OBTAINED: [2, 4],
	EVENT_REFINE_DONE: [3],
	EVENT_ORB_COMBINE: [3],
	EVENT_MIX_DONE: [3],
	EVENT_PLAYTIME: [3],
	EVENT_MONEY: [3],
	EVENT_QUEST_DONE: [5],
}

## type=3 누적 도전 의 sub_type 정밀 필터 (Round 59 RE).
## event_kind 가 type 3 의 sub_type 와 매칭되는지 — 없으면 모든 sub_type 허용 (느슨).
const EVENT_TO_SUB_TYPES := {
	EVENT_REFINE_DONE: [6],          # CheckMissionRefine 의 cmp #6
	EVENT_ORB_COMBINE: [10],         # CheckOrbCombine 의 cmp #0xa
	EVENT_PLAYTIME: [2],             # CheckMissionPlaytime 의 cmp #2
	EVENT_MIX_DONE: [],              # sub_type 미해석 — 모든 sub 허용
	EVENT_MONEY: [],                 # sub_type 미해석 — 모든 sub 허용
}

var _missions: Array = []  # 105 mission record
# {mission_id: {sub_idx: current_value}} — sub_conditions 별 누적값
var _progress: Dictionary = {}
# {mission_id: bool} — 완료 표시
var _completed: Dictionary = {}


func _ready() -> void:
	_load_missions()


func _load_missions() -> void:
	var p := "res://assets/gamedata/mission.json"
	if not FileAccess.file_exists(p):
		push_warning("mission.json not found")
		return
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if data is Dictionary:
		_missions = data.get("entries", [])
	print("[Mission] loaded %d missions" % _missions.size())


func mission_count() -> int:
	return _missions.size()


func mission_dict(mid: int) -> Dictionary:
	if mid < 0 or mid >= _missions.size(): return {}
	return _missions[mid]


func mission_name(mid: int) -> String:
	return str(mission_dict(mid).get("name", ""))


func mission_type_label(mid: int) -> String:
	var t = int(mission_dict(mid).get("mission_type", 255))
	return str(TYPE_LABELS.get(t, "?"))


func is_completed(mid: int) -> bool:
	return bool(_completed.get(mid, false))


## sub_idx 의 현재 진척값.
func get_progress(mid: int, sub_idx: int) -> int:
	var m: Dictionary = _progress.get(mid, {})
	return int(m.get(sub_idx, 0))


## 사람이 읽기 쉬운 진척 요약 (전체 sub_conditions / target_count 도달).
func progress_summary(mid: int) -> String:
	var rec = mission_dict(mid)
	if rec.is_empty(): return ""
	var subs: Array = rec.get("sub_conditions", [])
	var tgt_cnt = int(rec.get("target_count", 1))
	if tgt_cnt == 255: tgt_cnt = 1  # 255 = 단일 final_flag 모드
	var done := 0
	for i in subs.size():
		var sc: Dictionary = subs[i]
		if int(sc.get("sub_flag", 255)) == 255 and int(sc.get("slot", 255)) == 255:
			continue
		var cur = get_progress(mid, i)
		var tgt = int(sc.get("target_value", 0))
		if cur >= tgt: done += 1
	return "%d/%d 조건 달성" % [done, tgt_cnt]


## Generic 이벤트 — bump_progress(event_kind, key, amount). 매칭되는 mission_type 의
## sub_conditions 를 순회하며, sub_flag/slot 일치 시 current value 증가.
##
## key:
##  - monster_kill: monster_id
##  - item_obtained: (slot * 1000 + idx) 또는 그냥 idx
##  - refine_done/orb_combine/mix_done/playtime/money/quest_done: 무시 (any)
##
## amount: 증가량 (기본 1; money 의 경우 gold 양).
func bump_progress(event_kind: String, key: int = -1, amount: int = 1) -> void:
	var types: Array = EVENT_TO_MISSION_TYPES.get(event_kind, [])
	if types.is_empty(): return
	# Round 59: type=3 의 경우 sub_type 도 필터링 (정밀 매핑)
	var sub_types_filter: Array = EVENT_TO_SUB_TYPES.get(event_kind, [])
	for mid in _missions.size():
		if is_completed(mid): continue
		var rec: Dictionary = _missions[mid]
		var mtype = int(rec.get("mission_type", 255))
		if mtype not in types: continue
		# type=3 면 sub_type 도 매칭 (sub_types_filter 가 비어있으면 모두 허용)
		if mtype == 3 and not sub_types_filter.is_empty():
			var rec_sub = int(rec.get("sub_type", 0))
			if rec_sub not in sub_types_filter: continue
		var subs: Array = rec.get("sub_conditions", [])
		var changed := false
		for i in subs.size():
			var sc: Dictionary = subs[i]
			var sub_flag = int(sc.get("sub_flag", 255))
			var slot = int(sc.get("slot", 255))
			if sub_flag == 255 and slot == 255: continue
			var match := false
			match event_kind:
				EVENT_MONSTER_KILL:
					# type 0/1: sub_flag = monster_id
					if sub_flag == key: match = true
				EVENT_ITEM_OBTAINED:
					# type 2: slot 매칭 + sub_flag = item_idx
					# type 4: sub_type = category (slot 의미가 다름)
					var item_key = key % 1000
					var item_slot = key / 1000
					if mtype == 2:
						if slot == item_slot and sub_flag == item_key:
							match = true
					elif mtype == 4:
						# sub_type = category (무기/방어/장신구), key 는 slot
						if int(rec.get("sub_type", 0)) == item_slot:
							match = true
				_:
					# refine/orb/mix/playtime/money/quest — sub_flag 무시, 무조건 누적
					match = true
			if not match: continue
			var prev_progress: Dictionary = _progress.get(mid, {})
			var cur = int(prev_progress.get(i, 0))
			var tgt = int(sc.get("target_value", 0))
			if cur >= tgt: continue
			prev_progress[i] = min(cur + amount, tgt)
			_progress[mid] = prev_progress
			changed = true
		if changed:
			mission_progress_changed.emit(mid)
			_check_completion(mid)


## target_count 의 sub-condition 이 모두 충족되면 완료.
func _check_completion(mid: int) -> void:
	if is_completed(mid): return
	var rec: Dictionary = _missions[mid]
	var subs: Array = rec.get("sub_conditions", [])
	var tgt_cnt = int(rec.get("target_count", 1))
	if tgt_cnt == 255: tgt_cnt = 1
	var done := 0
	for i in subs.size():
		var sc: Dictionary = subs[i]
		if int(sc.get("sub_flag", 255)) == 255 and int(sc.get("slot", 255)) == 255:
			continue
		var cur = get_progress(mid, i)
		var tgt = int(sc.get("target_value", 0))
		if cur >= tgt: done += 1
	if done >= tgt_cnt:
		_completed[mid] = true
		mission_completed.emit(mid, mission_name(mid))


## Save / restore.
func to_save() -> Dictionary:
	return {"progress": _progress.duplicate(), "completed": _completed.duplicate()}


func from_save(data: Dictionary) -> void:
	_progress = data.get("progress", {}).duplicate()
	_completed = data.get("completed", {}).duplicate()
