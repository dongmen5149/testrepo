## 게임 전역 상태 (싱글톤).
extends Node

# 현재 맵/시나리오
var current_scene_id: int = 0
var current_episode: int = -1   # -1 = 일반 맵, >=0 = ep_N 시나리오
var current_stage: int = -1

# 플레이어 상태 (.scn 헤더에서 읽어옴)
var player_x: int = 0
var player_y: int = 0
var player_dir: int = 0

# 디버그
var verbose: bool = true
