## 게임 전역 상태 (싱글톤). save_manager 와 양방향 sync.
extends Node

const SaveManager = preload("res://scripts/core/save_manager.gd")

signal state_changed

# 현재 맵/시나리오
var current_scene_id: int = 0
var current_episode: int = -1
var current_stage: int = -1
var map_id: int = 0

# 플레이어 상태
var player_x: int = 0
var player_y: int = 0
var player_dir: int = 0
var hp: int = 100
var max_hp: int = 100
var sp: int = 50
var max_sp: int = 50
var level: int = 1
var exp: int = 0
var gold: int = 1000

# 클래스 + 능력치
var class_id: int = 0   # 0=워리어, 1=로그, 2=건슬링어, 3=나이트, 4=소서러
var stat_str: int = 12
var stat_dex: int = 8
var stat_int: int = 10
var stat_con: int = 6
var stat_points: int = 0   # 사용자 수동 분배 점수

# 해금된 스킬 (skill_id 리스트) — 레벨업 자동 해금. unlocked_skills 가 "사용 가능" 목록.
var unlocked_skills: Array[int] = [0]  # 첫 스킬 (basic attack) 시작부터

## 스킬북으로 학습한 스킬의 레벨 (Round 57). skill_index → current_max_level.
##
## 원본 HERO::IfLearnSkill (Round 21) 의 학습 mechanism:
##   - skill_book 의 class_id 가 player class 와 일치해야 학습 가능
##   - skill_level (1..7) 이 현재 보유 레벨보다 높을 때만 갱신
##   - 학습 시 skill_index 의 새 레벨이 stat scaling 에 반영 (game_data.resolve_skill_desc)
##
## 기본값: {0: 1} (basic attack LV1) — unlocked_skills [0] 와 매칭.
var skill_levels: Dictionary = {0: 1}

## Round 74: GUNNER class (class_id=2) 의 combo state.
##
## 원본 HERO+0x269 (R72 발견): GUNNER skill slot 5 (combo shot) 사용 시 누적되는 hit counter.
## damage 공식: `(combo_state * 0x14 + 0x1e) * X / 100` = `(combo*20+30)% × base`
##   combo 1 → 50% damage / 2 → 70% / 3 → 90% / 4 → 110% — 매 hit 마다 +20% bonus
## HERO+0x248 (s16) = ammo/charge counter, skill_info[+0x48] (s16) = max combo limit
##   combo 가 max 도달 시 reset → 다음 skill 사용 또는 hit 까지 0
var gunner_combo: int = 0
var gunner_max_combo: int = 4   # default; skill 별로 다름 (skill_info[+0x48])
var gunner_ammo: int = 0         # HERO+0x248 대응 — GUNNER 가 사용하는 ammo counter

## Round 75: R72 의 helper signal (curse_applied/buff_applied/stance_applied) 캐치용
## active effect list. battle_system 이 emit 하면 GameState 가 entry 추가/만료 처리.
##
## 원본 BATTLER::AddCurseSkill / AddBuffSkill / HERO::AddStanceSkill 의 Godot 대응 —
## 실제 효과 (stat modifier, DoT, regen 등) 는 후속 라운드 (R76+) 에서 통합.
##
## entry layout: {dispatch_byte: int, formula_1: int, formula_2: int, remaining_turns: int}
##   dispatch_byte = skill_info[+0x3a] (R72 special path key, 0x34/0x37 등)
##   formula_1/2  = Formula::calc(+0x3c/+0x3d) 평가 결과 (intensity 값)
##   remaining_turns = 5 default (UI 시각화용; 후속 라운드에서 정확한 turn count 반영)
var active_curses: Array = []     # [{dispatch, f1, f2, turns}, ...] — case 1+2
var active_buffs: Array = []      # [{dispatch, f1, f2, turns}, ...] — case 3+5
var active_stances: Array = []    # [{dispatch, f1, f2, turns}, ...] — case 4


## Round 75: active effect 추가 (battle_system signal 캐치).
func add_active_effect(kind: String, dispatch: int, f1: int, f2: int, turns: int = 5) -> void:
	var entry := {"dispatch": dispatch, "f1": f1, "f2": f2, "turns": turns}
	match kind:
		"curse": active_curses.append(entry)
		"buff": active_buffs.append(entry)
		"stance": active_stances.append(entry)
	state_changed.emit()


