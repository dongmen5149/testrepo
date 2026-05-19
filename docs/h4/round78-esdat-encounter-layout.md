# Hero4 Round 78 — ESDAT 67B encounter body layout

> R76 Track B 의 "0x3f opcode 274회" 실체 해명. ESDAT 67B 인카운터 정의 구조 분석.

## TL;DR

3 `_ESDAT_{0,1,2}` = **같은 157 일반 적의 난이도 3 stage 버전**. 67B body 가 152/157 entries (97%) 차지하는 균일 인카운터 정의.

핵심 발견: **R76 의 "0x3f opcode 274회" 는 opcode 가 아니라 section boundary marker**.

```
pos[0-41]   섹션 A: 적 분류 + base stat (HP/MP/ATK/DEF)
pos[42-43]  ★ 0xff 0x3f 경계 마커 (125/150 = 83%)
pos[44-55]  섹션 B: drop item id 또는 sub-record
pos[56]     ★ 0xff sub-boundary (119/152)
pos[57-66]  섹션 C: gold/EXP reward + trailer
```

## 적 분류 (pos[0] enemy class byte)

샘플 entries 첫 byte:
- 공화국 보병 → `0x0d`
- 공화국 사수 → `0x0e`
- 공화국 기갑병 → `0x09`
- 오토마톤 / 고대종 / 악령 / 유충 (top names)

→ pos[0] = enemy class/family ID, animation sheet 와 매핑.

## Stat field 위치 (>60% entry monotonic)

LE16 stat 위치: 2, 3, 23, 25, 27, 28, **29-30** (max/cur pair), 31, 35-40, 47, **49-50** (pair), 51, 56-60.

가설:
- pos[2-3] = stage-variant EXP base
- pos[23-25] = HP_max
- **pos[29-30 == 31-32** 인 케이스 다수 → 그 페어가 HP max/current 일 가능성
- pos[35-40] = ATK/DEF 페어 묶음
- pos[47-50] = drop probability + drop item id
- pos[57-60] = gold reward (큰 값)

## 정정/제한

- 67B 외 5/157 entries (140B / 213B / 432B / 72B) 는 별도 layout — 보스/이벤트 인카운터 가능성. 후속 분석 대상.
- pos[56] 의 0xff 가 119/152 (78%) 로 다소 약함 — sub-boundary 라기보단 "선택적 marker" 또는 stat 값 우연 일치.
- 23/150 entries 가 pos[42-43] 마커 부재 — variant 인카운터 (다른 layout) 또는 0xff 0x3f 마커가 다른 위치에 존재.

## R76 가설 정정

| R76 가설 | R78 실체 |
|---|---|
| `0x3f` opcode dispatch | section boundary marker (0xff 0x3f) |
| 0xff separator 평균 1.7/entry | 2 separator: pos[42] + pos[56] |
| script-like text record | base-stat + reward 의 정형 binary |

ESDAT 는 **script bytecode 가 아닌 stat block** 으로 BSDAT 와 동일 부류. SCN bytecode 분석은 350 SCN 파일에서만 적용.

## 후속

1. ⭐ pos[44-55] 의 drop item id LE16 → R75 의 349 items catalog 와 cross-reference
2. pos[57-60] gold/EXP 값 stage scaling 정량화
3. 5 outlier entries (140B/213B/432B/72B) 분석 — boss-tier 인카운터?
4. 트랙 C 미진행: ITEMDROP/smith/shop dat

## commit

- `tools/analysis/esdat_encounter_layout.py`
- `work/h4/converted/h4_esdat_encounter_layout.json`
- `docs/h4/round78-esdat-encounter-layout.md` (이 문서)
