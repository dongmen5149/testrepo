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

# 클래스 + 능력치
var class_id: int = 0   # 0=워리어, 1=로그, 2=건슬링어, 3=나이트, 4=소서러
var stat_str: int = 12
var stat_dex: int = 8
var stat_int: int = 10
var stat_con: int = 6
var stat_points: int = 0   # 사용자 수동 분배 점수

# 해금된 스킬 (skill_id 리스트)
var unlocked_skills: Array[int] = [0]  # 첫 스킬 (basic attack) 시작부터
var inventory: Array = []
var flags: Dictionary = {}

# 장비 슬롯 — 각 값은 inventory 의 인덱스 (또는 -1 = 비어있음)
const SLOT_WEAPON := 0
const SLOT_ARMOR := 1
const SLOT_HELMET := 2
const SLOT_BOOTS := 3
const SLOT_ACC1 := 4
const SLOT_ACC2 := 5
const SLOT_COUNT := 6
var equipment: Array[int] = [-1, -1, -1, -1, -1, -1]

## 강화 상태 (Round 52). inventory 인덱스 → {refine_count, sub_count, locked}.
##
## 원본 EquipItemInfo +0x165/+0x166/+0x167 (Round 17/26) 매핑:
##   refine_count: 강화 단계 (0..10), ApplyItemRefine 성공/큰성공 시 +1
##   sub_count:    누적 강화 합산값 (V[187], refined_stat = base + sub_count)
##   locked:       lock 상태 (+0x167=1 이면 더 이상 강화 불가)
##
## 새 인벤토리 슬롯에는 entry 없음 = (0,0,false). items.json 의 record refine_count
## 와 별개 (csv 시점 값 vs runtime 값).
var refine_state: Dictionary = {}


## inv_idx 의 강화 상태 반환. 미설정 시 빈 dict default.
func get_refine(inv_idx: int) -> Dictionary:
	return refine_state.get(inv_idx, {"refine_count": 0, "sub_count": 0, "locked": false})


## inv_idx 의 강화 상태 갱신.
func set_refine(inv_idx: int, refine_count: int, sub_count: int, locked: bool = false) -> void:
	if inv_idx < 0 or inv_idx >= inventory.size(): return
	refine_state[inv_idx] = {
		"refine_count": clamp(refine_count, 0, 10),
		"sub_count": max(0, sub_count),
		"locked": locked,
	}
	state_changed.emit()


## inv_idx 의 강화 상태 제거 (인벤 아이템 제거 시 호출).
func clear_refine(inv_idx: int) -> void:
	refine_state.erase(inv_idx)


## 아이템을 슬롯에 장착. inventory 인덱스 사용.
func equip(slot: int, inv_idx: int) -> bool:
	if slot < 0 or slot >= SLOT_COUNT: return false
	if inv_idx < 0 or inv_idx >= inventory.size(): return false
	equipment[slot] = inv_idx
	state_changed.emit()
	return true


func unequip(slot: int) -> void:
	if slot < 0 or slot >= SLOT_COUNT: return
	equipment[slot] = -1
	state_changed.emit()


func equipped_item(slot: int) -> Variant:
	if slot < 0 or slot >= SLOT_COUNT: return null
	var idx = equipment[slot]
	if idx < 0 or idx >= inventory.size(): return null
	return inventory[idx]


## 장비 stat 합산. inventory 의 아이템명 → items.json 의 slot_N 에서
## 검색 → stats[7] (atk/def) 추출 + Round 52 강화 보너스 (sub_count).
##
## refined_stat = base_stat + sub_count (Round 26 의 Formula VM id=35/36 결과).
## weapon slot 은 ATK, 그 외 equip slot 은 DEF 로 누적.
func equipment_bonus() -> Dictionary:
	var bonus := {"attack": 0, "defense": 0}
	for slot in SLOT_COUNT:
		var item = equipped_item(slot)
		if item == null: continue
		var inv_idx: int = equipment[slot]
		var item_name := str(item)
		var info = GameData.item_lookup(item_name)
		# items.json 의 stat_a 를 우선 사용 (Round 26 의 의미 있는 stat) — 없으면 fallback to stats[7]
		var base_stat: int = int(info.get("stat_a", 0))
		if base_stat == 0:
			for item_slot in range(10):
				var arr = GameData.items_in_slot(item_slot)
				var idx = arr.find(item_name)
				if idx >= 0:
					var data = GameData.item_stat(item_slot, idx)
					base_stat = int(data.get("attack", 0))
					break
		# Round 52 강화 보너스
		var refine = get_refine(inv_idx)
		var refined = base_stat + int(refine.get("sub_count", 0))
		if slot == SLOT_WEAPON:
			bonus["attack"] += refined
		else:
			bonus["defense"] += refined
	return bonus


