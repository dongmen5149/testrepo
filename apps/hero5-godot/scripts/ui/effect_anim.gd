## 이펙트 frame 애니메이션 (스킬 사용 시 적 위에 표시).
##
## sprite frames 디렉토리의 frame_NN_*.png 들을 순차 재생 (~10fps).
## 종료 후 자동 free.
class_name EffectAnim
extends Sprite2D

const DEFAULT_FPS := 10.0


static func spawn_at(parent: Node, pos: Vector2, sprite_dir: String,
		fps: float = DEFAULT_FPS) -> EffectAnim:
	var e = EffectAnim.new()
	e.position = pos
	e.centered = true
	e.z_index = 50
	parent.add_child(e)
	e._play(sprite_dir, fps)
	return e


var _frames: Array = []
var _frame_idx: int = 0
var _timer: float = 0.0
var _frame_dur: float = 0.1


func _play(sprite_dir: String, fps: float) -> void:
	_frame_dur = 1.0 / fps if fps > 0 else 0.1
	var d := DirAccess.open(sprite_dir)
	if d == null:
		queue_free(); return
	d.list_dir_begin()
	var fname := d.get_next()
	var entries: Array = []
	while fname != "":
		if fname.begins_with("frame_") and fname.ends_with(".png"):
			entries.append(fname)
		fname = d.get_next()
	entries.sort()
	for f in entries:
		_frames.append(load(sprite_dir + "/" + f))
	if _frames.is_empty():
		queue_free(); return
	texture = _frames[0]


func _process(delta: float) -> void:
	if _frames.is_empty(): return
	_timer += delta
	if _timer >= _frame_dur:
		_timer = 0.0
		_frame_idx += 1
		if _frame_idx >= _frames.size():
			queue_free()
			return
		texture = _frames[_frame_idx]
