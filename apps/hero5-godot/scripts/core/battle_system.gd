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
			# Formula VM id=0 (calc_pl[0]) 가 player attack base damage 공식.
			# clamp((V[2]+(32*V[58])+10*V[153]) * (100+V[20]) / 100, 1, 30000)
			# 변수가 정확히 매핑되지 않은 경우 임시 공식으로 fallback.
			var dmg := _calc_player_damage(0, _enemy_ctx())
			if dmg <= 0:
				# Fallback (FormulaVM lookup 미완 또는 0 반환 시)
				var atk = max(8, GameState.total_attack())
				dmg = max(1, atk + randi() % 8 - enemy_def / 2)
			enemy_hp = max(0, enemy_hp - dmg)
			log_message.emit("플레이어 → %s 에게 %d 피해 [F:0]" % [enemy_name, dmg])
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
			# 스킬 공식: calc_sk[skill_id] (id 2000+skill_id), 평가 결과가 데미지.
			var formula_id := 2000 + skill_id
			var dmg := _calc_player_damage(formula_id, _enemy_ctx(), skill_data)
			if dmg <= 0:
				# Fallback (FormulaVM 평가 0 시 임시 공식)
				var dmg_pct = int(skill_data.get("damage_pct", 150))
				var base_atk = 10 + (skill_id % 5)
				dmg = base_atk * dmg_pct / 100 + randi() % 5
			enemy_hp = max(0, enemy_hp - dmg)
			var skill_name = skill_data.get("name", "스킬")
			# cooldown 적용
			var cd = int(skill_data.get("cooldown", 0))
			if cd > 0: _cooldowns[skill_id] = cd
			log_message.emit("[%s]! %d 피해 (MP -%d) [F:%d]" % [skill_name, dmg, mp_cost, formula_id])
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
	# Enemy 데미지: calc_en[0] = id 1000 으로 시도. 미구현 시 임시 공식.
	var dmg := _calc_enemy_damage(1000)
	if dmg <= 0:
		var raw := enemy_attack + randi() % 5
		if player_defending: raw = raw / 2
		var def_v = GameState.total_defense() if GameState.has_method("total_defense") else 0
		dmg = max(1, raw - def_v / 2)
	elif player_defending:
		dmg = dmg / 2
	player_hp = max(0, player_hp - dmg)
	log_message.emit("%s → 플레이어에게 %d 피해 [F:1000]" % [enemy_name, dmg])
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


## Enemy 데미지 공식 평가 (calc_en).
##
## defender = player ctx (적이 플레이어를 공격하므로), skill = enemy stats.
func _calc_enemy_damage(formula_id: int) -> int:
	var fvm := get_node_or_null("/root/FormulaVM")
	if fvm == null:
		return 0
	var ctx := {
		"defender": _player_ctx(),
		"player": _enemy_player_ctx(),
		"skill": {"stats_u16": [enemy_attack, enemy_def, 0, 0, 0, 100]},
		"item": {},
	}
	return int(fvm.calc(formula_id, ctx))


## Enemy 의 상태를 "player" ctx 형식으로 변환 (대칭적 호출).
func _enemy_player_ctx() -> Dictionary:
	return {
		"557": enemy_attack,
		"632": enemy_attack,
		"634": enemy_def,
		"atk": enemy_attack,
		"def": enemy_def,
	}


## Enemy 컨텍스트 — defender 로 Formula VM 에 전달.
func _enemy_ctx() -> Dictionary:
	return {
		"hp": enemy_hp,
		"max_hp": enemy_max_hp,
		"atk": enemy_attack,
		"def": enemy_def,
	}


## Formula VM 호출 wrapper. formula_id 의 결과를 정수로 받음.
##
## ctx 구성:
##   - skill: skill_data (Dictionary, stats_u16 포함)
##   - defender: enemy ctx
##   - item: equipped weapon stats (있으면)
##   - player: GameState 의 stat 매핑
func _calc_player_damage(formula_id: int, defender_ctx: Dictionary, skill_data: Dictionary = {}) -> int:
	var fvm := get_node_or_null("/root/FormulaVM")
	if fvm == null:
		return 0
	var ctx := {
		"defender": defender_ctx,
		"player": _player_ctx(),
		"skill": skill_data,
		"item": _equipped_weapon_ctx(),
	}
	return int(fvm.calc(formula_id, ctx))


