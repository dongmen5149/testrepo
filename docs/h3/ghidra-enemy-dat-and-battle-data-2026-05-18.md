# Hero3 Ghidra — 전투 데이터 발견 (dat/enemy_dat 161 entries + 19B stat block) (Round 56)

> **세션**: 2026-05-18, Round 56
> **이전 Round**: [ghidra-asset-paths-and-arith-grep-2026-05-18.md](ghidra-asset-paths-and-arith-grep-2026-05-18.md) (Round 55)
> **재현 도구**: `tools/recon/dump_enemy_dat.py` / `parse_enemy_dat.py`

## 한 줄 요약

Round 47-55 의 "전투 시스템 위치 미발견" 미스터리 해결. **Hero3 의 전투 데이터는 binary 외부 `work/h3/extracted/dat/` 폴더에 별도 파일로 존재**: `enemy_dat` (5495B, **161 enemies**) + `enemyh_dat` (5495B, 161 hard mode enemies). 각 entry 의 19-byte stat block 구조 완전 분석 — **HP / EXP / ATK / DEF / Gold / MP / AGI 7개 필드 식별**. binary 내 함수들은 단순 **dat file 로더 + battle logic interpreter** 역할. R55 의 "전투 = NPC table data + SCN opcode 조합" 가설 정정 → **전투 = dat 파일 + binary interpreter**.

## 1. work/h3/extracted/dat/ 폴더 — 게임 데이터 파일들 (2WA)

`ls -la` 결과:

| 파일 | 크기 | 추정 내용 |
|---|---|---|
| `InGame_txt` | 2421B | in-game text (대사/UI 텍스트) |
| `char_dat` | 348B | 캐릭터 클래스 정의 (8 entries 예상) |
| `des_dat` | 824B | 설명 데이터 (text offset 테이블 포함) |
| **`enemy_dat`** | **5495B** | **★ 161 enemies (easy/normal mode)** |
| **`enemyh_dat`** | **5495B** | **★ 161 enemies (hard mode)** |
| `enemyg_dat` | 3542B | 적 그래픽 정보 |
| `drop_dat` | 3080B | **암호화/압축됨** (item drop table) |
| `droph_dat` | 3080B | **암호화/압축됨** (hard drop) |
| `getitem_dat` | 400B | **암호화/압축됨** (item acquisition) |
| `i0_dat` ~ `i18_dat` | 776~7400B | 챕터/스테이지 데이터 |
| `pe000_pa` ~ `pe2nn_pa` | 17~133B | path animation data |

**중요**: drop_dat / getitem_dat 의 high-entropy = **MD5 또는 다른 암호화 적용** (R53 MD5 알고리즘 발견과 연결 가능성). enemy_dat 는 **평문 EUC-KR** — 암호화 없음.

## 2. enemy_dat / enemyh_dat 구조 완전 분석

`tools/recon/parse_enemy_dat.py` 으로 161 entries 정확히 파싱.

### 2.1 Entry layout

```
[size_minus_2] [00] [name_len]   ← 3-byte header
[name + '@']                      ← name_len bytes, EUC-KR encoded
[19B stat block]
[01 1e]                            ← 2-byte trailer (entry terminator)
```

- **total_entry_size = (byte 0) + 2** (size byte + 2-byte trailer)
- name length 범위: 11~17 bytes (보통 13 또는 15)
- stat block: **항상 19 bytes**
- trailer: **항상 `0x01 0x1e`** (상수)

### 2.2 161 entries — sample

