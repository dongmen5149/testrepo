# Round 62 — item trailer bonus / skill rank decode / quest cross-reference (2026-05-18)

> 이번 라운드 목표: R61 의 item body 와 skill body 디코드 결과를 더 정밀하게 파고들어, R61 에서 "padding" 으로 가정했던 영역의 숨은 의미를 식별. 추가로 i17 퀘스트 아이템을 quest_*_dat 의 실제 텍스트와 매핑한다.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐ **R61 의 "trailer 4B = padding" 가정 폐기** — 346 equip items 중 **177 (51.2%)** 가 trailer 에 (bonus_type, value) × 2 쌍을 담고 있음 (반지 i12 의 인코딩과 동일).
- ⭐⭐⭐⭐ **이름 prefix = rarity class** 발견 (7 등급): `|` magic 85 / `'` legendary 20 / `$` epic 40 / `{` boss_drop 29 / `@` endgame 16 / `}` quest_reward 12 / 평범 144.
- ⭐⭐⭐ **variant byte = sprite index** 확정 — 0xff = default 188회, 그 외 슬롯별 sequential 범위 (헬멧 0x78~0x9d, 갑옷 0x86~0x8f, 대검 0x36~0x4a, 단검 0x41~0x4c 등).
- ⭐⭐⭐ **skill rank progression byte 위치 = +0x1d** (tail 마지막 byte) — 1~3 (또는 1~5) 범위. rank 가 높을수록 +0x0f (tier-up bonus) 도 함께 증가 (0→10→20).
- ⭐⭐⭐ **cross-weapon discriminator cols** (+0x02 weapon ATK scale / +0x09+0x0a base damage / +0x0b 검 전용 +40 bonus / +0x0c 건 전용 #20 / +0x0f+0x11 라이플 전용).
- ⭐⭐⭐ **i17 21 quest items 중 20개를 quest_*_dat 텍스트에서 매칭** — 각 아이템의 등장 퀘스트와 NPC 컨텍스트 확정. 미매칭 1개 (반토막난 지도) = 튜토리얼/시작 아이템 추정.

## 1. Item trailer = 숨은 bonus 인코딩 (★★★★)

R61 디코드에서 20B equip body 의 `+16..+19` 가 모두 0 이라 padding 으로 가정했다. R62 에서 prefix 가 `|`, `'`, `$`, `{`, `@`, `}` 인 special-name item 들의 trailer 가 non-zero 임을 발견.

### 1.1 인코딩 구조

trailer 4B = `(b1_type, b1_value, b2_type, b2_value)`. 반지 (i12) 의 `bonus_type` 매핑을 그대로 재사용 가능.

### 1.2 분류 통계 (12 equip categories, 346 items)

| 항목 | 값 |
|---|---|
| 전체 equip items | 346 |
| trailer 가 0이 아닌 (bonus 보유) | **177 (51.2%)** |
| 등장 bonus_type 종류 | 17 |

### 1.3 bonus_type 빈도 (전체 trailer)

| code | type | 빈도 |
|---:|---|---:|
| 0x06 | INT | 32 |
| 0x0c | DEF? | 27 |
| 0x08 | **?08** | 26 |
| 0x05 | STR | 24 |
| 0x0a | AGI | 22 |
| 0x09 | **?09** | 21 |
| 0x07 | VIT | 19 |
| 0x10 | **?10** | 17 |
| 0x11 | **?11** | 15 |
| 0x02 | HP | 14 |
| 0x0f | EVA | 13 |
| 0x0d | MDEF? | 13 |
| 0x0b | **?0b** | 13 |
| 0x12 | ATK | 9 |
| 0x0e | HIT | 4 |
| 0x03 | **?03** | 3 |
| 0x04 | **?04** | 3 |
| 0x01 | **?01** | 2 |

새로 발견된 미분류 type code 8개 (0x01/0x03/0x04/0x08/0x09/0x0b/0x10/0x11) 는 R63 에서 effect_handler 함수 분석으로 매핑 후보. 가설:
- 0x08 = MATK (defenders 에 자주 등장)
- 0x09 = MDEF 추가 또는 정신력
- 0x0b = 마법 회피? (배리어자켓/나이트건틀릿)
- 0x10 = 카오스 류 (카오스후드/카오스슈트/카오스건틀릿)
- 0x11 = 사격계 (라이오넬/제비우스/데스리미터, 다 라이플)

## 2. Name-prefix = rarity class (★★★★)

R61 까지는 이름에 `|`, `'`, `$` 등이 붙은 것이 무엇인지 불명확했다. R62 에서 통계 패턴으로 **rarity grading** 임을 확인.

### 2.1 prefix → rarity 매핑표

| prefix | class | 등장 수 | trailer 패턴 |
|---|---|---:|---|
| (none) | normal | 144 | trailer = 모두 0 |
| `\|` | magic | 85 | bonus pair 1개 |
| `'` | legendary | 20 | bonus pair 2개 (보통 1개만 채움) |
| `$` | epic | 40 | bonus pair 2개 모두 채움 |
| `{` | boss_drop | 29 | high stat_primary, 2 bonus pair |
| `@` | endgame | 16 | tier ≥ 14, 가격 매우 낮음 (event reward) |
| `}` | quest_reward | 12 | non-shop item |
| `"` | hidden | (0) | 미관찰 |
| `#` | set_bonus | (0) | 미관찰 |

### 2.2 검증 예 (i0_dat 헬멧)

| name | prefix | tier | variant | req_lvl | stat_primary | trailer | 해석 |
|---|---|---:|---:|---:|---:|---|---|
| 머리띠 | none | 0 | 0xff | 2 | 2 | 00 00 00 00 | normal |
| 강화후드 | none | 16 | 0x7b | 21 | 14 | 00 00 00 00 | normal |
| \|붉은머리띠 | magic | 0 | 0x78 | 10 | 8 | 0c 05 00 00 | DEF+5 |
| \|황금투구 | magic | 6 | 0x80 | 45 | 31 | 0d 0a 00 00 | MDEF+10 |
| '명왕가면 | legendary | 7 | 0x81 | 60 | 40 | 0f 19 00 00 | EVA+25 |
| $드래곤헬름 | epic | 11 | 0x85 | 56 | 38 | 02 0a 0d 0a | HP+10 + MDEF+10 |
| {다크써클릿 | boss_drop | 14 | 0xff | 60 | 42 | 06 14 08 14 | INT+20 + ?08+20 |
| @홀리써클릿 | endgame | 14 | 0x79 | 70 | 49 | 09 0f 0c 0a | ?09+15 + DEF+10 |
| }공허의투구 | quest_reward | 15 | 0x9d | 55 | 42 | 00 00 00 00 | 보상용 (no bonus) |

## 3. Variant byte = sprite index (★★★)

R61 에서 variant byte 분포만 보았을 때 0xff 가 dominant (188/346) 인 것은 알았지만 0x78~0x9d 범위의 1회 등장 값은 의미 불명이었다. R62 에서 각 슬롯별로 분리해보면:

| slot | variant 분포 |
|---|---|
| i0 헬멧 | 0xff×17 + 0x78~0x9d (sequential) |
| i1 갑옷 | 0xff×21 + 0x86~0x8f, 0x01~0x06 |
| i4 창 | 0xff×13 + 0x6d~0x73 |
| i5 대검 | 0xff×13 + 0x36~0x3d |
| i6 단검 | 0xff×13 + 0x41~0x48 |
| i9 다크석 | 0xff×25 (모두 동일!) |
| i10 홀리석 | 0xff×25 (모두 동일!) |

**결론**: variant = "sprite override byte". 0xff = default (tier 기본 sprite 사용), 그 외 = 해당 slot 의 unique sprite ID. 다크/홀리석은 시각적으로 동일 (드롭만 다르고 sprite 1종).

## 4. Skill rank progression byte (★★★)

R61 에서 weapon_passive 7-tier (창술1~창술7) 가 어떻게 구분되는지 미해결이었다. R62 에서 column diff 로 식별:

### 4.1 30B tail template (창 weapon_passive 기준)

```
00 00 ?? 00 00 00 00 00 00 03 03 00 01 01 00 ?? 00 00 00 7f 00 00 00 00 7f 00 00 00 00 ??
   col +02 ----------- col +0f -------------- col +1d (rank)
```

| col | 의미 | 값 패턴 |
|---|---|---|
| +0x02 | "ATK scale" | small=2, large=20 (창술1=2, 창술2=20 등) |
| +0x09+0x0a | base damage | 창=3/3, 검=42/42, 단검=41/41, 사격=45/45, 격발=45/45, 영탄=64/64, 광아=64/64 |
| +0x0f | tier-up bonus | 0..0..0..0..0..10..20 (창술 6/7 만 비제로) |
| +0x1d | **rank tier** | 1, 1, 2, 2, 2, 3, 2 (skill power class) |

`+0x1d` 가 일관되게 1, 2, 또는 3 의 값을 가지며, 이는 stat 증가 누진 단계 = "rank tier" 로 해석 가능.

### 4.2 weapon-discriminator (tier 1 cross-weapon)

7개 weapon class 의 tier-1 mastery 비교:

| weapon | +0x02 | +0x09 (base) | +0x0b | +0x0c | +0x0f | +0x11 | +0x1d |
|---|---:|---:|---:|---:|---:|---:|---:|
| 창 | 2 | 3 | 0 | 1 | 0 | 0 | 1 |
| 대검 | 20 | 42 | 40 | 1 | 0 | 0 | 1 |
| 단검 | 2 | 41 | 0 | 1 | 0 | 0 | 1 |
| 건 | 2 | 45 | 0 | **20** | 0 | 0 | **2** |
| 라이플 | 20 | 45 | 0 | 1 | **20** | **5** | 1 |
| 다크석 | 2 | 64 | 0 | 1 | 0 | 0 | 1 |
| 홀리석 | 30 | 64 | 0 | 1 | 0 | 0 | 1 |

해석:
- **대검** = +0x0b 에 unique 40 bonus (양손검 특수 보너스: damage scaling 2배?)
- **건** = +0x0c 가 20 (다른 무기는 1) — base damage 외 burst hits 수 추정
- **라이플** = +0x0f/+0x11 nonzero (range 또는 piercing)
- **홀리석** = +0x02 = 30 (최대) — high tier scale 적용

## 5. i17 quest item ↔ quest_*_dat cross-reference (★★★)

i17 의 21 개 퀘스트 아이템을 quest_00/01/10/11_dat 의 EUC-KR korean_strings 에서 substring 매칭.

### 5.1 매칭 결과 표 (20/21 OK)

| item | quest file | 등장 quest 컨텍스트 |
|---|---|---|
| 시그널펜던트A/B | quest_11 | 토레즈 채굴장 / 엘지스의 임무 (`서쪽의 채굴장 / 시그널펜던트 / 토레즈`) |
| 협곡의성수 | quest_00/10 | 메인퀘 "협곡의 독소" / 남동쪽 주둔지대장장이 조합 |
| 의문의보석 | quest_00 | 메인퀘 "절망의 극복" / 의문의 신호 |
| 토레즈시민증 | quest_00/10 | 메인퀘 "시민증 확보" / 일레느와 만남 |
| 시크릿카드 | quest_00/10 | 메인퀘 "반전세력" / 로우엔 동쪽 공장 조합 |
| 영혼석 | quest_00/01 | 작은동굴 봉인지 5개 모으기 (피리로 세계를 돌며) |
| 토레즈의서신 | quest_00/01/10/11 | 토레즈 일레느와 재회 |
| 오래된보석함 | quest_01 | 평원남쪽 사령의동굴 → 테너의 유물 연결 |
| 로얄윈터하츠 | quest_01 | 네오솔티아 노아의 깨트린 펜던트 / 대장장이 조합 |
| 반토막난 지도 | — | **unmatched** (튜토리얼 아이템 추정) |
| 레아의수련목록 | quest_00 | 레아의 펜던트 / 시엔 |
| 유리엽서 | quest_01/11 | 광산도시 토레즈 조합 |
| 유리방패 | quest_01/11 | 리파이너의유적 / 엔자크 역사학자 / 학설의 증거 |
| 굴베이그의완드 | quest_00 | 메인퀘 "유적 강행돌파" / 코르버스 |
| 테너의유물 | quest_01 | 사령의동굴 / 영혼석의 단서 / 협곡남쪽 폐쇄공장 |
| 운디네의부적 | quest_11 | 엔자크 여관 종업원 선물 |
| 평화의문장 | quest_11 | 정령석 / 네오솔티아 대장장이 / 로우엔 동쪽 공장 |
| 일레느의노트 | quest_10 | 엘지스 / 일레느의 집 / 반전주의자들의 거점 |
| 총기부속 | quest_11 | 엔자크 용병길드 조합 |
| 영혼사슬 | quest_11 | 엔자크 용병길드 조합 |

### 5.2 quest 구조 식별

각 entry 의 일관된 끝 4 strings 패턴:
```
{지역} / {장소} / {액션} / {보상/연결}
```
예: `광산 / 남쪽의 / 검은공장 / 시민증의 / 획득`. 이는 R58 에서 추정한 (name, description, location, target, category) 5 필드 구조와 정합.

## 6. R63 작업 후보 (자동 가능 우선)

1. ⭐⭐⭐ **새 bonus_type code (0x01/0x03/0x04/0x08/0x09/0x0b/0x10/0x11) 의미 매핑** — binary 의 effect_handler 함수 (FUN_4f358 또는 stat_modify) literal pool grep 으로 type→string 테이블 추출.
2. ⭐⭐⭐ **enchant (i16) tail vs trailer 비교** — i16 의 4B tail 패턴이 equip trailer 와 인코딩이 같은지 검증 (같다면 enchant = movable trailer).
3. ⭐⭐ **i15_dat NDK runner 처리** (사용자 환경 — R60/R61 이월).
4. ⭐⭐ **rank progression vs req_level table** — skill 의 +0x1d rank tier 와 equip 의 req_level (5tier=10 lvl 간격) 의 매핑 (skill rank 1 ↔ lvl 10, rank 2 ↔ lvl 25, rank 3 ↔ lvl 40 추정).
5. ⭐⭐ **rarity prefix → 가격 modifier 분석** — magic = base×1, legendary = base×1.5, epic = ×2, boss_drop = ×3 가설 검증.

## 7. 산출물

| 종류 | 파일 |
|---|---|
| 신규 doc | [`docs/h3/ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md`](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) (이 문서) |
| 신규 recon 3 | `tools/recon/analyze_item_variants.py` / `tools/recon/decode_skill_rank.py` / `tools/recon/cross_ref_quest_item.py` |
| 신규 dump | `work/h3/recon/item_variants.{json,log}` / `skill_rank_decoded.{json,log}` / `quest_item_xref.{json,log}` |
| 갱신 | `docs/h3/PROGRESS.md` / `docs/h3/SESSION_HANDOFF.md` |

## 8. 진척률 갱신 (Round 62 시점)

| 영역 | R61 | R62 | 변화 |
|---|---:|---:|---|
| 자산 포맷 분석/변환 | ~98% | ~98% | 변화 없음 |
| 자산 변환 산출 | ~95% | ~95% | 변화 없음 |
| Ghidra 게임 로직 리버싱 | ~62-65% | ~62-65% | 변화 없음 (binary 분석 없음) |
| **데이터 모델링** | **78%** | **84%** | +6%p — trailer 51% 의미 발견 / rarity / skill rank / quest xref |
| Android 엔진 재구현 | ~5-10% | ~5-10% | 변화 없음 |

**전체 진행률**: ~86-89% → **~88-91%** (+2%p)
