## BGM / SFX 매니저 (싱글톤).
##
## 원본: Event_Scene_ChangeBgm(bgm_id) opcode + AndroidService::putMusicClip /
## putSoundClip 호출. 우리 구현은 단순 AudioStreamPlayer 두 개 (BGM, SFX).
##
## 자산: assets/sounds/bgm_NN.ogg, eff_NN.ogg.
##
## Round 101: Audio bus 분리 — Master 단일 → Master + BGM + SFX 3 bus
## (res://default_bus_layout.tres). BGM/SFX bus 가 Master 로 send 되며 각자
## 독립 dB / mute 제어 가능. 이전엔 AudioStreamPlayer.volume_db 만 변경 →
## fade_swap 등에서 reset 위험. 이제 AudioServer.set_bus_volume_db /
## set_bus_mute 가 영속 적용 → player.volume_db 는 0 으로 고정 유지.
extends Node

const SOUND_DIR := "res://assets/sounds/"
const BGM_BUS_NAME := "BGM"
const SFX_BUS_NAME := "SFX"

var _bgm: AudioStreamPlayer
var _sfx: AudioStreamPlayer
var _current_bgm: int = -1
var _bgm_bus_idx: int = -1
var _sfx_bus_idx: int = -1


func _ready() -> void:
	# Round 101: bus index lookup (default_bus_layout.tres 로 미리 생성됨).
	_bgm_bus_idx = AudioServer.get_bus_index(BGM_BUS_NAME)
	_sfx_bus_idx = AudioServer.get_bus_index(SFX_BUS_NAME)
	# tres 미적용/누락 시 Master fallback (안전 가드).
	var bgm_bus := BGM_BUS_NAME if _bgm_bus_idx >= 0 else "Master"
	var sfx_bus := SFX_BUS_NAME if _sfx_bus_idx >= 0 else "Master"
	_bgm = AudioStreamPlayer.new()
	_bgm.bus = bgm_bus
	_bgm.volume_db = 0  # bus 가 dB 관리, player 는 0 유지.
	add_child(_bgm)
	_sfx = AudioStreamPlayer.new()
	_sfx.bus = sfx_bus
	_sfx.volume_db = 0
	add_child(_sfx)
	# tres 의 초기 bus dB (BGM -6, SFX -3) 가 default. 추후 SettingsPanel 의
	# _load_config 가 ConfigFile 값으로 덮어씀.


@export var fade_duration: float = 0.6
var _bgm_target_db: float = -6.0
# Round 97: SFX 도 target_db 영속화 (이전엔 즉시 volume_db 만 변경, fade/swap 시 잃음).
var _sfx_target_db: float = -3.0

# Round 97: slider (0..100 linear) → 자연 dB 곡선.
# - v=100 → 0 dB
# - v=50  → ≈ -6 dB (절반 청각)
# - v=10  → ≈ -20 dB (배경음)
# - v<1   → MUTE_DB (-80 dB, 사실상 무음)
const MUTE_THRESHOLD := 1.0
const MUTE_DB := -80.0


static func slider_to_db(v: float) -> float:
	if v < MUTE_THRESHOLD:
		return MUTE_DB
	# linear_to_db: y = 20 * log10(x). v=100 → x=1.0 → 0 dB. v=10 → x=0.1 → -20 dB.
	return linear_to_db(clampf(v, 0.0, 100.0) / 100.0)


## Round 101: bus-level volume 적용. bus index 가 유효한 경우 AudioServer.
## set_bus_volume_db 사용, 아니면 player.volume_db fallback (Master bus 직접
## 변경은 부적절하므로 player level 만 변경).
func set_bgm_volume(v: float) -> void:
	_bgm_target_db = slider_to_db(v)
	if _bgm_bus_idx >= 0:
		AudioServer.set_bus_volume_db(_bgm_bus_idx, _bgm_target_db)
	elif _bgm and not _muted:
		_bgm.volume_db = _bgm_target_db


