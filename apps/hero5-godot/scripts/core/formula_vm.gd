## Formula VM 평가기 — calc_pl/en/sk.dat 의 186 공식 실행.
##
## 원본: libHeroesLore5.so 의 `Formula::calcByFormula` (0x77244) + getValFunc (0x758d0).
## 자세히: docs/h5/DES_VARIANT.md, FORMULA_VAR_DICT.md.
##
## 호출 규약 (.so 와 동일):
##   r5 = skill   (HeroSkillInfo*)
##   r6 = defender (CHAR*)
##   fp = item    (ItemBase*)
##   gv = global  (player state, 자동 lookup)
##
## GDScript 측 ctx 는 위 4종을 Dictionary 로 받음:
##   {"skill": {...stats}, "defender": {...stats}, "item": {...stats}, "player": {...gv stats}}
##
## ID 분기:
##   0..999    → calc_pl (player, 39 formulas)
##   1000..1999 → calc_en (enemy, 19 formulas)
##   2000..3007 → calc_sk (skill, 128 formulas)
extends Node

const FORMULAS_PATH := "res://assets/data/formula/formulas.json"
const VAR_DICT_PATH := "res://assets/data/formula/var_dict.json"

# opcode (0x11..0x16)
const OP_ADD := 0x11
const OP_SUB := 0x12
const OP_MUL := 0x13
const OP_DIV := 0x14
const OP_MOD := 0x15
const OP_XOR := 0x16

var _formulas: Dictionary = {}    # id (str) → {lower, upper, body: [["op",N]|["imm",N]|["var",N]]}
var _var_dict: Dictionary = {}    # var_id (str) → {struct, offset, type, role}
var _loaded := false


func _ready() -> void:
	_load()


func _load() -> void:
	if _loaded:
		return
	for path_var in [[FORMULAS_PATH, "_formulas"], [VAR_DICT_PATH, "_var_dict"]]:
		var path: String = path_var[0]
		var attr: String = path_var[1]
		if not FileAccess.file_exists(path):
			push_warning("FormulaVM: missing %s — assets/data/formula JSONs not exported" % path)
			continue
		var f := FileAccess.open(path, FileAccess.READ)
		var txt := f.get_as_text()
		f.close()
		var parsed = JSON.parse_string(txt)
		if parsed is Dictionary:
			set(attr, parsed)
	_loaded = true


## formula_id 의 공식을 평가. ctx 는 {skill, defender, item, player} dict.
##
## 결과: 평가된 정수 (clamp 적용 후). 공식 미존재 시 0.
##
## 예: var dmg = FormulaVM.calc(0, {skill=skill_data, defender=enemy, item=null, player={atk=100, ...}})
func calc(formula_id: int, ctx: Dictionary = {}) -> int:
	_load()
	var key := str(formula_id)
	if not _formulas.has(key):
		return 0
	var spec: Dictionary = _formulas[key]
	var stack: Array[int] = []
	var body: Array = spec.get("body", [])
	for entry in body:
		if entry.size() < 2:
			continue
		var kind: String = entry[0]
		var arg: int = int(entry[1])
		match kind:
			"imm":
				stack.append(arg)
			"var":
				stack.append(_lookup_var(arg, ctx))
			"op":
				if stack.size() < 2:
					return 0
				var b: int = stack.pop_back()
				var a: int = stack.pop_back()
				stack.append(_apply_op(a, b, arg))
	if stack.is_empty():
		return 0
	var top: int = stack[-1]
	var lower: int = int(spec.get("lower", -2147483648))
	var upper: int = int(spec.get("upper", 2147483647))
	return clamp(top, lower, upper)


