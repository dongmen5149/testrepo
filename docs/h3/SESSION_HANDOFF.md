# Hero3 인수인계 노트 (Round 59 종료 시점, 2026-05-18)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~75-78%**. 게임 데이터 평문 파싱 95% 완료. DES 암호화 7 파일만 사용자 환경 (NDK runner) 필요.

마지막 commit: `4c0dad22 feat:영웅서기3 Round 59 — char/npcg/s4 dat 평문 파싱 (10 classes + 78 NPCs + 15 skills) + 리츠/케이 PLAYER 캐릭터 확정`

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ 다른 skill 파일 존재 확인

s4_dat = 창수 클래스 1개만 발견. 10 playable class 모두 skill 파일이 있어야 함.

```bash
ls work/h3/extracted/skill/
```

발견 시 → `tools/recon/parse_char_npcg_s4_dat.py` 의 `parse_s4_dat()` 재사용해서 모두 파싱.

**예상 파일명**: `s1_dat`~`s10_dat` (10 클래스용) 또는 `s_dat` (통합) 등.

### 1.2 ⭐⭐⭐ boss_dat stat 24-bit HP 가설 검증

R58 의 가설: boss_dat entry 의 bytes 0x08..0x0a (3 byte) = **24-bit HP**.

검증 방법:
- boss 0 리츠 lvl 14: bytes `00 68 10` → BE 24-bit = 0x006810 = 26640 HP
- boss 1 리츠 lvl 24: 동일 위치의 bytes 확인
- boss 2 리츠 lvl 32: 동일
- bossh 의 리츠 lvl 51/56/60: hard mode HP

리츠 라인업의 HP scaling (lvl 14 → 24 → 32 → 51 → 56 → 60) 이 합리적 증가 곡선이면 24-bit HP 가설 확정.

스크립트: `tools/recon/parse_boss_dat.py` 확장 — int24 BE 해석 추가.

### 1.3 ⭐⭐ 미확인 데이터 폴더 확인

```bash
ls work/h3/extracted/{map,event,fgi,font,snd,logo,boss,npc,skill,hero,comm,enemy}/ | head -200
```

R58 까지 dat/ + boss/ + npc/ + skill/ 만 확인. map/event/hero 폴더에 추가 데이터 파일 가능성 (예: `/dat/i0_dat`~`i18_dat` 외 다른 chapter 파일).

### 1.4 ⭐⭐ FUN_4f358 본문 정밀 (Round 55 가설 검증)

R55 발견: FUN_4f358 (896B) = int16 sign-extension + cmp #0xc 패턴. **enemy stat reader 가설**.

```bash
python tools/recon/disasm_battle_top_candidates.py
```

caller chain 추적 → 실제로 enemy_dat 의 stat field 를 읽는지 검증. 만약 stat reader 라면 → battle 시스템 호출 경로 발견.

### 1.5 ⭐ FUN_3a028 16-JT 디코드 (Round 54 보류)

party stats menu dispatcher. 16 entry 매핑 → 어떤 스탯/스킬 화면인지 식별.

```bash
# JT base @ sl + 0xffff4788 = ? — Round 51 의 decode 패턴 재사용
```

## 2. 사용자 환경 필요 작업 (보류)

### 2.1 DES 7 파일 복호화

**Hero5 NDK runner 활용**: `tools/ndk_des_runner/des_runner` (armv7 ELF) + key `"0EP@KO91"` + `dat/des_dat` tables → drop_dat / droph_dat / getitem_dat / smith_dat / smithh_dat / shop_dat / shoph_dat 복호화.

실행 환경: Android AVD armeabi-v7a 또는 qemu-arm. 자세한 절차: [`tools/ndk_des_runner/README.md`](../../tools/ndk_des_runner/README.md), `docs/h5/SESSION_HANDOFF.md` §진입점 A.

→ [[reference_h5_des_blocker]] 정보 그대로 적용.

복호 성공 시 예상 평문:
- drop_dat: 적별 drop item 테이블
- getitem_dat: 이벤트 item 획득
- smith_dat: 대장간 업그레이드 레시피
- shop_dat: 상점 inventory

### 2.2 SMAF→OGG 변환

H3 의 SMAF 음악 파일 33개, paired OGG 없음. `smaf2midi` 등 외부 도구 필요.

### 2.3 9,741 unique 대사 LLM 번역 (~$0.66)

비용 승인 필요. R39 의 scn_v2 26,415 줄 분석 결과 기반.

## 3. 이미 발견한 Hero3 게임 시스템 (Round 56-59 결과)

### 3.1 평문 파싱 완료 (11 파일)

| 파일 | 크기 | entries | 내용 |
|---|---|---|---|
| `dat/enemy_dat` | 5495B | 161 | 적 stats (lvl/MP/HP/Gold/ATK/DEF/EXP/AGI) |
| `dat/enemyh_dat` | 5495B | 161 | hard mode 적 stats |
| `boss/boss_dat` | 508B | 15 | 보스 stats (24-bit HP 가설) |
| `boss/bossh_dat` | 508B | 15 | hard 보스 stats |
| `dat/char_dat` | 348B | 10 | 플레이어블 클래스 (리츠 5 + 케이 5) |
| `dat/quest_00_dat` | 4851B | 37 | 메인퀘스트 1막 |
| `dat/quest_01_dat` | 4216B | 7+ | 사이드퀘스트 |
| `dat/quest_10_dat` | 5360B | ? | 메인퀘스트 2막 |
| `dat/quest_11_dat` | 4269B | ? | 사이드퀘스트 2막 |
| `npc/npcg_dat` | 1014B | 78 | NPC graphics info (13B/entry) |
| `skill/s4_dat` | 894B | 15 | 창수 클래스 skill tree |

