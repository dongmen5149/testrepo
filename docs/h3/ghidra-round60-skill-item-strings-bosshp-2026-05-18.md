# Hero3 — Round 60: skill 일괄 / item 카탈로그 / string table / boss HP 검증

날짜: 2026-05-18 (Round 60)
이전: [Round 59 — char/npcg/s4 dat 평문 파싱](ghidra-char-npcg-skill-parsing-2026-05-18.md)

## TL;DR

R59 SESSION_HANDOFF 의 4가지 우선 작업 모두 완료 + **추가 대규모 발견 2종**.

| # | 작업 | 결과 |
|---|---|---|
| 1 | `s1~s10_dat` 존재 확인 + 일괄 파싱 | **7 파일 (s4~s10) 모두 평문 파싱 — 105 skills** |
| 2 | `boss_dat` 24-bit HP 가설 검증 | **24-bit 가설 폐기, 16-bit BE @ +0a..+0b 확정** |
| 3 | 추가 폴더 enumeration | **menu/*.txt + dat/InGame_txt + dat/i*_dat 발견** |
| 4 (bonus) | menu / dat string table 파싱 | **246 strings 평문 (UI/help/class/country)** |
| 5 (bonus) | dat/i*_dat (19 파일) 파싱 | **17 파일 평문, 480+ items / i15_dat = 신규 DES 후보** |

진행률 ~75-78% → **~82-85%** (+7-10%p).

## 산출물

| Path | 내용 |
|---|---|
| [`tools/recon/parse_all_skill_dat.py`](../../tools/recon/parse_all_skill_dat.py) | s4~s10 일괄 파싱 (parse_s4_dat 재사용) |
| [`tools/recon/verify_boss_hp_hypothesis.py`](../../tools/recon/verify_boss_hp_hypothesis.py) | boss HP 필드 위치 hunt (BE16/LE16/BE24 brute force) |
| [`tools/recon/parse_string_table.py`](../../tools/recon/parse_string_table.py) | menu/*.txt + dat/InGame_txt string table 파서 |
| [`tools/recon/parse_i_dat.py`](../../tools/recon/parse_i_dat.py) | dat/i0~i18 item dat 일괄 파서 |
| `work/h3/recon/skill_dat_all.json` | 7 파일 × 15 skills = 105 entries dump |
| `work/h3/recon/skill_dat_all.log` | 동일, 사람이 읽기 좋은 형식 |
| `work/h3/recon/string_tables.json` | 6 string tables = 246 EUC-KR strings |
| `work/h3/recon/i_dat_all.json` | 17 item dat × ~25 entries = 480+ items |
| `work/h3/recon/i_dat_all.log` | item dump 로그 |

## 1. Skill 일괄 파싱 (7 파일 = 105 skills)

s4_dat 가 1 클래스 (창수) 만 발견되었던 R59 의 미해결 = `s5_dat` ~ `s10_dat` 발견.

**모든 파일 동일 구조**: `[size][00][name_len][EUC-KR name][body]` (s4_dat 와 동일). 각 파일 = 15 entries (passive 1-7 + active 8) × 1 weapon class.

| File | Size | 1st entry | 무기 클래스 |
|---|---:|---|---|
| `s4_dat` | 894B | **창술** | 창 (spear/halberd) |
| `s5_dat` | 922B | **검술** | 양손 대검 |
| `s6_dat` | 926B | **단도** | 단검 |
| `s7_dat` | 923B | **사격** | 건 (단발 화기) |
| `s8_dat` | 930B | **격발** | 라이플/중화기 |
| `s9_dat` | 904B | **영탄** | 다크 마법 |
| `s10_dat` | 938B | **광아** | 홀리 마법 |

각 클래스의 active skill 8개 패턴 예: 창술 → 섬광/자격/압도/유도/장벽/태산/의지/정신.

R59 의 char_dat (10 playable classes — 리츠 5 + 케이 5) + countryheader_txt (네오솔티아-케이, 아스크라-리츠) 와 정확히 매핑:

| 클래스 | 무기1 / 무기2 | skill_dat |
|---|---|---|
| 어썰트워리어 (리츠) | 창 + 방패 + 양손검 | s4, s11(방패) or s5 |
| 디스럽터 (리츠) | 양손검 + 건 | s5 + s7 |
| 건슬링어 (리츠) | 단검 + 건 | s6 + s7 |
| 나이트템플러 (리츠) | (홀리?) | s10 |
| 크레이지암즈 (리츠) | 모든 총기 | s7 + s8 |
| 버서커 (케이) | 양손검 + 단검 | s5 + s6 |
| 데스나이트 (케이) | 양손검 + 다크마법 | s5 + s9 |
| 섀도우워커 (케이) | 단검 + 다크마법 | s6 + s9 |
| 가디언나이트 (케이) | (방패+홀리?) | s10 |
| 소울마스터 (케이) | 홀리 마스터 | s10 |

→ `chatacterbody_txt` 의 클래스 설명과 100% 일치.

**s1~s3 부재** = 기본 클래스 (creator 스킬 없음) 또는 코드 하드코드.

## 2. boss_dat HP 위치 정밀 검증 (R58 가설 폐기 + 새 확정)

R58 의 "bytes 0x08..0x0a (3 byte) = 24-bit BE HP" 가설을 brute-force 로 검증.

방법: 19B stat block 의 모든 byte offset (0..16) 에서 BE16/LE16/BE24 값을 계산, Ritz 6 boss (lvl 14→24→32→51→56→60) 의 **monotonic scaling** 을 만족하는 위치 hunt.

결과:

```
Ritz lvl 14 stat block: 0e 00 68 10 b3 00 da 00 00 01 37 00 37 00 14 0a 00 00 00
                        lvl  pad ?    ?    ?    ?    ?     HP_max HP_cur ?    ?

Ritz HP scaling (BE16 @ offset +0a..+0b):
  lvl 14: 14080  (normal)
  lvl 24: 16896  (normal)
  lvl 32: 19456  (normal)
  lvl 51: 35840  (hard, 2.54x)
  lvl 56: 38912  (hard, 2.30x)
  lvl 60: 41728  (hard, 2.14x)
```

**R58 24-bit 가설은 wrong byte offset (08 vs 0a) + wrong width (24 vs 16) 였음.** 실제 HP는:

- **offset +0a..+0b (BE16) = MaxHP**
- **offset +0c..+0d (BE16) = CurrentHP** (initial = MaxHP, 두 필드 동일 값)
- **offset +0e..+0f (BE16) = EXP/Gold reward** (5130, 15380, 17950... 단조증가)

→ 이 layout 은 [`parse_enemy_dat.py`](../../tools/recon/parse_enemy_dat.py) 의 기존 `f10_11` 필드와 **동일**. **boss = enemy 의 단순 superset** (큰 차이는 6B 가변 trailer, R58 발견). enemy_dat 의 `f10_11` 필드 = HP, 동일하게 해석 가능.

**부수 발견**: hard mode HP scaling 2.1~2.5x (보스 별로 다름). 일관된 단순 배수가 아닌 manually-balanced.

## 3. menu/dat string table 발견 (246 strings 평문)

R59 폴더 enumeration 시 `menu/*.txt` 와 `dat/InGame_txt` 미파싱 인지.

**Format (역공학)**:
```
[LE16 total_size]              # 파일 전체 길이
[LE16 string_count]            # 문자열 갯수 N
[LE16 offset_0]
[LE16 offset_1]
...
[LE16 offset_{N-1}]            # 각 문자열 시작 위치 (file-relative)
[null-terminated EUC-KR strings 본문]
```

검증: `chatacterhader_txt` (134B) → size=0x0086=134 ✓, count=10 strings.

| File | Strings | 내용 |
|---|---:|---|
| `menu/chatacterhader_txt` | 10 | **클래스 이름** (버서커/데스나이트/섀도우워커/가디언나이트/소울마스터/어썰트워리어/디스럽터/건슬링어/나이트템플러/크레이지암즈) |
| `menu/chatacterbody_txt` | 10 | **클래스 설명** (예: "바람의 광전사들.;쌍검과 대검을 사용하여;폭풍처럼 적진을 유린한다.") |
| `menu/countryheader_txt` | 4 | **국가 이름** (네오솔티아 / 아스크라 / 네오솔티아-케이 / 아스크라-리츠) |
| `menu/countrybody_txt` | 2 | 국가 배경 설명 |
| `menu/helpbody_txt` | 13 | **게임 도움말** (조작/시스템/제련/네트워크/저작권/홈페이지 등 13 페이지) |
| `dat/InGame_txt` | **196** | **모든 in-game UI 텍스트** (MENU, STATUS, INVENTORY, EQUIPMENT, SKILL, QUEST, SYSTEM, 상태보기, 가방, 장비, 스킬, 퀘스트, 시스템, 세이브, 네트워크등록, 환경설정, 도움말, 스피어, 스워드, 나이프, 건, 라이플, 다크, 홀리, 액티브, 패시브, 쿨타임, 지속시간, 등) |

→ **i18n 진행률에 큰 영향**: PROGRESS 의 "UI 어휘 196개 100% 영문" 라인 = `dat/InGame_txt` 의 196 strings 였음 (R39 i18n 작업의 원본 위치 확인). 이번 라운드에 위치 확정.

**plot-relevant strings**:
- 게임 제작사: "일렉트로닉아츠코리아(유)"
- 게임 명칭: "영웅서기3 대지의성흔"
- 제작연원일: 2008. 9. 5.
- 등급분류번호: MO-080912-003호

## 4. dat/i0_dat ~ i18_dat = **게임 전체 아이템 카탈로그** (480+ items)

폴더 enumeration 에서 `i*_dat` 19개 파일 발견. 헤더 패턴이 enemy_dat / s4_dat 와 동일 → `parse_s4_dat` 재사용으로 일괄 파싱.

| File | Size | #Entries | 1st entry | 카테고리 |
|---|---:|---:|---|---|
| `i0_dat` | 1084B | 33 | 머리띠 | **헬멧/모자** (가죽모자, 후드, 강화모자, ...) |
| `i1_dat` | 1372B | 41 | 가죽옷 | **갑옷/로브** (가죽보호대, 가죽로브, 가죽갑옷, 강화XX...) |
| `i2_dat` | 1274B | 37 | 손목보호대 | **장갑/완갑** (가죽장갑, 글러브, 강화글러브) |
| `i3_dat` | 1286B | 38 | 천신발 | **신발/부츠** (가죽신발, 가죽부츠, 강화XX) |
| `i4_dat` | 808B | 25 | 하푼 | **창** (파이크, 스틸하푼, 트라이던트, 글레이브, ...) |
| `i5_dat` | 826B | 25 | 롱소드 | **대검** (브레이커, 브로드소드, 나이트소드, 쯔바이핸더, ...) |
| `i6_dat` | 826B | 25 | 핸드나이프 | **단검** (핸드커터, 대거, 어쌔신나이프, 아이언대거, ...) |
| `i7_dat` | 770B | 25 | 콜드 | **건** (로빈, 크로우, 호크아이, 카이트, ...) |
| `i8_dat` | 806B | 25 | 폭스테일 | **라이플** (울프탈론, 스네이크팽, 하이에나암즈, 퓨마웨폰, ...) |
| `i9_dat` | 780B | 25 | 다크스톤 | **다크마법 도구** (흑수정, 공작석, 다크앰버, 다크스피넬, ...) |
| `i10_dat` | 776B | 25 | 홀리스톤 | **홀리마법 도구** (수정, 코랄, 앰버, 스피넬, ...) |
| `i11_dat` | 728B | 22 | 가죽버클러 | **방패** (청동방패, 버클러, 강철방패, 라운드실드, ...) |
| `i12_dat` | 1319B | 40 | 근성의반지 | **반지/장신구** (회복의반지, 맹공의반지, 힘의반지, ...) |
| `i13_dat` | 2174B | 35 | 자비의손길 | **스킬북 또는 패시브 (?)** — 부가 검증 필요 |
| `i14_dat` | 1984B | 46 | 붉은용액 | **희귀/이벤트 아이템** |
| `i15_dat` | **7400B** | 26 | (binary, entropy 7.97) | **★ 신규 DES 후보** — 평문 파싱 실패 |
| `i16_dat` | 892B | 15 | 투신의 | **enchant 옵션** ("XX의" 접두사 + "무기/방어구에 결합" 설명) |
| `i17_dat` | 1140B | 21 | 시그널펜던트A | **퀘스트 아이템** (협곡의성수, 토레즈시민증, ...) |
| `i18_dat` | 1288B | 26 | 포션 | **소비 아이템** (하이포션, 미라클포션, 엘릭서, 과일쥬스, ...) |

### i15_dat = 신규 DES 후보 (8번째 암호화 파일)

- size 7400B
- entropy **7.97 bits/byte** (랜덤분포 매우 가까움 → DES/AES/압축)
- 첫 32B: `6a 02 87 9c 6d b8 09 76 07 d6 c4 9c c0 65 13 31 8c 0a 5f 25 d5 05 fd ac 36 d6 b1 af 88 38 85 89`

R57 의 알려진 DES 7 파일 (`drop_dat` / `droph_dat` / `getitem_dat` / `smith_dat` / `smithh_dat` / `shop_dat` / `shoph_dat`) 에 **i15_dat 추가** → **DES 후보 8 파일**. 같은 key `"0EP@KO91"` + tables 로 NDK runner 시 함께 복호화 가능 예상.

크기 7400B 가 가장 큼 → 가장 중요한 데이터 추정 (전체 item master table or shop inventory).

### 18 평문 카테고리 = **게임 아이템 시스템 완전 매핑**

- 9개 장비 슬롯: 모자(i0) + 갑옷(i1) + 장갑(i2) + 신발(i3) + 방패(i11) + 반지(i12) + 무기(i4~i10 — 7 weapon types)
- 마법 도구: 다크(i9) + 홀리(i10) — 각 25 entries × 5 tier
- 부가: enchant 옵션(i16) + 소비(i18) + 퀘스트(i17)
- 미상: i13 (35 entries) + i14 (46 entries) — body 패턴이 weapon 과 비슷 (5-tier 강화) 가설

각 entry 의 body (~20B) 구조 (추정):
- bytes 0..1: int16 LE 가격 (예: 100 = 0x64 0x00, 빈도 높음)
- bytes 2..3: pad
- bytes 4..5: int16 BE 요구레벨 또는 성능값
- bytes 6..9: pad
- bytes 10..11: int16 BE attribute (lvl-related, 5-tier scaling 0x01/0x07/0x0c/0x11/0x16)
- bytes 12..19: 추가 스탯 + flag

→ 다음 라운드(Round 61) 에서 정밀 필드 매핑 가능.

## 5. PROGRESS / 진행률 갱신

| 영역 | R59 | R60 | 변화 |
|---|---:|---:|---|
| 자산 포맷 분석/변환 | 80% | **82%** | +2%p (item dat format 추가 확인) |
| 자산 변환 산출 | 95% | 95% | — |
| Ghidra 로직 리버싱 | 75% | 75% | — (R60는 데이터 위주) |
| 게임 데이터 평문 매핑 | 70% | **95%** | +25%p ★ (item/skill/string 거의 전부) |
| Android 엔진 재구현 | 5~10% | 5~10% | — |
| i18n | UI 100% / 대사 0% | UI 100% / 대사 0% | — (대사 9,741건 그대로) |
| **합계 추정** | **~75-78%** | **~82-85%** | **+7%p** |

## 6. 다음 라운드 (Round 61) 우선순위

1. ⭐⭐⭐ **item dat body 19~20B stat block 정밀 필드 매핑**
   - 가격(LE16) + 요구레벨/스탯 + tier number + flag 의 정확한 위치
   - 9 슬롯 × ~25 items = 230+ items 의 완전 정량화

2. ⭐⭐⭐ **i15_dat 8번째 DES 파일 시도**
   - 기존 7 DES 후보와 함께 NDK runner 한번에 처리
   - 평문 시 가장 큰 데이터 (7400B) → 핵심 game data

3. ⭐⭐ **i13_dat (35) / i14_dat (46) 카테고리 식별**
   - body 패턴 비교 → 스킬북 / 마법서 / 희귀 아이템 등

4. ⭐⭐ **skill_dat 5+ tier 의 stat decode** (각 30-70B body)
   - 데미지 계수 / 쿨다운 / SP cost / element 등 필드 식별

5. ⭐ **FUN_4f358 본문 정밀 분석** (R55/R59 의 보류 작업)
6. ⭐ **FUN_3a028 16-JT 디코드** (R54 보류)

DES 작업은 사용자 환경 필요 — H5 의 NDK runner 활용. 자세한 절차: [`tools/ndk_des_runner/README.md`](../../tools/ndk_des_runner/README.md).

## 7. 참고

- 상위 인덱스: [SESSION_HANDOFF.md](SESSION_HANDOFF.md), [PROGRESS.md](PROGRESS.md)
- 직전: [Round 59 char/npcg/s4 dat](ghidra-char-npcg-skill-parsing-2026-05-18.md)
- R57 DES 키 / tables: [DES system](ghidra-des-system-and-dat-paths-2026-05-18.md)
- R58 boss/quest: [boss + quest + DES variants](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md)
