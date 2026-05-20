## 토스트 알림 — 우상단에 잠시 표시 후 페이드 아웃.
##
## Round 95: severity 라벨 (INFO/SUCCESS/WARN/ERROR) + fade-in tween +
## 동시 다수 toast 의 vertical stack. R86-R94 동안 demo/battle/SaveListPanel
## 등 다양한 발화점에서 인스턴스만 생성하고 색상/위치 일관성 부재 +
## 1 frame 내 다발 시 같은 좌표 (60, 110) 에 겹쳐 표시되던 문제 해결.
class_name Toast
extends CanvasLayer

enum Severity { INFO, SUCCESS, WARN, ERROR }

const COLORS := {
	Severity.INFO:    Color(1, 1, 0.4, 1),       # 노랑 (기본)
	Severity.SUCCESS: Color(0.5, 1, 0.5, 1),     # 연두
	Severity.WARN:    Color(1, 0.7, 0.3, 1),     # 주황
	Severity.ERROR:   Color(1, 0.4, 0.4, 1),     # 빨강
}
const FADE_IN_DUR := 0.18
const FADE_OUT_DUR := 0.6
const STACK_Y_BASE := 110.0
const STACK_Y_STEP := 32.0

# 현재 화면에 활성화된 toast 들 (stack 위치 계산용).
static var _active_toasts: Array = []


static func show_msg(parent: Node, text: String, duration: float = 2.5,
		color: Color = Color(1, 1, 0.4, 1)) -> void:
	# R95: 기존 API 호환 (color 직접 전달).
	var t = Toast.new()
	t.layer = 50
	parent.add_child(t)
	t._show(text, duration, color)


## R95: severity 기반 단축 API.
static func info(parent: Node, text: String, duration: float = 2.5) -> void:
	show_severity(parent, text, Severity.INFO, duration)


static func success(parent: Node, text: String, duration: float = 2.5) -> void:
	show_severity(parent, text, Severity.SUCCESS, duration)


static func warn(parent: Node, text: String, duration: float = 2.8) -> void:
	show_severity(parent, text, Severity.WARN, duration)


static func error(parent: Node, text: String, duration: float = 3.2) -> void:
	show_severity(parent, text, Severity.ERROR, duration)


static func show_severity(parent: Node, text: String, severity: int,
		duration: float = 2.5) -> void:
	show_msg(parent, text, duration, COLORS.get(severity, COLORS[Severity.INFO]))


var _label: Label
var _bg: ColorRect


func _show(text: String, duration: float, color: Color) -> void:
	# stack Y 결정 — 활성 toast 수만큼 아래로 밀어냄.
	var stack_y := STACK_Y_BASE + STACK_Y_STEP * float(_active_toasts.size())
	_active_toasts.append(self)
	_bg = ColorRect.new()
	_bg.color = Color(0, 0, 0, 0.7)
	_bg.position = Vector2(60, stack_y)
	_bg.size = Vector2(252, 28)
	_bg.modulate.a = 0.0
	add_child(_bg)
	_label = Label.new()
	_label.text = text
	_label.position = Vector2(8, 4)
	_label.size = Vector2(240, 24)
	_label.autowrap_mode = TextServer.AUTOWRAP_OFF
	_label.add_theme_color_override("font_color", color)
	_label.add_theme_font_size_override("font_size", 11)
	_bg.add_child(_label)
	# R95: fade-in + idle + fade-out + cleanup.
	var idle_dur: float = max(duration - FADE_IN_DUR - FADE_OUT_DUR, 0.1)
	var tween := create_tween()
	tween.tween_property(_bg, "modulate:a", 1.0, FADE_IN_DUR)
	tween.tween_interval(idle_dur)
	tween.tween_property(_bg, "modulate:a", 0.0, FADE_OUT_DUR)
	tween.tween_callback(_finish)


func _finish() -> void:
	_active_toasts.erase(self)
	queue_free()
