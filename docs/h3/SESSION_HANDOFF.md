# Hero3 인수인계 노트 (Round 68 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99%**. R68: gun marker (0x1f) 정밀 (s7 unique), boss skill table binary/dat 검색 (H4 confirmed but unresolved), FUN_4f358 재확인 (NPC table lookup, boss skill 무관). 자동 분석 한계 도달 — 남은 작업 거의 DES 복호화 의존.

마지막 commit: `ed407132 feat:영웅서기3 Round 67 — skill header 14B 정밀 + enemy_dat trailer 의미 + boss skill ID 4 가설 분석`

**Round 68 산출물 = uncommitted**:
- 신규 doc 1: [`ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md`](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md)
- 신규 recon 스크립트 2: `find_boss_skill_table.py` / `verify_gun_marker.py`
- 신규 산출물 (work/h3/recon/, gitignored): `boss_skill_table_search.{json,log}` / `gun_marker_verification.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 제한적)

자동 분석 한계 도달. 남은 자동 작업은 minor / 정밀화 위주.

### 1.1 ⭐⭐ i14 조합 재료 → 권총 ammo 시스템 연관

R68 발견: s7 의 0x1f marker = pistol unique 시스템. R61 의 i14 (탄성제 = 총용 조합재료) 와 연관 가능.

### 1.2 ⭐⭐ enemy_dat f4_5/f6_7/f8_9 field 정밀

현재 hp_max @+0x0a..+0x0b 만 확정. ATT1/ATT2/MP/EXP 위치는 추정 단계 (R56 추정 → R60 부분 검증).

### 1.3 ⭐ dialogue corpus 9,741 unique 대사 정렬

LLM 번역 준비 (사용자 환경).

## 2. 사용자 환경 필수 작업 (DES 의존)

### 2.1 ⭐⭐⭐ i15_dat NDK 복호화 + 7 DES 파일 일괄

drop_dat / droph_dat / getitem_dat / smith_dat / smithh_dat / shop_dat / shoph_dat / i15_dat = 8 files.
Hero5 NDK runner 활용 (key `"0EP@KO91"` + `dat/des_dat` tables).

### 2.2 ⭐⭐⭐ boss skill ID 매핑 최종 확정

R67/R68: H4 (별도 boss skill table) most likely but unresolved.
binary 직접 매칭 0 hit, dat 직접 매칭 1 hit (enemyg_dat 케이 패턴, 불확실).
DES 복호화된 파일 안에 boss AI table 발견 가능.

### 2.3 ⭐⭐ i14 → smith_dat 레시피

smith_dat (DES) 복호 시 i14 (조합 재료) → i0~i12 (결과물) 매핑.

### 2.4 ⭐ SMAF→OGG 33 파일 변환 + 9,741 대사 LLM 번역

## 3. Round 68 핵심 발견

### 3.1 gun marker (0x1f) 정밀 (★★★★)

```
weapon class별 +0x0c flag:
  s4 (창), s5 (대검), s6 (단검), s8 (라이플), s9 (다크), s10 (홀리):
    weapon_passive = 0x01, active_attack = 0x01, utility/buff = 0x00

  s7 (건/피스톨) 만 unique:
    weapon_passive = 0x14, active_attack = 0x1f, utility/buff = 0x00
```

→ s7 만 unique flag pair (0x14 + 0x1f) = pistol 특별 hit/ammo 시스템.
→ 라이플 (s8) 은 standard attack 처럼 작동.

### 3.2 boss skill table 검색 결과 (★★★)

R67 의 H4 가설 검증:
- binary 직접 매칭: **0 hit** (6 boss skill patterns 모두)
- dat 파일 매칭: **1 hit** (enemyg_dat 의 케이 패턴, sprite coincidence 추정)

→ H4 강화 but unresolved. DES 8 파일 복호화 후 재시도 필요.

추가 가설:
- H5: trailer[2..5] = tier 별 AI script ID
- H6: trailer[2..5] = 4 stat boost values
- H7: trailer[2..5] = AI behavior weight (probability)

### 3.3 FUN_4f358 본문 재확인 (★★★)

R55 발견 재확인: FUN_4f358 = NPC table multi-lookup (0x3c4 row stride + 0x3c element size).
literal pool 의 0x9e28 = task[+0x9e28] = R27 cluster NPC table base.
**boss skill mapping 과 직접 관련 없음**.

## 4. 작업 순서 권장 (Round 69)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 68 산출물
3. 자동: i14 ammo 시스템 연관 + enemy_dat f4_5 field 정밀
4. **DES 환경 필요** (사용자 진행) — i15_dat NDK + 7 DES 일괄
5. Round 69 doc 작성 + commit

목표 진행률 (Round 69 종료): **~99.5%** (자동 분석 거의 완료).

## 5. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 68 상세](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — ★ 이번 라운드
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer + boss skill 가설
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill / boss HP / string / item
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
