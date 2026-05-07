## Hero5 자산 로더 (싱글톤).
##
## 원본 VFS 의 자산 이름 (예: "c/sp/img0/000.mgr") 그대로 받아서 res:// 경로로 매핑.
## 임포트 파이프라인이 미리 변환한 PNG/JSON/OGG 를 로드한다.

extends Node

const ASSET_ROOT := "res://assets/"

## VFS 경로 → 변환 후 res:// 경로 매핑.
##   c/sp/img0/000.mgr  → assets/sprites/img0/000/  (디렉토리, frame_NN_*.png 들)
##   c/sp/pal/123.pal   → assets/palettes/123.json
##   c/map/face_07.gbm  → assets/gbm/map/face_07.png
##   c/snd/bgm_03.ogg   → assets/sounds/bgm_03.ogg
##   c/csv/menu_text.dat→ assets/text/menu_text.json
func vfs_to_res(vfs_name: String) -> String:
	# strip leading "c/"
	var rel := vfs_name
	if rel.begins_with("c/"):
		rel = rel.substr(2)
	# heuristic by prefix
	if rel.begins_with("sp/img"):
		# sprite dir — caller picks specific frame PNG
		return ASSET_ROOT + "sprites/" + rel.replace(".mgr", "")
	if rel.begins_with("sp/cif/"):
		return ASSET_ROOT + "sprites/cif/" + rel.get_file().replace(".cif", "")
	if rel.begins_with("sp/ext/"):
		return ASSET_ROOT + "sprites/ext/" + rel.get_file().replace(".ext", "")
	if rel.begins_with("sp/pal/"):
		return ASSET_ROOT + "palettes/" + rel.get_file().replace(".pal", ".json")
	if rel.begins_with("map/"):
		return ASSET_ROOT + "gbm/map/" + rel.get_file().replace(".gbm", ".png").replace(".pal", ".json")
	if rel.begins_with("snd/"):
		# remap ext to .ogg (game references .mmf alongside; we prefer .ogg)
		var fname = rel.get_file()
		var stem = fname.split(".")[0]
		return ASSET_ROOT + "sounds/" + stem + ".ogg"
	if rel.begins_with("font/"):
		return ASSET_ROOT + "fonts/" + rel.get_file()
	if rel.begins_with("csv/") or rel.begins_with("csv2/"):
		return ASSET_ROOT + "text/" + rel.get_file().replace(".dat", ".json")
	if rel.begins_with("ep/"):
		# scene scripts
		return ASSET_ROOT + "scenes/" + rel.replace(".scn", ".json")
	if rel.begins_with("img/"):
		return ASSET_ROOT + "ui/" + rel.get_file().replace(".mgr", "")
	# fallback
	return ASSET_ROOT + rel


## 텍스트 코퍼스 로드 (한글 대사).
func load_text(vfs_name: String) -> Dictionary:
	var path := vfs_to_res(vfs_name)
	if not FileAccess.file_exists(path):
		push_warning("text not found: %s -> %s" % [vfs_name, path])
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	return data if data is Dictionary else {}


## 스프라이트 이미지 (특정 프레임) 로드.
func load_sprite_frame(vfs_name: String, frame_idx: int) -> Texture2D:
	var dir := vfs_to_res(vfs_name)  # path without ext
	# frame files are named like frame_00_WxH_palN.png (variable suffix)
	var d := DirAccess.open(dir)
	if d == null:
		push_warning("sprite dir not found: %s" % dir)
		return null
	d.list_dir_begin()
	var prefix := "frame_%02d_" % frame_idx
	var fname := d.get_next()
	while fname != "":
		if fname.begins_with(prefix) and fname.ends_with(".png"):
			return load(dir + "/" + fname)
		fname = d.get_next()
	return null


## 팔레트 로드 (RGB565 LE pair → Color array).
func load_palette(vfs_name: String) -> PackedColorArray:
	var path := vfs_to_res(vfs_name)
	if not FileAccess.file_exists(path):
		return PackedColorArray()
	var f := FileAccess.open(path, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if not data is Array:
		return PackedColorArray()
	var arr: PackedColorArray = []
	for c in data:
		# JSON: each entry [r, g, b, a] (0-255)
		arr.append(Color(c[0]/255.0, c[1]/255.0, c[2]/255.0, c[3]/255.0))
	return arr
