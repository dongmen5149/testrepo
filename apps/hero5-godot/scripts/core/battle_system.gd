## 전투 시스템 골격.
##
## 원본 BATTLER 클래스 (BATTLER::InitColorChar, InitAddEffectValue 등 참조)
## 의 액션 RPG 전투를 단순화 — 4 종 액션 (공격/스킬/방어/도망).
##
## 실제 데미지 계산은 enemy_g.dat / skill_NN.dat 의 stats 참조 (extra_hex
## binary 디코딩 후속 작업).
class_name H5Battle
extends Node

signal battle_started(enemy_name: String)
signal battle_ended(victory: bool, exp: int, gold: int, items: Array)
signal log_message(msg: String)

enum Action { ATTACK, SKILL, DEFEND, FLEE }

var player_hp: int = 100
var player_max_hp: int = 100
var enemy_name: String = ""
var enemy_hp: int = 0
var enemy_max_hp: int = 0
var enemy_attack: int = 10
var enemy_def: int = 0


## 65535 = sentinel (게임이 사용 안 함). 그 외 0 < v < 65535 면 사용, 아니면 default.
func _stat_or(stats: Dictionary, key: String, default: int) -> int:
	if not stats.has(key): return default
	var v = int(stats[key])
	if v <= 0 or v >= 65535: return default
	return v


var skill_names: Array = []
var player_mp: int = 50
var player_max_mp: int = 50

# 턴 진행
var turn_count: int = 1
var is_player_turn: bool = true
signal turn_changed(turn: int, is_player: bool)

# skill_id → frames-until-usable
var _cooldowns: Dictionary = {}

const FRAME_PER_TURN := 1   # 1 turn = 1 second equiv (간소화)


func start_battle(monster_id: int = 0) -> void:
	_monster_id = monster_id
	turn_count = 1
	is_player_turn = true
	# enemy_table.json 에서 실제 stats (.so disasm 검증된 layout)
	var stats = GameData.enemy_stats(monster_id)
	enemy_name = "Monster #%d" % monster_id
	enemy_max_hp = _stat_or(stats, "hp", 50 + monster_id * 10)
	enemy_attack = _stat_or(stats, "atk", max(5, monster_id / 2 + 6))
	enemy_def = _stat_or(stats, "def", 0)
	enemy_hp = enemy_max_hp
	# Player class 의 skill list 로드 (class_id 0 = 워리어)
	skill_names = GameData.skills_for_class(0)
	battle_started.emit(enemy_name)
	log_message.emit("%s 와의 전투 시작! (HP %d)" % [enemy_name, enemy_hp])


func player_action(action: Action, skill_id: int = 0) -> void:
	match action:
		Action.ATTACK:
			var atk = max(8, GameState.total_attack())
			var raw_dmg := atk + randi() % 8
			var dmg = max(1, raw_dmg - enemy_def / 2)
			enemy_hp = max(0, enemy_hp - dmg)
			log_message.emit("플레이어 → %s 에게 %d 피해 (ATK %d, 적 DEF %d)" % [
				enemy_name, dmg, atk, enemy_def])
			if enemy_hp == 0:
				_finish(true)
				return
		Action.SKILL:
			# cooldown / MP 체크
			if _cooldowns.get(skill_id, 0) > 0:
				log_message.emit("재사용 대기 중 (%d턴 남음)" % _cooldowns[skill_id])
				return
			var skill_data = _skill_data(skill_id)
			var mp_cost = int(skill_data.get("mp_cost", 0))
			if player_mp < mp_cost:
				log_message.emit("MP 부족 (%d 필요)" % mp_cost)
				return
			player_mp -= mp_cost
			# damage 계수: skill 의 stat[5] 가 % (없으면 100%)
			var dmg_pct = int(skill_data.get("damage_pct", 150))
			var base_atk = 10 + (skill_id % 5)
			var dmg := base_atk * dmg_pct / 100 + randi() % 5
			enemy_hp = max(0, enemy_hp - dmg)
			var skill_name = skill_data.get("name", "스킬")
			# cooldown 적용
			var cd = int(skill_data.get("cooldown", 0))
			if cd > 0: _cooldowns[skill_id] = cd
			log_message.emit("[%s]! %d 피해 (MP -%d)" % [skill_name, dmg, mp_cost])
			if enemy_hp == 0:
				_finish(true)
				return
		Action.DEFEND:
			log_message.emit("방어 자세")
		Action.FLEE:
			var rate = flee_chance()
			if randi() % 100 < rate:
				log_message.emit("도망 성공 (%d%%)" % rate)
				_finish(false)
				return
			else:
				log_message.emit("도망 실패! (%d%%)" % rate)
	# 적 턴
	_enemy_turn(action == Action.DEFEND)


