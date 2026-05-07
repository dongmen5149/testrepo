## 전투 UI — battle_system.gd 와 연결.
class_name BattleUI
extends CanvasLayer

signal battle_completed(victory: bool, exp: int, gold: int)

const BattleSystem = preload("res://scripts/core/battle_system.gd")

@onready var bg: ColorRect = $BG
@onready var enemy_label: Label = $BG/Enemy
@onready var enemy_hp: ProgressBar = $BG/EnemyHP
@onready var player_label: Label = $BG/Player
@onready var player_hp: ProgressBar = $BG/PlayerHP
@onready var log_box: RichTextLabel = $BG/Log
@onready var attack_btn: Button = $BG/ActionBox/Attack
@onready var skill_btn: Button = $BG/ActionBox/Skill
@onready var defend_btn: Button = $BG/ActionBox/Defend
@onready var flee_btn: Button = $BG/ActionBox/Flee

var _battle: H5Battle = null


func _ready() -> void:
	visible = false
	attack_btn.pressed.connect(func(): _do(H5Battle.Action.ATTACK))
	skill_btn.pressed.connect(func(): _do(H5Battle.Action.SKILL))
	defend_btn.pressed.connect(func(): _do(H5Battle.Action.DEFEND))
	flee_btn.pressed.connect(func(): _do(H5Battle.Action.FLEE))


func start(monster_id: int, player_state: Dictionary) -> void:
	_battle = H5Battle.new()
	add_child(_battle)
	_battle.player_hp = int(player_state.get("hp", 100))
	_battle.player_max_hp = int(player_state.get("max_hp", 100))
	_battle.battle_started.connect(_on_started)
	_battle.battle_ended.connect(_on_ended)
	_battle.log_message.connect(_on_log)
	_battle.start_battle(monster_id)
	visible = true


func _on_started(name: String) -> void:
	enemy_label.text = name
	enemy_hp.max_value = _battle.enemy_max_hp
	enemy_hp.value = _battle.enemy_hp
	player_hp.max_value = _battle.player_max_hp
	player_hp.value = _battle.player_hp
	log_box.text = ""
	# 스킬 버튼 라벨에 실제 첫 스킬 이름
	if _battle.skill_names.size() > 0:
		skill_btn.text = _battle.skill_names[0]
	_set_buttons_enabled(true)


func _on_log(msg: String) -> void:
	log_box.append_text(msg + "\n")
	enemy_hp.value = _battle.enemy_hp
	player_hp.value = _battle.player_hp


func _on_ended(victory: bool, exp: int, gold: int) -> void:
	_set_buttons_enabled(false)
	await get_tree().create_timer(1.5).timeout
	visible = false
	battle_completed.emit(victory, exp, gold)
	if _battle:
		_battle.queue_free()
		_battle = null


func _do(action: int) -> void:
	if _battle: _battle.player_action(action)


func _set_buttons_enabled(on: bool) -> void:
	attack_btn.disabled = not on
	skill_btn.disabled = not on
	defend_btn.disabled = not on
	flee_btn.disabled = not on
