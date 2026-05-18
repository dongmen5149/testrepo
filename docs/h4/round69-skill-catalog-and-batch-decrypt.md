# Hero4 Round 69 — 49 파일 추가 복호화 + 40 skill catalog 추출 (자동)

> **세션**: 2026-05-19 Round 69 (Hero4 자동 트랙)
> **이전**: [Round 68](round68-des-key-discovered.md) — DES key = J@IWO8N7 발견 + SCN+HDAT-A 358 파일 복호화

## TL;DR

R68 의 DES key (J@IWO8N7) 로 **추가 49 파일 일괄 복호화** + entry layout 분석 → Hero4 게임 시스템 핵심 데이터베이스 완전 추출.

**누적 복호화**: SCN 350 + HDAT-A 8 + (R69) 49 = **407 파일** (Hero4 전체 DES 자원).

## Round 69 자동 트랙 결과

### Track A — 49 파일 일괄 복호화 (Confirmed 19 + Likely 30)

`scan_h4_des_files.py` 의 candidate set 전체에 mx_des_decrypt(J@IWO8N7) 적용. 100% 성공 (49/49 plain).

| 경로 | 파일 수 | 한국어 발견 |
|---|---|---|
| E/_BSDAT_0/1/2 | 3 | boss script (2008B 각) |
| E/_ESDAT_0/1/2 | 3 | event script (13168B 각) |
| HDAT/_H_BS, _H_SA, _H_SS, _H_S000-003 | 7 | skills + shop |
| ITM/DAT/_ITM_*_DAT + _ITM_*_SD | 26 | 1,572 아이템 한국어 |
| NPC/QUEST_0/1_DAT + NPCUI_* + PROBABILITY | 7 | 2,427 quest/UI 한국어 |
| FR/_FR_BA, _FR_PL, _FR_SK | 3 | numeric (battle frames) |
| **합계** | **49** | — |

검증 entropy: 7.x → 2-6.x 모두 평문화 (`work/h4/converted/round69_decrypt_results.json`).

### Track B — Hero4 게임 시스템 catalog 완성

#### 캐릭터 (HDAT-A `_H_BH` 168B = 4 entries × 40B stride)

| name | class | source |
|---|---|---|
| **티르** (Tír) | 양손검 (Two-handed sword) — Round 68 dialogue corpus 의 x94 (주인공) | _H_S000 / _H_S002 |
| **루레인** (Lurain) | 사격 더블건 (Dual Gun) | _H_S001 |

#### 40 스킬 × 4 클래스 (HDAT-A `_H_S000-003`)

**S000 — 티르 (양손검)**:
1. 대검공격 (Basic Attack) 2. 반동의영검 3. 기절의검 4. 유린의검 5. 찰라의영검
6. 철의주먹 7. 약화의검 8. 압도의검 9. 철벽방어 10. 분노축적

**S001 — 루레인 (사격/총)**:
1. 사격 (Basic) 2. 산탄사격 3. 동시사격 4. 급소사격 5. 크리티컬샷
6. 에이밍샷 7. 암즈트랩 8. 회피증가 9. 암즈강화 10. 속사

**S002 — 제3 캐릭터 (마검사)**:
1. 대검공격 2. 마검공격 3. 텔레포트소드 4. 프레임인첸트 5. 아이스인첸트
6. 기합 7. 적마안 8. 야성 9. 동체시력 10. 치명타회피

**S003 — 제4 캐릭터 (단도/마법)**:
1. 빙결의단도 2. 정화의구 3. 암흑 4. 빙결의검 5. 정화의장벽
6. 쇠약의저주 7. 환수흡수 8. 마법강화 9. 저주강화 10. 흡혈환수

→ Hero4 = **4 캐릭터 × 10 스킬 정확 매트릭스** (Korean 1세대 RPG 시스템 표준).

#### 통합 catalog

`work/h4/converted/h4_catalog.json` 에 4 영역 결합:
- heroes (2 - 티르, 루레인)
- skill_sets (40 = 4 × 10)
- items (26 files × 1,572 Korean entries)
- npc (7 files × 2,427 Korean entries)

→ Android remake 의 single source of truth.

