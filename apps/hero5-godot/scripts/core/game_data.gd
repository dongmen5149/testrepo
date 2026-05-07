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