## var_id 를 ctx 에서 lookup.
##
## - skill (1..60, 184..191): ctx.skill.stat[N] 또는 ctx.skill_sb.stat[N]
## - defender (192..251): ctx.defender.stat[N]
## - item (168..182): ctx.item.stat[N]
## - gv_sub (58..167): ctx.player.<offset 매핑>
## - 기타: 0 또는 특수 상수 (-50 등)
func _lookup_var(var_id: int, ctx: Dictionary) -> int:
	var key := str(var_id)
	if not _var_dict.has(key):
		return 0
	var info: Dictionary = _var_dict[key]
	var struct: String = info.get("struct", "unknown")
	var offset: int = int(info.get("offset", 0))
	var type_str: String = info.get("type", "u32")

	match struct:
		"const":
			if var_id == 248: return -50
			if var_id == 249: return -50
			return 0
		"skill":
			return _read_skill(ctx.get("skill"), var_id, offset, type_str)
		"defender":
			return _read_defender(ctx.get("defender"), var_id, offset, type_str)
		"item":
			return _read_item(ctx.get("item"), var_id, offset, type_str)
		"skill_sb":
			return _read_skill(ctx.get("skill_sb", ctx.get("skill")), var_id, offset, type_str)
		"gv_sub":
			return _read_player(ctx.get("player", {}), var_id, offset, type_str)
	return 0


func _apply_op(a: int, b: int, op: int) -> int:
	match op:
		OP_ADD: return a + b
		OP_SUB: return a - b
		OP_MUL: return a * b
		OP_DIV: return a / b if b != 0 else 0
		OP_MOD: return a % b if b != 0 else 0
		OP_XOR: return a ^ b
	return 0


# ──────────────────────────────────────────────────────────────────────
# 구조체 lookup (역설계로 알려진 offset 기반)
# ──────────────────────────────────────────────────────────────────────


## skill struct (var_id 1..60). offset 은 skill 구조체의 byte offset.
##
## 1=skill_id, 2=ptr/handle, 3..19=stat[0..15] (s16, +0x08..+0x28),
## 20..31=stat[16..27] (+0x66..+0x7c), 32..39=stat[28..35] (+0x7e..+0x8c),
## 40=special (+0x90 4B), 41..47=stat[36..42] (+0x98..+0xa6),
## 48..60=stat[43..55] (+0xa8..+0xb6)
##
## ctx.skill 은 보통 GameData 의 _skills_cache 에서 받은 dict 인데, 거기엔
## 이미 stats_u16 배열이 있음. offset → array index 변환 후 fetch.
func _read_skill(skill, var_id: int, offset: int, type_str: String) -> int:
	if skill == null:
		return 0
	if var_id == 1:
		return int(skill.get("id", 0)) if skill is Dictionary else 0
	# stats_u16 배열에서 offset 으로 lookup (offset 은 byte 단위, stat[i] = +0x08 + i*2)
	var stats: Array = []
	if skill is Dictionary:
		stats = skill.get("stats_u16", [])
	if stats.is_empty():
		return 0
	# var_id 별 stat index 직접 매핑 (FORMULA_VAR_DICT.md 참조)
	var idx := -1
	if var_id >= 3 and var_id <= 19:
		idx = var_id - 3
	elif var_id >= 20 and var_id <= 31:
		idx = 16 + (var_id - 20)
	elif var_id >= 32 and var_id <= 39:
		idx = 28 + (var_id - 32)
	elif var_id >= 41 and var_id <= 47:
		idx = 36 + (var_id - 41)
	elif var_id >= 48 and var_id <= 60:
		idx = 43 + (var_id - 48)
	if idx >= 0 and idx < stats.size():
		var v: int = int(stats[idx])
		# s16 변환
		if type_str == "s16" and v >= 0x8000:
			v -= 0x10000
		return v
	return 0


