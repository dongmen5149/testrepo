## 전투 UI — battle_system.gd 와 연결.
class_name BattleUI
extends CanvasLayer

signal battle_completed(victory: bool, exp: int, gold: int)

const BattleSystem = preload("res://scripts/core/battle_system.gd")

@onready var bg: ColorRect = $BG
@onready var enemy_label: Label = $BG/Enemy
@onready var enemy_sprite: Sprite2D = $BG/EnemySprite
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
	# 적 스프라이트 (enemy stats flags_a[0] 가 sprite_id 추정)
	_load_enemy_sprite(monster_id)


func _load_enemy_sprite(monster_id: int) -> void:
	var stats = GameData.enemy_stats(monster_id)
	if stats.is_empty():
		enemy_sprite.texture = null
		return
	var flags_a = stats.get("flags_a", [])
	if flags_a.is_empty(): return
	var sprite_id = int(flags_a[0])
	if sprite_id == 0xFF: return
	# img0..6 검색
	for cat in range(7):
		var dir := "res://assets/sprites/img%d/%03d" % [cat, sprite_id]
		if not DirAccess.dir_exists_absolute(dir): continue
		var d := DirAccess.open(dir)
		if d == null: continue
		d.list_dir_begin()
		var fname := d.get_next()
		while fname != "":
			if fname.begins_with("frame_00") and fname.ends_with(".png"):
				enemy_sprite.texture = load(dir + "/" + fname)
				return
			fname = d.get_next()
	enemy_sprite.texture = null


func _on_started(name: String) -> void:
	enemy_label.text = name
	enemy_hp.max_value = _battle.enemy_max_hp
	enemy_hp.value = _battle.enemy_hp
	player_hp.max_value = _battle.player_max_hp
	player_hp.value = _battle.player_hp
	_last_enemy_hp = _battle.enemy_hp
	_last_player_hp = _battle.player_hp
	log_box.text = ""
	# 스킬 버튼 라벨에 실제 첫 스킬 이름
	if _battle.skill_names.size() > 0:
		skill_btn.text = _battle.skill_names[0]
	_set_buttons_enabled(true)


const DamagePopup = preload("res://scripts/ui/damage_popup.gd")
var _last_enemy_hp: int = 0
var _last_player_hp: int = 0


func _on_log(msg: String) -> void:
	log_box.append_text(msg + "\n")
	# 데미지 차이 popup
	if _battle.enemy_hp < _last_enemy_hp:
		var dmg = _last_enemy_hp - _battle.enemy_hp
		DamagePopup.spawn(bg, enemy_label.position + Vector2(160, 30),
			"-%d" % dmg, Color(1, 0.4, 0.2))
	if _battle.player_hp < _last_player_hp:
		var dmg = _last_player_hp - _battle.player_hp
		DamagePopup.spawn(bg, player_label.position + Vector2(160, 30),
			"-%d" % dmg, Color(1, 0.6, 0.6))
	_last_enemy_hp = _battle.enemy_hp
	_last_player_hp = _battle.player_hp
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
