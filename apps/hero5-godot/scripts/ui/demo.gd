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
var _shop: CanvasLayer
var _quest_panel: CanvasLayer
var _hud: CanvasLayer
var _settings: CanvasLayer


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
	# 레벨업 popup
	GameState.level_up.connect(_on_level_up)
	# warp 감지: hero 가 이동하면 check_warp
	if _hero.has_signal("moved"):
		_hero.moved.connect(_on_hero_moved)
	_map.warp_triggered.connect(_on_warp)
	# 아이템 사용 알림
	if _status.has_signal("item_used"):
		_status.item_used.connect(func(name):
			_dialog.show_dialog("System", "%s 사용 (HP +30)" % name))
	_battle_ui = preload("res://scenes/battle.tscn").instantiate()
	add_child(_battle_ui)
	_shop = preload("res://scenes/shop_panel.tscn").instantiate()
	add_child(_shop)
	_quest_panel = preload("res://scenes/quest_panel.tscn").instantiate()
	add_child(_quest_panel)
	_hud = preload("res://scenes/hud.tscn").instantiate()
	add_child(_hud)
	var minimap = preload("res://scenes/minimap.tscn").instantiate()
	add_child(minimap)
	minimap.bind(_map, _hero)
	_settings = preload("res://scenes/settings_panel.tscn").instantiate()
	add_child(_settings)
	_interp = H5Interpreter.new()
	# Dialog 관련 opcode → dialog box 연결 (opcode_table.tsv)
	#   0x35 (53) Event_SituateBallon (2B)
	#   0x39 (57) Event_SituateDialogText (4B)
	#   0x3b (59) Event_SituateNarration (3B)
	#   0x3e (62) Event_SituatePopup (0B)
	_interp.set_handler(0x39, _on_dialog_text)
	_interp.set_handler(0x35, _on_dialog_text)
	_interp.set_handler(0x3b, _on_narration)
	# Event_Scene_ChangeBgm = idx 67 in opcode_table
	_interp.set_handler(0x43, _on_change_bgm)
	# Quest opcodes: SituateQuestPopup=53→0x35? actually 0x35 already=Ballon.
	# QuestStatus=51, QuestSwitch=58, QuestBoss=49, QuestTimer=50, QuestQSwitch=66.
	_interp.set_handler(51, func(args): _on_quest_status(args))
	# 시작 BGM
	Audio.play_bgm(0)
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
	var npc_data = _load_npc_table()
	if npc_data.is_empty():
		_dialog.show_dialog("System", "NPC 데이터 없음")
		return
	# 가까운 NPC 자동 감지 (스폰됐으면 좌표 기반)
	var nearest = _map.nearest_npc(int(_hero.position.x), int(_hero.position.y), 2)
	var npc: Dictionary
	if nearest >= 0 and nearest < npc_data.size():
		npc = npc_data[nearest]
	else:
		npc = npc_data[_scene_idx % npc_data.size()]
	var name = "NPC #%d" % npc.get("idx", 0)
	# 선택지 데모: 매 3번째 NPC 는 선택지 표시
	if _scene_idx % 3 == 0:
		_dialog.show_choices(name, "어떤 일이지?", ["퀘스트 받기", "상점 보기", "그냥 인사"])
		# 한 번만 connect
		if not _dialog.choice_selected.is_connected(_on_npc_choice):
			_dialog.choice_selected.connect(_on_npc_choice)
		return
	# quest_text 우선 시도, 없으면 ingame_text fallback
	var npc_idx = int(npc.get("idx", 0))
	var msg = GameData.quest_dialogue(npc_idx, _scene_idx % 3)
	if msg.is_empty():
		var dlg_id = int(npc.get("stat1", 0))
		if dlg_id != 65535:
			msg = GameData.ingame_text(dlg_id)
	if msg.is_empty():
		msg = "안녕하시오, 모험가여."
	_dialog.show_dialog(name, msg)


func _on_npc_choice(idx: int) -> void:
	match idx:
		0:
			Quest.start(0)  # 첫 quest = "여행자"
			_dialog.show_dialog("System", "퀘스트 시작: " + Quest.quest_name(0))
		1:
			_dialog.show_dialog("상인", "오늘은 좋은 물건 들어왔소. 다음에 상점 시스템에서 만나죠.")
		2:
			_dialog.show_dialog("NPC", "여행 잘 다녀오시오.")


func _on_change_bgm(args: PackedByteArray) -> void:
	if args.size() >= 1:
		Audio.play_bgm(args[0])


