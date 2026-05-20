## 세이브/로드 (평문 JSON).
##
## 원본은 DES 암호화 (`StaticUtil::SaveEncryptFile` / `LoadDecryptFile`,
## key=`__DES_KEY__`) 를 썼지만 리메이크에서는 평문 JSON 으로 단순화.
## 사용자 데이터 디렉토리: `user://hero5_save_<slot>.json`
class_name H5SaveManager
extends RefCounted

const SAVE_VERSION := 1
const MAX_SLOTS := 8
const AUTO_SLOT := 7   # slot 7 은 자동 저장 전용


static func save_path(slot: int) -> String:
	return "user://hero5_save_%d.json" % slot


static func make_payload(state: Dictionary) -> Dictionary:
	var inv: Array = state.get("inventory", [])
	# Round 91: skill_levels + stat_points + Sorcerer/Gunner combo state + active
	# effect arrays 추가 (이전엔 누락되어 quick_save → quick_load 가 stat/combo
	# 상태를 잃음).
	return {
		"version": SAVE_VERSION,
		"timestamp": Time.get_datetime_string_from_system(),
		"play_time_sec": int(state.get("play_time_sec", 0)),
		"scene_id": state.get("scene_id", 0),
		"map_id": state.get("map_id", 0),
		"player": {
			"x": state.get("player_x", 0),
			"y": state.get("player_y", 0),
			"dir": state.get("player_dir", 0),
			"class_id": state.get("class_id", 0),
			"hp": state.get("hp", 100),
			"max_hp": state.get("max_hp", 100),
			"sp": state.get("sp", 100),
			"max_sp": state.get("max_sp", 100),
			"level": state.get("level", 1),
			"exp": state.get("exp", 0),
			"gold": state.get("gold", 0),
			"str": state.get("stat_str", 0),
			"dex": state.get("stat_dex", 0),
			"int": state.get("stat_int", 0),
			"con": state.get("stat_con", 0),
			"stat_points": state.get("stat_points", 0),
		},
		"inventory": inv,
		"inventory_count": inv.size(),
		"equipment": state.get("equipment", []),
		"unlocked_skills": state.get("unlocked_skills", []),
		"skill_levels": state.get("skill_levels", {}),
		"gunner_combo": state.get("gunner_combo", 0),
		"gunner_max_combo": state.get("gunner_max_combo", 4),
		"gunner_ammo": state.get("gunner_ammo", 0),
		"active_curses": state.get("active_curses", []),
		"active_buffs": state.get("active_buffs", []),
		"active_stances": state.get("active_stances", []),
		"flags": state.get("flags", {}),
		"quest": state.get("quest", {}),
		"mission": state.get("mission", {}),
	}


static func save(slot: int, state: Dictionary) -> bool:
	if slot < 0 or slot >= MAX_SLOTS:
		push_error("invalid save slot: %d" % slot)
		return false
	var payload := make_payload(state)
	var f := FileAccess.open(save_path(slot), FileAccess.WRITE)
	if f == null:
		push_error("cannot open save file for writing")
		return false
	f.store_string(JSON.stringify(payload, "  "))
	return true


static func load_slot(slot: int) -> Dictionary:
	var p := save_path(slot)
	if not FileAccess.file_exists(p):
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if not data is Dictionary:
		return {}
	if int(data.get("version", 0)) != SAVE_VERSION:
		push_warning("save version mismatch (slot %d): %s" % [slot, data.get("version")])
	return data


static func list_slots() -> Array:
	var out: Array = []
	for i in MAX_SLOTS:
		var p := save_path(i)
		if FileAccess.file_exists(p):
			var data = load_slot(i)
			out.append({
				"slot": i,
				"timestamp": data.get("timestamp", ""),
				"play_time_sec": data.get("play_time_sec", 0),
				"scene_id": data.get("scene_id", 0),
				"player": data.get("player", {}),
				"inventory_count": data.get("inventory_count", 0),
			})
	return out


## 자동 저장 (전용 slot 7) — 일정 간격으로 호출.
static func auto_save(state: Dictionary) -> bool:
	return save(AUTO_SLOT, state)


## 가장 오래된 slot (timestamp 기준) 찾기.
static func oldest_slot() -> int:
	var oldest_time = ""
	var oldest_idx = -1
	for i in MAX_SLOTS:
		var p := save_path(i)
		if not FileAccess.file_exists(p): return i  # 빈 슬롯 우선
		var data = load_slot(i)
		var ts = data.get("timestamp", "")
		if oldest_idx < 0 or ts < oldest_time:
			oldest_time = ts; oldest_idx = i
	return max(0, oldest_idx)


static func delete_slot(slot: int) -> bool:
	var p := save_path(slot)
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
		return true
	return false


