## 한글 대사 박스 UI.
##
## Interpreter 의 SituateDialogText / SituateNarration / SituateBallon /
## SituatePopup 핸들러에 연결. 한 번에 한 줄씩 표시 → 스페이스/엔터로 진행.
class_name DialogBox
extends CanvasLayer

signal closed

@export var line_speed: float = 30.0   # chars/sec (typewriter)

@onready var bg: ColorRect = $BG
@onready var label: RichTextLabel = $BG/Label
@onready var name_tag: Label = $BG/NameTag
@onready var prompt: Label = $BG/Prompt

var _full_text: String = ""
var _shown_chars: int = 0
var _waiting: bool = false


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