var _steps_since_battle: int = 0
const ENCOUNTER_MIN_STEPS := 25
const ENCOUNTER_CHANCE := 0.10  # 10% per step after min


func _on_hero_moved(new_pos: Vector2) -> void:
	_map.check_warp(int(new_pos.x), int(new_pos.y))
	# 인카운터 체크 (HUD 등 UI 가 열려있으면 skip)
	if _battle_ui.visible or _shop.visible or _quest_panel.visible:
		return
	if GameState.in_combat: return
	_steps_since_battle += 1
	if _steps_since_battle >= ENCOUNTER_MIN_STEPS and randf() < ENCOUNTER_CHANCE:
		_steps_since_battle = 0
		_trigger_random_encounter()


func _trigger_random_encounter() -> void:
	# 맵 mapID 따라 적 풀 (간이): 0..74 valid 중 무작위
	var monster_id = randi() % 75
	_battle_ui.start(monster_id, {
		"hp": GameState.hp, "max_hp": GameState.max_hp,
	})


func _on_warp(target_scene: int) -> void:
	if target_scene < 0 or target_scene >= _scene_index.size(): return
	_scene_idx = target_scene
	_apply_scene()
	_dialog.show_dialog("System", "이동: scene #%d" % target_scene)


func _on_level_up(new_level: int, gained_skills: Array) -> void:
	# 큰 popup + 데미지 popup 으로 시각 강조
	var DamagePopup = preload("res://scripts/ui/damage_popup.gd")
	DamagePopup.spawn(self, _hero.position + Vector2(-30, -30),
		"LEVEL UP! → %d" % new_level, Color(1, 0.9, 0.3))
	var msg := "Lv. %d 달성!" % new_level
	if not gained_skills.is_empty():
		var skill_arr = GameData.skills_for_class(GameState.class_id)
		var names: Array = []
		for sid in gained_skills:
			if sid < skill_arr.size():
				names.append(skill_arr[sid])
		msg += "\n해금된 스킬: " + ", ".join(names)
	_dialog.show_dialog("System", msg)


func _on_quest_status(args: PackedByteArray) -> void:
	if args.size() >= 2:
		var qid = args[0]
		var status = args[1]
		if status == Quest.STATUS_ACTIVE:
			Quest.start(qid)
			_dialog.show_dialog("System", "퀘스트 시작: " + Quest.quest_name(qid))
		elif status == Quest.STATUS_COMPLETED:
			Quest.complete(qid)
			_dialog.show_dialog("System", "퀘스트 완료: " + Quest.quest_name(qid))


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
			KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
				# 1-8: 빠른 저장 슬롯 (Shift+숫자 = 로드)
				var slot = event.keycode - KEY_1
				if Input.is_key_pressed(KEY_SHIFT):
					if GameState.quick_load(slot):
						_scene_idx = GameState.current_scene_id
						_apply_scene()
						_dialog.show_dialog("System", "슬롯 %d 로드" % slot)
				else:
					GameState.current_scene_id = _scene_idx
					GameState.player_x = int(_hero.position.x)
					GameState.player_y = int(_hero.position.y)
					GameState.quick_save(slot)
					_dialog.show_dialog("System", "슬롯 %d 저장" % slot)
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
			KEY_V:
				# V: tile attribute 디버그 토글
				_map.show_tile_attr_debug = not _map.show_tile_attr_debug
			KEY_P:
				# P: NPC 마커 스폰 (npc_table 좌표 기반)
				_map.spawn_npcs(_map, 12)
			KEY_S:
				# S: 상점 열기
				_shop.open_shop(0)
			KEY_Q:
				# Q: 퀘스트 패널 토글
				_quest_panel.toggle()
			KEY_X:
				# X: 설정 토글
				_settings.toggle()
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
	# Scene 의 startX/Y 는 tile coord (8-bit, 보통). pixel 변환.
	# 0xFF (255) 는 "유지" 또는 "기본 위치" 의미 — 화면 중앙 placeholder.
	var sx = int(s.get("startX", 0xFF))
	var sy = int(s.get("startY", 0xFF))
	if sx >= 0xFF: sx = 5  # 기본 5 tile
	if sy >= 0xFF: sy = 5
	_hero.position = Vector2(sx * 32 + 16, sy * 32 + 16)
	_hero.direction = int(s.get("startDir", H5Character.DIR_DOWN)) % 4
	# BGM도 mapID 따라 변경 (간단 매핑: mapID % 21 = bgm idx)
	Audio.play_bgm(int(s.get("mapID", 0)) % 21)
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
