# Hero4 Round 79 — ESDAT outlier (boss-tier) encounter 구조

> R78 의 67B 정형 인카운터 분석 위에서 5 outlier entries (72B/140B/213B/432B) 의 구조 해독.

## TL;DR

5 outlier ESDAT entries = **multi-phase boss encounters** (같은 적의 여러 모드/페이즈).

핵심 발견: **0xff 0x3f section marker 가 정확히 73B 간격으로 반복**.

| name | size | marker 위치 | phase 수 (가설) |
|---|---|---|---|
| 죽음의 구 | 72B | (없음) | 1 (특수 형식, marker 없음) |
| 기갑병 | 140B | [115] | 2 (linked encounter) |
| 소환된 좀비 | 140B | [42, 115] | 2 phases |
| 좀비 | 213B | [42, 115, 188] | 3 phases |
| 오토마톤 | 432B | [42, 115, 188, 261] | 4+ phases |

inter-marker 차이: 115-42 = 73, 188-115 = 73, 261-188 = 73 → **73B/phase 고정**.

## 구조 가설

```
phase = 67B encounter + 6B inter-phase link = 73B
```

67B 정형 인카운터 (R78) 위에 6B link 데이터 (다음 phase ID? sound trigger?) 추가 → 73B repeating block.

오토마톤 432B 의 경우:
- Header (선택): 0-41 (= 42B, first marker 이전)
- Phase blocks: 4 × 73B = 292B
- 잔여: 432 - 42 - 292 = 98B (trailer / 추가 phase + reward)

## 보스 일반 패턴

같은 적이 **67B 일반 인카운터 + outlier 보스 인카운터** 둘 다 보유:
- "오토마톤" entries: 67B × 6 (일반 적 그룹) + 432B × 1 (보스 페이즈) = **일반/보스 dual-mode**
- 보스 phase 의 stat 은 일반 entry stat 보다 강화 (예상 — 향후 정량 검증)

## R78 67B 와의 일관성

`0xff 0x3f` marker 위치 = pos[42-43] (R78 확정) ↔ outlier 의 첫 marker 도 pos[42] = 일치.
67B body = single-phase encounter (마지막 marker = pos[42] 1회만).
73B+ block = multi-phase boss encounter.

## 다음 후보

1. **6B inter-phase link 내용 분석** (pos[67-72] 구조)
2. 오토마톤 432B 의 마지막 98B trailer 정밀
3. 보스 phase stat 강화율 정량 (일반 67B 대비)
4. `_H_BH` 4번째 stat block 캐릭터 식별 (R76 미해결, `_ITM_03` 사용자 정체)

## 산출

- `docs/h4/round79-esdat-outliers.md` (이 문서)
- (도구 변경 없음 — 분석만)
