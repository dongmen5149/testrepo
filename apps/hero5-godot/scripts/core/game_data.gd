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


## smithtable.json 의 NPC blacksmith recipe 캐시 (Round 32 / Round 55).
##
## Round 28 의 ApplyNormalMix 가 MixSmithTableInfo* 별도 데이터 사용.
## smith_0/1/2.dat = 각 96 entries (option_grade 별 — 0=common, 1=set craft, 2=advanced).
## 총 288 records (모두 success_rate 75%). mix_book 의 csv slot_15 와 다른 데이터원.
var _smith_cache: Dictionary = {}

func _load_smithtable() -> Dictionary:
	if _smith_cache.is_empty():
		var p := "res://assets/gamedata/smithtable.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_smith_cache = JSON.parse_string(f.get_as_text()) or {}
	return _smith_cache


## smith_id (0..2) 의 named recipe 만 반환 (NONE / 빈 record 제외).
func smith_table(smith_id: int) -> Array:
	var data = _load_smithtable()
	var tbl: Dictionary = data.get("smith_%d" % smith_id, {})
	var entries: Array = tbl.get("entries", [])
	var out: Array = []
	for e in entries:
		var rec: Dictionary = e
		var nm = str(rec.get("name", ""))
		if nm.is_empty() or nm == "NONE": continue
		var recipe: Dictionary = rec.get("recipe", {})
		if recipe.is_empty(): continue
		# ing1 도 없는 placeholder 도 제거
		if recipe.get("ing1") == null: continue
		out.append(rec)
	return out


## smith recipe (smith_NN.dat 의 row) → mix_panel 의 parse_recipe 와 동일 schema.
## smithtable.json 은 이미 recipe = {ing1/2/3, result_cat/idx, success_rate} 형태이므로
## parse_recipe 를 재활용 가능.
func parse_smith_recipe(rec: Dictionary) -> Dictionary:
	return parse_recipe(rec)


## smith_0/1/2 전체 named recipe 합쳐 반환 — blacksmith UI 의 list 소스.
## 각 entry 에 _smith_id (0/1/2), _grade label 부착.
func smith_all() -> Array:
	var out: Array = []
	for sid in range(3):
		for rec in smith_table(sid):
			var copy: Dictionary = rec.duplicate()
			copy["_smith_id"] = sid
			copy["_grade"] = ["기본", "세트", "고급"][sid] if sid < 3 else "?"
			out.append(copy)
	return out


## class_id → 해당 클래스의 skill_book 이 들어있는 items.json slot (Round 21).
##
## HERO::IfLearnSkill 공식: `(class_id / 2) + 16`. Warrior(0)/Rogue(1) → slot_16,
## Gunslinger(2)/Knight(3) → slot_17. Sorcerer(4) 는 stub (dead code, Round 22).
func skill_book_slot_for_class(class_id: int) -> int:
	return (class_id / 2) + 16


## 해당 class 의 모든 skill book record (slot_16 또는 slot_17 에서 class_id 일치 필터).
##
## slot_16 = Warrior(0)+Rogue(1) 합쳐 95 books, slot_17 = Gunslinger(2)+Knight(3) 98 books.
## 같은 slot 안에서도 두 클래스 책이 섞여있어 record.class_id 로 추가 필터링.
func skill_books_for_class(class_id: int) -> Array:
	var slot = skill_book_slot_for_class(class_id)
	var data = _load_items()
	var arr: Array = data.get("slot_%d" % slot, [])
	var out: Array = []
	for r in arr:
		if int(r.get("class_id", -1)) == class_id:
			out.append(r)
	return out


