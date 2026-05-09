# Hero3 Remake — 진행 상황 & 다음 단계

> 이 문서는 다음 작업 세션에서 컨텍스트 유실 없이 이어서 진행할 수 있도록 정리한 핸드오프.
> 자세한 자산 포맷 사양은 [`docs/asset-formats.md`](asset-formats.md) 참조.

## ⚡ 다음 세션 — 여기서부터 시작

**최신 커밋 시점**: 2026-05-10 PM-7 — **2U + 2T + 2V 일괄 + task pointer 클러스터 식별 + system-wide GOT slots 발견**. (1) ⭐⭐ **0xb3084 슬롯 direct write 0건 → GVM firmware 외부 주입 확정**. 0x4ad10-0x4af10 클러스터 (11+ 함수) 가 task pointer wrapper API. `ldr r3, [r3]; ldr r3, [r3]` double indirection 패턴 = task_ptr_ptr → task_struct. (2) ⚠ **FUN_0009b252 type-tag reader 가설 약화** — cmp #0x05 단 3 BL (type-5 dispatch 부재). 가장 무거운 arm 은 cmp #0x06 (23 BLs). (3) ⭐ **system-wide GOT slots 발견**: 0x9c70/0x9c71/0x9c84/0xac78 같은 추가 글로벌 슬롯들 (FUN_000818f0 / default_key_handler 등 다수 함수에서 반복 사용). (4) FUN_00026a80 (8.4KB) / FUN_000818f0 (5.4KB) = **GOT slot 액세스 압도적** (각각 150, 225 GOT slot LDR sites). 신규 도구 2개 (`find_global_slot_writers.py`, `analyze_arm_handlers.py`). 상세는 [ghidra-task-state-2026-05-10.md](ghidra-task-state-2026-05-10.md).

**이전 세션** (2026-05-10 PM-6): context_getter 정체 확정 (단일 GOT 슬롯 getter, 인자 없음) + type-tag reader 자동 검색 + chain dispatcher 검증. 상세는 [ghidra-context-getter-readers-2026-05-10.md](ghidra-context-getter-readers-2026-05-10.md).

### 한 줄 요약 (현재 상태)

영웅서기3는 **1주차 콘텐츠 완성도 높은 플레이 가능 게임** + **§4.4 95% 해독** + **task pointer 클러스터 + system-wide global slots 식별** (2026-05-10 PM-7). 0xb3084 = task_ptr_ptr (GVM 외부 주입). 0x4ad10-0x4af10 클러스터 = task wrapper API. 추가 글로벌 슬롯 4개 (0x9c70/9c71/9c84/ac78) widespread 사용. type-tag reader 가설 부분 약화 — 풀이 미완. 다음 진척은 **(1) FUN_000439a0 / FUN_00047a14 핵심 sub-handler 본문, (2) 추가 GOT slot 의미 파악, (3) task_struct 필드 매핑, (4) SMAF/번역 사용자 블로커**.

### 게임 update flow (2026-05-10 정정)

```
???_indirect_main_loop  (PIC indirect, 추적 한계 — Ghidra Script 필요)
  ├ FUN_0006619c  (paint/tick callback) — 매 프레임 호출
  │  └ FUN_00062d1c (state[0x94] = "현재 페이지 인덱스" 분기)
  │    ├ page 0 → FUN_0005c038 → FUN_0005d214 (jt 0xa9cc4, record 0x3c4×0x3c)
  │    ├ page 1 → FUN_0005e6ac → FUN_0005f948 (jt 0xa9d70, record 0x14)
  │    └ page 2 → FUN_00060ab4 (9KB, page 2 UI + 데이터 테이블)
  ├ FUN_00070f34  (key handler) — 키 입력 시 호출. param_2=0x31('1')/0x33('3') 으로 page--/page++
  ├ FUN_0008b2e8  (sister entry, record 0x3c4)
  │  └ inline @ 0x8c19c → FUN_0008d5e4 (jt 0xabaa8)
  └ FUN_0008dcd8  (main entry, record 0x3c4)
     └ inline @ 0x8eb80 → FUN_0008ff18 (jt 0xabc68)
```

각 dispatcher: **19 entries (opcode 0~0x12) → 7 distinct handlers** (0x00~0x0c 공통 + 0x0d~0x12 각 unique).
NPC slot record: stride `0x3c4`, `+0x3b3` flag, `+0x3b6` opcode short, `+0x3b8` arg short.

> ⚠ **2026-05-10 정정**: 위 page 0/1/2 는 **별도 게임 시스템이 아니라 한 화면 안의 3 탭** (키 1/3 으로 순환). 따라서 page 2 = battle 가설은 기각. 진짜 battle 트리거는 별도 위치.

### 다음 세션 첫 5분 — 무조건 봐야 할 곳

1. **이 섹션 + 위 game update flow (2026-05-10 정정판)** 읽기
2. `git log --oneline -8` — 최신 커밋 확인
3. `git status --short` — 미커밋 잔여 확인
4. **[ghidra-task-state-2026-05-10.md](ghidra-task-state-2026-05-10.md)** ⭐⭐⭐ — **최신 PM-7** (task pointer 클러스터 + system-wide GOT slots + arm handler 매핑)
5. (참고) [ghidra-context-getter-readers-2026-05-10.md](ghidra-context-getter-readers-2026-05-10.md) — PM-6 (context_getter 정정)
6. (참고) [ghidra-queue-protocol-2026-05-10.md](ghidra-queue-protocol-2026-05-10.md) — PM-5 (큐 protocol)
7. (선택) 빌드 검증 — 아래 §"재현 명령"

### 🚀 "이어서 진행" 한 마디로 시작할 때 (자동 진행 권장 흐름)

다음 세션에서 사용자가 "영웅서기3 이어서 진행" 같은 짧은 지시만 줬을 때, 다음 흐름으로 자동 진행:

**1) 컨텍스트 복구** (1분):
- `git log --oneline -8` 로 최근 작업 파악 (Round 17 = `a3e35715` 까지 완료)
- 위 PM-7 핸드오프 문서 + 이 우선순위 표의 ⭐ 항목 확인

**2) 권장 다음 작업 (Round 18 후보, 우선순위 순)**:

| # | 작업 | 명령 | 기대 산출물 |
|---|---|---|---|
| ⭐⭐ 2W | FUN_000439a0 본문 (popular sub-handler, 188B, 37 callers) | `python tools/recon/disasm_subsystem_func.py 0x439a0 0x44280 --label popular_helper_439a0` | `work/h3/popular_helper_439a0_disasm.json` — type-6 처리 핵심 식별 |
| ⭐⭐ 2X | FUN_00047a14 본문 (또 다른 sub-handler) | next entry 확인 후 `disasm_subsystem_func.py 0x47a14 <end>` | `work/h3/sub_handler_47a14_disasm.json` |
| ⭐ 2Y | 추가 GOT slot writer 추적 | `python tools/recon/find_global_slot_writers.py --slot-offset 0x9c70` (그리고 0x9c71, 0x9c84, 0xac78 각각) | 4개 슬롯의 writer 분포 → GVM 외부 주입 vs 게임 내부 셋팅 구분 |
| 2Z | task_struct 필드 매핑 | 0x4ad34 클러스터 함수 본문 일괄 분석 | task_struct (offset → 의미) 매핑 |

**3) Round 18 작업 후 마무리**:
- 분석 결과 → 신규 문서 `docs/h3/ghidra-<주제>-2026-05-XX.md` 작성
- PROGRESS.md 우선순위 표에 ✅ 추가 + 새로운 권장 작업 ⭐ 추가
- 메모리 파일 (`project_hero3_remake.md`) 에 Round 18 항목 추가
- Python 회귀 (`python -m unittest ...` — 위 §재현 명령 참조) 통과 확인 후 커밋

**4) 사용자 블로커 작업이 더 가치 있으면 우선순위 변경**:
- SMAF→OGG 변환 (`tools/converter/convert_h3_smaf.py`) — BGM/SFX 활성, 게임 체감 큼
- 대사 LLM 번역 (`ANTHROPIC_API_KEY` 셋업 후 `translate_dialogues.py` 실행, ~$0.66)

**5) 환경 셋업 (PowerShell, 필요 시만)**:
```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
```
(Python 분석은 JAVA_HOME 불필요. Android 빌드/테스트 시에만.)

### 다음 세션 — 우선순위 (블로커별)

> ⭐ = 권장 다음 작업

**🔴 사용자 입력 블로커 (실질 진척 여기서)**