func set_sfx_volume(v: float) -> void:
	_sfx_target_db = slider_to_db(v)
	if _sfx_bus_idx >= 0:
		AudioServer.set_bus_volume_db(_sfx_bus_idx, _sfx_target_db)
	elif _sfx and not _muted:
		_sfx.volume_db = _sfx_target_db


# Round 98: Mute 토글. F8 키 또는 SettingsPanel 의 mute 체크박스에서 호출.
# Round 101: bus-level mute 사용 (AudioServer.set_bus_mute) — bus volume 은
# 그대로 유지하면서 mute on/off 만 토글. 이전 volume_db swap 보다 깨끗.
# Round 102: mute_changed 시그널 신규 — HUD/SettingsPanel 등 listener 가
# 체크박스/indicator 를 polling 없이 갱신.
signal mute_changed(muted: bool)
var _muted: bool = false


func is_muted() -> bool:
	return _muted


func set_muted(mute: bool) -> void:
	var changed := (_muted != mute)
	_muted = mute
	if _bgm_bus_idx >= 0:
		AudioServer.set_bus_mute(_bgm_bus_idx, _muted)
	elif _bgm:
		_bgm.volume_db = (MUTE_DB if _muted else _bgm_target_db)
	if _sfx_bus_idx >= 0:
		AudioServer.set_bus_mute(_sfx_bus_idx, _muted)
	elif _sfx:
		_sfx.volume_db = (MUTE_DB if _muted else _sfx_target_db)
	# Round 102: 상태 변화 시에만 emit (체크박스 silent update 가 동일 값
	# set_muted 호출하는 cycle 의 무한 발화 방지).
	if changed:
		mute_changed.emit(_muted)


## 토글 후 새 상태 반환 (UI 가 텍스트/체크박스 동기화).
func toggle_mute() -> bool:
	set_muted(not _muted)
	return _muted


func play_bgm(bgm_id: int) -> void:
	if bgm_id == _current_bgm and _bgm.playing:
		return
	var path := SOUND_DIR + "bgm_%02d.ogg" % bgm_id
	if not FileAccess.file_exists(path):
		push_warning("bgm not found: %s" % path)
		return
	var stream = load(path)
	if not stream is AudioStream: return
	if _bgm.playing:
		# fade out, swap, fade in
		_fade_swap(stream, bgm_id)
	else:
		_bgm.stream = stream
		# Round 101: bus 가 volume 관리 → player 는 0dB 유지 (bus 미적용 시
		# fallback 으로 _bgm_target_db 사용).
		_bgm.volume_db = 0.0 if _bgm_bus_idx >= 0 else _bgm_target_db
		_bgm.play()
		_current_bgm = bgm_id


## Round 101: fade-out / fade-in 은 player.volume_db 의 상대적 변화로 수행.
## bus 가 절대 dB 를 관리하고 player 는 상대 attenuator 역할.
func _fade_swap(new_stream: AudioStream, bgm_id: int) -> void:
	var fade_out_target := -40.0  # 충분히 낮춰서 transition 자연스럽게
	var fade_in_target := 0.0 if _bgm_bus_idx >= 0 else _bgm_target_db
	var t := create_tween()
	t.tween_property(_bgm, "volume_db", fade_out_target, fade_duration / 2)
	t.tween_callback(func():
		_bgm.stream = new_stream
		_bgm.play()
		_current_bgm = bgm_id)
	t.tween_property(_bgm, "volume_db", fade_in_target, fade_duration / 2)


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
		# Round 97: 매 재생마다 target_db 재적용 (외부에서 volume_db 가 변형됐을 대비).
		# Round 98: _muted 시 MUTE_DB (bus fallback path).
		# Round 101: bus 적용 시 player 는 0dB (bus 가 volume + mute 관리).
		_sfx.volume_db = (
			0.0 if _sfx_bus_idx >= 0
			else (MUTE_DB if _muted else _sfx_target_db)
		)
		_sfx.play()
