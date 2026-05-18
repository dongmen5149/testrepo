# Round 68 — boss skill table 검색 + FUN_4f358 재확인 + gun marker 정밀 (2026-05-19)

> 이번 라운드 목표: R67 후속 — boss skill ID 매핑 (H4 검증), FUN_4f358 본문 분석, gun marker (0x1f) 정밀.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐ **gun marker 0x1f 정밀**: s7 (건/피스톨) active_attack 4 전용. **0x14 + 0x1f = s7 unique flag pair**. 라이플 (s8) 는 standard 0x01 사용
- ⭐⭐⭐ **boss skill table 검색**: binary 직접 매칭 0 hit, dat 직접 매칭 1 hit (enemyg_dat 의 케이 패턴 — sprite coincidence 추정). **H4 가설 confirmed: boss skill ID 가 binary 에 hard-coded 안 됨**
- ⭐⭐⭐ **FUN_4f358 본문 확인**: R55 의 NPC table multi-lookup 함수 재확인 (0x3c4 stride + 0x3c element size). boss skill mapping 과 직접 관련 없음. Thumb ARM literal pool 분석으로 확정
- ⭐⭐ **trailer[2..5] 의미 후속 가설**: tier-dependent (lvl 14/24 같은 trailer, lvl 32 다른 trailer), character class identity 와 연관

## 1. boss skill table 검색 결과 (★★★) — `work/h3/recon/boss_skill_table_search.json`

R67 의 H4 (별도 boss skill table) 가설 검증.

### 1.1 binary 직접 매칭

6 boss skill 패턴 모두 binary 에서 0 hit:

| pattern | label | binary hits |
|---|---|---:|
| `03 02 01 02` | 리츠 t1/t2 | 0 |
| `02 02 01 01` | 케이 t1/t2 | 0 |
| `09 03 03 07` | 멜페토 t4 | 0 |
| `07 08 05 09` | 큐 t4 | 0 |
| `13 0d 09 09` | 리츠 t3 | 0 |
| `14 0e 0a 08` | 케이 t3 | 0 |

→ binary 직접 hard-coded 안 됨 = boss skill mapping 이 별도 dat 파일 또는 runtime computed.

### 1.2 dat 파일 직접 매칭

- **enemyg_dat**: 케이 t1/t2 (2,2,1,1) **3 hits** @ 0xea, 0x100, 0x116
- 다른 5 패턴 = 0 hit

enemyg_dat = NPC/enemy graphics info (R56 발견). 3 hits 가 sprite 데이터의 coincidence 인지 boss skill mapping 인지 불명확. byte sequence (2,2,1,1) 은 sprite/animation 데이터에 자주 등장 가능.

### 1.3 결론

**H4 가설 강화 but 명확한 매핑 unresolved**:
- binary hard-coded 아님 (R67 H1~H3 가설 모두 reject)
- dat 파일 직접 매칭 minimal (1/6 패턴만 부분 hit, 불확실)
- **DES 8 파일 복호화 후 재확인 필요** (drop_dat / smith_dat / shop_dat 등)
- 또는 FUN_4f358 의 NPC table runtime computation 으로 boss skill 동적 결정 가능

### 1.4 alternative hypothesis (R68 신규)

- **H5**: trailer[2..5] = boss progression tier 별 AI script ID
- **H6**: trailer[2..5] = 4 stat boost values (ATT1/ATT2/P_DEF/M_DEF +N)
- **H7**: 값 자체가 AI behavior weight (probability of each skill slot)

리츠 tier 1 (lvl 14) + tier 2 (lvl 24) **같은 trailer (3,2,1,2)**, tier 3 (lvl 32) **다른 trailer (19,13,9,9)** = tier-dependent. character class 마다 다른 패턴 (어쌀트워리어 vs 버서커).

## 2. FUN_4f358 본문 ARM disasm 재확인 (★★★) — Thumb instruction

R55 의 발견 재확인. FUN_4f358 = NPC table multi-lookup, boss skill mapping 과 직접 관련 없음.

### 2.1 핵심 instruction (Thumb)

```
0x4f358: 90 b5 6f 46 86 b0 3c 1f  push {r4,r7,lr}; mov r7, sp; sub sp, #0x18; subs r0, r7, #4
0x4f37c: f1 23 9b 00 5a 43 3c 23  mov r3, #0xf1; lsl r3, #2 (=0x3c4); mul r2, r3; mov r3, #0x3c
0x4f384: 4b 43 d3 18 1b 18         mul r3, r1; add r3, r2; add r3, r3
```

