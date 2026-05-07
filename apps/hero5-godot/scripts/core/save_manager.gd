## 세이브/로드 (평문 JSON).
##
## 원본은 DES 암호화 (`StaticUtil::SaveEncryptFile` / `LoadDecryptFile`,
## key=`__DES_KEY__`) 를 썼지만 리메이크에서는 평문 JSON 으로 단순화.
## 사용자 데이터 디렉토리: `user://hero5_save_<slot>.json`
class_name H5SaveManager
extends RefCounted

const SAVE_VERSION := 1
const MAX_SLOTS := 8
const AUTO_SLOT := 7   # slot 7 은 자동 저장 전용


static func save_path(slot: int) -> String:
	return "user://hero5_save_%d.json" % slot


static func make_payload(state: Dictionary) -> Dictionary:
	var inv: Array = state.get("inventory", [])
	return {
		"version": SAVE_VERSION,
		"timestamp": Time.get_datetime_string_from_system(),
		"play_time_sec": int(state.get("play_time_sec", 0)),
		"scene_id": state.get("scene_id", 0),
		"map_id": state.get("map_id", 0),
		"player": {
			"x": state.get("player_x", 0),
			"y": state.get("player_y", 0),
			"dir": state.get("player_dir", 0),
			"class_id": state.get("class_id", 0),
			"hp": state.get("hp", 100),
			"max_hp": state.get("max_hp", 100),
			"sp": state.get("sp", 100),
			"max_sp": state.get("max_sp", 100),
			"level": state.get("level", 1),
			"exp": state.get("exp", 0),
			"gold": state.get("gold", 0),
			"str": state.get("stat_str", 0),
			"dex": state.get("stat_dex", 0),
			"int": state.get("stat_int", 0),
			"con": state.get("stat_con", 0),
		},
		"inventory": inv,
		"inventory_count": inv.size(),
		"equipment": state.get("equipment", []),
		"unlocked_skills": state.get("unlocked_skills", []),
		"flags": state.get("flags", {}),
		"quest": state.get("quest", {}),
	}


static func save(slot: int, state: Dictionary) -> bool:
	if slot < 0 or slot >= MAX_SLOTS:
		push_error("invalid save slot: %d" % slot)
		return false
	var payload := make_payload(state)
	var f := FileAccess.open(save_path(slot), FileAccess.WRITE)
	if f == null:
		push_error("cannot open save file for writing")
		return false
	f.store_string(JSON.stringify(payload, "  "))
	return true


static func load_slot(slot: int) -> Dictionary:
	var p := save_path(slot)
	if not FileAccess.file_exists(p):
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if not data is Dictionary:
		return {}
	if int(data.get("version", 0)) != SAVE_VERSION:
		push_warning("save version mismatch (slot %d): %s" % [slot, data.get("version")])
	return data


static func list_slots() -> Array:
	var out: Array = []
	for i in MAX_SLOTS:
		var p := save_path(i)
		if FileAccess.file_exists(p):
			var data = load_slot(i)
			out.append({
				"slot": i,
				"timestamp": data.get("timestamp", ""),
				"play_time_sec": data.get("play_time_sec", 0),
				"scene_id": data.get("scene_id", 0),
				"player": data.get("player", {}),
				"inventory_count": data.get("inventory_count", 0),
			})
	return out


## 자동 저장 (전용 slot 7) — 일정 간격으로 호출.
static func auto_save(state: Dictionary) -> bool:
	return save(AUTO_SLOT, state)


## 가장 오래된 slot (timestamp 기준) 찾기.
static func oldest_slot() -> int:
	var oldest_time = ""
	var oldest_idx = -1
	for i in MAX_SLOTS:
		var p := save_path(i)
		if not FileAccess.file_exists(p): return i  # 빈 슬롯 우선
		var data = load_slot(i)
		var ts = data.get("timestamp", "")
		if oldest_idx < 0 or ts < oldest_time:
			oldest_time = ts; oldest_idx = i
	return max(0, oldest_idx)


static func delete_slot(slot: int) -> bool:
	var p := save_path(slot)
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
		return true
	return false
