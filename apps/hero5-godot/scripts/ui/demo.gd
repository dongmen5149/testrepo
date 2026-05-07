## 통합 데모: Map + Character + Interpreter (basic).
##
## ① Map 렌더러로 mapID 의 4-layer 합성
## ② Character 가 .scn 헤더의 startX/Y/dir 위치에 스폰
## ③ Interpreter 가 .scn body 의 첫 몇 opcode 를 실행 (현재는 console log)
extends Node2D

const MapRenderer = preload("res://scripts/core/map_renderer.gd")
const Character = preload("res://scripts/core/character.gd")
const Interp = preload("res://scripts/core/interpreter.gd")

@onready var status: Label = $UI/Status

var _map: Node2D
var _hero: Sprite2D
var _scene_index: Array = []
var _scene_idx: int = 0
var _dialog: CanvasLayer
var _interp: H5Interpreter
var _status: CanvasLayer
var _battle_ui: CanvasLayer


func _ready() -> void:
	_map = MapRenderer.new()
	add_child(_map)
	_load_scene_index()
	_hero = _spawn_hero()
	add_child(_hero)
	_dialog = preload("res://scenes/dialog_box.tscn").instantiate()
	add_child(_dialog)
	_status = preload("res://scenes/status_panel.tscn").instantiate()
	add_child(_status)
	# 실제 게임 데이터에서 인벤토리 placeholder 생성
	var inv: Array = []
	# 각 item slot 에서 첫 아이템
	for i in range(4):
		var arr = GameData.items_in_slot(i)
		if arr.size() > 0:
			inv.append(arr[0] if arr[0] else "(item_%02d)" % i)
	# drop table 에서 5개 추가
	var drops = GameData.drop_table()
	for i in range(5):
		if i < drops.size() and drops[i]:
			inv.append("[drop] " + drops[i])
	if inv.is_empty():
		inv = ["회복약", "마나약", "한손검", "가죽갑옷"]
	# GameState 싱글톤 사용. inv 가 비어있으면 placeholder.
	if GameState.inventory.is_empty():
		GameState.inventory = inv
	_status.set_state(GameState.to_save_dict())
	GameState.state_changed.connect(func(): _status.set_state(GameState.to_save_dict()))
	# 전투 결과 → GameState 적용
	if _battle_ui.has_signal("battle_completed"):
		_battle_ui.battle_completed.connect(func(victory, exp, gold):
			if victory:
				GameState.add_battle_reward(exp, gold))
	_battle_ui = preload("res://scenes/battle.tscn").instantiate()
	add_child(_battle_ui)
	_interp = H5Interpreter.new()
	# Dialog 관련 opcode → dialog box 연결 (opcode_table.tsv)
	#   0x35 (53) Event_SituateBallon (2B)
	#   0x39 (57) Event_SituateDialogText (4B)
	#   0x3b (59) Event_SituateNarration (3B)
	#   0x3e (62) Event_SituatePopup (0B)
	_interp.set_handler(0x39, _on_dialog_text)
	_interp.set_handler(0x35, _on_dialog_text)
	_interp.set_handler(0x3b, _on_narration)
	_apply_scene()


func _on_dialog_text(args: PackedByteArray) -> void:
	# args[0]=string_idx? args[1]=face_idx? args[2..3] reserved
	# 실제 의미는 Event_SituateDialogText 본문 추가 분석 필요.
	# 데모용으로 placeholder 한글 출력.
	var sample := ["대화 테스트입니다.", "여행을 시작합시다.",
			"마을 사람들에게 도움을 청해보세요."]
	var idx = args[0] % sample.size() if args.size() > 0 else 0
	_dialog.show_dialog("NPC", sample[idx])


func _on_narration(args: PackedByteArray) -> void:
	_dialog.show_dialog("나레이션", "...")


func _npc_talk() -> void:
	# 가장 가까운 NPC 와 대화 (시뮬레이션). npc_table 의 첫 valid 사용.
	var npc_data = _load_npc_table()
	if npc_data.is_empty():
		_dialog.show_dialog("System", "NPC 데이터 없음")
		return
	# scene_idx 따라 다른 NPC 선택
	var npc = npc_data[_scene_idx % npc_data.size()]
	var char_names = GameData.char_names()
	var name = "NPC #%d" % npc.get("idx", 0)
	# stat1 (dialog id) → ingame_text lookup 시도
	var dlg_id = int(npc.get("stat1", 0))
	if dlg_id != 65535:
		var msg = GameData.ingame_text(dlg_id)
		if msg.is_empty():
			msg = "안녕하시오, 모험가여."
		_dialog.show_dialog(name, msg)
	else:
		_dialog.show_dialog(name, "...")


func _load_npc_table() -> Array:
	var p := "res://assets/gamedata/npc_table.json"
	if not FileAccess.file_exists(p): return []
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	return data if data is Array else []


func _load_scene_index() -> void:
	var p := "res://assets/scenes/index.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Array: _scene_index = data


func _spawn_hero() -> Sprite2D:
	var c = Character.new()
	# 적당한 캐릭터 sprite 디렉토리 — 첫 sprites/img0/0NN
	c.sprite_dir = "res://assets/sprites/img0/000"
	c.position = Vector2(160, 240)
	return c


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_M:
				_map.map_id = (_map.map_id + 1) % 200
				_update_status()
			KEY_N:
				if _scene_index.size() > 0:
					_scene_idx = (_scene_idx + 1) % _scene_index.size()
					_apply_scene()
			KEY_T:
				# T: dialog 테스트
				_on_dialog_text(PackedByteArray([_scene_idx % 3]))
			KEY_E:
				# E: NPC 인터랙션 (npc_table.json 의 stat1 을 dialogID 로 사용)
				_npc_talk()
			KEY_ESCAPE, KEY_I:
				# ESC/I: 상태창 토글
				_status.toggle()
			KEY_F5:
				# F5: 빠른 저장 (slot 0) — GameState 통해
				GameState.current_scene_id = _scene_idx
				GameState.map_id = _map.map_id
				GameState.player_x = int(_hero.position.x)
				GameState.player_y = int(_hero.position.y)
				GameState.quick_save(0)
				_dialog.show_dialog("System", "저장됨 (slot 0)")
			KEY_C:
				# C: collision 디버그 토글
				_map.show_collision_debug = not _map.show_collision_debug
			KEY_B:
				# B: 랜덤 전투 시작
				_battle_ui.start(_scene_idx % 5, {"hp": 100, "max_hp": 100})
			KEY_F9:
				# F9: 빠른 로드
				if GameState.quick_load(0):
					_scene_idx = GameState.current_scene_id
					_apply_scene()
					_dialog.show_dialog("System", "불러옴 (slot 0)")


func _apply_scene() -> void:
	if _scene_index.size() == 0: return
	var s = _scene_index[_scene_idx]
	_map.map_id = int(s.get("mapID", 0))
	_hero.position = Vector2(
		int(s.get("startX", 160)),
		int(s.get("startY", 240)))
	_update_status()
	_run_intro(s)


func _update_status() -> void:
	if _scene_index.size() == 0:
		status.text = "mapID=%d  (no scene index)" % _map.map_id
		return
	var s = _scene_index[_scene_idx]
	status.text = "scene #%d: %s\nmapID=%d  body=%dB" % [
		_scene_idx, s.get("name", "?"), _map.map_id, s.get("body_len", 0)]


func _run_intro(scene_meta: Dictionary) -> void:
	# 첫 진입 시 Interpreter 가 처음 5개 opcode 만 console 에 dump
	var interp = Interp.new()
	interp.run_intro(scene_meta)
