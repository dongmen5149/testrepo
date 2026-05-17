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


## quest_NN.dat 의 한글 대사 (453 records 중 idx 번째 의 첫 한글 발췌).
##   episode 0/1/2 에 해당.
var _quest_text_cache: Array = []

func quest_dialogue(idx: int, episode: int = 0) -> String:
	if _quest_text_cache.is_empty():
		var p := "res://assets/gamedata/quests_text.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_quest_text_cache = JSON.parse_string(f.get_as_text()) or []
	if episode >= _quest_text_cache.size(): return ""
	var ep = _quest_text_cache[episode]
	var records = ep.get("records", [])
	if idx < 0 or idx >= records.size(): return ""
	var korean: Array = records[idx].get("korean", [])
	if korean.is_empty(): return ""
	# 첫 두 한글 발췌 (전체는 너무 길어 dialog 한 줄 분량으로 자름)
	var combined = " ".join(korean[:3])
	return combined.substr(0, 80)


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
var _items_cache: Dictionary = {}


## items.json 의 slot_N 구조 캐시.
func _load_items() -> Dictionary:
	if _items_cache.is_empty():
		var p := "res://assets/gamedata/items.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_items_cache = JSON.parse_string(f.get_as_text()) or {}
	return _items_cache


## items.json 의 slot_N 카테고리 메타 (decode_h5_item.py SLOT_META 와 일치).
## _meta.category_dispatch[slot_str] = {category, kind, runtime_struct, runtime_size}.
func item_slot_meta(slot: int) -> Dictionary:
	var data = _load_items()
	var meta_root = data.get("_meta", {})
	var dispatch = meta_root.get("category_dispatch", {})
	return dispatch.get(str(slot), {})


## 아이템 stats 해석 (slot 별 의미 다름).
##   slot 0..10 (무기/방어구/액세서리): stats[0]=price, stats[7]=attack_power
##   slot 11 (battle_use 포션):           stats[0]=price, stats[2..5]=effect refs
##   slot 13 (orb):                       stats[0]=price
##   slot 16-17 (skill_book):             stats[0]=price, 다른 stats=skill_id 참조
## 카테고리 메타: ITEM_STRUCT.md 의 ItemTable::GetItemTableInfo dispatch 표 참조.
func item_stat(slot: int, idx: int) -> Dictionary:
	var data = _load_items()
	var arr = data.get("slot_%d" % slot, [])
	if idx < 0 or idx >= arr.size():
		return {}
	var it = arr[idx]
	var stats: Array = it.get("stats_u16", [])
	# 신규 디코더: it.price 직접 추출 (없으면 stats[0]).
	var price = it.get("price", stats[0] if stats.size() > 0 else 0)
	var meta = item_slot_meta(slot)
	var info := {
		"name": it.get("name", ""),
		"prefix": it.get("prefix", 0),
		"price": price,
		"category": meta.get("category", "?"),
		"kind": meta.get("kind", "?"),
	}
	# 카테고리별 추가 의미
	if meta.get("category") == "equip":
		info["attack"] = stats[7] if stats.size() > 7 else 0
		info["sub_id"] = stats[6] if stats.size() > 6 else 0
	return info


## items.json 의 모든 slot 을 순회하여 name → (slot, idx, record) 매핑 캐시 구축.
##
## status_panel/refine_panel 의 분류·tooltip·equip validation 이 모두
## 이 lookup 으로 정확한 record fields (subtype/class_mask/level_limit/tier_flags/
## refine_count/...) 에 접근. 한국어 substring 매칭 (Round 50 이전) 을 대체.
var _item_name_index: Dictionary = {}

func _build_item_index() -> void:
	if not _item_name_index.is_empty(): return
	var data = _load_items()
	for slot in range(19):
		var arr: Array = data.get("slot_%d" % slot, [])
		for i in arr.size():
			var rec: Dictionary = arr[i]
			var nm: String = str(rec.get("name", ""))
			if nm.is_empty(): continue
			# 중복 시 첫 등장 우선 (slot 낮은 쪽 = 무기 → 방어구 순)
			if not _item_name_index.has(nm):
				_item_name_index[nm] = {"slot": slot, "idx": i, "record": rec}


