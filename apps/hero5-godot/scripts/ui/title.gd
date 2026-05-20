## 타이틀 화면.
##
## Round 93: 인라인 slot 버튼 생성 + 우클릭 삭제 popup 제거 → R92 SaveListPanel
## 로 위임. Continue 버튼 = SaveListPanel 토글; slot_loaded 시그널 시 GameState
## 가 이미 로드된 상태이므로 SceneRouter.to_demo 직행 (quick_load 중복 없음).
## "저장 데이터 없음" fallback 만 SlotsLabel 유지.
extends Node2D

const SaveManager = preload("res://scripts/core/save_manager.gd")

@onready var logo: Sprite2D = $Logo
@onready var new_btn: Button = $UI/NewGameButton
@onready var cont_btn: Button = $UI/ContinueButton
@onready var slots: Label = $UI/SlotsLabel

var _save_list: CanvasLayer


func _ready() -> void:
	new_btn.pressed.connect(_on_new_game)
	cont_btn.pressed.connect(_on_continue)
	# Round 93: SaveListPanel 인스턴스 (Title 화면에서 Continue 시 띄움).
	_save_list = preload("res://scenes/save_list_panel.tscn").instantiate()
	add_child(_save_list)
	_save_list.slot_loaded.connect(_on_slot_loaded)
	_refresh_status()
	SceneFader.fade_in(self)
	# 로고: c/sp/imgcom/title.mgr 의 첫 frame
	var logo_dir = AssetLoader.sprite_dir("c/sp/imgcom/title.mgr")
	if not logo_dir.is_empty():
		var tex = AssetLoader.first_frame_of(logo_dir)
		if tex: logo.texture = tex
	# 타이틀 BGM (bgm_00 — 일반적으로 main theme)
	Audio.play_bgm(0)


func _on_new_game() -> void:
	# fresh state — clear GameState
	GameState.current_scene_id = 0
	GameState.map_id = 0
	GameState.player_x = 160
	GameState.player_y = 240
	GameState.hp = 100; GameState.max_hp = 100
	GameState.sp = 50; GameState.max_sp = 50
	GameState.level = 1; GameState.exp = 0
	GameState.gold = 1000
	GameState.inventory = []
	GameState.flags = {}
	SceneRouter.to_class_select(self)


func _on_continue() -> void:
	# Round 93: SaveListPanel 띄워 slot 선택. slot_loaded 시 _on_slot_loaded 로.
	_save_list.toggle()


func _on_slot_loaded(slot: int) -> void:
	# SaveListPanel 이 이미 GameState.quick_load 수행 — Title 은 demo 로 전환만.
	slots.text = "슬롯 %d 로드 중..." % slot
	SceneRouter.to_demo(self)


func _refresh_status() -> void:
	var ss := SaveManager.list_slots()
	if ss.is_empty():
		slots.text = "저장 데이터 없음 (New Game 만 가능)"
		cont_btn.disabled = true
	else:
		slots.text = "Continue → 슬롯 선택 (%d 슬롯 사용 중)" % ss.size()
		cont_btn.disabled = false


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_on_new_game()