## skill_book record 의 사람 친화 detail.
##
## {name, class_id, skill_index, skill_level, required_level, price, desc}
## desc = resolve_skill_desc(class_id, skill_index) 결과 (LV stat 치환).
func skill_book_detail(rec: Dictionary) -> Dictionary:
	var cid = int(rec.get("class_id", 0))
	var sidx = int(rec.get("skill_index", 0))
	return {
		"name": str(rec.get("name", "")),
		"class_id": cid,
		"skill_index": sidx,
		"skill_level": int(rec.get("skill_level", 1)),
		"required_level": int(rec.get("required_level", 0)),
		"price": int(rec.get("price", 0)),
		"desc": resolve_skill_desc(cid, sidx),
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


## Round 75 → R77: skill record 의 R72/R73 발견 fields 를 사람 친화 dict 로 노출.
##
## R77 (HERO::LoadResSkillInfo @0x8bba4 full disasm) 결과 정정:
## - file-loaded 영역 (+0x00..+0x43): R72/R73 의 5 field 정확 매핑 확정
## - runtime 영역 (+0x44..+0x57): LoadResSkillInfo 가 file 에서 채우지 않음
##   → kb_idx/shock_count/max_combo/sp_delta/knight_threshold 는
##     skills.json 의 stats_u16 와 무관 (별도 init source 추적 필요, R78+)
##
## 정확 매핑 (file-loaded only, R77 검증 완료):
##   +0x28 (effect_type):       stats sub-rel 0x1a — 0=NO_HIT, 1·2=curse, 3·5=buff, 4=stance
##   +0x30 (dynamic_formula_id): stats sub-rel 0x26 — case 5 (shock) Formula::calc id
##   +0x3a (special_dispatch):   stats sub-rel 0x2b — case 1+2 의 0x34/0x37 special path key
##   +0x3c (formula_id_1):       stats sub-rel 0x2d — 1st Formula::calc id
##   +0x3d (formula_id_2):       stats sub-rel 0x2e — 2nd Formula::calc id
##
## 잠정 (runtime 영역, R78+ 정확화 필요):
##   +0x44 (knockback_idx):      class 3 KNIGHT motion 23 path KB index (R69)
##   +0x46 (shock_count):        case 5 dispatch (R73)
##   +0x48 (max_combo):          GUNNER skill slot 5 combo 한도 (R73)
##   +0x4a (sp_delta):           case 0 NO_HIT path 의 IncreaseSP 인자 (R72)
##   +0x4e (knight_threshold):   class 3 KNIGHT secondary check (R73)
##
## stats_u16 layout 은 skills.json 의 byte stream — 각 stat 가 2B 라 가정 시
## index = offset / 2. stats_u16 길이가 충분치 않으면 default 반환.
func skill_info(class_id: int, skill_id: int) -> Dictionary:
	if _skills_cache.is_empty():
		var p := "res://assets/gamedata/skills.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_skills_cache = JSON.parse_string(f.get_as_text()) or {}
		_ensure_spirit_skills_loaded()
	var arr = _skills_cache.get("class_%d" % class_id, [])
	if skill_id < 0 or skill_id >= arr.size():
		return {}
	var rec: Dictionary = arr[skill_id]
	# Round 87: class_5 (spirit) 는 _ensure_spirit_skills_loaded 가 R77 sub-rel offset
	# 으로 explicit field 채워둠 → stats_u16 추정 매핑 안 거치고 직접 사용.
	if class_id == 5 and rec.has("effect_type"):
		return {
			"name": rec.get("name", ""),
			"desc": rec.get("desc", ""),
			"effect_type": int(rec.get("effect_type", 0)),
			"dynamic_formula_id": int(rec.get("dynamic_formula_id", 0)),
			"special_dispatch": int(rec.get("special_dispatch", 0)),
			"formula_id_1": int(rec.get("formula_id_1", 0)),
			"formula_id_2": int(rec.get("formula_id_2", 0)),
			"primary_u16": int(rec.get("primary_u16", 0)),
			"secondary_u16": int(rec.get("secondary_u16", 0)),
			# R79 dead reads — spirit data 에도 부재이지만 호환 위해 0 반환
			"knockback_idx": 0,
			"shock_count": 0,
			"max_combo": 4,
			"sp_delta": 0,
			"knight_threshold": 0,
		}
	var stats: Array = rec.get("stats_u16", [])
	# 다른 class (0..3): R72/R73 byte offset → stats_u16 index 매핑 (추정).
	# skills.json 의 stats_u16 가 8 entries 만이라 OOB 시 default 0 반환 (R79 dead reads).
	var info := {
		"name": rec.get("name", ""),
		"desc": rec.get("desc", ""),
		"effect_type": _stat_at(stats, 14, 0),       # +0x28 / 2 = 0x14 — 추정
		"dynamic_formula_id": _stat_at(stats, 18, 0), # +0x30 / 2 = 0x18
		"special_dispatch": _stat_at(stats, 21, 0),   # +0x3a / 2 = 0x1d — 추정
		"formula_id_1": _stat_at(stats, 22, 0),       # +0x3c / 2 = 0x1e
		"formula_id_2": _stat_at(stats, 23, 0),       # +0x3d / 2 = 0x1e half — fallback
		"knockback_idx": _stat_at(stats, 26, 0),      # R79 dead
		"shock_count": _stat_at(stats, 27, 0),        # R79 dead
		"max_combo": _stat_at(stats, 28, 4),          # R79 dead
		"sp_delta": _stat_at(stats, 29, 0),           # R79 dead
		"knight_threshold": _stat_at(stats, 31, 0),   # R79 dead
	}
	return info


## stats array 의 index 위치 값을 안전하게 반환 (out-of-range 시 default).
func _stat_at(stats: Array, index: int, default: int) -> int:
	if index < 0 or index >= stats.size():
		return default
	return int(stats[index])


## skill 설명에서 `}#NN<unit>|` 등 템플릿 변수를 stat 값으로 치환.
##   예: "재사용대기 }#09초|" + stats_u16[9]=600 → "재사용대기 600초|"
##       "근접공격력 }#05%|" + stats_u16[5]=120 → "근접공격력 120%|"
## Round 105: stats_u16 의 값은 file 의 raw u16 LE stride 로 얻은 것인데,
## 실측 결과 placeholder `#NN` 이 참조하는 실제 stat 값과 일치하지 않음. 실
## source 는 Formula::calc 런타임 — R106+ 의 통합 작업 대상. R105 휴리스틱
## 가드: 값 > 500 시 `?` 로 표시.
const PLACEHOLDER_UNREASONABLE_THRESHOLD := 500

## Round 106→109: R75 convention 의 placeholder NN → 의미 label.
## R106 형식 `"공격%"` 는 desc 의 unit (`%`, `초`) 와 중복 노출 → R109 에서 unit
## 분리. desc 의 `}#NN<unit>|` 가 unit 을 보유하므로 label 은 의미만.
##   raw                placeholder 치환                    bracket 변환
##   `}#05%|`           `}?(공격)%|`                       `[?(공격)%]`  (R109)
##   `}#08초|`          `}?(지속)초|`                       `[?(지속)초]` (R109)
##                       (이전 R106: `[?(공격%)%]` / `[?(지속초)초]` — 단위 중복)
##
##   #04 → 효과 강도 (effect_pct)
##   #05 → damage 자릿수 (R57 convention, spirit/class 공통)
##   #06 → magic 자릿수
##   #07 → MP cost
##   #08 → duration (buff/curse 지속)
##   #09 → cooldown
##   #12 → 다목적 (배수/초/… — desc unit 으로 구분)
## 미매핑 NN 은 raw `?` 유지.
const PLACEHOLDER_LABELS := {
	4: "효과",
	5: "공격",
	6: "마법",
	7: "MP",
	8: "지속",
	9: "쿨",
	10: "값",
	11: "강화",
	12: "수치",
	13: "양",
}

## Round 108→109: placeholder NN → stat source (Formula::calc 우선, explicit field 차순).
## R105/R106 의 stats_u16[NN] 직접 치환은 file padding 과 불일치 — spirit 의
## primary_u16 / formula_id_1·2 / mp_cost·cooldown (R87) 및 FormulaVM 으로 해석.
## R109: #12 의 `primary_u16` 매핑 제거 — 폭발 `}#12초|` 가 damage% (300) 로
## 잘못 노출되던 케이스 차단. NN 미매핑 시 stats_u16[12] fallback → garbage 가드.
const PLACEHOLDER_STAT_SOURCE := {
	4: {"formula_key": "formula_id_2", "field": "secondary_u16"},
	5: {"formula_key": "formula_id_1", "field": "primary_u16"},
	6: {"formula_key": "formula_id_1", "field": "primary_u16"},
	7: {"field": "mp_cost"},
	8: {"formula_key": "formula_id_2", "field": "secondary_u16"},
	9: {"field": "cooldown"},
}


func _ensure_skills_cache_loaded() -> void:
	if _skills_cache.is_empty():
		var p := "res://assets/gamedata/skills.json"
		if FileAccess.file_exists(p):
			var f := FileAccess.open(p, FileAccess.READ)
			_skills_cache = JSON.parse_string(f.get_as_text()) or {}
	_ensure_spirit_skills_loaded()


func _skill_record(class_id: int, skill_id: int) -> Dictionary:
	_ensure_skills_cache_loaded()
	var arr: Array = _skills_cache.get("class_%d" % class_id, [])
	if skill_id < 0 or skill_id >= arr.size():
		return {}
	return arr[skill_id]


func _formula_vm() -> Node:
	return get_node_or_null("/root/FormulaVM")


## Round 108: Formula::calc 용 최소 player ctx (battle_system._player_ctx 축약).
func _placeholder_player_ctx() -> Dictionary:
	var atk: int = GameState.total_attack() if GameState.has_method("total_attack") else 10
	var def_v: int = GameState.total_defense() if GameState.has_method("total_defense") else 5
	return {
		"hp": GameState.hp,
		"max_hp": GameState.max_hp,
		"sp": GameState.sp,
		"max_sp": GameState.max_sp,
		"level": GameState.level,
		"str": GameState.stat_str,
		"dex": GameState.stat_dex,
		"int": GameState.stat_int,
		"con": GameState.stat_con,
		"atk": atk,
		"def": def_v,
		"557": GameState.level,
		"566": GameState.stat_str,
		"568": GameState.stat_dex,
		"570": GameState.stat_con,
		"572": GameState.stat_int,
		"584": GameState.sp,
		"734": GameState.stat_int,
		"736": GameState.stat_int,
		"738": GameState.stat_con,
		"740": GameState.stat_str,
		"742": GameState.max_sp,
	}


func _placeholder_formula_ctx(class_id: int, skill_id: int, rec: Dictionary) -> Dictionary:
	var info: Dictionary = skill_info(class_id, skill_id)
	var skill_payload: Dictionary = rec.duplicate(true)
	for k in info.keys():
		skill_payload[k] = info[k]
	return {
		"skill": skill_payload,
		"defender": {"atk": 10, "def": 5, "hp": 100, "max_hp": 100},
		"item": {},
		"player": _placeholder_player_ctx(),
	}


func _calc_placeholder_formula(formula_id: int, ctx: Dictionary) -> int:
	if formula_id <= 0:
		return 0
	var fvm := _formula_vm()
	if fvm == null:
		return 0
	return int(fvm.calc(formula_id, ctx))


func _placeholder_int_field(rec: Dictionary, info: Dictionary, field: String) -> int:
	if rec.has(field):
		return int(rec[field])
	if info.has(field):
		return int(info[field])
	return -1


func _format_placeholder_display(nn: int, value: int) -> String:
	if value < 0 or value > PLACEHOLDER_UNREASONABLE_THRESHOLD:
		if PLACEHOLDER_LABELS.has(nn):
			return "?(%s)" % PLACEHOLDER_LABELS[nn]
		return "?"
	return str(value)


## Round 108: 단일 placeholder NN 의 표시용 정수 (-1 = 미해결).
func eval_placeholder_stat(nn: int, class_id: int, skill_id: int) -> int:
	var src: Dictionary = PLACEHOLDER_STAT_SOURCE.get(nn, {})
	if src.is_empty():
		return -1
	var rec: Dictionary = _skill_record(class_id, skill_id)
	if rec.is_empty():
		return -1
	var info: Dictionary = skill_info(class_id, skill_id)
	var ctx: Dictionary = _placeholder_formula_ctx(class_id, skill_id, rec)
	if src.has("formula_key"):
		var fid: int = int(info.get(src["formula_key"], 0))
		var calc_v: int = _calc_placeholder_formula(fid, ctx)
		if calc_v > 0 and calc_v <= PLACEHOLDER_UNREASONABLE_THRESHOLD:
			return calc_v
	if src.has("field"):
		var fv: int = _placeholder_int_field(rec, info, src["field"])
		if fv >= 0 and fv <= PLACEHOLDER_UNREASONABLE_THRESHOLD:
			return fv
	var stats: Array = rec.get("stats_u16", [])
	if nn >= 0 and nn < stats.size():
		var raw: int = int(stats[nn])
		if raw <= PLACEHOLDER_UNREASONABLE_THRESHOLD:
			return raw
	return -1


func _resolve_placeholder_stat(nn: int, class_id: int, skill_id: int) -> String:
	return _format_placeholder_display(nn, eval_placeholder_stat(nn, class_id, skill_id))


func resolve_skill_desc(class_id: int, skill_id: int) -> String:
	_ensure_skills_cache_loaded()
	if class_id == 5 and not _skills_cache.has("class_5"):
		_ensure_spirit_skills_loaded()
	var skill: Dictionary = _skill_record(class_id, skill_id)
	if skill.is_empty():
		return ""
	var desc: String = str(skill.get("desc", ""))
	var stats: Array = skill.get("stats_u16", [])
	# Round 110: bracket-aware — `}...|` 내부 #NN 만 치환. bare `#NN` (예: `#01돌격-스턴효과`)
	# 은 skill-link 참조이므로 보존. R108 의 `result.replace("#%02d", val)` 무차별 치환은
	# class_0..3 의 46+ skill-link 를 corruption 했음 (`#01돌격-스턴효과` → `0돌격-스턴효과`).
	# Round 111: indices 에 `}...|` 괄호 내부에 등장하는 모든 `#NN` 자동 수집 →
	# SOURCE 미매핑 NN (#10/#11/#13) 도 stats fallback / label fallback 통해 처리.
	var indices: Array[int] = []
	for nn in PLACEHOLDER_STAT_SOURCE.keys():
		if desc.find("#%02d" % nn) != -1:
			indices.append(nn)
	for i in stats.size():
		if not indices.has(i):
			indices.append(i)
	# R111: 괄호 내부에 등장하는 `#NN` 자동 수집 (#10/#11/#13 등 SOURCE 미매핑)
	var bi: int = 0
	while bi < desc.length():
		var b_open := desc.find("}", bi)
		if b_open == -1:
			break
		var b_close := desc.find("|", b_open + 1)
		if b_close == -1:
			break
		var bracket_inner := desc.substr(b_open + 1, b_close - b_open - 1)
		var pi: int = 0
		while pi < bracket_inner.length() - 2:
			if bracket_inner[pi] == "#" \
				and bracket_inner[pi + 1].is_valid_int() \
				and bracket_inner[pi + 2].is_valid_int():
				var nn_str := bracket_inner.substr(pi + 1, 2)
				var nn := nn_str.to_int()
				if not indices.has(nn):
					indices.append(nn)
				pi += 3
			else:
				pi += 1
		bi = b_close + 1
	# display_val 산출 (NN → 치환값)
	var values: Dictionary = {}
	for i in indices:
		if PLACEHOLDER_STAT_SOURCE.has(i):
			values[i] = _resolve_placeholder_stat(i, class_id, skill_id)
		else:
			var raw_val: int = int(stats[i]) if i < stats.size() else -1
			values[i] = _format_placeholder_display(i, raw_val)
	return _replace_placeholders_in_brackets(desc, values)


## Round 110: `}...|` 강조 괄호 내부의 `#NN` 만 치환.
## bare `#NN` (괄호 외부, 주로 skill-link 참조) 은 보존.
## 동일 괄호 안에서 여러 #NN 등장 가능 (예: `}SP #07| 소모.;재사용대기 }#09초|.`).
func _replace_placeholders_in_brackets(desc: String, values: Dictionary) -> String:
	var result := ""
	var i := 0
	while i < desc.length():
		var c := desc[i]
		if c == "}":
			var close := desc.find("|", i + 1)
			if close == -1:
				result += desc.substr(i)
				break
			var inner := desc.substr(i + 1, close - i - 1)
			for nn in values.keys():
				inner = inner.replace("#%02d" % nn, values[nn])
			result += "}" + inner + "|"
			i = close + 1
		else:
			result += c
			i += 1
	return result


## Round 90: spirit/class skill description 을 UI 표시용으로 한국어 정제.
##
## R88 의 raw desc 는 `}#NN<unit>|` placeholder + `;` 줄바꿈 마커를 포함.
## 본 함수는 (1) resolve_skill_desc 로 stat 치환 후 (2) `}...|` 강조 브래킷을
## `[...]` 로 변환 (UI 가독성) + (3) `;` → `\n` 변환.
##
##   예 (spirit #0 암흑탄, stats_u16[5]=12336):
##     raw   : "거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다.;..."
##     return: "거대한 암흑탄을 발사하여\n정령마력 [12336%]의\n피해를 준다.\n..."
##
## Round 108: spirit/class placeholder 는 primary_u16·formula_id·FormulaVM 우선.
## Formula JSON 미export 시 calc=0 → explicit field (예: 암흑탄 #05→400) 노출.
## Round 111: `{관련특성|` 섹션 헤더 → `▸ <text>:` + bare `#NN<text>` skill-link →
## `• <text>` 불릿 렌더링. class_0..3 의 46건 skill-link 정직 표시.
##
## Round 112: 원본 데이터 quirk 흡수 — (1) `}<text>}<num>|` 중첩 시 inner `}` 제거
## 후 `[text num]` 으로 평탄화 (봉쇄/섬광탄 `}시야를 }1|로` 패턴), (2) `{` 를 close
## 대체 marker 로 수용 (쐐기탄 `}민첩 12당 1{의` 의 bit-flip 가설).
func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:
	var raw := resolve_skill_desc(class_id, skill_id)
	if raw.is_empty():
		return ""
	# `}TEXT|` 강조 브래킷 → `[TEXT]`. `}` 와 `|` 가 짝지어 등장한다고 가정.
	var out := ""
	var i := 0
	while i < raw.length():
		var c := raw[i]
		if c == "}":
			# R112: `|` 또는 `{` (data quirk) 를 close marker 로 수용. 더 가까운 쪽 사용.
			var close_pipe := raw.find("|", i + 1)
			var close_brace := raw.find("{", i + 1)
			var close := -1
			if close_pipe == -1:
				close = close_brace
			elif close_brace == -1:
				close = close_pipe
			else:
				close = min(close_pipe, close_brace)
			if close == -1:
				out += c
				i += 1
				continue
			# R112: 중첩 `}` 가 bracket 안에 등장하면 inner `}` 는 제거.
			var inner := raw.substr(i + 1, close - i - 1).replace("}", "")
			out += "[" + inner + "]"
			i = close + 1
		elif c == "{":
			# R111: `{관련특성|` 섹션 헤더 → `▸ 관련 특성:`. 일반 `{TEXT|` 도 동일 처리.
			var close := raw.find("|", i + 1)
			if close == -1:
				out += c
				i += 1
				continue
			var header := raw.substr(i + 1, close - i - 1)
			if header == "관련특성":
				out += "▸ 관련 특성:"
			else:
				out += "▸ " + header + ":"
			i = close + 1
		elif c == "#" and i + 2 < raw.length() \
			and raw[i + 1].is_valid_int() and raw[i + 2].is_valid_int() \
			and (out.is_empty() or out.ends_with("\n")):
			# R111: bare `#NN<text>` skill-link → `• <text>` 불릿.
			# R112: 줄 시작 (`\n` 직후 또는 빈 출력) 위치만 불릿화. 행 중간의 `#NN`
			# (예: 포격 `사격당 |#07|의`) 은 raw 유지.
			out += "• "
			i += 3
		elif c == ";":
			out += "\n"
			i += 1
		else:
			out += c
			i += 1
	return out


## Round 90: skill desc 의 첫 줄 (`;` 분리 첫 segment) 만 UI 로그용으로 반환.
## battle log 에 짧게 표시할 때 사용. placeholder 치환 + 브래킷 정제 후 첫 줄.
##   예: "거대한 암흑탄을 발사하여" (placeholder 가 첫 줄 뒤에 있으면 그대로).
func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:
	var full := resolve_skill_desc_display(class_id, skill_id)
	if full.is_empty():
		return ""
	var nl := full.find("\n")
	if nl == -1:
		return full.strip_edges()
	return full.substr(0, nl).strip_edges()


## Round 83: spirit skills (class_5, 16 entries) 를 별도 c_csv_skill_05.json 에서 load.
##
## skills.json 은 class_0..3 만 포함 (Sorcerer = class_4 부재). spirit 은 별개 raw csv
## 형식 (count + records[{name, extra_hex, desc_text}]). 본 함수가 첫 호출 시
## _skills_cache["class_5"] 채움.
##
## Round 88: `desc_text` 필드 (EUC-KR 디코딩 완료, tools/converter/decode_h5_skill_desc.py)
## 를 entry["desc"] 에 채워 — Sorcerer 의 spirit 스킬 설명이 한국어로 노출됨.
##   spirit #0 암흑탄: "거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다.;..."
##   spirit #7 정신감응: "패시브 스킬.;전투시 정령 게이지가;..."
## `;` 는 줄바꿈, `}#NN%|` 는 stat placeholder (spirit layout 다르므로 R89+ 정밀화).
##
## 이로써 battle_system._skill_data 의 Sorcerer fallback (`class_5`) 이 정상 동작:
##   `_skills_cache.get("class_5", [])` 가 16 spirit skill 의 name + desc list 반환.
func _ensure_spirit_skills_loaded() -> void:
	if _skills_cache.has("class_5"):
		return
	var p := "res://assets/gamedata/c_csv_skill_05.json"
	if not FileAccess.file_exists(p):
		_skills_cache["class_5"] = []
		return
	var f := FileAccess.open(p, FileAccess.READ)
	var raw = JSON.parse_string(f.get_as_text()) or {}
	var records: Array = raw.get("records", [])
	var converted: Array = []
	for r in records:
		var bytes = _hex_to_bytes(str(r.get("extra_hex", "")))
		# Round 84: extra_hex hex string → bytes → little-endian u16 stride 24 entries.
		# Round 87: R77 LoadResSkillInfo file layout 의 정확한 sub-rel offset 으로
		# explicit field 추출. R84 의 stats_u16 24 entries (u16 stride) 는 보조용
		# 으로 유지하되, R72/R73 의 5 critical field 는 직접 명시.
		# 16 spirit 분석 결과: effect_type 0/2/7 분포, formula_id_1 대부분 57,
		# 다양한 special_dispatch (curse/debuff 류 다수).
		var stats_u16: Array = []
		var n = min(48, bytes.size())
		for i in range(0, n - 1, 2):
			stats_u16.append((bytes[i + 1] << 8) | bytes[i])
		# R77 명시적 field (bytes.size() ≥ 48 일 때만)
		var has_stats = bytes.size() >= 48
		# R88: desc_text (decode_h5_skill_desc.py 후처리, EUC-KR → UTF-8) 를 desc 로.
		var desc_text = str(r.get("desc_text", ""))
		var entry: Dictionary = {
			"name": str(r.get("name", "정령%d" % converted.size())),
			"stats_u16": stats_u16,
			"desc": desc_text,
			"_raw_bytes_size": bytes.size(),
		}
		if has_stats:
			# R77 sub-rel offset → HeroSkillInfo entry field 정확 매핑.
			entry["effect_type"] = bytes[0x1a]              # → entry+0x28 (R70/R72 JT1 key)
			entry["dynamic_formula_id"] = bytes[0x26]       # → entry+0x30 (R73 case 5)
			entry["special_dispatch"] = bytes[0x2b]         # → entry+0x3a (R72 0x34/0x37 분기)
			entry["formula_id_1"] = bytes[0x2d]             # → entry+0x3c (R72)
			entry["formula_id_2"] = bytes[0x2e]             # → entry+0x3d (R72)
			entry["primary_u16"] = bytes[0x22] | (bytes[0x23] << 8)  # → entry+0x32
			entry["secondary_u16"] = bytes[0x24] | (bytes[0x25] << 8)  # → entry+0x36
			entry["desc_len"] = bytes[0x2f]                 # description string length
			# R57 관습 호환: stats[5]=damage% / stats[7]=mp / stats[9]=cooldown
			# R77 의 sub-rel: 0x0a (idx 5 of 0..0x2f bytes?) — 단순 byte index 사용
			# 실제 spirit data 에서 mp/cd/damage 위치는 추후 R88+ 정밀화
			entry["mp_cost"] = bytes[0x07] if bytes.size() > 7 else 0   # 추정 (sub-rel 0x07 = 0 in spirit 0)
			entry["cooldown"] = bytes[0x0d] if bytes.size() > 0xd else 0  # 추정 (sub-rel 0x0d = 0x5d in spirit 0)
			entry["damage_pct"] = bytes[0x00] if bytes.size() > 0 else 100  # placeholder
		converted.append(entry)
	_skills_cache["class_5"] = converted


## hex string ("00abef...") → PackedByteArray.
func _hex_to_bytes(hex: String) -> PackedByteArray:
	var out := PackedByteArray()
	var n := hex.length() - (hex.length() % 2)
	for i in range(0, n, 2):
		var byte_str = hex.substr(i, 2)
		out.append(byte_str.hex_to_int())
	return out
