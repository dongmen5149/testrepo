## CHAR/HERO 캐릭터 컨트롤러.
##
## 원본 (libHeroesLore5.so) 의 CHAR 클래스 매핑:
##   this[0x2c] = motion   (우리: var motion: int)
##   this[0x2d] = dir      (우리: var direction: int 0=down,1=left,2=right,3=up — 추정)
##   this[0x2e] = frame    (자동 애니메이션)
##   GetMaxFrame(motion, dir) = SPRITE_DATA 에서 읽음 (우리: 배열 lookup)
##
## 4방향 이동: WASD / 화살표.
## 충돌은 Map.collision_at(x, y) 호출 (구현은 map 측에서 처리).
class_name H5Character
extends Sprite2D

# motion enum (원본 추정값)
const MOTION_WALK := 0
const MOTION_RUN := 1
const MOTION_STAND := 2

# direction enum
const DIR_DOWN := 0
const DIR_LEFT := 1
const DIR_RIGHT := 2
const DIR_UP := 3

@export var move_speed: float = 80.0   # px/s
@export var sprite_dir: String = "res://assets/sprites/img0/000"  # 캐릭터 sprite 디렉토리

var motion: int = MOTION_STAND
var direction: int = DIR_DOWN
var frame_idx: int = 0
var _frame_timer: float = 0.0
var _frame_textures: Dictionary = {}   # frame_idx → Texture (single anim)
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

	# 애니메이션 진행 (4방향 walk-cycle)
	_frame_timer += delta
	var frame_dur := 0.15 if motion == MOTION_WALK else 0.5
	if _frame_timer >= frame_dur:
		_frame_timer = 0.0
		var seq: Array = (
			_walk_frames.get(direction, [0]) if motion == MOTION_WALK
			else _stand_frames.get(direction, [0]))
		if seq.is_empty(): return
		# 다음 시퀀스 인덱스
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
