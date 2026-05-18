# Hero3 인수인계 노트 (Round 69 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99.3%**. **자동 분석 완전 한계 도달** — R69 의 i14 ammo 정정 + enemy stat scaling + dialogue translation queue 가 마지막 자동 작업. 남은 모든 작업이 **사용자 환경 (DES 복호화 + LLM 번역 + audio 변환) 필수**.

마지막 commit: `daeabed3 feat:영웅서기3 Round 68 — gun marker 0x1f 정밀 (s7 unique) + boss skill table 검색 + FUN_4f358 재확인`

**Round 69 산출물 = uncommitted**:
- 신규 doc 1: [`ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md`](ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md)
- 신규 recon 스크립트 3: `analyze_i14_ammo_system.py` / `refine_enemy_stats.py` / `sort_dialogue_for_translation.py`
- 신규 산출물 (work/h3/, gitignored): `recon/i14_ammo_system.{json,log}` / `recon/enemy_stat_fields.{json,log}` / `translation_queue.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 자동 분석 종료 — 사용자 환경 필수 작업

### 1.1 ⭐⭐⭐ DES 8 파일 복호화 (최우선)

- **i15_dat** (7400B, entropy 7.97, master item table 추정)
- drop_dat / droph_dat (3080B, enemy 드롭)
- getitem_dat (400B, fixed drops)
- smith_dat / smithh_dat (896B, smith 레시피)
- shop_dat / shoph_dat (상점 카탈로그)

방법: Hero5 NDK runner (key `"0EP@KO91"` + `dat/des_dat` tables, R57 확정).

### 1.2 ⭐⭐⭐ boss skill ID 매핑 최종 확정

R67/R68 의 H4 가설 (별도 boss skill table) 검증. DES 복호화된 파일 안에 boss AI table 발견 가능.

### 1.3 ⭐⭐ i14 smith 레시피 매핑

smith_dat 복호화 후 i14 → i0~i12 정확 매핑. R69 의 7 카테고리 + weapon-class crafting map 기준.

### 1.4 ⭐⭐ Dialogue LLM 번역

9,740 entries, **$4.09 추정 비용** (Claude Sonnet 4.6). 한국어 → 영어 i18n.

### 1.5 ⭐ SMAF→OGG audio 변환

33 파일. Android audio asset 준비.

## 2. Round 69 핵심 발견

### 2.1 R68 's7 별도 ammo 시스템' 가설 정정 (★★★★)

- i14 의 "탄성제" desc = "권총/라이플의 조합에 사용"
- **권총 (s7) + 라이플 (s8) ammo 시스템 공유**
- 0x1f marker (s7 active) vs 0x01 (s8 active) = **사거리/조준 모드 표시만**
  - 단발 권총: 빠른 사격 / 다중 타겟 (난사)
  - 연발 라이플: 정확 사격 / 관통 (직격/연쇄/위협)
- "스톤/총기" 고대 정령석 = 다크석/홀리석 + 권총/라이플 4 class 공유
- "시몬의문장" = 총기 전용 강화 (s7+s8 모두)

### 2.2 i14 조합 재료 7 카테고리 (★★★★)

```
공통 용액 (3): 붉은/푸른/투명
공정 재료 (6): 제련석, 연마가루, 정령석, 탄성제, 강화제, 질긴섬유
원소 속성 (4): 바람피리, 만년설, 혈목, 흑암석
몬스터 드롭 (15): 쥐가죽, 박쥐날개 등
고대 재료 t1 (4): 에스텔시아 (투구), 그리톤 (장갑), 아르세네스 (무기), 데비그린 (스톤/총기)
고대 재료 t2 (4): 카메루시아, 시르톤, 뮤제게네스, 오헨그린
고대 재료 t3 (4): 헤게네시아, 아케톤, 바스테네스, 큐브그린
클래스 강화 문장 (5): 아벨(전사), 시몬(총기), 포프(마법), 부폰(방어), 하피(회피)
```

### 2.3 enemy_dat 19B field scaling 정밀 (★★★)

```
+0x00         lvl                  (R56 확정)
+0x04..+0x05  variant/ID           (scaling 1.04x → 변동 없음)
+0x06..+0x07  MP_max               (scaling 2.71x median)
+0x08..+0x09  EXP_high or Gold     (scaling 3.84x median)
+0x0a..+0x0b  HP_max               (R60 확정, scaling 2.22x stable)
+0x0c..+0x0d  HP_cur               (scaling 3.00x)
+0x0e..+0x0f  EXP_main             (scaling 6.92x, group별 9.7x or 1.80x)
+0x10         ATK                  (scaling 2.93x)
+0x11         AGI/DOD              (scaling 1.21x = +2 constant)
+0x12         pad
```

### 2.4 dialogue translation queue (★★★)

```
unique_texts:        9,741
meaningful_korean:   9,740 (99.99%)
char_count_total:    34,043
번역 비용 추정:       $4.09 (Claude Sonnet 4.6)
```

## 3. 작업 순서 권장 (Round 70+)

자동 분석 완전 종료. 남은 작업은 사용자 환경에서:

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 69 산출물 (자동 분석 마지막)
3. **사용자 환경 진행**:
   - DES 8 파일 복호화 (Hero5 NDK runner)
   - Dialogue LLM 번역 (9,740 entries)
   - SMAF→OGG audio 변환

목표 진행률 (Round 70+, 사용자 환경 후): **~99.8%+** (DES 복호화로 boss skill / smith 레시피 / item table 완료 시).

## 4. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 69 상세](ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md) — ★ 이번 라운드
- [Round 68](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — boss skill 검색 + gun marker + FUN_4f358
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer + boss skill 가설
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + skill effect v2 + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — trailer + effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill / boss HP / string
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
