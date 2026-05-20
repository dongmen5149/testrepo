# Hero4 Round 107 — 죽음의 구 countdown timer 단위 검증 (R98 후속)

> R98 의 pos[63-64] LE16 = 600/480/360 가 **초(seconds)** 단위인지 구조·코퍼스 교차 검증.

## TL;DR

| 검증 | 결과 |
|---|---|
| 3 stage 시퀀스 | `_ESDAT_0/1/2` @ `0x331b` — **600 → 480 → 360** 재현 |
| stage 간 차이 | **-120 고정** (3 stage 모두) |
| 72B entry 전수 스캔 | 600/480/360 은 **이름 `죽음의 구` + offset 0x331b 만** |
| dialogue | `10분`/`8분`/`6분` **0 hits** — `죽음의 구` 는 ESDAT 3회만 |
| **단위 결론** | **LE16 = seconds** → **10분 / 8분 / 6분** (신뢰도: 구조 high, 대사 none) |

## 단위 가설 비교

| 가설 | divisor | stage 0→2 표시 | -120/step | 채택 |
|---|---|---|---|---|
| **seconds** | 60 | 10 / 8 / 6 **분** | 2분 | **✅** |
| two_minute_blocks | 120 | 5 / 4 / 3 blocks | 1 block | 가능하나 UI 표기와 불일치 |
| centiseconds | 100 | 6.0 / 4.8 / 3.6 분 | 1.2분 | 비정수 분 표기 |
| deciseconds | 10 | 60 / 48 / 36 초 | 12초 | 보스 제한으로 과장 |

`600 % 60 == 0`, `480 % 60 == 0`, `360 % 60 == 0` — 정수 분 환산이 깔끔함.

## 게임 디자인 해석

- `_ESDAT_0` → `_ESDAT_1` → `_ESDAT_2` = **월드 스테이지 진행**에 따른 난이도·보상·**시간 압박** 동시 상승
- HP 120→322→437, gold 3339→13621→18499 와 timer 감소가 **동일 방향** (후반일수록 짧은 제한)

## 한계

- SCN/대사에 분 단위 문구 없음 → Ghidra `BATTLER`/`ESDAT` 로더에서 `×60` 또는 tick 변환 여부는 미확인
- 엔진이 내부 tick(예: 2초)으로 저장해도 **저장값 자체는 초 단위 정수**로 보는 것이 가장 단순

## 산출

- `tools/converter/parse_h4_death_sphere_timer_verify.py`
- `work/h4/converted/h4_death_sphere_timer_verify.json`
- `h4_catalog.json` → `death_sphere.timer_unit_verify`

## 다음 후보

1. **환수 합신 / 환수특공 / 환수증폭 dialogue 검색** (R103) — HDAT skill 파일에만 1 hit each, SCN 0
2. **type=0 magic skill sub-categorization** (R104)
3. **R100 milestone 결산 문서**
