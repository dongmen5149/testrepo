# Hero4 Round 81 — `_H_BH` 4 stat block 정체 + R76 정정

> R71 의 "4 hero stat blocks" 해석을 정정. R76 의 `_ITM_03` 사용자 미스터리 해소.

## TL;DR

**`_H_BH` 4 entries = 2 영웅 × 2 mode** (4명 아님).

| entry | byte[2] global idx | byte[3] hero_id | name | offset |
|---|---|---|---|---|
| 0 | 0x00 | 0 (티르) | 티르 | pos 0..39 (40B) |
| 1 | 0x01 | 0 (티르) | 티르 | pos 40..79 (40B) |
| 2 | 0x02 | 1 (루레인) | 루레인 | pos 80..127 (48B) |
| 3 | 0x03 | 1 (루레인) | 루레인 | pos 128..167 (40B) |

영웅 = **티르 + 루레인 2명만** (catalog 의 `heroes.count=2` 와 일치). 4 stat block 의 4 는 **mode/form 개수** (각 영웅이 2 mode).

## Entry structure

```
[size_field:1B=0x26][00][global_idx:1B][hero_id:1B][nlen:1B][name:EUC-KR][00][stat block...]
```

- 티르 EUC-KR (4B) → entry size 40B
- 루레인 EUC-KR (6B) → entry size 48B (entry 2) 또는 40B (entry 3, 다른 stat 패딩)

Stat 영역 (entry 0 위치 [10..15] 기준):
- 티르 mode 0: `0b 07 08 06 1e 06` = 11/7/8/6/**30**/6
- 티르 mode 1: `06 0b 07 08 00 06` = 6/11/7/8/0/6
- 루레인 mode 0: `0a 07 08 08 32 04` = 10/7/8/8/**50**/4
- 루레인 mode 1: `05 09 07 0b 00 04` = 5/9/7/11/0/4

→ mode 별 starting stat 정의 (lvl/HP/MP/ATK/etc).

## R76 `_ITM_03` 사용자 정체 해소

R76 매핑 정정:

| weapon DAT | 매핑 | 영웅 + mode |
|---|---|---|
| `_ITM_01` (highest dual) | S000 양손검 | **티르 mode 0** |
| `_ITM_02` (mid dual) | S002 마검 | **티르 mode 1** |
| `_ITM_00` (mid-low dual) | S003 단도+마법 | **루레인 mode 1** |
| `_ITM_03` (lowest dual) | _(2nd 캐릭터 정체)_ | **루레인 mode 0 (검 변종)** ★ |
| `_ITM_04..06` (single-ATK) | S001 사격 sub-types | **루레인 mode 0 (사격)** |

→ 루레인은 **2개의 mode 0** weapons 보유 가능성: 검 (`_ITM_03`) + 사격 (`_ITM_04..06`). 실제 게임 내 switch logic 또는 storyline 분기 시 변환.

또는 (대안): `_ITM_03` 가 4 mode-character matrix 의 1개 빈 슬롯 (루레인 mode 1 = 단도+마법 _ITM_00 사용, mode 0 = 검 _ITM_03 + 사격 _ITM_04..06 다중 무기).

heroes.list[0] note 의 "_H_S000 / _H_S002 (variants)" 표현 = 티르가 2 mode 보유한다는 직접 증거.

## R71 가설 정정

R71 의 "168B = 1B header + 4 entries × 가변 + 2B trailer" 표현은 정확하지만 **entries 가 4 영웅이 아니라 2 영웅의 4 form** 임을 명확화. R71 후속에서 캐릭터 수 = 4 라고 추정한 다른 문서들 정정 필요.

## 다음 후보

1. ⭐ 루레인이 실제로 검/사격 다중 mode 인지 검증 (게임 dialogue corpus 의 mode-switching 문구 검색)
2. _H_BS / _H_SA / _H_SS 파일 분석 — 추가 hero stat 영역
3. 보스 phase stat 강화율 정량 (R76-R80 연속 분석 마감)
4. 트랙 C (ITEMDROP/smith/shop dat)

## 산출

- 재복호화: `work/h4/decrypted/HDAT/_H_BH` (168B)
- `docs/h4/round81-hero-bh-resolved.md` (이 문서)
