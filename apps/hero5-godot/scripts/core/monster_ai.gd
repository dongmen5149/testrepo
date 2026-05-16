## Hero5 Monster AI 시스템 — byte-code VM 구현 (Round 48).
##
## 원본 `Monster::Ai_Process` / `Ai_doActionList` / `Ai_onAction` /
## `ActionOfTrigger` / `IsTriggerEqual` 을 GDScript 로 재현.
##
## 데이터원: `assets/gamedata/monster_ai.json` (Round 45 의 decode_h5_monsterai.py
## 산출, 48 AI definition).
##
## 사용:
##   var ai = MonsterAI.create_runtime(monster_node, ai_type_id)
##   # 매 frame:
##   MonsterAI.process(ai)
##
## 자세히: docs/h5/MONSTER_AI.md
extends Node

const AI_JSON_PATH := "res://assets/gamedata/monster_ai.json"

# Round 44 의 13 action opcode operand size
const OPCODE_OPERAND := {
	0: 2, 1: 2, 2: 1, 3: 1, 4: 3, 5: 4, 6: 2, 7: 3, 8: 2, 9: 2, 10: 1,
	11: -1,   # variable: byte n + n data bytes
	12: 1,
}

# Round 46 의 13 trigger code operand size
const TRIGGER_OPERAND := {
	0: 0, 1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1,
	7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0,
}

# AI definitions: ai_id (int) -> parsed dict
var ai_defs: Dictionary = {}


func _ready() -> void:
	_load_ai_defs()


func _load_ai_defs() -> void:
	if not FileAccess.file_exists(AI_JSON_PATH):
		push_warning("monster_ai.json not found at %s" % AI_JSON_PATH)
		return
	var f := FileAccess.open(AI_JSON_PATH, FileAccess.READ)
	var data: Dictionary = JSON.parse_string(f.get_as_text())
	if data == null or not data.has("by_id"):
		push_warning("monster_ai.json malformed (no by_id)")
		return
	var by_id: Dictionary = data["by_id"]
	for key in by_id.keys():
		ai_defs[int(key)] = by_id[key]


## Monster 의 AI runtime state. 원본 Monster 클래스의 +0x288..+0x315 영역에 해당.
##
## host = AI 가 제어하는 캐릭터 노드 (CHAR 인터페이스). 최소 GetX/GetY/GetMotion/
## GetDir/SetDir 구현 필요.
class MonsterAIState:
	extends RefCounted

	var ai_def: Dictionary             # ai_defs[ai_type_id]
	var host: Node                     # 제어 대상 CHAR

	# Round 44 의 Monster struct AI 영역 (모두 byte 단위)
	var action_idx: int = 0xff          # +0x294 (0xff = 종료)
	var next_action_idx: int = 0xff     # +0x295
	var opcode: int = -1                # +0x297 = sub-state index
	var operand: PackedByteArray        # +0x2a8..+0x2ab (4 byte buffer)
	var action_counter: int = 0         # +0x2b1
	var list_active: int = 0            # +0x2b2
	var action_cooldown: int = 9        # +0x2b4 (u16, default 9 frames)
	var state: int = 1                  # +0x2c3 (Ai_stateCheck input)
	var action_type: int = 0            # +0x2c4 (signed byte)
	var sub_action: int = 0             # +0x2c5
	var sub_action_data: int = 0        # +0x2c6 (sight range 추정)
	var first_set_flag: int = 0         # +0x2c7
	var action_timer: int = 0           # +0x2c8

	# Skill 영역 (5 source paths)
	var skill_id: int = -1              # +0x2c9 (현재 skill, opcode 4)
	var skill_target: int = 4           # +0x2ca
	var skill_range: int = 0             # +0x2cb
	var skill_param: PackedByteArray = PackedByteArray([0, 0, 0, 0])  # +0x2cc..+0x2cf (opcode 5)

	var anim_override: int = 0          # +0x2c2 (opcode 12)
	var action_running: int = 1          # +0x2d0
	var skill_disable: int = 0          # +0x315

	var skill_src_303: int = 0          # +0x303 (opcode 6)
	var skill_src_304: int = 0          # +0x304
	var skill_src_305: int = 0          # +0x305 (opcode 7)
	var skill_src_308: int = 0          # +0x308 (opcode 8)
	var skill_src_30a: int = 0          # +0x30a (opcode 9, NEXT_SKILL)

	# Trigger one-shot flags (모두 0/1)
	var flag_29f: int = 0
	var flag_2b6: int = 0
	var flag_2b7: int = 0
	var flag_2b9: int = 0
	var flag_2ba: int = 0
	var flag_2bc: int = 0
	var flag_2bd: int = 0
	var flag_2be: int = 0
	var flag_2bf: int = 0
	var flag_2c0: int = 0
	var flag_2c1: int = 0

	# Tokenizer state (트리거 stream, action stream)
	var trigger_offset: int = 0          # trigger stream cursor
	var action_offset: int = 0           # action stream cursor

	func _init() -> void:
		operand = PackedByteArray([0, 0, 0, 0])


