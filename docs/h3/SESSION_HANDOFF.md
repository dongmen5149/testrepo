# Hero3 인수인계 노트 (Round 67 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~98-99%**. R67 정밀: skill header 14B 완전 디코드 (range/weapon_flag/animation), enemy_dat 2B trailer 의미 확정 (difficulty + encounter type), boss skill slot ID 매핑 가설 정리 (H4 별도 boss skill table 가장 유력). DES 8 파일만 사용자 환경 필요.

마지막 commit: `e38c13c2 feat:영웅서기3 Round 66 — debuff codes 정밀 + skill effect v2 (3-debuff 발견) + boss combat_rating 공식 + game_balance.json v1.1`

**Round 67 산출물 = uncommitted**:
- 신규 doc 1: [`ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md`](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md)
- 신규 recon 스크립트 3: `decode_skill_header.py` / `decode_enemy_trailer.py` / `analyze_boss_skill_id.py`
- 신규 산출물 (work/h3/recon/, gitignored): `skill_header.{json,log}` / `enemy_trailer.{json,log}` / `boss_skill_id_analysis.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ boss skill ID (1..20) → actual skill 매핑 (R68 핵심)

R67 결론: H4 (별도 boss skill table) 가장 유력. 다음 단계:
- binary `client.bin64000` 에서 boss skill mapping table grep (예: `01 xx xx xx 02 xx xx xx ...` 12-entry pattern)
- DES 복호화 후 boss_skill_dat 또는 ai_dat 같은 파일 발견 시 매핑
- FUN_4f358 본문 ARM disassembly 에서 skill dispatch table 확인

스크립트: `tools/recon/find_boss_skill_table.py` (신규)

### 1.2 ⭐⭐⭐ i15_dat NDK 복호화 (사용자 환경 계속 보류)

R63-R66 와 동일.

### 1.3 ⭐⭐ i14 조합 재료 → smith_dat 레시피

smith_dat 복호화 후 매칭 (DES 사용자 환경 의존).

### 1.4 ⭐⭐ FUN_4f358 본문 ARM disassembly

debuff handler dispatch + boss skill mapping 검증.

### 1.5 ⭐ gun marker (0x1f at +0x0c) 추가 검증

R67 발견: s7_dat (건/pistol) 4 skills 만 0x1f. 라이플 (s8) 은 보유 안 함. 이유 파악.

## 2. 사용자 환경 필요 작업 (보류)

§1.2 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역.

## 3. Round 67 핵심 발견

### 3.1 skill header 14B 완전 디코드 (★★★★)

```
+0x00..+0x01  LE16 SP cost (100..800)
+0x04         primary damage base
+0x05         secondary damage base (combo)
+0x07         utility marker (0x14 for utility skill)
+0x09..+0x0a  animation timing / sprite frames
+0x0b         range/AoE radius (20/30/40/80/100)
+0x0c         weapon class flag (1=attack, 31=gun marker, 0=utility)
+0x0d         hit flag
```

핵심:
- **range = weapon class 별 고유**: 단검 20, 창 30, 검·마법 40, 라이플 80, utility 100
- **0x1f at +0x0c = gun marker** (s7_dat 4 skills 전용)
- **(85, 85) at +0x09..+0x0a = utility skill** (압도/유도/위협/망각/전율 공통)

### 3.2 enemy_dat 2B trailer 의미 (★★★★)

```
[0] difficulty marker: 01 normal / 02 hard / 05 cross-mode / 00 sentinel
[1] encounter type:    0x1e standard battle (126/161=78%) / 0xff special
```

→ 161 enemies = 126 standard + 35 special.

### 3.3 boss skill slot ID 매핑 가설 정리 (★★★)

```
Distinct IDs: {1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 19, 20}  Range: 1..20

H1 (글로벌 active 1-base):    rejected (weapon class 불일치)
H2 (weapon internal active):   rejected (ID range 초과)
H3 (weapon 15-skill 1-base):   partial (tier 1/2 가능, tier 3 초과)
H4 (별도 boss skill table):    most likely  ★ R68+ 검증
```

## 4. 작업 순서 권장 (Round 68)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 67 산출물
3. **boss skill table 검색** (`tools/recon/find_boss_skill_table.py` 신규)
4. **i15_dat NDK runner** (사용자 환경)
5. Round 68 doc 작성 + commit

목표 진행률 (Round 68 종료): **~99%** (boss skill 매핑 +0.5%p, smith 레시피 +0.5%p).

## 5. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 67 상세](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — ★ 이번 라운드
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0 + value scale
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 100%
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill / boss HP / string / item
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
