## 한글 대사 박스 UI.
##
## Interpreter 의 SituateDialogText / SituateNarration / SituateBallon /
## SituatePopup 핸들러에 연결. 한 번에 한 줄씩 표시 → 스페이스/엔터로 진행.
##
## Round 68 RE: 원본 `DIALOG_INFO::DialogWindow_Proc` (@0x71b48, 912B) 의
## main state byte (+0x2b) 는 0..7 의 8-way jumptable.
## state 0 = inactive / 1,3,6 = idle-busy / 2,4 = fade-in / 5,7 = HSB fade-out.
## sub-step counter (+0x29) 가 0→4 도달 시 phase finalize → SetDialogWindow.
## 본 Godot 구현은 typewriter 모드(글자 수 카운팅) 로 동일 효과를 단순화.
## 상세는 docs/h5/RE/npc_dialog.md.
class_name DialogBox
extends CanvasLayer

signal closed

# DIALOG_INFO 의 +0x2b main state byte 값 (logical 매핑, Godot 내부 미사용 — RE 참고용)
const DIALOG_STATE_INACTIVE       = 0  # 대화 종료, 외부 입력 받음 (DialogWindow_Proc → r0=0)
const DIALOG_STATE_IDLE_ACTIVE    = 1  # 대화 활성, busy (r0=1)
const DIALOG_STATE_FADE_IN_A      = 2  # phase A — phase data pool +0x10..+0x18
const DIALOG_STATE_IDLE_ACTIVE_2  = 3  # state 1 alias
const DIALOG_STATE_FADE_IN_B      = 4  # phase B — pool +0x1c..+0x24
const DIALOG_STATE_FADE_HSB_A     = 5  # phase C — pool +0x28..+0x30 + RestorePal/ChangeHSB
const DIALOG_STATE_IDLE_ACTIVE_3  = 6  # state 1 alias
const DIALOG_STATE_FADE_HSB_B     = 7  # phase D — pool +0x34..+0x3c + RestorePal/ChangeHSB

# Event_SituateDialogText 의 sub_state (+0xdf) → SetDialogWindow 인자 매핑
const DIALOG_SUBSTEP_FINAL        = 4         # +0x29 이 4 도달 시 phase 종료
const DIALOG_TRIGGER_FIRST        = Vector2i(1, 2)  # +0xdf==0 (첫 대화)
const DIALOG_TRIGGER_TYPE2        = Vector2i(4, 2)  # +0xdf==5 (다른 종류)
const DIALOG_TRIGGER_PAIR         = Vector2i(6, 5)  # +0xdf==2 (paired NPC)

@export var line_speed: float = 30.0   # chars/sec (typewriter)

@onready var bg: ColorRect = $BG
@onready var label: RichTextLabel = $BG/Label
@onready var name_tag: Label = $BG/NameTag
@onready var prompt: Label = $BG/Prompt

var _full_text: String = ""
var _shown_chars: int = 0
var _waiting: bool = false

# 선택지 모드
var _choices: Array = []
var _choice_idx: int = 0
var _choice_buttons: Array = []
signal choice_selected(idx: int)


func _ready() -> void:
	visible = false
	prompt.visible = false


func show_dialog(speaker: String, text: String) -> void:
	visible = true
	name_tag.text = speaker
	_full_text = text
	_shown_chars = 0
	label.text = ""
	_waiting = false
	prompt.visible = false
	_clear_choices()


## 선택지 표시 (대사 후 분기).
func show_choices(speaker: String, prompt_text: String, choices: Array) -> void:
	show_dialog(speaker, prompt_text)
	_choices = choices
	_choice_idx = 0
	_render_choices()


func _render_choices() -> void:
	_clear_choices()
	for i in _choices.size():
		var btn = Button.new()
		btn.text = "%d. %s" % [i + 1, _choices[i]]
		btn.position = Vector2(8, 80 + i * 18)
		btn.size = Vector2(280, 16)
		btn.pressed.connect(func(): _on_choice_pressed(i))
		bg.add_child(btn)
		_choice_buttons.append(btn)


func _on_choice_pressed(idx: int) -> void:
	choice_selected.emit(idx)
	_clear_choices()
	visible = false


func _clear_choices() -> void:
	for b in _choice_buttons: b.queue_free()
	_choice_buttons.clear()
	_choices.clear()


func _process(delta: float) -> void:
	if not visible: return
	if _shown_chars < _full_text.length():
		_shown_chars = min(_shown_chars + int(line_speed * delta) + 1,
				_full_text.length())
		label.text = _full_text.substr(0, _shown_chars)
		if _shown_chars >= _full_text.length():
			_waiting = true
			prompt.visible = true


func _input(event: InputEvent) -> void:
	if not visible: return
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("ui_select"):
		if _waiting:
			# close
			visible = false
			closed.emit()
		else:
			# fast-forward
			_shown_chars = _full_text.length()
			label.text = _full_text
			_waiting = true
			prompt.visible = true
		get_viewport().set_input_as_handled()