## 수동 stat 분배. 단, stat_points 점수가 있어야 가능.
func allocate_stat(stat_name: String, points: int = 1) -> bool:
	if stat_points < points: return false
	match stat_name:
		"str": stat_str += points
		"dex": stat_dex += points
		"int": stat_int += points
		"con":
			stat_con += points
			max_hp += points * 5
		_: return false
	stat_points -= points
	state_changed.emit()
	return true


## 캐릭터 총 ATK = base STR-derived + equipment bonus.
func total_attack() -> int:
	var base = stat_str * 2 + level * 3
	return base + int(equipment_bonus().get("attack", 0))


func total_defense() -> int:
	var base = stat_con + level * 2
	return base + int(equipment_bonus().get("defense", 0))

var verbose: bool = true

# 플레이 시간 추적
var play_time_sec: float = 0.0


var _regen_timer: float = 0.0
const REGEN_INTERVAL := 2.0  # 2초마다 회복
var in_combat: bool = false

var _auto_save_timer: float = 0.0
const AUTO_SAVE_INTERVAL := 60.0  # 60초마다 자동 저장


func _process(delta: float) -> void:
	play_time_sec += delta
	# 비전투 시 HP/SP 자동 회복
	if not in_combat:
		_regen_timer += delta
		if _regen_timer >= REGEN_INTERVAL:
			_regen_timer = 0.0
			var hp_regen := max(1, max_hp / 50)   # 2%/2초
			var sp_regen := max(1, max_sp / 30)
			var changed := false
			if hp < max_hp:
				hp = min(max_hp, hp + hp_regen)
				changed = true
			if sp < max_sp:
				sp = min(max_sp, sp + sp_regen)
				changed = true
			if changed: state_changed.emit()
	# 자동 저장 (60초마다, 비전투 시)
	if not in_combat:
		_auto_save_timer += delta
		if _auto_save_timer >= AUTO_SAVE_INTERVAL:
			_auto_save_timer = 0.0
			SaveManager.auto_save(to_save_dict())


func to_save_dict() -> Dictionary:
	return {
		"scene_id": current_scene_id,
		"map_id": map_id,
		"play_time_sec": int(play_time_sec),
		"player_x": player_x, "player_y": player_y, "player_dir": player_dir,
		"class_id": class_id,
		"hp": hp, "max_hp": max_hp,
		"sp": sp, "max_sp": max_sp,
		"level": level, "exp": exp, "gold": gold,
		"stat_str": stat_str, "stat_dex": stat_dex,
		"stat_int": stat_int, "stat_con": stat_con,
		"inventory": inventory,
		"equipment": equipment,
		"unlocked_skills": unlocked_skills,
		"flags": flags,
		"quest": Quest.to_save() if Quest else {},
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
signal level_up(new_level: int, gained_skills: Array)

func add_battle_reward(exp_gain: int, gold_gain: int) -> void:
	exp += exp_gain
	gold += gold_gain
	while exp >= level * 100:
		exp -= level * 100
		level += 1
		# 절반은 자동 분배, 절반은 수동 (3 ~ 5 점)
		_apply_levelup_stats()
		stat_points += 3
		max_hp += 10 + stat_con
		hp = max_hp
		max_sp += 5 + stat_int / 2
		sp = max_sp
		# 스킬 해금: lvl 5/10/15/20/25 마다 새 스킬
		var newly_unlocked: Array = []
		for tier in [5, 10, 15, 20, 25, 30, 35, 40]:
			if level == tier:
				var skill_idx = unlocked_skills.size()
				if skill_idx < 43:  # 클래스당 43 스킬
					unlocked_skills.append(skill_idx)
					newly_unlocked.append(skill_idx)
		level_up.emit(level, newly_unlocked)
	state_changed.emit()


func _apply_levelup_stats() -> void:
	# 클래스별 분포: 워리어 STR>INT>DEX>CON, 로그 DEX>CON, ...
	match class_id:
		0:  # 워리어
			stat_str += 2; stat_int += 1; stat_dex += 1
		1:  # 로그
			stat_dex += 2; stat_con += 2
		2:  # 건슬링어
			stat_dex += 2; stat_str += 1; stat_int += 1
		3:  # 나이트
			stat_str += 1; stat_int += 2; stat_dex += 1
		4:  # 소서러
			stat_int += 2; stat_con += 2
		_:
			stat_str += 1; stat_dex += 1; stat_int += 1; stat_con += 1
