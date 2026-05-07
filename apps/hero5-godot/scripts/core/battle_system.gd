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
signal battle_ended(victory: bool, exp: int, gold: int)
signal log_message(msg: String)

enum Action { ATTACK, SKILL, DEFEND, FLEE }

var player_hp: int = 100
var player_max_hp: int = 100
var enemy_name: String = ""
var enemy_hp: int = 0
var enemy_max_hp: int = 0
var enemy_attack: int = 10


var skill_names: Array = []


func start_battle(monster_id: int = 0) -> void:
	# enemy_table.json 에서 실제 stats
	var stats = GameData.enemy_stats(monster_id)
	enemy_name = "Monster #%d" % monster_id
	if stats.has("hp") and int(stats["hp"]) != 65535:
		enemy_max_hp = int(stats["hp"])
		enemy_attack = max(5, int(stats.get("mp", 10)) / 4)
	else:
		enemy_max_hp = 50 + monster_id * 10
	enemy_hp = enemy_max_hp
	# Player class 의 skill list 로드 (class_id 0 = 워리어)
	skill_names = GameData.skills_for_class(0)
	battle_started.emit(enemy_name)
	log_message.emit("%s 와의 전투 시작! (HP %d)" % [enemy_name, enemy_hp])


func player_action(action: Action, skill_id: int = 0) -> void:
	match action:
		Action.ATTACK:
			var dmg := 8 + randi() % 8
			enemy_hp = max(0, enemy_hp - dmg)
			log_message.emit("플레이어 → %s 에게 %d 피해" % [enemy_name, dmg])
			if enemy_hp == 0:
				_finish(true)
				return
		Action.SKILL:
			var dmg := 15 + randi() % 10
			enemy_hp = max(0, enemy_hp - dmg)
			var skill_name := "스킬"
			if skill_id >= 0 and skill_id < skill_names.size():
				skill_name = skill_names[skill_id]
			elif not skill_names.is_empty():
				skill_name = skill_names[randi() % min(8, skill_names.size())]
			log_message.emit("[%s]! %d 피해" % [skill_name, dmg])
			if enemy_hp == 0:
				_finish(true)
				return
		Action.DEFEND:
			log_message.emit("방어 자세")
		Action.FLEE:
			if randi() % 100 < 70:
				log_message.emit("도망 성공")
				_finish(false)
				return
			else:
				log_message.emit("도망 실패!")
	# 적 턴
	_enemy_turn(action == Action.DEFEND)


func _enemy_turn(player_defending: bool) -> void:
	var dmg := enemy_attack + randi() % 5
	if player_defending: dmg = dmg / 2
	player_hp = max(0, player_hp - dmg)
	log_message.emit("%s → 플레이어에게 %d 피해" % [enemy_name, dmg])
	if player_hp == 0:
		log_message.emit("플레이어 패배...")
		_finish(false)


func _finish(victory: bool) -> void:
	if victory:
		var exp := 10 + randi() % 20
		var gold := 5 + randi() % 50
		log_message.emit("승리! EXP +%d  Gold +%d" % [exp, gold])
		battle_ended.emit(true, exp, gold)
	else:
		battle_ended.emit(false, 0, 0)