## item 이름 → {slot, idx, kind, category, level_limit, class_mask, class_label,
## tier_flags, tier_label, refine_count, stat_a, stat_b, ...}. 미발견 시 빈 dict.
##
## kind/category 는 _meta.category_dispatch (decode_h5_item.py SLOT_META) 매핑.
## tier_label = Round 24 의 val_15f upper 3 bit 라벨 (legendary/rare/gem/common).
## class_mask = Round 16 의 val_15f lower 5 bit (1=W,2=R,4=G,8=K,16=S).
func item_lookup(name: String) -> Dictionary:
	_build_item_index()
	var hit: Dictionary = _item_name_index.get(name, {})
	if hit.is_empty(): return {}
	var slot: int = hit["slot"]
	var rec: Dictionary = hit["record"]
	var meta: Dictionary = item_slot_meta(slot)
	var info := {
		"slot": slot,
		"idx": hit["idx"],
		"name": name,
		"category": meta.get("category", "?"),
		"kind": meta.get("kind", "?"),
	}
	# equip 카테고리 (slot 0-10) 전용 fields
	if meta.get("category") == "equip":
		info["level_limit"] = int(rec.get("level_limit", 0))
		info["class_mask"] = int(rec.get("class_mask", 0))
		info["class_label"] = str(rec.get("class_label", ""))
		info["tier_flags"] = int(rec.get("tier_flags", 0))
		info["tier_label"] = str(rec.get("tier_label", ""))
		info["refine_count"] = int(rec.get("refine_count", 0))
		info["stat_a"] = int(rec.get("stat_a", 0))
		info["stat_b"] = int(rec.get("stat_b", 0))
		info["sub_count"] = int(rec.get("sub_count", 0))
		info["price"] = int(rec.get("price", 0))
		info["sockets"] = rec.get("sockets", [])
		info["subtype"] = int(rec.get("subtype", 0))
		info["price"] = int(rec.get("price", 0))
	elif meta.get("category") == "battle_use":
		# slot_11 포션류: Round 23 의 4 byte ext (effect_type/success_rate/value/duration)
		info["effect_type"] = int(rec.get("effect_type", 0))
		info["success_rate"] = int(rec.get("success_rate", 100))
		info["effect_value"] = int(rec.get("effect_value", 0))
		info["duration"] = int(rec.get("duration", 0))
	elif meta.get("category") == "skill_book":
		# slot_16/17: Round 21 의 4 byte (class_id/skill_index/skill_level/required_level)
		info["class_id"] = int(rec.get("class_id", 0))
		info["skill_index"] = int(rec.get("skill_index", 0))
		info["skill_level"] = int(rec.get("skill_level", 1))
		info["required_level"] = int(rec.get("required_level", 0))
		info["price"] = int(rec.get("price", 0))
	else:
		info["price"] = int(rec.get("price", 0))
	return info


## 5-class mask (Round 16: W=1/R=2/G=4/K=8/S=16) 가 class_id 를 허용하는지.
## class_mask == 0 = "모두 가능" (소비/소재 등 non-equip).
func class_mask_allows(class_mask: int, class_id: int) -> bool:
	if class_mask == 0: return true
	return (class_mask & (1 << class_id)) != 0


## kind → equipment slot index (GameState.SLOT_*). 미매칭 시 -1.
## status_panel._slot_for_kind 가 한국어 substring 매칭 (Round 50 이전) 대신 사용.
## 현재 GameState 는 6 슬롯 (Weapon/Armor/Helmet/Boots/Acc1/Acc2). shield/spirit 은
## Acc 슬롯에 임시 매핑 (실제 EquipItem cat 0-6 7 슬롯과 1 슬롯 차이 — TODO).
func equip_slot_for_kind(kind: String) -> int:
	match kind:
		"weapon", "weapon_2", "weapon_3", "weapon_4": return GameState.SLOT_WEAPON
		"armor": return GameState.SLOT_ARMOR
		"helmet": return GameState.SLOT_HELMET
		"boots": return GameState.SLOT_BOOTS
		"accessory": return GameState.SLOT_ACC1
		"accessory_2": return GameState.SLOT_ACC2
		"shield", "spirit": return GameState.SLOT_ACC2
	return -1