## Runtime state 생성. host 가 GetX/GetY/GetMotion/GetDir 등 인터페이스를 제공해야 함.
func create_runtime(host: Node, ai_type_id: int) -> MonsterAIState:
	if not ai_defs.has(ai_type_id):
		push_warning("AI def %d not loaded" % ai_type_id)
		return null
	var s := MonsterAIState.new()
	s.host = host
	s.ai_def = ai_defs[ai_type_id]
	return s


## 매 frame 호출 (원본 Monster::Ai_Process 의 등가).
##
## 1. (생략) stun check — host 가 _is_stunned() 제공 시 호출
## 2. state check — Ai_stateCheck 등가 (간소화)
## 3. cooldown decrement (Monster+0x2b4)
## 4. Ai_Action — sub-state machine (간소화: action stream tokenizer 호출)
func process(s: MonsterAIState) -> void:
	if s == null or s.ai_def.is_empty(): return
	if s.host and s.host.has_method("is_stunned") and s.host.is_stunned():
		return
	# state check 는 host 가 제공 (선택)
	if s.host and s.host.has_method("ai_state_check"):
		s.host.ai_state_check(s.state)
	# cooldown: 9 frame default
	if s.action_cooldown > 0:
		s.action_cooldown -= 1
	else:
		s.action_cooldown = 9
	_ai_action(s)


# === Ai_Action 등가 — 13 sub-state dispatch ===
func _ai_action(s: MonsterAIState) -> void:
	if s.host and s.host.has_method("is_die") and s.host.is_die():
		return
	if s.action_type == 0:
		# SetTargetPoint(0) — host 가 제공 (선택)
		if s.host and s.host.has_method("set_target_point"):
			s.host.set_target_point(0)
		return
	# sub-state index = s.opcode (Monster+0x297)
	# 0..12 jumptable. 실 동작은 host method 로 위임 — 정밀 구현은 battle_system 통합 시
	# (이 라운드는 framework + opcode/trigger interpreter 만)
	match s.opcode:
		0:
			# CHASE_TIMER
			if s.action_timer > 0:
				s.action_timer -= 1
			elif s.action_type == 1:
				if s.host and s.host.has_method("ai_chase_check"):
					s.host.ai_chase_check(s.sub_action_data)
		8:
			# SKILL_USE_30A — most common cast path
			if s.host and s.host.has_method("ai_cast_skill"):
				s.host.ai_cast_skill(s.skill_src_30a)
			s.opcode = -1
		_:
			pass


# === Ai_doActionList 등가 — action stream interpreter ===
func step_action_list(s: MonsterAIState) -> bool:
	if s.action_idx == 0xff: return false
	if s.action_running == 0: return false
	# action_list_offset_table 에서 현재 list 의 시작 offset
	var offset_table: Array = s.ai_def.get("action_list_offset_table", [])
	if s.action_idx >= offset_table.size(): return false
	var stream: PackedByteArray = _hex_to_bytes(s.ai_def.get("action_stream_hex", ""))
	# 토큰 1 byte 읽고 dispatch
	if s.action_offset >= stream.size(): return false
	var op := stream[s.action_offset]
	s.action_offset += 1
	s.opcode = op
	var ret := _on_action(s, op, stream)
	if ret == 0:
		# action 완료
		s.action_running = 0
		s.action_counter += 1
		s.list_active = 1
		return false
	return true


# === Ai_onAction 등가 — 13 opcode interpreter ===
## 반환값: 0 = continue, 1 = action 완료
func _on_action(s: MonsterAIState, op: int, stream: PackedByteArray) -> int:
	var sz: int = OPCODE_OPERAND.get(op, -2)
	if sz == -2:
		# unknown opcode — default handler returns 0 (continue)
		return 0
	if op == 11:
		# variable
		if s.action_offset >= stream.size(): return 0
		var n := stream[s.action_offset]
		s.action_offset += 1
		if s.action_offset + n > stream.size(): return 0
		for i in range(min(n, 4)):
			s.operand[i] = stream[s.action_offset + i]
		s.action_offset += n
		return 0
	# load operand bytes
	for i in range(min(sz, 4)):
		if s.action_offset + i < stream.size():
			s.operand[i] = stream[s.action_offset + i]
	s.action_offset += sz
	match op:
		0:
			# WALK
			s.action_type = s.operand[0]
			s.sub_action_data = s.operand[1]
			if s.action_type == 1:
				return 1   # complete: actual cast handled by Ai_Action state
			if s.host and s.host.has_method("ai_set_motion"):
				s.host.ai_set_motion(1)   # motion=1
		1:
			# CHANCE_WALK
			s.action_type = s.operand[0]
			s.sub_action_data = s.operand[1]
			if randi() % 100 < s.operand[1]:
				if s.host and s.host.has_method("ai_set_motion"):
					s.host.ai_set_motion(5)
		2:
			s.sub_action = s.operand[0]
		3:
			if s.first_set_flag == 0:
				s.first_set_flag = s.operand[0]
		4:
			# SKILL_SET → state 3
			s.skill_id = s.operand[0]
			s.skill_target = s.operand[1]
			s.skill_range = s.operand[2]
		5:
			# SKILL_PARAM → state 4
			for i in range(4):
				s.skill_param[i] = s.operand[i]
		6:
			s.skill_src_303 = s.operand[0]
			s.skill_src_304 = s.operand[1]
		7:
			s.skill_src_305 = s.operand[0]
			# operand[1], operand[2] → +0x306/+0x307
		8:
			s.skill_src_308 = s.operand[0]
		9:
			# NEXT_SKILL → state 8
			s.skill_src_30a = s.operand[0]
		12:
			s.anim_override = s.operand[0]
		_:
			pass
	return 0


