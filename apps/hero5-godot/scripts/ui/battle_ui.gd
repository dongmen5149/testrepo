## 전투 UI — battle_system.gd 와 연결.
class_name BattleUI
extends CanvasLayer

signal battle_completed(victory: bool, exp: int, gold: int, items: Array)

const BattleSystem = preload("res://scripts/core/battle_system.gd")

@onready var bg: ColorRect = $BG
@onready var enemy_label: Label = $BG/Enemy
@onready var enemy_sprite: Sprite2D = $BG/EnemySprite
@onready var turn_indicator: Label = $BG/TurnIndicator
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


## Round 85: battle 진입 시 fade transition — 검정 페이드아웃 → battle data
## setup + visible=true → 페이드인. 사용자 시각적 신호로 turn-based 영역 진입.
##
## 이전 (R63-R84): visible=true instant 토글. 사용자가 갑작스럽게 battle UI 등장
## 으로 느끼는 disorientation 해소.
const SceneFaderRef = preload("res://scripts/ui/scene_fader.gd")

func start(monster_id: int, player_state: Dictionary) -> void:
	if visible: return   # Round 85: 이미 battle 중이면 무시 (중복 진입 방지)
	await SceneFaderRef.warp_fade(self, func():
			_setup_and_show(monster_id, player_state),
		0.25, 0.25)


## start() 의 mid-callback 으로 분리 — 검정 화면 동안 battle 데이터 setup 후 visible=true.
func _setup_and_show(monster_id: int, player_state: Dictionary) -> void:
	GameState.in_combat = true
	_battle = H5Battle.new()
	add_child(_battle)
	_battle.player_hp = int(player_state.get("hp", 100))
	_battle.player_max_hp = int(player_state.get("max_hp", 100))
	_battle.battle_started.connect(_on_started)
	_battle.battle_ended.connect(_on_ended)
	_battle.log_message.connect(_on_log)
	_battle.turn_changed.connect(_on_turn_changed)
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
	flee_btn.text = "도망 (%d%%)" % _battle.flee_chance()
	_set_buttons_enabled(true)


const DamagePopup = preload("res://scripts/ui/damage_popup.gd")
const EffectAnim = preload("res://scripts/ui/effect_anim.gd")
var _last_enemy_hp: int = 0
var _last_player_hp: int = 0


func _on_log(msg: String) -> void:
	log_box.append_text(msg + "\n")
	# 데미지 차이 popup + 이펙트
	if _battle.enemy_hp < _last_enemy_hp:
		var dmg = _last_enemy_hp - _battle.enemy_hp
		DamagePopup.spawn(bg, enemy_label.position + Vector2(160, 30),
			"-%d" % dmg, Color(1, 0.4, 0.2))
		# 이펙트: c/sp/imgcom/eff.mgr 첫 frame sequence
		var eff_dir = AssetLoader.sprite_dir("c/sp/imgcom/eff.mgr")
		if not eff_dir.is_empty() and enemy_sprite.texture:
			EffectAnim.spawn_at(bg, enemy_sprite.position, eff_dir, 12.0)
	if _battle.player_hp < _last_player_hp:
		var dmg = _last_player_hp - _battle.player_hp
		DamagePopup.spawn(bg, player_label.position + Vector2(160, 30),
			"-%d" % dmg, Color(1, 0.6, 0.6))
	_last_enemy_hp = _battle.enemy_hp
	_last_player_hp = _battle.player_hp
	enemy_hp.value = _battle.enemy_hp
	player_hp.value = _battle.player_hp


func _on_ended(victory: bool, exp_gain: int, gold_gain: int, items: Array) -> void:
	_set_buttons_enabled(false)
	if victory:
		await _show_victory_popup(exp_gain, gold_gain, items)
	else:
		await _show_defeat_popup()
	# Round 85: battle 종료 시 fade-out — 페이드아웃 → visible=false + cleanup → 페이드인.
	# 사용자 시각적 신호로 turn-based 영역 이탈 + map 으로 복귀.
	await SceneFaderRef.warp_fade(self, func():
			visible = false
			GameState.in_combat = false
			if _battle:
				_battle.queue_free()
				_battle = null,
		0.25, 0.25)
	battle_completed.emit(victory, exp_gain, gold_gain, items)


## 승리 popup — EXP/Gold/획득 아이템 요약 + 확인 버튼.
func _show_victory_popup(exp_gain: int, gold_gain: int, items: Array) -> void:
	var panel := Panel.new()
	panel.name = "ResultPanel"
	panel.position = Vector2(40, 120)
	panel.size = Vector2(240, 200)
	bg.add_child(panel)
	var title := Label.new()
	title.text = "승 리!"
	title.position = Vector2(0, 8)
	title.size = Vector2(240, 32)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", Color(1, 0.9, 0.4, 1))
	panel.add_child(title)
	var lines := PackedStringArray()
	lines.append("EXP +%d" % exp_gain)
	lines.append("Gold +%d" % gold_gain)
	if items.is_empty():
		lines.append("(획득 아이템 없음)")
	else:
		lines.append("획득 아이템:")
		for it in items:
			lines.append("  • " + str(it))
	var body := Label.new()
	body.text = "\n".join(lines)
	body.position = Vector2(16, 50)
	body.size = Vector2(208, 110)
	body.add_theme_font_size_override("font_size", 13)
	panel.add_child(body)
	var ok := Button.new()
	ok.text = "확인"
	ok.position = Vector2(80, 162)
	ok.size = Vector2(80, 28)
	panel.add_child(ok)
	# 확인 버튼 또는 4초 자동 닫힘
	var done := false
	ok.pressed.connect(func(): done = true)
	var t := 0.0
	while not done and t < 4.0:
		await get_tree().process_frame
		t += get_process_delta_time()
	panel.queue_free()


func _show_defeat_popup() -> void:
	var panel := Panel.new()
	panel.position = Vector2(40, 180)
	panel.size = Vector2(240, 100)
	bg.add_child(panel)
	var title := Label.new()
	title.text = "패 배..."
	title.position = Vector2(0, 16)
	title.size = Vector2(240, 32)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", Color(0.7, 0.3, 0.3, 1))
	panel.add_child(title)
	await get_tree().create_timer(1.5).timeout
	panel.queue_free()


func _do(action: int) -> void:
	if _battle: _battle.player_action(action)


func _on_turn_changed(turn: int, is_player: bool) -> void:
	if turn_indicator:
		var who = "플레이어" if is_player else _battle.enemy_name
		var color = Color(1, 0.9, 0.4, 1) if is_player else Color(1, 0.5, 0.5, 1)
		turn_indicator.text = "턴 %d — %s" % [turn, who]
		turn_indicator.add_theme_color_override("font_color", color)
	# 도주 % 미리보기
	if is_player and _battle:
		flee_btn.text = "도망 (%d%%)" % _battle.flee_chance()
	_set_buttons_enabled(is_player)


func _set_buttons_enabled(on: bool) -> void:
	attack_btn.disabled = not on
	skill_btn.disabled = not on
	defend_btn.disabled = not on
	flee_btn.disabled = not on
