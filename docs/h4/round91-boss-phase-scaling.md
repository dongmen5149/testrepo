# Hero4 Round 91 — Multi-phase boss encounter stat scaling 정량

> R80 의 "보스 phase stat 강화율 정량" 후속. 4 outlier multi-phase encounter 의
> phase 별 stat 추출 + scaling 계산.

## TL;DR

ESDAT 4 outlier 의 phase 별 stat 추출 결과 **2 패턴** 확인:

| 패턴 | encounter | phase 0 → final scaling | 설명 |
|---|---|---|---|
| **Monotonic climb** | 좀비 (2+1) | HP +17%, ATK +9%, DEF +12% | 단순 강화형 |
| **V-shape (dip+climb)** | 오토마톤 (5+1) | HP +27%, ATK +33%, DEF +24% | phase 1 dip → 최종 peak |
| Boss → loot | 소환된 좀비 (1+1) | HP -12%, ATK -15% | phase 0=peak, final=defeat-state |
| Anomaly | 기갑병 (1+1) | HP +54%, ATK +49% (DEF stable) | 0xff 0x3f marker 부재 |

각 phase 가 **enemy_class byte (pos[0]) 도 함께 전환** → 단순 stat scaling 이 아니라 visual/skill 도 변화.

## 4 outlier 전체

### 좀비 (213B = 2 × 73 + 67) — 단순 단조 증가형

| phase | enemy_class | HP[23] | ATK[35] | DEF[37] | gold[57] | EXP[59] |
|---|---|---|---|---|---|---|
| 0 | 13 | 175 | 2,825 | 6,144 | 2,569 | 2,053 |
| 1 | 28 | 175 | 2,825 | 6,144 | 2,569 | 2,053 |
| final | 28 | **204** | **3,082** | **6,912** | **3,339** | **2,569** |
| ratio | — | 1.166× | 1.091× | 1.125× | 1.300× | 1.251× |

- phase 0 → 1 = visual transition (class 13 → 28) **but stat 동일**
- phase 1 → final = stat 단조 증가 (12-30% range)
- gold 가 가장 크게 증가 (1.30×), DEF 가 가장 적게 (1.13×)

### 오토마톤 (432B = 5 × 73 + 67) — V-shape (대표 5-phase 보스)

| phase | enemy_class | HP[23] | ATK[35] | DEF[37] | gold[57] | EXP[59] | 해석 |
|---|---|---|---|---|---|---|---|
| 0 | 13 | 154 | 2,316 | 5,376 | 2,569 | 2,053 | 등장 |
| 1 | 26 | 97  | 1,289 | 3,584 | 1,025 | 0     | **취약 cinematic** |
| 2 | 26 | 138 | 2,059 | 4,864 | 2,053 | 1,025 | 회복 |
| 3 | 26 | 158 | 2,316 | 5,632 | 2,569 | 2,053 | 회복 완료 |
| 4 | 47 | 179 | 2,825 | 6,144 | 2,569 | 2,053 | **boss form 진화** |
| final | 47 | **195** | **3,082** | **6,656** | **3,339** | **2,569** | enraged 최종 |
| p0 → final | — | 1.27× | 1.33× | 1.24× | 1.30× | 1.25× | |

- enemy_class 3 distinct forms (13 → 26 → 47) — 등장/중간/최종 3 단계 visual
- phase 1 "취약" 상태에서 EXP=0 (드랍 없음) → 컷씬/이벤트 phase 가설
- 최종 phase 가 모든 stat 의 max value

### 소환된 좀비 (140B = 1 × 73 + 67) — 역방향 패턴

| phase | enemy_class | HP[23] | ATK[35] | DEF[37] | gold[57] | EXP[59] |
|---|---|---|---|---|---|---|
| 0 | 13 | 208 | 3,338 | 7,168 | 3,339 | 2,569 |
| final | 28 | 183 | 2,826 | 6,400 | 2,569 | 2,053 |
| ratio | — | 0.88× | 0.85× | 0.89× | 0.77× | 0.80× |

- phase 0 stats > final stats → "final" 이 강화 phase 가 아닌 **defeat / loot drop** config 일 가능성
- 또는 "소환된 좀비" 가 등장 시점이 peak (소환 직후 강력) → 시간 흐름에 따라 약화

### 기갑병 (140B = 1 × 73 + 67) — R80 anomaly

| phase | enemy_class | HP[23] | ATK[35] | DEF[37] | gold[57] | EXP[59] |
|---|---|---|---|---|---|---|
| 0 | 9 | 39 | 520 | 2,560 | 1,025 | 0 |
| final | 26 | 60 | 776 | 2,560 | 0 | 0 |
| ratio | — | 1.54× | 1.49× | 1.00× | 0× | — |

- pos[42-43] = `33 33` (R80 가 지적한 marker 부재)
- HP/ATK 단조 증가, DEF 고정, reward 부재 (gold=0, EXP=0)
- 다른 outlier 와 layout 미세 차이 — encounter 가 아니라 **mini-boss / minion variant** 가설

## 6B inter-phase link 검증 (R80 재확인)

오토마톤 5 phase link 추적 (R80 표 재현):

| phase 전환 | sig[67-68] | phase_id[69-70] | transition[71-72] |
|---|---|---|---|
| 0 → 1 | 0x47 0x00 | 654 | `bf fa` (continue) |
| 1 → 2 | 0x47 0x00 | 655 | `bf fa` (continue) |
| 2 → 3 | 0x47 0x00 | 656 | `bf fa` (continue) |
| 3 → 4 | 0x47 0x00 | 657 | `b1 bc` (**final 진입**) |
| 4 → final | 0x47 0x00 | 658 | `b1 bc` (final) |

R80 검증 ✓ — phase_id 가 sequential (654-658), `b1 bc` 가 final phase 진입 marker.

## Stat scaling 패턴 요약 (메인 보스 좀비/오토마톤 기준)

phase 0 → final monotonic 비율 (V-shape 의 dip 무시 시):

| stat | 좀비 | 오토마톤 | 평균 |
|---|---|---|---|
| HP   | 1.17× | 1.27× | **~1.22×** |
| ATK  | 1.09× | 1.33× | **~1.21×** |
| DEF  | 1.13× | 1.24× | **~1.19×** |
| gold | 1.30× | 1.30× | **1.30×** |
| EXP  | 1.25× | 1.25× | **1.25×** |

**결론**: 보스의 last-phase 강화율 = HP/ATK/DEF 약 +20-25%, 보상은 +25-30% 추가. ratio 가 보스마다 매우 일관됨 (특히 gold/EXP 정확히 1.30× / 1.25×) — **공식 기반 scaling 가능성**.

## 산출

- `tools/converter/parse_h4_boss_phases.py` (신규)
- `work/h4/converted/h4_boss_phases.json` (13.8KB)
- `docs/h4/round91-boss-phase-scaling.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **dialogue corpus 환수 등장 빈도** (R87 후속) — 베놈/헤지호그 × 35,752 대사
2. **`_H_SA` group_id ↔ 5 환수 매핑 검증** (R88 후속)
3. **`_H_SA` ability skill_id 카테고리 식별** (R88 후속)
4. **element byte[5]=2 검증** (R89 후속)
5. **Q_REPAY drop_id 의미** (R90 후속)
6. **죽음의 구 72B 정밀** (R91 미해결) — 특수 layout encounter
7. **R78 stat field 의미 확정** — R91 의 일관된 ratio 가 HP[23-24] 가설을 강화
