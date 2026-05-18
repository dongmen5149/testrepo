# Round 67 — skill header (+0x00..+0x0d) + enemy trailer + boss skill ID 가설 (2026-05-19)

> 이번 라운드 목표: R66 후속 3 작업 — skill header 14B 의미 정밀, enemy_dat 2B trailer 의미 (R66 의 `01 1e` 미스터리), boss skill slot ID 매핑 가설 정리.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐ **skill header (+0x00..+0x0d) 완전 디코드** — SP cost + damage base + range/AoE + weapon_class flag + hit flag. range 분포 (단검 20 / 창 30 / 검·마법 40 / 라이플 80 / utility 100) 와 weapon_flag 0x1f (gun marker, s7 전용 4 skills) 발견
- ⭐⭐⭐⭐ **enemy_dat 2B trailer 의미 확정** — [0] = difficulty marker (`01`=normal / `02`=hard / `05`=cross-mode special / `00`=sentinel), [1] = encounter type (`0x1e`=standard battle, `0xff`=scripted/event). 161 enemies 분포: 126 standard + 35 special
- ⭐⭐⭐ **boss skill slot ID 매핑 — 4 가설 분석, H4 (별도 boss skill table) 가장 유력** — H1 (글로벌 active 1-base), H2 (weapon internal active), H3 (weapon 15-skill 1-base) 모두 일관되지 않음. R68+ binary 분석 필요

## 1. skill header 14B 완전 디코드 (★★★★) — `work/h3/recon/skill_header.json`

R66 schema v2 에서 effect chain (+0x0e..+0x1d) 만 디코드. header 의 의미 정밀화.

### 1.1 layout

```
+0x00..+0x01  LE16  SP cost (100..800 range)
+0x02..+0x03  pad (00 00)
+0x04         byte  primary damage base
+0x05         byte  secondary damage base (combo, 대부분 0)
+0x06         pad
+0x07         byte  utility marker (0x14=20 for utility skill)
+0x08         pad
+0x09..+0x0a  byte pair  animation timing / sprite frames
+0x0b         byte  range / AoE radius
+0x0c         byte  weapon class flag
+0x0d         byte  hit flag
```

### 1.2 range distribution (24 active_attack skills)

| range | n | weapon kind | examples |
|---:|---:|---|---|
| 0 | 1 | gun cross-fire | 난사 (s7) |
| 20 | 3 | melee 단검 | 참혼, 암영, 난무 (s6) |
| 30 | 4 | melee 창 / gun | 섬광, 자격 (s4) + 연사, 곡예 (s7) |
| 40 | 9 | melee 검 / 마법 | 검 s5 + 라이플 s8 + 다크 s9 + 홀리 s10 |
| 80 | 2 | sniper | 질풍 (s5), 저격 (s7) |
| 100 | 5 | utility/debuff | 압도, 유도, 위협, 망각, 전율 |

### 1.3 weapon_flag (+0x0c) distribution

| flag | n | meaning |
|---:|---:|---|
| 0x01 | 15 | 일반 attack |
| 0x00 | 5 | utility / no direct damage |
| 0x1f (=31) | 4 | **gun-specific marker (s7_dat 전용)** |

→ **0x1f 가 gun (s7) 전용 marker**: 연사 / 난사 / 곡예 / 저격 전부 보유. 라이플 (s8) 은 보유 안 함 → "건 (pistol/handgun)" 만 표시하는 weapon-class flag.

### 1.4 +0x09..+0x0a animation timing pattern

| (a09, a0a) | 용도 | examples |
|---|---|---|
| (85, 85) = 0x55 0x55 | utility/debuff | 압도, 유도, 위협, 망각, 전율 |
| (41, 41) = 0x29 0x29 | 단검 1체 | 참혼, 암영 |
| (102, 102) | 강력한 melee | 섬광 |
| (106, 107) | 검 sweep | 질풍 |
| 다양 | weapon-specific | 각 weapon class 마다 다른 frame timing |

→ +0x09..+0x0a = **sprite frame/animation duration** 으로 추정. utility 는 공통 (85, 85) = "no attack animation".

## 2. enemy_dat 2B trailer 의미 (★★★★) — `work/h3/recon/enemy_trailer.json`

R67 발견: enemy_dat 의 trailer `01 1e` 가 161 enemies 의 78% 차지.

### 2.1 layout

```
[0] difficulty/mode marker:
  0x01 = normal mode
  0x02 = hard mode
  0x05 = cross-mode special (unchanged across normal/hard)
  0x00 = sentinel/legacy

[1] encounter type:
  0x1e (=30) = standard battle enemy
  0xff       = special/event/scripted enemy
```