## Round 75: 매 turn 종료 시 호출 — 모든 active effect 의 remaining_turns 감소 + 만료 제거.
func tick_active_effects() -> void:
	var changed := false
	for arr_name in ["active_curses", "active_buffs", "active_stances"]:
		var arr: Array = get(arr_name)
		var keep: Array = []
		for entry in arr:
			entry["turns"] = int(entry["turns"]) - 1
			if entry["turns"] > 0:
				keep.append(entry)
			else:
				changed = true
		set(arr_name, keep)
	if changed:
		state_changed.emit()

var inventory: Array = []
var flags: Dictionary = {}

# 장비 슬롯 — 각 값은 inventory 의 인덱스 (또는 -1 = 비어있음)
const SLOT_WEAPON := 0
const SLOT_ARMOR := 1
const SLOT_HELMET := 2
const SLOT_BOOTS := 3
const SLOT_ACC1 := 4
const SLOT_ACC2 := 5
const SLOT_COUNT := 6
var equipment: Array[int] = [-1, -1, -1, -1, -1, -1]

## 강화 상태 (Round 52). inventory 인덱스 → {refine_count, sub_count, locked}.
##
## 원본 EquipItemInfo +0x165/+0x166/+0x167 (Round 17/26) 매핑:
##   refine_count: 강화 단계 (0..10), ApplyItemRefine 성공/큰성공 시 +1
##   sub_count:    누적 강화 합산값 (V[187], refined_stat = base + sub_count)
##   locked:       lock 상태 (+0x167=1 이면 더 이상 강화 불가)
##
## 새 인벤토리 슬롯에는 entry 없음 = (0,0,false). items.json 의 record refine_count
## 와 별개 (csv 시점 값 vs runtime 값).
var refine_state: Dictionary = {}


## inv_idx 의 강화 상태 반환. 미설정 시 빈 dict default.
func get_refine(inv_idx: int) -> Dictionary:
	return refine_state.get(inv_idx, {"refine_count": 0, "sub_count": 0, "locked": false})


## inv_idx 의 강화 상태 갱신.
func set_refine(inv_idx: int, refine_count: int, sub_count: int, locked: bool = false) -> void:
	if inv_idx < 0 or inv_idx >= inventory.size(): return
	refine_state[inv_idx] = {
		"refine_count": clamp(refine_count, 0, 10),
		"sub_count": max(0, sub_count),
		"locked": locked,
	}
	state_changed.emit()


## inv_idx 의 강화 상태 제거 (인벤 아이템 제거 시 호출).
func clear_refine(inv_idx: int) -> void:
	refine_state.erase(inv_idx)


## Orb socket 상태 (Round 54). inventory 인덱스 → {sockets: [u8 ×5]}.
##
## 원본 EquipItemInfo +0x168 = orb_count (count of populated sockets),
## +0x169..+0x16d = 5 socket bytes (각 byte = orb_idx + 1, 0 = 빈 슬롯).
## Round 26 ApplyOrbCombine mechanism. sub_orbs=9 (동일 그룹 9 byte) → 강도 2x.
##
## 빈 슬롯은 0, 보유 슬롯은 slot_12 의 orb idx + 1.
var orb_state: Dictionary = {}


## inv_idx 의 socket 배열 반환 (always 5 entries).
func get_orb_sockets(inv_idx: int) -> Array:
	var st = orb_state.get(inv_idx, {})
	var s: Array = st.get("sockets", [0, 0, 0, 0, 0])
	# 안전 보장 — 정확히 5 entries
	while s.size() < 5: s.append(0)
	return s.slice(0, 5)


## 빈 socket 에 orb 장착 (slot_idx ∈ [0..4], orb_idx = slot_12 의 record idx).
## 빈 슬롯 없으면 false 반환.
func add_orb_to_socket(inv_idx: int, orb_idx: int) -> int:
	var sockets = get_orb_sockets(inv_idx)
	for i in 5:
		if sockets[i] == 0:
			sockets[i] = orb_idx + 1
			orb_state[inv_idx] = {"sockets": sockets}
			state_changed.emit()
			return i
	return -1


## 특정 socket 의 orb 제거. 제거된 orb idx 반환 (없으면 -1).
func remove_orb_from_socket(inv_idx: int, slot_idx: int) -> int:
	if slot_idx < 0 or slot_idx >= 5: return -1
	var sockets = get_orb_sockets(inv_idx)
	var encoded: int = sockets[slot_idx]
	if encoded == 0: return -1
	sockets[slot_idx] = 0
	orb_state[inv_idx] = {"sockets": sockets}
	state_changed.emit()
	return encoded - 1


