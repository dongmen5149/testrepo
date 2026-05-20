## Round 92: Save slot 선택 UI 패널.
##
## R91 의 save round-trip 정합성 fix 후속. 그동안 demo.gd 의 1-8 숫자 키 +
## Shift 조합만으로 slot 저장/로드가 가능했고 사용자는 어느 슬롯이 어떤
## 상태인지 알기 어려웠음. F6 으로 열리는 본 패널이 8 슬롯 (+ AUTO 7)
## 의 timestamp / class / level / gold / playtime 을 표시 + 행마다 Load /
## Save / Delete 버튼.
##
## save_manager.list_slots() 의 metadata 를 그대로 활용 (R49 부터 존재).
## auto-save slot (AUTO_SLOT=7) 은 "AUTO" 라벨 + Save 버튼 비활성화 (자동
## 갱신 전용).
class_name SaveListPanel
extends CanvasLayer

const CLASS_NAMES := ["워리어", "로그", "건슬링어", "나이트", "소서러"]

@onready var bg: ColorRect = $BG
@onready var title_label: Label = $BG/Title
@onready var slot_list: VBoxContainer = $BG/SlotList
@onready var close_btn: Button = $BG/CloseButton
@onready var status_label: Label = $BG/StatusLabel


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)


## 패널 표시 토글. 열릴 때 슬롯 목록 새로고침.
func toggle() -> void:
	visible = not visible
	if visible:
		refresh()


## 슬롯 행을 재생성. 각 슬롯의 metadata 를 표시 + 3 액션 버튼 연결.
func refresh() -> void:
	for child in slot_list.get_children():
		child.queue_free()
	for i in H5SaveManager.MAX_SLOTS:
		var row := _build_slot_row(i)
		slot_list.add_child(row)


func _build_slot_row(slot: int) -> Control:
	var hbox := HBoxContainer.new()
	hbox.custom_minimum_size = Vector2(0, 32)
	var info := Label.new()
	info.custom_minimum_size = Vector2(160, 28)
	info.text = _format_slot(slot)
	hbox.add_child(info)
	var load_btn := Button.new()
	load_btn.text = "로드"
	load_btn.custom_minimum_size = Vector2(40, 24)
	load_btn.pressed.connect(_on_load.bind(slot))
	hbox.add_child(load_btn)
	var save_btn := Button.new()
	save_btn.text = "저장"
	save_btn.custom_minimum_size = Vector2(40, 24)
	# AUTO slot 은 수동 저장 비활성화.
	save_btn.disabled = (slot == H5SaveManager.AUTO_SLOT)
	save_btn.pressed.connect(_on_save.bind(slot))
	hbox.add_child(save_btn)
	var del_btn := Button.new()
	del_btn.text = "X"
	del_btn.custom_minimum_size = Vector2(24, 24)
	del_btn.pressed.connect(_on_delete.bind(slot))
	hbox.add_child(del_btn)
	return hbox


func _format_slot(slot: int) -> String:
	var data := H5SaveManager.load_slot(slot)
	var prefix := "Slot %d" % slot
	if slot == H5SaveManager.AUTO_SLOT:
		prefix = "AUTO  "
	if data.is_empty():
		return "%s: (빈 슬롯)" % prefix
	var p: Dictionary = data.get("player", {})
	var cid: int = int(p.get("class_id", 0))
	var class_name_str: String = CLASS_NAMES[cid] if cid >= 0 and cid < CLASS_NAMES.size() else "?"
	var level: int = int(p.get("level", 1))
	var gold: int = int(p.get("gold", 0))
	var pt: int = int(data.get("play_time_sec", 0))
	var ts: String = str(data.get("timestamp", ""))
	# YYYY-MM-DDTHH:MM:SS → MM-DD HH:MM (짧게)
	var short_ts := ts.substr(5, 11) if ts.length() >= 16 else ts
	return "%s: Lv%d %s G%d %s [%02d:%02d]" % [
		prefix, level, class_name_str, gold, short_ts,
		int(pt / 60), int(pt) % 60,
	]


func _on_load(slot: int) -> void:
	if GameState.quick_load(slot):
		status_label.text = "Slot %d 로드 완료" % slot
		# 호출자가 scene 갱신할 수 있도록 signal 발화.
		slot_loaded.emit(slot)
		visible = false
	else:
		status_label.text = "Slot %d 비어 있음" % slot


func _on_save(slot: int) -> void:
	if GameState.quick_save(slot):
		status_label.text = "Slot %d 저장 완료" % slot
		refresh()
	else:
		status_label.text = "Slot %d 저장 실패" % slot


func _on_delete(slot: int) -> void:
	if H5SaveManager.delete_slot(slot):
		status_label.text = "Slot %d 삭제" % slot
		refresh()
	else:
		status_label.text = "Slot %d 비어 있음" % slot


signal slot_loaded(slot: int)