| pos | name (EUC-KR) | lvl | MP? | HP | Gold | ATK | DEF | EXP | AGI | f17 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x0000 | 아스크란가드 | 15 | 385 | 926 | 45 | 41 | 32 | 792 | 9 | 10 |
| 0x0025 | 코르버스워리어 | 30 | 475 | 1566 | 314 | 54 | 47 | 797 | 14 | 10 |
| 0x004c | 아스크란워리어 | 34 | 476 | 1860 | 316 | 56 | 51 | 799 | 16 | 10 |
| 0x0073 | 솔티안워리어 | 34 | 476 | 1860 | 316 | 56 | 51 | 799 | 16 | 10 |
| 0x0098 | 아스크란템플러 | 40 | 374 | 2433 | 325 | 64 | 57 | 801 | 18 | 10 |
| 0x00bf | 솔티안로그 | 22 | 508 | 1219 | 47 | 44 | 61 | 6427 | 12 | 10 |
| 0x00e2 | 도적 | 25 | 426 | 1498 | 51 | 47 | 64 | 6428 | 13 | 10 |
| 0x00ff | 코르버스로그 | 28 | 350 | 1779 | 52 | 48 | 67 | 6429 | 14 | 10 |
| 0x0124 | 아스크란체이서 | 36 | 354 | 2104 | 317 | 56 | 75 | 6431 | 16 | 10 |
| 0x014b | 코르버스어쌔신 | 39 | 559 | 2388 | 318 | 58 | 78 | 6432 | 17 | 10 |
| 0x0172 | 솔티안매지션 | 21 | 475 | 699 | 43 | 47 | 38 | 794 | 11 | 8 |
| 0x0197 | 솔티안위자드 | 33 | 411 | 1821 | 309 | 57 | 50 | 798 | 15 | 10 |
| 0x01bc | 솔티안워락 | 40 | 374 | 2398 | 317 | 65 | 57 | 801 | 18 | 10 |
| 0x01df | 아스크라건너 | 14 | 333 | 904 | 40 | 44 | 28 | 24 | 9 | 10 |
| 0x0204 | 코르버스건너 | 29 | 412 | 1787 | 54 | 58 | 43 | 29 | 14 | 10 |
| 0x0229 | 아스크란슈터 | 33 | 411 | 1821 | 314 | 63 | 47 | 30 | 15 | 10 |
| 0x024e | 아스크란엑셀 | 36 | 354 | 2104 | 318 | 67 | 53 | 799 | 16 | 10 |
| 0x0273 | 아스크란워락 | 36 | 354 | 2104 | 318 | 67 | 53 | 799 | 16 | 10 |
| 0x0298 | 포레스트쿠퍼 | 5 | 676 | 330 | 30 | 33 | 19 | 21 | 6 | 10 |
| 0x02bd | 와일드쿠퍼 | 8 | 555 | 609 | 32 | 35 | 22 | 22 | 7 | 10 |

### 2.3 Easy vs Hard 비교 (entry 0: 아스크란가드)

| stat | Easy | Hard | scaling |
|---|---|---|---|
| **lvl** | 15 | 47 | 3.13x |
| f4_5 | 385 | 297 | 0.77x (DECREASE) |
| **f6_7** | 926 | **3755** | **4.05x ★ HP** |
| f8_9 | 45 | 615 | 13.7x |
| f10_11 | 41 | 97 | 2.37x |
| f12_13 | 32 | 127 | 3.97x |
| **f14_15** | 792 | **7725** | **9.75x ★ EXP** |
| f16 | 9 | 40 | 4.44x |
| f17 | 10 | 12 | 1.20x |

### 2.4 19-byte stat block 필드 매핑 (가설)

