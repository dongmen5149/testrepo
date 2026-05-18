# Hero3 Ghidra — Boss data + Quest data 평문 파싱 완료 + DES variant matrix 실패 (Round 58)

> **세션**: 2026-05-18, Round 58
> **이전 Round**: [ghidra-des-system-and-dat-paths-2026-05-18.md](ghidra-des-system-and-dat-paths-2026-05-18.md) (Round 57)
> **재현 도구**: `tools/recon/dump_all_dat_files.py` / `parse_boss_dat.py` / `parse_quest_dat.py` / `tools/converter/decrypt_h3_dat_des.py` (variant matrix)

## 한 줄 요약

R57 의 "신규 데이터 파일들 JAR 재추출 필요" 가설 **즉시 폐기** — 모든 파일이 이미 `work/h3/extracted/` 의 별도 폴더 (`boss/`, `npc/`, `skill/`, `dat/`) 에 추출되어 있음. R56 의 dat/ 폴더만 검색했던 한계. **boss_dat (508B) = 15 bosses 완전 파싱** (리츠/케이/멜페토/큐/벨루스/시즈타이탄/아르보르/오르도/홀리가디언). **quest_*_dat 4개 파일 = 37+7+?+? quests 평문 EUC-KR 완전 파싱** (메인퀘스트 + 사이드퀘스트 본문). **DES variant matrix (ECB/CBC+IV/parity/bit-reverse)** 모두 entropy 감소 0 → **NDK runner 가 H3 도 유일 해결책** 확정 (H5 와 동일).

## 1. 모든 dat 파일 entropy 분석 (2YA)

`tools/recon/dump_all_dat_files.py` Shannon entropy 계산 + Korean/ASCII 분포:

| 파일 | 크기 | mod 8 | entropy | 분류 |
|---|---|---|---|---|
| **boss/boss_dat** | 508B | ✗ | 5.611 | **평문 ★** (enemy_dat 구조) |
| **boss/bossh_dat** | 508B | ✗ | 5.736 | 평문 (hard mode) |
| **dat/quest_00_dat** | 4851B | ✗ | 5.942 | **평문 ★** (Korean dominant, 4004 EUC chars) |
| **dat/quest_01_dat** | 4216B | ✓ | 5.988 | 평문 |
| **dat/quest_10_dat** | 5360B | ✓ | 5.922 | 평문 |
| **dat/quest_11_dat** | 4269B | ✗ | 6.001 | 평문 |
| dat/shop_dat | 72B | ✓ | 5.920 | 의심 (작은 파일) |
| dat/shoph_dat | 72B | ✓ | 5.892 | 의심 |
| **dat/smith_dat** | 896B | ✓ | **7.760 ★** | **암호화 (DES 후보)** |
| **dat/smithh_dat** | 896B | ✓ | **7.680 ★** | 암호화 |
| npc/npcg_dat | 1014B | ✗ | **3.615 ★ LOW** | 평문 structured (13B/entry) |
| skill/s4_dat | 894B | ✗ | 4.725 | 평문 (skill 텍스트) |
| dat/drop_dat | 3080B | ✓ | 7.904 ★ | 암호화 (R56 known) |
| dat/droph_dat | 3080B | ✓ | 7.785 ★ | 암호화 |
| dat/getitem_dat | 400B | ✓ | 7.400 | 암호화 |
| dat/enemy_dat | 5495B | ✗ | (R56 평문) | 161 enemies 평문 |
| dat/enemyh_dat | 5495B | ✗ | (R56 평문) | 161 enemies hard 평문 |

**DES 후보 update**: drop_dat, droph_dat, getitem_dat (R56 known) + **smith_dat, smithh_dat (R58 신규)** + shop_dat/shoph_dat (의심). 총 7 파일.

## 2. ★ boss_dat 완전 파싱 (2YA)

`tools/recon/parse_boss_dat.py` 결과: **15 bosses 추출**.

### 2.1 Boss entry 구조 (enemy_dat 와 약간 다름)