## filter 카테고리 ("weapon"/"armor"/"potion"/"misc") 에 매칭되는지.
## items.json 의 정확한 kind 사용 (Round 50 이전의 substring 매칭 정정).
func item_matches_filter(name: String, filter_key: String) -> bool:
	if filter_key == "all": return true
	var info = item_lookup(name)
	if info.is_empty():
		# items.json 에 없으면 fallback to substring
		return true if filter_key == "misc" else false
	var kind: String = info.get("kind", "")
	match filter_key:
		"weapon":
			return kind in ["weapon", "weapon_2", "weapon_3", "weapon_4"]
		"armor":
			return kind in ["armor", "helmet", "boots", "shield", "accessory", "accessory_2", "spirit"]
		"potion":
			return kind == "potion"
		"misc":
			return kind in ["orb", "material", "material_2", "recipe", "skill_book_wr", "skill_book_gk", "cash_item"]
	return false


## (cat, idx) → item name lookup (Round 53). recipe ingredient/result 가 cat/idx 형태로
## 저장돼있어 mix_panel 이 이름 조회용으로 사용.
##
## cat = items.json 의 slot_N 인덱스, idx = 그 slot 의 record idx.
func item_name_at(cat: int, idx: int) -> String:
	var data = _load_items()
	var arr: Array = data.get("slot_%d" % cat, [])
	if idx < 0 or idx >= arr.size(): return ""
	return str(arr[idx].get("name", ""))


## slot_15 mix_book recipe 전체 리스트 (Round 25, 116 entries) — 각 entry 는
## items.json 의 record dict (recipe 필드 포함). mix_panel 의 ItemList 소스.
func mix_recipes() -> Array:
	var data = _load_items()
	return data.get("slot_15", [])


## recipe entry 의 ingredient/result 를 이름 + 갯수 로 풀어서 반환.
## {"ingredients": [{"name", "count", "cat", "idx"}, ...], "result": {"name", "cat", "idx"}, "success_rate"}.
func parse_recipe(rec: Dictionary) -> Dictionary:
	var recipe: Dictionary = rec.get("recipe", {})
	if recipe.is_empty(): return {}
	var ings: Array = []
	for key in ["ing1", "ing2", "ing3"]:
		var ing = recipe.get(key)
		if ing == null: continue
		if not (ing is Dictionary): continue
		var c = int(ing.get("cat", 0))
		var i = int(ing.get("idx", 0))
		ings.append({
			"cat": c, "idx": i,
			"count": int(ing.get("count", 1)),
			"name": item_name_at(c, i),
		})
	var result_cat = int(recipe.get("result_cat", 0))
	var result_idx = int(recipe.get("result_idx", 0))
	return {
		"ingredients": ings,
		"result": {
			"cat": result_cat, "idx": result_idx,
			"name": item_name_at(result_cat, result_idx),
		},
		"success_rate": int(recipe.get("success_rate", 100)),
	}


## items.json slot_12 의 53 orb record 반환 (Round 54).
##
## orb 1개 = item record. orb_idx (0..52) 가 record idx + 1 - 1 = idx 그 자체.
## socket 에 저장될 때는 (orb_idx + 1) 로 encode (0 = 빈 슬롯 의미).
func orb_records() -> Array:
	var data = _load_items()
	return data.get("slot_12", [])


## orb_idx → 이름. orb_panel 의 socket 표시용.
func orb_name(orb_idx: int) -> String:
	var orbs = orb_records()
	if orb_idx < 0 or orb_idx >= orbs.size(): return ""
	return str(orbs[orb_idx].get("name", ""))


## orb_idx 의 stat bonus (equipment_bonus 에 합산). Round 26 의 ApplyOrbCombine
## 정확한 stat 식은 별도 RE 필요 — 합리적 단순화 (Round 54):
##   - orb price 가 강도 proxy (price 0 = test orb / price > 0 = real orb)
##   - price 100 → +1, price 200 → +2, ...  (단순 / 100 stepping)
func orb_bonus_for(orb_idx: int) -> int:
	var orbs = orb_records()
	if orb_idx < 0 or orb_idx >= orbs.size(): return 0
	var price = int(orbs[orb_idx].get("price", 0))
	if price <= 0: return 0
	# 등비 단순화: price 의 자릿수 - 1 (100→1, 1000→2, ...)
	# 실제로는 prefix/val_134/val_135 의 combination 일 가능성
	return max(1, int(round(log(max(1, price)) / log(10))))


## orb idx → 그룹 (Round 26: 3 그룹 × 13). 단순 매핑: idx / 13.
func orb_group(orb_idx: int) -> int:
	return orb_idx / 13


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
