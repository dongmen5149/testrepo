## 데미지/이펙트 숫자 popup.
##
## 호출: `DamagePopup.spawn(parent, position, "+15", Color.RED)` 같은 식.
## 1초 동안 위로 떠오르며 페이드 아웃.
class_name DamagePopup
extends Label


static func spawn(parent: Node, pos: Vector2, text: String,
		color: Color = Color.WHITE) -> DamagePopup:
	var p = DamagePopup.new()
	p.text = text
	p.modulate = color
	p.position = pos
	p.add_theme_font_size_override("font_size", 18)
	p.z_index = 100
	parent.add_child(p)
	p._animate()
	return p


func _animate() -> void:
	var tween := create_tween().set_parallel(true)
	tween.tween_property(self, "position:y", position.y - 40, 0.8)\
		.set_ease(Tween.EASE_OUT)
	tween.tween_property(self, "modulate:a", 0.0, 0.8)\
		.set_delay(0.2)
	tween.chain().tween_callback(queue_free)
