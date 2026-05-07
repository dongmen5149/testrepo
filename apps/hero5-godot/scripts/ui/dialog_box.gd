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
