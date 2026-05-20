# Hero4 Round 106 — `_ITM_OPTION` 1928B 구조 정밀 (R84/R105 후속)

> R84 의 텍스트 추출(120 run) + R105 의 LE16 qty 정정 이후, OPTION 파일 자체의 binary layout 을 확정.

## TL;DR

1928B `_ITM_OPTION` = **6B header + 122 variable entries + 5B tail**. 각 entry 가 3B 의미 payload `[effect_id][category][magnitude]` 를 갖는다. magnitude 가 level (L1-L4) 에 따라 monotonic 증가하는 패턴 확인.

R84 의 1928/16=120.5 non-integer 의문 해소: stride 는 fixed 가 아니라 **variable-length text entry**.

## Layout 확정

| 영역 | offset | 크기 | 의미 |
|---|---|---|---|
| header | 0..5 | 6B | `04 00 00 00 00 00` (LE32=4 = L1-L4 max level?) |
| entries | 6..1922 | 1917B | 122 entries (variable size) |
| tail | 1923..1927 | 5B | padding/sentinel `00 00 00 00 00` |

### Entry format

```
[size LE16] [nlen 1B] [name nlen B] [payload 3B]
```

- `size` = 2-byte 이후 payload 까지의 길이 = `nlen(1) + name(nlen) + 3` - 1 = name 자체 길이 + 3
- `nlen` = name 문자열 바이트 수 (EUC-KR, ASCII 혼합)
- `payload` = **항상 3 바이트 고정**

### Payload 3B semantic

| byte | 의미 | 관찰값 |
|---|---|---|
| `[0]` | effect_id | 0, 2,4,5,6,7,8,11,12,14-25,27,30,68,75,76,78,79,80,85,86,87,90 (33 unique pair) |
| `[1]` | category | 0 (normal stat, 101/122), **15** (proc, 18/122), **100** (스턴발동, 3/122) |
| `[2]` | magnitude | 1-20 — **L1→L4 monotonic 증가** |

## Monotonic magnitude 검증

| base name | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| HP회복 | 5 | 10 | 15 | 20 |
| HP흡수 | 5 | 10 | — | 15 |
| 근접공격 (id=12) | 5 | 10 | 15 | 20 |
| 마법공격 (id=15) | 5 | 10 | 15 | 20 |
| 명중 (id=17) | 5 | 10 | 15 | 20 |
| 회피 (id=19) | 5 | 10 | 15 | 20 |
| 저항 (id=21) | 3 | 6 | 10 | 13 |
| 원거리공격 (id=14) | 5 | 10 | 15 | 20 |
| 물리방어 (id=16) | 5 | 10 | 15 | 20 |
| 슬로우발동 (id=75 cat=15) | 5 | 10 | — | 15 |
| 화염발동 (id=78 cat=15) | 5 | 10 | — | 15 |
| 스턴발동 (id=68 cat=100) | 1 | 3 | — | 5 |

→ L3 누락은 일부 effect 의 데이터 결손 (R84 의 "스턴발동 L3 누락" 관찰과 일치).

## category byte 의미 (byte[1])

| value | count | 의미 |
|---|---|---|
| 0 | 101 | 일반 stat bonus / 평탄 증가 |
| 15 (0x0f) | 18 | **proc effect** (공격 시 부가효과 발동: 슬로우/넉백/화염/결빙/데미지반사) |
| 100 (0x64) | 3 | **스턴발동 전용** (높은 hitchance 분류? 100% 보장 stun proc) |

→ R84 의 "Proc / 발동" 분류가 binary 에서 cat=15 marker 로 명시되어 있음 확정.

## effect_id 0 의 의미 — "+ variant" 그룹

effect_id=0, cat=0 인 13 entries 의 base name 이 모두 `X +` 형태:
HPmax +, HP회복 +, 근접공격 +, 마법공격력 +, 무기공격력 +, 물리방어력 +, 마법방어력 +, 명중 +, 회피 +, 저항 +, 크리티컬 +, SP소모 +, 쿨타임감소.

→ effect_id=0 = **flat-additive 변종 표식**, 실 stat 분기는 engine 이 name string parsing 으로 처리하는 것으로 추정.

## effect_id ↔ base name 매핑 (cat=0 normal)

| id | base | id | base |
|---|---|---|---|
| 2 | HPmax | 19 | 회피 |
| 4 | HP회복 | 20 | 블록 |
| 5 | HP흡수 | 21 | 저항 |
| 6 | SPmax / Spmax | 22 | 크리티컬 |
| 7 | SP소모 | 23 | 크리데미지 |
| 8 | SP회복 | 24 | 직격 |
| 11 | SP분노 | 25 | 무기 |
| 12 | 근접공격 / 평균공격 | 27 | 쿨타임 |
| 14 | 원거리공격 | 30 | 무게 |
| 15 | 마법공격 | 80 | 물약회복 |
| 16 | 물리방어 | 87 | 레벨제한감소 |
| 17 | 명중 | 90 | 특수공격 / 사격/마법 / 사격/마법 보완 |
| 18 | 회피 (alt id 18 이름은 명중 변종) | | |

## R84 정정/확정 사항

| R84 | R106 |
|---|---|
| "120 text entries / 51 unique types" | **122 entries** (parsing 기반 정확), R84 미카운트 sentinel '0' 2개 포함 |
| "1928/16=120.5 non-integer (다른 stride?)" | **fixed stride 아님** — variable-length entry, header 6B + tail 5B 가 균등 stride 가설 깸 |
| "L3 누락 (스턴발동)" | **데이터 결손 확정** (binary 에 entry 자체 없음, encoder bug 가능성) |
| "Proc / 발동 분류" | **cat byte=15 marker** binary 에서 명시 |
| "양손검 보완 / 사격/마법 보완" | effect_id=90 그룹 (특수공격 등과 동일 id) |

## 산출

- `tools/converter/parse_h4_itm_option_struct.py` (신규)
- `work/h4/converted/h4_itm_option_struct.json` (~50KB+)
- `docs/h4/round106-itm-option-structure.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
2. **환수 합신 / 환수특공 / 환수증폭 dialogue 검색** (R103 후속)
3. **type=0 magic skill 의 sub-categorization** (R104 후속)
4. **R100 milestone 결산 문서**
5. **effect_id 0 의 "X +" variant 가 실 game engine 에서 어떻게 분기되는지** — Ghidra/디컴파일 필요 (자동 한계)
