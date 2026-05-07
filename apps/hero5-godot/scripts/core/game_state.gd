## 게임 전역 상태 (싱글톤). save_manager 와 양방향 sync.
extends Node

const SaveManager = preload("res://scripts/core/save_manager.gd")

signal state_changed

# 현재 맵/시나리오
var current_scene_id: int = 0
var current_episode: int = -1
var current_stage: int = -1
var map_id: int = 0

# 플레이어 상태
var player_x: int = 0
var player_y: int = 0
var player_dir: int = 0
var hp: int = 100
var max_hp: int = 100
var sp: int = 50
var max_sp: int = 50
var level: int = 1
var exp: int = 0
var gold: int = 1000
var inventory: Array = []
var flags: Dictionary = {}

var verbose: bool = true


func to_save_dict() -> Dictionary:
	return {
		"scene_id": current_scene_id,
		"map_id": map_id,
		"player_x": player_x, "player_y": player_y, "player_dir": player_dir,
		"hp": hp, "max_hp": max_hp,
		"sp": sp, "max_sp": max_sp,
		"level": level, "exp": exp, "gold": gold,
		"inventory": inventory,
		"flags": flags,
	}


func apply_save(data: Dictionary) -> void:
	current_scene_id = int(data.get("scene_id", 0))
	map_id = int(data.get("map_id", 0))
	var p = data.get("player", data)  # support both nested + flat
	player_x = int(p.get("x", p.get("player_x", 0)))
	player_y = int(p.get("y", p.get("player_y", 0)))
	player_dir = int(p.get("dir", p.get("player_dir", 0)))
	hp = int(p.get("hp", 100))
	max_hp = int(p.get("max_hp", 100))
	sp = int(p.get("sp", 50))
	max_sp = int(p.get("max_sp", 50))
	level = int(p.get("level", 1))
	exp = int(p.get("exp", 0))
	gold = int(p.get("gold", 1000))
	inventory = data.get("inventory", [])
	flags = data.get("flags", {})
	state_changed.emit()


func quick_save(slot: int = 0) -> bool:
	return SaveManager.save(slot, to_save_dict())


func quick_load(slot: int = 0) -> bool:
	var data = SaveManager.load_slot(slot)
	if data.is_empty(): return false
	apply_save(data)
	return true


## 전투 결과 적용.
func add_battle_reward(exp_gain: int, gold_gain: int) -> void:
	exp += exp_gain
	gold += gold_gain
	# 간이 레벨업: 100 EXP/level
	while exp >= level * 100:
		exp -= level * 100
		level += 1
		max_hp += 10; hp = max_hp
		max_sp += 5; sp = max_sp
	state_changed.emit()