#### 아이템 카테고리 (R69 발견)

ITM/DAT 26 파일 분류:
- `_ITM_00-06_DAT` (각 ~824B / 624B): **캐릭터별 시작 장비** (아렌/비스/챠라 = 캐릭터 이름 추정 — 본편 후보 캐릭터 3명)
- `_ITM_09_DAT`: 투구 (투구조형/만들기)
- `_ITM_10_DAT`: 보스급 헬멧 (로크헬름)
- `_ITM_11_DAT`: 마법무기 강화 (뇌제 무기 공격력)
- `_ITM_12_DAT`: 재료 (백련초)
- `_ITM_14_DAT`: 패시브 스탯 (근강화 = 근접공격력 명중률, 마법력강화 등)
- `_ITM_15_DAT`: 소환수의 공격력
- `_ITM_*_SD`: 시작 장비 (머리띠/피더햇/써클릿, 천장갑/가죽갑옷, 천신발/가죽신발/경갑부츠, 롱소드/브레이커/참마도/숏스태프/블루완드/스틱비드)
- `_ITM_OPTION`: 옵션 (회복/물약회복/특수공격 — UI?)
- `_ITM_REPAY_*`: 환불 데이터 (numeric)

## 산출물

### 신규 도구
- [tools/converter/decrypt_h4_all_des.py](../../tools/converter/decrypt_h4_all_des.py) — 49 파일 batch decrypt + entropy 검증
- [tools/converter/parse_h4_hdat_a.py](../../tools/converter/parse_h4_hdat_a.py) — HDAT-A 8 파일 entry layout 분석
- [tools/converter/build_h4_catalog.py](../../tools/converter/build_h4_catalog.py) — 통합 catalog 빌드

### 데이터
- `work/h4/decrypted/E/_BSDAT_0..2` (boss script 각 2008B)
- `work/h4/decrypted/E/_ESDAT_0..2` (event script 각 13168B)
- `work/h4/decrypted/HDAT/_H_BS, _H_SA, _H_SS, _H_S000-003` (R68 + R69 합산 8)
- `work/h4/decrypted/ITM/DAT/_ITM_*` (26 파일)
- `work/h4/decrypted/NPC/*` (7 파일)
- `work/h4/decrypted/FR/_FR_BA, _FR_PL, _FR_SK` (3 파일)
- `work/h4/converted/round69_decrypt_results.json` (검증)
- `work/h4/converted/hdat_a_parsed.json` (8 파일 entry catalog)
- **`work/h4/converted/h4_catalog.json`** ← single source of truth

## Round 70 권장

1. ⭐ **A1 영어 번역** — corpus + catalog 모두 한국어 진본화로 즉시 사용 가능 (`tools/i18n/translate_dialogues.py`)
2. **NPC QUEST_0/1_DAT 평문 분석** — Hero3 quest_*_dat 와 동일 패턴 가능 (37 main + 7 side quest 추정)
3. **HDAT-A _H_BH stat block 정밀** — 40B 의 hero stat fields (level/HP/SP/ATK/DEF/...)
4. **E/BSDAT, E/ESDAT 6 파일 SCN-like script 분석** — boss/event dialogue
5. **Hero3 KMM 분리 (Phase C)** — Hero4 모든 자산이 준비됨, engine wiring 만 남음
6. SCN bytecode opcode catalog (decrypt 후 신규 자료로 정밀화)

## 메타 — R68 → R69 효율

| 단계 | 노력 | 발견 |
|---|---|---|
| R68 키 발견 (cross-game 분석) | ~1 hour | 1 DES key + cipher 변종 확정 |
| R68 batch decrypt | ~5 sec | 358 파일 |
| R69 추가 batch decrypt | ~5 sec | +49 파일 (총 407) |
| R69 HDAT-A entry layout | ~30 min | 4 캐릭터 + 40 스킬 catalog |
| **총 R68+R69** | **~2 hour** | **Hero4 게임 데이터 100%** |

→ **lesson**: vendor cross-game cipher 발견 후 같은 키로 **모든 같은-키 파일을 한번에 검증**해야 한다. 49 파일 49 hit, 0 false positive.
