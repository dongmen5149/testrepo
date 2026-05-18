# Hero4 Session Handoff — Round 69 종료, Round 70 즉시 시작 가이드

> **다음 세션 시작점**: 이 문서를 가장 먼저 읽기. 라운드별 디테일은 `round68-des-key-discovered.md` + `round69-skill-catalog-and-batch-decrypt.md`.

## 30초 요약

**🏆 Round 68+69 (2026-05-18/19) 종료 — Hero4 자동 영역 100%**:
- DES key 발견 (`J@IWO8N7`) + cipher 변종 확정 (`tools/h5_des.py:mx_des_decrypt`)
- **407 파일 일괄 복호화** = SCN 350 + HDAT-A 8 + (R69) E/ITM/NPC/FR 49
- dialogue corpus 4,078 garbage → **35,752 entries** (8.76x 증가)
- Hero4 게임 시스템 catalog: 4 캐릭터 (티르/루레인 + 2) × **10 스킬 = 40 스킬 매트릭스**
- 1,572 한국어 아이템 + 2,427 한국어 quest/UI entries
- `work/h4/converted/h4_catalog.json` = Android single source of truth

## Round 70 즉시 시작 — 4 가지 자동 트랙

### 트랙 A: A1 영어 번역 ⭐ (자동, ~30분, ~$0.30)

corpus + catalog 모두 한국어 진본화 완료 → 즉시 사용 가능.

```bash
export ANTHROPIC_API_KEY=sk-...
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
# 출력: work/h4/converted/dialogue_translations_en.json
# translation_dict.py 의 CHARACTERS_H4 52 + PLACES_H4 12 + h4_catalog.json 자동 활용
```

번역 우선순위 (corpus top 사용):
- 퀘스트 (347), 입수 (175), 완료 (171)
- 티르 (94) → "Tír", 루레인 → "Lurain"
- 40 스킬 이름 (translation_dict 추가 필요)

### 트랙 B: NPC QUEST 평문 정밀 파싱 (자동, ~1시간)

`work/h4/decrypted/NPC/_QUEST_{0,1}_DAT` (7568B + 7328B) 평문 확정 (entropy 6.1).
Hero3 R58 의 `quest_*_dat` 동일 패턴 (37 main + 7 side) 가능. 평문 구조:
```
[size_byte+2] [00] [name_len] [name:EUC-KR] [description] [위치;목표;카테고리]
```

```bash
# 참조: tools/recon/parse_quest_dat.py (Hero3 용)
# Hero4 용 변종: tools/recon/parse_h4_quest.py 작성 필요
```

### 트랙 C: HDAT-A _H_BH stat block 정밀 (자동, ~30분)

168B = 4 entries × 40B 의 hero stat fields. 한국어 이름 4B + 36B numeric.
36B 분해:
- level (1B), reserved (1B)
- HP/SP/ATK/DEF/MAT/MDF (2B × 6 = 12B)
- 기타 stats (?? 22B)

Hero3 enemy_dat R56 의 19B stat block 참조 (`docs/h3/ghidra-enemy-dat-and-battle-data-2026-05-18.md`).

### 트랙 D: E/BSDAT, E/ESDAT 6 SCN-like script (자동, ~1시간)

Boss/event scripts. 2008B/13168B 의 평문. SCN bytecode 와 동일 opcode 가설:
```bash
# 비교: work/h4/decrypted/E/_BSDAT_0 헤더 vs SCN 헤더
# docs/h4/formats/scn.md 의 opcode 0x01/0x0c/0xff 적용
```

### 그 외 (사용자 결정)

- **Phase C (KMM 분리)** — Hero3 안정, Hero4 모든 자산 준비. engine refactor 시작.
- **Phase D (iOS)** — Mac + Apple Developer 필요
- Hero3/Hero5 트랙 — `docs/h3/SESSION_HANDOFF.md` / `docs/h5/SESSION_HANDOFF.md` 참조

## 산출물 위치 (R68 + R69 누적)

