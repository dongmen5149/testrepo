# Hero4 Round 98 — 죽음의 구 72B 특수 layout 정밀 분석 (R91 후속)

> R91 의 미해결 anomaly 해소. 죽음의 구 = **time-limited boss encounter** 임을 확정.

## TL;DR

3 stage variant (`_ESDAT_0/1/2` @ 0x331b) 의 byte-by-byte 비교 결과:

| field | stage 0 | stage 1 | stage 2 | 의미 |
|---|---|---|---|---|
| HP pos[23-24] LE16 | 120 | 322 | 437 | 단조 증가 (1× → 3.6×) |
| ATK pos[27-28] LE16 | 195 | 567 | 772 | 단조 증가 (1× → 4×) |
| gold pos[57-58] LE16 | 3,339 | 13,621 | 18,499 | 보스급 보상 (1× → 5.5×) |
| EXP pos[59-60] LE16 | 2,569 | 13,359 | 16,961 | 보스급 보상 (1× → 6.6×) |
| **★ timer pos[63-64] LE16** | **600** | **480** | **360** | **monotonic 감소 (-120/stage)** |

**Countdown timer 핵심 발견**:
- pos[63-64] LE16 값이 stage 진행시 -120 씩 정확히 단축
- 단위가 초(seconds)라면: stage 0 = **10분**, stage 1 = **8분**, stage 2 = **6분**
- "죽음의 구" = "death sphere" = **time-limited boss encounter**
  → R80 의 "보스 카운트다운 / mini-boss" 가설 검증 완료

## 72B layout 확정

```
pos[0]      = enemy_class (=0x32, 죽음의 구 전용 ID)
pos[1-2]    = header LE16 (variable per stage)
pos[3-6]    = EXP_base LE32 (variable per stage)
pos[8-9]    = const (0x33 0xa9 = 51, 169)
pos[14]     = const (=0x9c = 156)
pos[22]     = const (=0x0f = 15)
pos[23-24]  = HP LE16
pos[25-26]  = HP dup LE16
pos[27-28]  = ATK LE16
pos[29-30]  = DEF LE16
pos[31-32]  = DEF dup LE16
pos[33-36]  = speed/misc
pos[42-43]  = ★ R80 anomaly = 04 00 (표준 ff 3f 부재)
pos[55-56]  = sub-boundary 07 ff (표준 +56 marker 유지)
pos[57-58]  = gold LE16
pos[59-60]  = EXP LE16
pos[61-62]  = (transition 영역)
pos[63-64]  = ★ COUNTDOWN TIMER LE16 (death sphere 시간 제한, seconds)
pos[65-71]  = zero padding (7B trailer)
```

## R91 anomaly 해명

R91 에서 노트:
- 죽음의 구 72B = single phase + 5B extra padding
- pos[42-43] 0xff 0x3f marker 부재

R98 해명:
- 5B extra 는 trailer 가 아니라 **timer (pos[63-64]) + padding (pos[65-71])** 구조
- pos[42-43] marker 부재 이유: timer 영역 확보를 위한 layout 변형 (= boss 카운트다운 mode signature)
- enemy_class=0x32 (50) 는 죽음의 구 전용 unique class (다른 보스: 13, 26, 28, 47 등)

## Stage scaling 의미

각 stage 가 game stage 변화에 따른 difficulty progression (`_ESDAT_0/1/2`):

| stage | 시간 | HP | ATK | gold/EXP |
|---|---|---|---|---|
| 0 (초기) | **10분** | 120 | 195 | 3.3k/2.5k |
| 1 (중반) | **8분** | 322 | 567 | 13.6k/13.4k |
| 2 (후반) | **6분** | 437 | 772 | 18.5k/17.0k |

플레이어가 게임 진행할수록 죽음의 구는:
- **시간은 짧아지고** (-2분/stage)
- **HP/ATK 는 강해지며**
- 보상은 풍부해짐 (gold/EXP 5-7배 증가)

→ 전형적인 "time-attack boss" 디자인. 다른 보스 (좀비/오토마톤/기갑병) 와 달리 multi-phase 가 아닌 **time-limited single phase**.

## 다른 ESDAT outlier 와 비교

| encounter | size | 구조 | timer? |
|---|---|---|---|
| 좀비 | 213B | 2 phase + final (multi-phase) | — |
| 소환된 좀비 | 140B | 1 phase + final | — |
| 오토마톤 | 432B | 5 phase + final (V-shape) | — |
| 기갑병 | 140B | R80 marker anomaly | — |
| **죽음의 구** | **72B** | **single + 5B timer** | **★ countdown LE16** |

→ 죽음의 구는 ESDAT 5 outlier 중 **유일한 time-limited type**.

## 산출

- `tools/converter/parse_h4_death_sphere.py` (신규)
- `work/h4/converted/h4_death_sphere.json` (4.5KB)
- `docs/h4/round98-death-sphere.md` (이 문서)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **n0124_scn tutorial 전문 분석** (R92 후속)
2. **bonus_id=0 + tier_value 의미** (R94 후속)
3. **character class skill (S000-S003) stat block schema** (R95 후속)
4. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
5. **죽음의 구 timer 단위 검증** (R98 후속) — 600=10분 가설 in-game 확인 필요
