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

# Round 48: Monster AI VM runtime. enemy 가 AI def 가 있는 경우만 활성.
var _ai_runtime = null   # MonsterAI.MonsterAIState | null


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
	# Monster AI runtime 초기화 (Round 48). monster_id 가 ai_type_id 와 다르면
	# enemy_*.dat 의 Monster+0x22e 를 GameData 에서 가져와야 하지만 임시로
	# monster_id 자체를 ai_type_id 로 사용.
	_ai_runtime = MonsterAI.create_runtime(self, monster_id) if MonsterAI else null
	battle_started.emit(enemy_name)
	log_message.emit("%s 와의 전투 시작! (HP %d)" % [enemy_name, enemy_hp])


## Monster AI 가 다음 turn 에 사용할 skill 추천. 없으면 -1.
##
## battle_system 은 turn-based 추상화라서 매 enemy turn 시작 시 AI VM 을
## "한 action 진행" 시켜서 skill_src_30a 또는 skill_id 를 읽어 사용.
##
## Round 50: Ai_Action 13 sub-state precise dispatch 가 통합되면서 cast 가 발생할 때
## host.ai_cast_skill() 가 호출되어 `_ai_pending_skill_id` 에 기록됨. 이를 우선 반환.
func _ai_pick_skill() -> int:
	if _ai_runtime == null: return -1
	_ai_pending_skill_id = -1
	# 트리거 검사 → action 전환 시도
	MonsterAI.step_trigger_list(_ai_runtime)
	# action stream 1 step (필요 시 여러 step 까지 loop 가능)
	for _i in range(8):
		var alive = MonsterAI.step_action_list(_ai_runtime)
		if not alive: break
	# Ai_Action sub-state 가 cast → host.ai_cast_skill 통해 기록한 값 우선
	MonsterAI.process(_ai_runtime)
	if _ai_pending_skill_id > 0: return _ai_pending_skill_id
	# fallback: opcode 9 (NEXT_SKILL) > opcode 4 (SKILL_SET) > -1
	if _ai_runtime.skill_src_30a > 0: return _ai_runtime.skill_src_30a
	if _ai_runtime.skill_id > 0: return _ai_runtime.skill_id
	return -1


# === MonsterAI host CHAR interface (Round 50, R66 명세 강화) ===
##
## monster_ai.gd 의 Ai_Action 13 sub-state 가 호출하는 CHAR 인터페이스.
##
## 시스템은 두 host 경로 사용 (둘 다 dead code 아님):
##
## | host             | 사용 경로                  | 호출 특성                       |
## |------------------|----------------------------|---------------------------------|
## | battle_system    | turn-based 전투 (B / NPC)  | 위치 개념 없음 — 시야/거리 default |
## | character.gd     | real-time AI tick (R62 G)  | map 좌표 기반 정확한 값 (R61)   |
##
## battle_system 의 stub 은 turn-based 추상화의 **합리적 default**:
##   - 거리/방향 개념 없음 → distance=0, dir=0 (항상 hero 와 같은 cell)
##   - 시야 trigger → 항상 true (시야 진입 1회 trigger 가 즉시 활성)
##   - motion 항상 idle → 매 turn AI VM 이 다음 action 진행
##   - cooldown 실제 동작 (R66 추가): `_cooldowns` dict + is_able_skill 검사
##
## character.gd (R61) 의 의미:
##   - fast_distance_to_hero: tile Chebyshev 거리
##   - get_dir/set_dir: map dir enum
##   - get_motion: HOST_MOTION_* 의 실시간 anim state

## Ai_Action 의 _do_cast 가 호출. 다음 enemy turn 에 쓸 skill_id 기록.
var _ai_pending_skill_id: int = -1

func ai_cast_skill(skill_id: int) -> void:
	_ai_pending_skill_id = skill_id

func is_die() -> bool:
	return enemy_hp <= 0

## turn-based: idle 항상 (motion 0). 매 turn AI VM 이 walk/cast 진행 가능.
func get_motion() -> int:
	return 0

## turn-based: dead 또는 stunned 시 공격 불가.
func is_attack_able() -> bool:
	return enemy_hp > 0 and not is_stunned()

## turn-based: skill_id > 0 + cooldown 만료. R66 으로 _cooldowns 실 연동.
func is_able_skill(skill_id: int) -> bool:
	if skill_id <= 0: return false
	return int(_cooldowns.get(skill_id, 0)) <= 0

func get_dir() -> int:
	return 0

func set_dir(_d: int) -> void:
	pass

func hero_turn_direction() -> void:
	pass

## turn-based: monster 는 항상 hero 와 같은 cell 에 있다고 가정 (시야 안).
func fast_distance_to_hero() -> int:
	return 0

