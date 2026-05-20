## 설정 패널 — 볼륨 / FPS 표시 / fullscreen.
class_name SettingsPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var bgm_slider: HSlider = $BG/BGMSlider
@onready var sfx_slider: HSlider = $BG/SFXSlider
@onready var mute_check: CheckBox = $BG/MuteCheck   # Round 99
@onready var fps_check: CheckBox = $BG/FPSCheck
@onready var fullscreen_check: CheckBox = $BG/FullscreenCheck
@onready var fps_label: Label = $BG/FPSLabel
@onready var close_btn: Button = $BG/CloseButton

var _show_fps: bool = false


const CONFIG_PATH := "user://config.cfg"


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)
	bgm_slider.value_changed.connect(_on_bgm_volume)
	sfx_slider.value_changed.connect(_on_sfx_volume)
	# Round 99: MuteCheck 토글 시 R98 API 위임 (체크박스 ↔ F8 양방향 동기화).
	mute_check.toggled.connect(_on_mute_toggled)
	fps_check.toggled.connect(func(on):
		_show_fps = on; fps_label.visible = on; _save_config())
	fullscreen_check.toggled.connect(_on_fullscreen)
	_load_config()


func _load_config() -> void:
	var cfg := ConfigFile.new()
	var muted := false
	if cfg.load(CONFIG_PATH) == OK:
		bgm_slider.value = cfg.get_value("audio", "bgm", 70)
		sfx_slider.value = cfg.get_value("audio", "sfx", 80)
		muted = cfg.get_value("audio", "muted", false)
		fps_check.button_pressed = cfg.get_value("display", "fps", false)
		fullscreen_check.button_pressed = cfg.get_value("display", "fullscreen", false)
	else:
		bgm_slider.value = 70
		sfx_slider.value = 80
	# Round 97: 로드된 값을 AudioManager 에 즉시 반영 (이전엔 사용자가 슬라이더
	# 만지기 전까지 default -6dB 로 재생됐음).
	Audio.set_bgm_volume(bgm_slider.value)
	Audio.set_sfx_volume(sfx_slider.value)
	# Round 98: mute 상태도 영속 + 즉시 반영.
	Audio.set_muted(muted)
	# Round 99: MuteCheck 체크박스를 ConfigFile 의 muted 상태로 초기화. toggled
	# signal 재발화 방지를 위해 set_pressed_no_signal 사용 (set_muted 는 이미 위에서 호출).
	mute_check.set_pressed_no_signal(muted)


func _save_config() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "bgm", bgm_slider.value)
	cfg.set_value("audio", "sfx", sfx_slider.value)
	# Round 98: 현재 mute 상태 저장.
	cfg.set_value("audio", "muted", Audio.is_muted())
	cfg.set_value("display", "fps", fps_check.button_pressed)
	cfg.set_value("display", "fullscreen", fullscreen_check.button_pressed)
	cfg.save(CONFIG_PATH)


func toggle() -> void:
	visible = not visible


## Round 97: dB 변환을 AudioManager 의 자연 곡선 helper 로 위임 + SFX target_db
## 영속화 (이전엔 즉시 volume_db 만 변경, _fade_swap 시 -3dB 로 reset). 또한
## 이전의 `-40 + (v/100) * 40` 선형 dB 매핑은 -40~0 의 좁은 범위에서 비-자연.
## 새 매핑 = `linear_to_db(v/100)` 으로 v=100→0dB, v=50→-6dB, v=10→-20dB,
## v<1→-80dB(MUTE) — 청각적으로 균등.
func _on_bgm_volume(v: float) -> void:
	Audio.set_bgm_volume(v)
	_save_config()


func _on_sfx_volume(v: float) -> void:
	Audio.set_sfx_volume(v)
	_save_config()


## Round 99: MuteCheck 체크박스 → AudioManager.set_muted.
## Round 104: _save_config 호출 제거 — Audio.set_muted → mute_changed.emit →
## demo._on_audio_mute_changed → _settings._save_config 의 signal chain 이
## 이미 저장. 중복 save 제거로 단일 source of truth 유지.
## sync_mute_check(state) helper 가 외부 호출자에서 체크박스를 silent update.
func _on_mute_toggled(on: bool) -> void:
	Audio.set_muted(on)


## F8 외부 토글 후 호출되어 체크박스를 신호 발화 없이 동기화.
func sync_mute_check(state: bool) -> void:
	mute_check.set_pressed_no_signal(state)


func _on_fullscreen(on: bool) -> void:
	if on:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	_save_config()


func _process(_dt: float) -> void:
	if _show_fps:
		fps_label.text = "FPS: %d" % Engine.get_frames_per_second()