## 모든 socket 의 orb 일괄 제거 (아이템 제거 시).
func clear_orbs(inv_idx: int) -> void:
	orb_state.erase(inv_idx)


## 스킬북 학습 가능 여부 + 사유 (Round 57).
##
## 반환 {ok, reason}. reason 은 ok=false 일 때만 채워짐 (UX 메시지).
##
## 조건 (Round 21 의 HERO::IfLearnSkill 매핑):
##   1) book.class_id 가 player class_id 와 일치
##   2) player level >= book.required_level
##   3) 현재 보유 skill_level < book.skill_level (이미 동급 이상이면 학습 불필요)
func can_learn_skill_book(info: Dictionary) -> Dictionary:
	if info.is_empty() or info.get("kind") not in ["skill_book_wr", "skill_book_gk"]:
		return {"ok": false, "reason": "스킬북이 아닙니다"}
	var book_class: int = int(info.get("class_id", -1))
	if book_class != class_id:
		return {"ok": false, "reason": "다른 클래스 전용 (클래스 %d)" % book_class}
	var req_lvl: int = int(info.get("required_level", 0))
	if level < req_lvl:
		return {"ok": false, "reason": "레벨 부족 (필요 Lv.%d)" % req_lvl}
	var book_lvl: int = int(info.get("skill_level", 1))
	var skill_idx: int = int(info.get("skill_index", 0))
	var have: int = int(skill_levels.get(skill_idx, 0))
	if have >= book_lvl:
		return {"ok": false, "reason": "이미 LV%d 보유 (책은 LV%d)" % [have, book_lvl]}
	return {"ok": true, "reason": ""}


## 스킬북 학습 — skill_levels 갱신 + unlocked_skills 에 없으면 추가.
##
## 호출자 책임: 인벤토리에서 책 제거 (skill_book_panel 이 _learn 후 처리).
## skill_index 가 unlocked_skills 에 없어도 학습 가능 (책으로 직접 해금).
func learn_skill_book(info: Dictionary) -> bool:
	var check = can_learn_skill_book(info)
	if not check["ok"]: return false
	var skill_idx: int = int(info["skill_index"])
	var book_lvl: int = int(info["skill_level"])
	skill_levels[skill_idx] = book_lvl
	if skill_idx not in unlocked_skills:
		unlocked_skills.append(skill_idx)
	state_changed.emit()
	return true


## skill_idx 의 현재 보유 레벨 (책 + 자연 해금 포함). 미보유 시 0.
func get_skill_level(skill_idx: int) -> int:
	return int(skill_levels.get(skill_idx, 0))


## 아이템을 슬롯에 장착. inventory 인덱스 사용.
func equip(slot: int, inv_idx: int) -> bool:
	if slot < 0 or slot >= SLOT_COUNT: return false
	if inv_idx < 0 or inv_idx >= inventory.size(): return false
	equipment[slot] = inv_idx
	state_changed.emit()
	return true


func unequip(slot: int) -> void:
	if slot < 0 or slot >= SLOT_COUNT: return
	equipment[slot] = -1
	state_changed.emit()


## 인벤토리 내 동일 이름 item 갯수 — mix_panel 의 재료 보유량 검사용 (Round 53).
##
## 현재 inventory 가 단순 String 배열이라 동일 item 중복 = 여러 entry. 이 카운트로
## "재료 5개 필요" check 수행.
func inventory_count(name: String) -> int:
	var n := 0
	for item in inventory:
		if str(item) == name: n += 1
	return n


## 인벤토리에서 동일 이름 item 을 n 개 소비 (앞에서부터). 실제 제거 갯수 반환.
## refine_state 가 있는 슬롯도 함께 erase.
func consume_inventory(name: String, n: int) -> int:
	var removed := 0
	var i := 0
	while i < inventory.size() and removed < n:
		if str(inventory[i]) == name:
			# equipment 에 장착된 슬롯은 건드리지 않음
			var is_equipped := false
			for slot in SLOT_COUNT:
				if equipment[slot] == i:
					is_equipped = true
					break
			if is_equipped:
				i += 1
				continue
			inventory.remove_at(i)
			clear_refine(i)
			clear_orbs(i)
			# i 이후 equipment 인덱스 shift
			for slot in SLOT_COUNT:
				if equipment[slot] > i:
					equipment[slot] -= 1
			removed += 1
		else:
			i += 1
	if removed > 0:
		state_changed.emit()
	return removed


