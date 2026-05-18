# Hero3 인수인계 노트 (Round 65 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~96-97%**. 게임 데이터 평문 파싱 ~98% 완료. **skill effect mask 완전 디코드** (+0x10..+0x1d 14B), debuff code 가 별도 enum 확정, **0x14/0x19 = completely unused**, boss trailer 6B = sprite_idx + skill slots, **signed int16 사용처 정확히 2곳만**.

마지막 commit: `2a0bc9f9 feat:영웅서기3 Round 64 — game_balance.json 통합 출력 (537KB) / value scale 매핑 / 0x14·0x19 미사용 확정 / ultimate skill diff`

**Round 65 산출물 = uncommitted**:
- 신규 doc 1: [`ghidra-round65-trailer-effect-mask-signed-2026-05-19.md`](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md)
- 신규 recon 스크립트 4: `analyze_trailer_bonus.py` / `decode_skill_effect_mask.py` / `decode_boss_trailer.py` / `verify_signed_values.py`
- 신규 산출물 (work/h3/recon/, gitignored): `trailer_bonus.{json,log}` / `effect_mask.{json,log}` / `boss_trailer.{json,log}` / `value_sign_verification.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ debuff code 정밀 의미 (R66 핵심)

R65 발견: skill +0x13 / +0x18 = debuff code, 6 distinct codes 사용:
- 0x03 = BLEED 가설 (암영/직격 "관통/출혈 유도")
- 0x06 = ATT2_DEBUFF (망각)
- 0x08 = M_DEF_DEBUFF (전율) — 또는 P_DEF
- 0x09 = ACC_DEBUFF (격광, 압도)
- 0x0a = DOD_DEBUFF (전율 2차)
- 0x15 = TAUNT (유도) — R63 미식별 코드의 새 의미
- 0x1c = STUN (참혼/저격) — R63 의 REVIVE 와 다른 enum

다음 단계: game string table 에서 추가 의미 검색 + i13 디버프 비교로 코드 매핑 강화.

스크립트: `tools/recon/refine_debuff_codes.py` (신규)

### 1.2 ⭐⭐⭐ game_balance.json schema v1.1 출력

R65 산출물 통합 — skill 에 debuff fields / boss 에 sprite_idx + skill slots / equip 에 parsed trailer.

스크립트: `tools/recon/export_game_balance.py` 수정 (v1.1)

### 1.3 ⭐⭐ boss combat_rating (trailer[0]) 의미

R65 발견: boss trailer[0] 이 lvl 과 비례 안 함. boss-only metric. 추가 분석.

### 1.4 ⭐⭐ skill primary_damage_scale weird values

위협 = 64767 (0xfcff), 망각/전율 = 65279 (0xfeff) — 이상한 값. 의미 추적.

### 1.5 ⭐⭐ i15_dat NDK runner 처리 (사용자 환경)

R63-R64 와 동일.

### 1.6 ⭐ FUN_4f358 본문 ARM disassembly

debuff_code → effect handler 매핑 추적.

## 2. 사용자 환경 필요 작업 (보류)

§1.5 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역 — R64 와 동일.

## 3. Round 65 핵심 산출물

### 3.1 skill +0x10..+0x1d 14-byte effect block (★★★★★)

```
+0x10..+0x11   LE16  primary damage scale
+0x12          byte  pad
+0x13          byte  1차 debuff code (0x7f = no debuff)
+0x14..+0x15   LE16 signed  1차 debuff primary value
+0x16..+0x17   LE16 signed  1차 debuff secondary value
+0x18          byte  2차 debuff code
+0x19..+0x1a   LE16 signed  2차 debuff primary value
+0x1b..+0x1c   LE16 signed  2차 debuff secondary value
+0x1d          byte  rank / power class (R63)
```

24 active_attack skills 중 9 개가 debuff 보유.

### 3.2 debuff code 별도 enum (★★★★)

| code | name | example | i13 의 의미와 비교 |
|---:|---|---|---|
| 0x03 | BLEED | 암영/직격 | i13 에선 HP_REGEN |
| 0x06 | ATT2_DEBUFF | 망각 | i13/equip 와 동일 |
| 0x08 | M_DEF_DEBUFF | 전율 | i13/equip 와 동일 |
| 0x09 | ACC_DEBUFF | 격광/압도 | i13/equip 와 동일 |
| 0x0a | DOD_DEBUFF | 전율 2차 | i13/equip 와 동일 |
| 0x15 | TAUNT | 유도 | R63 미식별 |
| 0x1c | STUN | 참혼/저격 | i13 에선 REVIVE |

→ debuff context 는 일부 코드 stat enum 과 공유, 일부 (0x15, 0x1c) 재정의.

### 3.3 0x14 / 0x19 completely unused (★★★)

R64 추정 "equip trailer 에 출현" 도 폐기 — bt 위치 0회.

실제 사용 stat enum = 22 codes (R63 의 24 codes 중 0x14, 0x19 제외).

### 3.4 boss_dat 6B trailer (★★★)

```
[0] combat rating
[1] sprite/model index (8 distinct)
[2..5] 4 boss-specific skill slot IDs (0xFF = unused)
```

- 16 story boss (skill slots 사용): 리츠/케이/멜페토/큐
- 14 misc boss (FF×4): 벨루스/시즈타이탄/아르보르/오르도/홀리가디언

### 3.5 signed int16 통일 가설 정정 (★★★)

R64 의 "signed int16 통일" 가설 폐기. 실제로는 **단 2곳만 signed**:
1. i13 effect_value: 5 negative cases (적 대상 디버프)
2. skill +0x14..+0x17 debuff mask: 9 with-debuff skills

그 외 모든 value field 는 unsigned (byte/LE16/BE16).

## 4. 작업 순서 권장 (Round 66)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `git add` + `git commit` Round 65 산출물
3. **debuff code 정밀 매핑** (`tools/recon/refine_debuff_codes.py` 신규)
4. **game_balance.json v1.1** (export_game_balance.py 수정)
5. **boss combat_rating 함수 추적**
6. **skill primary_damage_scale weird values** 의미
7. **i15_dat NDK runner** (사용자 환경)
8. Round 66 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 66 종료): **~97-98%** (debuff code 정밀 +1%p, schema v1.1 통합 +0.5%p).

## 5. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~65)
- [Round 65 상세](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — ★ 이번 라운드 (skill effect mask + boss trailer + signed 정정)
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json + value scale + ultimate skill diff
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 완전
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity / quest xref
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill 일괄 / boss HP / string / item 카탈로그
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