func set_attack_motion(skill_id: int) -> void:
	# state 4/6 = motion+dir lookup 후 cast. ai_cast_skill 가 후속으로 호출됨.
	_ai_pending_skill_id = skill_id

## turn-based: R66 으로 실 동작. skill_id 별 FRAME_PER_TURN frame 까지 lock.
func set_cool_time(skill_id: int) -> void:
	if skill_id > 0:
		_cooldowns[skill_id] = FRAME_PER_TURN

func skill_end() -> void:
	pass

func ai_check_irect_hit(_range_val: int) -> bool:
	# turn-based: 항상 hit (range 검사 생략)
	return true

func ai_check_visibility(_irect_idx: int) -> bool:
	# turn-based: 항상 hero 가시 (시야 진입 1회 trigger 만)
	return true

func ai_all_dead() -> bool:
	return enemy_hp <= 0

func ai_tutorial_flag(_idx: int) -> bool:
	return false

## turn-based: stun 상태 — 기본 false. 추후 enemy debuff 시스템에서 set.
func is_stunned() -> bool:
	return false


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


## class_stats.json 을 캐싱 (5 클래스 base stat).
static var _class_stats_cache: Array = []

func _class_stats() -> Array:
	if _class_stats_cache.is_empty():
		var p := "res://assets/gamedata/class_stats.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			var data = JSON.parse_string(f.get_as_text())
			if typeof(data) == TYPE_ARRAY:
				_class_stats_cache = data
	return _class_stats_cache


## class_id 의 unk0..unk5 (atk_growth_coef + 5 secondary stat base) 를 dict 로 반환.
## Round 7 LoadResClassInfo disasm 로 확정된 sequential 6 short 영역.
## 실패 시 워리어 (idx=0) default fallback.
func _class_secondary_base(class_id: int) -> Dictionary:
	var stats := _class_stats()
	if stats.is_empty(): return {"unk0": 1000, "unk1": 0, "unk2": 0, "unk3": 0, "unk4": 0, "unk5": 0}
	var idx: int = clamp(class_id, 0, stats.size() - 1)
	var rec: Dictionary = stats[idx]
	return rec


