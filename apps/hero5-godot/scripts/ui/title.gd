## 타이틀 화면.
extends Node2D

const SaveManager = preload("res://scripts/core/save_manager.gd")

@onready var logo: Sprite2D = $Logo
@onready var new_btn: Button = $UI/NewGameButton
@onready var cont_btn: Button = $UI/ContinueButton
@onready var slots: Label = $UI/SlotsLabel


func _ready() -> void:
	new_btn.pressed.connect(_on_new_game)
	cont_btn.pressed.connect(_on_continue)
	_refresh_slots()
	SceneFader.fade_in(self)
	# 로고: c/sp/imgcom/title.mgr 의 첫 frame
	var logo_dir = AssetLoader.sprite_dir("c/sp/imgcom/title.mgr")
	if not logo_dir.is_empty():
		var tex = AssetLoader.first_frame_of(logo_dir)
		if tex: logo.texture = tex
	# 타이틀 BGM (bgm_00 — 일반적으로 main theme)
	Audio.play_bgm(0)
	pass  # logo loading moved to title.gd _ready (sprite_index 기반)


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


var _selected_slot: int = -1


func _on_continue() -> void:
	# 가장 최근 저장 자동 선택 (없으면 0)
	var slot = _selected_slot if _selected_slot >= 0 else 0
	if not SceneRouter.to_demo_with_load(self, slot):
		slots.text = "슬롯 %d 비어있음" % slot


func _refresh_slots() -> void:
	# 기존 slot 버튼 제거
	for c in $UI.get_children():
		if c.name.begins_with("Slot_"):
			c.queue_free()
	var ss := SaveManager.list_slots()
	if ss.is_empty():
		slots.text = "저장 데이터 없음 (New Game 만 가능)"
		cont_btn.disabled = true
		return
	cont_btn.disabled = false
	slots.text = "슬롯 선택 (또는 Continue):"
	# 각 slot 버튼 생성
	for s in ss:
		var slot = int(s.get("slot", 0))
		var p = s.get("player", {})
		var btn := Button.new()
		btn.name = "Slot_%d" % slot
		var pt = int(s.get("play_time_sec", 0))
		var hh = pt / 3600; var mm = (pt % 3600) / 60
		btn.text = "[%d] Lv.%d cls%d %dG inv%d  %02d:%02d" % [
			slot, int(p.get("level", 1)),
			int(p.get("class_id", 0)),
			int(p.get("gold", 0)),
			int(s.get("inventory_count", 0)),
			hh, mm]
		btn.position = Vector2(8, 380 + slot * 22)
		btn.size = Vector2(304, 20)
		btn.add_theme_font_size_override("font_size", 10)
		btn.pressed.connect(func(): _on_slot_selected(slot))
		# 우클릭 / Shift+클릭 = 삭제 확인
		btn.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed:
				if ev.button_index == MOUSE_BUTTON_RIGHT or ev.shift_pressed:
					_confirm_delete(slot))
		$UI.add_child(btn)


func _on_slot_selected(slot: int) -> void:
	_selected_slot = slot
	SceneRouter.to_demo_with_load(self, slot)


func _confirm_delete(slot: int) -> void:
	# 간이 confirmation (popup)
	var popup := AcceptDialog.new()
	popup.dialog_text = "슬롯 %d 의 저장 데이터를 삭제하시겠습니까?" % slot
	popup.title = "슬롯 삭제"
	popup.add_cancel_button("취소")
	popup.confirmed.connect(func():
		SaveManager.delete_slot(slot)
		_refresh_slots()
		popup.queue_free())
	popup.canceled.connect(func(): popup.queue_free())
	add_child(popup)
	popup.popup_centered()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_on_new_game()
