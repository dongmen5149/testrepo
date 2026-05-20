## 화면 상단 HUD — HP/SP/Lv/Gold 미니바.
##
## GameState.state_changed 시 자동 갱신.
## Round 102: AudioIndicator (♪/🔇) — Audio.mute_changed signal 구독.
class_name HUD
extends CanvasLayer

@onready var hp_bar: ProgressBar = $HUD/HPBar
@onready var sp_bar: ProgressBar = $HUD/SPBar
@onready var hp_label: Label = $HUD/HPLabel
@onready var sp_label: Label = $HUD/SPLabel
@onready var lv_label: Label = $HUD/LvLabel
@onready var gold_label: Label = $HUD/GoldLabel
@onready var audio_indicator: Label = $HUD/AudioIndicator   # Round 102


const AUDIO_ON_TEXT := "♪"
const AUDIO_OFF_TEXT := "🔇"
const AUDIO_ON_COLOR := Color(0.6, 0.9, 0.6, 1)   # 연두
const AUDIO_OFF_COLOR := Color(1, 0.4, 0.4, 1)    # 빨강


func _ready() -> void:
	GameState.state_changed.connect(_refresh)
	# Round 102: AudioManager 의 mute_changed signal 구독으로 polling 없이
	# indicator 동기화. F8 / SettingsPanel 어느 쪽에서 토글해도 HUD 즉시 갱신.
	Audio.mute_changed.connect(_on_mute_changed)
	# Round 103: AudioIndicator 클릭 시 F8 와 동일한 mute 토글 호출.
	audio_indicator.gui_input.connect(_on_audio_indicator_input)
	_refresh()
	_on_mute_changed(Audio.is_muted())   # 초기 상태 적용


## Round 103: indicator 클릭 (좌클릭 release) → Audio.toggle_mute().
## demo.gd 의 mute_changed handler (R103) 가 Toast / 체크박스 / ConfigFile 동기화.
func _on_audio_indicator_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and not event.pressed \
			and event.button_index == MOUSE_BUTTON_LEFT:
		Audio.toggle_mute()


func _refresh() -> void:
	hp_bar.max_value = GameState.max_hp
	hp_bar.value = GameState.hp
	hp_label.text = "HP %d/%d" % [GameState.hp, GameState.max_hp]
	sp_bar.max_value = GameState.max_sp
	sp_bar.value = GameState.sp
	sp_label.text = "SP %d/%d" % [GameState.sp, GameState.max_sp]
	lv_label.text = "Lv.%d" % GameState.level
	gold_label.text = "%dG" % GameState.gold


func _on_mute_changed(muted: bool) -> void:
	if muted:
		audio_indicator.text = AUDIO_OFF_TEXT
		audio_indicator.add_theme_color_override("font_color", AUDIO_OFF_COLOR)
	else:
		audio_indicator.text = AUDIO_ON_TEXT
		audio_indicator.add_theme_color_override("font_color", AUDIO_ON_COLOR)
