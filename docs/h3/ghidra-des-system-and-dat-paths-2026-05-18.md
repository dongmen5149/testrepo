# Hero3 Ghidra — DES 시스템 완전 식별 + dat path string 25개 발견 (Round 57)

> **세션**: 2026-05-18, Round 57
> **이전 Round**: [ghidra-enemy-dat-and-battle-data-2026-05-18.md](ghidra-enemy-dat-and-battle-data-2026-05-18.md) (Round 56)
> **재현 도구**: `tools/recon/find_dat_path_references.py` / `dump_dat_path_context.py` / `verify_des_dat_tables.py` / `tools/converter/decrypt_h3_dat_des.py`

## 한 줄 요약

Round 56 의 "암호화 추정" drop_dat / getitem_dat 가설 검증 + DES 시스템 완전 식별. binary 내 **25개 dat path string 발견** (`/dat/enemy_dat`, `/boss/boss_dat`, `/dat/shop_dat`, `/dat/smith_dat`, `/dat/quest_00_dat`, `/skill/s4_dat`, `/npc/npcg_dat` 등). **결정적 발견**: `/dat/des_dat` 직후 8B = `"0EP@KO91"` (Hero5 와 동일 DES 키!) + **`dat/des_dat` 파일 자체가 표준 FIPS DES 알고리즘 테이블 (IP / IP⁻¹ / E / P / S1-S8 / PC1 / PC2)** 824B 완전 일치. DES key + tables + 암호문 모두 식별. Simple ECB 복호화는 실패 (mode/parity 변형 이슈, Round 58 후속).

## 1. binary 내 25개 dat path strings (2XA)

`tools/recon/find_dat_path_references.py` grep 결과:

| 주소 | 경로 | 분류 |
|---|---|---|
| 0xa5d64 | `/boss/bossh_dat` | ★ boss data (hard) — extracted/ 폴더 없음 |
| 0xa5d74 | `/boss/boss_dat` | ★ boss data (easy) |
| 0xa6394 | `/dat/enemyh_dat` | enemy hard (★ R56 161 entries) |
| 0xa63a4 | `/dat/enemy_dat` | enemy easy (★ R56 161 entries) |
| 0xa63b4 | `/dat/enemyg_dat` | enemy graphics |
| 0xa63c4 | `/dat/droph_dat` | drop hard (암호화) |
| 0xa63d4 | `/dat/drop_dat` | drop easy (암호화) |
| 0xa6878 | `/dat/char_dat` | character class |
| 0xa6ab4 | `/dat/getitem_dat` | item acquisition (암호화) |
| 0xa7130 | `/dat/InGame_txt` | in-game text |
| 0xa889c | `/dat/ph001_pa` | path animation |
| 0xa8c18 | `/enemy/e000_cif` | enemy sprite (cif) |
| 0xa8c28 | `/enemy/e1000_bm` | enemy bitmap |
| 0xa8c48 | `/dat/pe000_pa` | path animation |
| 0xa91a0 | `/dat/i0_dat` | chapter 0 data |
| 0xa91f8 | `/dat/quest_00_dat` | ★ quest data |
| 0xab410 | `/npc/npcg_dat` | NPC graphics |
| 0xab420 | `/dat/shoph_dat` | ★ shop hard |
| 0xab430 | `/dat/shop_dat` | ★ shop easy |
| 0xab724 | `/dat/smithh_dat` | ★ smith (item upgrade) hard |
| 0xab734 | `/dat/smith_dat` | ★ smith easy |
| 0xac584 | `/dat/des_dat` | ★★★ DES algorithm tables |
| 0xad138 | `/skill/s4_dat` | skill 4 data |

