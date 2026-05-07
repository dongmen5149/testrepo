# Hero3 Remake — 진행 상황 & 다음 단계

> 이 문서는 다음 작업 세션에서 컨텍스트 유실 없이 이어서 진행할 수 있도록 정리한 핸드오프.
> 자세한 자산 포맷 사양은 [`docs/asset-formats.md`](asset-formats.md) 참조.

## ⚡ 다음 세션 — 여기서부터 시작

**최신 커밋**: `c24c447 feat:영웅서기3 §4.2 _mp extras 97% 해독 + 데코 마커 렌더` (이전 세션까지 반영)

### A5) §4.3 _cif cell layout 4-byte stride 검증 (2026-05-07 후반) ✅ 부분
- [tools/recon/analyze_cif.py](../../tools/recon/analyze_cif.py) 신설 — h0_cif 113 frame 자동 추출, group/lead 분포 통계.
- **셀 stride 확정**: group1(`0a 02 0b` 41-byte 레코드, 8 frame) 의 R0→R2/R4→R6 byte-delta 분석 결과 — y-bobbing 변동이 정확히 4-byte 주기 offset 1 위치(4, 8, 16, 20, 24, 28, 32, 36, 40)에서만 ±1 발생.
- **셀 포맷 (가설 검증됨)**: `[x_s8, y_s8, bm_ref_u8, flag_u8]` 4 byte × 9 cells, offset 3..38. 트레일러 2 byte (offset 39..40) 미해독.
- **shadow cell 식별**: cell 2 (offset 11..14) 는 bobbing 안함 → 그림자 셀로 추정 (지면 고정).
- group1 R0 디코드 결과: cell0~8 모두 BM ref 0x00~0x27 범위 — h0_cif indices=[1,2,3,10,17,19,16,8] 와 직접 매칭 안됨. 글로벌 multi-frame BM 인덱스로 해석 필요 (이슈 #4 와 동일 패턴).
- **미해결**: ① count byte(0x0b=11) vs 실측 9 cells 불일치 — count 의미 재해석 필요, ② 트레일러 2 byte 정체, ③ ref→BM 매핑 — §4.1 글로벌 인덱스 테이블 풀어야 함, ④ 4방향(UP/DOWN/LEFT/RIGHT) 매핑은 group1/group2/...별 sprite 시각 매칭 필요.

**A6) 그룹 분류 + 방향 매핑 가설 (2026-05-07 추가) ✅ 부분**
- analyze_cif.py 가 113 frame 을 25 lead group 으로 분류. → [work/h3/h0_cif_groups.json](../../work/h3/h0_cif_groups.json)
- **렌더 후보 그룹 (작은 ref/좌표, 4-byte cell layout 적합)**: `0a020b`(16), `0a0208`(19), `0a2208`(17), `0a2306`(5), `0a0302`(1), `0a2500`(2), `0a0500`(2) — 합계 62 frames.
- **방향 매핑 가설**: type byte (offset 1) 의 bit 5 (=0x20) 가 horizontal flip 플래그.
  - `0a 02 0b` cell0 x=-5 / `0a 22 08` cell0 x=+4 → 같은 액션의 LEFT/RIGHT mirror 추정
  - `0a 02 08` (UP/DOWN 후보) / `0a 23 06` (다른 방향)
- 비-렌더 그룹들 (`0a 84 04`, `0a 80 00`, `0a e8 19` 등 51 frames) — 좌표가 ±90, ±125 같은 큰 값 → hitbox/이벤트/사운드 메타데이터 프레임 추정. 렌더링과 무관할 가능성.

**A7) Placeholder PNG 렌더로 4-byte cell layout 시각 검증 ✅ (2026-05-07 추가)**
- [tools/recon/render_cif_frame.py](../../tools/recon/render_cif_frame.py) 신설 — 96×96 캔버스에 ref 별 색상의 16px 박스로 cell 0~8 그림
- 4 lead group 출력 → [work/h3/cif_render/](../../work/h3/cif_render/) 4 PNG
  - `0a020b @12`: 휴머노이드 클러스터 ✓
  - `0a2208 @1039`: 같은 모양이 **horizontal mirror** ✓ — bit 5 flip 가설 확정
  - `0a0208 @670`, `0a2306 @3125`: 다른 방향/액션의 다른 클러스터 형태
- **결론**: 4-byte cell layout `[x_s8, y_s8, ref, flag]` 시각 검증 완료. 가설 확정.
- 모든 hero cif (h0~h11) 의 indices 가 h1XXXX_bm 시리즈만 참조함을 확인 (header 분석). 슬롯들은 공유 BM atlas 의 일부.

**A8) ref → h1XXXX_bm 매핑 해독 ✅ (2026-05-07 확정)**
- [tools/recon/composite_cif_frame.py](../../tools/recon/composite_cif_frame.py) 신설 — cumulative pool 가설 검증.
- **확정 매핑**: `ref → h1{ref//3:04d}_bm/frame_{ref%3:02d}`. 3 frames/file, 69 frame 글로벌 풀.
- 실제 BM 합성 결과 → [work/h3/cif_render_real/](../../work/h3/cif_render_real/)
  - `0a020b @12`: **명확한 휴머노이드 영웅 sprite** ✓ 머리/몸/무기 식별 가능
  - `0a2306 @3125`: 다른 자세의 영웅 sprite ✓
  - `0a2208 @1039` (mirror): 일부 cell ref 0x82/0xeb 가 풀 범위 초과 → 9-cell 고정 가정이 over-fit. 실제 cell count 가변, 후행 byte 는 메타.
