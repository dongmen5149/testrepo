## Game Over scene (Round 82).
##
## Hero 사망 시 Demo 에서 자동 전환 (SceneRouter.to_game_over). 사용자에게
## Continue (slot 0 자동 로드 → Demo 복귀) / Title (Give up) 선택지 제공.
##
## 이전: hero HP=0 시 demo.gd 가 silent quick_load(0) 로 즉시 복원 → 사용자가
## "왜 갑자기 살아났는지" 모름. 본 scene 으로 명시적 흐름.
extends Control

const SaveManager = preload("res://scripts/core/save_manager.gd")


func _ready() -> void:
	# 반투명 검정 배경 + Game Over 텍스트 + 2 버튼
	var bg := ColorRect.new()
	bg.color = Color(0, 0, 0, 0.95)
	var size := get_viewport().get_visible_rect().size
	bg.size = size
	add_child(bg)

	var title := Label.new()
	title.text = "Game Over"
	title.add_theme_font_size_override("font_size", 36)
	title.add_theme_color_override("font_color", Color(1, 0.3, 0.3, 1))
	title.size = Vector2(size.x, 60)
	title.position = Vector2(0, size.y * 0.25)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(title)

	# 사유 표시 (SceneRouter 가 set)
	var reason := SceneRouter.last_game_over_reason()
	if reason.is_empty():
		reason = "쓰러졌습니다"
	var reason_lbl := Label.new()
	reason_lbl.text = reason
	reason_lbl.add_theme_font_size_override("font_size", 14)
	reason_lbl.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9, 1))
	reason_lbl.size = Vector2(size.x, 28)
	reason_lbl.position = Vector2(0, size.y * 0.40)
	reason_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(reason_lbl)

	# Continue 버튼
	var cont_btn := Button.new()
	cont_btn.text = "Continue (slot 0)"
	cont_btn.size = Vector2(200, 40)
	cont_btn.position = Vector2(size.x * 0.5 - 100, size.y * 0.55)
	cont_btn.pressed.connect(_on_continue)
	add_child(cont_btn)

	# Title 버튼
	var title_btn := Button.new()
	title_btn.text = "Title (Give up)"
	title_btn.size = Vector2(200, 40)
	title_btn.position = Vector2(size.x * 0.5 - 100, size.y * 0.55 + 50)
	title_btn.pressed.connect(_on_title)
	add_child(title_btn)

	# Slot 정보 (현재 slot 0 의 상태 미리보기)
	var slots := SaveManager.list_slots()
	if slots.is_empty():
		cont_btn.disabled = true
		cont_btn.text = "Continue (저장 없음)"
	else:
		var slot0 := _find_slot(slots, 0)
		if not slot0.is_empty():
			var p: Dictionary = slot0.get("player", {})
			var info := "Lv.%d cls%d %dG" % [
				int(p.get("level", 1)),
				int(p.get("class_id", 0)),
				int(p.get("gold", 0))]
			var info_lbl := Label.new()
			info_lbl.text = info
			info_lbl.add_theme_font_size_override("font_size", 11)
			info_lbl.add_theme_color_override("font_color", Color(0.7, 0.8, 1, 1))
			info_lbl.size = Vector2(size.x, 18)
			info_lbl.position = Vector2(0, size.y * 0.55 + 96)
			info_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			add_child(info_lbl)

	SceneFader.fade_in(self)
	SceneRouter.notify_ready()


func _find_slot(slots: Array, want: int) -> Dictionary:
	for s in slots:
		if int(s.get("slot", -1)) == want:
			return s
	return {}


func _on_continue() -> void:
	if not SceneRouter.to_demo_with_load(self, 0):
		# 로드 실패 → Title 로
		SceneRouter.to_title(self)


func _on_title() -> void:
	SceneRouter.to_title(self)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		_on_continue()
	elif event.is_action_pressed("ui_cancel"):
		_on_title()