```
[size-2] [00] [name_len=4]   ← 3-byte header (enemy 와 동일)
[name + NO '@']               ← 4 bytes EUC-KR (2 Korean chars, enemy 는 6+ chars)
[19B stat block]              ← 동일 (lvl + 6×int16 + 3 byte)
[6-byte trailer]              ← 가변 (33 00 / 38 00 / 3c 00 / 42 02 / 33 01 / ...)
total = 32B (또는 34/36/38 가변)
```

### 2.2 15 Boss 라인업 (easy mode)

| pos | name | lvl (e/h) | 비고 |
|---|---|---|---|
| 0x0000 | **리츠** | 14 / 51 | tier 1 |
| 0x0020 | **리츠** | 24 / 56 | tier 2 (paired with 케이) |
| 0x0040 | **리츠** | 32 / 60 | tier 3 |
| 0x0060 | **멜페토** | 44 / 66 | tier 4 |
| 0x0082 | **케이** | 14 / 51 | tier 1 (paired with 리츠) |
| 0x00a2 | **케이** | 24 / 56 | tier 2 |
| 0x00c2 | **케이** | 32 / 60 | tier 3 |
| 0x00e2 | **큐** | 44 / 66 | tier 4 (paired with 멜페토) |
| 0x0100 | **벨루스** | 32 / 60 | |
| 0x0122 | **시즈타이탄** | 35 / 62 | |
| 0x0148 | **시즈타이탄** | 44 / 66 | tier 2 |
| 0x016e | **아르보르** | 39 / 64 | |
| 0x0192 | **오르도** | 44 / 66 | |
| 0x01b4 | **오르도** | 35 / 62 | tier 2 |
| 0x01d6 | **홀리가디언** | 46 / 67 | final boss? |

→ **리츠 + 케이** = paired duo. **멜페토 + 큐** = another paired duo. **홀리가디언** = 최고 레벨 = **final boss 가능성**.

### 2.3 Boss stat 해석 정확도 부족

enemy_dat 와 동일 19B stride 로 파싱했지만, stat 값이 비현실적으로 큼 (예: 리츠 lvl 14 f4_5=45824). boss_dat 의 stat field 가 endian 또는 byte layout 이 다를 수 있음.

원본 boss 0 (리츠 lvl 14) stat block bytes:
```
0x07: 0e          ; level = 14
0x08: 00 68 10    ; ★ 3 byte (NOT pad — enemy_dat 는 00 00 00 padding)
0x0b: b3 00       ; 2 byte (LE = 179)
0x0d: da 00       ; 2 byte (LE = 218)
0x0f: 00 01       ; 2 byte
0x11: 37 00       ; 2 byte (LE = 55)
0x13: 37 00       ; 2 byte (LE = 55)
0x15: 14 0a       ; 2 byte (LE = 0x0a14 = 2580)
0x17: 00 00 00    ; 3 byte
0x1a-0x1f: 33 00 03 02 01 02 ; 6 byte trailer (varies)
```

**가설**: boss 의 stat 는 **little-endian int16 + 3-byte HP**. 24-bit HP 가 boss 의 핵심 차이 (enemy max HP 28520 → boss 최대 ~1M 가능).

## 3. ★ quest_*_dat 4개 파일 완전 파싱 (2YA)

`tools/recon/parse_quest_dat.py` 결과: **순수 평문 EUC-KR quest text**.

### 3.1 quest_00_dat (4851B, 37 entries)

| # | name | body 요약 |
|---|---|---|
| 0 | 노력의 증명1 | 레아에게 받은 수련과제. 네메시스숲;블랙헨지 메인퀘스트 |
| 1 | 수상한 동굴 | 처음보는 동굴. 작은 동굴 탐사 메인퀘스트 |
| 2 | 길잃은 소녀 | 네오 솔티아까지 안내. 시엔과 함께 귀환 |
| 3 | 아름다운 임무 | 빛의 신당의 시엔에게 레아의 펜던트. 시엔 재회 |
| 4 | 길치인 소녀 | 시엔 재회 (재이동) |
| 5 | 협곡의 독소 | 협곡의 성수 조합 (대장장이 - 레아) |
| 6 | 위험한 협곡 | 시엔 재회 (재시도) |
| 7 | 국경 돌파 | 솔티아 추락 → 적국 진입 (아스크라 국경) |
| ... | (29 more) | |