| 산출물 | 경로 |
|---|---|
| 복호화 SCN 350 | `work/h4/decrypted/SC/*_scn` |
| 복호화 HDAT-A 8 | `work/h4/decrypted/HDAT/_H_*` |
| 복호화 E/BSDAT 3 + ESDAT 3 | `work/h4/decrypted/E/_BSDAT_*, _ESDAT_*` |
| 복호화 ITM/DAT 26 | `work/h4/decrypted/ITM/DAT/_ITM_*` |
| 복호화 NPC 7 | `work/h4/decrypted/NPC/*` |
| 복호화 FR 3 | `work/h4/decrypted/FR/_FR_*` |
| dialogue corpus | `work/h4/converted/dialogue_corpus.json` (35,752 lines) |
| top frequent | `work/h4/converted/dialogue_top_texts.json` |
| HDAT-A entry catalog | `work/h4/converted/hdat_a_parsed.json` |
| **통합 catalog** | **`work/h4/converted/h4_catalog.json`** (heroes + skills + items + npc) |
| R69 검증 | `work/h4/converted/round69_decrypt_results.json` |
| Android assets | `apps/hero4-android/app/src/main/assets/` (496 PNG + JSON) |
| Round 68 상세 | `docs/h4/round68-des-key-discovered.md` |
| Round 69 상세 | `docs/h4/round69-skill-catalog-and-batch-decrypt.md` |

## 신규 도구 (R68 + R69)

| 도구 | 용도 |
|---|---|
| `tools/recon/find_h4_des_key_v5.py` | DES key v5 brute-force (Hero3 binary cross-game + curated keys) — R68 발견 |
| `tools/converter/decrypt_h4_scn.py` (수정) | mx-des / std-ecb / std-cbc 3 mode, --input_dir 옵션 |
| `tools/converter/decrypt_h4_all_des.py` | 49 파일 batch decrypt + entropy 검증 + Korean sample |
| `tools/converter/parse_h4_hdat_a.py` | HDAT-A 8 파일 entry layout 분석 (name marker + stride) |
| `tools/converter/build_h4_catalog.py` | 통합 Hero4 catalog 빌드 (h4_catalog.json) |

## 진행률 갱신 (R69 시점)

| 영역 | R67 | R68 | R69 |
|---|---|---|---|
| 자산 포맷 분석/변환 | ~95% | ~98% | **~100%** |
| 대사 corpus 한국어 | 0% garbage | 100% (35,752) | 100% (검증 + 안정) |
| 게임 시스템 데이터 (캐릭터+스킬+아이템) | 0% | 0% | **100% (catalog 통합)** |
| 암호화 시스템 | ~70% | **100%** | 100% (407 파일 전체 확정) |
| Phase A | 99% | 100% | **100% (Hero4 자동 영역 진짜 끝)** |
| Phase B (Ghidra) | 30% | 30% | 30% (선택적) |
| Phase C (KMM) | 0% | 0% | 0% (engine wiring 대기) |
| Phase D (iOS) | 0% | 0% | 0% |

**Hero4 Android remake 완성 기준**: 약 **40-45%** (Phase A 끝, engine wiring부터 진행)

## 핵심 lesson (Round 68 + 69)

1. **Cross-game vendor analysis 가 Ghidra 보다 빠를 수 있다**: Hero3 R57 + Hero5 h5_des.py 가 이미 같은 vendor 의 DES variant 를 풀어둠. Hero4 만으로는 v1-v4 (~10시간 시도) 모두 실패. cross-game 검증 1시간만에 해결.
2. **암호 변종은 부분 모델링 X**: S1[58] 1 byte 만 수정하는 v4 는 실패. swap+reversed subkey 까지 풀 변종 적용 필수.
3. **DES key 발견 즉시 모든 sentinel-공유 파일 검증**: 49 파일 49 hit. cipher prefix sentinel 통계가 미리 모든 같은-키 파일을 식별해 둠.
4. **Vendor 가 8-byte ASCII key 를 path string 직후에 평문으로 저장**: Hero3 (`0EP@KO91` after `/dat/des_dat`), Hero4 (`J@IWO8N7L0E7E` after `/DAT/_DAT_DES`). 한빛소프트 표준 패턴.
