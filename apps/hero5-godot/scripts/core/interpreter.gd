## .scn body 의 Interpreter 바이트코드 실행기.
## Dialog / Teleport / Direction / Move 등 핵심 핸들러 구현.
##
## 원본 EventProc::onFunction 은 77개 opcode 를 dispatch — 우리는 가장 빈번한
## 것부터 stub 으로 구현 (현재는 print 로 추적).
##
## 실제 Event 의 의미 매핑은 work/h5/analysis/opcode_table.tsv 참조.
## Runtime 우선순위:
##   1. assets/scenes/opcode_table.json 이 존재하면 거기서 77개 전체 로드
##   2. fallback = 아래 BASE_TABLE (잘 알려진 ~38 opcode 만)
class_name H5Interpreter
extends RefCounted

const EXTERNAL_TABLE_PATH := "res://assets/scenes/opcode_table.json"

# opcode → (name, arg_size). 0x00-0x1d = ARM disasm 자동 추출 결과 (.so 의 EventProc::onFunction).
# 외부 EXTERNAL_TABLE_PATH (assets/scenes/opcode_table.json) 가 source of truth — 77개 전체.
# 본 BASE_TABLE 은 외부 JSON 부재 시 fallback 만. ~40 opcode 는 외부 JSON 의존.
const BASE_TABLE := {
	0x00: ["Event_EnemyAction", 6],
	0x01: ["Event_EnemyChange", 2],
	0x02: ["Event_EnemyChangeAction", 7],
	0x03: ["Event_EnemyDir", 2],
	0x04: ["Event_EnemyEffect", 2],
	0x05: ["Event_EnemyImo", 2],
	0x06: ["Event_EnemyMove", 5],
	0x07: ["Event_EnemyMoveRelative", 5],
	0x08: ["Event_EnemyTeleport", 5],
	0x09: ["Event_EventAction", 6],
	0x0a: ["Event_EventChangeCheck", 2],
	0x0b: ["Event_EventChangeImg", 2],
	0x0c: ["Event_EvnetImgAction", 7],
	0x0d: ["Event_EventChangeMoveType", 2],
	0x0e: ["Event_EventDirection", 2],
	0x0f: ["Event_EventEffect", 2],
	0x10: ["Event_EventImo", 2],
	0x11: ["Event_EventMove", 5],
	0x12: ["Event_EventMoveBreak", 1],
	0x13: ["Event_EventMoveRelative", 5],
	0x14: ["Event_EventTeleport", 5],
	0x15: ["Event_MapCollision", 3],
	0x16: ["Event_MapEncountPirate", 2],
	0x17: ["Event_MapObjChangeAll", 2],
	0x18: ["Event_MapTileChange", 6],
	0x19: ["Event_MapTileChangeAll", 4],
	0x1a: ["Event_MapWorldControl", 2],
	0x1b: ["Event_PlayerAction", 5],
	0x1c: ["Event_PlayerAppearSpirit", 1],
	0x1d: ["Event_PlayerChange", 1],
	# Quest opcodes (.so disasm 검증):
	0x29: ["Event_QuestBoss", 2],
	0x2a: ["Event_QuestQSwitch", 2],
	0x2b: ["Event_QuestStatus", 2],
	0x2c: ["Event_QuestSwitch", 2],
	0x2d: ["Event_QuestTimer", 4],
	# Situate / Scene (.so disasm 검증):
	0x32: ["Event_Scene_SaveAble", 1],
	0x33: ["Event_Scene_WarpAble", 1],
	0x34: ["Event_Scene_WarpPoint", 4],
	0x35: ["Event_SituateBallon", 2],
	0x36: ["Event_SituateCamera", 3],
	0x37: ["Event_SituateCameraTarget", 2],
	0x38: ["Event_SituateDelay", 1],
	0x39: ["Event_SituateDialogText", 4],
	0x3a: ["Event_SituateWindowOff", 1],
	0x3b: ["Event_SituateNarration", 3],
	0x3e: ["Event_SituatePopup", 1],
	# (Event_Scene_ChangeBgm 은 dispatch table 에 존재하지 않음 — 별도 메커니즘)
}

## OPCODE_TABLE: 인스턴스 단위 — BASE_TABLE 복사 + 외부 JSON 머지.
var OPCODE_TABLE: Dictionary = {}


func _init() -> void:
	OPCODE_TABLE = BASE_TABLE.duplicate()
	_try_load_external()


