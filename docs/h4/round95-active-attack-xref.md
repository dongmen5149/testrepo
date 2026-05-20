# Hero4 Round 95 — element byte[5]=2 검증 + R89 정정

> R89 가 byte[5]=2 를 "element" 로 명명했으나, 전 코퍼스 cross-ref 로
> **byte[5]=2 가 element 가 아닌 summon-exclusive subtype marker** 임을 확정.

## TL;DR

전 decrypted 252 파일에서 0x14 ACTIVE_ATTACK signature 를 검색한 결과:

| 항목 | 결과 |
|---|---|
| 검색된 파일 | 252 |
| 0x14 signature 발견 파일 | 11 |
| **clean valid hit (byte[5]∈{2}, valid speed/range/anim)** | **5 (모두 `_H_SS`)** |
| 기타 false-positive (coincidental 0x14 byte, all-zero supporting fields) | 16 |

→ byte[5]=2 는 **`_H_SS` (환수 catalog) 전용** 의 invariant marker. character class skill, ESDAT, ITM, SCN 등에서는 valid ACTIVE_ATTACK template 부재.

## Valid `_H_SS` ACTIVE_ATTACK 5 entries (R87/R89 재확인)

| 환수 | offset | damage | byte[5] | heal_flag | speed | range | anim |
|---|---|---|---|---|---|---|---|
| 베놈 뇌격 | 0x0116 | 300 | 2 | 0 | 53 | 120 | 4 |
| 헤지호그 뇌격 | 0x01fd | 200 | 2 | 0 | 53 | 100 | 4 |
| 그래비티 뇌격 | 0x02f3 | 400 | 2 | 0 | 53 | 160 | 5 |
| 쇼커 뇌격 | 0x03e3 | 300 | 2 | 0 | 53 | 140 | 5 |
| 세이프가드 회복 | 0x04cb | 500 | 2 | 2 | 61 | 100 | 20 |

5/5 모두 byte[5]=2. byte[5] 가 element 라면 "magic damage" 만 다루는 셈이지만, **5 환수 모두 동일 값** 이므로 variable element 가 아닌 invariant marker.

## False-positive hits 예시

| 파일 | 0x14 offset | byte[5] | 진단 |
|---|---|---|---|
| `FR/_FR_BA` @0x0215 | 0 | damage=24320 (= 0x5f00) — 다른 stat block 의 일부일 가능성 |
| `HDAT/_H_S003` @0x0012 | 0 | damage=8, speed=15 — 캐릭터 skill 의 일부 |
| `HDAT/_H_SA` @0x0039 | 0 | damage=2578 (= LE16 value), 다른 field |
| `MAP/SC/eXXXX_scn` | 1/6 | 비정형 — scn opcode byte 우연 |

이들 모두 byte[5] = 0/1/6 등 다양 → invariant `_H_SS` 와 명확히 구분됨.

## R89 정정

| 항목 | R89 | R95 |
|---|---|---|
| byte[5] 의 명명 | "element" | **"ACTIVE_ATTACK subtype marker"** |
| 의미 | 속성 (마법/물리 등) | **summon-exclusive 고정값 (=2 = 환수 attack)** |
| variable? | 다른 element 값 가능성 시사 | invariant — `_H_SS` 외 valid ACTIVE_ATTACK 부재 |

R89 의 PASSIVE_TEMPLATE byte[5] = subtype (6/7/11/12) 은 그대로 유효. ACTIVE_ATTACK 의 byte[5] 도 같은 layer 의 "subtype marker" 역할 — 단 ACTIVE_ATTACK 에서만 한 값(2) 만 사용됨.

## Character skill schema 미해결

`_H_S000`~`_H_S003` 의 character class skill 은 별개 stat block schema 사용. 각 skill 의 body 는 `[00][ff ff][00 00][...]` pattern + EUC-KR text suffix 형태. 23B fixed-size stat block 가 아닌 가변 길이.

이는 R96+ 별도 분석 트랙. 본 라운드는 R89 element 가설 검증만 완결.

## 산출

- `tools/converter/parse_h4_active_attack_xref.py` (신규)
- `work/h4/converted/h4_active_attack_xref.json` (6.5KB)
- `docs/h4/round95-active-attack-xref.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **Q_REPAY drop_id 의미** (R90 후속) — 32 entries 의 drop_id 가 ITM 아이템 idx 인지 검증
2. **죽음의 구 72B 특수 layout 정밀** (R91 후속)
3. **n0124_scn tutorial 전문 분석** (R92 후속) — 환수 시스템 in-game 설명
4. **bonus_id=0 + tier_value 의미** (R94 후속)
5. **character class skill (S000-S003) stat block schema** (R95 후속) — 가변 길이 body 정밀