### 2.2 분포 (normal mode)

| trailer | n | meaning |
|---|---:|---|
| `01 1e` | 126 | standard normal-mode enemy |
| `01 ff` | 19 | normal-mode special/scripted |
| `05 ff` | 11 | cross-mode special (unchanged) |
| `00 ff` | 5 | sentinel/legacy |

hard mode 동일 패턴, byte 0 만 `01 → 02` 변경. `05`/`00` 패턴은 **unchanged** (boss intro / scripted encounter 추정).

### 2.3 의미

- byte 0 = "어느 difficulty 에서 spawn 되는지" 표시
- byte 1 = "regular vs scripted" 구분
- 126/161 = 78% standard combat encounter
- 35/161 = special enemies (boss intro / quest-bound / scripted)

## 3. boss skill slot ID 매핑 — 4 가설 분석 (★★★) — `work/h3/recon/boss_skill_id_analysis.json`

R65 발견: story boss (16 entries) 의 trailer[2..5] = 4 byte = skill slot IDs.

### 3.1 distinct IDs 분포

```
Distinct IDs: {1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 19, 20}
Range: 1..20
Total slots used: 64 (16 boss × 4 slot)
```

### 3.2 가설들

#### H1: 글로벌 active_attack 1-base index
- 매핑: id 1 = 파동 (s10), id 2 = 격광, id 3 = 섬광, ...
- 리츠 t1 (3,2,1,2) = 섬광, 격광, 파동, 격광 → **서로 다른 weapon class, 일관성 없음**
- **rejected**

#### H2: weapon-class internal active 1-base
- 매핑: id 1-3 = s5_dat[7,8,9] active 들
- 리츠 t3 의 ID 19/13 이 3-skill 범위 초과 → **rejected**

#### H3: weapon-class 15-skill 1-base (passive + active 모두)
- 매핑: id 1-15 = s5_dat[0..14]
- 리츠 t1 (3,2,1,2) = s5_dat[2,1,0,1] = 검술3, 검술2, 검술, 검술2 — **4 weapon_passive, 가능**
- 리츠 t3 (19,13,9,9): id 19 > 15 max → **partial / rejected**

#### H4: 별도 boss skill table (binary 내)
- ID 1..20 = boss-specific skill ID, skill_dat 와 분리된 table
- binary literal grep 또는 DES 복호화된 파일 분석 필요
- **most likely** — R68+ 검증

### 3.3 결론

H1~H3 매핑 시도 모두 일관되지 않음. **H4 (별도 boss skill table)** 가 가장 가능성 높음.

binary 내 `0xff ff ff ff` (R65 misc boss pattern) 와 `1..20` ID space 가 별도 boss skill enum 을 강하게 시사. R68 후속 작업으로 미룸.

## 4. R67 산출물

### 4.1 신규 스크립트 (3개)

- `tools/recon/decode_skill_header.py` — skill header 14B 정밀
- `tools/recon/decode_enemy_trailer.py` — enemy 2B trailer 의미
- `tools/recon/analyze_boss_skill_id.py` — boss skill ID 4 가설 분석

### 4.2 신규 출력 (모두 `work/h3/recon/`, gitignored)

- `skill_header.{json,log}`
- `enemy_trailer.{json,log}`
- `boss_skill_id_analysis.{json,log}`

### 4.3 진행률 갱신

- **R66 종료 ~97-98%** → **R67 종료 ~98-99%** (+1%p)
- 게임 시스템 모델링: 99→99.5% (skill header + enemy 분류 + boss skill ID 가설)
- DES 8 파일 보류 = 사용자 환경 필요

## 5. Round 68 후속 작업

1. ⭐⭐⭐ **i15_dat NDK 복호화** + 7 DES 파일 일괄 — 사용자 환경 (계속 보류)
2. ⭐⭐⭐ **boss skill ID (1..20) → actual skill 매핑** — binary literal grep 또는 DES 파일 분석
3. ⭐⭐ **i14 조합 재료 → smith_dat 레시피** — smith_dat (DES) 복호 시 매칭
4. ⭐⭐ **FUN_4f358 본문 ARM disassembly** — debuff handler dispatch + boss skill mapping 검증
5. ⭐ **gun marker (0x1f) 추가 검증** — 라이플 (s8) 가 0x1f 보유 안 하는 이유

## 6. 참고 (이전 라운드)

- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + boss combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0 + value scale
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 100%
- (R56-R62) — see SESSION_HANDOFF.md §7
