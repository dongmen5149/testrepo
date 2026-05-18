## CHAR/HERO 캐릭터 컨트롤러.
##
## 원본 (libHeroesLore5.so) 의 CHAR 클래스 매핑:
##   this[0x2c] = motion   (우리: var motion_state)
##   this[0x2d] = dir      (우리: var direction 0=down,1=left,2=right,3=up — 추정)
##   this[0x2e] = frame    (자동 애니메이션)
##   GetMaxFrame(motion, dir) = SPRITE_DATA 에서 읽음 (우리: 배열 lookup)
##
## Round 50 의 host CHAR interface 13 method (+ 4 추가) 가 monster_ai 의 runtime
## 에서 호출됨. battle_system 의 turn-based stub 대신 — character 가 hero 또는
## monster 일 때 map 좌표 기반 정확한 값을 반환 (Round 61).
##
## 4방향 이동: WASD / 화살표.
## 충돌은 Map.collision_at(x, y) 호출 (구현은 map 측에서 처리).
class_name H5Character
extends Sprite2D

# 내부 motion state (sprite anim 용)
const MOTION_WALK := 0
const MOTION_RUN := 1
const MOTION_STAND := 2

# 원본 CHAR motion enum (Round 50 RE — host_get_motion 에서 반환):
#   0 = idle, 1 = walk, 5 = run, 6 = attack, 9 = die, 12 = skill_cast
const HOST_MOTION_IDLE := 0
const HOST_MOTION_WALK := 1
const HOST_MOTION_RUN := 5
const HOST_MOTION_ATTACK := 6
const HOST_MOTION_DIE := 9
const HOST_MOTION_CAST := 12

# direction enum (원본과 일치 가정)
const DIR_DOWN := 0
const DIR_LEFT := 1
const DIR_RIGHT := 2
const DIR_UP := 3

const TILE_SIZE := 32   # 1 tile = 32 px (map_renderer 와 일치)

@export var move_speed: float = 80.0   # px/s
@export var sprite_dir: String = "res://assets/sprites/img0/000"  # 캐릭터 sprite 디렉토리

## Round 61: character 의 역할 — true = 영웅(hero), false = 몬스터.
## hero 는 입력으로 움직이고, monster 는 AI 가 host method 를 호출하여 제어.
@export var is_hero: bool = true

## monster 가 추적할 hero 참조 (spawner 가 설정). hero 자신은 사용 안 함.
var target_hero: Node2D = null

var motion: int = MOTION_STAND
var direction: int = DIR_DOWN
var frame_idx: int = 0
var _frame_timer: float = 0.0
var _frame_textures: Dictionary = {}   # frame_idx → Texture (single anim)

## Round 61: AI host 상태 — character.gd 가 monster 일 때 사용.
var hp: int = 100
var max_hp: int = 100
var dead: bool = false
var stunned: bool = false
## host_motion 강제 override (state 별로 monster_ai 가 attack/cast 등으로 변경)
var _forced_host_motion: int = -1
var _cooldowns: Dictionary = {}        # skill_id → remaining frames
## ai_cast_skill 가 호출되면 emit, demo.gd 가 처리 (실 데미지 적용)
signal ai_skill_cast(skill_id: int, source: Node2D)
# 4-방향 walk-cycle: dir → [frame_idx,...]
var _walk_frames: Dictionary = {
	DIR_DOWN: [0, 1, 2, 1],
	DIR_LEFT: [3, 4, 5, 4],
	DIR_RIGHT: [6, 7, 8, 7],
	DIR_UP: [9, 10, 11, 10],
}
var _stand_frames: Dictionary = {
	DIR_DOWN: [0],
	DIR_LEFT: [3],
	DIR_RIGHT: [6],
	DIR_UP: [9],
}

signal moved(new_pos: Vector2)


# === Round 61: AI host CHAR interface (monster_ai.gd 가 호출) ===
##
## 13 base + 4 추가 = 17 method. battle_system.gd 의 turn-based stub 을 대체.
## monster_ai 의 _host_call_bool / _host_call_int 가 has_method() check 후 호출,
## 미정의 시 default 반환. 따라서 hero 인스턴스도 안전하게 host 로 사용 가능.

