# Hero4 Round 108 — 환수 combo skill dialogue 검색 (R103 후속)

> R103 의 mode-2 환수 combo 가설을 dialogue corpus 로 검증.

## TL;DR

R103 에서 발견한 5 환수 관련 skill 의 등장 파일을 전수 검색한 결과:
- **5 skill 모두 catalog (`_H_S002`/`_H_S003`) 에 1 hit 만 등장**
- **scene / NPC / event dialogue 등장 = 0**
- → R103 가설 **mode-2 mechanic-only, story 노출 없음** 강력 검증
- R92 의 "환수 시스템 = 상점 NPC + tutorial scene 도입, 메인 story 영향 최소" 패턴 그대로 연장

## 결과

| skill | class | total | by_role | dialogue hits |
|---|---|---|---|---|
| 환수 합신 | _H_S002 (티르 마검) | 1 | catalog_hdat=1 | **0** |
| 환수특공 | _H_S003 (루레인 마법) | 1 | catalog_hdat=1 | **0** |
| 환수증폭 | _H_S003 | 1 | catalog_hdat=1 | **0** |
| 환수흡수 | _H_S003 (primary) | 1 | catalog_hdat=1 | **0** |
| 흡혈환수 | _H_S003 (primary) | 1 | catalog_hdat=1 | **0** |

(corpus = 252 파일 / 484,512 bytes EUC-KR 전수 검색)

## 해석

1. **mode-2 진입 / combo 발동 시 별도 system dialogue 없음** — gameplay 의 mechanic 으로만 존재
2. R86–R99 의 환수 시스템과 동일 패턴: `_H_SS`/`_H_SA` catalog + `NPCUI_GUARDIANSHOP_DAT` 상점 + `n0124_scn` tutorial 외 story 부재
3. 환수 시스템 전체가 **side-mechanic** 으로 설계됨 — 메인 시나리오 (62 quest) 진행과 독립적

## R103 가설 검증 매트릭스

| 가설 | R103 근거 | R108 dialogue 검증 |
|---|---|---|
| alt-form = mode-2 advanced variant | ✅ MP cost 1.5× / lvl_req mid-tier | ✅ catalog-only, mechanic-level |
| 환수 합신/특공/증폭 = combo skill | ✅ 이름·class·환수 cross-link | ✅ catalog 외 노출 0 = system skill |
| S003 = 소환사 class 핵심 | ✅ 환수흡수/흡혈환수/특공/증폭 모두 S003 | ✅ S003 만 4/5 hit |

## 산출

- `tools/converter/parse_h4_summon_combo_dialogue.py` (신규)
- `work/h4/converted/h4_summon_combo_dialogue.json` (3,495 B)
- `docs/h4/round108-summon-combo-dialogue.md` (이 문서)

## 다음 후보 (남은 자동 트랙)

1. **type=0 magic skill sub-categorization** (R104 후속)
2. **R100 milestone 결산 문서** (`MILESTONE_R100.md` — R68–R108 누적)
3. 사용자 트랙: A1 영어 번역, Phase C Step 4d Compose MP
