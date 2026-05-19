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


## Round 84: in-scene map warp fade — 검정으로 fade-out → callback (실제 warp 수행) →
## 검정 → 투명 fade-in. scene 전환 없이 현재 scene 내부에서 시각적 전환만.
##
## 사용:
##   await SceneFader.warp_fade(self, func(): _apply_new_scene(), 0.25, 0.25)
##
## `mid_callback` 은 화면이 완전히 검정이 된 직후 호출됨 — map_id 변경, hero 위치
## 이동 등 시각적으로 instant 해야 할 작업 수행. mid_callback 이 끝나면 자동으로
## fade-in.
static func warp_fade(node: Node, mid_callback: Callable, out_dur: float = 0.25, in_dur: float = 0.25) -> void:
	if node == null or not node.is_inside_tree():
		mid_callback.call()
		return
	# Fade-out (투명 → 검정)
	var rect := _make_overlay(node, Color(0, 0, 0, 0))
	if rect == null:
		mid_callback.call()
		return
	var t_out := node.create_tween()
	t_out.tween_property(rect, "color:a", 1.0, out_dur)
	await t_out.finished
	# 중간 콜백 — 실제 warp (map 변경, hero 위치 등) 수행
	mid_callback.call()
	# Fade-in (검정 → 투명)
	var t_in := node.create_tween()
	t_in.tween_property(rect, "color:a", 0.0, in_dur)
	await t_in.finished
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