## 사망 여부 — _ai_action 진입 직후 체크. dead=true 면 AI 중단.
func is_die() -> bool:
	return dead or hp <= 0

## 기절(stunned) — _ai_action 시작 시 체크.
func is_stunned() -> bool:
	return stunned

## 현재 motion (원본 CHAR enum). _state_set_attack_motion / _state_skill_cast 가
## 잠깐 override 함. 그 외엔 내부 motion state 매핑.
func get_motion() -> int:
	if _forced_host_motion >= 0:
		return _forced_host_motion
	if dead: return HOST_MOTION_DIE
	match motion:
		MOTION_STAND: return HOST_MOTION_IDLE
		MOTION_WALK: return HOST_MOTION_WALK
		MOTION_RUN: return HOST_MOTION_RUN
	return HOST_MOTION_IDLE

func is_attack_able() -> bool:
	return not dead and not stunned and hp > 0

## skill_id 의 cooldown 이 만료됐고 살아있으면 true.
func is_able_skill(skill_id: int) -> bool:
	if dead or stunned: return false
	return int(_cooldowns.get(skill_id, 0)) <= 0

func get_dir() -> int:
	return direction

func set_dir(d: int) -> void:
	direction = d & 3

## monster 가 hero 쪽으로 방향 전환. tile coord diff 의 dominant axis 사용.
func hero_turn_direction() -> void:
	if is_hero or target_hero == null: return
	var dx = int(target_hero.position.x - position.x)
	var dy = int(target_hero.position.y - position.y)
	if abs(dx) >= abs(dy):
		direction = DIR_RIGHT if dx > 0 else DIR_LEFT
	else:
		direction = DIR_DOWN if dy > 0 else DIR_UP

## hero 까지의 tile 거리 (Chebyshev — king move). monster 가 사정거리 판단에 사용.
## hero 자신이거나 target_hero 미설정 시 9999 (Round 50 default 와 호환).
func fast_distance_to_hero() -> int:
	if is_hero or target_hero == null: return 9999
	var dx = abs(int(target_hero.position.x - position.x)) / TILE_SIZE
	var dy = abs(int(target_hero.position.y - position.y)) / TILE_SIZE
	return max(dx, dy)

## state 4/6 (Round 50) 진입 시 호출. set_attack_motion 후 다음 frame 에 ai_cast_skill 호출.
func set_attack_motion(skill_id: int) -> void:
	_forced_host_motion = HOST_MOTION_ATTACK
	# skill_id 자체는 ai_cast_skill 가 처리. 여기선 motion 만 변경.

## state 5/7/8 의 _do_cast — 스킬 발동 emit. demo.gd 등이 실 데미지 처리.
func ai_cast_skill(skill_id: int) -> void:
	if dead or stunned: return
	_forced_host_motion = HOST_MOTION_CAST
	ai_skill_cast.emit(skill_id, self)

## cooldown 등록 (frame 단위, 1 frame ≈ 1/30s 가정).
## skill 의 cooldown 데이터는 skills.json stats[9] (초) — caller 가 frame 변환.
func set_cool_time(skill_id: int) -> void:
	# 기본 30 frame ≈ 1 초. skill 별 정확한 cd 는 demo 가 ai_skill_cast 받고 별도 설정.
	if not _cooldowns.has(skill_id):
		_cooldowns[skill_id] = 30

## state 9 — skill 끝났음. motion 원복.
func skill_end() -> void:
	_forced_host_motion = -1

## attack range 안에 hero 가 있는지 — fast_distance_to_hero 와 비교.
func ai_check_irect_hit(range_val: int) -> bool:
	if range_val <= 0: range_val = 1
	return fast_distance_to_hero() <= range_val

## ai_check_visibility — 단순화: distance < idx 가 시야 안인 것으로 가정.
## 실제 게임은 obstacle / line-of-sight check. R61 단순화.
func ai_check_visibility(idx: int) -> bool:
	if idx <= 0: idx = 8   # 기본 시야 8 tile
	return fast_distance_to_hero() <= idx