## defender (CHAR*, var_id 192..251). offset 구조는 skill 과 동일.
##
## ctx.defender 는 enemy stats dict 또는 CHAR Node 가 가질 만한 값 (atk/def/hp/...).
## 이 단순화된 구조에서는 Dictionary 로 받고 stat lookup.
func _read_defender(defender, var_id: int, offset: int, _type_str: String) -> int:
	if defender == null or not defender is Dictionary:
		return 0
	# 자주 쓰이는 var_id 직접 매핑 (offset 0x08+i*2 = stat[i])
	var d: Dictionary = defender
	var idx := -1
	if var_id >= 194 and var_id <= 209:
		idx = var_id - 194
	elif var_id >= 210 and var_id <= 251:
		# +0x66 부터 추가 stats — defender 의 stat[16+] 와 매핑
		idx = 16 + (var_id - 210)
	# CHAR/BATTLER stats 의 일반 명칭 추정 (idx 0..7 정도)
	# 0=hp, 1=mp, 2=atk, 3=def, ... (게임 마다 다르지만 .so 의 BATTLER offset 패턴)
	if idx == 0: return int(d.get("atk", d.get("attack", 0)))
	if idx == 1: return int(d.get("def", d.get("defense", 0)))
	if idx == 2: return int(d.get("dex", 0))
	if idx == 3: return int(d.get("int", d.get("intel", 0)))
	if idx == 4: return int(d.get("luk", 0))
	if idx == 5: return int(d.get("hp", 0))
	if idx == 6: return int(d.get("mp", 0))
	if idx == 7: return int(d.get("max_hp", d.get("hp", 0)))
	# 그 외 인덱스는 stat 배열에서 (있다면)
	var arr: Array = d.get("stats", [])
	if idx >= 0 and idx < arr.size():
		return int(arr[idx])
	return 0


## item struct. var_id 168..182. FORMULA_VAR_DICT.md offset 매핑.
func _read_item(item, var_id: int, offset: int, _type_str: String) -> int:
	if item == null:
		return 0
	if not item is Dictionary:
		return 0
	var d: Dictionary = item
	# var_id 별 매핑
	match var_id:
		168: return int(d.get("atk_value", d.get("atk", 0)))
		169: return int(d.get("def_value", d.get("def", 0)))
		170, 171, 172, 173:
			var stats: Array = d.get("stats", [])
			var idx := var_id - 170
			if idx < stats.size(): return int(stats[idx])
			return 0
		181: return int(d.get("flag", 0))
		182: return int(d.get("field", 0))
	return 0


## gv+0x1474 sub-struct 필드 lookup (var_id 58..167).
##
## offset → ctx.player 의 명명된 필드로 매핑. 정확한 의미는 미확정이지만
## 기본 GameState 와 매핑 가능한 것은 합리적 추정값을 반환.
func _read_player(player: Dictionary, var_id: int, offset: int, type_str: String) -> int:
	if player.is_empty():
		# Default fallback — GameState 자동 채움
		return _player_default(var_id, offset)
	# offset 별 직접 매핑 (정확한 의미는 후속 RE 필요 — 추정값 우선)
	if player.has(str(offset)):
		return int(player[str(offset)])
	# var_id 별 약식 매핑
	if 58 <= var_id <= 110:
		# 작은 stat 값들 (s8/s16) — 기본 0
		return 0
	if 111 <= var_id <= 167:
		# 큰 stat 값들 (s16) — player attack/defense/hp/mp 등
		return _player_default(var_id, offset)
	return 0


