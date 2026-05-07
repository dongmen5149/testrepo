## BGM / SFX 매니저 (싱글톤).
##
## 원본: Event_Scene_ChangeBgm(bgm_id) opcode + AndroidService::putMusicClip /
## putSoundClip 호출. 우리 구현은 단순 AudioStreamPlayer 두 개 (BGM, SFX).
##
## 자산: assets/sounds/bgm_NN.ogg, eff_NN.ogg.
extends Node

const SOUND_DIR := "res://assets/sounds/"

var _bgm: AudioStreamPlayer
var _sfx: AudioStreamPlayer
var _current_bgm: int = -1


func _ready() -> void:
	_bgm = AudioStreamPlayer.new()
	_bgm.bus = "Master"
	_bgm.volume_db = -6
	add_child(_bgm)
	_sfx = AudioStreamPlayer.new()
	_sfx.bus = "Master"
	_sfx.volume_db = -3
	add_child(_sfx)


func play_bgm(bgm_id: int) -> void:
	if bgm_id == _current_bgm and _bgm.playing:
		return
	var path := SOUND_DIR + "bgm_%02d.ogg" % bgm_id
	if not FileAccess.file_exists(path):
		push_warning("bgm not found: %s" % path)
		return
	var stream = load(path)
	if stream is AudioStream:
		_bgm.stream = stream
		_bgm.play()
		_current_bgm = bgm_id


func stop_bgm() -> void:
	_bgm.stop()
	_current_bgm = -1


func play_sfx(eff_id: int) -> void:
	var path := SOUND_DIR + "eff_%02d.ogg" % eff_id
	if not FileAccess.file_exists(path):
		push_warning("sfx not found: %s" % path)
		return
	var stream = load(path)
	if stream is AudioStream:
		_sfx.stream = stream
		_sfx.play()