# === ActionOfTrigger 등가 — trigger stream walker ===
## 반환값: true = 트리거 매칭 (action 전환), false = 미매칭 (다음 entry)
func step_trigger_list(s: MonsterAIState) -> bool:
	var stream: PackedByteArray = _hex_to_bytes(s.ai_def.get("trigger_stream_hex", ""))
	if s.trigger_offset >= stream.size(): return false
	var code := stream[s.trigger_offset]
	s.trigger_offset += 1
	# trigger 5 = ALWAYS_GOTO special path
	if code == 5:
		if s.trigger_offset >= stream.size(): return false
		s.action_idx = stream[s.trigger_offset]
		s.trigger_offset += 1
		_immadiately_init(s)
		return true
	# 일반 trigger: IsTriggerEqual 호출
	var operand_sz: int = TRIGGER_OPERAND.get(code, 0)
	var operand_val: int = 0
	if operand_sz == 1 and s.trigger_offset < stream.size():
		operand_val = stream[s.trigger_offset]
		s.trigger_offset += 1
	var matched := _is_trigger_equal(s, code, operand_val)
	if s.trigger_offset >= stream.size(): return false
	var action_id := stream[s.trigger_offset]
	s.trigger_offset += 1
	if matched:
		s.action_idx = action_id
		_immadiately_init(s)
		return true
	return false


# === IsTriggerEqual 등가 — 13 trigger 평가 ===
func _is_trigger_equal(s: MonsterAIState, code: int, operand: int) -> bool:
	match code:
		0:
			if s.flag_29f == 0:
				s.flag_29f = 1
				return true
			return false
		1:
			# VISIBILITY_RECT: operand = IRect index (×40 = base offset into Monster+0x2d8)
			# host 가 visibility 검사 메서드 제공 시 사용
			if s.host and s.host.has_method("ai_check_visibility"):
				return s.host.ai_check_visibility(operand)
			return false
		2:
			if s.flag_2bc == 1:
				s.flag_2bc = 0
				return true
			return false
		3:
			# ALL_MONSTERS_DEAD
			if s.host and s.host.has_method("ai_all_dead"):
				if s.host.ai_all_dead():
					s.flag_2c1 = 1
					return true
			return false
		4:
			# SELF_DEAD
			if s.host and s.host.has_method("is_die") and s.host.is_die():
				s.flag_2ba = 1
				return true
			return false
		5:
			# ALWAYS_GOTO handled in caller
			return true
		6:
			# TUTORIAL_FLAG vs gv+0x130/0x131/0x132
			if s.host and s.host.has_method("ai_tutorial_flag"):
				return s.host.ai_tutorial_flag(operand)
			return false
		7:
			if s.flag_2bf == 1:
				s.flag_2bf = 0
				return true
			return false
		8:
			if s.flag_2b9 == 1:
				s.flag_2b9 = 0
				return true
			return false
		9:
			if s.flag_2bd == 1:
				s.flag_2bd = 0
				return true
			return false
		10:
			if s.flag_2be == 1:
				s.flag_2be = 0
				return true
			return false
		11:
			if s.flag_2b7 == 1:
				s.flag_2b7 = 0
				return true
			return false
		12:
			if s.flag_2b6 == 1:
				s.flag_2b6 = 0
				return true
			return false
	return false


func _immadiately_init(s: MonsterAIState) -> void:
	# 원본 Monster::ImmadiatelyInit — action 전환 시 일부 fields reset
	s.action_running = 1
	s.opcode = -1
	s.action_timer = 0


func _hex_to_bytes(hex: String) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(hex.length() / 2)
	for i in range(out.size()):
		out[i] = ("0x" + hex.substr(i * 2, 2)).hex_to_int()
	return out