## GameState 의 player stats 를 Formula VM ctx 형식으로 변환.
##
## offset → 의미 매핑은 .so writer 분석 (h5_find_gv_writers.py) 으로 확정:
##   0x22d (V[58]) = level                    — calc_pl id=18 max_exp 공식 검증
##   0x230        = player_class               — ChangeHeroClass writer
##   0x236..0x23c (V[60..63]) = base str/dex/int/con — calc_pl id=20..23 패턴
##   0x248 (V[69]) = SP                        — HERO::IncreaseSP writer
##   0x24a (V[70]) = CP                        — HERO::IncreaseCP writer
##   0x278..0x282 (V[111..116]) = 클래스 base 계수  — HERO::LoadResClassInfo writer
##   0x298..0x29e (V[118..121]) = bonus str/dex/int/con — calc_pl id=20..23 패턴
## 미확정: V[111..116]의 6개 클래스 계수 (atk/def/hit/avoid 등) 의미 — calc_pl
## formula 별 사용에서 추론은 가능하나 정확한 라벨은 후속 RE 필요.
func _player_ctx() -> Dictionary:
	var atk: int = GameState.total_attack() if GameState.has_method("total_attack") else 10
	var def_v: int = GameState.total_defense() if GameState.has_method("total_defense") else 5
	var ctx: Dictionary = {
		"hp": GameState.hp,
		"max_hp": GameState.max_hp,
		"sp": GameState.sp,
		"max_sp": GameState.max_sp,
		"level": GameState.level,
		"str": GameState.stat_str,
		"dex": GameState.stat_dex,
		"int": GameState.stat_int,
		"con": GameState.stat_con,
		"atk": atk,
		"def": def_v,
	}
	# === 확정 매핑 (writer 분석 + calc_pl 공식 cross-check) ===
	ctx["557"] = GameState.level         # 0x22d  V[58]  level (확정 — id=18 max_exp 공식)
	ctx["566"] = GameState.stat_str      # 0x236  V[60]  base_str
	ctx["568"] = GameState.stat_dex      # 0x238  V[61]  base_dex
	ctx["570"] = GameState.stat_int      # 0x23a  V[62]  base_int
	ctx["572"] = GameState.stat_con      # 0x23c  V[63]  base_con
	ctx["584"] = GameState.sp            # 0x248  V[69]  SP (cur)
	ctx["586"] = 0                       # 0x24a  V[70]  CP (cur)  — GameState에 없음, 0
	# bonus stats (장비/buff): GameState 에 분리 저장 없음 → total - base 로 계산하거나 0
	ctx["664"] = max(0, atk - GameState.stat_str)    # 0x298  V[118] bonus_str (대용)
	ctx["666"] = max(0, def_v - GameState.stat_dex)  # 0x29a  V[119] bonus_dex (대용)
	ctx["668"] = 0                                    # 0x29c  V[120] bonus_int
	ctx["670"] = 0                                    # 0x29e  V[121] bonus_con
	# === 추정 매핑 (calc_pl 공식 입력) — 클래스 base 계수 (LoadResClassInfo writer) ===
	# V[111] (0x278) = atk_per_level coefficient (id=4 ATK 식에서 V[111]*level 형태로 사용)
	ctx["632"] = max(1, atk / max(1, GameState.level))  # rough: avg atk per level
	ctx["634"] = max(1, def_v / max(1, GameState.level))  # 0x27a  V[112] def coef
	ctx["636"] = ctx["hp"]                                # 0x27c  V[113] (TouchPressed 등에서 set — UI? hp 임시)
	ctx["638"] = ctx["max_hp"]                            # 0x27e  V[114] max_hp 추정
	ctx["640"] = ctx["sp"]                                # 0x280  V[115] sp 추정
	ctx["642"] = ctx["max_sp"]                            # 0x282  V[116] max_sp 추정
	# 음수 패널티 var_id (formula_vm.gd 가 V[248,249] 를 -50 으로 처리, 248/249 는 직접 매핑 불요)
	return ctx


## 장착된 무기 → item ctx (var_id 168..182 lookup 용).
func _equipped_weapon_ctx() -> Dictionary:
	var weapon = GameState.equipped_item(GameState.SLOT_WEAPON)
	if weapon == null: return {}
	# weapon 은 inventory 의 item 이름 (str). items.json 에서 stats 검색.
	var item_name := str(weapon)
	# GameData.item_stat 은 dict 또는 비어있는 값을 반환할 수 있음
	var atk: int = 0
	var def_v: int = 0
	if GameData.has_method("item_stat"):
		atk = int(GameData.call("item_stat", item_name, "atk"))
		def_v = int(GameData.call("item_stat", item_name, "def"))
	return {
		"atk_value": atk,
		"def_value": def_v,
		"stats": [atk, def_v, 0, 0],
	}


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