func _enemy_turn(player_defending: bool) -> void:
	is_player_turn = false
	turn_changed.emit(turn_count, false)
	var raw_dmg := enemy_attack + randi() % 5
	if player_defending: raw_dmg = raw_dmg / 2
	# 방어력 차감
	var def = GameState.total_defense()
	var dmg = max(1, raw_dmg - def / 2)
	player_hp = max(0, player_hp - dmg)
	log_message.emit("%s → 플레이어에게 %d 피해" % [enemy_name, dmg])
	# 모든 cooldown 1 감소
	for k in _cooldowns.keys():
		_cooldowns[k] = max(0, _cooldowns[k] - 1)
	if player_hp == 0:
		log_message.emit("플레이어 패배...")
		_finish(false)
		return
	turn_count += 1
	is_player_turn = true
	turn_changed.emit(turn_count, true)


## 도주 성공률: HP 비율 + DEX + 턴 수 기반.
##   기본 50%, HP 낮을수록 +, DEX 높을수록 +, 턴 길수록 +. 최대 95%.
func flee_chance() -> int:
	var hp_ratio = float(player_hp) / max(1, player_max_hp)
	var base = 50
	if hp_ratio < 0.3: base += 25
	elif hp_ratio < 0.6: base += 10
	base += min(20, GameState.stat_dex)
	base += min(15, turn_count * 3)
	return clamp(base, 30, 95)


## skill_id → {name, mp_cost, cooldown, damage_pct} 메타.
func _skill_data(skill_id: int) -> Dictionary:
	# 직접 skills.json 에서 stats_u16 읽음 (class_0 임시)
	if skill_id < 0 or skill_id >= skill_names.size():
		return {"name": "?", "mp_cost": 0, "cooldown": 0, "damage_pct": 100}
	var name = skill_names[skill_id]
	# stats[9] = cooldown(초), stats[5] = damage % (관습)
	# 실제 skill 의 stat 추출 — GameData 의 _skills_cache 통해
	var sk_arr = GameData._skills_cache.get("class_0", [])
	if skill_id < sk_arr.size():
		var stats: Array = sk_arr[skill_id].get("stats_u16", [])
		var mp = stats[7] if stats.size() > 7 else 0
		var cd = stats[9] if stats.size() > 9 else 0
		var dpct = stats[5] if stats.size() > 5 else 100
		return {
			"name": name,
			"mp_cost": min(int(mp), 30),
			"cooldown": min(int(cd), 5),
			"damage_pct": clamp(int(dpct), 50, 300),
		}
	return {"name": name, "mp_cost": 5, "cooldown": 1, "damage_pct": 150}


var _monster_id: int = 0


func _finish(victory: bool) -> void:
	if victory:
		var stats = GameData.enemy_stats(_monster_id)
		var exp_g = _stat_or(stats, "exp", 10 + randi() % 20)
		var gold_g = _stat_or(stats, "gold", 5 + randi() % 50)
		var drops := _roll_drops()
		log_message.emit("승리! EXP +%d  Gold +%d" % [exp_g, gold_g])
		Quest.on_enemy_killed(_monster_id)
		battle_ended.emit(true, exp_g, gold_g, drops)
	else:
		battle_ended.emit(false, 0, 0, [])


## 25% 확률로 drop_table 에서 1 ~ 2 개 아이템 결정.
func _roll_drops() -> Array:
	if randi() % 100 >= 25: return []
	var table = GameData.drop_table()
	if table.is_empty(): return []
	var n = 1 + (randi() % 2)
	var out: Array = []
	for i in n:
		var pick = table[randi() % table.size()]
		if pick and not out.has(pick):
			out.append(pick)
	return out
