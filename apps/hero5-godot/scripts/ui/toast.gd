## 토스트 알림 — 우상단에 잠시 표시 후 페이드 아웃.
class_name Toast
extends CanvasLayer


static func show_msg(parent: Node, text: String, duration: float = 2.5,
		color: Color = Color(1, 1, 0.4, 1)) -> void:
	var t = Toast.new()
	t.layer = 50
	parent.add_child(t)
	t._show(text, duration, color)


var _label: Label
var _bg: ColorRect


func _show(text: String, duration: float, color: Color) -> void:
	_bg = ColorRect.new()
	_bg.color = Color(0, 0, 0, 0.7)
	_bg.position = Vector2(60, 110)
	_bg.size = Vector2(252, 28)
	add_child(_bg)
	_label = Label.new()
	_label.text = text
	_label.position = Vector2(8, 4)
	_label.size = Vector2(240, 24)
	_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	_label.add_theme_color_override("font_color", color)
	_label.add_theme_font_size_override("font_size", 11)
	_bg.add_child(_label)
	# fade
	var tween := create_tween()
	tween.tween_interval(duration - 0.6)
	tween.tween_property(_bg, "modulate:a", 0.0, 0.6)
	tween.tween_callback(queue_free)
