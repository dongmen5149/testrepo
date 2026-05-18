## Orb socket 패널 — Round 17/26 의 ApplyOrbCombine mechanism Godot 구현.
##
## 원본 mechanism (libHeroesLore5.so::RefineItem::ApplyOrbCombine, ~1208B):
##   item +0x168 = orb_count (populated socket count, V[188])
##   +0x169..+0x16d = 5 socket bytes (각 byte = orb_idx + 1, 0 = 빈)
##   Round 26: 53 orb (csv slot_12) 중 sub_orbs=9 (동일 그룹 9 byte) 시 강도 2x.
##
## UI 구성:
##   - 좌측: equip 카테고리 inventory item 리스트 (강화 단계 + populated socket 수)
##   - 중앙: 선택된 item 의 5 socket 표시 (Slot 0..4) + 각 socket 의 orb 이름 + bonus
##   - 우측: 인벤토리 orb 리스트 (보유 orb_idx + count) — 빈 socket 클릭 시 장착
class_name OrbPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var equip_list: ItemList = $BG/EquipList
@onready var socket_list: ItemList = $BG/SocketList
@onready var orb_list: ItemList = $BG/OrbList
@onready var info_label: Label = $BG/Info
@onready var remove_btn: Button = $BG/RemoveBtn
@onready var close_btn: Button = $BG/CloseBtn

signal closed
signal orb_changed(inv_idx: int, action: String)  ## action ∈ {"socket", "remove"} — Round 58 mission hook

var _selected_inv_idx: int = -1
var _selected_socket_slot: int = -1
var _shown: bool = false


func _ready() -> void:
	visible = false
	equip_list.item_selected.connect(_on_equip_selected)
	socket_list.item_selected.connect(_on_socket_selected)
	orb_list.item_activated.connect(_on_orb_activated)
	remove_btn.pressed.connect(_on_remove_pressed)
	close_btn.pressed.connect(toggle)


func toggle() -> void:
	_shown = not _shown
	visible = _shown
	if _shown:
		_refresh_equip_list()
	else:
		closed.emit()


## inventory 의 equip 카테고리 item 만 (socket 보유 가능).
func _refresh_equip_list() -> void:
	equip_list.clear()
	_selected_inv_idx = -1
	_selected_socket_slot = -1
	info_label.text = ""
	for i in GameState.inventory.size():
		var name = str(GameState.inventory[i])
		var info = GameData.item_lookup(name)
		if info.get("category", "") != "equip": continue
		var sockets = GameState.get_orb_sockets(i)
		var populated = sockets.reduce(func(acc, x): return acc + (1 if x != 0 else 0), 0)
		var ref = GameState.get_refine(i)
		var rc: int = int(ref.get("refine_count", 0))
		var label = "%s +%d  [%d/5]" % [name, rc, populated]
		var idx = equip_list.add_item(label)
		equip_list.set_item_metadata(idx, i)
	_refresh_socket_list()
	_refresh_orb_list()


func _on_equip_selected(idx: int) -> void:
	_selected_inv_idx = int(equip_list.get_item_metadata(idx))
	_selected_socket_slot = -1
	_refresh_socket_list()
	_refresh_orb_list()


func _refresh_socket_list() -> void:
	socket_list.clear()
	remove_btn.disabled = true
	if _selected_inv_idx < 0:
		info_label.text = "(아이템 선택)"
		return
	var sockets = GameState.get_orb_sockets(_selected_inv_idx)
	var item_name = str(GameState.inventory[_selected_inv_idx])
	info_label.text = "%s 의 socket:" % item_name
	for i in 5:
		var encoded: int = int(sockets[i])
		var label = "[%d] (빈 슬롯)" % i if encoded == 0 \
			else "[%d] %s (+%d)" % [i, GameData.orb_name(encoded - 1), GameData.orb_bonus_for(encoded - 1)]
		socket_list.add_item(label)


func _on_socket_selected(idx: int) -> void:
	_selected_socket_slot = idx
	var sockets = GameState.get_orb_sockets(_selected_inv_idx)
	# 채워진 슬롯이면 remove 가능
	remove_btn.disabled = int(sockets[idx]) == 0


## 인벤토리에서 orb 종류 별 보유 수 카운팅 → orb_list.
func _refresh_orb_list() -> void:
	orb_list.clear()
	# orb 보유: inventory 안의 slot_12 item — items.json 의 slot_12 record 와 매칭.
	# inventory 가 String 배열이므로 orb 이름 → orb_idx 역매핑 필요.
	var orbs = GameData.orb_records()
	var name_to_idx: Dictionary = {}
	for i in orbs.size():
		var nm = str(orbs[i].get("name", ""))
		if not nm.is_empty():
			name_to_idx[nm] = i
	# inventory 안의 orb 카운팅
	var counts: Dictionary = {}
	for item in GameState.inventory:
		var nm = str(item)
		if name_to_idx.has(nm):
			counts[nm] = int(counts.get(nm, 0)) + 1
	# orb_list 표시
	for nm in counts.keys():
		var oi = int(name_to_idx[nm])
		var bonus = GameData.orb_bonus_for(oi)
		var grp = GameData.orb_group(oi)
		var idx = orb_list.add_item("%s × %d  (+%d, grp %d)" % [nm, counts[nm], bonus, grp])
		orb_list.set_item_metadata(idx, oi)


## orb 더블클릭 = 빈 socket 에 장착 + inventory 에서 1개 소비.
func _on_orb_activated(idx: int) -> void:
	if _selected_inv_idx < 0:
		info_label.text = "장비 먼저 선택"
		return
	var orb_idx: int = int(orb_list.get_item_metadata(idx))
	var orb_name = GameData.orb_name(orb_idx)
	# 빈 socket 있는지
	var slot = GameState.add_orb_to_socket(_selected_inv_idx, orb_idx)
	if slot < 0:
		info_label.text = "빈 socket 없음"
		return
	# inventory 에서 1개 소비
	GameState.consume_inventory(orb_name, 1)
	info_label.text = "✓ %s → slot %d" % [orb_name, slot]
	orb_changed.emit(_selected_inv_idx, "socket")
	# 인벤 변동으로 selected idx 가 shift 됐을 수도 있음 — 전체 refresh
	_refresh_equip_list()
	# 선택 복원 (가능한 한)
	for i in equip_list.item_count:
		var meta = equip_list.get_item_metadata(i)
		if meta != null and int(meta) == _selected_inv_idx:
			equip_list.select(i)
			_on_equip_selected(i)
			break


## socket 의 orb 제거 — orb 는 inventory 로 돌아옴.
func _on_remove_pressed() -> void:
	if _selected_inv_idx < 0 or _selected_socket_slot < 0: return
	var orb_idx = GameState.remove_orb_from_socket(_selected_inv_idx, _selected_socket_slot)
	if orb_idx < 0: return
	var orb_name = GameData.orb_name(orb_idx)
	GameState.inventory.append(orb_name)
	GameState.state_changed.emit()
	info_label.text = "✓ %s 제거 → 인벤토리" % orb_name
	orb_changed.emit(_selected_inv_idx, "remove")
	_refresh_socket_list()
	_refresh_orb_list()
	_refresh_equip_list()
	for i in equip_list.item_count:
		var meta = equip_list.get_item_metadata(i)
		if meta != null and int(meta) == _selected_inv_idx:
			equip_list.select(i)
			break