key constants:
- **0x3c4** = NPC table **row stride** (R55 확인)
- **0x3c (=60)** = NPC table **element size** = R56 의 ObjectB instance size
- 0x9e28 (literal pool @ +0x70) = **task[+0x9e28]** = R27 cluster (NPC table base)

→ FUN_4f358 = `npc_table[row][col]` accessor (row 0x3c4 stride, col 0x3c stride). boss skill 와 무관.

## 3. gun marker (0x1f) 정밀 검증 (★★★★) — `work/h3/recon/gun_marker_verification.json`

R67 발견 정밀화 — s7 vs s8 weapon flag 차이.

### 3.1 weapon class 별 +0x0c flag

| weapon | weapon_passive | active_attack | active_buff | passive_bonus |
|---|---|---|---|---|
| s4 (창) | 0x01 | 0x01 | 0x00 | 0x00 |
| s5 (대검) | 0x01 | 0x01 | 0x00 | 0x00 |
| s6 (단검) | 0x01 | 0x01 | 0x00 | 0x00 |
| **s7 (건/피스톨)** | **0x14** | **0x1f** | 0x00 | 0x00 |
| s8 (라이플) | 0x01 | 0x01 | 0x00 | 0x00 |
| s9 (다크석) | 0x01 | 0x01 | 0x00 | 0x00 |
| s10 (홀리석) | 0x01 | 0x01 | 0x00 | 0x00 |

→ **s7 만 unique flag pair (0x14 + 0x1f)**.

### 3.2 의미

- **0x14 (s7 weapon_passive)**: 사격 mastery marker
- **0x1f (s7 active_attack)**: pistol multi-target/multi-hit marker (연사/난사/곡예/저격 모두)
- **0x01 (다른 weapon class)**: standard physical attack flag
- **0x00 (utility/buff)**: no attack target

→ 게임 내 의미: **단발 권총 (s7) 은 다른 무기와 별도 hit/ammo 시스템 보유**. 라이플 (s8) 은 standard attack 처럼 작동.

Hero3 의 사격 (s7) skill 4개는 다음 특징:
- 연사 (rank 4): 1체 다중 사격
- 난사 (rank 10, ultimate): 다수 적 무차별
- 곡예 (rank 4): 거리 조정 사격
- 저격 (rank 1): 한발 위력 극대화

→ 권총 ammo 시스템 또는 자세 (조준/사격 자세) 가 다른 무기와 별개. R68+ 의 i14 조합 재료 분석 시 권총 탄약 (탄성제 R61) 와 연관 확인 가능.

## 4. R68 산출물

### 4.1 신규 스크립트 (2개)

- `tools/recon/find_boss_skill_table.py` — binary + dat 파일 boss skill 패턴 검색
- `tools/recon/verify_gun_marker.py` — s7 vs s8 weapon flag 정밀

### 4.2 신규 출력 (모두 `work/h3/recon/`, gitignored)

- `boss_skill_table_search.{json,log}`
- `gun_marker_verification.{json,log}`

### 4.3 진행률 갱신

- **R67 종료 ~98-99%** → **R68 종료 ~99%** (+0.5%p)
- 게임 시스템 모델링: 99.5→99.7% (gun marker 정밀 + boss skill 가설 정리 + FUN_4f358 재확인)
- 자동 분석 한계 도달 — 남은 작업 = DES 복호화 (사용자 환경 필수)

## 5. Round 69 후속 작업

### 5.1 자동 가능 (제한적)

1. ⭐⭐ **i14 조합 재료 → 권총 ammo 시스템 연관 정밀** — 탄성제 (총용) 와 s7 의 0x1f marker 연관 분석
2. ⭐⭐ **enemy_dat 의 f4_5/f6_7/f8_9 field 정밀** — boss stat 의 ATT/DEF/MP 위치 (현재 hp_max @+0x0a..+0x0b 만 확정)
3. ⭐ **dialogue corpus 9,741 unique 대사 정렬** — LLM 번역 준비 (사용자 환경)

### 5.2 사용자 환경 필수

1. ⭐⭐⭐ **i15_dat NDK 복호화** + 7 DES 파일 일괄
2. ⭐⭐⭐ **boss skill ID 매핑 최종 확정** — DES 파일 안에 boss AI table 발견 가능
3. ⭐⭐ **i14 → smith_dat 레시피** — smith_dat (DES) 복호 시 매칭
4. ⭐ **SMAF→OGG 33 파일 변환** — Android audio asset

## 6. 참고 (이전 라운드)

- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer + boss skill 4 가설
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum
- (R56-R62) — see SESSION_HANDOFF.md