## GameState 의 player stats 를 Formula VM ctx 형식으로 변환.
##
## offset → 의미 매핑은 .so writer 분석 (h5_find_gv_writers.py) 으로 확정:
##   0x22d (V[58]) = level                    — calc_pl id=18 max_exp 공식 검증
##   0x230        = player_class               — ChangeHeroClass writer
##   0x236..0x23c (V[60..63]) = base str/dex/int/con — calc_pl id=20..23 패턴
##   0x248 (V[69]) = SP                        — HERO::IncreaseSP writer
##   0x24a (V[70]) = CP                        — HERO::IncreaseCP writer
##   0x278..0x282 (V[111..116]) = atk_growth + 5 secondary base — LoadResClassInfo
##   0x298..0x29e (V[118..121]) = bonus str/dex/int/con — calc_pl id=20..23 패턴
##   0x2a0..0x2a8 (V[122..126]) = 5 buff stat slot — Round 9 ApplyBuildupEffect
##                                  jumptable entry type 30..36 (V add s16)
##   0x2aa (V[127]) = defense_reduction_percent — Round 8 calc_pl 공식
##   0x2ac (V[128]) = atk_percent_bonus         — Round 8 id=24 공식
##   0x2ae..0x2b6 (V[129..133]) = 5 secondary stat bonus — Round 7 id=25..29 짝
## 미확정: V[112..116] 5 secondary stat 의 한국어 라벨 (hit/avoid/crit/block/speed
## 중 무엇) — UI status menu 함수 한글 string 매핑 RE 필요.
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
	ctx["570"] = GameState.stat_con      # 0x23a  V[62]  base_con (Round 11 정정 — 이전 int)
	ctx["572"] = GameState.stat_int      # 0x23c  V[63]  base_int (Round 11 정정 — 이전 con)
	ctx["584"] = GameState.sp            # 0x248  V[69]  SP (cur)
	ctx["586"] = 0                       # 0x24a  V[70]  CP (cur)  — GameState에 없음, 0
	# bonus stats (장비/buff): GameState 에 분리 저장 없음 → total - base 로 계산하거나 0
	ctx["664"] = max(0, atk - GameState.stat_str)    # 0x298  V[118] bonus_str (대용)
	ctx["666"] = max(0, def_v - GameState.stat_dex)  # 0x29a  V[119] bonus_dex (대용)
	ctx["668"] = 0                                    # 0x29c  V[120] bonus_con (Round 11 정정 — buildup "건강+#1")
	ctx["670"] = 0                                    # 0x29e  V[121] bonus_int (Round 11 정정 — buildup "정신+#1")
	# === Round 7+9: LoadResClassInfo + ApplyBuildupEffect disasm 으로 정확화 ===
	# V[111] (0x278) = atk_growth_per_(level*2+str) coefficient
	#   id=24 공식: V[5] + V[111] * ((V[58]*2) + V[154]) → V[111] 가 multiplier.
	# V[112..116] = 클래스별 secondary stat base 5개 (LoadResClassInfo seq).
	#   class_stats.json 의 unk0 = atk_growth, unk1..unk5 = secondary base.
	var class_id: int = GameState.class_id if "class_id" in GameState else 0
	var class_rec: Dictionary = _class_secondary_base(class_id)
	ctx["632"] = int(class_rec.get("unk0", 1000))         # 0x278  V[111] atk growth coef
	ctx["634"] = int(class_rec.get("unk1", 0))            # 0x27a  V[112] base 근접명중 (Round 11)
	ctx["636"] = int(class_rec.get("unk2", 0))            # 0x27c  V[113] base 장거리명중
	ctx["638"] = int(class_rec.get("unk3", 0))            # 0x27e  V[114] base 회피
	ctx["640"] = int(class_rec.get("unk4", 0))            # 0x280  V[115] base 방패방어
	ctx["642"] = int(class_rec.get("unk5", 0))            # 0x282  V[116] base 크리티컬
	# === Round 9+12: V[122..126] = 5 buff stat slot (라벨 확정) ===
	# ApplyBuildupEffect jumptable entry type 30/31/32/34/36 → 0x2a0..0x2a8 에 V add s16.
	# Round 12: csv 매핑 + formula 패턴 (100±V[xxx])/100 으로 정확 라벨 식별.
	# InitStatusComputation 가 0 reset. Godot 측에는 buff state 미구현 → 0 default.
	ctx["672"] = 0                                        # 0x2a0  V[122] EXP %bonus (csv 0x1d)
	ctx["674"] = 0                                        # 0x2a2  V[123] SP소모% 감소 (csv 0x1e)
	ctx["676"] = 0                                        # 0x2a4  V[124] CP충전LV (csv 0x1f)
	ctx["678"] = 0                                        # 0x2a6  V[125] 쿨타임 감소% (csv 0x21)
	ctx["680"] = 0                                        # 0x2a8  V[126] 포션효과 % (csv 0x23)
	# Round 8: V[127] (0x2aa) = def_reduction_percent (s8), V[128] (0x2ac) = atk%bonus.
	ctx["682"] = 0                                        # 0x2aa  V[127] def_reduction%
	ctx["684"] = 0                                        # 0x2ac  V[128] atk_percent_bonus
	# V[129..133] = 5 secondary stat bonus (calc_pl id=25..29 의 두 번째 항).
	# Round 11: csv 0x14..0x19 매핑으로 라벨 확정 (근접명중/장거리명중/회피/방패방어/크리티컬 bonus).
	# 장비/buff 의 secondary stat 보너스 — 현재 0 (장비 분석 미완).
	ctx["686"] = 0                                        # 0x2ae  V[129] 근접명중 bonus
	ctx["688"] = 0                                        # 0x2b0  V[130] 장거리명중 bonus
	ctx["690"] = 0                                        # 0x2b2  V[131] 회피 bonus
	ctx["692"] = 0                                        # 0x2b4  V[132] 방패방어 bonus
	ctx["694"] = 0                                        # 0x2b6  V[133] 크리티컬 bonus
	# 주의: 0x294/0x295/0x296 (ApplyBuildupEffect 가 store 하는 active buff descriptor) 는
	# Formula VM 의 var_dict 에 없는 HERO 구조체 필드 (UI 아이콘 표시용).
	# V[151..155] (0x2de..0x2e6) — formula 의존 stat (id=0 / id=24 cross-check).
	# Round 12 정정: V[152]=DEX 잘못 → 둘 다 magic stat (INT). element 1/2 짝.
	ctx["734"] = GameState.stat_int                       # 0x2de  V[151] magic stat 1 (id=4 element 1)
	ctx["736"] = GameState.stat_int                       # 0x2e0  V[152] magic stat 2 (id=5 element 2)
	ctx["738"] = GameState.stat_con                       # 0x2e2  V[153] con  (id=0 MaxHP 10*V[153])
	ctx["740"] = GameState.stat_str                       # 0x2e4  V[154] str  (id=24 ATK V[58]*2+V[154])
	ctx["742"] = GameState.max_sp                         # 0x2e6  V[155] max_sp 확정
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