## ai_all_dead — 자기 자신 사망 여부 (group 전체는 spawner 가 관리).
func ai_all_dead() -> bool:
	return dead

## ai_tutorial_flag — 튜토리얼 모드는 게임 진척 이후 false. 단순 fallback.
func ai_tutorial_flag(_idx: int) -> bool:
	return false


## demo / spawner 가 monster 의 HP/dead 갱신 시 호출. 사망 시 motion=die + signal 등.
func take_damage(dmg: int) -> void:
	if dead: return
	hp = max(0, hp - dmg)
	if hp == 0:
		dead = true
		_forced_host_motion = HOST_MOTION_DIE


## 매 frame 호출 — cooldown decrement. monster_ai.process 와 동일 주기 가정.
## hero 는 자체 _physics_process 사용, monster 는 demo 가 별도로 cooldown_tick.
func cooldown_tick() -> void:
	for k in _cooldowns.keys():
		_cooldowns[k] = max(0, int(_cooldowns[k]) - 1)


func _ready() -> void:
	centered = true
	_load_frames()
	_apply_frame()


func _load_frames() -> void:
	var d := DirAccess.open(sprite_dir)
	if d == null:
		push_warning("character sprite dir not found: %s" % sprite_dir)
		return
	d.list_dir_begin()
	var fname := d.get_next()
	while fname != "":
		if fname.begins_with("frame_") and fname.ends_with(".png"):
			# frame_NN_WxH_palM.png
			var parts = fname.split("_")
			if parts.size() >= 2:
				var n = int(parts[1])
				_frame_textures[n] = load(sprite_dir + "/" + fname)
		fname = d.get_next()
	if _frame_textures.size() == 0:
		push_warning("no frames in %s" % sprite_dir)


func _physics_process(delta: float) -> void:
	# Round 61: monster 는 입력으로 움직이지 않음 (AI runtime 이 host method 로 제어).
	if not is_hero:
		_advance_anim(delta)
		return

	var move := Vector2.ZERO
	if Input.is_action_pressed("ui_up"):    move.y -= 1; direction = DIR_UP
	if Input.is_action_pressed("ui_down"):  move.y += 1; direction = DIR_DOWN
	if Input.is_action_pressed("ui_left"):  move.x -= 1; direction = DIR_LEFT
	if Input.is_action_pressed("ui_right"): move.x += 1; direction = DIR_RIGHT

	if move.length_squared() > 0:
		motion = MOTION_WALK
		var step := move.normalized() * move_speed * delta
		var new_pos := position + step
		# 충돌 체크 (parent 가 collision_at(x,y) 노출 시)
		var p := get_parent()
		if p and p.has_method("collision_at"):
			if p.collision_at(int(new_pos.x), int(new_pos.y)) == 0:
				position = new_pos
				moved.emit(position)
		else:
			position = new_pos
			moved.emit(position)
	else:
		motion = MOTION_STAND
	_advance_anim(delta)


## 애니메이션 진행 (4방향 walk/stand cycle). hero + monster 공통.
func _advance_anim(delta: float) -> void:
	_frame_timer += delta
	var frame_dur := 0.15 if motion == MOTION_WALK else 0.5
	if _frame_timer >= frame_dur:
		_frame_timer = 0.0
		var seq: Array = (
			_walk_frames.get(direction, [0]) if motion == MOTION_WALK
			else _stand_frames.get(direction, [0]))
		if seq.is_empty(): return
		var current_pos := seq.find(frame_idx)
		var next_pos := (current_pos + 1) % seq.size() if current_pos >= 0 else 0
		frame_idx = seq[next_pos]
		_apply_frame()


func _apply_frame() -> void:
	if frame_idx in _frame_textures:
		texture = _frame_textures[frame_idx]
	elif _frame_textures.size() > 0:
		# fallback to closest available frame
		var keys = _frame_textures.keys()
		keys.sort()
		texture = _frame_textures[keys[0]]
