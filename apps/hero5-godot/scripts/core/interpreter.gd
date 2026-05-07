## .scn body 의 Interpreter 바이트코드 실행기 (초기 골격).
##
## 원본 EventProc::onFunction 은 77개 opcode 를 dispatch — 우리는 가장 빈번한
## 것부터 stub 으로 구현 (현재는 print 로 추적).
##
## 실제 Event 의 의미 매핑은 work/h5/analysis/opcode_table.tsv 참조.
class_name H5Interpreter
extends RefCounted

# opcode → (name, arg_size). Phase 2-A.10 자동 추출 결과.
const OPCODE_TABLE := {
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
	0x12: ["Event_EventMoveBreak", 0],
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
	# (full table loaded from assets/scenes/opcode_table.json at runtime)
}


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


func _dispatch(op: int, name: String, args: PackedByteArray) -> void:
	# 현재는 모든 opcode 를 print. 실제 동작은 후속 구현.
	# 가장 자주 쓰일 후속 구현 후보:
	#   Event_PlayerTeleport, Event_SituateDialogText, Event_PlayerMove,
	#   Event_PlayerDirection, Event_SituateCamera, Event_SituateDelay
	print("  0x%02x %s %s" % [op, name, args.hex_encode()])