- **결정사항**: cell 0~8 중 ref ≤ 0x44 인 것만 렌더 cell, 그 외는 메타데이터. 정확한 cell count 인코딩은 추후 (count byte 0x0b 의미 재해석 필요).

**A9) 4방향 walk-cycle PNG 베이킹 ✅ (2026-05-07 완료)**
- [tools/converter/bake_hero_walkcycle.py](../../tools/converter/bake_hero_walkcycle.py) — h0_cif 첫 4 그룹 × 8 frame = 32 PNG 베이킹.
- 산출: [android/app/src/main/assets/sprites/hero/h0_walk/dir{0..3}_{0..7}.png](../../android/app/src/main/assets/sprites/hero/h0_walk/)
- 각 방향(0=group1@12, 1=group2@341, 2=group3@670, 3=group4@1039)에서 영웅 sprite 가 시각 확인됨. 일부 cell 은 메타라 떨어져 보이지만 main body 는 일관됨.

**A10) MapWalkScene walk-cycle 와이어 ✅ (2026-05-07 완료)**
- `loadHeroFrames` → `loadHeroWalk` 로 교체. `List<List<Bitmap>>` (4 dir × 8 anim) 로딩.
- 영웅 렌더 분기: `heroWalk[facing][animFrame % 8]`. 8 frame walk-cycle 자동 cycling.
- 매핑: dir0=DOWN, dir1=UP, dir2=LEFT, dir3=RIGHT (FACING 순서와 동일 가정 — 디바이스에서 시각 검증 필요).
- 빌드: `:app:assembleDebug` + `:app:testDebugUnitTest` 모두 BUILD SUCCESSFUL.

**A11) walk_sheet 시각 분석 + dirOrder 가설 적용 ✅ (2026-05-07 완료)**
- 4×8 walk-cycle 비교 시트 생성 → [docs/h3/walk_sheet.png](walk_sheet.png)
- 시각 관찰: dir0 / dir3 가 명확한 좌우 mirror 쌍 → 각각 LEFT, RIGHT. dir1 / dir2 는 DOWN, UP 후보.
- `MapWalkScene.loadHeroWalk()` 에 `dirOrder = intArrayOf(1, 2, 0, 3)` 추가 — FACING_DOWN=1, FACING_UP=2, FACING_LEFT=0, FACING_RIGHT=3.
- 빌드+테스트 BUILD SUCCESSFUL.

**A12) boss/enemy cif 구조 비교 → 별도 인코딩 확정 (2026-05-07)**
- boss0_cif (slot_count=1, indices=[8], 10084 byte) / e000_cif (slot_count=1, indices=[4], 1697 byte) 헤더 분석.
- **결론**: hero cif 의 `0a XX YY` 41-byte 프레임 구조가 boss/enemy 에는 **적용되지 않음**.
  - boss0_cif post-header: `01 09 12 7f 00 ff ff 20 05 d5 cb ...` — `7f 00 ff ff` 패턴이 cell 종료 sentinel 로 추정.
  - enemy 는 더 짧고(1.6~1.8KB) 구조 미해독.
- hero cif 는 8 slot multipart 합성용 (캐릭터 합성), boss/enemy 는 단일 sprite slot 으로 단순 frame list 추정. 별도 디코더 필요.

**A13) 흩어진 cell 의 정체 ✅ 분석 완료**
- 0a 22 08 같은 mirror 그룹의 cell 5/8 ref >0x44 는 메타 cell. 나머지 7 cell 만 렌더 시 sprite body 일관성 유지됨 (walk_sheet 시각 확인).
- "흩어진" 인상은 실제 sprite parts (무기/아이템 overlay) 포함된 자연스러운 모습. 추가 정리 불필요.

**다음 세션 첫 작업** (1~2시간):
1. 디바이스/에뮬레이터 실행해 dirOrder 시각 검증. DOWN↔UP 어긋나면 `intArrayOf(2,1,0,3)` 으로 swap.
2. boss/enemy cif 별도 디코더 작성 (sentinel `7f00ffff` 기반 frame split). [HIGH 우선순위는 아님 — 전투 시스템 구현 시점에 필요]
3. flag byte 의미 분석 — 0x00 vs 0x01 vs 0x08 패턴 (frame draw_order 추정).
2. 흩어진 cell 정리 — ref ≤ 0x44 필터를 더 정교하게 (cell idx 0~5 만 렌더, 6~8 은 메타?). 또는 type byte YY (=0x0b/0x08/0x06) 가 실제 cell count 이고 9 가 아니라는 가설 검증.
3. flag byte 의미 — 0x00 vs 0x01 vs 0x08 패턴 분석 (flip/blend/draw_order 후보).
4. boss0_cif / e000_cif 같은 cif 에 동일 cumulative 매핑 검증 (boss/enemy 는 b1XXXX_bm / e0XXXX_bm 풀 추정).

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
| `_cif` | 103 | ⚠️ 헤더만 (animation timing 미해독) |
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
- ~~CI 셋업~~ ✅ [.github/workflows/android.yml](../.github/workflows/android.yml) — push/PR에 testDebugUnitTest + assembleDebug 자동 실행
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
- **추천 도구**:
  - `smaf2midi` (Linux/Windows)
  - 또는 KSS/Yamaha SMAF SDK
  - 최후의 수단: 수동 변환 (33개라 가능)

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
