## 상점 UI — 구매/판매.
##
## items.json (slot 0..9 무기/방어구) 의 첫 N 개를 노출. price=stats[0].
class_name ShopPanel
extends CanvasLayer

signal closed

const SHOP_OFFER_PER_SLOT := 4

@onready var bg: ColorRect = $BG
@onready var gold_label: Label = $BG/Gold
@onready var item_list: ItemList = $BG/Items
@onready var info: Label = $BG/Info
@onready var buy_btn: Button = $BG/BuyButton
@onready var sell_btn: Button = $BG/SellButton
@onready var close_btn: Button = $BG/CloseButton

var _offers: Array = []   # [{slot, idx, name, price, attack}]
var _selected: int = -1
var _mode: String = "buy"  # buy / sell


func _ready() -> void:
	visible = false
	buy_btn.pressed.connect(_buy_selected)
	sell_btn.pressed.connect(_sell_selected)
	close_btn.pressed.connect(_close)
	item_list.item_selected.connect(_on_item_selected)


func open_shop(shop_id: int = 0) -> void:
	visible = true
	_mode = "buy"
	_offers.clear()
	# 무기 (slot 0..3) 의 첫 N 개를 offer 로
	for slot in range(4):
		for i in range(SHOP_OFFER_PER_SLOT):
			var data = GameData.item_stat(slot, i)
			if data.is_empty(): continue
			if data.get("price", 0) <= 0: continue
			data["slot"] = slot
			data["idx"] = i
			_offers.append(data)
	_refresh()


func _refresh() -> void:
	gold_label.text = "Gold: %d" % GameState.gold
	item_list.clear()
	for o in _offers:
		var line = "%s — %d G  (atk %d)" % [o["name"], o["price"], o.get("attack", 0)]
		item_list.add_item(line)
	info.text = ""
	_selected = -1


func _on_item_selected(idx: int) -> void:
	_selected = idx
	if idx < _offers.size():
		var o = _offers[idx]
		info.text = "%s\n가격: %d G" % [o["name"], o["price"]]


func _buy_selected() -> void:
	if _selected < 0 or _selected >= _offers.size(): return
	var o = _offers[_selected]
	var price = int(o.get("price", 0))
	if GameState.gold < price:
		info.text = "골드 부족! (필요 %d, 보유 %d)" % [price, GameState.gold]
		return
	GameState.gold -= price
	GameState.inventory.append(o["name"])
	GameState.state_changed.emit()
	info.text = "구매 완료: %s" % o["name"]
	_refresh()


func _sell_selected() -> void:
	# 선택한 아이템을 인벤에서 제거하고 골드 회수 (간이: 가격의 1/2)
	if _selected < 0 or _selected >= _offers.size(): return
	var o = _offers[_selected]
	var idx_in_inv = GameState.inventory.find(o["name"])
	if idx_in_inv < 0:
		info.text = "보유하지 않음"
		return
	GameState.inventory.remove_at(idx_in_inv)
	var refund = int(o.get("price", 0)) / 2
	GameState.gold += refund
	GameState.state_changed.emit()
	info.text = "판매: %s (+%d G)" % [o["name"], refund]
	_refresh()


func _close() -> void:
	visible = false
	closed.emit()