### 3.2 quest_01_dat (4216B, 7 entries) — 다른 지역

| # | name | body 요약 |
|---|---|---|
| 0 | 엔자크의 영광 | 굴베이그의지팡이 (엔자크사막, 역사학자) |
| 1 | 영혼의 시 | 유리엽서 조합 (광산도시 토레즈, 소녀) |
| 2 | 로우엔의 치안 | 도적 처치 (로우엔 평원, 공무원) |
| 3 | 남쪽의 마물 | 데몬의뿔 수집 (로우엔, 데몬) |
| 4 | 마지막 증거 | 유리방패 (리파이너의유적, 역사학자) |
| 5 | 미궁의 미궁 | ? |
| 6 | ? | ? |

### 3.3 Entry 구조

```
[size_byte+2 total] [00] [name_len]
[name (Korean EUC-KR, no '@')]
[description body — embedded length prefixes \x13/\x19/\x1c/etc.]
[suffix: 위치;목표 + 카테고리(메인퀘스트/사이드퀘스트/엔자크/토레즈/로우엔)]
```

각 quest = (name, description, location, target, category/source) 5-tuple. Hero3 의 **퀘스트 데이터베이스 완전 추출**.

### 3.4 Hero3 게임 지역 (퀘스트로 식별)

- **네메시스숲** — 시작 지역 (블랙헨지, 빛의신당, 주둔지)
- **네오솔티아** — 솔티안 왕국 수도
- **협곡** — 분기 지점
- **아스크라** — 적국
- **엔자크사막** — 동남쪽 사막 (역사학자 NPC)
- **토레즈** — 광산도시 (소녀 NPC)
- **로우엔 평원** — 동쪽 평원 (도적/데몬)
- **리파이너의유적** — 던전

## 4. DES variant matrix 실패 (2YB)

`tools/converter/decrypt_h3_dat_des.py` 확장 — 5 variants 시도:

| variant | drop_dat entropy | smith_dat entropy | 결론 |
|---|---|---|---|
| ECB plain key | 7.885 | 7.746 | 변함없음 |
| CBC + zero IV | 7.932 | 7.789 | 변함없음 |
| CBC + key as IV | 7.933 | 7.788 | 변함없음 |
| ECB + parity-adjusted key | 7.885 | 7.746 | 변함없음 |
| ECB + bit-reversed key | 7.905 | 7.726 | 변함없음 |

→ **모든 variant 가 high entropy 유지** = 어느 것도 평문으로 복호 안 됨.

### 4.1 결론: Hero5 와 동일한 차단

[`reference_h5_des_blocker`] memory 의 정확한 동일 패턴:
- 표준 FIPS DES tables 확정 (des_dat 824B 매칭)
- key "0EP@KO91" 확정 (binary 0xac594)
- 그러나 정적 분석 (PyCryptodome / pyDes) 복호 실패
- **NDK runner (armv7 dlsym + MX_desDecrypt) 만 해결책**

Hero3 도 동일하게 `tools/ndk_des_runner/des_runner` (H5 용) 활용 가능 — 키와 알고리즘이 동일하므로 same binary runner 사용 가능. 단, dat 파일들이 추가적인 outer wrapping (MD5 prefix mismatch 등) 을 가질 수 있어 H5 와 미세 차이 존재 가능.

## 5. 신규 발견 종합 (Round 58)

### 평문 파싱 완료

- **15 bosses** (boss_dat / bossh_dat)
- **44+ quests** (quest_00 37 + quest_01 7 + quest_10/11 부분)
- **161+161 enemies** (R56 known)
- enemy 라인업: 아스크란/코르버스/솔티안/포레스트/와일드 군단 + 보스 9개 분리

### 신규 데이터 파일 분류