## GameState 와 직접 연동된 기본 매핑 — autoload GameState 사용.
##
## var_id ↔ field 매핑은 .so writer 분석 (h5_find_gv_writers.py) +
## calc_pl 공식 cross-check 로 확정 (battle_system.gd::_player_ctx 와 동일).
func _player_default(var_id: int, _offset: int) -> int:
	var gs := get_node_or_null("/root/GameState")
	if gs == null:
		return 0
	match var_id:
		58: return int(gs.level)              # 0x22d  V[58]  level (확정)
		60: return int(gs.stat_str)           # 0x236  base_str
		61: return int(gs.stat_dex)           # 0x238  base_dex
		62: return int(gs.stat_int)           # 0x23a  base_int
		63: return int(gs.stat_con)           # 0x23c  base_con
		69: return int(gs.sp)                 # 0x248  SP (cur)
		# V[111..116] = LoadResClassInfo 가 6 sequential s16 store — 클래스 base 계수 (Round 7).
		# id=24 ATK 공식: V[5] + V[111] * ((V[58]*2) + V[154])
		# → V[111] = atk_growth_per_(level*2+str) coefficient.
		# id=25..29 의 V[112..116] = 5 secondary stats base (각각 V[129..133] 와 짝).
		111: return max(1, int(gs.total_attack() if gs.has_method("total_attack") else 10) / max(1, int(gs.level) * 2 + int(gs.stat_str)))
		112: return 0                         # 0x27a  secondary stat #1 base
		113: return 0                         # 0x27c  secondary stat #2 base
		114: return 0                         # 0x27e  secondary stat #3 base
		115: return 0                         # 0x280  secondary stat #4 base
		116: return 0                         # 0x282  secondary stat #5 base
		118: return 0                         # 0x298  bonus_str (장비/버프, 미보유)
		119: return 0                         # 0x29a  bonus_dex
		120: return 0                         # 0x29c  bonus_int
		121: return 0                         # 0x29e  bonus_con
		# 0x294/0x295/0x296 active buff descriptor (HERO::ApplyBuildupEffect 가 store) 는
		# Formula VM 의 var_dict 에 없음 — gameplay 코드(UI 아이콘 표시 등) 전용 필드.
		# 따라서 V[125]/V[126] 매핑 대상이 아님 (V[125]=0x2a6 / V[126]=0x2a8 는 별개).
		125: return 0                         # 0x2a6  buff stack slot (InitStatusComputation resets)
		126: return 0                         # 0x2a8  buff stack slot
		# V[127..148] = buff/equipment 가 추가하는 bonus stat (Round 8 — calc_pl 공식 패턴).
		127: return 0                         # 0x2aa s8  defense_reduction_percent (id=84..85 0..99 bound)
		128: return 0                         # 0x2ac  atk_percent_bonus (id=24 (100+V[128])/100)
		129: return 0                         # 0x2ae  secondary stat #1 bonus (id=25 V[129]*10)
		130: return 0                         # 0x2b0  secondary stat #2 bonus (id=26 V[130]*10)
		131: return 0                         # 0x2b2  secondary stat #3 bonus (id=27 flat)
		132: return 0                         # 0x2b4  secondary stat #4 bonus (id=28 flat)
		133: return 0                         # 0x2b6  secondary stat #5 bonus (id=29 flat)
		134, 135: return 0                    # 0x2b8, 0x2ba magic atk paired (element 1/2)
		136, 137, 138, 139, 140, 141, 142, 143: return 0  # 0x2bc..0x2ca 4-pair element bonuses
		144, 145: return 0                    # 0x2cc, 0x2ce main element bonuses (id=7,8)
		146, 148: return 0                    # 0x2d0, 0x2d4 sub-stats for 255-bound formula (id=16)
		147: return 0                         # 0x2d2  element bonus
		# V[151..154] = formula 의존 stat (Round 7 — id=0 MaxHP / id=24 ATK 공식 cross-check).
		151: return int(gs.stat_int)          # magic stat base (id=4 magic atk +V[151])
		152: return int(gs.stat_dex)          # magic stat base (id=5 paired with V[151])
		153: return int(gs.stat_con)          # con 보정 (id=0 max_hp 공식 10*V[153])
		154: return int(gs.stat_str)          # str 보정 (id=24 atk 공식 V[58]*2+V[154])
		155: return int(gs.max_sp)            # 0x2e6  max_sp 확정 (ApplyBuildupEffect SP clamp upper bound)
		_:
			return 0


## 디버그: formula 의 infix 표현 반환 (formula_id 별로).
func describe(formula_id: int) -> String:
	_load()
	var key := str(formula_id)
	if not _formulas.has(key):
		return "<no formula %d>" % formula_id
	var spec: Dictionary = _formulas[key]
	var stack: Array[String] = []
	var op_sym := {OP_ADD: "+", OP_SUB: "-", OP_MUL: "*", OP_DIV: "/", OP_MOD: "%", OP_XOR: "^"}
	for entry in spec.get("body", []):
		var kind: String = entry[0]
		var arg: int = int(entry[1])
		match kind:
			"imm":
				stack.append(str(arg))
			"var":
				stack.append("V[%d]" % arg)
			"op":
				if stack.size() < 2: return "<malformed>"
				var b: String = stack.pop_back()
				var a: String = stack.pop_back()
				stack.append("(%s%s%s)" % [a, op_sym.get(arg, "?"), b])
	var infix := stack[-1] if not stack.is_empty() else "<empty>"
	return "clamp(%s, %d, %d)" % [infix, spec.get("lower", 0), spec.get("upper", 0)]
