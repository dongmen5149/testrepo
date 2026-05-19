## Scene 전환 라우터 (Round 82, autoload).
##
## 게임 전체의 scene 전환을 한 곳에서 관리하는 state machine.
## SceneFader 의 단순 fade + change_scene 위에 의미적 라우팅 (Title / ClassSelect /
## Demo / GameOver) 과 transition guard (중복 전환 방지) 를 얹는다.
##
## 사용:
##   SceneRouter.to_title(self)
##   SceneRouter.to_class_select(self)
##   SceneRouter.to_demo(self)              # GameState 이미 로드된 상태
##   SceneRouter.to_demo_with_load(self, 0)  # slot 로드 후 전환
##   SceneRouter.to_game_over(self, "monster_kill")
##   SceneRouter.quit_to_title(self, true)   # confirm prompt + 전환
##
## 의미상:
##   Title → ClassSelect (New Game) | Demo (Continue)
##   ClassSelect → Demo (start)
##   Demo → GameOver (hero death) | Title (Quit-to-Title)
##   GameOver → Demo (Continue load) | Title (Give up)
extends Node

signal scene_changing(from_state: String, to_state: String)
signal scene_changed(state: String)

const SceneFader = preload("res://scripts/ui/scene_fader.gd")

enum State { TITLE, CLASS_SELECT, DEMO, GAME_OVER }

const SCENE_PATHS := {
	State.TITLE: "res://scenes/title.tscn",
	State.CLASS_SELECT: "res://scenes/class_select.tscn",
	State.DEMO: "res://scenes/demo.tscn",
	State.GAME_OVER: "res://scenes/game_over.tscn",
}

var _current_state: State = State.TITLE
var _transitioning: bool = false
var _last_game_over_reason: String = ""


func current_state() -> State:
	return _current_state


func current_state_name() -> String:
	return State.keys()[_current_state]


func is_transitioning() -> bool:
	return _transitioning


## Title 으로 전환 (게임 종료 후 메뉴 복귀, GameOver 의 Give up).
func to_title(node: Node) -> void:
	_change(node, State.TITLE)


## ClassSelect 로 전환 (New Game).
func to_class_select(node: Node) -> void:
	_change(node, State.CLASS_SELECT)


## Demo (게임 본편) 로 전환 — GameState 이미 세팅된 상태 가정.
func to_demo(node: Node) -> void:
	_change(node, State.DEMO)


## Slot 로드 후 Demo 진입. 로드 실패 시 false 반환 (전환 안 함).
func to_demo_with_load(node: Node, slot: int) -> bool:
	if not GameState.quick_load(slot):
		return false
	to_demo(node)
	return true


## GameOver scene 으로 전환. reason 은 GameOver scene 에서 표시.
func to_game_over(node: Node, reason: String = "") -> void:
	_last_game_over_reason = reason
	_change(node, State.GAME_OVER)


func last_game_over_reason() -> String:
	return _last_game_over_reason


## Quit-to-Title prompt. confirm 이면 popup 으로 확인, 아니면 즉시 전환.
func quit_to_title(node: Node, confirm: bool = true) -> void:
	if not confirm:
		to_title(node)
		return
	var popup := AcceptDialog.new()
	popup.dialog_text = "타이틀로 돌아가시겠습니까?\n(저장하지 않은 진행도는 잃을 수 있습니다)"
	popup.title = "타이틀로"
	popup.add_cancel_button("취소")
	popup.confirmed.connect(func():
		popup.queue_free()
		to_title(node))
	popup.canceled.connect(func(): popup.queue_free())
	node.add_child(popup)
	popup.popup_centered()


func _change(node: Node, to: State) -> void:
	if _transitioning:
		return
	if not node or not node.is_inside_tree():
		return
	var from := _current_state
	_transitioning = true
	scene_changing.emit(State.keys()[from], State.keys()[to])
	# fade-out + change
	_current_state = to
	SceneFader.change_scene(node, SCENE_PATHS[to])
	# scene_changed 는 새 scene 의 _ready 시 자동 emit (scene 측에서 notify_ready 호출 권장)
	_transitioning = false


## 새 scene 의 _ready 에서 호출 — 전환 완료 알림.
func notify_ready() -> void:
	scene_changed.emit(State.keys()[_current_state])