### 3.2 DES 암호화 (미해결, 7 파일)

| 파일 | 크기 | entropy |
|---|---|---|
| `dat/drop_dat` | 3080B | 7.90 |
| `dat/droph_dat` | 3080B | 7.79 |
| `dat/getitem_dat` | 400B | 7.40 |
| `dat/smith_dat` | 896B | 7.76 |
| `dat/smithh_dat` | 896B | 7.68 |
| `dat/shop_dat` | 72B | 5.92 (의심) |
| `dat/shoph_dat` | 72B | 5.89 |

DES 정보:
- **Key**: `"0EP@KO91"` (binary 0xac594, 8 bytes ASCII)
- **Algorithm tables**: `dat/des_dat` (824B = 표준 FIPS DES IP/IP⁻¹/E/P/S1-S8/PC1/PC2)
- **변형 시도**: ECB / CBC+zero-IV / CBC+key-IV / parity-adjusted / bit-reversed key 모두 실패
- **유일 해결**: Hero5 NDK runner (armv7 dlsym + MX_desDecrypt)

### 3.3 Ghidra 분석 진척

- ✓ FUN_818f0 = (event×state) 2D matrix dispatcher (Round 50-52, 30 leaf handlers)
- ✓ FUN_9a008 = 7-mode script bytecode interpreter (Round 53-54, 122 sub-opcodes)
- ✓ FUN_77c78 = MD5-verified save record reader (Round 53)
- ✓ MD5 algorithm in binary (FUN_5610c / 5613c / 56164 / 561dc)
- ✓ DES key + tables 위치 (Round 57)
- ✓ ObjectB master interface (14 methods, Round 31-53)
- ✓ task_struct (binary 외부 0xb6c80, R51 GOT[+0x444])
- ✓ Entity_state record (38B, 9 sub-fields, Round 52)
- ◯ FUN_4f358 = int16 stat extractor 가설 (Round 55) — 정밀 분석 필요
- ◯ FUN_3a028 16-JT (Round 54 보류)
- ◯ SCN opcode 0x12 (R37 11.4KB) 47-arm 매핑 (보류)

## 4. Hero3 게임 세계 (퀘스트 메타데이터로 식별)

### 4.1 8 main regions

1. **네메시스숲** — 시작 지역 (블랙헨지, 빛의신당, 주둔지)
2. **네오솔티아** — 솔티안 왕국 수도
3. **협곡** — 분기 지점 (성수 조합)
4. **아스크라** — 적국 (국경 돌파 후)
5. **엔자크사막** — 동남쪽 사막 (역사학자 NPC)
6. **토레즈** — 광산도시 (소녀 NPC, 유리엽서)
7. **로우엔 평원** — 동쪽 평원 (도적, 데몬)
8. **리파이너의유적** — 던전

### 4.2 2 주인공 + 5 클래스 분기

- **리츠**: 어쌀트워리어 / 디스럽터 / 건슬링어 / 나이트템플러 / 크레이지암즈
- **케이**: 버서커 / 데스나이트 / 섀도우워커 / 가디언나이트 / 소울마스터

### 4.3 적 라인업 (군단 시스템)

- 아스크란 군단 (적국, 가장 다양: 가드/워리어/템플러/체이서/엑셀/워락/건너/슈터)
- 코르버스 군단 (워리어/로그/어쌔신/건너)
- 솔티안 군단 (왕국군, 워리어/로그/매지션/위자드/워락)
- 포레스트/와일드 쿠퍼 (야생 동물)
- 일반 (도적 등)

### 4.4 15 bosses

- **리츠/케이** (튜토리얼/대결, tier 1-3, lvl 14-32)
- **멜페토/큐** (paired, tier 4, lvl 44)
- 벨루스, 시즈타이탄(×2), 아르보르, 오르도(×2)
- **홀리가디언** (lvl 46/67, final boss 추정)

## 5. 작업 순서 권장

다음 세션에 한 라운드 (Round 60) 진행할 때 다음 순서로:

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `ls work/h3/extracted/skill/` — 다른 skill 파일 즉시 확인 (1순위 작업)
3. 발견된 파일 모두 파싱 (`parse_char_npcg_s4_dat.py` 재사용)
4. boss_dat 24-bit HP 가설 검증 (parse_boss_dat.py 확장)
5. 추가 폴더 확인 (`ls work/h3/extracted/{map,event,fgi,font,snd,logo}/`)
6. 시간 여유 시 FUN_4f358 본문 분석
7. Round 60 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 60 종료 시): **~78-82%** (skill 파일 발견 시 +3%p, HP 가설 검증 시 +1%p).

## 6. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~59)
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보 (H3 도 동일 적용)
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-8].md`
- 모든 recon scripts: `tools/recon/`
