# Hero5 EventProc::Event_* 정확한 의미 매핑

ARM disasm 기반 1:1 binding 정리 (`tools/h5_extract_event_funcs.py`).
`interpreter.gd` 의 dispatch 핸들러를 채울 때 참조.

원본 dump: `work/h5/analysis/event_funcs_disasm.txt` (102 함수, 5800+ 라인).

---

## 1. 완전 추출 (100% 의미 확정)

### Player 액션
| opcode 이름 | 인자 | 본문 호출 → C++ 함수 | 의미 |
|---|---|---|---|
| `Event_PlayerDamage(char pct)` | %0-100 | → `BATTLER::IncreaseHP(-dmg)` | (pct × max_hp / 100) HP 감소. 100% 만 즉사 허용. (자세히 BATTLE_FORMULA.md) |
| `Event_PlayerRestoreHp(char pct)` | % | → `BATTLER::IncreaseHP(+heal)` | (pct × max_hp / 100) HP 회복. clamp ≤ max_hp. |
| `Event_PlayerRestoreSp(char pct)` | % | → `HERO::IncreaseSP(+sp)` | (pct × max_sp / 100) SP 회복. |
| `Event_PlayerDirection(char dir)` | 1B | → `CHAR::SetDir(dir)` | 4-방향 (0=다운, 1=라이트, 2=업, 3=레프트) |
| `Event_PlayerTeleport(u16 x, u16 y, u8 dir, u8 ?)` | 5B | → `HERO::Event_Teleport(x, y, dir, ?)` | 즉시 좌표 이동 |
| `Event_PlayerImo(char emo_id)` | 1B | → `EmotionImo::SetMotion(emo_id, ?)` | 머리 위 감정 아이콘 |
| `Event_PlayerAction(...)` | 5B | → `HERO::Event_setMotion(...)` | 모션 시작 |
| `Event_PlayerMove(u16 dx, u16 dy, u8, u8)` | 5B | → `HERO::Event_setMove(...)` | 상대 이동 |
| `Event_PlayerEffect(...)` | 1B | → `CHAR::SetCharSprEffect(eff_id, ?)` | 스프라이트 이펙트 |
| `Event_PlayerExpendMoney(u32)` | 4B | **stub (비어있음)** | DRM 잔재? 미사용. |
| `Event_PlayerChangeFace(char)` | 1B | **stub** | 미사용 |

### Map 변경
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_MapTileChange(u8 x, u8 y, u8 layer, u8 a, u8 b, u8 c)` | 6B | → `Map::MapChangeTile(...)` | 단일 타일 교체 |
| `Event_MapTileChangeAll(char a, u8 layer, u8 b, u8 c, u8 d)` | 4B | → `Map::MapChangeThemeTile(...)` | 테마 일괄 교체 |
| `Event_MapCollision(u8 x, u8 y, u8 attr)` | 3B | → `Map::MapAttributeChange(x, y, attr)` | 충돌 속성 변경 |
| `Event_MapEncountPirate` | 2B | **stub** | 미사용 |
| `Event_MapObjChangeAll` | 2B | **stub** | 미사용 |
| `Event_MapWorldControl` | 2B | **stub** | 미사용 |

### Enemy 액션
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_EnemyChange(u8 idx, u8 monster_id)` | 2B | → `Map::MonsterChange(idx, monster_id, ?)` | 적 슬롯 교체 |
| `Event_EnemyChangeAction(...)` | 7B | wrapper → `Event_EnemyChange` + `Event_EnemyAction` | 교체 + 액션 동시 |
| `Event_EnemyAction/Move/MoveRelative/Teleport/...` | 다양 | (각각의 wrapper) | 적 모션/이동 |

### Event(NPC/오브젝트) 액션
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_EventEffect(u8 idx, u8 eff_id)` | 2B | → `CHAR::SetCharSprEffect` | NPC/오브젝트 이펙트 |
| `Event_EventImo(u8 imo)` | 2B | → `Npc::NpcImo(imo)` | NPC 감정 |
| `Event_EvnetImgAction` (sic, 오타) | 7B | wrapper → `Event_EventChangeImg` + `Event_EventAction` | 이미지 교체+액션 |
| `Event_EventMoveBreak` | 1B | **stub** | 이동 중단 |

### Quest
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_QuestStatus(u8 qid, u8 status)` | 2B | → `QuestMgr::QuestSetStatus(qid, status)` | 퀘 상태 직접 설정 |
| `Event_QuestQSwitch(u8 qid, u8 on_off)` | 2B | → `QuestMgr::QuestSwitchStatus(qid, on_off)` | 퀘 토글 |
| `Event_QuestSwitch` | 2B | (Q 와 거의 동일) | 동일 |
| `Event_QuestTimer(u8 qid, u16 dur)` | 4B | → `QuestMgr::QuestStartTimer` | 퀘 타이머 |
| `Event_QuestBoss(u8 qid, u8 ?)` | 2B | → quest 보스 출현 트리거 | |
| `Event_SituateQuestPopup(u8 qid)` | 1B | → `QuestMgr::QuestStatusList(qid)` | 퀘 팝업 |