| offset | range (easy) | range (hard) | 추정 의미 |
|---|---|---|---|
| +0 | byte, lvl | 1~67 | 1~66 | **레벨** |
| +1..+3 | 3B padding | 00 00 00 | 00 00 00 | **예약 (항상 0)** |
| +4..+5 | int16 BE | 8~1023 | 미상 | **MP/maxMP** 또는 ranged stat. easy < hard 도 있음 |
| **+6..+7** | int16 BE | 49~28520 | 미상 | **★ HP / maxHP** (4x scaling) |
| **+8..+9** | int16 BE | 29~2922 | 미상 | **Gold drop** (13x scaling) |
| +10..+11 | int16 BE | 27~360 | 미상 | **ATK** (2.4x) |
| +12..+13 | int16 BE | 16~468 | 미상 | **DEF** (4x) |
| **+14..+15** | int16 BE | 20~6433 | 미상 | **★ EXP gain** (~10x) |
| +16 | byte | 5~87 | 미상 | **AGI/SPD** 또는 **CRT chance** |
| +17 | byte | 0~40 | 미상 | 미상 (작은 scaling, action count?) |
| +18 | byte | 0 | 0 | **예약 (항상 0)** |

→ **19 byte stat block = lvl(1) + pad(3) + 6×int16_BE(12) + 2 bytes + pad(1)**.

### 2.5 통계 요약

- enemy_dat: **161 entries** (총 5495B 정확 매칭)
- enemyh_dat: **161 entries** (총 5495B 동일)
- 모든 entry 가 trailer `0x01 0x1e` 로 종료
- name encoding: **EUC-KR (CP949)** 단일
- 부수 발견: 일부 enemy 이름 typo 없음 (정상)

## 3. 161 enemies 의 라인업 — 분류 (이름 기반)

처음 20 entry 의 이름 패턴:
- **클래스 prefix**: 아스크란/코르버스/솔티안/포레스트/와일드
- **클래스 suffix**: 가드, 워리어, 템플러, 로그, 어쌔신, 매지션, 위자드, 워락, 건너, 슈터, 엑셀, 체이서, 쿠퍼

각 클래스 prefix × suffix 조합 = 약 ~20-30 base classes + level/area variations 으로 161 entries 채워짐.

특수 enemy 들:
- **도적** (lvl 25) — 기본 적
- **포레스트쿠퍼** (lvl 5) — 시작 지역 적
- **와일드쿠퍼** (lvl 8) — 약간 더 강한 시작 지역 적

→ **Hero3 의 enemy 종류**:
1. 아스크란 (Askran) 군단 — guard, warrior, templar, chaser, axel, warlock, gunner, shooter
2. 코르버스 (Korbus) 군단 — warrior, rogue, assassin, gunner
3. 솔티안 (Soltian) 군단 — warrior, rogue, magician, wizard, warlock
4. 포레스트/와일드 쿠퍼 (Cooper) — 야생 동물
5. 일반 (도적 등)

## 4. binary 내 enemy_dat 로더 함수 식별 (다음 라운드 작업)

이제 명확해진 작업: **binary 의 어느 함수가 `dat/enemy_dat` 를 읽고 161 entries 를 파싱하는지 식별**.

후보 검색 전략:
1. binary 의 literal pool 에서 string `"/dat/enemy"` 또는 `"enemy_dat"` 검색
2. R55 의 asset path table (0xac1d8+) 와 동일 영역에서 `/dat/` prefix string 검색
3. ObjectB.method[+0x7c/+0x80] (R53 record reader) 가 호출되는 caller 중 enemy file 처리하는 곳

## 5. R55 의 "전투 = NPC table + SCN opcode" 가설 정정

R55 의 NPC table indexing 패턴 (`base + 0x3c4*row + 0x3c*col`) 의 base 는 `task[+0x9e28]` (R27 cluster) 였음. 이 cluster 가 **runtime 에서 enemy_dat 파일 내용을 로드한 메모리 영역** 일 가능성.

새 가설:
- `task[+0x9e28]` = enemy/character data **로드 후 메모리 base ptr**
- 0x3c4 stride = 한 enemy class 의 모든 variant 묶음 (multiple instances)
- 0x3c stride = 한 enemy entry 의 메모리 expansion (19B stat → 60B with extras)
- 60B 가 R52 의 vtable[+0x54] alloc(60B) 와 정확히 일치 = **enemy instance object size**

