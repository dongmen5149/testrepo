## 설정 패널 — 볼륨 / FPS 표시 / fullscreen.
class_name SettingsPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var bgm_slider: HSlider = $BG/BGMSlider
@onready var sfx_slider: HSlider = $BG/SFXSlider
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
	fps_check.toggled.connect(func(on):
		_show_fps = on; fps_label.visible = on; _save_config())
	fullscreen_check.toggled.connect(_on_fullscreen)
	_load_config()


func _load_config() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(CONFIG_PATH) == OK:
		bgm_slider.value = cfg.get_value("audio", "bgm", 70)
		sfx_slider.value = cfg.get_value("audio", "sfx", 80)
		fps_check.button_pressed = cfg.get_value("display", "fps", false)
		fullscreen_check.button_pressed = cfg.get_value("display", "fullscreen", false)
	else:
		bgm_slider.value = 70
		sfx_slider.value = 80


func _save_config() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "bgm", bgm_slider.value)
	cfg.set_value("audio", "sfx", sfx_slider.value)
	cfg.set_value("display", "fps", fps_check.button_pressed)
	cfg.set_value("display", "fullscreen", fullscreen_check.button_pressed)
	cfg.save(CONFIG_PATH)


func toggle() -> void:
	visible = not visible


func _on_bgm_volume(v: float) -> void:
	var db = -40.0 + (v / 100.0) * 40.0
	if Audio._bgm: Audio._bgm.volume_db = db
	Audio._bgm_target_db = db
	_save_config()


func _on_sfx_volume(v: float) -> void:
	var db = -40.0 + (v / 100.0) * 40.0
	if Audio._sfx: Audio._sfx.volume_db = db
	_save_config()


func _on_fullscreen(on: bool) -> void:
	if on:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	_save_config()


func _process(_dt: float) -> void:
	if _show_fps:
		fps_label.text = "FPS: %d" % Engine.get_frames_per_second()
