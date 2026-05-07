## 씬 전환 페이드 헬퍼.
##
## 사용:
##   await SceneFader.change_scene(self, "res://scenes/demo.tscn")
##   SceneFader.fade_in(self)
class_name SceneFader
extends RefCounted


## 화면을 검정으로 페이드아웃 → 씬 변경.
static func change_scene(node: Node, target_path: String, dur: float = 0.3) -> void:
	var rect := _make_overlay(node, Color(0, 0, 0, 0))
	if rect == null:
		node.get_tree().change_scene_to_file(target_path)
		return
	var tween := node.create_tween()
	tween.tween_property(rect, "color:a", 1.0, dur)
	await tween.finished
	node.get_tree().change_scene_to_file(target_path)


## 씬 진입 시 검정 → 투명으로 페이드인.
static func fade_in(node: Node, dur: float = 0.3) -> void:
	var rect := _make_overlay(node, Color(0, 0, 0, 1))
	if rect == null: return
	var tween := node.create_tween()
	tween.tween_property(rect, "color:a", 0.0, dur)
	await tween.finished
	rect.get_parent().queue_free()


static func _make_overlay(node: Node, start_color: Color) -> ColorRect:
	if node == null or not node.is_inside_tree(): return null
	var layer := CanvasLayer.new()
	layer.layer = 100
	node.add_child(layer)
	var rect := ColorRect.new()
	rect.color = start_color
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var size = node.get_viewport().get_visible_rect().size
	rect.size = size
	rect.position = Vector2.ZERO
	layer.add_child(rect)
	return rect