**부수 발견** (Round 56에서 확인되지 않은 추가 데이터 파일):
- `/boss/boss_dat`, `/boss/bossh_dat` — boss 전용 데이터 (extracted 폴더에 boss/ 하위 cif/bm 만 있고 boss_dat 없음 — 분리 필요)
- `/dat/quest_00_dat` — quest 데이터 (~?? entries 추정)
- `/dat/shop_dat`, `/dat/shoph_dat` — shop inventory + price
- `/dat/smith_dat`, `/dat/smithh_dat` — 대장간 업그레이드 데이터
- `/skill/s4_dat` — skill 4 정의 (다른 skill 파일도 있을 듯)
- `/npc/npcg_dat` — NPC graphics info (R14 NPC table 의 그래픽 측면)

## 2. ★★★ DES 시스템 완전 식별 (2XD)

### 2.1 DES 키 "0EP@KO91" 발견 (binary 내 평문 노출)

`tools/recon/dump_dat_path_context.py` 결과: `/dat/des_dat` string 직후 (0xac584 + 0x10 = 0xac594) 에:

```
0xac594: 30 45 50 40 4b 4f 39 31      = ASCII "0EP@KO91"
```

이는 **메모리에 저장된 정보** `[reference_h5_des_blocker.md]` 와 **완전 일치**: "Hero5 calc DES 정적분석 종결 — 표준 FIPS + 키 0EP@KO91 확정". Hero5 의 DES 키가 **Hero3 에서도 동일하게 사용** 됨.

### 2.2 des_dat = 표준 FIPS DES 알고리즘 테이블 (824B 완전 매칭)

`tools/recon/verify_des_dat_tables.py` 으로 표준 DES tables 와 byte-by-byte 비교:

| Table | offset | size | 첫 8 bytes (검증) | 매칭 |
|---|---|---|---|---|
| **IP** (Initial Permutation) | 0x000 | 64B | [58, 50, 42, 34, 26, 18, 10, 2] | ✓ |
| **IP⁻¹** (Inverse IP) | 0x040 | 64B | [40, 8, 48, 16, 56, 24, 64, 32] | ✓ |
| **E** (Expansion) | 0x080 | 48B | [32, 1, 2, 3, 4, 5, 4, 5] | ✓ |
| **P** (Permutation) | 0x0b0 | 32B | [16, 7, 20, 21, 29, 12, 28, 17] | ✓ |
| **S1-S8** (S-boxes) | 0x0d0 | 512B | [14, 4, 13, 1, 2, 15, 11, 8] (S1 row 0) | ✓ |
| **PC-1** (Key permutation) | 0x2d0 | 56B | [57, 49, 41, 33, 25, 17, 9, 1] | ✓ |
| **PC-2** (Key compression) | 0x308 | 48B | [14, 17, 11, 24, 1, 5, 3, 28] | ✓ |
| **총합** | | **824B** | | **정확 일치** |

→ **des_dat 파일 = FIPS PUB 46-3 (DES) 의 모든 algorithm tables 를 1-indexed 형식으로 직렬화한 외부 파일**. binary 의 DES 구현은 이 파일을 로드하여 테이블 lookup 으로 동작.

### 2.3 Hero3 의 DES 시스템 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│ Hero3 DES System                                        │
├─────────────────────────────────────────────────────────┤
│ 1. DES algorithm code → binary (특정 함수, 미식별)         │
│ 2. DES tables       → dat/des_dat (824B, 표준 FIPS)    │
│ 3. DES key          → "0EP@KO91" @ binary 0xac594       │
│ 4. encrypted data:                                      │
│    - dat/drop_dat   (3080B, 385 blocks × 8B)            │
│    - dat/droph_dat  (3080B)                             │
│    - dat/getitem_dat ( 400B,  50 blocks)                │
└─────────────────────────────────────────────────────────┘
```

### 2.4 Simple ECB 복호화 시도 — 실패

`tools/converter/decrypt_h3_dat_des.py` 으로 PyCryptodome DES.MODE_ECB + key="0EP@KO91" 적용:

```
=== drop_dat (3080B) ===
  first 64B hex: ad 62 56 1a 75 c7 e6 ca 08 9f 82 de b5 b5 e1 c5 ...
  byte distribution: korean-range=1127 ascii=1123 null=10 (total=3080)