func _try_load_external() -> void:
	if not FileAccess.file_exists(EXTERNAL_TABLE_PATH): return
	var f := FileAccess.open(EXTERNAL_TABLE_PATH, FileAccess.READ)
	if f == null: return
	var data = JSON.parse_string(f.get_as_text())
	# 형식 옵션:
	#   A. {"opcodes": [{"op":0,"name":"Event_X","size":N}, ...]}
	#   B. {"0": ["Event_X", N], "53": ["Event_SituateBallon", 2], ...}
	if data is Dictionary:
		if data.has("opcodes") and data["opcodes"] is Array:
			for entry in data["opcodes"]:
				var op = int(entry.get("op", -1))
				var name = str(entry.get("name", ""))
				var sz = int(entry.get("size", 0))
				if op >= 0 and not name.is_empty():
					OPCODE_TABLE[op] = [name, sz]
		else:
			for k in data.keys():
				var op = int(k)
				var v = data[k]
				if v is Array and v.size() >= 2:
					OPCODE_TABLE[op] = [str(v[0]), int(v[1])]


func run_intro(scene_meta: Dictionary) -> void:
	# 현재는 메타만 print. body 바이트는 별도 파일이 필요 (.scn 원본 또는 export 시 포함).
	print("[Interp] enter scene %s mapID=%d body_len=%d" % [
		scene_meta.get("name", "?"),
		scene_meta.get("mapID", -1),
		scene_meta.get("body_len", 0)])
	print("[Interp] start pos=(%d, %d) dir=%d" % [
		scene_meta.get("startX", 0),
		scene_meta.get("startY", 0),
		scene_meta.get("startDir", 0)])


## body 바이트 (.scn 원본의 11-byte 헤더 이후) 를 해석.
##   body: PackedByteArray
##   max_steps: 안전 한계 (무한 루프 방지)
func step(body: PackedByteArray, max_steps: int = 64) -> void:
	var pos := 0
	var n := body.size()
	var steps := 0
	while pos < n and steps < max_steps:
		steps += 1
		var op := body[pos]; pos += 1
		if op == 0xFF:
			# escape: <argc> <sizes...> <subs...>
			if pos >= n: break
			var argc := body[pos]; pos += 1
			if argc > 0x13:
				print("[Interp] END marker"); break
			var sizes: Array = []
			for i in argc:
				if pos >= n: break
				sizes.append(body[pos]); pos += 1
			# skip sub-streams
			for sz in sizes:
				pos = min(pos + sz, n)
			print("[Interp] ESC argc=%d sizes=%s" % [argc, sizes])
			continue
		if op in OPCODE_TABLE:
			var entry = OPCODE_TABLE[op]
			var name = entry[0]
			var sz = entry[1]
			var args = body.slice(pos, pos + sz)
			pos += sz
			_dispatch(op, name, args)
		else:
			print("[Interp] OP 0x%02x ???" % op)
	if steps >= max_steps:
		print("[Interp] step limit reached")


## 등록된 외부 핸들러: 호스트 (Demo 씬 등) 가 set_handler() 로 등록.
## 핸들러 시그니처: func(args: PackedByteArray) -> void
var _handlers: Dictionary = {}

func set_handler(opcode: int, fn: Callable) -> void:
	_handlers[opcode] = fn


