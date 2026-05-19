# Hero4 Round 76 — Weapon Class × Character Class 매핑

> **세션**: 2026-05-19 (R75 직후 연속 자동 트랙 A)
> **이전**: [SESSION_HANDOFF.md](SESSION_HANDOFF.md) 트랙 A, [round70-75-summary.md](round70-75-summary.md)

## TL;DR

R75 의 7 weapon classes (_ITM_00..06) 와 R69 의 4 character classes (S000..S003) 를 데미지 프로파일 + level 진행 곡선 으로 매핑.

| weapon DAT | type | dmg avg | level curve | 매핑 | 영웅 |
|---|---|---|---|---|---|
| `_ITM_01_DAT` | dual-ATK | 65.0 (최대) | 1→94, step 3 | **S000 양손검** | **티르** |
| `_ITM_02_DAT` | dual-ATK | 55.6 | 1→92, step 3 | **S002 마검** | 티르 (alt) / 3번째 영웅 |
| `_ITM_00_DAT` | dual-ATK | 46.8 | 1→91, step 2 | **S003 단도+마법** | 4번째 영웅 (미확인) |
| `_ITM_03_DAT` | dual-ATK | 45.4 (최소) | 1→93, step 4 | (예비 / NPC class) | 미확인 |
| `_ITM_04_DAT` | single-ATK | 106.9 | 1→95, step 4 | **S001 권총** | **루레인** |
| `_ITM_05_DAT` | single-ATK | 101.6 | 1→95, step 4 | **S001 저화력총** | 루레인 |
| `_ITM_06_DAT` | single-ATK | 97.0 | 1→95, step 4 | **S001 중화기** | 루레인 |

산출물: [`work/h4/converted/h4_weapon_class_mapping.json`](../../work/h4/converted/h4_weapon_class_mapping.json) + Android 자산 배포 (`apps/hero4-android/app/src/main/assets/h4_weapon_class_mapping.json`).

## 핵심 근거

### 1. Dual-ATK vs Single-ATK 구분

- _ITM_00..03 모두 `ATK1 > 0` AND `ATK2 > 0` → **두 손/양손 dual-strike** 모델 (검/단도)
- _ITM_04..06 모두 `ATK1 > 0`, `ATK2 == 0` → **단일 타격** (총류, 한 발 = 한 데미지)

이는 R69 의 4 character class 중 `S001 사격` 만 단일 발사 무기 = single-ATK 와 정확히 부합.

### 2. Level 진행 곡선의 유니크성

dual-ATK 4종 (`_ITM_00..03`) 의 level 진행이 서로 다름:
- `_ITM_00`: 1, 3, 6, 11, 16, 21, ... (step 2 → 5)
- `_ITM_01`: 1, 4, 9, 14, 19, ... (step 3 → 5)
- `_ITM_02`: 1, 4, 7, 12, 17, ... (step 3 → 5)
- `_ITM_03`: 1, 5, 8, 13, 18, ... (step 4 → 5)

→ 각 class 가 **독립된 캐릭터의 등급표** 라는 가설 강화.

single-ATK 3종 (`_ITM_04..06`) 은 진행 곡선이 동일 (1, 5, 10, 15, ..., 95) → **한 캐릭터의 무기 sub-type** 3종.

### 3. 스킬셋과의 cross-check

| skill set | top skill names | 무기 적합성 |
|---|---|---|
| S000 | 대검공격/반동의영검/유린의검/찰라의영검 | dual-strike 검 (✓ _ITM_01 highest dmg) |
| S001 | 사격/산탄사격/동시사격/급소사격/속사 | 총류 (✓ single-ATK) |
| S002 | 대검공격/마검공격/프레임인첸트/아이스인첸트 | 마검 (검+속성) (✓ _ITM_02 mid dmg + 속성 flag) |
| S003 | 빙결의단도/정화의구/암흑/빙결의검/저주강화 | 단도+마법 (✓ _ITM_00 mid-low) |

## 미해결 질문

1. **`_ITM_03` 의 사용자** — 4 dual class > 3 sword 캐릭터 (S000+S002+S003) → 1개 잉여. NPC/적 전용 또는 잠금 클래스 가능성. R71 의 4 hero stat blocks 가 단서.
2. **`_H_BH` 4번째 stat block 의 캐릭터 이름** — R71 에서 가변 길이로 정밀화는 했으나 3-4번째 entry 의 식별이 _필요. dialogue corpus 에서 티르(94회)/루레인 외 빈도 상위 캐릭터 cross-check 추천.
3. **`_ITM_04/05/06` 의 sub-type 정확명** — handgun/rifle/heavy 가설은 데미지 곡선 기반 추정일 뿐. 한국어 원본 매뉴얼 또는 게임 내 상점 UI screenshot 필요.
4. **property_flag 0-7 의미** — R74 에서 추정만. 원소속성? 등급? 추가 분석 트랙 별도 필요.

## 다음 트랙 추천

- ⭐ **트랙 B**: BSDAT body opcode dispatch (R72 의 88 boss script body 풀이) — SCN opcode 와 비교
- **트랙 C**: ITEMDROP / smith / shop dat 정밀
- _H_BH 4 stat block 의 3-4번째 entry 식별 (캐릭터 발굴) → `_ITM_03` 사용자 확정 가능

## commit

이 라운드 산출:
- `tools/analysis/map_h4_weapon_classes.py` (신규)
- `work/h4/converted/h4_weapon_class_mapping.json` (생성, gitignore)
- `apps/hero4-android/app/src/main/assets/h4_weapon_class_mapping.json` (배포)
- `docs/h4/round76-weapon-class-mapping.md` (이 문서)
