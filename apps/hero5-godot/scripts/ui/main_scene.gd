## 첫 부트 검증 씬.
## - title 스프라이트 표시
## - asset_loader 로 한글 텍스트 로드 → Label 에 표시
## - 좌/우 화살표로 다른 face_NN 이미지 토글
extends Node2D

@onready var sprite: Sprite2D = $Sprite
@onready var label: Label = $UI/Label
@onready var info: Label = $UI/InfoLabel

var face_idx: int = 0
const MAX_FACE := 30

func _ready() -> void:
	_load_face(face_idx)
	_load_some_text()
	info.text = "← / → : face 변경  |  자산 임포트 검증 씬"

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_right"):
		face_idx = (face_idx + 1) % MAX_FACE
		_load_face(face_idx)
	elif event.is_action_pressed("ui_left"):
		face_idx = (face_idx - 1 + MAX_FACE) % MAX_FACE
		_load_face(face_idx)

func _load_face(idx: int) -> void:
	var path := "res://assets/gbm/map/face_%02d.png" % idx
	if FileAccess.file_exists(path):
		sprite.texture = load(path)
		label.text = "face_%02d.gbm  (idx=%d)" % [idx, idx]
	else:
		# fallback to face_00 if missing
		var alt := "res://assets/gbm/map/face_%02d.png" % 0
		if FileAccess.file_exists(alt):
			sprite.texture = load(alt)
		label.text = "(missing) face_%02d" % idx

func _load_some_text() -> void:
	# 한글 코퍼스 검증
	var path := "res://assets/text/_corpus.txt"
	if FileAccess.file_exists(path):
		var f := FileAccess.open(path, FileAccess.READ)
		var lines := f.get_as_text().split("\n")
		# 그냥 첫 5줄
		var preview := ""
		var n = 0
		for line in lines:
			var s = line.strip_edges()
			if s.length() > 3:
				preview += s + "\n"
				n += 1
				if n >= 5: break
		info.text += "\n\n[corpus preview]\n" + preview