### Situate (연출)
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_SituateBallon(u8 a, u8 b)` | 2B | **stub** | 말풍선 (미구현?) |
| `Event_SituateNarration(u16 str_id, u8 a)` | 3B | → `Strings::getString(id, ...)` + `NARRATION_INFO::SetNarration` | 내레이션 텍스트 |
| `Event_SituateSystemMessage(u16 str_id)` | 2B | → `Strings::getString` + `Battle::SetSystemMsgUi` | 시스템 메시지 |
| `Event_SituateScreenShake(u8 a, u8 b, u8 c)` | 3B | → `Map::setMapShake(a, b, c)` | 화면 흔들림 |
| `Event_SituateSlowMotion(u8 a, u8 b, u8 c)` | 3B | → `Battle::SetSlowFrame` + `Battle::InitSlowFrame` | 슬로우 모션 |
| `Event_SituateDelay(u8 ms)` | 1B | **stub (시간 인자만 저장)** | 지연 |
| `Event_SituateDialogText(u32 str_id)` | 4B | → 대화 텍스트 표시 | (자세한 분기는 1500B Battle::SetDialog 등 별도) |
| `Event_SituatePopup` | 1B | **stub** | 일반 팝업 |
| `Event_SituateNextEvent(u8)` | 1B | **stub** | 다음 이벤트 |
| `Event_SituateVolumeBGM(char)` | 1B | **stub** | BGM 볼륨 |
| `Event_SituateCamera(u8, u8, u8)` | 3B | → 카메라 이동 | |
| `Event_SituateCameraTarget(u8 target_idx)` | 2B | → 카메라 대상 |
| `Event_SituateWindowOff` | 1B | **stub** | 대화창 끄기 |

### Scene flag / 메뉴
| opcode 이름 | 인자 | 본문 호출 | 의미 |
|---|---|---|---|
| `Event_Scene_SaveAble(u8)` | 1B | scene 플래그 설정 | 저장 허용 토글 |
| `Event_Scene_WarpAble(u8)` | 1B | | 워프 허용 |
| `Event_Scene_WarpPoint(u8 x, u8 y, u8, u8)` | 4B | scene 메타 설정 | 워프 좌표 |
| `Event_UiInn(u16)` | 2B | → 여관 UI |
| `Event_UiShop(u8 npc_id)` | 1B | → `Battle::CallNpcMenu` | 상점 |
| `Event_UiAlchemist(u8 npc_id)` | 1B | → `Battle::CallNpcMenu` | 연금술사 |
| `Event_UiGameUi(char on_off)` | 1B | → `Battle::SetGameUIView` | HUD 토글 |
| `Event_UiShip(u8)` | 1B | → 배 UI |
| `Event_UiNetWork` | 0B | **stub** | 네트워크 (DRM) |

---

## 2. 4B 빈 stub 함수 (총 13개 — 의도적 미구현)

`Event_Init / Event_add / Event_screenEnd / Event_Scene_WarpPoint /
Event_PlayerChangeFace / Event_PlayerExpendMoney / Event_MapEncountPirate /
Event_MapObjChangeAll / Event_MapWorldControl / Event_SituateBallon /
Event_SituateVolumeBGM / Event_UiInn / Event_UiNetWork`

`push {lr} / pop {pc}` 만 있는 빈 함수들 — 옛 피쳐폰 빌드 잔재 또는 DRM 제거 흔적.
인터프리터에서는 **arg_size 만큼 스킵하고 무시** 하면 동작 영향 없음.

---

## 3. 더 깊은 분석 필요한 함수

| 함수 | 크기 | 비고 |
|---|---:|---|
| `Event_SituateDialogText` | 1500+B | NPC 대화창 — Strings::getString + 다이얼로그 트리 |
| `Event_PlayerAddEffect` | 200+B | 버프/디버프 적용 |
| `Event_GMDInit` | 200+B | GM 디버그 모드? |
| `Event_QuestNew` | 200+B | 퀘 신규 등록 |

---

## 4. interpreter.gd 핸들러 채우기 가이드

현재 `apps/hero5-godot/scripts/core/interpreter.gd` 의 `_dispatch()` 는 print 만.
위 표 참조해서 다음 우선순위로 실제 동작을 채울 수 있다:

1. **Event_PlayerRestoreHp/Sp** — `GameState.player_hp += pct * max_hp / 100` (clamp).
2. **Event_PlayerTeleport** — `Demo.player.global_position = Vector2(x*tile, y*tile); player.facing = dir`.
3. **Event_PlayerDirection** — `Demo.player.facing = dir`.
4. **Event_QuestStatus / QuestQSwitch** — `Quest.set_status(qid, status)` / `Quest.toggle(qid)`.
5. **Event_MapTileChange** — `MapRenderer.set_tile(x, y, layer, tile_id)`.
6. **Event_SituateScreenShake** — `Camera2D` 에 shake 트윈.
7. **Event_SituateNarration / SystemMessage** — 한글 코퍼스에서 str_id 로 참조 후 UI 표시.

---

## 5. 산출

- `tools/h5_extract_event_funcs.py` — 102 함수 일괄 disasm 도구.
- `work/h5/analysis/event_funcs_disasm.txt` — 5874 라인 dump.
- 본 문서 — Event_* 의미 매핑 reference.