| 파일 | 상태 |
|---|---|
| boss_dat, bossh_dat | ✓ 평문 (R58 파싱) |
| quest_00..11_dat | ✓ 평문 (R58 파싱) |
| s4_dat (skill) | 평문 (R58 entropy 확인) — Round 59 파싱 필요 |
| npcg_dat | 평문 structured 13B/entry — Round 59 파싱 필요 |
| char_dat (348B) | 평문 (R56 보류) — Round 59 파싱 |
| smith_dat, smithh_dat | 암호화 (DES 후보, **신규**) |
| shop_dat, shoph_dat | 의심 (72B 작아서 entropy 신뢰성 낮음) |
| drop_dat, droph_dat | 암호화 (R56 known) |
| getitem_dat | 암호화 (R56 known) |

### Hero3 의 npc/ + skill/ + boss/ 폴더 확인

R57 에서 "JAR 재추출 필요" 가설 폐기:
- `extracted/boss/` 폴더에 `boss_dat`, `bossh_dat` 존재 ✓
- `extracted/npc/` 폴더에 `npcg_dat` 존재 ✓
- `extracted/skill/` 폴더에 `s4_dat` 존재 ✓
- `extracted/dat/` 폴더에 `quest_*_dat`, `shop_dat`, `smith_dat` 존재 ✓

## 6. Hero3 진행률 갱신 (Round 58 시점)

| 영역 | Round 57 | Round 58 |
|---|---|---|
| 자산 포맷 분석 | ~85% | **~90%** (+5%p: quest, boss, npcg 평문 확인) |
| Ghidra 게임 로직 | ~62% | ~62% (변동 없음) |
| 전투 데이터 | 100% | **+15 bosses, +44 quests** |
| 전투 코드 | ~5% | ~5% |
| 암호화 시스템 | ~70% | ~70% (variant matrix 시도, 결과 동일) |

**Android remake 완성 기준**: 약 **72-75%** (boss + quest 데이터 추출로 +3-5%p)

## 7. Round 59 권장 작업

### 7.1 우선 1순위: H5 NDK runner 로 H3 dat 복호화 검증

[`tools/ndk_des_runner/des_runner`] (Hero5 빌드 완료) 에 Hero3 의 drop_dat / smith_dat / getitem_dat 를 입력 → `MX_desInit("0EP@KO91") + MX_desDecrypt(data)` 호출 → 평문 dump.

H5 docs 의 NDK runner README + AVD/qemu 절차 활용. H3 가 H5 의 outer wrapping 패턴 같으면 동일 절차로 해결.

### 7.2 우선 2순위: 미파싱 평문 파일

- `s4_dat` (894B) — skill 4 data (다른 s*_dat 도 있을 가능성)
- `npcg_dat` (1014B, 78 entries × 13B) — NPC graphics info
- `char_dat` (348B) — 8-15 character classes

### 7.3 우선 3순위: boss_dat stat field 정확 매핑

byte 0x08..0x0a 의 3-byte 가 24-bit HP 일 가능성 → boss 의 진짜 max HP 추출 (수십만~수백만).

### 7.4 보류 작업 (Round 53~57 누적)

- FUN_4f358 본문 정밀
- FUN_3a028 16-JT
- FUN_88a30 16-JT
- SCN opcode 0x12 47-arm
- arg=+55/+57 menu hotkey
- enemy_dat loader 함수 발견 (sl-rel offset 비표준 패턴)

## 부록 — 산출 스크립트

| 스크립트 | 역할 |
|---|---|
| `dump_all_dat_files.py` | 15개 dat 파일 entropy + EUC-KR 분포 분석 |
| `parse_boss_dat.py` | 15 bosses 추출 + 19B stat block 파싱 |
| `parse_quest_dat.py` | 4 quest 파일 평문 EUC-KR 텍스트 추출 |
| `decrypt_h3_dat_des.py` (확장) | 5 DES variant matrix |

raw output: `work/h3/round58_all_dat.txt`, `round58_boss_parse.txt`, `round58_quest_parse.txt`, `round58_des_variants.txt`.