func _dispatch(op: int, name: String, args: PackedByteArray) -> void:
	if op in _handlers:
		_handlers[op].call(args)
		return
	# 기본 핸들러 — BASE_TABLE 또는 외부 JSON 에 등록된 이름은 처리.
	# 외부 JSON 에서만 활성화되는 이름들 (Event_PlayerMove 등) 은 케이스 보존.
	match name:
		# BASE_TABLE 의 Enemy* / Event* / Map* (0x00-0x1a)
		"Event_EnemyEffect":
			if args.size() >= 2:
				print("[Interp] EnemyEffect(idx=%d, fx=%d)" % [args[0], args[1]])
		"Event_EnemyMove", "Event_EnemyMoveRelative":
			if args.size() >= 5:
				print("[Interp] %s %s" % [name, args.hex_encode()])
		"Event_EnemyTeleport":
			if args.size() >= 5:
				var x = args[0] | (args[1] << 8)
				var y = args[2] | (args[3] << 8)
				print("[Interp] EnemyTeleport(%d, %d, dir=%d)" % [x, y, args[4]])
		"Event_EventMove", "Event_EventMoveRelative":
			if args.size() >= 5:
				print("[Interp] %s %s" % [name, args.hex_encode()])
		"Event_EventTeleport":
			if args.size() >= 5:
				var x = args[0] | (args[1] << 8)
				var y = args[2] | (args[3] << 8)
				print("[Interp] EventTeleport(%d, %d, dir=%d)" % [x, y, args[4]])
		"Event_MapTileChange":
			# args: x, y, tileID_lo, tileID_hi, layer, ?
			if args.size() >= 6:
				print("[Interp] MapTileChange x=%d y=%d tile=%d layer=%d" % [
					args[0], args[1],
					args[2] | (args[3] << 8),
					args[4]])
		"Event_MapTileChangeAll":
			print("[Interp] MapTileChangeAll %s" % args.hex_encode())
		# BASE_TABLE 의 Player* (0x1b-0x1d)
		"Event_PlayerAction":
			if args.size() >= 5:
				print("[Interp] PlayerAction %s" % args.hex_encode())
		"Event_PlayerAppearSpirit":
			print("[Interp] PlayerAppearSpirit %s" % args.hex_encode())
		"Event_PlayerChange":
			if args.size() >= 1:
				print("[Interp] PlayerChange(%d)" % args[0])
		# BASE_TABLE 의 Quest* (0x31, 0x32, 0x33, 0x3a, 0x42)
		"Event_QuestBoss":
			if args.size() >= 2:
				print("[Interp] QuestBoss(qid=%d, ?=%d)" % [args[0], args[1]])
		"Event_QuestTimer":
			if args.size() >= 4:
				var dur = args[1] | (args[2] << 8)
				print("[Interp] QuestTimer(qid=%d, dur=%d)" % [args[0], dur])
		"Event_QuestStatus":
			if args.size() >= 2:
				print("[Interp] QuestStatus(qid=%d, status=%d)" % [args[0], args[1]])
		"Event_QuestSwitch", "Event_QuestQSwitch":
			if args.size() >= 2:
				print("[Interp] %s(qid=%d, on=%d)" % [name, args[0], args[1]])
		# BASE_TABLE 의 Situate* + Scene_*
		"Event_SituateBallon":
			print("[Interp] Ballon %s" % args.hex_encode())
		"Event_SituateDialogText":
			print("[Interp] DialogText %s" % args.hex_encode())
		"Event_SituateNarration":
			print("[Interp] Narration %s" % args.hex_encode())
		"Event_SituatePopup":
			print("[Interp] Popup")
		"Event_Scene_ChangeBgm":
			if args.size() >= 1:
				print("[Interp] ChangeBgm(%d)" % args[0])
		# 외부 JSON 에서 활성화될 수 있는 이름들 (BASE_TABLE 외).
		"Event_PlayerTeleport":
			if args.size() >= 5:
				var x = args[0] | (args[1] << 8)
				var y = args[2] | (args[3] << 8)
				print("[Interp] PlayerTeleport(%d, %d, dir=%d)" % [x, y, args[4]])
		"Event_PlayerDirection":
			if args.size() >= 1:
				print("[Interp] PlayerDirection(%d)" % args[0])
		"Event_PlayerMove":
			if args.size() >= 5:
				print("[Interp] PlayerMove %s" % args.hex_encode())
		"Event_PlayerEffect":
			if args.size() >= 1:
				print("[Interp] PlayerEffect(%d)" % args[0])
		"Event_SituateDelay":
			if args.size() >= 2:
				var ms = args[0] | (args[1] << 8)
				print("[Interp] SituateDelay(%dms)" % ms)
		"Event_SituateScreenShake":
			print("[Interp] SituateScreenShake")
		"Event_SituateCamera":
			print("[Interp] SituateCamera %s" % args.hex_encode())
		"Event_SituateCameraTarget":
			if args.size() >= 1:
				print("[Interp] CameraTarget(target=%d)" % args[0])
		"Event_SituateSystemMessage":
			# args = u16 str_id (Strings::getString → Battle::SetSystemMsgUi)
			if args.size() >= 2:
				var sid = args[0] | (args[1] << 8)
				print("[Interp] SystemMessage(str_id=%d)" % sid)
		"Event_screenEffect":
			if args.size() >= 1:
				print("[Interp] ScreenEffect(%d)" % args[0])
		"Event_Scene_WarpAble", "Event_Scene_WarpPoint", "Event_Scene_SaveAble":
			print("[Interp] %s %s" % [name, args.hex_encode()])
		# disasm 확정 (EVENT_OPCODE_REFERENCE.md):
		"Event_PlayerDamage":
			# arg = u8 percent. dmg = pct × max_hp / 100.
			# percent != 100 일 때 dmg = min(dmg, cur_hp - 1) — 즉사 방지.
			# → BATTLER::IncreaseHP(-dmg).
			if args.size() >= 1:
				var pct: int = args[0]
				var dmg: int = pct * GameState.max_hp / 100
				if pct == 100:
					dmg = GameState.hp
				elif dmg >= GameState.hp:
					dmg = max(0, GameState.hp - 1)
				GameState.hp = max(0, GameState.hp - dmg)
				print("[Interp] PlayerDamage(pct=%d%%) -> -%d HP (now %d/%d)" % [pct, dmg, GameState.hp, GameState.max_hp])
		"Event_PlayerRestoreHp":
			# arg = u8 percent. heal = pct × max_hp / 100. clamp ≤ max_hp.
			if args.size() >= 1:
				var pct: int = args[0]
				var heal: int = pct * GameState.max_hp / 100
				GameState.hp = min(GameState.max_hp, GameState.hp + heal)
				print("[Interp] PlayerRestoreHp(pct=%d%%) -> +%d HP (now %d/%d)" % [pct, heal, GameState.hp, GameState.max_hp])
		"Event_PlayerRestoreSp":
			# arg = u8 percent. → HERO::IncreaseSP. clamp ≤ max_sp.
			if args.size() >= 1:
				var pct: int = args[0]
				var heal: int = pct * GameState.max_sp / 100
				GameState.sp = min(GameState.max_sp, GameState.sp + heal)
				print("[Interp] PlayerRestoreSp(pct=%d%%) -> +%d SP (now %d/%d)" % [pct, heal, GameState.sp, GameState.max_sp])
		"Event_PlayerDirection":
			# arg = u8 dir (0..3). 외부 핸들러 없으면 GameState 만 갱신.
			if args.size() >= 1:
				GameState.player_dir = args[0]
				print("[Interp] PlayerDirection(%d)" % args[0])
		"Event_PlayerTeleport":
			# args = u16 x, u16 y, u8 dir. GameState 좌표 갱신.
			if args.size() >= 5:
				var tx: int = args[0] | (args[1] << 8)
				var ty: int = args[2] | (args[3] << 8)
				GameState.player_x = tx
				GameState.player_y = ty
				GameState.player_dir = args[4]
				print("[Interp] PlayerTeleport(%d, %d, dir=%d)" % [tx, ty, args[4]])
		"Event_PlayerImo":
			# arg = u8 emo_id (머리 위 이모티콘).
			if args.size() >= 1:
				print("[Interp] PlayerImo(emo=%d)" % args[0])
		"Event_QuestStatus":
			# args = u8 qid, u8 status. 0=inactive 1=active 2=completed 3=failed.
			if args.size() >= 2:
				var qid: int = args[0]; var status: int = args[1]
				if status == Quest.STATUS_ACTIVE:
					Quest.start(qid)
				elif status == Quest.STATUS_COMPLETED:
					Quest.complete(qid)
				else:
					Quest._state[qid] = status
				print("[Interp] QuestStatus(qid=%d, status=%d)" % [qid, status])
		"Event_QuestSwitch", "Event_QuestQSwitch":
			# args = u8 qid, u8 on_off. on=1 → start, off=0 → reset.
			if args.size() >= 2:
				var qid: int = args[0]; var on_off: int = args[1]
				if on_off:
					Quest.start(qid)
				else:
					Quest._state[qid] = Quest.STATUS_INACTIVE
				print("[Interp] %s(qid=%d, on=%d)" % [name, qid, on_off])
		"Event_EnemyChange":
			# args = u8 slot_idx, u8 monster_id. → Map::MonsterChange.
			if args.size() >= 2:
				print("[Interp] EnemyChange(slot=%d, mon=%d)" % [args[0], args[1]])
		"Event_MapCollision":
			# args = u8 x, u8 y, u8 attr. → Map::MapAttributeChange.
			if args.size() >= 3:
				print("[Interp] MapCollision(x=%d, y=%d, attr=%d)" % [args[0], args[1], args[2]])
		"Event_SituateSlowMotion":
			# args = u8 a, u8 b, u8 c. → Battle::SetSlowFrame + InitSlowFrame.
			if args.size() >= 3:
				print("[Interp] SituateSlowMotion(%d, %d, %d)" % [args[0], args[1], args[2]])
		_:
			print("  0x%02x %s %s" % [op, name, args.hex_encode()])
