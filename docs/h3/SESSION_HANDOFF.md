# Hero3 인수인계 노트 (Round 66 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~97-98%**. game_balance.json v1.1 (582KB) 출력 완료. R66 정정: debuff code = stat enum 동일 (value 부호로 buff/debuff), skill effect block = right-justified chain (전율 3-debuff 발견), boss combat_rating = round(lvl/2 + 44|64). DES 8 파일만 사용자 환경 필요.

마지막 commit: `c3fd598f feat:영웅서기4 Round 68+69 — DES key J@IWO8N7 발견 + 407 파일 일괄 복호화 + 게임 catalog 추출` (H3 R65 산출물 흡수)

**Round 66 산출물 = uncommitted**:
- 신규 doc 1: [`ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md`](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md)
- 신규 recon 스크립트 2: `refine_debuff_codes.py` / `decode_skill_effect_v2.py`
- 수정 스크립트 1: `export_game_balance.py` (v1.1)
- 신규 산출물 (work/h3/recon/, gitignored): `debuff_codes_refined.{json,log}` / `skill_effect_v2.{json,log}` / `game_balance.json` (582KB v1.1)
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ skill header (+0x00..+0x0d) 정밀

R66 의 skill_effect_v2 schema 에서 effect chain 만 디코드. header (+0x00..+0x0d) 14 bytes 의 정확한 의미는 부분 파악:
- +0x00..+0x01: LE16 SP cost ✓
- +0x02..+0x03: pad
- +0x04..+0x05: byte pair (damage_base?)
- +0x06..+0x08: pad
- +0x09..+0x0a: 0x55 0x55 marker (max stat?)
- +0x0b: byte (range/duration?)
- +0x0c..+0x0d: subheader

스크립트: `tools/recon/decode_skill_header.py` (신규)

### 1.2 ⭐⭐⭐ boss skill slot ID → actual skill 매핑

R65 발견: story boss trailer[2..5] = 4 skill slot ID (1~20 범위). 이 ID 가 어떤 skill_dat 의 actual skill 인지 매핑.

가설: ID = skill_dat 의 entry index (0-based)? 또는 별도 boss skill table?

스크립트: `tools/recon/map_boss_skill_id.py` (신규)

### 1.3 ⭐⭐⭐ i15_dat NDK 복호화 (사용자 환경 계속)

### 1.4 ⭐⭐ i14 조합 재료 → smith_dat 레시피

smith_dat 복호화 시 i14 (조합 재료) → i0~i12 (결과물) 매핑 표 발견 가능.

### 1.5 ⭐⭐ FUN_4f358 본문 ARM disassembly

debuff handler dispatch 검증 (R55/R59/R61/R63/R64/R65/R66 보류).

### 1.6 ⭐ enemy_dat trailer `01 1e` 의미

`1e` = 30 = boss spawn flag? Or just constant terminator.

## 2. 사용자 환경 필요 작업 (보류)

§1.3 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역.

## 3. Round 66 핵심 발견

### 3.1 debuff code = stat enum 동일 (R65 가설 정정) ★★★★★

- skill debuff code 와 i13 디버프 effect_type high byte 가 동일 enum 사용
- value 부호로 buff/debuff 구분
- 2 컨텍스트 분리: 0x0d (CRI_DEF vs STUN_RESIST), 0x1c (REVIVE vs STUN_TRIGGER)
- 신규 master enum: 0x15 = TAUNT
- skill debuff distinct codes: 11 개 (R65 의 6 보다 5개 추가)

### 3.2 skill effect block schema v2 (★★★★★)

```
30-byte tail right-justified chain:
  pos 14..18 = slot1 (code + LE16+LE16 signed)
  pos 19..23 = slot2
  pos 24..28 = slot3
  pos 29 = rank
  pos 0..13 = header (SP cost + damage scale + pad)
```

전율 (s9_dat) = **3-debuff skill** 신규 발견: P_DEF + M_DEF + DOD.

### 3.3 boss combat_rating 공식 (★★★★)

```
rating = round(lvl / 2 + 44)  # normal
rating = round(lvl / 2 + 64)  # hard
```

30 boss entries 모두 검증 통과. "challenge equivalence level" = boss 의 권장 player level 표시.

### 3.4 game_balance.json v1.1 (★★★)

537KB → 582KB. R66 enrichment 추가:
- skills.*.skills[].effect_v2 (slot1/slot2/slot3 + header)
- bosses.*.trailer_decoded (combat_rating + sprite_idx + skill_slots)
- combat_rating_formula
- stat_enum context_split (0x0d, 0x1c) + context_buff (0x0b) + TAUNT (0x15)
- skill_debuff_codes 11 distinct

## 4. 작업 순서 권장 (Round 67)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 66 산출물
3. **skill header 정밀** (`tools/recon/decode_skill_header.py` 신규)
4. **boss skill ID 매핑** (`tools/recon/map_boss_skill_id.py` 신규)
5. **i15_dat NDK runner** (사용자 환경)
6. Round 67 doc 작성 + commit

목표 진행률 (Round 67 종료): **~98-99%**.

## 5. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 66 상세](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — ★ 이번 라운드
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer 재집계 + effect mask + signed (R66 에서 schema 정정)
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0 + value scale
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 100%
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity / quest xref
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill / boss HP / string / item
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
