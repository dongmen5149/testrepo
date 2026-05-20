## 단축키 도움말 — 모든 키 매핑 한 화면 표시.
class_name HelpPanel
extends CanvasLayer

@onready var bg: ColorRect = $BG
@onready var content: RichTextLabel = $BG/Content
@onready var close_btn: Button = $BG/CloseButton


## Round 94: R82-R93 의 키 추가 + 정정 사항 반영.
##  - F6 (SaveListPanel R92) 신규
##  - F10 (Quit to Title R82) 신규
##  - "Title Continue" 항목 = SaveListPanel 위임 (R93 — 인라인 slot UI 폐지)
##  - 기존 누락 키 보강: G (monster spawn), SPACE (attack), R/K/O/J/L/, (R52-58 패널)
##
## Round 107: R105/R106 의 placeholder UX 동작을 사용자에게 노출.
##  - `}#NN<unit>|` 가 garbage 시 label 노출 (R109 form: `?(공격)%` — 단위 분리)
##  - PLACEHOLDER_LABELS 7 entry (#04/#05/#06/#07/#08/#09/#12) 의미 설명
##
## Round 109: PLACEHOLDER_LABELS 에서 unit 분리 — desc 본문의 `%`/`초` 와 중복
## 노출 차단. #12 의 primary_u16 매핑 제거 (폭발 #12 가 damage% 로 잘못
## 노출되던 케이스 fix). 미해결 시 raw 본문 unit 만 유지.
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
  S — 상점 / Q — 퀘스트 / I·ESC — 상태창
  R — 강화 / K — 합성 / O — Orb 소켓
  J — 대장간 / L — 스킬북 / , — 미션

[b]전투[/b]
  B — 즉시 전투 (테스트)
  SPACE — 인접 monster 공격
  G — 주변에 random monster 스폰 (AI 테스트)
  버튼: 공격 / 스킬(이름) / 방어 / 도망 (% 표시)

[b]세이브[/b]
  1-8 — 슬롯 N 저장
  Shift+1-8 — 슬롯 N 로드
  F5 / F9 — slot 0 빠른 저장/로드
  F6 — Save 목록 패널 (8 슬롯 + AUTO 메타 + Load/Save/Delete)
  자동 저장: 60초마다 slot 7

[b]설정 / Scene[/b]
  X — Settings (BGM/SFX/FPS/전체화면)
  H — 이 도움말
  F8 — 음소거 토글 (mute on/off, ConfigFile 영속)
  F10 — 타이틀로 (확인 popup)

[b]Title 화면[/b]
  새 게임 → 클래스 선택 → 시작
  Continue → Save 목록 패널에서 슬롯 선택
  목록에서 Delete 버튼으로 슬롯 삭제

[b]스킬 설명 placeholder[/b]
  `#NN` 자리 의미 (R108/R109: Formula::calc + 스킬 필드 우선, 미해결 시 `?`):
    #04 → 효과   #05 → 공격   #06 → 마법   #07 → MP
    #08 → 지속   #09 → 쿨    #10 → 값    #11 → 강화
    #12 → 수치   #13 → 양
  정령 스킬은 primary_u16 등 파일 필드로 일부 수치 표시 (예: 암흑탄 400%).
  값 >500 또는 미해결 → `[?(공격)%]` 형식 (R109: label 과 unit 분리).
  미매핑 NN 은 `?`. R111: `{관련특성|` 섹션 → `▸ 관련 특성:` + 스킬 링크 불릿.
"""


func _ready() -> void:
	visible = false
	close_btn.pressed.connect(func(): visible = false)
	content.bbcode_enabled = true
	content.text = HELP_TEXT


func toggle() -> void:
	visible = not visible
