## 게임 데이터 (csv .dat) 로더 (싱글톤).
##
## convert_h5_csv.py 산출 JSON 파일들을 메모리에 로드.
## 각 테이블 = {count, records: [{name, extra_hex}]}.
extends Node

const DATA_DIR := "res://assets/gamedata/"

var tables: Dictionary = {}   # 테이블명 → {count, records}


func _ready() -> void:
	_load_all()


func _load_all() -> void:
	var idx_path := DATA_DIR + "_index.json"
	if not FileAccess.file_exists(idx_path):
		push_warning("gamedata index not found: %s" % idx_path)
		return
	var f := FileAccess.open(idx_path, FileAccess.READ)
	var idx = JSON.parse_string(f.get_as_text())
	if not idx is Dictionary: return
	var n := 0
	for entry in idx.get("tables", []):
		var name = entry[0] if entry is Array else entry.get("0", "")
		# the JSON dump 형식이 [name, count] 배열일 수 있음
		var key = name if typeof(name) == TYPE_STRING else str(name)
		var fname = key.replace("/", "_").replace(".dat", ".json")
		var path = DATA_DIR + fname
		if not FileAccess.file_exists(path): continue
		var ff := FileAccess.open(path, FileAccess.READ)
		var data = JSON.parse_string(ff.get_as_text())
		if data is Dictionary:
			tables[key] = data
			n += 1
	print("[GameData] loaded %d tables" % n)


## 테이블 → 이름 배열만 추출 (인벤토리/메뉴 표시용).
func names(table_name: String) -> Array:
	var t = tables.get(table_name, {})
	var out: Array = []
	for r in t.get("records", []):
		out.append(r.get("name", ""))
	return out


## 캐릭터 클래스 이름 (워리어/로그/...) 5개.
func class_names() -> Array:
	return names("c/csv/class.dat")


## 사용 가능한 캐릭터 이름.
func char_names() -> Array:
	return names("c/csv/name.dat")


## 메뉴 텍스트 (UI 라벨).
func menu_text(idx: int) -> String:
	var arr = names("c/csv/menu_text.dat")
	if idx >= 0 and idx < arr.size():
		return arr[idx]
	return ""


## 인게임 텍스트 (시스템 메시지 등).
func ingame_text(idx: int) -> String:
	var arr = names("c/csv/ingame_text.dat")
	if idx >= 0 and idx < arr.size():
		return arr[idx]
	return ""


## 클래스 스킬 목록 (class_id 0..4).
func skills_for_class(class_id: int) -> Array:
	return names("c/csv/skill_%02d.dat" % class_id)


## 아이템 목록 (slot 0..3 = 무기/방어/소비/기타 추정).
func items_in_slot(slot: int) -> Array:
	return names("c/csv/item_%02d.dat" % slot)


## 드롭 테이블 — droptable.dat 의 record name (몬스터 ID → drop 매핑 추정).
func drop_table() -> Array:
	return names("c/csv/droptable.dat")


## 상점 / 대장간.
func shop_inventory(shop_id: int) -> Array:
	return names("c/csv/shop_%d.dat" % shop_id)


func smith_recipes(smith_id: int) -> Array:
	return names("c/csv/smith_%d.dat" % smith_id)


## 적 g_data id → enemy_table.json 의 인덱스 (직접 매핑).
func enemy_stats(idx: int) -> Dictionary:
	if not _enemy_table_cache.is_empty():
		return _enemy_table_cache[idx] if idx < _enemy_table_cache.size() else {}
	var p := "res://assets/gamedata/enemy_table.json"
	if FileAccess.file_exists(p):
		var f := FileAccess.open(p, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if data is Array:
			_enemy_table_cache = data
			return _enemy_table_cache[idx] if idx < _enemy_table_cache.size() else {}
	return {}


var _enemy_table_cache: Array = []
var _skills_cache: Dictionary = {}


## skill 설명에서 `}#NN%}` 등 템플릿 변수를 stat 값으로 치환.
##   예: "재사용대기 }#09초|" + stats_u16[9]=600 → "재사용대기 600초|"
##       "근접공격력 }#05%|" + stats_u16[5]=120 → "근접공격력 120%|"
func resolve_skill_desc(class_id: int, skill_id: int) -> String:
	if _skills_cache.is_empty():
		var p := "res://assets/gamedata/skills.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_skills_cache = JSON.parse_string(f.get_as_text()) or {}
	var arr = _skills_cache.get("class_%d" % class_id, [])
	if skill_id < 0 or skill_id >= arr.size():
		return ""
	var skill = arr[skill_id]
	var desc = skill.get("desc", "")
	var stats: Array = skill.get("stats_u16", [])
	# regex 대신 단순 치환
	var result = desc
	for i in stats.size():
		result = result.replace("}#%02d" % i, "}%d" % stats[i])
		result = result.replace("#%02d" % i, str(stats[i]))
	return result