# =============================================================================
# Round 49 — 원본 binary save 포맷 (H_*.sav / SL_*.sav) read/write
#
# Round 41-43 의 SAVE_FORMAT.md 분석 결과를 GDScript 로 구현. 원본 게임의
# save 파일과 binary-compatible 한 직렬화 — DES 미적용, plain bytes.
#
# 사용 시점:
#   - 원본 .sav 파일을 import (디바이스에서 추출한 save 데이터를 Godot 로드)
#   - 원본 게임으로 export (Godot save 를 안드로이드 원본에 inject)
# =============================================================================

const H_SAV_SIZE := 0x20c   # H_*.sav 총 사용 영역 (524 byte)


## H_*.sav binary writer.
##
## state 의 필드를 SAVE_FORMAT.md § 3.1 layout 에 맞춰 직렬화.
##
## 입력 state dict 필드 (모두 optional, 미제공 시 0):
##   field_f0:u32, class_id:u8, hero_22d:u8, gold:u32,
##   stats:Array[8 u16] (HP/MP/STR/DEX/CON/INT + 2),
##   skill_buff:PackedByteArray(43), equip:PackedByteArray(7),
##   field_4c:u32, field_60:u8, skill_slots:Array (10 records × 41B),
##   timestamp_create:int (u64 unix-like), timestamp_update:int
static func serialize_hero_save(state: Dictionary) -> PackedByteArray:
	var buf := PackedByteArray()
	buf.resize(H_SAV_SIZE)
	# 모두 0 init (resize 시 자동)

	# +0x0..3 u32 → HERO+0xf0
	_put_u32_le(buf, 0x00, int(state.get("field_f0", 0)))
	# +0x4 u8 = class_id (HERO+0x22c, Round 13)
	buf[0x04] = int(state.get("class_id", 0)) & 0xff
	# +0x5 u8 (HERO+0x22d)
	buf[0x05] = int(state.get("hero_22d", 0)) & 0xff
	# +0x6..9 u32 = EXP/gold
	_put_u32_le(buf, 0x06, int(state.get("gold", 0)))
	# +0xa..0x19 = 8 × u16 stat block (HP/MP/STR/DEX/CON/INT + 2)
	var stats: Array = state.get("stats", [0,0,0,0,0,0,0,0])
	for i in range(8):
		var v: int = int(stats[i]) if i < stats.size() else 0
		_put_u16_le(buf, 0x0a + i * 2, v)
	# +0x1a..0x44 = 43 bytes skill/buff state
	var sb: PackedByteArray = state.get("skill_buff", PackedByteArray())
	for i in range(min(sb.size(), 0x2b)):
		buf[0x1a + i] = sb[i]
	# +0x45..0x4b = 7 × u8 equip slot
	var eq: PackedByteArray = state.get("equip", PackedByteArray())
	for i in range(min(eq.size(), 7)):
		buf[0x45 + i] = eq[i]
	# +0x4c..0x4f u32
	_put_u32_le(buf, 0x4c, int(state.get("field_4c", 0)))
	# +0x50..0x5f (16 bytes, sub-block)
	var sb2: PackedByteArray = state.get("field_50_block", PackedByteArray())
	for i in range(min(sb2.size(), 16)):
		buf[0x50 + i] = sb2[i]
	# +0x60 u8 (record count for next loop)
	buf[0x60] = int(state.get("field_60", 0)) & 0xff
	# +0x61..(0x60+0x29*10) = 10 × 41B skill slot records
	var slots: Array = state.get("skill_slots", [])
	for i in range(min(slots.size(), 10)):
		var rec: PackedByteArray = slots[i] if slots[i] is PackedByteArray else PackedByteArray()
		for j in range(min(rec.size(), 0x29)):
			buf[0x61 + i * 0x29 + j] = rec[j]
	# +0x1fc..0x203 u64 timestamp #1 (creation)
	_put_u64_le(buf, 0x1fc, int(state.get("timestamp_create", 0)))
	# +0x204..0x20b u64 timestamp #2 (last save)
	_put_u64_le(buf, 0x204, int(state.get("timestamp_update", 0)))
	return buf


## H_*.sav binary reader. serialize 의 역.
static func deserialize_hero_save(data: PackedByteArray) -> Dictionary:
	if data.size() < H_SAV_SIZE:
		push_warning("H sav too small: %d < %d" % [data.size(), H_SAV_SIZE])
	var stats: Array = []
	for i in range(8):
		stats.append(_get_u16_le(data, 0x0a + i * 2))
	var skill_buff := PackedByteArray()
	skill_buff.resize(0x2b)
	for i in range(0x2b):
		if 0x1a + i < data.size():
			skill_buff[i] = data[0x1a + i]
	var equip := PackedByteArray()
	equip.resize(7)
	for i in range(7):
		if 0x45 + i < data.size():
			equip[i] = data[0x45 + i]
	var field_50_block := PackedByteArray()
	field_50_block.resize(16)
	for i in range(16):
		if 0x50 + i < data.size():
			field_50_block[i] = data[0x50 + i]
	var slots: Array = []
	for i in range(10):
		var rec := PackedByteArray()
		rec.resize(0x29)
		for j in range(0x29):
			var off := 0x61 + i * 0x29 + j
			if off < data.size():
				rec[j] = data[off]
		slots.append(rec)
	return {
		"field_f0": _get_u32_le(data, 0x00),
		"class_id": data[0x04] if data.size() > 0x04 else 0,
		"hero_22d": data[0x05] if data.size() > 0x05 else 0,
		"gold": _get_u32_le(data, 0x06),
		"stats": stats,
		"skill_buff": skill_buff,
		"equip": equip,
		"field_4c": _get_u32_le(data, 0x4c),
		"field_50_block": field_50_block,
		"field_60": data[0x60] if data.size() > 0x60 else 0,
		"skill_slots": slots,
		"timestamp_create": _get_u64_le(data, 0x1fc),
		"timestamp_update": _get_u64_le(data, 0x204),
	}


