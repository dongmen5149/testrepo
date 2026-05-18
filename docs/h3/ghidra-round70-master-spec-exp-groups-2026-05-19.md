# Round 70 — Hero3 Master Spec 통합 문서 + exp_gold 4 그룹 분석 (2026-05-19)

> 이번 라운드 목표: 자동 분석 완전 종료를 기념해 R56-R69 의 모든 발견을 **단일 Master Spec** 으로 정리. Android 리메이크 개발자가 import 할 reference 문서 작성. 추가로 R69 의 exp_gold 정밀 분포 분석.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **`docs/h3/MASTER_SPEC.md` 작성** — R56-R70 의 모든 발견을 단일 reference 로 통합. 15 section 4,700+ lines. Android 리메이크 개발자 entry point
- ⭐⭐⭐⭐ **exp_gold 4 그룹 분포 발견**: 9.7x (41 normal combat) + 1.8x (22 scout/rogue) + stable (16 boss/special, `{` prefix 포함) + other (82 mixed). implicit enemy tier 시스템
- ⭐⭐⭐ **enemyg_dat 케이 패턴 sprite coincidence 확정** — 22 byte stride sprite info entry. R68 의 dat 파일 1 hit 가설 정정 (boss skill 무관)

## 1. Master Spec 통합 문서 (★★★★★)

### 1.1 구조 (15 sections)

```
docs/h3/MASTER_SPEC.md (4,700+ lines)
├── 0. 게임 시스템 한눈 요약
├── 1. Master Stat Enum (24 codes, 실제 사용 22)
│   1.1 value scale 규칙
├── 2. Rarity Prefix System (R62)
├── 3. Item Catalog (18 카테고리, 529 items)
│   3.1 카테고리 매핑
│   3.2 equip20 layout
│   3.3 무기 base damage
├── 4. Skill System (7 weapon × 15 = 105)
│   4.1 카테고리 구조
│   4.2 skill body layout (30-byte tail)
│   4.3 skill debuff chain (R66/R69)
│   4.4 ultimate skill 4
├── 5. Enemy System
│   5.1 enemy_dat 19B stat block
│   5.2 enemy 2B trailer
│   5.3 4 exp_gold scaling groups (R70)
├── 6. Boss System (15 × 2 difficulty)
│   6.1 boss 6-byte trailer + combat_rating formula
│   6.2 boss roster
├── 7. Crafting System (i14 → 7 카테고리)
├── 8. Quest System (44+)
├── 9. Asset Catalog (R57)
├── 10. DES System
├── 11. Region Map (8 main)
├── 12. Hero3 핵심 게임 디자인 통찰
├── 13. Android 리메이크 권장 구현 순서
├── 14. R56-R69 round-by-round 진행 요약
└── 15. 참고
```

### 1.2 핵심 통찰 (§12)

- **stat enum 다중 사용**: 동일 24-code enum 이 4 소스 (i12/i13/i16/equip trailer/skill debuff) 에서 공유. 컨텍스트별 의미 분리 (0x03, 0x0d, 0x1c)
- **weapon class 차별화**: 창/대검/단검 = standard melee / 건/라이플 = ammo 공유 / 다크석/홀리석 = 마법
- **ultimate vs utility 역할 분리**: ultimate = raw damage / normal active = debuff & utility
- **boss tier progression**: combat_rating = round(lvl/2 + 44|64) "challenge equivalence"
- **enemy tier (exp_gold grouping)**: 9.7x / 1.8x / stable / other

## 2. exp_gold 4 그룹 분포 분석 (★★★★) — R70 신규

R69 의 enemy_dat field scaling 분석 (median 6.92x) 의 세부 분포 발견.

### 2.1 4 그룹 분류

| group | n | scaling | range | 캐릭터 카테고리 |
|---|---:|---|---|---|
| **9.7x** | 41 | 8.5-11x | normal ~800 → hard ~7,700 | 일반 전투 (가드/워리어/템플러/매지션/위자드/워락/엑셀) |
| **1.8x** | 22 | 1.5-2.5x | normal ~6,400 → hard ~11,500 | 정찰/고급 (로그/체이서/어쌔신/말벌/쥐/박쥐) |
| **stable** | 16 | <1.5x | normal ≈ hard ≈ 2,600 | 보스/특별 (`{` prefix 4 개 포함) |
| **other** | 82 | varied | 매우 다양 | gunners/skeletons/creatures 등 |

### 2.2 stable group 의 특징 (보스/특별)