func equipped_item(slot: int) -> Variant:
	if slot < 0 or slot >= SLOT_COUNT: return null
	var idx = equipment[slot]
	if idx < 0 or idx >= inventory.size(): return null
	return inventory[idx]


## 장비 stat 합산. inventory 의 아이템명 → items.json 의 slot_N 에서
## 검색 → stats[7] (atk/def) 추출 + Round 52 강화 보너스 (sub_count).
##
## refined_stat = base_stat + sub_count (Round 26 의 Formula VM id=35/36 결과).
## weapon slot 은 ATK, 그 외 equip slot 은 DEF 로 누적.
func equipment_bonus() -> Dictionary:
	var bonus := {"attack": 0, "defense": 0}
	for slot in SLOT_COUNT:
		var item = equipped_item(slot)
		if item == null: continue
		var inv_idx: int = equipment[slot]
		var item_name := str(item)
		var info = GameData.item_lookup(item_name)
		# items.json 의 stat_a 를 우선 사용 (Round 26 의 의미 있는 stat) — 없으면 fallback to stats[7]
		var base_stat: int = int(info.get("stat_a", 0))
		if base_stat == 0:
			for item_slot in range(10):
				var arr = GameData.items_in_slot(item_slot)
				var idx = arr.find(item_name)
				if idx >= 0:
					var data = GameData.item_stat(item_slot, idx)
					base_stat = int(data.get("attack", 0))
					break
		# Round 52 강화 보너스
		var refine = get_refine(inv_idx)
		var refined = base_stat + int(refine.get("sub_count", 0))
		# Round 54 orb 보너스 — 각 socket 당 GameData.orb_bonus_for(orb_idx) 합산
		var orb_bonus := 0
		for encoded in get_orb_sockets(inv_idx):
			if encoded == 0: continue
			orb_bonus += GameData.orb_bonus_for(encoded - 1)
		# Round 26: sub_orbs=9 (동일 그룹 9 byte) 시 강도 2x — 단순 동치: 9개 다 채우면 2배
		var populated: int = 0
		for encoded in get_orb_sockets(inv_idx):
			if encoded != 0: populated += 1
		if populated >= 5:
			orb_bonus *= 2
		if slot == SLOT_WEAPON:
			bonus["attack"] += refined + orb_bonus
		else:
			bonus["defense"] += refined + orb_bonus
	return bonus


## 수동 stat 분배. 단, stat_points 점수가 있어야 가능.
func allocate_stat(stat_name: String, points: int = 1) -> bool:
	if stat_points < points: return false
	match stat_name:
		"str": stat_str += points
		"dex": stat_dex += points
		"int": stat_int += points
		"con":
			stat_con += points
			max_hp += points * 5
		_: return false
	stat_points -= points
	state_changed.emit()
	return true


## 캐릭터 총 ATK = base STR-derived + equipment bonus + active effect modifier (R76).
##
## Round 76: active_buffs / active_curses 가 stat 에 영향:
##   - active_buffs (R72 case 3+5 / +0x3c-3d formula result) → ATK % bonus
##     entry["f1"] 을 % 가중치로 누적 (예: f1=20 → +20% ATK)
##   - active_stances (R72 case 4 / KNIGHT 방어 stance 등) → ATK 변동 없음 (DEF 만)
##   - active_curses (R72 case 1+2) → ATK 변동 없음 (DEF 감소만, 적용처는 별도)
##
## 공식: `atk_total = (base + equip_bonus + magic_bonus) × (100 + buff_atk_pct) / 100`
##   buff_atk_pct = Σ entry["f1"] for entry in active_buffs (clamp 0..200)
##
## Round 83: Sorcerer (class_id=4) 는 INT × 2 를 base 에 추가로 더함 (magic 클래스
## 특화). 다른 클래스는 STR 기반만. 원본 c_csv_skill_04 부재 stub 의 대응 — Sorcerer
## active skill 없는 대신 일반 공격이 INT scaling 으로 강화. 다른 클래스의 STR 기반
## 과 동등한 effective 공격력 유지.
func total_attack() -> int:
	var base = stat_str * 2 + level * 3
	if class_id == 4:
		base += stat_int * 2   # Sorcerer: INT magic bonus (active skill 부재 보상)
	var equip = int(equipment_bonus().get("attack", 0))
	var raw = base + equip
	var buff_pct = 0
	for entry in active_buffs:
		buff_pct += int(entry.get("f1", 0))
	buff_pct = clamp(buff_pct, 0, 200)
	return raw * (100 + buff_pct) / 100