## SL_*.sav binary writer (헤더만 확정 — Round 42 의 24 offset 정밀 일치 영역).
##
## 입력 state dict 필드:
##   class_id:u8 (0-4), level:u8 (1-25), hero_22d:u8,
##   pos_x:s32, pos_y:s32, playtime_ms:i64, scene_idx:u32,
##   state_flag:u8
##
## file[0] = level*10 + class_id packing (Round 43 의 핵심 발견).
const SL_SAV_HEADER_SIZE := 0x17   # +0x00..+0x16 header (확정 영역)


static func serialize_slot_save(state: Dictionary) -> PackedByteArray:
	var buf := PackedByteArray()
	buf.resize(SL_SAV_HEADER_SIZE)
	# +0x0 = level * 10 + class_id (Round 43 packing 규칙)
	var class_id: int = int(state.get("class_id", 0)) & 0xff
	var level: int = int(state.get("level", 1)) & 0xff
	buf[0x00] = (level * 10 + class_id) & 0xff
	# +0x1 (HERO+0x22d)
	buf[0x01] = int(state.get("hero_22d", 0)) & 0xff
	# +0x2..0x5 u32 = GetX (OBJECT::GetX)
	_put_u32_le(buf, 0x02, int(state.get("pos_x", 0)))
	# +0x6..0x9 u32 = GetY
	_put_u32_le(buf, 0x06, int(state.get("pos_y", 0)))
	# +0xa..0x11 u64 = playtime (MC_knlCurrentTime delta)
	_put_u64_le(buf, 0x0a, int(state.get("playtime_ms", 0)))
	# +0x12..0x15 u32 = scene_idx (HERO_class+0xa0)
	_put_u32_le(buf, 0x12, int(state.get("scene_idx", 0)))
	# +0x16 u8 = state flag (HERO_class+0x8b)
	buf[0x16] = int(state.get("state_flag", 0)) & 0xff
	return buf


static func deserialize_slot_save(data: PackedByteArray) -> Dictionary:
	if data.size() < SL_SAV_HEADER_SIZE:
		push_warning("SL sav too small: %d" % data.size())
		return {}
	var packed: int = data[0x00]
	return {
		"class_id": packed % 10,   # Round 43: load 가 % 10 / / 10 분리
		"level": int(packed / 10),
		"hero_22d": data[0x01],
		"pos_x": _get_u32_le(data, 0x02),
		"pos_y": _get_u32_le(data, 0x06),
		"playtime_ms": _get_u64_le(data, 0x0a),
		"scene_idx": _get_u32_le(data, 0x12),
		"state_flag": data[0x16],
	}


# =============================================================================
# byte helpers (LE little-endian, Hero5 원본 포맷 일치)
# =============================================================================

static func _put_u16_le(buf: PackedByteArray, off: int, val: int) -> void:
	buf[off + 0] = val & 0xff
	buf[off + 1] = (val >> 8) & 0xff


static func _put_u32_le(buf: PackedByteArray, off: int, val: int) -> void:
	buf[off + 0] = val & 0xff
	buf[off + 1] = (val >> 8) & 0xff
	buf[off + 2] = (val >> 16) & 0xff
	buf[off + 3] = (val >> 24) & 0xff


static func _put_u64_le(buf: PackedByteArray, off: int, val: int) -> void:
	for i in range(8):
		buf[off + i] = (val >> (i * 8)) & 0xff


static func _get_u16_le(buf: PackedByteArray, off: int) -> int:
	if off + 2 > buf.size(): return 0
	return buf[off] | (buf[off + 1] << 8)


static func _get_u32_le(buf: PackedByteArray, off: int) -> int:
	if off + 4 > buf.size(): return 0
	return buf[off] | (buf[off + 1] << 8) | (buf[off + 2] << 16) | (buf[off + 3] << 24)


static func _get_u64_le(buf: PackedByteArray, off: int) -> int:
	if off + 8 > buf.size(): return 0
	var lo: int = _get_u32_le(buf, off)
	var hi: int = _get_u32_le(buf, off + 4)
	return lo | (hi << 32)