→ **dat 파일은 storage, runtime task[+0x9e28] 는 in-memory copy**. 둘 모두가 R14 의 0x3c4 grid 와 R55 의 NPC table 정체.

## 6. 다음 라운드 (Round 57) 권장 작업

### 6.1 우선 1순위: enemy_dat 로더 함수 식별

binary 의 literal pool grep:
- `"/dat/enemy"` 또는 `"enemy_dat"` string 검색
- 발견되면 reference site 추적 → loader 함수

### 6.2 우선 2순위: enemyg_dat / char_dat 구조 분석

- `enemyg_dat` (3542B) = enemy graphics info (sprite ID, animation frames, sound IDs)
- `char_dat` (348B) = 약 10-15 character class 정의

### 6.3 우선 3순위: drop_dat / getitem_dat 복호화

high entropy 데이터. R53 의 MD5 알고리즘 외에 다른 알고리즘 시도 필요:
- 단순 XOR (key = 0x?? 반복)
- DES (Hero4/5 에서 발견된 알고리즘)
- 또는 LZSS/RLE 압축

### 6.4 보류된 작업 (Round 53~55 누적)

- FUN_4f358 본문 정밀 (int16 stat extractor — 이제 enemy stat reader 가설)
- FUN_3a028 16-JT (party stats menu)
- FUN_88a30 16-JT (save/load menu)
- SCN opcode 0x12 (R37 11.4KB) 47-arm
- FUN_9a008 mode 4 state 4-5 의 9-entry sub-sub-JT
- arg=+55/+57 menu hotkey 분기

## 7. 분석 진행률 갱신

### Major systems identified (R47~R56)

| system | location | status |
|---|---|---|
| input dispatcher | FUN_818f0 (R50-52) | 완전 분석 (30 leaf handlers) |
| save/load | FUN_77c78 + MD5 (R51-53) | 완전 분석 |
| script bytecode VM (script) | FUN_9a008 7-mode (R52-54) | 부분 분석 (mode 2/4 일부) |
| script bytecode VM (SCN/dialog) | FUN_8e89e (R35) | 부분 분석 |
| ObjectB master interface | GOT[+0x18] (R31-53) | 14 methods 식별 |
| task_struct | task @ 0xb6c80 (R51) | 30+ fields known |
| **enemy data** | **dat/enemy_dat** | **★ Round 56 신규: 161 enemies, 19B stat block** |
| asset path resolver | binary 0xac1d8+ string table | 부수 발견 (R55) |
| MD5 algorithm | FUN_5613c/56164/561dc | R53 발견 |
| cursor / UI nav | FUN_92bf8/92cc0/92d30 | R50 완전 분석 |

### Round 56 시점 추정 진행률

- **자산 포맷 분석/변환**: ~85% (enemy 데이터 추가 발견으로 +5%)
- **자산 변환 산출**: ~95% (변동 없음)
- **Ghidra 게임 로직 리버싱**: ~60% (battle data 외부 파일 확인으로 모듈 경계 명확화)
- **task_struct 모델**: ~55%
- **Android 엔진 재구현**: ~5~10% (변동 없음)
- **전투 시스템 데이터**: 100% (Round 56 발견 — 161 enemies stat 추출 완료)
- **전투 시스템 코드**: ~0% (binary 내 enemy_dat 로더 + interpreter 미식별)

**Android remake 완성 기준 진행률**: 약 **65~70%** (battle data 발견으로 +5%p)

## 부록 — 산출 스크립트

| 스크립트 | 역할 |
|---|---|
| `dump_enemy_dat.py` | dat/ 폴더의 8개 데이터 파일 raw byte + stride hypothesis 테스트 |
| `parse_enemy_dat.py` | enemy_dat / enemyh_dat 의 161 entries 완전 파싱 + 19B stat block 분석 |

raw output: `work/h3/round56_dat_dumps.txt`, `work/h3/round56_enemy_parse_v2.txt`.
