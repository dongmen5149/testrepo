## 단축키 도움말 — 모든 키 매핑 한 화면 표시.
class_name HelpPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var content: RichTextLabel = $BG/Content
@onready var close_btn: Button = $BG/CloseButton


const HELP_TEXT := """[b]이동 / 환경[/b]
  WASD / 방향키 — 이동 (자동 인카운터)
  M — 다음 mapID 토글
  N — 다음 scene 전환
  C — collision 디버그 토글
  V — tile attribute 디버그
  P — NPC 마커 스폰

[b]상호작용[/b]
  E — 가장 가까운 NPC 와 대화
  T — dialog 테스트
  S — 상점
  Q — 퀘스트 패널
  I / ESC — 상태창

[b]전투[/b]
  B — 즉시 전투 (테스트)
  버튼: 공격 / 스킬(이름) / 방어 / 도망 (% 표시)

[b]세이브[/b]
  1-8 — 슬롯 N 저장
  Shift+1-8 — 슬롯 N 로드
  F5 / F9 — slot 0 빠른 저장/로드
  자동 저장: 60초마다 slot 7

[b]설정[/b]
  X — Settings (BGM/SFX/FPS/전체화면)
  H — 이 도움말

[b]Title 화면[/b]
  새 게임 → 클래스 선택 → 시작
  Continue → slot 0 자동 로드
  슬롯 우클릭 / Shift+클릭 → 삭제
"""


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)
	content.bbcode_enabled = true
	content.text = HELP_TEXT


func toggle() -> void:
	visible = not visible