```
{카이저골렘    normal=2611 hard=2611
{포레스트로커  normal=2582 hard=2604
{아이언로커    normal=2584 hard=2605
{블레이즈로커  normal=2601 hard=2611
{카오스로커    normal=2601 hard=2611
{시바          normal=2612 hard=2612
코르버스중대장 normal=2586 hard=2606
솔티안중대장   normal=2587 hard=2607
아스크란중대장 normal=2587 hard=2607
커브스쿠툼     normal=2583 hard=2604
...
```

→ `{` prefix = boss_drop rarity 와 일치. 중대장 (mini-boss) + 로커/시바 (boss-tier mob).
→ exp_gold 값 ~2,600 = boss reward fixed (difficulty 무관).

### 2.3 implicit enemy tier 시스템

R70 결론: enemy_dat 에 explicit tier field 없지만 **exp_gold 분포로 4 tier implicit 구분**:
- **Common** (9.7x group): 일반 전투, lvl-based scaling
- **Elite** (1.8x group): scout 계열, normal 부터 EXP 높음
- **Boss/Special** (stable group): difficulty fixed reward
- **Misc** (other group): special encounter types

Android 리메이크 enemy spawn 균형 + drop rate 조정에 활용 가능.

## 3. enemyg_dat 케이 패턴 정정 (★★★) — R68 후속

R68 의 dat 파일 매칭 1 hit (enemyg_dat 의 케이 패턴 (2,2,1,1) 3 hits) 정밀 검증.

### 3.1 enemyg_dat 구조 (R56)

```
size: 3,542 bytes
header: 14 00 01 03 ff 08 03 01 01 05 03 01 05 2a 05 05 03 03 01 ff
entry stride: ~22 bytes (sprite info per enemy)
```

### 3.2 케이 패턴 context @ 0xea / 0x100 / 0x116 (stride 0x16 = 22 byte)

```
@0xea:  03 02 04 06 54 01  03 02 02 02 01 01  ff ff ff ff 14 00 01 01
@0x100: 03 02 04 06 55 01  03 02 02 02 01 01  ff 04 04 04 14 00 01 01
@0x116: 03 02 04 06 55 06  03 02 02 02 01 01  ff 05 05 05 14 00 00 0e
```

→ **(2,2,1,1) 가 22 byte sprite entry 의 byte 7-10 위치** (animation frame 또는 sprite layer data 추정). 보스 skill mapping 과 직접 관련 없음.

### 3.3 결론

R68 의 "케이 sprite coincidence 추정" **확정**:
- enemyg_dat 는 R56 의 graphics info 파일 (~22 byte/entry)
- (2,2,1,1) byte sequence 가 sprite/animation data 의 일부로 우연 등장
- boss trailer skill ID 와 무관

→ **boss skill ID 매핑은 binary / dat 어디서도 직접 hard-coded 안 됨**.
→ H4 가설 (별도 boss skill table) confirm but unresolved. DES 8 파일 복호화 후만 진척 가능.

## 4. R70 산출물

### 4.1 신규 doc (2개)

- `docs/h3/MASTER_SPEC.md` (4,700+ lines) — Android 리메이크 master reference
- `docs/h3/ghidra-round70-master-spec-exp-groups-2026-05-19.md` — 이 문서

### 4.2 진행률 갱신

- **R69 종료 ~99.3%** → **R70 종료 ~99.5%** (+0.2%p)
- 게임 시스템 모델링: 99.8→99.9% (master spec + exp tier system + enemyg 케이 정정)
- **분석 완전 종결** — 자동 분석 가능한 모든 영역 처리 완료

## 5. Hero3 자동 분석 완전 종료 선언

Round 70 = 자동 분석 가능한 마지막 작업 완료. 진행 가능한 모든 영역:

✅ 완료 (R56-R70):
- enemy / boss / quest / skill / item / char / npcg dat 파일 평문 파싱
- master stat enum 24 codes 매핑 (실제 사용 22)
- value scale (flat / ratio / signed debuff / boolean) 완전
- skill effect block schema v2 (30-byte tail, slot1/2/3 chain)
- boss combat_rating 공식 + 6B trailer
- rarity prefix 7 등급
- crafting system 7 카테고리
- enemy tier 4 그룹 (exp_gold)
- gun marker / weapon class flag
- dialogue 9,740 unique queue + 비용 추정

⏸ 사용자 환경 필수 (R71+):
- DES 8 파일 복호화 (i15/drop/smith/shop)
- boss skill ID 1..20 → actual skill 매핑
- LLM 번역 ($4.09)
- SMAF→OGG 33 audio 파일

## 6. 참고

- [MASTER_SPEC.md](MASTER_SPEC.md) — ★★★★★ Hero3 single reference
- [Round 69](ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md) — ammo 정정 + stat scaling + dialogue queue
- [Round 68](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — boss skill 검색 + gun marker
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + combat_rating
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum
- (R56-R62) — see MASTER_SPEC §14