| 우선 | 작업 | 비고 |
|---|---|---|
| ~~2A~~ | ~~NPC handler 영역 capstone 디스어셈블~~ | ✅ 2026-05-09 PM-3. 21 handler 일괄 디스어셈블 → `work/h3/dispatcher_handlers_summary.json`. **본문 분석 결론**: 모든 handler 의 BL 다수가 `0xa42a0` (= `bx r3`) veneer 로 향함 — register-indirect call. NPC 좌표 offset 자동 식별 실패 (record_offset_hint 들이 GOT-relative global) — 정확한 의미 식별은 결국 사용자 GUI 의 caller-chain 분석 필요 |
| ~~2B~~ | ~~`FUN_00060ab4` (mode 2, 9KB) capstone 디스어셈블~~ | ✅ 2026-05-09 PM-3. 본문 = 1.5KB 코드 + 7KB 임베디드 데이터 (literal 풀). 16 직접 BL (0 veneer) → `0x4ad10`(4) `0x9f624`(3) `0xd53c`(2) `0x9fb78`(2). switch 패턴 **없음** — sequential setup + 내부 graphics 콜. 추정: **scene/render primitive** (렌더 + 데이터 테이블 baked) — battle 분기 가능성. 결과: `work/h3/mode2_disasm.json` |
| ~~2C~~ | ~~진짜 _scn byte stream parser 발견~~ | ⚠ 2026-05-09 PM-3 자동 검색. **strings table @ 0xaac58** 확인 (`/event/e0000_scn`, `/map/map0_mp`, `Event_freeID`, `/map/sprite_0_cif` 등 9개 game asset path 템플릿). PIC GOT-relative load 만 사용 → 직접 xref 0건. movw imm12=0xc58 등의 16-bit offset 형태로 참조 흔적 — Ghidra GUI 의 cross-reference 추적 필요 |
| ~~2D~~ | ~~3 entry indirect caller (main loop) 추적~~ | ⚠ 2026-05-10 사용자 GUI 동행 분석. hex 검색 6건 0건 + Ghidra XREF 0건 + decompiled output grep 0건 → **정적 분석 ceiling 확정**. ROI 낮음 (state[0x94] 재해석으로 main loop 의 가치 감소). 시도 시 Ghidra Script 작성 (BLX register + MOVW/MOVT 패턴) 필요, 1~2시간 + 성공 보장 X |
| ~~2F~~ | ~~mode 2 (`FUN_00060ab4`) 의 7KB literal pool = page 2 UI 데이터 해석~~ | ✅ 2026-05-10 PM-2. **가설 기각** — 9KB 가 100% 코드. 이전 "1.5KB+7KB 데이터" 는 capstone alignment stop 오인. 진짜 정체 = page 2 UI rendering function (drawText 18x + sound 15x + 화면 포인터 29x). 결과: `work/h3/mode2_ui_data.json`, 도구 `parse_mode2_ui_data.py` (walk_with_skip 표준화) |
| ~~2G~~ | ~~진짜 battle 트리거 별도 추적~~ | ✅ 2026-05-10 PM-2. **state[0x460] = menu highlight flag** 확인 (battle 아님). FUN_00064048 분석 → cmp 분포 부재 + ring buffer 직렬화 (FUN_0007e150/0x7e184/0x7e890 = GVM 이벤트 큐 API). state machine 아님. 결과: `work/h3/default_key_handler.json`, 도구 `disasm_default_key_handler.py` |
| ~~2I~~ | ~~402 stub 함수 우선순위 분류 + 분석~~ | ✅ 2026-05-10 PM-3. `tools/recon/rank_pic_stubs.py` + `analyze_top_stubs.py` 로 top 15 카테고리 추정. ⭐ **FUN_00006334** (10KB, MASSIVE state machine) = main loop 후보. **FUN_000818f0** (5.4KB, 287 BLs) = per-entity update loop. **FUN_00026a80** (8.4KB, 51 distinct BL) = subsystem router. **FUN_0003d5d0** (4.3KB, 37 callers, 22 cmp arms) = **sound subsystem dispatcher**. 결과: `work/h3/pic_stubs_ranked.json`, `work/h3/top_stubs_analysis.json` |
| ~~2J~~ | ~~FUN_0007e150 큐 producer/consumer 매핑~~ | ✅ 2026-05-10 PM-3. `tools/recon/find_queue_callers.py` 로 138 BL → 31 caller 매핑. ⭐⭐ **FUN_00057394** (3.5KB) = **큐 lifecycle owner = render command buffer / display list builder** 후보 (graphics_primitive 20x + byte_append 19x + flush 7x). **FUN_00056bf8** = save/load codec 후보. 4 함수가 큐 호출의 70% 차지. 결과: `work/h3/queue_callers.json` |
| ~~2K~~ | ~~FUN_00057394 본문 디스어셈블~~ | ✅ 2026-05-10 PM-4. **typed record writer 확정** — byte_append(0x05) + byte_append(subop) + args + flush_swap 패턴. 7 records emit, 5 distinct subops (0x14/0x3/0x3d/0x3f/0x40). type-5 record stream codec |
| ~~2L~~ | ~~FUN_00006334 본문 디스어셈블~~ | ✅ 2026-05-10 PM-4. 96 cmp arms (15+ distinct nonzero values 1-22), 162 PC-rel LDR (135 GOT slot), interesting BL 0건. main loop 가설 **부분 약화** — event/script interpreter 또는 save record processor 후보 |
| ~~2M~~ | ~~FUN_0003d5d0 dispatcher 22 arm 디코드~~ | ✅ 2026-05-10 PM-4. **22 arms + sound 페어 패턴 확정** (sound_trigger 21x + helper_9fd64 17x = 한 sound 명령 = 두 함수 호출). sound id immediate 모두 indirect (21/21 unknown) — 더 깊은 r0 backtrace 필요 |
| ~~2N~~ | ~~FUN_00056bf8 (queue codec) 본문 분석~~ | ✅ 2026-05-10 PM-5. **codec 확정** — cmp arm 값 = byte_append immediate 값 (0x3d/0x3e/0x1f). 5 records emit (type-0/1×2/4/0x1f). reader (cmp 0x06/0x09/0x07) + writer (byte_append 0x01/0x04 등) 둘 다 |
| ~~2O~~ | ~~FUN_00008aca 본문 분석~~ | ✅ 2026-05-10 PM-5. **별도 함수 아님 — FUN_00006334 의 공유 epilogue gadget** (70x BL = 70 early-exit). 부수 발견: 0x8ac6 BL → FUN_000031dc (chain dispatcher 후보) |
| ~~2P~~ | ~~r0 backtrace 강화 (10+ instr propagation)~~ | ✅ 2026-05-10 PM-5. `track_reg_value` 재귀 register propagation + r0~r3 동시 추적 + prev_instrs 컨텍스트. byte_append immediate 80~90% 식별. sound ID 는 모두 메모리 로드라 추적 한계 |
| ~~2Q~~ | ~~FUN_000031dc 본문 분석~~ | ✅ 2026-05-10 PM-6. 47 arms, 4 distinct type tags, helper 거의 없음 (graphics_primitive 1). FUN_00006334 와 페어 chain dispatcher 검증 |
| ~~2R~~ | ~~FUN_0004ad10 (context_getter) 정체 재분석~~ | ✅ 2026-05-10 PM-6. **단일 GOT 슬롯 getter 확정** (GOT base + 0x444 = 0xB3084). 인자 없음. PM-5 의 "r0 인자" 는 backtrace false signal (consumed before BL). |
| ~~2S~~ | ~~type-5 reader 발견~~ | ✅ 2026-05-10 PM-6. binary 전체 cmp #type_tag 검색 (`find_type_tag_readers.py`). type-5 cmp = 111 sites widespread. **FUN_0009b252** (4KB, 5 distinct nonzero tags) = 가장 강력한 reader 후보 |
| ~~2T~~ | ~~FUN_0009b252 86 arm 별 BL target 매핑~~ | ✅ 2026-05-10 PM-7. cmp #0x06 (23 BLs) + cmp #0x00 (23) + cmp #0x01 (16) 위주. **cmp #0x05 단 3 BL** → type-5 reader 가설 약화. 핵심 sub-handler: **FUN_000439a0** (popular helper, 7x for cmp#6) + **FUN_00047a14** (6x for cmp#6) |
| ~~2U~~ | ~~0xB3084 글로벌 슬롯 의미 추적~~ | ✅ 2026-05-10 PM-7. **direct write 0건 → GVM firmware 외부 주입 확정**. 0x4ad10-0x4af10 클러스터 (11+ 함수) = task pointer wrapper API. `ldr r3, [r3]; ldr r3, [r3]` double indirection (task_ptr_ptr → task_struct). 추가 GOT slots 발견 (0x9c70/9c71/9c84/ac78) |
| ~~2V~~ | ~~FUN_00026a80 / FUN_000818f0 본문~~ | ✅ 2026-05-10 PM-7. FUN_00026a80 (8.4KB): GOT slot LDR 150 사이트 (subsystem router 가설 유지). FUN_000818f0 (5.4KB): GOT slot LDR 225 사이트 + task_ptr_getter 212x — entity update loop 확정 |
| ⭐ **2W** | **FUN_000439a0 (188B, 37 callers) 본문 분석** | 가장 인기 sub-handler. 다양한 dispatcher 의 cmp arm 에서 재사용. type-6 처리 핵심. 자동 가능 |
| ⭐ **2X** | **FUN_00047a14 본문 분석** | 또 다른 핵심 sub-handler. cmp arms 다수에서 등장 (cmp#6 6x, #1 3x, #7 2x). 자동 가능 |
| 2Y | 추가 GOT slots (0x9c70/9c71/9c84/ac78) writer 추적 | `find_global_slot_writers.py --slot-offset 0x9c70` 등으로 검색. GVM 외부 주입 vs 게임 내부 셋팅 구분. 자동 가능 |
| 2Z | task_struct 필드 매핑 | 0x4ad34 클러스터 함수 본문 분석으로 task_struct 의 (offset → 의미) 매핑. 자동 가능 |
| 2H | _mp NPC 좌표 외부 init/spawn 함수 추적 | 2D 의존 (main loop 발견 시 부속). 단독으로는 자동 검출 불가 |
| 2 | SMAF→OGG 변환 (smaf-converter JAR + TiMidity++ + ffmpeg) | §4.5 — BGM/SFX 활성. 게임 체감 큼. **2026-05-10 도구 갱신**: `tools/converter/convert_h3_smaf.py` 실행으로 헤더 분석 + 변환 가이드 생성. JAR 다운받아 `bgm0_mf` 시범 변환 권장 |
| 3 | 대사 LLM 번역 실행 (~$0.66) | §4.6 — "마지막에" 결정. _scn entries 추출 완료, 호출만 남음 |
| 4 | 추가 게임 콘텐츠 (보스/맵/퀘스트) 디자인 결정 | 1주차 콘텐츠는 완성. 확장 여부 미정 |

**🟡 자동 진행 가능 (가치 낮음, 채울 거리)**

| # | 작업 | 예상 | 비고 |
|---|---|---|---|
| 5 | 일본어 부분 i18n (UI 핵심 50~100 string) | 2시간 | 자동 영문 추가 가능, 일본어/한국어 매핑은 사용자 검수 전제 |
| 6 | h4-h11 walk-cycle 인코딩 추가 분석 | 4시간+ | cif 헤더 / 외부 인덱스 필요. Ghidra 진척 의존. 게임 영향 없음 (h0 만 wire) |
| ~~7~~ | ~~enemy/boss cif 디코더 (`FUN_00098ef8` 알고리즘 적용)~~ | ✅ 2026-05-09 | `tools/recon/analyze_cif.py` 에 `decode_cell_byte / parse_boss_header / parse_boss_cells / split_frames_by_sentinel / boss_cif_summary` 추가. 39 cif 일괄 통계 (`tools/recon/dump_boss_cif.py`). 단위 테스트 13건. **다음 단계 (cell ref → BM 매핑)** 는 §4.3 후속 작업 — 전투 베이킹 진입 시 |

### 핵심 진입 문서

- [ghidra-task-state-2026-05-10.md](ghidra-task-state-2026-05-10.md) — **⭐⭐⭐ 최신 PM-7** (task pointer 클러스터 + system-wide GOT slots + arm handler 매핑)
- [ghidra-context-getter-readers-2026-05-10.md](ghidra-context-getter-readers-2026-05-10.md) — PM-6 (context_getter 정정 + FUN_0009b252 reader 후보 + chain dispatcher)
- [ghidra-queue-protocol-2026-05-10.md](ghidra-queue-protocol-2026-05-10.md) — PM-5 (큐 protocol 11 type tags + epilogue gadget 발견 + FUN_00056bf8 codec)
- [ghidra-pic-stubs-2026-05-10.md](ghidra-pic-stubs-2026-05-10.md) — PM-3 (402 stub ranking + 큐 caller 매핑 + top 15 카테고리)
- [ghidra-mode2-default-handler-2026-05-10.md](ghidra-mode2-default-handler-2026-05-10.md) — PM-2 (mode 2 정정 + default key handler + 402 stub 패턴 첫 발견)
- [ghidra-scn-dispatcher-2026-05-10.md](ghidra-scn-dispatcher-2026-05-10.md) — AM 차례 (state[0x94] 재해석 + 3 entry caller 한계 확정)
- [ghidra-scn-dispatcher-2026-05-09c.md](ghidra-scn-dispatcher-2026-05-09c.md) — 자동 분석 2A/2B/2C 종합
- [ghidra-scn-dispatcher-2026-05-09b.md](ghidra-scn-dispatcher-2026-05-09b.md) — 95% 해독 도달 (caller chain + mode selector). superseded
- [ghidra-scn-dispatcher-2026-05-09.md](ghidra-scn-dispatcher-2026-05-09.md) — §4.4 초기 부분 해독 (참고용)
- [ghidra-findings-2026-05-08.md](ghidra-findings-2026-05-08.md) — 2026-05-08 세션 (참고용)
- [ghidra-scn-opcode-walkthrough.md](ghidra-scn-opcode-walkthrough.md) — §4.4 초기 walkthrough (참고용)
- [ghidra-gui-guide.md](ghidra-gui-guide.md) — Ghidra 일반 가이드
- [asset-formats.md](asset-formats.md) — 자산 포맷 사양

### 빌드/테스트 — 재현 명령

```powershell
# 환경 (PC별 JDK 경로 다름)
# 현재 PC (집): Eclipse Adoptium
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot'
# 다른 PC: Microsoft (옛 작업 환경)
# $env:JAVA_HOME = 'C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Android 빌드 + 테스트 (32/32 Kotlin 테스트)
& "C:\gameRemake\testrepo\android\gradlew.bat" -p "C:\gameRemake\testrepo\android" :app:assembleDebug :app:testDebugUnitTest

# Python 회귀 테스트 (120 test: cif 22 + cif-conv 5 + mp 18 + scn 17 + text 5 + palette 6 + dat 8 + bm_v2 9 + extract_strings 22 + translation_dict 9 + walk-cycle 3 PIL-skip)
python -m unittest tools.recon.test_analyze_cif tools.recon.test_extract_strings tools.converter.test_convert_mp tools.converter.test_convert_scn tools.converter.test_convert_cif tools.converter.test_convert_text tools.converter.test_convert_palette tools.converter.test_convert_dat tools.converter.test_convert_bm_v2 tools.i18n.test_translation_dict

# Boss/enemy cif 일괄 통계 (39 파일 → work/h3/boss_cif_summary.json)
python tools/recon/dump_boss_cif.py

# §4.4 dispatcher 자동 분석 도구 (2026-05-09 PM 추가)
python tools/recon/find_dispatcher_v3.py            # dispatcher 후보 통계 (UNRECOVERED_JUMPTABLE / chain compare)
python tools/recon/find_all_19op_dispatchers.py     # 4 dispatcher 자동 발견 + jump table 디코드
python tools/recon/decode_scn_jumptable.py          # 단일 jump table 19 entries 디코드
python tools/recon/find_bl_callers.py               # ARM Thumb-2 BL 디코드해서 caller 검색 (TARGETS 수정 후 사용)
python tools/recon/disasm_dispatcher2_handlers.py   # capstone 으로 dispatcher 2 handler 디스어셈블
python tools/recon/disasm_all_dispatcher_handlers.py # dispatcher 1/3/4 의 21 handler 일괄 디스어셈블 (PM-3)
python tools/recon/disasm_helper_funcs.py            # top BL target prologue 분석 (veneer vs real, PM-3)
python tools/recon/disasm_mode2_fn.py                # mode 2 FUN_00060ab4 (9KB) 본문 분석 (PM-3) — 768 instr 에서 stop (구버전)
python tools/recon/parse_mode2_ui_data.py            # ⭐ mode 2 walk_with_skip 분석 (2026-05-10 PM-2) — 100% 코드 확정
python tools/recon/disasm_default_key_handler.py     # ⭐ FUN_00064048 default key handler 분석 (2026-05-10 PM-2)
python tools/recon/rank_pic_stubs.py                 # ⭐ 402 PIC stub 우선순위 ranking (2026-05-10 PM-3)
python tools/recon/find_queue_callers.py             # ⭐ GVM 큐 API caller 매핑 (2026-05-10 PM-3)
python tools/recon/analyze_top_stubs.py              # ⭐ top 15 stub 일괄 분석 + 카테고리 추정 (2026-05-10 PM-3)
python tools/recon/disasm_subsystem_func.py 0x57394 0x58172 --label render_buffer       # ⭐ 2K (PM-4)
python tools/recon/disasm_subsystem_func.py 0x6334 0x8aca --label main_dispatcher       # ⭐ 2L (PM-4)
python tools/recon/disasm_subsystem_func.py 0x3d5d0 0x3e690 --label sound_dispatcher    # ⭐ 2M (PM-4)
python tools/recon/disasm_subsystem_func.py 0x56bf8 0x56f3c --label queue_codec         # ⭐ 2N (PM-5)
python tools/recon/disasm_subsystem_func.py 0x64048 0x64852 --label default_key_v2      # 2P 검증 (PM-5)
python tools/recon/disasm_subsystem_func.py 0x630e8 0x64018 --label cmd_processor       # 2P 검증 (PM-5)
python tools/recon/find_type_tag_readers.py                                              # ⭐ 2S binary 전체 cmp #type_tag 검색 (PM-6)
python tools/recon/disasm_subsystem_func.py 0x31dc 0x4c22 --label chain_dispatcher       # 2Q (PM-6)
python tools/recon/disasm_subsystem_func.py 0x9b252 0x9c280 --label type_tag_reader      # 2S top reader 후보 (PM-6)
python tools/recon/find_global_slot_writers.py                                           # ⭐ 2U 0x444 슬롯 writer 추적 (PM-7)
python tools/recon/analyze_arm_handlers.py 0x9b252 0x9c280 --label type_tag_reader       # ⭐ 2T arm-by-arm BL 매핑 (PM-7)
python tools/recon/disasm_subsystem_func.py 0x26a80 0x294a2 --label subsystem_router     # 2V (PM-7)
python tools/recon/disasm_subsystem_func.py 0x818f0 0x82df4 --label entity_update_loop   # 2V (PM-7)
python tools/recon/find_real_func_start.py          # 영역 내 push prologue 위치 → 함수 boundary
python tools/recon/find_npc_record_offsets.py       # NPC slot record (0x3c4) offset access 추출
python tools/recon/cluster_dispatcher_callers.py    # caller 들을 포함 함수 단위로 클러스터링
python tools/recon/extract_candidate_funcs.py 0xADDR1 0xADDR2  # all_decompiled.c 에서 함수 본문 추출
```

### 환경

- JDK 21 (Eclipse Adoptium 21.0.11) / Ghidra 12.0.4 / Gradle 8.9 / AGP 8.7.2 / Kotlin 2.0.20 / compileSdk 35
- 테스트 PC = `C:\gameRemake\testrepo` / Ghidra = `C:\Users\viewe\Downloads\ghidra_12.0.4_PUBLIC_20260303\ghidra_12.0.4_PUBLIC\`

---

## 📜 2026-05-10 PM-7 세션 작업 압축 (2U + 2T + 2V + task pointer 클러스터)

**테마**: PM-6 의 context_getter 정체 확정 후속. writer 추적 + arm 별 BL 매핑 + top stub 미분석 항목 본문 일괄.

**A. 2U — 0xb3084 슬롯 writer 추적** ([find_global_slot_writers.py](../../tools/recon/find_global_slot_writers.py))
- binary 전체 350K instr 검색 → **direct write 0건**, direct read 0건
- 7 PC-rel LDR 사이트 (literal 0x444) — 모두 0x4ad10-0x4ae10 클러스터 (단일 영역)
- → ⭐⭐ **GVM firmware 가 외부에서 슬롯을 셋팅** 확정. 게임 binary 는 read-only.
- 0x4ad10-0x4af10 클러스터 (11+ 함수) = **task pointer wrapper API**:
  - FUN_0004ad10 = task_ptr getter
  - FUN_0004ad34 = task setup (`ldr r3, [r3]; ldr r3, [r3]` double indirect = task_ptr_ptr → task_struct)
  - FUN_0004ae10 = parameterized task action (case 2/3)
  - FUN_0004ae7c = task_struct field setter (offsets 8, 0x18)

**B. 2T — FUN_0009b252 arm-by-arm BL 매핑** ([analyze_arm_handlers.py](../../tools/recon/analyze_arm_handlers.py))
- 86+ cmp arms 의 분기 블록 별 BL targets 추출
- ⚠ **type-5 reader 가설 약화**: cmp #0x05 단 3 BL (type-5 처리 거의 없음)
- 가장 무거운 arm: cmp #0x06 (23 BLs), cmp #0x00 (23, null check), cmp #0x01 (16)
- 핵심 sub-handlers 발견: ⭐ **FUN_000439a0** (cmp#6 7x, cmp#1 4x) + **FUN_00047a14** (cmp#6 6x, cmp#1 3x) — 다양한 arm 에서 재사용

**C. 2V — top stub 미분석 본문**
- **FUN_00026a80** (8.4KB subsystem router): GOT slot LDR 150 사이트 (177 중 85%) — 매우 다양한 글로벌 액세스. 51 distinct BL targets.
- **FUN_000818f0** (5.4KB entity update loop): GOT slot LDR 225 사이트 (244 중 92%) + task_ptr_getter 212x. 좁은 BL diversity (17) + 높은 호출량.

**D. ⭐ system-wide GOT slots 발견**
FUN_000818f0 의 r0 backtrace (false signal 가능성 있지만 일관된 패턴):
- 0x9c70, 0x9c71 (인접 1 byte) — default_key_handler 와 공유
- 0x9c84 — default_key_handler
- 0xac78 — 새로 발견

→ GOT base + 0x9c70/0x9c71/0x9c84/0xac78 = system-wide global state slots. 게임의 핵심 글로벌 다수 위치.

**E. 핵심 교훈**
1. **direct write 0건 = 외부 주입 신호**. PIC 환경의 표준 패턴.
2. **wrapper API cluster 식별의 가치**: 11+ 함수 클러스터가 한 슬롯 wrapping = task struct 의 다양한 필드 액세스 패턴.
3. **arm-by-arm BL 매핑 = dispatcher 정체 식별의 결정적 도구**: 단순 arm 카운트보다 BL distribution 이 정확한 지표.
4. **handler reuse 패턴**: small popular helper (FUN_000439a0) 가 다양한 dispatcher arm 에서 재사용 = 공통 sub-handler. 본문 분석으로 multiple sub-system 풀이 한 번에 진척.

**F. 다음 세션 권장**
- ⭐ **2W**: FUN_000439a0 본문 분석 (가장 인기 sub-handler)
- ⭐ **2X**: FUN_00047a14 본문 분석 (또 다른 핵심 sub-handler)
- 2Y: 추가 GOT slots writer 추적 (`--slot-offset 0x9c70` 등)
- 2Z: task_struct 필드 매핑 (0x4ad34 클러스터 본문)

---

## 📜 2026-05-10 PM-6 세션 작업 압축 (2R + 2S + 2Q + context_getter 정정)

**테마**: PM-5 의 큐 protocol 매핑 후속. context_getter 의 인자 가설 검증 + type-tag reader 자동 검색 + chain dispatcher 본문.

**A. 2R — `FUN_0004ad10` 정체 확정** ⭐⭐
- raw 디스어셈블 결과: `mov sl, pcrel + add r3, sl + ldr r0, [r3] + bx lr` 패턴
- **GOT base + 0x444 (= 0xB3084) 의 단일 슬롯 getter** — 인자 없음
- PM-5 의 "r0 인자" 가설은 **backtrace false signal**: r0 가 BL 직전에 다른 instruction (`adds r3, r3, r0`) 에서 이미 consumed 되고, BL 의 인자가 아니었음
- 의미: 이 슬롯은 **모든 함수가 공유하는 single global state pointer** (current task / current scene 류). 매우 빈번 호출.

**B. 2S — type-tag reader 자동 검색** ([find_type_tag_readers.py](../../tools/recon/find_type_tag_readers.py))
- binary 전체 350K instructions 디스어셈블 → 4575 cmp #type_tag arms 분포
- type-5 prevalence: **111 cmp 사이트** (PM-5 dominant 와 일관)
- ⭐ **FUN_0009b252** (rank #1, 4KB) = **5 distinct nonzero type tags + 86 cmp arms + 53 context_getter calls** — 가장 강력한 reader 후보
- queue reader → cmp #type 직접 패턴은 단 2건 (대부분 더 복잡한 dataflow → 자동 식별 한계)
- 부수: FUN_00006334 (#5), FUN_000031dc (#30) 도 5/4 distinct type tags 사용

**C. 2Q — `FUN_000031dc` (chain dispatcher) 본문**
- 6.7KB, 47 cmp arms (다양한 imm: 0x32='2', 0x46='F' 등)
- interesting BL 단 3 (graphics_primitive 1, context_getter 2)
- → main_dispatcher (FUN_00006334) 와 같은 카테고리 — chain dispatcher 가설 검증

**D. 큐 protocol 풀이 진척**
| 측면 | 상태 |
|---|---|
| writer (4 함수) type tag emit | ✅ 매핑 완료 (PM-5) |
| reader (다수 함수) type tag 사용 분포 | ✅ binary 전체 검색 완료 (PM-6) |
| 큐 reader → cmp #type 직접 패턴 | ❌ 거의 없음 (자동 식별 한계) |
| FUN_0009b252 정밀 본문 분석 | 미진행 (다음 세션 권장) |

**E. 핵심 교훈**
1. **raw bytes 검증의 가치**: PM-5 "r0 인자" 가설을 한 capstone 호출로 즉시 정정. Ghidra 디컴파일 의심 시 raw 가 결정적.
2. **backtrace false signal 패턴**: `ldr r0, [pc, #X]; ... use r0 ...; bl <foo>` — r0 는 BL 직전 consumed 됐을 수 있음. 도구 결과는 검증 필요.
3. **binary 전체 wide-scan 의 효율**: 350K instructions → 838 함수 type tag 매핑 즉시. specific 분석보다 ROI 높을 때 있음.
4. **single-slot global pointer** (FUN_0004ad10) = 게임의 핵심 state. 슬롯 0xB3084 의 의미 파악이 다음 큰 진척 후보.

**F. 다음 세션 권장**
- ⭐ **2T**: FUN_0009b252 86 arm 별 BL target 추출 → type-5 sub-op → handler 매핑
- ⭐ **2U**: 0xB3084 글로벌 슬롯 의미 추적 (write 측 식별)
- 2V: FUN_00026a80 / FUN_000818f0 본문 (top stub 미분석)

---

## 📜 2026-05-10 PM-5 세션 작업 압축 (2P + 2N + 2O + 큐 protocol 종합)

**테마**: PM-4 의 큐 record 포맷 가설 후속. 도구 강화 + 추가 함수 분석으로 큐 protocol 의 type tag 매트릭스 종합.

**A. 2P — `disasm_subsystem_func.py` backtrace 강화**
- `track_reg_value(instrs, idx, target_reg, depth=15)` 재귀 register propagation
- 지원: mov #imm / mov reg / ldr [pc] / adds reg+imm / adds self / lsls/asrs/lsrs / movw imm
- `backtrace_args(instrs, idx)` — r0~r3 동시 추적 + prev_instrs 컨텍스트
- 효과: byte_append immediate 80~90% 식별. PIC `ldr r0, [pc, #imm]` 패턴으로 GOT slot offset 추출 가능. sound ID 는 메모리 로드라 추적 한계.

**B. 2N — FUN_00056bf8 = 큐 codec 확정** ⭐
- 836B, 10 cmp arms (0x3d, 0x3e, 0x1f, 0x06, 0x09, 0x07, 0x01, 0x00, 0x06, 0x09)
- byte_append immediate: 0x01×2, 0x00×2, 0x3e×2, 0x3d, 0x04, 0x1f
- **cmp arm 값 = byte_append immediate 값** (0x3d, 0x3e, 0x1f) → 같은 type tag 시스템 reader/writer 둘 다
- 5 records emit: (1, 0x3d), (0), (4, 0x3e), (0x1f, 0), (1, 0x3e)

**C. 2O — FUN_00008aca 정체 정정** ⭐⭐
- Ghidra: `void FUN_00008aca(void) { return; }` (빈 함수)
- 실제 capstone: `mov sp, r7; pop {r3}; mov sl, r3; pop {r4-r7, pc}` = epilogue gadget
- → **FUN_00008aca 는 별도 함수 아님 = FUN_00006334 의 공유 epilogue gadget**
- "70x BL to 0x8aca" = 70 early-exit branches (shared epilogue gadget 패턴)
- 부수 발견: 0x8ac6 의 `bl 0x31dc` = FUN_000031dc (또 다른 6.7KB MASSIVE) → chain dispatcher 가능성

**D. 큐 protocol 종합 매핑** (4 writer 분석)

| record type | FUN_00057394 | FUN_00056bf8 | FUN_00064048 | FUN_000630e8 | 합계 |
|---|---|---|---|---|---|
| type-5 ⭐ (`0x05`) | 7 | — | 4 | 5 | **16** |
| type-0/1/4/0x1f | — | 5 | — | 2 (type-4) | 7 |
| sub-op 0x3d~0x41 | 다수 | 0x3d, 0x3e | 0x3d, 0x3f | 0x41 | — |

→ **type-5 가 가장 흔한 record** (3 writer, 16 emits). sub-op 가 ASCII '=','?','@','A' 부근.
→ **journal/event log/save serialization** 가설.

**E. 부수 발견 — `FUN_0004ad10` 의 인자 사용 가능성**
- 강화된 backtrace 로 default_key_handler 의 BL context_getter 호출 시 r0 가 다른 GOT slot offsets (0x9c70, 0x9c71, 0x9c84) 으로 셋되는 패턴 발견
- Ghidra 디컴파일은 `void → undefined4` (인자 없음) 으로 표시했으나 실제는 r0 인자를 받을 가능성
- 이전 분석 "context_getter" 가 모두 같은 값 반환한다는 가정 정정 필요

**F. 핵심 교훈**
1. **Ghidra 의 또 다른 misleading 패턴**: 빈 함수 (`return;`) 도 분석 실패 신호일 수 있음. raw bytes 가 epilogue gadget 인 경우 다수.
2. **shared epilogue gadget** = ARM Thumb 컴파일러 최적화 패턴. 큰 함수의 다수 early-exit 가 한 epilogue 로 통합.
3. **type tag protocol 매핑은 cumulative**: 각 함수 별 byte_append immediate 누적 매트릭스. 4 writer 만 봐도 11 type tags + 6 sub-opcodes 식별.
4. **r0 backtrace 의 한계**: 함수 인자 입력 / prior BL return value 케이스는 식별 불가. dataflow analysis 필요.
5. **PIC 의 인자 기반 helper**: Ghidra 의 `void` 시그니처 의심. 실제는 r0 인자 사용 가능성.

**G. 다음 세션 권장**
- ⭐ **2Q**: FUN_000031dc 본문 분석 (chain dispatcher 후보)
- ⭐ **2R**: FUN_0004ad10 인자 패턴 검증 (context_getter 실제 인자 사용 여부)
- 2S: type-5 reader 발견 (cmp #0x05 arm 가진 함수)

---

## 📜 2026-05-10 PM-4 세션 작업 압축 (2K + 2L + 2M 본문 디스어셈블)

**테마**: PM-3 의 "top 15 카테고리 추정" 후속. 핵심 3 함수 (FUN_00057394 / FUN_00006334 / FUN_0003d5d0) 의 본문 capstone 디스어셈블로 정체 검증.

**A. 통합 도구 신규** ([disasm_subsystem_func.py](../../tools/recon/disasm_subsystem_func.py))
- argparse 기반 CLI (addr / end / label)
- cmp+conditional branch 자동 페어링 → arm 추출
- BL r0 backtrace (직전 ~3 instr 검색, mov/movs/adds #imm + ldr [pc,#imm] 인식)
- TARGETS_OF_INTEREST 매핑 (큐 API 10 + UI helper 7 + sound trigger) → 인자 분포 자동 통계
- PC-rel LDR 카테고리화 (negative_signed/got_slot/medium_int 등)

**B. 2K — FUN_00057394 = typed record writer 확정** ⭐
- byte_append immediate 분포: **0x05: 7x (record begin marker)**, 0x3d: 3x, 0x14/0x3/0x3f/0x40 각 1x
- flush_swap 7회 = byte_append #0x05 7회 → **각 record = 한 commit 단위**
- 7 records 패턴: `byte_append(0x05) + byte_append(<subop>) + (memcpy_read | u32_append | nothing) + flush_swap`
- 12 cmp arms 모두 null check 위주 → state machine 아님, **sequential serializer**
- → display list 가 아닌 **typed record stream codec** 가설 (0x05 = type tag, sub-opcode 5종)

**C. 2L — FUN_00006334 = 광범위 dispatcher (main loop 가설 약화)**
- 96 cmp arms (cmp #0: 53회 null check + 15 distinct nonzero values 1-22)
- 162 PC-rel LDR 중 135 = GOT slot offsets (글로벌 데이터 heavy 접근)
- **interesting BL 0건** — render/input/sound helper 호출 부재 → main loop 아니라 interpreter/serializer 후보
- 추가 단서: 187 internal BL → top FUN_00008aca 70회 (inner loop body 후보), FUN_00080664 22회

**D. 2M — FUN_0003d5d0 = sound subsystem dispatcher 확정** ⭐
- 22 cmp arms (cmp #0xc3, 0x0f, 0x1e, 0x04, 0x05, 0x15 등 다양)
- **(sound_trigger + helper_9fd64) 페어 패턴**: 21 sound_trigger + 17 helper_9fd64 calls — offset 차이 ~8 bytes 로 페어 호출
- → 한 sound 명령 = (sound_trigger setup + helper_9fd64 worker) 두 함수 호출
- sound ID immediate 21/21 모두 indirect (register/memory load) — capstone 1-3 instr backtrace 부족, 더 깊은 propagation 필요
- 127 PC-rel LDR (medium_int 69 + small_int 31) → **100+ 정수 상수 임베드** = sound parameters

**E. 큐 record 포맷 가설 (2K 발견)**
```
record:
  byte type_tag      ; 0x05 = type-A (FUN_00057394 emit)
  byte sub_opcode    ; type 별 의미 다름 (5종 for type-5)
  variable args      ; memcpy_read 또는 u32_append 또는 없음
  flush_swap()       ; commit
```
→ 다른 큐 writer (FUN_00056bf8 / FUN_00064048 / FUN_000630e8) 의 type tag 매핑으로 protocol 풀이 가능.

**F. 핵심 교훈**
1. 통합 도구 (`disasm_subsystem_func.py`) 한 개로 3 함수 분석 — 함수별 specific 도구보다 효율.
2. **cmp arm 카운트 + 분포** = 함수 카테고리 1차 지표. 12 arms (null 위주) = serializer / 22 arms (다양) = subsystem dispatcher / 96 arms = wide dispatcher.
3. **BL r0 1-3 instr backtrace 한계**: mov/movs #imm 만 잡힘. register-loaded args 는 propagation 필요. sound ID 21/21 unknown 이 그 예.
4. **typed record stream 가설 = 큐 protocol 의 열쇠**. byte_append 의 첫 인자가 일관된 type tag 패턴이면 코덱 식별 용이.
5. **"main loop" 검증은 helper 호출 패턴으로**. 외형 (96 arms, 10KB) 아닌 render/input/sound 호출 여부로 판단.

**G. 다음 세션 권장**
- ⭐ **2N**: FUN_00056bf8 본문 분석 → 다른 큐 writer/reader type tag 발견
- ⭐ **2O**: FUN_00008aca 분석 → main_dispatcher inner loop body 정체
- 2P: r0 backtrace 10+ instr propagation 강화 → sound ID 매핑

---

## 📜 2026-05-10 PM-3 세션 작업 압축 (2I + 2J + top 15 stub 카테고리 추정)

**테마**: PM-2 의 "402 PIC stub 패턴" 발견 후속. ranking 도구 + 큐 caller 매핑 + top 15 일괄 분석으로 핵심 subsystem 다수 식별.

**A. 2I — 402 stub ranking** ([rank_pic_stubs.py](../../tools/recon/rank_pic_stubs.py))
- 각 stub size (다음 entry까지 거리) + BL count (capstone walk_with_skip) + caller_count (full-binary BL 디스어셈블 → target 매칭)
- top 5 by size: FUN_00006334(10KB), FUN_00060ab4(8.8KB ✅), FUN_00026a80(8.4KB), FUN_000031dc(6.7KB), FUN_000818f0(5.4KB)
- top 5 by callers: FUN_00075b98(58), FUN_00040ea0(38), FUN_0003d5d0(37), FUN_000439a0(37), FUN_0008578c(34)
- top 5 by BLs: FUN_000818f0(287), FUN_00026a80(209), FUN_00006334(187), FUN_00060ab4(155), FUN_0003add0(137)
- 0 direct caller (PIC-indirect-only): 39 / 402

**B. 2J — 큐 API caller 매핑** ([find_queue_callers.py](../../tools/recon/find_queue_callers.py))
- 10개 큐/IO API 함수 (`0x7e150, 0x7e184, 0x7e1c4, 0x7e890`, etc.) 의 binary 전체 BL 사이트 추적
- **138 BL sites → 31 distinct caller functions**
- 큐 호출의 70% 가 4 함수: FUN_00057394 (29 calls) + FUN_00056bf8 (18) + FUN_00064048 (16) + FUN_000630e8 (14)
- producer-only 8 함수, consumer-only 7 함수 (모두 0x64980-0x64cc8 영역 = default_key_handler 이웃)

**C. top 15 stub 카테고리 추정** ([analyze_top_stubs.py](../../tools/recon/analyze_top_stubs.py))

| stub | 정체 추정 | 신뢰도 |
|---|---|---|
| FUN_00057394 (3.5KB) | **render command buffer / display list builder** | 높음 (graphics 20x + byte_append 19x + flush 7x + memset 10x) |
| FUN_00006334 (10KB) | main game loop dispatcher / entity list iterator | 중간 (cmp 17 arms + +0x18 read 75x) |
| FUN_00026a80 (8.4KB) | main subsystem router | 중간 (51 distinct BL targets) |
| FUN_000818f0 (5.4KB) | per-entity update loop | 중간 (212x context getter + 42x to 0x82df4) |
| FUN_0003d5d0 (4.3KB, 37 callers) | **sound subsystem dispatcher** | 높음 (sound_trigger 21x + cmp 22 arms) |
| FUN_00056bf8 (836B) | save/load codec | 중간 (queue read+write 둘 다) |
| FUN_000630e8 (3.9KB) | command/event processor | 중간 (cmp 12 arms + queue) |
| FUN_00075b98 (324B, 58 callers) | init/reset helper | 중간 (memset+58callers) |
| FUN_0003add0 (3.1KB, 0 callers) | PIC-indirect frame callback | 중간 (state +0x1dc~+0x1f0 16-byte struct) |

**D. 핵심 교훈**
1. **stub ranking 은 ROI 큰 자동화**: 402 stubs 중 top 15 만 봐도 핵심 subsystem 다수 식별. 사이즈/호출자/BL 카운트는 단순 통계지만 정체 추정에 충분.
2. **큐 API 같은 "특이" 함수의 caller 추적이 강력**: 138 BL sites → 31 함수만, 그중 4개가 호출의 70% 차지. **subsystem boundary 탐색의 좋은 출발점**.
3. **카테고리 자동 추정 휴리스틱이 1차 분류로 유용**: queue_writer / drawing_heavy / state_machine_or_dispatcher / sequential. 정밀 식별은 본문 디스어셈블 필요.
4. **+0x002~+0x004 (작은 state)** vs **+0x100+ (큰 game state)** 구분으로 함수 역할 추정. 작은 offset = stack/worker, 큰 offset = page/entity state.

**E. 다음 세션 권장**
- ⭐ **2K**: FUN_00057394 본문 디스어셈블 → display list 가설 검증 + 큐 byte 포맷 식별
- ⭐ **2L**: FUN_00006334 본문 디스어셈블 → 17 arm state machine entry table → main loop 가설 검증
- **2M**: FUN_0003d5d0 sound dispatcher 22 명령 디코드 → BGM/SFX 매핑

---

## 📜 2026-05-10 PM-2 세션 작업 압축 (2F + 2G 일괄 + 402 stub 패턴 발견)

**테마**: 2F (mode 2 literal pool 해석) + 2G (battle 트리거 별도 추적) 자동 분석 일괄. 두 가설 모두 기각하면서 더 큰 시스템적 발견 (Ghidra 가 402 PIC 함수 본문 분석 실패) 도달.

**A. 2F: mode 2 (FUN_00060ab4) 정정** ⭐
- 신규 도구 [`tools/recon/parse_mode2_ui_data.py`](../../tools/recon/parse_mode2_ui_data.py) — capstone `walk_with_skip` 패턴
- **9KB 가 100% 코드** (이전 "1.5KB+7KB 데이터" 는 capstone 첫 stop 을 데이터로 오인)
- 3 code blocks (1568 / 4870 / 2366 bytes) + 2 byte alignment 패딩 2건 = 8804 bytes 디코드
- 정체 = page 2 UI rendering function: 54 BL (top: 화면 포인터 29x, drawText 18x, sound 15x), switch 패턴 부재
- 207 PC-rel LDR 카테고리: negative GOT-rel 111, medium_int 47, GOT slot offset 9, RGB 색상 2

**B. 2G: FUN_00064048 (default key handler) 분석**
- 신규 도구 [`tools/recon/disasm_default_key_handler.py`](../../tools/recon/disasm_default_key_handler.py)
- Ghidra 디컴파일은 `{ FUN_0004ad10(); }` stub 처럼 보이지만 raw bytes 는 진짜 PIC 함수 (60 byte stack frame + GOT setup)
- 2KB 함수, 54 BL — top: `0x4ad10` 29x (GOT context getter), `0x7e150` 10x (byte buffer append), `0x7e890` 4x (ring buffer flush)
- cmp #imm 분포: 7 distinct values, 거의 == 0 → **state machine 아님**
- 결론: ring buffer 직렬화 호출 패턴 — GVM 이벤트 큐 API 사용. battle 트리거 후보 기각

**C. state[0x460] 정체 확인** — `if (state[0x460] != 0) FUN_0000defc(screen, 0, 0, state[0x70], state[0x74], 0x78, 0, 0, 0)` 패턴이 8개+ 함수에 등장 → **menu item 선택 highlight 플래그** (battle 트리거 아님)

**D. ⭐⭐ Ghidra PIC 디컴파일 시스템적 실패 발견**
- `void FUN_xxxxxxxx(void) { /* WARNING: Subroutine does not return */ FUN_0004ad10(); }` 패턴이 **402 함수** 에 등장
- 1470 함수 중 **27%** 가 자동 분석에서 본문 추출 실패
- 지금까지 "PIC indirect call 추적 한계" 라고 정리해 온 것의 진짜 원인
- 본 세션의 mode 2 / FUN_00064048 둘 다 이 402 안에 포함

**E. 발견된 GVM SDK 이벤트 큐 API**
- `FUN_0007e150(byte)` = byte buffer append (size at +8, data at +0xc)
- `FUN_0007e184(uint*, uint)` = memcpy from buffer (deserialize)
- `FUN_0007e1c4(uint)` = 32-bit word append
- `FUN_0007e890()` = ring buffer flush + swap (cyclic 4-slot 모드)
- 구조체 layout: `[+0:status, +1:idx_mod_4, +8:size, +0xc:data...]`

**F. 핵심 교훈**
1. **Ghidra 디컴파일을 그대로 믿지 말 것**: "Subroutine does not return" + 단일 호출 = PIC 분석 실패 신호. raw bytes / 다음 함수 entry 까지 거리로 진짜 함수 크기 확인.
2. **capstone walk_with_skip 패턴 표준화**: 첫 disasm stop 은 거의 항상 alignment. 2 byte 건너뛰면 진행. data gap 으로 잘못 결론 짓지 말 것.
3. **가설 정정 절차**: 7KB literal pool 가설 (2026-05-09 PM-3) 한 세션 만에 정정. 빠른 검증으로 효율 유지.
4. **stub 패턴은 시스템적 문제**: 단일 함수 (FUN_00064048) 의 "stub-처럼-보임" → 같은 패턴이 402 곳에 → 진짜는 Ghidra 의 PIC 처리 한계. 단일 함수 트러블슈팅보다 패턴 인식이 더 가치.

**G. 다음 세션 권장**
- ⭐ **2I**: 402 stub 함수 우선순위 분류 (size, BL count, 호출 빈도) → top 후보부터 walk_with_skip 분석
- ⭐ **2J**: FUN_0007e150 큐 producer/consumer 매핑 → 게임 로직 진입점 후보
- 사용자 블로커 (SMAF / 번역) 게임 체감 영향 큼

---

## 📜 2026-05-10 AM 세션 작업 압축 (state[0x94] 재해석 + 3 entry caller 한계 확정)

**테마**: 사용자 GUI 동행으로 main loop 추적 시도 → 정적 분석 ceiling 도달 확인. 그러나 우회 단서로 `state[0x94]` 의 정체가 mode/battle 이 아닌 3-페이지 UI 탭 인덱스로 재해석됨 → PROGRESS 다수 가설 정정.

**A. 사용자 GUI 동행 — 6단계**
1. 함수 포인터 hex 검색 (`Search → Memory`): thumb-bit-set/clear 두 형태 × 3 entry = 6 검색 → **모두 0건** → 함수 포인터 = 런타임 동적 주입 확정
2. 바이너리 시작 (`0x0`) 관찰: `Reset / UndefinedInstruction / SupervisorCall` 라벨은 표준 ARM 예외 벡터 자동 부여, 그러나 실제 바이트는 분기 명령 아님 — SKT GVM 펌웨어가 표준 벡터 미사용
3. GOT 베이스 (`0xb2c40`) 확정: 20+ 함수 XREF (R/W). 4 low-addr 함수가 슬롯에 쓰기 → 초기화 함수 후보
4. 4 low-addr 함수 (`0xf9c/0xffc/0x10c0/0x10f4`) 디컴파일 → **resource open/close/count/read** API wrapper 확정 (main loop 단서 아님)
5. 3 entry XREF 직접 확인: 모두 0건 (재확인). `FUN_0008dcd8` 는 GUI 인식 / headless export 누락
6. `state[0x94]` 셋 위치 grep → `FUN_00070f34` 발견

**B. ⭐⭐ `FUN_00070f34` 발견 — 키 입력 핸들러**
```c
void FUN_00070f34(int param_1, int param_2) {  // param_1=state, param_2=key
  iVar1 = param_1 + DAT_000711ec;               // FUN_0006619c 와 동일 패턴
  if (state[0x94] == 1 && param_2 == 0x2a) ...   // page=1 + '*'
  else if (param_2 == 0x31) state[0x94]--;       // '1' 키 → page--
  else if (param_2 == 0x33) state[0x94]++;       // '3' 키 → page++
  else if (param_2 == -0x10) ...
  else FUN_00064048();                            // default key handler
}
```
- 키 '1'/'3' 으로 `state[0x94]` 가 0 ↔ 1 ↔ 2 순환 (wrap)
- → **`state[0x94]` = 3-페이지 UI 의 탭 인덱스** (mode/battle 아님)
- `FUN_0006619c` 와 sibling = paint/key 짝 callback 가설

**C. PROGRESS 가설 정정**
| 기존 가설 | 2026-05-10 평가 |
|---|---|
| mode 0/1/2 = NPC/menu/battle 분기 | ❌ 기각. 실제는 한 화면 안의 3 탭 |
| `FUN_00060ab4` (mode 2, 9KB) = battle/cutscene | ❌ 기각. **3번째 탭 페이지 UI** 일 가능성 — 7KB 임베디드 데이터 = UI 레이아웃 |
| dispatcher 1 (NPC dispatcher) 19 opcode = NPC 행동 | 재검토 필요. page 0 의 19 UI 요소 가능성 |
| dispatcher 2 = menu/dialog UI handler | ✅ 유지. 단 "menu 모드 진입" 이 아닌 "page 1 컨텐츠" |
| 3 entry indirect caller 추적 가능 (Ghidra GUI) | ❌ 한계 확정. Ghidra Script 만 마지막 카드, ROI 낮음 |

**D. 핵심 교훈**
1. PIC 바이너리에서 indirect call caller 추적은 정적 분석 ceiling. Ghidra 자동 + GUI XREF + decompiled grep 모두 0건이면 마지막은 Script.
2. **빠른 가설 정정 절차** 필요. mode 0/1/2 가설을 4 세션 끌고 왔으나 키 핸들러 1개 발견으로 즉시 기각. 가설은 항상 다른 코드 패스로 교차 검증.
3. 사용자 GUI 협업의 가치: hex 검색 / 캡처 같은 단순 작업도 자동 분석이 못 본 분포 (예: 0xb2c40 의 20+ XREF) 시각화. 다만 ROI 낮은 단계는 일찍 인지하고 우회.
4. `all_decompiled.c` (헤드리스 export) 의 한계: GUI 인식 함수도 export 누락 가능 (`FUN_0008dcd8`). GUI 기반 분석은 export grep 으로 검증 필요.

**E. 다음 세션 권장**
- ⭐ **2F**: mode 2 의 7KB literal pool 을 UI 레이아웃 데이터로 해석 시도 (자동)
- ⭐ **2G**: 진짜 battle 트리거 — 다른 state offset (e.g. `+0x460`) 추적 또는 `FUN_00064048` 분석
- 또는 **사용자 블로커** (SMAF/번역) 로 우회 — 게임 체감 영향 큼

---

## 📜 2026-05-09 PM 후반-3 세션 작업 압축 (§4.4 자동 후속 — 2A/2B/2C 일괄)

**테마**: 이전 세션의 자동 가능 항목 (2A/2B/2C) 전체 capstone 일괄 분석 — 사용자 입력 없이 진척 가능한 부분 소진.

**A. dispatcher 1/3/4 의 21 handler 일괄 디스어셈블** (2A) — `tools/recon/disasm_all_dispatcher_handlers.py` 신규
- 4 jump table 자동 디코드 (jt @ 0xa9cc4 / 0xa9d70 / 0xabaa8 / 0xabc68) → 19 entries × 4 dispatcher
- dispatcher 1 (NPC 1, FUN_0005d214): handlers 0x66338(0x00~0x0c, 0x800B) / 0x6788e / 0x67a68 / 0x67b58 / 0x67dc8 / 0x67ee8 / 0x67ff0
- dispatcher 3 (FUN_0008b2e8 inline 0x8c19c): handlers 0x933da / 0x935b8 / 0x93934 / 0x93b28 / 0x93d48 / 0x94044 / 0x9428e / 0x9447a
- dispatcher 4 (FUN_0008dcd8 inline 0x8eb80): handlers 0x95bfe / 0x960e8 / 0x962f4 / 0x9651c / 0x9685c / 0x96aa6 / 0x96bf8
- 결과 → `work/h3/dispatcher_handlers_summary.json`. handler 별 BL/PC-rel LDR/record-offset hint 집계 + cross-handler frequency

**B. PIC veneer table 식별** ⭐ — 핵심 발견
- 0xa42a0 ~ 0xa42cc 영역: `bx r3 / mov r8,r8 (NOP) / bx r4 / NOP / ... / bx lr / NOP` 패턴 12 entries
- 모든 dispatcher BL 의 65/14 calls (의 다수) 가 이 veneer 로 향함 — 즉 **register-indirect call 의 trampoline**
- 의미: 핵심 helper 함수가 동적으로 정해지는 함수 포인터 → 자동 caller-chain 추적 본질적 한계 (PROGRESS 의 "PIC indirect dominant" 와 일치)
- helper prologue 분석 (`tools/recon/disasm_helper_funcs.py`): 0x10f84 / 0x10f4 / 0xf9c / 0xffc 등은 진짜 함수 — 작은 state-machine 또는 KVM API wrapper

**C. mode 2 (`FUN_00060ab4`) 본문 분석** (2B) — `tools/recon/disasm_mode2_fn.py` 신규
- 9KB (0x60ab4 ~ 0x62d1c) 중 **실제 코드 ~1.5KB (768 instr) + 임베디드 literal 풀 ~7KB**
- 16 직접 BL (veneer 0건) — `0x4ad10`(4) `0x9f624`(3) `0xd53c`(2) `0x9fb78`(2) `0xec80`(1)
- `cmp Rn, #imm` (switch) 패턴 **없음** — sequential setup 코드
- 추정: **scene/render primitive** with baked data tables — `0x9f624` 가 graphics primitive dispatcher (앞 세션의 9KB 함수 분석에서 확인된 switch-laden 함수)
- battle / cutscene / map transition 중 어느 것인지는 사용자 GUI 의 caller 식별 필요

**D. _scn parser strings table 위치 확정** (2C) — 부분 진척
- 문자열 위치: 0xaac58 ~ 0xaad00 영역
  ```
  0xaac58: "/event/e0000_scn"
  0xaac6c: "/map/map0_mp"
  0xaac7c: "Event_freeID~~~~~~~~~~~1"
  0xaac98: "/map/sprite_0_cif"
  0xaacac: "/map/sprObj0_bm"
  0xaacbc: "/map/obj_0_bm"
  0xaaccc: "/npc/face_bm"
  0xaacdc: "/npc/imo_bm"
  0xaace8: "/map/theme_0_bm"
  ```
- 이 9 string 은 게임 자산 로딩 path 템플릿 (sprintf 로 숫자 substitute 후 fopen)
- **직접 xref 0건** — 절대 주소 / GOT-relative signed offset 모두 검색했으나 매칭 없음
- 16-bit offset 0xc58 (= 0xaac58 - 0xaa000) 은 binary 안 3 위치에 등장 — 그러나 그 중 2개는 함수 내부 literal pool (오인 가능성), 1개는 jump table 데이터
- 결론: 진짜 _scn parser entry 는 사용자 GUI 의 cross-reference (Ghidra `Window > References to`) 추적 필요. 자동 한계

**E. 자동 진행 한계 정의**
- 2A 의 record_offset_hint (0x100~0x400 immediate offset) 들은 NPC slot record offset 이 아니라 **dispatcher 의 GOT-relative global state 접근** (r7 = sl 역할). NPC 좌표 offset 자동 식별 본질적 불가능 — caller 트래커가 필요
- 모든 dispatcher BL 의 50%+ 가 veneer indirect call 이라서 **callee 식별이 동적 포인터 해석 필요**

**F. 신규 도구 3개**
- `tools/recon/disasm_all_dispatcher_handlers.py` — 4 dispatcher × 21 handler 일괄 capstone + cross-handler 통계
- `tools/recon/disasm_helper_funcs.py` — top BL target prologue 분석 (veneer vs real helper 구분)
- `tools/recon/disasm_mode2_fn.py` — mode 2 entry FUN_00060ab4 본문 + literal pool magic 검색

**G. 산출물 (work/h3/, gitignore — 재현 명령으로 생성)**
- `dispatcher_handlers_summary.json`
- `helper_func_prologues.json`
- `mode2_disasm.json`
- (기존) `scn_dispatcher_jumptable.json` — dispatcher 4 (jt 0xabc68) 19 entries

**H. 핵심 교훈**
1. **PIC veneer 가 BL 통계의 dominant noise** — `0xa42a0` 65 calls 는 실제로 65개의 다른 함수 indirect call. BL frequency 만으로 helper 식별 불가.
2. **자동 분석의 ceiling 도달**: handler 본문 디스어셈블 → record-offset 자동 추출은 **GOT-relative global vs slot record offset 구분 어려움**. 사용자 GUI 의 register tainting / caller chain 분석이 본질적으로 필요.
3. **mode 2 의 7KB literal 풀**: 큰 함수일수록 임베디드 데이터 비중 큼. 9KB 중 실제 코드는 1.5KB → "큰 함수 = 복잡한 로직" 가설 부정.
4. **strings table 의 PIC 참조 패턴**: 16-bit offset (movw imm12) + 베이스 register 합산 → linear scan 만으로는 xref 추적 부정확.

**I. 다음 세션 권장 작업**
- ⭐ **2D**: 3 entry (`FUN_0006619c` / `FUN_0008b2e8` / `FUN_0008dcd8`) 의 indirect caller 추적 — Ghidra GUI 의 `Window > Defined Strings` 에서 0xaac58 strings 의 xref 따라가서 main loop 발견
- 또는 **mode 2 분기 의미 식별**: `FUN_00062d1c` (mode selector) 의 caller 추적으로 `state[0x94]=2` 가 언제 셋되는지 → battle 진입점 식별
- **SMAF→OGG 외부 변환** 또는 **번역 LLM 호출** — 게임 체감 영향 큰 사용자 블로커들

---

## 📜 2026-05-09 PM 후반-2 세션 작업 압축 (§4.4 자동 후속 — dispatcher 2 재해석)

**테마**: 95% 해독 후 1A/1B/1C/1E 자동 분석으로 dispatcher 2 정체 재해석 + 3 entry indirect 확정.

**A. dispatcher 2 capstone 디스어셈블 (1A)** — _scn parser 가설 부정
- handler 7개 본문 디스어셈블 → 모두 sprite text drawing (`FUN_0003ecfc`) + sound trigger (`FUN_00099764`) 호출 패턴
- 결론: dispatcher 2 (`FUN_0005f948`) 는 _scn parser 가 **아니고** menu/dialog UI state machine
- 19-opcode 매칭은 컴파일러가 같은 dispatcher 패턴을 여러 sub-system 에 사용한 결과
- 진짜 _scn byte stream parser 는 별도 위치 — 다음 세션 과제 (2C)

**B. NPC slot record offset grep (1B)** — 좌표 위치 한계 확인
- dispatcher 본문에는 +0x3b3/+0x3b6/+0x3b8 만 access — 좌표 없음
- 좌표는 **handler 영역 (Ghidra 미인식) 또는 NPC init 함수에 있음** → 2A 의 capstone 디스어셈블로 발견 가능

**C. mode 2 (`FUN_00060ab4`) 분석 (1C)** — 9KB 큰 함수
- push prologue 확인 → 진짜 함수 (0x60ab4 ~ 0x62d1c, 9KB)
- Ghidra 본문 디컴파일은 panic stub 만 — boundary 또는 분기 인식 실패
- mode 2 = battle / cutscene / map transition 추정 — capstone 본문 디스어셈블 필요 (2B)

**D. dispatcher 3/4 inline 위치 (1E)** — 두 host 함수 확정
- dispatcher 3 inline @ `0x8c19c` (FUN_0008b2e8 안)
- dispatcher 4 inline @ `0x8eb80` (FUN_0008dcd8 안)
- 두 entry 모두 BL caller 0건 → PIC indirect call 만으로 진입

**E. 자동 분석 도구 2개 신규**
- `tools/recon/disasm_dispatcher2_handlers.py` — capstone (5.0.7) 으로 handler BL/LDR 추출
- `tools/recon/find_npc_record_offsets.py` — record offset access 자동 추출

**F. 핵심 교훈**:
1. 19-opcode 패턴은 **NPC dispatcher 단독 표지가 아님**. 컴파일러가 여러 sub-system 에 같은 jump table 패턴 사용. record stride + handler 호출 패턴 둘 다 봐야 의미 식별.
2. capstone 디스어셈블이 Ghidra 미인식 영역 분석에 필수 — Python 환경 (`import capstone`) 확인 후 자동화.
3. 자동 분석으로 발견된 함수 chain (caller chain) 은 신뢰도 높음. find_function_for_position 같은 character-pos 기반 함수 식별은 부정확 (decompiled output 안의 indented call 도 매칭됨).

---

## 📜 2026-05-09 PM 후반 세션 작업 압축 (§4.4 95% 해독)

**테마**: 부분 해독 (50%) 에서 caller-of-caller 자동 추적으로 **3-way mode selector + game update entry** 까지 도달 (95%).

**A. 4 Dispatcher 자동 발견** (`find_all_19op_dispatchers.py`)
- 같은 19-opcode + 7 distinct handler 패턴 자동 검색 → binary 안 6 출현 위치 → 4 distinct dispatcher
- 4 dispatcher: jt @ 0xa9cc4 / 0xa9d70 / 0xabaa8 / 0xabc68
- 각 dispatcher 의 jump table 19 entries 디코드 (raw binary 직접 읽기)

**B. Caller chain 자동 추적** (`find_bl_callers.py` 반복)
- `FUN_0005d214` ← `FUN_0005c038` ← `FUN_00062d1c` ← `FUN_0006619c` (game update entry)
- `FUN_0005f948` ← `FUN_0005e6ac` ← `FUN_00062d1c` ← `FUN_0006619c`
- 4 단계 Thumb-2 BL 디코드로 진짜 entry 까지 도달

**C. 3-way mode selector 발견** (`FUN_00062d1c`)
- `state[0x94] byte = mode (0/1/2)` 로 sub-dispatcher 선택
- 게임이 frame 마다 entry 호출 → mode 분기 → dispatcher 실행

---

## 📜 2026-05-09 PM 세션 작업 압축 (§4.4 NPC dispatcher 부분 해독)

**테마**: 2026-05-08 에서 "자동 식별 불가능 확정" 이었던 §4.4 를 사용자 GUI + 자동 분석 도구 8개 결합으로 부분 해독. dispatcher 함수 + jump table + record 구조 확정. caller 추적은 indirect call 한계 도달.

**A. NPC behavior dispatcher 발견** ⭐⭐
- 자동 분석 흐름:
  1. v3 통계 (find_dispatcher_v3.py) — `0x8e112` 후보 (UNRECOVERED_JUMPTABLE 검색)
  2. Ghidra GUI (사용자) — 실제 디컴파일 코드에서 dispatcher 패턴 확인 (`if (0x12 < opcode) ...; jump table call`)
  3. raw binary scan (decode_scn_jumptable.py) — jump table 19 entries → 7 distinct case label
  4. 함수 boundary 검증 (find_real_func_start.py) — push prologue 위치로 진짜 함수 영역 (`0x8dcd8` ~) 확정
  5. caller 추적 (find_bl_callers.py) — Thumb-2 BL 디코드, 외부 호출 0건 확정 (function pointer indirect)
- **핵심 결과**:
  - dispatcher 1: **`FUN_0008dcd8`** (size ~3KB, Ghidra 미인식 — 사용자 수동 생성 필요)
    - sub-block 1: `0x8e112` (사용자 rename: `scn_dispatch_evt`)
    - sub-block 2: `0x8e89e` (jump table call site)
  - dispatcher 2: **`FUN_0008b2e8`** (size ~9.6KB, sister, 다른 jump table) — 추정 battle/dialog dispatcher
  - jump table @ `0x000abc68`, 19 entries (opcode 0~0x12)
  - 7 distinct case label (0x00~0x0c 공통 `0x95bfe` + 0x0d~0x12 6 unique)
  - NPC slot record: stride 0x3c4 × 0x3c, +0x3b3 flag, +0x3b6 opcode short, +0x3b8 arg short

**B. 자동 분석 도구 8개 신규** (`tools/recon/`)
- `find_dispatcher_v3.py` — 1,470 함수 통계 (UNRECOVERED_JUMPTABLE / switch / chain compare)
- `extract_candidate_funcs.py` — all_decompiled.c 에서 함수 본문 추출
- `rank_size_top.py` — Function Size sort 결과 우선순위 정렬
- `decode_scn_jumptable.py` — raw binary 에서 jump table 디코드
- `check_handler_prologues.py` — handler 주소가 함수 시작인지 ARM Thumb prologue 검증
- `find_real_func_start.py` — 영역에서 push prologue 위치 → 진짜 함수 boundary
- `find_dispatcher_caller.py` — 절대/GOT-relative 주소 패턴 검색
- `find_bl_callers.py` — Thumb-2 BL 명령어 디코드 → caller 검색

**C. 한계 도달**
- caller chain: dispatcher 안의 self-loop (0x8e89a → 0x8e112, 0x8e12a → 0x8e89e) 만 발견. 외부 BL 호출 0건. function pointer indirect call 만으로 진입 — Ghidra 자동 추적 본질적 한계.
- handler 본문: Ghidra 가 `0x95xxx ~ 0x96xxx` 영역을 작은 stub 함수들로 잘못 분리 → 디컴파일 끊김. 사용자 GUI 에서 `Override Switch Statement` 또는 영역 재분석 필요.

**D. 다음 세션 진척 가능**
- §4.4 1A: handler 영역 디컴파일 (사용자 GUI, 30~60분)
- §4.4 1B: caller RAM 동적 셋업 위치 추적
- §4.2: NPC slot record 안의 다른 offset (좌표) 검증 — 자동 가능, 발견된 stride 활용

**핵심 교훈**:
1. dispatcher 가 BL 직접 caller 0건이라는 건 **function pointer indirect call** 이라는 뜻. Ghidra 자동 추적은 PIC 환경에서 본질적 한계.
2. Ghidra 가 jump table 자동 복구 실패 시 case 영역을 작은 stub 함수로 잘못 분리. 진짜 함수 boundary 는 raw binary 의 push prologue 위치로 직접 확정해야.
3. dispatcher 후보 자동 식별 휴리스틱: switch 문은 신뢰도 낮음 (UNRECOVERED_JUMPTABLE 로 분류됨). UNRECOVERED_JUMPTABLE 표지 + 작은 정수 chain compare + RGB565/4-bit nibble 표지 없음 = 강력 후보.

---

## 📜 2026-05-09 AM 세션 작업 압축

**테마**: 사용자 블로커 (Ghidra/SMAF/번역/디자인) 제외하고 자동 진행 가능 항목 소진. 우선순위 #7 (enemy/boss cif 디코더) 코드화 완료.

**A. boss/enemy cif 디코더 라이브러리화** ✅
- `tools/recon/analyze_cif.py` 에 FUN_00098ef8 알고리즘을 5개 함수로 코드화:
  - `decode_cell_byte(cb)` — bit 7=special / bits 5..6=orient / bits 0..4=ref 분해, 0x7f sentinel 인식
  - `parse_boss_header(data)` — slot_count, category, indices, body_offset 추출
  - `parse_boss_cells(body, max_cells=-1)` — 4-byte stride 셀 스트림 디코딩
  - `split_frames_by_sentinel(cells)` — sentinel cell 을 frame 경계로 분할
  - `boss_cif_summary(data)` — 단일 cif 통계 리턴
- `tools/recon/dump_boss_cif.py` (신규) — 39 boss/enemy cif 일괄 분석 → `work/h3/boss_cif_summary.json`
- 통계 결과: 4개 파일에 sentinel 존재 (boss0=46, boss1=2, boss3=86, boss4=147 — 4-byte aligned scan 기준). 나머지 35개는 sentinel 0건 → 단일 frame.
- 단위 테스트 13건 추가 ([test_analyze_cif.py](../../tools/recon/test_analyze_cif.py)): cell byte decode 5건, header parse 2건, cells parse 3건, frame split 3건, real-file 2건.

**B. 잔여 우선순위 검토**
- **#5 일본어 i18n** — "일본어/한국어 매핑은 사용자 검수 전제" 명시 → LLM API 키도 사용자 블로커. 자동 처리하면 검토 부담만 늘어남 → 스킵.
- **#6 h4-h11 walk-cycle 추가 분석** — Ghidra 진척 의존 + 게임 영향 없음 (h0 만 wire). 4시간+ ROI 낮음 → 스킵.
- **결론**: 자동 진행 가능 항목 모두 소진. 다음 진척 은 모두 사용자 입력 (Ghidra §4.4 caller chain / SMAF 도구 / 번역 API / 디자인 결정).

**C. convert_cif --boss 모드 + asset-formats 문서화** (커밋 `169d6ba`)
- `convert_cif.py` 에 `--boss` 옵션: FUN_00098ef8 디코더로 cell 까지 JSON dump (frame_summaries 64 frame cap).
- `test_convert_cif.py` 신규: 5 단위 테스트.
- `docs/asset-formats.md` _cif 섹션 갱신: hero/boss/enemy frame 인코딩 명세 + cell byte 분해 + 미확정 항목.

**D. 테스트 커버리지 확장** (커밋 ⌛)
- `test_convert_text.py` (5건): build_text_table fixture + EUC-KR 라운드트립 + InGame_txt 통합.
- `test_convert_palette.py` (6건): Hero3 4-byte / Hero4 8-byte 양 포맷, size 미스매치 검증.
- `test_convert_dat.py` (8건): EUC-KR 한글 시퀀스 추출 (단일/다중/min_chars/ASCII 거부/incomplete lead byte).
- `test_translation_dict.py` (9건): for_game H3/H4 분리, all_translations 병합, alias 호환, 캐릭터 leak 검사, 사전 무결성.

**E. 검증**
- Python **89 test 통과** (skip 8: PIL 3 + work/h3 미추출 5 — 사용자 PC 에서는 통과).
- Android 빌드 검증 — 본 세션 환경(Linux 샌드박스)은 Android SDK + 네트워크 부재로 미실행. 사용자 PC 에서 `:app:assembleDebug` + `:app:testDebugUnitTest` 32 통과 확인 필요. 변경분이 Android 코드에 영향을 주지 않으므로 회귀 위험 0.

**핵심 교훈**:
1. boss/enemy cif 의 4-byte 셀 stride 는 hero h0 (`[x, y, ref, flag]`) 와 다른 의미: byte 0 = cell_byte (orient/ref/special) → 같은 cif 포맷이지만 hero 와 boss 가 별개 디코더 사용. 향후 통합 시 이 구분 유지 필요.
2. sentinel 분포가 보스/엔미별로 매우 다양 (0~662). 단일 frame splitter 로 모든 cif 처리 가능하지만, frame 경계 의미는 파일별 검증 필요.
3. cell ref → BM 파일 매핑은 미해결. cif 헤더 indices 와 5-bit ref 의 관계 분석이 다음 단계 (전투 sprite 베이킹 시점).

---

## 📜 2026-05-08 세션 작업 압축

**테마**: P0 디바이스 검증 → §4.4 dispatcher 자동 식별 시도 (실패) → §4.3 boss decoder 발견 → 자동 가능 cleanup 마무리.

**A. P0 디바이스/에뮬레이터 walk-cycle 시각 검증** ✅
- 컨택트 시트 (`work/h3/walk_check/h0_sheet.png`) 시각 분석으로 h0 매핑 확정.
- dir 0 = DOWN (face 가시), dir 1 = UP (후면), dir 2/3 = LEFT/RIGHT mirror.
- `facing_to_dir=[0,1,2,3]` 올바름. swap 불필요.

**B. h4-h11 broken bake 발견 + 정리**
- 부수 발견: h4-h11 의 dir_mapping.json 들이 모두 garbage 데이터.
  - h0: cells ref ≤ 39, x/y ∈ [-19, 25] — 정상.
  - h4-h11: ref=255, x=-124, flag=0xfd 등 — non-walk-cycle 프레임 잘못 추출.
- 원인: cif 구조가 h0 와 다름. h0 = 4 group × 8 frame 동일-lead 구조 (`0a020b`×8, `0a0501`×8, `0a0208`×8, `0a2208`×8). h4-h11 = 4-5 frame 짧은 그룹들 흩어짐.
- 시도한 가설들 (모두 빗나감):
  - boss-style 0x7f sentinel decoder → h4-h11 sentinel 거의 없음 (h4=3, h9=15, 나머지 0)
  - 첫 32 frame 가정 → h4 frame 4 부터 valid cell 시작
- 조치: [bake_hero_walkcycle.py](../../tools/converter/bake_hero_walkcycle.py) 에 `has_h0_walkcycle_structure()` check 추가. h4-h11 자동 skip → broken PNG 미생성. 단위 테스트 3건 추가 (h0 통과 / h4 / h11 차단).
- 자산 cleanup: 8 폴더 × 33 파일 = 264 broken 자산 삭제. h0_walk 만 잔존.

**C. Ghidra GUI 세션** — §4.4 dispatcher 추적
- 진입 단서: `onEventMessageOkKey @ 0xa6888`, `eventManager @ 0xa6ad8` 등.
- 시도 결과:
  - debug string xref → 0건 (PIC + GOT indirection, §4.1 풀 때와 동일)
  - 5 후보 GUI 검증 (FUN_182c4 / 186c8 / 18d08 / 190f8 / 98ef8) → 모두 sprite drawer/UI 류, dispatcher 0건
  - Python 휴리스틱 강화 (renderer 강 필터, byte read, callee size, UNRECOVERED_JUMPTABLE) → 최강 후보 FUN_00019b5a 도 4-bit sprite drawer
- **결론**: Hero3 binary 는 sprite engine 코드가 dominant. _scn dispatcher 자동 식별 **불가능 확정**. GUI 인터랙티브 caller-chain 분석 필요.
- 부수 발견 (실질 ROI):
  - **§4.3 boss/enemy cif decoder = `FUN_00098ef8 @ 0x98ef8`** — 0x7f sentinel skip + 4-byte cell stride. PROGRESS §4.3 미해독 항목과 정확히 일치. 향후 enemy/boss sprite 베이킹 진입점.
  - **§4.1 후속 (HD blender) = `FUN_00014e68`** — RGB565 mask + palette 이중 lookup. sprites_hd 자동 생성 진입점.
  - **animation tick handler = `UndefinedFunction_00041172`** — `frame_idx++` per tick + frame_count wrap.

**D. 단위 테스트 35건 추가**
- [test_convert_mp.py](../../tools/converter/test_convert_mp.py) — 18 test (parse_extras 4 strategy + edge cases + parse_mp + real-file regression)
- [test_convert_scn.py](../../tools/converter/test_convert_scn.py) — 17 test (extract_euckr_strings + parse_scn + parse_scn_v2 speaker/mode + real-file regression)
- 기존 [test_analyze_cif.py](../../tools/recon/test_analyze_cif.py) — 9 test (s8/parse_cells/find_frames/walk_cycle_structure)
- **총 44 Python test 통과** + Android 32 Kotlin test = 76 test.

**E. 신규 문서**
- [ghidra-findings-2026-05-08.md](ghidra-findings-2026-05-08.md) — Ghidra 세션 종합 결과 (16개 함수 분석)
- [ghidra-scn-opcode-walkthrough.md](ghidra-scn-opcode-walkthrough.md) — §4.4 detailed walkthrough (다음 세션 사용자 GUI 작업용)

**핵심 교훈 (이전 세션과 비교)**:
1. PIC indirect call 이 dominant 한 binary 에서는 자동 grep/패턴 식별이 sprite engine 함수에 휘둘림 — 사용자 GUI caller-chain 분석 외 답 없음.
2. cif animation 인코딩은 hero 별로 구조 다름 (h0 = 8-frame 동일 lead, h4-h11 = 4-5 frame 짧은 그룹). 단일 휴리스틱으로 일괄 처리 불가.
3. 단위 테스트는 자동 진행 가능 항목 중 가장 가치 높음 — 향후 변경 회귀 방지 + 사양 문서화 기능.

---

### 이번 세션 상세 로그 (2026-05-07) — 참고용 펼치기

<details>
<summary>A5~A18 시간순 진행 로그 (커밋 메시지로 추적 가능)</summary>

- **A5** §4.3 cell 4-byte stride 검증 (commit `021df49`) — y-bobbing diff 분석으로 stride 확정
- **A6** 25 lead group 분류 + 방향 매핑 가설 (`55a69fd`) — bit5 flip
- **A7** Placeholder 박스 시각 검증 (`a30f048`) — 4 lead group humanoid cluster 확인
- **A8** ref→BM cumulative 매핑 해독 (`67937b4`) — composite_cif_frame.py, 실제 sprite 합성 성공
- **A9** 4방향 walk-cycle 32 PNG 베이킹 (`55939da`) — h0_walk/dir{0..3}_{0..7}.png
- **A10** MapWalkScene wire (`394389d`) — loadHeroWalk
- **A11** walk_sheet 시각 + dirOrder 가설 (`ee3188d`) — initial intArrayOf(1,2,0,3)
- **A12~13** boss/enemy 별도 인코딩 확정 + 흩어진 cell 결론 (`a373d75`)
- **A14** _scn 세그먼트 통계 (`6566958`) — opcode 협소 확인
- **A15** boss/enemy 추가 관찰 (`8552ea0`) — sentinel/stride 다름
- **A16** 9 hero 일괄 베이킹 (`7b6b455`) — 288 PNG (h0/h4-h11)
- **A17** MainActivity 리팩토링 (`703677d`)
- **A18** flag byte 분포 분석 (`79640dd`) — draw_order 후보
- **A19** dirOrder 픽셀 symmetry 자동 검증 (`c224fd5`) — verify_walk_symmetry.py
- **A20** per-hero dir_mapping.json + MapWalkScene 로더 (`7040707`) — 캐릭터마다 mirror pair 다름
- **A21** h1/h2/h3 portrait 베이크 (`c6e5c0f`) — 74 PNG
- **A22** analyze_cif 단위 테스트 6/6 (`56c9a22`)

</details>

---

### (이전) 미커밋 변경 (2026-05-07 후반) — §4.2 _mp extras **부분 해독 + 데코 마커 렌더 완료**:

### A2) §4.2 _mp extras 해독 — **97% 자동 파싱 성공** ✅
- 사용자 Ghidra GUI 분석 시도 → string xref 막혀 보류 후 **경험적 디코딩으로 전환**
- 6 byte fixed-stride 레코드 포맷 확정: `[type_u8] [id_u8] [x_u16_LE] [y_u16_LE]` (좌표는 픽셀, /16 = tile)
- 헤더 변형 3가지 자동 감지: `h2_s6` (flag+count, 62맵) / `h1_s6` (count only, 54맵) / `multi` (2섹션, 14맵). 잔여 4맵은 sentinel/empty.
- **134/135 맵, 7,620 레코드** 추출 → `work/h3/converted/maps/*.json` 의 `extras_records` 필드
- [tools/converter/convert_mp.py](../../tools/converter/convert_mp.py) 에 파서 통합. `parse_extras()` 가 strategy/records/leftover 반환.
- **레코드 정체 판별**: 풀/덤불/가구 같은 시각 데코레이션 (NPC 아님). id 0x3e/0x3f 가 1567건 (~20%) 으로 풀 데코로 추정. type byte 0x00/0x80 ≈ 50/50 → facing/state 플래그 추정.
- NPC 위치는 _mp 안에 없고 `_scn` opcode 스트림에 있을 것으로 추정 — §4.4 미해독에 묶임. NpcRegistry/MapGraph 자동화는 §4.4 해독 후로 연기.

### A3) MapWalkScene 데코 마커 렌더 ✅
- [MapWalkScene.kt](../../android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt) 에 `DecoMarker` + `colorForDecoId()` 추가. id 별 색상으로 작은 점 표시 (풀=녹색, 가구=갈색, 특수=빨강 등). §4.1 sprite 디코딩 풀리면 진짜 그림으로 교체.
- 검증: `:app:assembleDebug` + `:app:testDebugUnitTest` 모두 BUILD SUCCESSFUL.

### A4) §4.3 _cif animation timing 분석 시작 — **부분 진척, 셀 구조 미해독**

**대상**: `hero/h0_cif` (8025 byte, 영웅 메인 애니메이션)

**확정된 구조**:
- 헤더 10 byte: `slot_count=8, category=0, indices=[1,2,3,10,17,19,16,8]` (8 슬롯이 BM 파일 번호 매핑)
- 애니메이션 데이터 (offset 10~): **41 byte 고정 프레임 레코드**
- `byte[0]` = `0x0a` (10) — **duration** (프레임 단위, ~333ms @ 30fps = 일반 걷기 속도)
- `byte[1]` = `0x02` — 애니메이션 타입 플래그 추정
- `byte[2]` = `0x0b` (11) — 셀 개수 추정
- `bytes[3..40]` = 38 byte 셀 합성 데이터 (구조 미확정)

**핵심 발견 — 프레임 페어링**:
- R0=R1, R2=R3, R4=R5, R6=R7 (동일 내용 2번 반복) → 좌/우 미러 또는 사용 빈도 가중치 추정
- R0/R1 → R2/R3 diff: 8개 byte 위치(offset 4, 8, 16, 20, 24, 28, 32, 36)에서 **정확히 -1씩 감소**
  → 캐릭터 상하 bobbing y-offset
- R8부터 첫바이트 `08 0a` → 다른 애니메이션 상태 시작 (공격/사망/idle 후보)
- "0a 02 0b" 마커가 1110 byte 간격으로 다시 등장 → 다른 방향/액션 그룹

**미해결**:
- 41 byte 중 38 byte 셀 데이터 정확한 인코딩 (4 byte × 11 = 44 mismatch, 3 byte 가변 가설 유력)
- 셀 = `[bm_idx, x_off, y_off, transform/flip]` 4-tuple 추정이지만 stride 미확정
- 4방향(UP/DOWN/LEFT/RIGHT) + 액션(IDLE/WALK/ATTACK/HURT/DEATH) 매핑 미확정
- 다른 cif 파일(boss/enemy)에서 같은 구조 적용 가능한지 검증 필요

**다음 세션 첫 작업** (1~2시간 예상):
1. 41 byte 안 셀 stride 확정 — diff 위치 패턴 + Frame R8 (다른 액션) 비교 분석
2. 1개 액션(걷기 down) 셀 구조 풀어 1방향 walk-cycle Android 구현
3. 4방향 매핑 (R0~R7 그룹이 어느 방향인지 sprite 시각 매칭)
4. 검증되면 boss0_cif / e000_cif 동일 포맷 적용

### A1) §4.2 자동 grep 시도 — **블로킹 상태로 결론** (참고용)
- `work/ghidra_out/all_decompiled.c` (76,876줄, 3,556 함수) 패턴 grep 으로 _mp 파서 함수 추적 시도
- 결과: PIC + GOT-relative offset 때문에 string xref 없음. `Event_freeID`/`loadDataID` 등 PROGRESS의 심볼명은 디컴파일 출력에 `FUN_xxxx` 형태로만 존재.
- `& 0xc0`, `>> 6` 같은 상위 비트 마스크 grep — 0건 매칭 (extras TLV 가설 검증 불가)
- map0 (NEOSOLTIA) extras 첫 24 byte = `c0 52 00 02 22 02 54 00 00 02 1e 02 6a 00 00 02 e8 01 40 00 80 36 68 00` (1266 byte 전체) 통계 분석은 `analyze_mp_extras.py` 가 이미 수행 — record size 4(60맵)/6(35맵) 분포, 첫 byte 0x80(67맵)/0xc0(11맵) dominant. **단순 fixed-size 가설 부적합 확정.**
- **결론**: §4.2 진행은 사용자가 Ghidra GUI 에서 인터랙티브 분석 필요 (§4.1 성공 패턴 동일). 자동화 grep 한계 도달.

### B) Android Kotlin 코드베이스 대규모 리팩토링 — **완료, 빌드/테스트 검증됨**

총 **6개 엔진 파일 + 17개 씬 파일** 정리. 기능 변경 0, 가독성·유지보수성 개선.

**Engine**:
- [Settings.kt](../../android/app/src/main/java/com/hero3/remake/engine/Settings.kt) — `isEn: Boolean` 프로퍼티 + `lang(ko, en): String` 헬퍼 추가 → **모든 씬이 공유**. 기존 60+회 `if (settings.language == "en") A else B` 패턴 통합.
- [GameState.kt](../../android/app/src/main/java/com/hero3/remake/engine/GameState.kt) (290→299줄) — `edit { ... }` 헬퍼로 17개 setter 단순화, `bossesDefeated` 프로퍼티 추가로 markEnemy/markBoss 패턴 일관화, `copyFrom` 을 INT/LONG/BOOL/STRING_SET/STRING 키 그룹 순회로 단순화 (새 필드 추가 시 그룹에만 등록하면 됨).
- [NpcRegistry.kt](../../android/app/src/main/java/com/hero3/remake/engine/NpcRegistry.kt) (391→418줄) — `postBoss×3 + dialoguesAfter×3 = 9 필드` → `List<PostBossDialogue>` 단일 필드. 라인 수는 늘었지만 구조 평행화로 새 보스 단계 추가 시 단순 `+ PostBossDialogue(...)` 로 끝남.

**Scenes** (BattleScene 710→680, MapWalkScene 620→628, 그 외 1~3줄 수준 정리):
- BattleScene: `renderPickList<T>` 제네릭화로 SkillPick/ItemPick 통합, `lang/pushEvent/menuTop/drawMenuFrame` 헬퍼 추출, 풀패스 25+회 제거
- MapWalkScene: 풀패스 12회 제거, ko/en 분기 8회 통합
- NpcDialogueScene: 3중 if-체인(`postBoss/postBoss2/postBoss3`) → 단일 `for (pb in n.postBoss.asReversed())` reverse-iterate
- InventoryScene, ShopScene, StatusScene, SettingsScene, TravelScene, EndingScene, TitleScene, BestiaryScene, RecordsScene, SkillScene, QuestScene, DialogueDemoScene, SaveSlotScene — `com.hero3.remake.engine.X` 풀패스 → import, `settings.lang/isEn` 사용

**검증**: `:app:testDebugUnitTest` (32 통과) + `:app:assembleDebug` 모두 BUILD SUCCESSFUL.

**SharedPreferences key 전부 동일** → 기존 세이브 슬롯 호환 유지.

**다음에 할 일 1순위**: 이 모든 변경 한 번에 커밋 (제안 메시지: `refactor: settings.lang/isEn 헬퍼 도입 + GameState edit 헬퍼 + NpcRegistry postBoss 리스트화 + 23 파일 정리`).

이후 우선순위는 §"다음 진행 후보" 참조. **§4.2 Ghidra 작업이 여전히 다음 큰 작업**이며, 이제 사용자의 Ghidra GUI 인터랙티브 분석이 필요한 상황이다.

## ⚡ 다음 세션 — 시작 전 5분 체크리스트

1. `git log --oneline -3` 로 최신 커밋 확인 (위 미커밋 작업분이 이미 커밋됐는지)
2. `git status --short` — 추가 미커밋 변경 있는지 파악
3. 이 문서 §"현재 상태 스냅샷" + §"다음 진행 후보" 읽기
4. **Android 빌드 검증** — JAVA_HOME 설정 후 wrapper 실행:
   ```powershell
   # PC 마다 JDK 경로 다름:
   #   현재 작업 PC (Microsoft Build of OpenJDK):
   $env:JAVA_HOME = 'C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot'
   #   집 PC (Adoptium Temurin):
   # $env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot'
   $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
   cd android
   .\gradlew.bat :app:assembleDebug         # APK
   .\gradlew.bat :app:testDebugUnitTest     # 32 단위 테스트
   ```
   (영구 등록하려면 시스템 환경변수에 JAVA_HOME 박아두기)
5. `work/h3/converted/`, `work/h3/converted_hd/`, `work/ghidra_out/` 등 산출물 비어있으면 §"재현 명령" 참조

---

## 📊 현재 상태 스냅샷 (2026-05-06 종료 시점)

### 자산 변환 현황

| 포맷 | 개수 | 상태 |
|---|---:|---|
| `_txt` | 9 | ✅ EUC-KR → JSON |
| `_pa` | 216 | ✅ RGBA8888 JSON |
| `_bm` (file) | 479 | ✅ 다중프레임 지원 |
| `_bm` (frame) | **3149** | ✅ type 0x0b + **0x0c (2026-05-06 해독)** |
| `_cif` | 103 | ✅ **2026-05-07 해독** — hero 9 캐릭터 walk-cycle 32 frame 베이크 (288 PNG) + dir_mapping.json / h1/h2/h3 portrait 74 PNG / boss·enemy 별도 인코딩 (전투 시스템 시점 처리) |
| `_mp` | 134/135 | ✅ terrain+collision / ✅ extras 97% (데코 마커 7,620개, NPC는 §4.4 의존) |
| `_scn` | 244 | ⚠️ 대사 추출 (26,415) / opcode 미해독 |
| `_dat` | 45 | ✅ EUC-KR 한글 추출 |
| `_mf` | 33 | 📋 표준 SMAF, 외부 도구로 변환 필요 |

HD 4× 업스케일: **3149 frame** (work/h3/converted_hd/), Android assets 동기화 완료.

### 빌드/테스트 — 검증 완료 (2026-05-06)

- `:app:assembleDebug` ✅ 1m10s 성공 → `app/build/outputs/apk/debug/app-debug.apk`
- `:app:testDebugUnitTest` ✅ **32/32 통과** (CharacterTest 7 / InventoryTest 6 / PartyTurnOrderTest 15 / SkillTest 4)
- 빌드 환경: JDK 21 (Adoptium 21.0.11.10) + Gradle 8.9 + AGP 8.7.2 + Kotlin 2.0.20 + compileSdk 35
- CI: `.github/workflows/android.yml` (push/PR에 자동 실행)

### Android 클라이언트 — 완성도 높은 1주차 게임

**플레이어 진행 루프** (전부 동작):
- 새 게임 → 솔티아 마을 → NPC 대화 → 촌장이 가디언 토벌 의뢰 (`guardian_hunt`)
- 외곽(map1) / 가디언 동굴(map10) 탐험 → 인카운터 / 보물상자 / 자연 회복
- 보스 1: `boss_guardian` (map10 8,4) → 처치 시 화이트 플래시 + Tier-2 잠금 해제 + `chaos_lord` 자동 활성
- 혼돈의 영역(map11) → 보스 2: `boss_chaos` (map11 6,6) → Tier-3 잠금 해제 + `sealed_god` 자동 활성
- 봉인의 사원(map12) → 최종 보스: `boss_sealed` (map12 10,6) → 처치 시 EndingScene 자동 진입 → 한·영 크레딧 → 타이틀 ★ CLEAR

**게임 시스템**:
- 캐릭터: 케이/리츠 각 5 클래스 (StatusScene L 키로 자유 변경)
- 12 스킬 (Lv 1/5/6/7/8 단계별 잠금 해제), heal/damage 모두 effective stats 반영
- 16 아이템 (Tier 1/2/3) — 무기/방어구/장신구/소비/재료/열쇠
- 적 13 (10 일반 + 3 보스), 드롭 테이블, 도감 (BestiaryScene)
- 8 보물상자, 빠른 이동(50G), 여관 10G/100G
- 퀘스트 4개, 자동 완료 + 후속 체인, EventBus 토스트
- 세이브 슬롯 3 + 활성 슬롯 0, 모든 진행 상태 영구 저장

**씬 (20 + Ending) 모두 정식 구현**:
- Title / MainMenu / MapWalk / NpcDialogue / SaveSlots / Status / Inventory(가방·장비·스킬 탭) / DialogueDemo / Settings / SpriteGallery / Map(heatmap) / Battle / Shop / Skill / Quest / Bestiary / Records / EventViewer / Travel / Ending
- 미니맵, 활성 퀘스트 라인, 보스 근접 경고, 출구 힌트
- Battle: 부유 / lunge / hit shake / 데미지 popup / 사망 페이드 / 보스 인트로(1.8s) / 처치 플래시(600ms)
- 토스트 시스템 (보스/레벨업/퀘스트/드롭/픽업/세이브)
- 튜토리얼 오버레이 (첫 진입 6s, Settings 에서 재생 가능)

**Settings**: 언어(ko/en) / 화질(SD/HD) / 인카운터 배수(0/0.5/1/2x) / 미니맵 ON/OFF / 튜토리얼 재생

**SfxBus** (사운드 stub, §4.5 후 즉시 활성):
- TitleScene → Bgm.TITLE / MapWalk → Bgm.FIELD / Battle → Bgm.BATTLE or Bgm.BOSS / Ending → Bgm.ENDING
- BattleScene HIT / LEVEL_UP / BOSS_INTRO / BOSS_DEFEAT, MapWalk CHEST 호출 wired up
- `SfxBus.debugToast = true` 면 EventBus 로 어떤 효과음이 트리거되는지 시각화

### 원본 자산 분석 (Ghidra 없이 가능한 한도)

**`_scn` (이벤트 스크립트, 244 파일 / 316KB, 52% 텍스트)**:
- 화자 태그 105 종 추출 (리츠 4890 / 케이 4599 / 일레느 3064 / ...)
- 25,818 대사 트리플 → 화자/모드/텍스트 구조화 JSON (244 파일 + summary)
- "다음 대사" opcode 식별: `0x00 [mode]`, mode ∈ {0x7c, 0x27, 0x24, 0x7b}
- 헤더 영역 분리: 첫 화자 태그 이전이 0~1930 byte 이벤트 메타 (트리거/플래그) — Ghidra 진입점 우선순위
- inter-speaker 영역은 단순 마커, 분기 opcode 부재

**`_cif` (애니메이션, 103 파일)**:
- 헤더 재해석: `uint8 slot_count + uint8 category` (기존 uint16 가정 폐기)
- category 0 = hero/boss (8슬롯), category 1 = enemy (0~7)
- `19 19` 마커 = frame size (76% 파일)
- `tools/converter/convert_cif.py` 헤더 패치 완료. 9-byte record 가설 약함 → 가변 record 추정

**`_mp` extras (134 맵)**:
- best record_size 4(60맵)/6(35맵)/12(10맵) 분산 → 단일 fixed-size 가설 부적합
- 첫 byte 0x80(67맵)/0xc0(11맵) dominant → flag/type
- **결정적 디코드는 Ghidra 필요** (현재 MapGraph 수동 정의로 우회)

---

## 🎯 다음 진행 후보 (우선순위순)

### 0) **이번 세션 변경분 커밋** [즉시] ⭐
- 미커밋 변경: 23개 Kotlin 파일 리팩토링 + docs/h3/PROGRESS.md
- 제안 메시지: `refactor: settings.lang/isEn 헬퍼 도입 + GameState edit 헬퍼 + NpcRegistry postBoss 리스트화 + 23 파일 정리`
- 변경 파일 목록은 `git status --short` 로 확인. 모두 동작 보존(테스트 32/32, 빌드 OK).
- 추가로 이전 세션의 `tools/h5_bin_probe.py` 미커밋 1건이 남아 있을 수 있음 — 이번 H3 리팩토링 커밋과는 분리해 별도 커밋 권장.

### A) **Ghidra §4.2~4.4 분석** [환경 다 갖춰짐, §4.1로 패턴 매칭 방식 검증됨, 자동화 grep 으로는 §4.2 한계 도달]

> **2026-05-07 시도 결과**: §4.2 _mp extras 의 자동 grep 식별은 실패. PIC + GOT-relative offset 으로 string xref 추적 불가, `& 0xc0`/`>> 6` 같은 마스크 패턴도 디컴파일 출력에 0건 매칭. **사용자가 Ghidra GUI 에서 인터랙티브 분석 필요** (§4.1 성공 흐름과 동일). 메인 Claude 는 함수 후보 패턴 제시 + 디컴파일 결과 분석을 보조한다.

#### Ghidra 환경 (이미 셋업 완료)
- JDK 21 (Adoptium 21.0.11) / Ghidra 12.0.4 / `work/ghidra_proj/Hero3.gpr`
- 자동 분석 + GOT base(`0xb2c40`) 적용 → **3556 함수** 식별, 전부 디컴파일된 결과: `work/ghidra_out/all_decompiled.c` (16MB)
- 진입 가이드: [`docs/h3/ghidra-gui-guide.md`](ghidra-gui-guide.md)

#### §4.1 해독 과정에서 배운 것 (§4.2~4.4에 그대로 적용)
1. **PIC + GOT indirection으로 string xref 자동 추적은 0건** (literal pool 검색도 0건). 문자열 주소가 absolute가 아니라 GOT-relative offset로 저장됨.
2. **우회 = 함수 패턴 grep**. `all_decompiled.c`를 grep으로 훑어서 진입점 단서 함수들의 시그너처(예: 0x0c → `cVar2 == '\f'`)로 진짜 함수 식별.
3. **PROGRESS의 가설은 검증 전 추정**일 수 있음 (§4.1 "sparse encoding" 가설이 오답이었듯). 디컴파일 코드 직접 확인이 진실.

#### 남은 3가지 진입점 (우선순위순)

1. **§4.2 `_mp` extras** ⭐ 효과 가장 큼 (134맵 자동화)
   - 단서: `Event_freeID`(@0xaac7c), `loadDataID`(@0xa6efc) 함수 또는 디버그 문자열 부근
   - 풀면: NpcRegistry / MapGraph / EncounterTable / ChestRegistry 모두 자동 생성. 현재 솔티아 외 5맵만 수동 정의된 것을 134개 전체 자동화.
2. **§4.3 `_cif` animation timing** — 시각 임팩트
   - 단서: `Hero_Free`(@0xa6e8c), `freeBossType`(@0xa6e70) 부근
   - 풀면: 진짜 4방향 걷기/공격/사망/피격 애니메이션 (현재 정적 frame 매핑)
3. **§4.4 `_scn` opcode** — 게임 흐름 깊이
   - 단서: `onEventMessageOkKey`(@0xa6888), `eventManager`(@0xa6ad8) 부근 switch/dispatch
   - 풀면: 분기/플래그 set/사운드 트리거/컷씬 명령 모두 실행 (현재 대사만 표시)

### B) **사운드 (SMAF→OGG)** [블로커: 외부 도구]
- §4.5 — SMAF 디코더 (`smaf2midi` 또는 KSS/Yamaha SMAF SDK) 또는 33개 수동 변환
- 변환 후 `engine/SfxBus.kt` 의 `play()` / `playMusic()` 만 구현하면 즉시 활성. 호출처는 이미 wired up

### C) **대사 번역 실행** [블로커: API 키 + 사용자 결정]
- 비용: ~$0.66 (Claude Haiku 4.5, 9,741 unique). 한 번만 실행
- 사용자가 "번역은 마지막"이라고 했으므로 게임 콘텐츠가 마무리된 시점에 진행
- 명령 (in §"재현 명령")
- 결과: `dialogue_translations_en.json` 자동 배포, NpcDialogueScene 가 settings.language == "en" 일 때 자동 사용

### D) **게임 콘텐츠 확장** [블로커 없음, 작업량만]
- 추가 보스 / 맵 / NPC / 퀘스트
- 추가 스킬·아이템·세트 효과
- ~~멀티 캐릭터 액티브 파티~~ ✅ 완료 (BattleScene 라운드 기반 멀티 파티)
- ~~세이브 자동 (currently 슬롯 0 만 자동, 슬롯 1~3 수동)~~ ✅ 보스 처치 시 활성 슬롯 flush + 마지막 사용 수동 슬롯(`lastSavedSlot`) 자동 미러링
- 일본어/중국어 (translate_dialogues.py system prompt 교체)

### E) **빌드/테스트 환경** [전부 완료]
- ~~gradle wrapper 추가~~ ✅ Gradle 8.9 wrapper
- ~~단위 테스트~~ ✅ 32 통과 (Character 7 / Inventory 6 / Skill 4 / PartyTurnOrder 15)
- ~~AGP 업그레이드~~ ✅ 8.5.2 → 8.7.2 + Kotlin 2.0.20 (compileSdk 35 경고 해소)
- ~~컴파일 경고 정리~~ ✅ 0건
- ~~CI 셋업~~ ✅ [.github/workflows/android.yml](../.github/workflows/android.yml) — push/PR에 testDebugUnitTest + assembleDebug 자동 실행. [.github/workflows/python-tools.yml](../.github/workflows/python-tools.yml) (2026-05-09) — Python 변환기/i18n 89 test 자동 실행 (Hero3 JAR 추출 포함, Pillow/capstone 자동 설치).
- ~~코드 리팩토링 1차~~ ✅ 2026-05-07 — Settings.lang/isEn 도입, GameState edit 헬퍼, NpcRegistry postBoss 리스트화, 23 파일 풀패스/ko·en 분기 정리. 동작 100% 보존.
- 남은 후순위:
  - `_scn` 분석 결과 회귀 테스트 (Ghidra opcode 해독 후)
  - 추가 리팩토링 후보: `MainActivity.kt` (215줄, SceneRequest 라우팅) / `Quest.kt` (146줄) / `EncounterTable.kt` / `MapGraph.kt` 등 데이터 테이블류

### F) **추가 리팩토링** [선택, 블로커 없음]

이번 라운드(2026-05-07)는 **씬+엔진의 풀패스/i18n 헬퍼 통합**에 집중했고, 큰 결함은 더 없음. 미해결 리팩토링 후보:
- **MainActivity.kt** (215줄) — `SceneRequest` sealed class + when 분기. Scene 팩토리 패턴으로 추출 가능.
- **데이터 등록기** (`ChestRegistry`, `EncounterTable`, `MapGraph`, `ShopRegistry`) — 현재 하드코딩. §4.2 _mp extras 해독 후 자동 생성 전환 예정 → 지금 손대지 말 것.
- **세이브 JSON 직렬화** (GameState.loadParty/saveParty/loadInventory/saveInventory) — kotlinx.serialization 도입 가능하나 의존성 추가 필요. ROI 낮음.

---

## 📁 코드 구조 — 어디에 뭐가 있나

### Android 클라이언트 (`android/app/src/main/`)

```
java/com/hero3/remake/
├── MainActivity.kt              # SceneRequest 라우팅 + GameState/Settings 주입
├── engine/                      # 핵심 시스템 (data + logic)
│   ├── Character.kt             # CharacterRegistry, Stats, effectiveAttack/Defense/Intl
│   ├── Item.kt                  # ItemRegistry, Inventory(MAX_SLOTS=20)
│   ├── Skill.kt                 # SkillRegistry (Lv 게이트, 12 스킬)
│   ├── Enemy.kt                 # EnemyRegistry (10 일반 + 3 보스, dropTable)
│   ├── Quest.kt                 # QuestRegistry, QuestLog (자동 완료 + followUp 체인)
│   ├── ChestRegistry.kt         # 8 상자 정적 정의
│   ├── ShopRegistry.kt          # NPC별 재고 (gameState 따라 잠금 해제)
│   ├── EncounterTable.kt        # 맵별 인카운터 확률 + 적 풀
│   ├── MapGraph.kt              # 맵 간 연결 (E/W/N/S edges 수동 정의)
│   ├── NpcRegistry.kt           # 13 NPC + patrolPath + postBoss 분기 + action(heal)
│   ├── GameState.kt             # 슬롯별 SharedPreferences (party/inventory/quests/etc)
│   ├── Settings.kt              # 언어/화질/인카운터/미니맵
│   ├── EventBus.kt              # 단순 toast 큐
│   ├── SfxBus.kt                # 사운드 stub
│   ├── GameView.kt              # SurfaceView 60fps + 키 매핑
│   ├── InputController.kt       # 비트마스크 입력
│   ├── VirtualKeypadView.kt     # 가상 키패드 오버레이
│   ├── Scene.kt                 # 추상 (consumesPoundKey 플래그)
│   ├── Strings.kt               # i18n 헬퍼
│   └── UiKit.kt                 # 공용 그리기 (drawBox/drawHeader/drawHints)
└── scene/                       # 20개 씬
    ├── TitleScene / MainMenuScene / MapWalkScene / NpcDialogueScene
    ├── SaveSlotScene / StatusScene / InventoryScene / SkillScene / QuestScene
    ├── BattleScene / ShopScene / BestiaryScene / RecordsScene
    ├── TravelScene / EventViewerScene / EndingScene
    ├── SettingsScene / DialogueDemoScene / SpriteGalleryScene / MapScene

assets/
├── sprites/         3,131 frame PNG (1×, SD)
├── sprites_hd/      4× scale4x HD
├── maps/            134 _mp.json
├── cif/             103 _cif.json (헤더 패치 적용 — 재변환 필요)
├── strings/ palettes/
├── dat/char_dat.json
├── scn_v2/          245 화자별 대사 JSON (244 + summary)
├── dialogue_corpus.json + dialogue_top_texts.json + asset_catalog.json
└── (dialogue_translations_en.json 은 §A 실행 후 생성)

res/values{,-ko}/strings.xml
```

### 분석 도구 (`tools/`)

```
recon/                # 정찰
├── extract_strings.py / disasm_thumb.py / find_pic_xrefs.py / find_f81f.py / find_base.py
├── analyze_mp_extras.py        # _mp extras 통계
├── analyze_cif.py              # _cif 헤더/body 통계
├── analyze_scn_opcodes.py      # _scn byte freq
├── extract_scn_speakers.py     # _scn 화자 태그 추출
├── dump_scn_structure.py       # 단일 _scn 구조 덤프
├── scn_dialogue_opcode.py      # [speaker] 직전 byte → 대사 시작 opcode
├── scn_inter_speaker.py        # 대사 ~ 다음 화자 사이 byte
└── scn_header.py               # 첫 화자 이전 영역 (이벤트 메타)

converter/            # 자산 변환
├── convert_all.py / convert_text.py / convert_palette.py
├── convert_bm_v2.py / convert_cif.py / convert_mp.py / convert_scn.py / convert_dat.py
├── convert_scn_v2.py           # 화자별 대사 트리플 추출 (NEW)
├── build_dialogue_corpus.py
└── prepare_android_assets.py   # scn_v2/, dat/char_dat 자동 복사 추가

i18n/                 # 번역 인프라
├── translation_dict.py
├── generate_string_resources.py
├── build_asset_catalog.py
└── translate_dialogues.py      # Claude Haiku 4.5 (§A 실행)

hd/
├── upscale_poc.py / batch_upscale.py
```

### 분석 산출물 (`work/`)
- `extras_summary.json` — _mp extras 통계
- `cif_anim_summary.json` — _cif 통계
- `scn_opcode_freq.json` — _scn byte freq
- `scn_speakers.json` — 105 화자 + 샘플
- `scn_dialogue_opcode.json` — 대사 시작 opcode
- `scn_inter_summary.json` — 대사 사이 byte
- `scn_header_summary.json` — 헤더 영역
- `converted/scn_v2/` — 244 + summary

---

## 🔧 재현 명령

### 자산 재변환 (필요 시)
```bash
# 경로: work/h3/extracted (입력) / work/h3/converted (출력) / work/h3/converted_hd (HD 출력)
cd tools/converter
PYTHONIOENCODING=utf-8 python convert_all.py ../../work/h3/extracted ../../work/h3/converted
PYTHONIOENCODING=utf-8 python convert_scn_v2.py ../../work/h3/extracted/event ../../work/h3/converted/scn_v2
PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/h3/converted ../../android/app/src/main/assets

cd ../hd
HERO_GAME=h3 PYTHONIOENCODING=utf-8 python batch_upscale.py    # work/h3/converted_hd 생성 (3분)
# HD assets 동기화 (prepare_android_assets는 SD만 복사함)
python -c "import shutil, pathlib; src=pathlib.Path('../../work/h3/converted_hd'); dst=pathlib.Path('../../android/app/src/main/assets/sprites_hd'); shutil.rmtree(dst, ignore_errors=True); n=0
for png in src.rglob('*.png'):
    o = dst / png.relative_to(src); o.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(png, o); n+=1
print(f'{n} HD sprites copied')"

cd ../i18n
PYTHONIOENCODING=utf-8 python generate_string_resources.py
PYTHONIOENCODING=utf-8 python build_asset_catalog.py
```

### Ghidra 분석 산출물 재생성 (§4.2~4.4 진행 시)
```
1. ghidraRun.bat 실행 → Hero3.gpr 프로젝트 → client.bin64000 더블클릭
2. Window → Script Manager → tools/ghidra/ 디렉토리 등록 (이미 등록됐으면 스킵)
3. SetGotBase.java 실행 (r10 = 0xb2c40 적용 후 재분석, 5~20분 대기)
4. DecompileAll.java 실행 → c:/gameRemake/testrepo/work/ghidra_out/all_decompiled.c (5~15분)
5. 그 후 Claude에 "ghidra_out/all_decompiled.c 끝났어" 알리면 패턴 grep 진행
```

### `_scn` / `_cif` / `_mp` 통계 재실행
```bash
cd tools/recon
PYTHONIOENCODING=utf-8 python analyze_mp_extras.py
PYTHONIOENCODING=utf-8 python analyze_cif.py
PYTHONIOENCODING=utf-8 python analyze_scn_opcodes.py
PYTHONIOENCODING=utf-8 python extract_scn_speakers.py
PYTHONIOENCODING=utf-8 python scn_dialogue_opcode.py
PYTHONIOENCODING=utf-8 python scn_inter_speaker.py
PYTHONIOENCODING=utf-8 python scn_header.py
```

### 대사 번역 (§A — API 키 필요)
```bash
cd tools/i18n
export ANTHROPIC_API_KEY=...
PYTHONIOENCODING=utf-8 python translate_dialogues.py --limit 100   # 검증
PYTHONIOENCODING=utf-8 python translate_dialogues.py               # 전체
cd ../converter
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
```

### Android 빌드 (PowerShell)
```powershell
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
cd android
.\gradlew.bat :app:assembleDebug         # APK → app/build/outputs/apk/debug/app-debug.apk
.\gradlew.bat :app:testDebugUnitTest     # 단위 테스트 (32 통과)
```
또는 Android Studio 에서 `android/` 디렉토리 열기.

**환경 영구 설정 권장**: 시스템 환경변수에 `JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot` 등록.

⚠️ `android/local.properties`는 gitignore돼있어 첫 빌드 시 자동 생성 안 됨. 다른 PC에서 클론하면 SDK 경로 수동 입력 필요:
```
sdk.dir=C:\\path\\to\\Android\\Sdk
```

---

## ⚠️ 알려진 이슈 / TODO

| ID | 이슈 | 워크어라운드 / 액션 |
|---|---|---|
| #1 | `map134_mp` 비표준 헤더 (NUL 부재) | 변환 시 1개 에러 보고됨, 무시 가능 |
| #2 | ~~type 0x0c BM 프레임이 노이즈로 렌더~~ | ✅ 2026-05-06 해독 완료. 8-bit indexed dense, byte 0 = 투명. `convert_bm_v2.py` 패치 후 91개 정상 |
| #3 | 일부 0x0b/0x0c BM 2 byte underrun | 시각 영향 미미 (마지막 픽셀 행 일부 누락). 0x0c도 동일 패턴 (theme_0 -2 byte) |
| #4 | hero/boss CIF 인덱스가 BM 파일명과 매칭 안됨 | enemy/map은 직접 매칭 정상. §4.3 해독 후 자동 매핑 가능 |
| #5 | `Hero3OptionSave` (32B) XOR 암호화 | 호환 불필요라 무시 |
| #6 | ~~`_cif` 새 헤더 적용 후 재변환 미실행~~ | ✅ 2026-05-06 자산 재변환 시 같이 재생성됨 |
| #7 | ~~gradle wrapper 부재~~ | ✅ 2026-05-04 wrapper.jar/gradlew/gradlew.bat 추가 (Gradle 8.9) |
| #8 | ~~멀티 캐릭터 파티는 데이터만 있고 전투 참여 X~~ | ✅ 2026-05-04 BattleScene 멀티 파티 지원. 살아있는 멤버 전원 라운드 행동, 적은 랜덤 타겟, 힐은 HP 최저 아군 자동 |
| #9 | NPC patrol 이 hero 충돌 무시 | 시각적 겹침만 발생, 게임 로직 영향 없음 |
| #10 | 사운드 미구현 | SfxBus stub 만 wired up. §B (SMAF→OGG) 후 활성 |
| #11 | `local.properties` gitignored (의도) | 클론한 PC마다 sdk.dir 수동 입력 필요. 본 PC(`C:\Users\viewe\AppData\Local\Android\Sdk`)는 등록됨 |
| #12 | JAVA_HOME 시스템 환경변수 미설정 | 빌드할 때마다 PowerShell에서 `$env:JAVA_HOME=...` 필요. 영구 등록 권장. **PC별 경로 다름**: 현재 PC = `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot`, 집 PC = `C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot` |

## 📜 2026-05-07 세션 작업 압축 (§4.2 시도 실패 + 코드 리팩토링)

**목표**: §4.2 _mp extras 해독 → 실패 후 Android Kotlin 코드 정리로 전환.

**진행 단계**:
1. **§4.2 자동화 시도 → 블로킹 확인**:
   - `all_decompiled.c` (76,876줄) 패턴 grep — `Event_freeID`/`loadDataID` 심볼명 0건 (PIC 디컴파일에 없음).
   - `& 0xc0`/`>> 6` 마스크 grep — 0건 매칭.
   - Explore 에이전트가 후보로 제시한 `FUN_00010fe4` 는 §4.1 의 비트맵 디코더 (false positive).
   - 결론: 사용자의 Ghidra GUI 인터랙티브 분석 필요. 메인 Claude 자동화 한계.

2. **JDK 경로 확인**: 현재 PC 의 JDK 21 위치가 PROGRESS 의 Adoptium 경로와 다름 — `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (Microsoft Build of OpenJDK). 집 PC 는 Adoptium Temurin. Claude 메모리(`reference_jdk_paths.md`)에 양쪽 PC 경로 기록함.

3. **코드 리팩토링 1차**:
   - **Settings.kt** 에 `isEn`/`lang(ko, en)` 추가 → 모든 씬이 공유.
   - **GameState.kt**: `edit { ... }` 헬퍼, `bossesDefeated` 프로퍼티, `copyFrom` 키 그룹화.
   - **NpcRegistry.kt**: `postBoss×3 + dialoguesAfter×3 = 9 필드` → `List<PostBossDialogue>`.
   - **NpcDialogueScene**: 3중 if-체인 → 단일 `for (pb in n.postBoss.asReversed())`.
   - **BattleScene** 710→680: `renderPickList<T>` 제네릭, `lang/pushEvent/menuTop/drawMenuFrame` 헬퍼 추출.
   - **MapWalkScene** 620→628: 풀패스 12회 + ko/en 분기 8회 정리.
   - **나머지 13 씬** (Inventory/Shop/Status/Settings/Travel/Ending/Title/Bestiary/Records/Skill/Quest/DialogueDemo/SaveSlot): 풀패스 import 정리, `settings.lang/isEn` 사용.
   - **검증**: `:app:testDebugUnitTest` (32 통과) + `:app:assembleDebug` 두 번 BUILD SUCCESSFUL.

**핵심 교훈**:
1. PIC 디컴파일은 자동 패턴 grep 만으로 함수 식별 한계. §4.1 성공도 사용자의 GUI 인터랙티브 분석이 핵심이었음.
2. 16개 씬에 동일 패턴(ko/en 분기) 반복 → **공통 라이브러리(Settings)** 에 한 번만 추가하는 것이 파일별 헬퍼 중복보다 더 큰 임팩트.
3. 데이터 클래스의 `field, field2, field3` 같은 평행 시리즈는 거의 항상 `List<DataClass>` 로 압축 가능 (NpcRegistry.postBoss 케이스).

---

## 📜 2026-05-06 세션 작업 압축 (Ghidra §4.1 해독)

**목표**: 사용자 PC에서 Ghidra GUI 분석으로 §4.1 type 0x0c 비트맵 디코더 해독. 자동화 한계 도달한 상태에서 사람의 인터랙티브 분석 필요.

**진행 단계**:
1. **JDK 21 + Ghidra 12.0.4 + Android SDK 환경 셋업** (사용자 PC에 처음으로) → `Hero3.gpr` 프로젝트 생성, ARM:LE:32:v5t로 변환 (Cortex-M 첫 시도 실패 후), 자동 분석으로 3556 함수 식별
2. **GOT base 0xb2c40 적용** (`tools/ghidra/SetGotBase.java`) → r10 컨텍스트 + 재분석
3. **string xref 시도 → 실패** (`frameBuf is NULL` @ 0xa61c8 references = 0). PIC + GOT-relative offset 때문에 자동 추적 불가.
4. **literal pool 검색 시도 → 0건** (`tools/ghidra/FindEntryPoints.java` 결과 모든 needle에서 `literal-pool refs : 0`). 문자열 주소가 절대값이 아닌 GOT 오프셋.
5. **DecompileAll.java 실행 → 함수 패턴 grep**으로 우회. 16MB `all_decompiled.c` 생성.
6. **`& 0x3f` (RGB565 그린 채널 마스크) 8건 grep** → `FUN_00010fe4 @ 0x10fe4` 식별. `cVar2 == '\v'` (0x0b) / `cVar2 == '\f'` (0x0c) 분기 발견.
7. **0x0c 분기 (라인 4834~5060) 분석**:
   - 8가지 transformation (param_13 0~7)
   - 핵심 루프: `if (*pbVar1 != 0) *puVar10 = palette[*pbVar1]` → 1 byte/pixel, byte 0 = 투명
   - **이전 "sparse encoding" 가설 오답 확정**

**해독 후 작업**:
- `convert_bm_v2.py` `decode_0c` 교체 + 가변 팔레트 처리 (`ch` 필드 = palette count, 1~256)
- 검증: theme_0/obj_0/h00000 변환 → obj_0/frame_02 = 나무 스프라이트 정상 렌더 ✓
- 전체 자산 재변환: 479 파일 → 3149 frame (+18) → HD 4× 업스케일 → Android sprites/+sprites_hd/ 갱신
- 빌드 검증: `:app:assembleDebug` 1m10s 성공, 단위테스트 32/32 통과
- 빌드 환경 정리: `android/local.properties` 생성 (gitignored)

**핵심 교훈**:
1. PIC 코드는 string xref 자동화 안 됨 → 패턴 grep 우회가 효율적
2. PROGRESS의 가설(sparse encoding) ≠ 진실(8-bit dense indexed). 추정과 디컴파일 코드 검증 항상 분리.
3. `ch` 필드는 cell height 아니라 palette count. 다른 BM 포맷 docs도 검증 필요할 수 있음.

---

## 📜 2026-05-04 세션 작업 압축

(상세 마일스톤 38건은 git log `af5574a` 및 그 후속 커밋 참조. 위 §"현재 상태 스냅샷" 이 최종 결과. 아래는 단일 라이너 인덱스)

- 콘텐츠: 3 보스 + Tier 1/2/3 + 퀘스트 체인 + EndingScene + ★ CLEAR 배지 + 회차 보존
- 시스템: 장비/effective stats + 레벨업 + 자연 회복 + 패배 부활 + 여관/신관 + 보물상자 + 빠른 이동 + 직업 변경
- 씬 신규: Battle/Shop/Skill/Quest/Bestiary/Records/EventViewer/Travel/Ending
- UX: 미니맵 + 활성 퀘스트 + 보스 근접/출구 힌트 + 토스트 + 튜토리얼 + 데미지 popup + 부유/lunge/shake/fade/플래시
- 분석 도구 8개 + 보고서 7개 (`work/scn_*.json`, `work/cif_*.json`, `work/extras_summary.json`)
- 자산 통합: scn_v2/ 245 JSON, dat/char_dat.json, _cif 헤더 패치
- 버그 수정: 슬롯 copyFrom 누락 필드, ShopScene early-return, 새 게임 진짜 초기화, 클리어 플래그 보존
- 사운드 stub: SfxBus + 모든 호출처 wired up
- 폴리시: HP/SP/EXP 바, 메뉴 스크롤, 슬롯 카운트, NPC 퀘스트 마커, 영웅 방향 sprite, 액세서리 효과


**이전 마일스톤** (2026-05-01, NPC + 세이브슬롯 완료):
- **11개 Android 씬** (Title/MainMenu/MapWalk/NpcDialogue/SaveSlots/Status/Inventory/DialogueDemo/Settings/SpriteGallery/Map)
- **NPC 시스템** — `NpcRegistry` + map0 에 4 NPC 하드코딩 (촌장/상인/경비병/아이) + 인접 OK 키 → `NpcDialogueScene`
- **세이브 슬롯** — 3슬롯 SAVE/LOAD UI, 슬롯별 별도 SharedPreferences
- **MapWalkScene 충돌 확장** — Layer 1 + NPC 칸 통행 불가 + 인접 NPC 힌트 표시
- `MapWalkScene` 영웅 맵 위 이동 + 충돌 + 카메라 스크롤
- `GameState` slotId 기반 영구 저장 (현재 맵, 영웅 좌표, 방향)
- UI 어휘 196개 100% 영어 번역 + 메뉴 어휘
- `translate_dialogues.py` Claude Haiku 4.5 기반 대사 번역 스크립트
- `DialogueDemoScene` / `NpcDialogueScene` 영어 토글 시 번역 사용
- HD 자산 (3,131 sprite scale4x 4×) + 자산 카탈로그 + 대사 코퍼스 (26,415 lines, 9,741 unique)
- **dat/ 파일 추가 변환** — char_dat 분석으로 캐릭터 클래스 구조 확인 (리츠/케이 각 5 클래스)

_(상세 다음 단계는 본 문서 상단 §"다음 진행 후보" 참조)_

---

## 1. 프로젝트 개요

| 항목 | 값 |
|---|---|
| 원본 게임 | 영웅서기3 - 운명의수레바퀴 (한빛소프트, 2008, SK텔레콤 GVM/Clet) |
| 원본 위치 | `Hero3/0103EFD4.jar` + `Hero3/__adf__` + `Hero3/P/` (세이브) |
| 원본 바이너리 | `client.bin64000` (735KB ARM Thumb 네이티브, GCC `-fpic`, GOT base = `r10`) |
| 자산 총량 | 1,272개 파일 (9개 포맷) |
| 전략 | **Strategy C** — 자산 재활용 + Kotlin/Android 엔진 재구현 |
| 결정사항 | HD 리마스터 진행 / 다국어 지원 / 세이브 호환 X |

## 2. 완료된 작업 (2026-05-01 기준)

### 2.1 자산 포맷 분석 + 변환

| 포맷 | 개수 | 상태 | 변환 결과물 |
|---|---:|---|---|
| `_txt` (텍스트 테이블) | 9 | ✅ 완전 | EUC-KR → JSON |
| `_pa` (팔레트) | 216 | ✅ 완전 | RGBA8888 JSON |
| `_bm` (비트맵, type 0x0b) | 479 | ✅ 완전 | **3,131 frame PNG** |
| `_bm` (type 0x0c sparse) | (포함) | ⚠️ 부분 | bit layout 미확정 |
| `_cif` (애니메이션) | 103 | ⚠️ 부분 | slot count + indices만 추출 |
| `_mp` (맵) | 134/135 | ✅ 헤더+레이어 | terrain + collision JSON |
| `_mp` extras | – | ⚠️ 부분 | NPC/exit 추정 |
| `_mf` (사운드 SMAF) | 33 | 📋 표준 | 빌드 타임 OGG 변환 도구 필요 |
| `_scn` (이벤트 스크립트) | 244 | ⚠️ 부분 | **26,415 대사 (9,741 unique)** |

### 2.2 HD 리마스터

- ✅ scale4x 알고리즘 검증 — pixel-art 보존 + 대각선 매끄럽게
- ✅ 3,131개 sprite frame 4× 업스케일 완료
- ✅ Android `assets/sprites_hd/` 배포

### 2.3 Android 클라이언트

- ✅ Gradle 8.7 / AGP 8.5.2 / compileSdk 35 / minSdk 24
- ✅ 240×320 가상 캔버스 + letterbox 스케일 (`GameView` SurfaceView 60fps)
- ✅ MIDP 호환 입력 매핑 (`InputController` 비트마스크)
- ✅ 가상 키패드 오버레이 (D-pad + OK + L/R + #)
- ✅ Scene 추상화 + 씬 스택 (push/pop 지원)
- ✅ `Settings` 영구 저장 (SharedPreferences) — 언어 / HD 토글
- ✅ `GameState` 영구 저장 — 현재 맵 ID, 영웅 좌표, 바라보는 방향, 파티 리더
- ✅ `Strings` i18n 헬퍼 — 196개 InGame_txt 모두 string resource 화 (txt_000~txt_195)
- ✅ `UiKit` 공용 그리기 헬퍼 (박스, 메뉴아이템, 다이얼로그 박스, 헤더, 힌트)
- ✅ **씬 11개 구현**:
  - `TitleScene` — 로고 + 메뉴 (새 게임 → MapWalk / 이어하기 → SaveSlots / 설정 / 갤러리)
  - `MainMenuScene` — 7개 원본 메뉴 (상태/가방/장비/스킬/퀘스트/세이브/시스템) + 디버그
  - **`MapWalkScene`** — 영웅 이동 + Layer 1 충돌 + NPC 칸 통행 불가 + 카메라 스크롤 + 걷기 애니 + 인접 NPC 힌트
  - **`NpcDialogueScene`** — 단일 NPC 대화 (포트레이트 + 한·영 토글 + 글자 흘려쓰기)
  - **`SaveSlotScene`** — 3슬롯 SAVE/LOAD UI + 슬롯별 별도 SharedPreferences
  - `StatusScene` — 캐릭터 스탯 mockup (이름/직업/LV/HP/SP + 12개 스탯)
  - `InventoryScene` — 가방/장비/스킬 탭 + 5×4 슬롯 그리드 mockup
  - `DialogueDemoScene` — 코퍼스에서 대사 글자 흘려쓰기 + 화자/이벤트 변경 + 영어 번역 토글
  - `SettingsScene` — 언어/품질 토글 (Activity 재생성으로 locale 적용)
  - `SpriteGalleryScene` — 3,131 sprite 5fps 애니메이션, Settings 연동(SD/HD 자동 선택)
  - `MapScene` — 134 맵 색상 heatmap 브라우저 (디버그용)
- ✅ **NpcRegistry** — map0 에 4 NPC 하드코딩 (촌장/상인/경비병/아이) + 한·영 대사 + 4방향 인접 검사
- ✅ 자산 번들: sprites + sprites_hd + maps + cif + strings + palettes + dialogue_corpus + dialogue_translations_en + asset_catalog

### 2.4 클라이언트 바이너리 분석

- ✅ ASCII 문자열 추출 — 9,120개 (파일 경로, 함수명, 디버그 메시지 등)
- ✅ PIC 패턴 식별 (LDR + ADD sl + LDR 3-level indirection via GOT base)
- ✅ Capstone Thumb 디스어셈블 가능 환경 구축
- ⚠️ 함수 단위 분석은 한정적 (GOT-기반 PIC가 직접 string xref 추적을 어렵게 함)

### 2.5 i18n / 번역 인프라

- ✅ `tools/i18n/translation_dict.py` — 한↔영 번역 사전 (캐릭터·지명·UI 어휘)
- ✅ `tools/i18n/generate_string_resources.py` — `values/strings.xml` (영어) + `values-ko/strings.xml` (한국어) 자동 생성
- ✅ **InGame_txt 196개 100% 영어 번역 커버리지** (txt_000~txt_195)
- ✅ 캐릭터 사전: 케이/Kei, 리츠/Ritz, 일레느/Ilene, 시엔/Sien, 레아/Lea, 엘지스/Elgis, 케네스/Kenneth, 이안/Ian, 멜페토/Melpheto, 토레즈/Torez 등
- ✅ 지명 사전: 솔티아/Soltia, NEOSOLTIA/Neo Soltia, GUARDIAN_CAVE 1~7, RUINED_DESERT 1~3, GULBEIG_RUIN 5~7 등 30+ 곳
- ✅ 접두 마법 효과: @투신의/of War God, @공명의/of Resonance 등 15종
- ✅ `tools/i18n/build_asset_catalog.py` — 변환 자산 인덱스 (`asset_catalog.json`)
  - 카테고리별 sprite 디렉토리 + frame count + first dimension
  - 134 맵 (한·영 이름 매핑 포함)
- ✅ Android Activity locale override (Configuration#setLocale + recreate)

### 2.6 인프라

- ✅ 메모리 시스템 (`MEMORY.md` + `project_hero3_remake.md`)
- ✅ 변환 파이프라인 (`tools/converter/convert_all.py` 단일 진입점)
- ✅ HD 파이프라인 (`tools/hd/`)
- ✅ i18n 파이프라인 (`tools/i18n/`)
- ✅ 정찰 도구 (`tools/recon/`)
- ✅ 작업 디렉토리 (`work/`) gitignore

## 3. 디렉토리 구조

```
testrepo/
├── Hero3/                         # 원본 (수정 금지)
│   ├── 0103EFD4.jar               # 원본 JAR
│   ├── __adf__                    # GVM 메타
│   └── P/Hero3{Game,Option,Slot}Save  # 세이브 (호환 X)
├── docs/
│   ├── asset-formats.md           # 자산 포맷 사양
│   └── PROGRESS.md                # ← 이 파일 (핸드오프)
├── tools/
│   ├── converter/                 # 자산 변환기 (Python)
│   │   ├── convert_all.py         # 통합 진입점
│   │   ├── convert_text.py / convert_palette.py
│   │   ├── convert_bm_v2.py       # 멀티프레임 BM 디코더
│   │   ├── convert_cif.py / convert_mp.py / convert_scn.py / convert_dat.py
│   │   ├── build_dialogue_corpus.py
│   │   └── prepare_android_assets.py
│   ├── i18n/                      # i18n + 자산 카탈로그
│   │   ├── translation_dict.py    # 한↔영 사전 (캐릭터/지명/UI/접두효과)
│   │   ├── generate_string_resources.py  # values{,-ko}/strings.xml 생성
│   │   ├── build_asset_catalog.py # asset_catalog.json
│   │   └── translate_dialogues.py # Claude Haiku 4.5 대사 번역 스크립트
│   ├── hd/
│   │   ├── upscale_poc.py         # scale4x 알고리즘
│   │   └── batch_upscale.py       # 일괄 처리
│   └── recon/                     # 바이너리 정찰 (capstone)
│       ├── extract_strings.py / disasm_thumb.py
│       ├── find_pic_xrefs.py / find_f81f.py / find_base.py
├── android/                       # Android Kotlin 클라이언트
│   ├── settings.gradle.kts / build.gradle.kts / gradle.properties
│   ├── README.md                  # 빌드 방법
│   └── app/
│       ├── build.gradle.kts
│       └── src/main/
│           ├── AndroidManifest.xml
│           ├── res/values{,-ko}/strings.xml + themes.xml
│           ├── assets/                  # 변환된 자산 (3000+ 파일)
│           │   ├── sprites/             # 표준 (1×)
│           │   ├── sprites_hd/          # HD (4× scale4x)
│           │   ├── maps/                # 134 _mp.json
│           │   ├── cif/                 # 103 _cif.json
│           │   ├── strings/ / palettes/
│           │   ├── dialogue_corpus.json / dialogue_top_texts.json
│           │   ├── dialogue_translations_en.json   # (생성 후 배포)
│           │   └── asset_catalog.json
│           └── java/com/hero3/remake/
│               ├── MainActivity.kt           # Scene 스택 + Locale override
│               ├── engine/
│               │   ├── GameView.kt           # SurfaceView 60fps 렌더 루프
│               │   ├── InputController.kt    # MIDP 비트마스크
│               │   ├── VirtualKeypadView.kt  # 가상 키패드
│               │   ├── Scene.kt              # 추상화
│               │   ├── UiKit.kt              # 공용 그리기 (박스/메뉴/다이얼로그/헤더)
│               │   ├── Settings.kt           # SharedPreferences (언어/HD)
│               │   ├── GameState.kt          # slotId 기반 게임 진행도
│               │   ├── Strings.kt            # i18n 헬퍼 (txt_NNN)
│               │   └── NpcRegistry.kt        # NPC 데이터 (현재 map0 4명 하드코딩)
│               └── scene/                   # 11개 씬
│                   ├── TitleScene.kt         # 로고+메뉴
│                   ├── MainMenuScene.kt      # 7개 원본 메뉴 + 디버그
│                   ├── MapWalkScene.kt       # 영웅 이동 + NPC 인접 검사
│                   ├── NpcDialogueScene.kt   # NPC 대화 + 한·영 토글
│                   ├── SaveSlotScene.kt      # 3 슬롯 SAVE/LOAD
│                   ├── StatusScene.kt        # 캐릭터 스탯 mockup
│                   ├── InventoryScene.kt     # 가방/장비/스킬 mockup
│                   ├── DialogueDemoScene.kt  # 코퍼스 대사 데모
│                   ├── SettingsScene.kt      # 언어/품질
│                   ├── SpriteGalleryScene.kt # 3,131 sprite 애니메이션
│                   └── MapScene.kt           # 134 맵 heatmap (디버그)
├── work/                          # gitignore (재생성 가능)
│   ├── extracted/                 # JAR 풀린 자산
│   ├── converted/                 # 변환된 자산 (PNG/JSON)
│   ├── converted_hd/              # HD 자산 (4× scale4x)
│   └── (분석용 보조 출력들)
└── Readme.md
```

## 4. 추가 진행 필요한 항목

우선순위 순서로 정렬. 각 항목은 **목표 / 블로커 / 작업 계획** 으로 구성.

> 2026-05-01 업데이트: Pre-Ghidra UI/번역 작업 완료. Section 4.6 (대사 번역), 4.7 (게임 로직), 4.1~4.5 (Ghidra 필요한 항목들) 이 다음 우선순위.

### 4.1 [HIGH] type 0x0c sparse pixel format 정밀 해독

- **목표**: theme/obj 타일을 진짜 그래픽으로 렌더링 → 맵을 실제 게임 화면처럼 표시
- **블로커**: 16-bit 레코드의 정확한 bit layout (col/color/row 비트 순서) 미확정. 4가지 가설 모두 깨끗한 디코드 실패
- **현재 상황**:
  - 스플래시 통계: 2 bytes per non-transparent pixel
  - 1638 records / 3072 pixels (theme_6) ≈ 53% non-transparent (합리적)
  - 첫 바이트 패턴이 row 단위로 클러스터링됨 — row 인코딩이 high byte일 가능성 높음
- **추천 작업 방법**:
  1. Ghidra 또는 capstone 으로 `client.bin64000` 의 비트맵 디코더 함수 식별 — 0xf81f 직접 비교 코드는 없으나 `frameBuf is NULL` 문자열 (offset 0xa61c8) 가까이의 함수 추적
  2. PIC 패턴 (`LDR; ADD sl; LDR`) 을 따라 함수 내부 픽셀 unpack 로직 분석
  3. 또는 Ghidra GUI 로 binary 를 raw ARM Thumb 로드 후 분석
- **파일**: `work/decode_0c_theme.py`, `work/analyze_0c.py`, `work/find_frame_markers.py`
- **예상 효과**: theme(47), obj(44), 캐릭터 일부 0x0c 프레임이 정상 렌더링 → MapScene이 진짜 게임 월드 표시

### 4.2 [HIGH] `_mp` extras 영역 (NPC/exit/event 배치) 파싱

- **목표**: 맵 위에 NPC, 출구, 이벤트 트리거 표시 → 인터랙티브 맵 가능
- **블로커**: 7-byte 정도 record로 추정되나 정확한 필드 구조 미확정
- **현재 관찰**:
  - flag byte (0x00/0x40/0x80/0xc0) 빈번 — entity type 또는 direction 추정
  - 16-bit 좌표값 임베디드 추정 (x, y)
- **추천 작업**:
  1. Ghidra 로 NPC 로딩 함수 (`Event_freeID`, `loadDataID` 부근) 분석
  2. 또는 여러 맵의 extras 데이터를 정렬·차분 분석하여 record 길이 통계적으로 추정
- **파일**: `work/analyze_extras.py`

### 4.3 [HIGH] `_cif` animation timing 데이터 디코드

- **목표**: 캐릭터를 진짜 애니메이션 (idle/walk/attack/hit/death 등)으로 표시
- **블로커**: slot indices 이후의 byte-stream 시퀀스 (timing/event 데이터) 미해독
- **현재 관찰**:
  - 9-byte record 가정 시 끝에 0xff terminator
  - `19 19` 고정값 (frame size?) 패턴
  - hero/boss는 8 슬롯 (4방향 × 2상태?), enemy는 1~4 슬롯
- **추천 작업**: Ghidra `Hero_Free`, `freeBossType` 부근 함수 분석

### 4.4 [MEDIUM] `_scn` opcode 매핑

- **목표**: 이벤트 스크립트의 명령어 디스어셈블 → 실제 이벤트 흐름 재현
- **현재 상황**: 26,415 대사는 추출했지만 byte-code 명령은 미해독
- **추천 작업**:
  1. Ghidra 로 이벤트 인터프리터 함수 식별 (`onEventMessageOkKey`, `eventManager` 부근)
  2. Switch 또는 dispatch table 패턴 찾아 opcode → 동작 매핑
  3. Python 디스어셈블러 작성

### 4.5 [MEDIUM] 사운드 SMAF → OGG 변환 파이프라인

- **목표**: 33개 BGM/효과음을 Android `MediaPlayer`로 재생 가능하게
- **블로커**: SMAF 디코더 도구 필요 (런타임 SMAF 라이브러리 없음)
- **헤더 검증**: 33/33 SMAF (MMMD magic) 확인 — `tools/converter/convert_h3_smaf.py` 실행 시 `work/h3/analysis/smaf_summary.txt` 생성 (BGM 19 + SFX 14, 총 186KB)
- **추천 도구 (2026-05-10 조사 갱신)**:
  - **smaf-converter** (Java JAR, https://github.com/antanas-vasiliauskas/smaf-converter) — 사전 빌드 JAR, JRE 만 있으면 즉시 사용. vavi-sound 기반 (au/Softbank YAMAHA 링톤 호환, SKT GVM 호환은 직접 테스트 필요)
  - **TiMidity++** (Windows 바이너리, https://sourceforge.net/projects/timidity/) + SF2 soundfont — MID → WAV
  - **FFmpeg** (winget install Gyan.FFmpeg) — WAV → OGG
- **불가 확인 옵션**: `smaf2midi` (Wohlstand) → GitHub 404 (소멸), `vgmstream` → SMAF 미지원, Pure Python → FM 합성 시뮬레이션 필요 비현실적
- **사용자 작업 시나리오**:
  1. smaf-converter JAR 다운로드 → `bgm0_mf` 1개로 시범 변환 후 음질/호환성 확인
  2. 일괄 변환 PowerShell 명령 (`tools/converter/convert_h3_smaf.py` 의 docstring 참조)
  3. TiMidity++ + ffmpeg 로 WAV → OGG
  4. Android `app/src/main/assets/sounds/` 에 배포

### 4.6 [MEDIUM] 대사 번역 (UI 어휘는 완료)

- **상태**: UI 어휘 196개 100% 영어 번역 완료. 대사 본문 (9,741 unique) 미번역
- **다음 단계**:
  1. ~~캐릭터 이름·지명 수동 번역~~ ✅ 완료 (translation_dict.py)
  2. ~~UI 텍스트 196개 수동 번역~~ ✅ 완료 (100% 커버리지)
  3. **대사 자동 번역 (LLM 활용) → 사람 검수** ← 다음 작업
     - Input: `dialogue_corpus.json` (26,415 lines, 9,741 unique)
     - Pipeline: unique 텍스트만 → LLM 번역 → DialogueDemoScene 으로 검수
  4. 일본어/중국어 추가 (`values-ja`, `values-zh-rCN`)

### 4.7 [LOW] Android 게임 로직 본격 구현

- **현재**: 8개 씬 (Title/MainMenu/Status/Inventory/DialogueDemo/Settings/SpriteGallery/MapScene) 모두 mockup 또는 데모 단계로 구현됨
- **다음 단계**:
  1. ~~타이틀 화면~~ ✅ 완료 (`TitleScene`)
  2. ~~다이얼로그 박스 시스템~~ ✅ 완료 (`UiKit.drawDialogueBox` + `DialogueDemoScene`)
  3. ~~인벤토리/스테이터스 화면 mockup~~ ✅ 완료 (실제 데이터 연결만 남음)
  4. **맵 화면에 영웅 sprite 배치 + 이동** ← 다음 작업 (RPG 본체의 시작)
     - 영웅 위치 좌표 + Settings 에 저장 (현재 맵 ID + x/y)
     - 방향키 → 좌표 갱신 + Layer 1 (collision) 검사
     - Map 전이 (출구 좌표 도달 시) — `_mp` extras 분석 필요 (4.2)
  5. NPC 시스템 (sprite 배치 + 인터랙션 → DialogueScene)
  6. 캐릭터 데이터 모델 + 저장 (게임 진행도)
  7. 전투 시스템 (가장 큰 작업)

### 4.8 [LOW] 빌드 검증

- **현재**: Android 코드만 작성됨, 실제 빌드 미검증 (Gradle/Android SDK 미설치 환경)
- **사용자 환경에서 필요**:
  ```
  cd android
  gradle wrapper --gradle-version 8.7    # 한 번만
  ./gradlew :app:assembleDebug
  ```
- 또는 Android Studio 에서 `android/` 디렉토리 열기

## 5. 빠른 참조

### 5.1 변환 명령어

```bash
# 원본 JAR 추출
unzip -o Hero3/0103EFD4.jar -d work/extracted

# 모든 자산 변환 (단일 명령)
cd tools/converter
PYTHONIOENCODING=utf-8 python convert_all.py ../../work/extracted ../../work/converted

# 대사 코퍼스 빌드
PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py

# Android assets 갱신
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets

# HD 업스케일 (수 분 소요)
cd ../hd
PYTHONIOENCODING=utf-8 python batch_upscale.py
```

### 5.2 바이너리 정찰

```bash
cd tools/recon
# ASCII 문자열 + 함수명 추출
PYTHONIOENCODING=utf-8 python extract_strings.py | less

# Thumb 디스어셈블 (시작 64 bytes + LDR pc-rel literal pool)
PYTHONIOENCODING=utf-8 python disasm_thumb.py
```

### 5.3 핵심 발견값 (외부 도구에 입력 시 유용)

| 값 | 의미 |
|---|---|
| `0xf81f` | RGB565 마젠타, 모든 BM의 투명 색 마커 |
| `0x1ff8` (LE) / `0xf81f` (BE) | BM 프레임 boundary 마커 |
| `0xa61c8` | 'frameBuf is NULL' 문자열 file offset |
| `0xa5d94` | '/hero/h00000_bm' 문자열 file offset |
| `r10 (sl)` | GOT base 레지스터 |
| GCC `-fpic` | 컴파일 옵션 (PIC) |

### 5.4 자주 보는 파일

- 자산 포맷 사양: [`docs/asset-formats.md`](asset-formats.md)
- Android README: [`android/README.md`](../android/README.md)
- 스토리 코퍼스: `work/converted/dialogue_corpus.json` (3MB)
- 빈도 상위 200: `work/converted/dialogue_top_texts.json`

## 6. 알려진 이슈

| ID | 이슈 | 워크어라운드 |
|---|---|---|
| #1 | `map134_mp` 비표준 헤더 (NUL 부재) | 변환 시 1개 에러 보고됨, 무시 가능 |
| #2 | type 0x0c 프레임이 노이즈로 렌더 | 정상. bit layout 미해독, 추후 정밀 분석 필요 |
| #3 | 일부 0x0b 프레임 2-6 byte underrun | 시각 영향 미미 (마지막 픽셀 행 일부 누락) |
| #4 | hero/boss CIF 인덱스가 BM 파일명 매칭 안 됨 | 멀티프레임 BM의 글로벌 인덱스 추정. enemy/map은 직접 매칭 정상 |
| #5 | `Hero3OptionSave` (32B) XOR 암호화 | 호환 불필요라 무시 |

## 7. 빠른 재시작 체크리스트

다음 세션에서 이 프로젝트를 이어서 할 때:

1. [ ] `MEMORY.md` 가 자동 로드되어 컨텍스트 유지됨
2. [ ] 이 [`PROGRESS.md`](PROGRESS.md) 파일 맨 위 **⚡ 다음 세션** 섹션 확인
3. [ ] [`docs/asset-formats.md`](asset-formats.md) 에서 자산 포맷 세부 확인
4. [ ] 작업할 항목 결정 (A/B/C/... 중 선택, 또는 §4 의 8개 후보)
5. [ ] `work/extracted/` 가 비어있으면 JAR 재추출:
   ```bash
   unzip Hero3/0103EFD4.jar -d work/extracted
   ```
6. [ ] 변환 산출물이 비어있으면 재실행:
   ```bash
   cd tools/converter
   PYTHONIOENCODING=utf-8 python convert_all.py ../../work/extracted ../../work/converted
   PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py
   PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
   cd ../i18n
   PYTHONIOENCODING=utf-8 python generate_string_resources.py
   PYTHONIOENCODING=utf-8 python build_asset_catalog.py
   cd ../hd
   PYTHONIOENCODING=utf-8 python batch_upscale.py    # 시간 소요 (3분 정도)
   ```
7. [ ] Android Studio 로 `android/` 열거나 `cd android && gradle wrapper --gradle-version 8.7 && ./gradlew :app:assembleDebug` 로 빌드 검증

## 7a. 마지막 세션 (2026-05-01) 결정사항·맥락

다음 세션이 알아야 할 미묘한 사항:

- **현재 상태**: NPC 시스템 + 세이브 슬롯 + dat 파싱까지 완료. 11개 씬 통합되어 영웅이 NPC와 대화하고 세이브 가능. **다음 자연스러운 진행은 (1) 대사 번역 실행 → (2) 인벤토리/스테이터스 데이터 모델 → (3) 출구·맵 전환 → (4) 상점/전투** 순서.
- **NpcRegistry 는 하드코딩**: map0(NEOSOLTIA) 4명 (촌장/상인/경비병/아이). `_mp` extras 파싱이 풀리면 자동 생성으로 전환. 그 전까지는 `engine/NpcRegistry.kt`에 직접 추가.
- **GameState slotId 시스템**: slot 0 = 활성, slot 1~3 = SaveSlotScene 저장. 슬롯별로 별도 SharedPreferences. 새 슬롯 추가 시 SaveSlotScene `slotCount` 만 늘리면 됨.
- **char_dat 분석 완료, 미연결**: 리츠 5클래스 / 케이 5클래스 데이터가 `assets/dat/char_dat.json`에 있음. StatusScene 의 mockup ("케이 / Soltian Warrior") 을 이 데이터로 교체할 준비됨.
- **번역 사전 한계**: 일부 한국 RPG 고유 어휘는 추정 번역 (예: "지축모드" → "Pivot Mode", "투신의" → "of War God"). 원작자 의도 다를 수 있음.
- **type 0x0c 파일이 많음**: theme(47) + obj(44) + 일부 캐릭터 sprite. 현재 MapWalkScene 은 색상 그리드 placeholder. Ghidra 후 재변환하면 진짜 타일로 교체.
- **map134_mp** 비표준 (NUL 부재): 변환 에러 1건. 무시 가능.
- **NPC 칸 통행 불가 + facing-tile OK**: 영웅이 바라보는 칸에 NPC 가 있으면 OK 키로 대화. 인접한 NPC 가 있으면 하단 힌트에 표시.

## 8. 작업 환경 메모

- OS: Windows 11
- Python: 3.12 (with Pillow 11.2.1, capstone 5.0.7)
- Shell: bash (Git Bash) + PowerShell 사용 가능
- 인코딩 함정: PowerShell/Windows console 은 cp949 → 한국어 출력 시 `PYTHONIOENCODING=utf-8` 필수
- 작업 디렉토리: `c:\gameRemake\testrepo`