## 캐릭터 총 DEF = base CON-derived + equipment bonus + active stance/curse modifier (R76).
##
## Round 76: active_stances / active_curses 가 stat 에 영향:
##   - active_stances (R72 case 4) → DEF % bonus (KNIGHT 방어 stance +50% 등)
##   - active_curses (R72 case 1+2) → DEF % reduction (debuff 의 강도)
##   - active_buffs 는 DEF 영향 없음 (ATK 전용)
##
## 공식: `def_total = (base + equip_bonus) × (100 + stance_pct - curse_pct) / 100`
##   stance_pct = Σ entry["f1"] for entry in active_stances (clamp 0..150)
##   curse_pct  = Σ entry["f1"] for entry in active_curses (clamp 0..80)
func total_defense() -> int:
	var base = stat_con + level * 2
	var equip = int(equipment_bonus().get("defense", 0))
	var raw = base + equip
	var stance_pct = 0
	for entry in active_stances:
		stance_pct += int(entry.get("f1", 0))
	stance_pct = clamp(stance_pct, 0, 150)
	var curse_pct = 0
	for entry in active_curses:
		curse_pct += int(entry.get("f1", 0))
	curse_pct = clamp(curse_pct, 0, 80)
	var net_pct = 100 + stance_pct - curse_pct
	return raw * net_pct / 100

var verbose: bool = true

# 플레이 시간 추적
var play_time_sec: float = 0.0


var _regen_timer: float = 0.0
const REGEN_INTERVAL := 2.0  # 2초마다 회복
var in_combat: bool = false

var _auto_save_timer: float = 0.0
const AUTO_SAVE_INTERVAL := 60.0  # 60초마다 자동 저장


func _process(delta: float) -> void:
	play_time_sec += delta
	# 비전투 시 HP/SP 자동 회복
	if not in_combat:
		_regen_timer += delta
		if _regen_timer >= REGEN_INTERVAL:
			_regen_timer = 0.0
			var hp_regen := max(1, max_hp / 50)   # 2%/2초
			var sp_regen := max(1, max_sp / 30)
			var changed := false
			if hp < max_hp:
				hp = min(max_hp, hp + hp_regen)
				changed = true
			if sp < max_sp:
				sp = min(max_sp, sp + sp_regen)
				changed = true
			if changed: state_changed.emit()
	# 자동 저장 (60초마다, 비전투 시)
	if not in_combat:
		_auto_save_timer += delta
		if _auto_save_timer >= AUTO_SAVE_INTERVAL:
			_auto_save_timer = 0.0
			SaveManager.auto_save(to_save_dict())


func to_save_dict() -> Dictionary:
	# Round 91: stat_points + Sorcerer/Gunner state + active effect arrays +
	# mission state 추가 (이전엔 누락되어 save → load 후 stat/combo 사라짐).
	return {
		"scene_id": current_scene_id,
		"map_id": map_id,
		"play_time_sec": int(play_time_sec),
		"player_x": player_x, "player_y": player_y, "player_dir": player_dir,
		"class_id": class_id,
		"hp": hp, "max_hp": max_hp,
		"sp": sp, "max_sp": max_sp,
		"level": level, "exp": exp, "gold": gold,
		"stat_str": stat_str, "stat_dex": stat_dex,
		"stat_int": stat_int, "stat_con": stat_con,
		"stat_points": stat_points,
		"gunner_combo": gunner_combo,
		"gunner_max_combo": gunner_max_combo,
		"gunner_ammo": gunner_ammo,
		"active_curses": active_curses.duplicate(true),
		"active_buffs": active_buffs.duplicate(true),
		"active_stances": active_stances.duplicate(true),
		"inventory": inventory,
		"equipment": equipment,
		"unlocked_skills": unlocked_skills,
		"skill_levels": skill_levels,
		"flags": flags,
		"quest": Quest.to_save() if Quest else {},
		"mission": Mission.to_save() if Mission else {},
	}