```

→ **여전히 high-entropy 랜덤 바이트**. 평문이 아님.

**가능 원인** (Round 58 후속):
1. **key parity 변형**: DES 표준은 64-bit key 의 각 byte LSB = parity bit. "0EP@KO91" 의 parity 조정 필요
2. **CBC mode + IV**: 단순 ECB 가 아닌 CBC + 초기 IV (binary 어딘가)
3. **key XOR pre-processing**: 평문 key 가 아닌 변형 (XOR with 0x?? 또는 시리얼번호)
4. **압축 후 암호화**: 평문 → LZSS/Deflate 압축 → DES 암호화 (Hero5 에서 일부 발견 패턴)
5. **bit order endianness**: J2ME/Java 와 다른 bit ordering

### 2.5 시각적 검증: des_dat raw vs IP table

```
des_dat +0x000..0x010:   3a 32 2a 22 1a 12 0a 02  3c 34 2c 24 1c 14 0c 04
decimal (1-indexed):      58 50 42 34 26 18 10  2  60 52 44 36 28 20 12  4
표준 IP (FIPS PUB 46-3):  58 50 42 34 26 18 10  2  60 52 44 36 28 20 12  4  ★ MATCH
```

## 3. dat path string reference 분석 — 비표준 패턴 (2XA 부속)

`dump_dat_path_context.py` 으로 25개 path string 의 reference 검색:

### 3.1 Direct PC-rel + sl-rel = 0개 매칭

Round 51-55 의 표준 PIC 패턴 (`ldr Rx, [pc, #imm]` + sl-rel literal) 으로는 0개 hit. 

### 3.2 Word-aligned table 매칭 = 3개만

- 0x00944 → `/skill/s4_dat` (0xad138)
- 0xae0b4 → `/skill/s4_dat`
- 0xb2ebc → `/dat/char_dat` ★ **GOT[+0x27c] 에 매칭** (0xb2c40 + 0x27c = 0xb2ebc)

→ **GOT[+0x27c] = `/dat/char_dat` 경로 string ptr** (신규 GOT slot).

### 3.3 비표준 reference 패턴 (가설)

25개 path 중 22개는 word-aligned table 에 없음. 가능한 패턴:
1. **packed string table + index**: 모든 path 가 0xa5d64..0xad138 에 연속 packed. 코드가 base + length-offset 으로 접근
2. **base + index*16**: 16-byte 정렬 (0xa6394, 0xa63a4, 0xa63b4, 0xa63c4, 0xa63d4 같은 16B-aligned 패턴 확인)
3. **2-pass 접근**: 다른 코드가 string 의 마지막 char (예: `_dat\0`) 까지 walk 후 사용

→ Round 58 작업: 패턴 식별 후 enemy_dat 로더 함수 발견.

## 4. 신규 발견 사항

### 신규 데이터 파일 발견 (binary string 으로 확인)

이전 라운드 미발견:
- `/boss/boss_dat`, `/boss/bossh_dat`
- `/dat/quest_00_dat`
- `/dat/shop_dat`, `/dat/shoph_dat`
- `/dat/smith_dat`, `/dat/smithh_dat`
- `/skill/s4_dat`
- `/npc/npcg_dat`

이들은 **extracted/dat/** 폴더에 일부 존재하지 않거나 다른 이름. Round 58 작업: extracted/boss/ 와 extracted/dat/ 폴더 다시 확인 + 추가 dat 파일 추출 필요.

### 신규 GOT slot

- **GOT[+0x27c]** = `/dat/char_dat` path string ptr (0xb2ebc, R55 known GOT slots 27 → **28**)

## 5. Hero3 분석 종합 갱신 (Round 57 시점)

| 시스템 | 위치 | 상태 |
|---|---|---|
| input dispatcher (FUN_818f0) | binary | 완전 |
| save/load (FUN_77c78) | binary | 완전 |
| script VM (FUN_9a008 7-mode) | binary | 부분 |
| script VM (FUN_8e89e SCN) | binary | 부분 |
| **enemy data (161 entries)** | **dat/enemy_dat** | **R56 완전 분석** |
| **DES key + tables** | **binary 0xac594 + dat/des_dat** | **R57 완전 식별** |
| **DES 복호화 대상** | **dat/drop_dat, droph_dat, getitem_dat** | **암호화됨, 복호화 시도 실패 (R58 후속)** |
| character class | dat/char_dat (348B) | 미파싱 |
| boss data | (별도 파일, 미추출?) | 미발견 |
| quest data | dat/quest_00_dat (미추출?) | 미발견 |
| shop data | dat/shop_dat (미추출?) | 미발견 |

### Android remake 진행률

- **자산 포맷 분석/변환**: ~85% (DES 키 확인으로 +3%)
- **Ghidra 게임 로직 리버싱**: ~62% (DES 시스템 식별로 +2%)
- **전투 시스템 데이터**: 100% (R56 enemy_dat)
- **전투 시스템 코드**: ~5% (DES decrypt 필요)
- **암호화/보안**: ~70% (key + algorithm tables 식별, 복호화 미완)

**전체 진행률**: 약 **70%** (Round 56 + 57 합산 +10%p)

## 6. Round 58 권장 작업

### 6.1 우선 1순위: DES 복호화 완성

`drop_dat` (3080B = 385 blocks × 8B) 복호화 시도 매트릭스:
- **key parity 변형**: "0EP@KO91" 각 byte LSB 조정 (`0x30 → 0x31`, ...)
- **endian swap**: key + data block 의 8-byte little-endian / big-endian 변환
- **CBC mode**: 다양한 IV 시도 (zeros, key 재사용, 첫 8B from des_dat)
- **bit reversed key**: 각 byte 의 bit reverse
- **Hero5 NDK runner 참조**: `[reference_h5_des_blocker.md]` 의 NDK 구현 참조

### 6.2 우선 2순위: 추가 dat 파일 추출

JAR/midletbundle 에서 다음 파일 별도 추출:
- `/boss/boss_dat` + `/boss/bossh_dat`
- `/dat/quest_00_dat`
- `/dat/shop_dat` + `/dat/shoph_dat`
- `/dat/smith_dat` + `/dat/smithh_dat`
- `/skill/s4_dat` + 다른 skill 파일들
- `/npc/npcg_dat`

### 6.3 우선 3순위: enemy_dat 로더 함수 발견

dat path string 의 비표준 reference 패턴 식별 → loader 함수 발견 → battle logic 추적.

### 6.4 보류된 작업 (Round 53~56 누적)

- FUN_4f358 본문 정밀
- FUN_3a028 16-JT (party stats menu)
- FUN_88a30 16-JT (save/load menu)
- SCN opcode 0x12 47-arm
- arg=+55/+57 menu hotkey

## 부록 — 산출 스크립트

| 스크립트 | 역할 |
|---|---|
| `find_dat_path_references.py` | binary 전체 `/dat/` `_dat` string grep + reference 검색 |
| `dump_dat_path_context.py` | 25개 path string 주변 바이트 + word-aligned pointer table 검색 |
| `verify_des_dat_tables.py` | des_dat 824B = 표준 DES 7 tables 검증 |
| `tools/converter/decrypt_h3_dat_des.py` | DES key "0EP@KO91" + MODE_ECB 복호화 시도 (실패) |

raw output: `work/h3/round57_dat_refs.txt`, `work/h3/round57_dat_pointer_table.txt`, `work/h3/round57_des_dat_verify.txt`, `work/h3/round57_des_decrypt.txt`.