## Round 91: save round-trip 정합성 — class_id / stat_* / equipment /
## unlocked_skills / skill_levels / play_time_sec / stat_points / gunner_* /
## active_* / quest / mission 모두 복원. 이전엔 player_x/y/hp/level/gold/
## inventory/flags 만 복원되어 save → load 시 클래스/스탯/스킬 lost.
func apply_save(data: Dictionary) -> void:
	current_scene_id = int(data.get("scene_id", 0))
	map_id = int(data.get("map_id", 0))
	play_time_sec = float(data.get("play_time_sec", 0))
	var p = data.get("player", data)  # support both nested + flat
	player_x = int(p.get("x", p.get("player_x", 0)))
	player_y = int(p.get("y", p.get("player_y", 0)))
	player_dir = int(p.get("dir", p.get("player_dir", 0)))
	class_id = int(p.get("class_id", data.get("class_id", 0)))
	hp = int(p.get("hp", 100))
	max_hp = int(p.get("max_hp", 100))
	sp = int(p.get("sp", 50))
	max_sp = int(p.get("max_sp", 50))
	level = int(p.get("level", 1))
	exp = int(p.get("exp", 0))
	gold = int(p.get("gold", 1000))
	stat_str = int(p.get("str", p.get("stat_str", stat_str)))
	stat_dex = int(p.get("dex", p.get("stat_dex", stat_dex)))
	stat_int = int(p.get("int", p.get("stat_int", stat_int)))
	stat_con = int(p.get("con", p.get("stat_con", stat_con)))
	stat_points = int(p.get("stat_points", data.get("stat_points", 0)))
	inventory = data.get("inventory", [])
	# equipment: Array[int] 타입 유지 (PackedByteArray 비교 대비)
	var eq_raw: Array = data.get("equipment", [])
	equipment.clear()
	for v in eq_raw:
		equipment.append(int(v))
	# unlocked_skills: Array[int]
	var us_raw: Array = data.get("unlocked_skills", [])
	unlocked_skills.clear()
	for v in us_raw:
		unlocked_skills.append(int(v))
	# skill_levels: JSON 의 key 는 string → int 변환
	var sl_raw = data.get("skill_levels", {})
	skill_levels = {}
	if sl_raw is Dictionary:
		for k in sl_raw.keys():
			skill_levels[int(k)] = int(sl_raw[k])
	gunner_combo = int(data.get("gunner_combo", 0))
	gunner_max_combo = int(data.get("gunner_max_combo", 4))
	gunner_ammo = int(data.get("gunner_ammo", 0))
	active_curses = data.get("active_curses", [])
	active_buffs = data.get("active_buffs", [])
	active_stances = data.get("active_stances", [])
	flags = data.get("flags", {})
	if Quest and data.has("quest"):
		Quest.from_save(data.get("quest", {}))
	if Mission and data.has("mission"):
		Mission.from_save(data.get("mission", {}))
	state_changed.emit()


func quick_save(slot: int = 0) -> bool:
	return SaveManager.save(slot, to_save_dict())


func quick_load(slot: int = 0) -> bool:
	var data = SaveManager.load_slot(slot)
	if data.is_empty(): return false
	apply_save(data)
	return true


## 전투 결과 적용.
signal level_up(new_level: int, gained_skills: Array)

func add_battle_reward(exp_gain: int, gold_gain: int) -> void:
	exp += exp_gain
	gold += gold_gain
	while exp >= level * 100:
		exp -= level * 100
		level += 1
		# 절반은 자동 분배, 절반은 수동 (3 ~ 5 점)
		_apply_levelup_stats()
		stat_points += 3
		max_hp += 10 + stat_con
		hp = max_hp
		max_sp += 5 + stat_int / 2
		sp = max_sp
		# 스킬 해금: lvl 5/10/15/20/25 마다 새 스킬
		var newly_unlocked: Array = []
		for tier in [5, 10, 15, 20, 25, 30, 35, 40]:
			if level == tier:
				var skill_idx = unlocked_skills.size()
				if skill_idx < 43:  # 클래스당 43 스킬
					unlocked_skills.append(skill_idx)
					newly_unlocked.append(skill_idx)
		level_up.emit(level, newly_unlocked)
	state_changed.emit()


func _apply_levelup_stats() -> void:
	# 클래스별 분포: 워리어 STR>INT>DEX>CON, 로그 DEX>CON, ...
	match class_id:
		0:  # 워리어
			stat_str += 2; stat_int += 1; stat_dex += 1
		1:  # 로그
			stat_dex += 2; stat_con += 2
		2:  # 건슬링어
			stat_dex += 2; stat_str += 1; stat_int += 1
		3:  # 나이트
			stat_str += 1; stat_int += 2; stat_dex += 1
		4:  # 소서러
			stat_int += 2; stat_con += 2
		_:
			stat_str += 1; stat_dex += 1; stat_int += 1; stat_con += 1
