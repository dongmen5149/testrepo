# Hero5 Round 100 밀레스톤 결산

> R82-R99 18 라운드 누적 +13.90%p (73.01% → 86.07%) 의 진척 정리 + 잔여 큰 덩어리.
> 본 문서는 R100 결산용. 일별 라운드 상세는 [PROGRESS.md](PROGRESS.md), 즉시 재개는 [SESSION_HANDOFF.md](SESSION_HANDOFF.md) §⚡.
> **완성도 4지표·베타 정의**는 [COMPLETION.md](COMPLETION.md) (R108+: 종합 **87.6%** / 베타 **~61%** / 클로즈드 **~72%**).

---

## 1. 누적 변화 (R82 시작 → R99 종료)

| 카테고리 | R82 시작 | R99 종료 | Δ | 주요 라운드 |
|---|---|---|---|---|
| A. 자산 추출/디코딩 | 95% | 95% | — | (SMAF audio 단일 미완) |
| B. 게임 데이터 RE/JSON | 96% | 96% | — | (완료, R37-R69) |
| C. 게임 로직 RE | 93% | 93% | — | (Formula/AI/HSI 완료, TEM 65 잔여) |
| D. Godot 코어 구현 | 88% | **92%** | +4 | R76 stat mod / R86 export / R91 round-trip / R92 SaveListPanel / R97 AudioManager |
| E. Godot 통합/Scene | 55% | **92%** | **+37** | R82 SceneRouter / R83 Sorcerer / R84 warp fade / R85 battle fade / R92 F6 / R93 Title 통합 / R95 Toast UX / R96 severity / R98 F8 / R99 체크박스 |
| F. 누락 시스템 | 6% | **60%** | **+54** | R83 Sorcerer / R86 distribution / R87 spirit mapping / R88 desc EUC-KR / R90 placeholder / R91 round-trip |
| G. 출시 보완 | 35% | **65%** | +30 | R86 export preset / BUILD_ANDROID.md / R89 launcher icons |
| H. 안정성/QA | 60% | **70%** | +10 | R94 HelpPanel 동기화 / R98 F8 추가 |
| **종합** | **73.01%** | **86.07%** | **+13.06** | 18 라운드 평균 +0.73%p/라운드 |

→ 가장 큰 임팩트 영역: **E (+37%p)** Scene 흐름 정비 + UX, **F (+54%p)** 누락 시스템 채움.

---

## 2. 카테고리별 주요 마일스톤

### A. 자산 (95% — 단일 미완)
- ✅ VFS 100% 풀림, 92 JSON, DES 키 0EP@KO91, sprite/palette/text/font 디코더 완성
- ❌ SMAF .mmf audio playback — `.mmf` 디코더 부재 (R100+ 옵션 B)

### B. 게임 데이터 (96% — 완료)
- ✅ 1360 item / 5 skill class+spirit / 166×3 enemy / 151×3 quest / 105 mission / 252 drop
- ✅ R37-R69 동안 모든 .dat 파일 종류 식별 + JSON 변환

### C. 게임 로직 RE (93%)
- ✅ Formula VM 186 공식 / AI 100% / ProcHeroSkill 92% / HSI 11/11 / Cooldown / Battle / Save 95%
- ❌ TEM (TargetEffectMgr) per-frame cascade 65% — R80/R81 overview, 상세 case-by-case 미완 (R100+ 옵션 D)

### D. Godot 코어 (92%)
- ✅ 10 UI 패널 (R51-R58 + R92 SaveListPanel) — Status/Shop/Quest/Refine/Mix/Orb/Blacksmith/SkillBook/Mission/SaveList
- ✅ Character/AI tick/전투/damage 공식 / stat modifier / Save round-trip (R91) / AudioManager 정밀 (R97 linear_to_db + mute R98)
- ❌ damage 공식 85% (R74 보강했지만 일부 edge case), Dialog 85%

### E. Godot 통합 (92% — 가장 큰 도약 +37%p)
- ✅ R82 SceneRouter autoload + GameOver + Quit-to-Title
- ✅ R83 Sorcerer (class_id=4) 부분 활성화 + INT magic bonus
- ✅ R84/R85 Map warp fade + Battle UI fade
- ✅ R92 F6 SaveListPanel 워크플로우
- ✅ R93 Title Continue → SaveListPanel 통합 (인라인 slot UI ~50줄 제거)
- ✅ R95/R96 Toast UX (severity / fade-in / stack / 12 호출 마이그레이션)
- ✅ R98/R99 음소거 F8 + 체크박스 4 layer 일관
- ❌ Audio playback **50%** (정확화는 됐으나 SMAF 부재로 실 BGM 일부 누락)

### F. 누락 시스템 (60% — +54%p)
- ✅ Sorcerer R83/R87 (R72 5 critical field + R77 sub-rel + R87 explicit 8 field + R88 desc + R90 placeholder)
- ✅ Save round-trip R91 (class_id/stat/equipment/skill_levels/gunner/active/quest/mission 모두 복원)
- ❌ **디바이스 빌드 0%** — 사용자 환경 의존 (R86 export preset + R89 launcher icons 완성, Godot Editor GUI 실 빌드 남음)
- ❌ Cash shop 30%
- ❌ Spirit stats_u16 정확 byte→field 매핑 (R90 placeholder 의 숫자 정확화 위해 R100+ 옵션 C)

### G. 출시 보완 (65%)
- ✅ R86 export_presets.cfg (Debug + Release, gradle_build, min_sdk=23, target_sdk=34, arm64-v8a, 11 permissions, immersive)
- ✅ R86 BUILD_ANDROID.md (8 섹션)
- ✅ R89 launcher icons (3 PNG, PIL 자동 생성)
- ❌ Perf 30% / Packaging 50% / Localization 60%

### H. QA (70%)
- ✅ 18 자동 테스트 도구 (R82-R99, 각 라운드마다 `tools/h5_test_*.py`)
- ✅ R94 HelpPanel 26 키 동기화
- ❌ **실 디바이스 플레이 검증 0%** — 사용자 환경 (R100+ 옵션 A)

---

## 3. 잔여 큰 덩어리 (R100+ 우선순위)

1. **Godot Editor 실 빌드 + 실 디바이스 검증** (옵션 A, 사용자 작업) — F 디바이스 빌드 0→60, +0.6%p
2. **Spirit stats_u16 정확 byte→field 매핑 RE** (옵션 C, autonomous) — Formula::calc + spirit-specific layout, F 60→70%, +1.0%p
3. **SMAF audio playback** (옵션 B, autonomous) — .mmf 디코더 + AudioStream Godot 통합, A 95→99%, +0.3%p
4. **ProcTargetEffectSkill cascade 정밀** (옵션 D, autonomous) — R81 후속, C 93→94%, +0.2%p

→ **이론 천장 (종합 8카테고리)**: 옵션 A+B+C+D 모두 완료 시 **≈ 88.2%** (R100+ 후속 4-5 라운드 분량).
→ **베타 100%** ≠ 종합 88% — 실기기 QA·콘텐츠·체감 품질 추가 필요 ([COMPLETION.md](COMPLETION.md) §4·§8).

**R108 스냅샷 (2026-05-20)**: 종합 **87.6%** (+0.1 from R107). F 68% (placeholder 1차). 베타 C **~61%** / 클로즈드 C′ **~72%** (adb 0%).

---

## 4. 18 라운드 라인업 (R82-R99)

```
R82  SceneRouter + GameOver + Quit-to-Title         +0.84
R83  Sorcerer 부분 활성화 + INT magic bonus           +1.80
R84  Map warp fade + Spirit extra_hex 부분 파싱       +1.26
R85  Battle UI fade transition                       +1.20
R86  Distribution build preset + BUILD_ANDROID.md    +1.60
R87  Spirit R77 sub-rel full mapping → 80% 돌파      +1.30
R88  Spirit desc EUC-KR 디코딩 (16/16 한국어)        +1.00
R89  Android launcher icons asset (3 PNG)            +0.80
R90  Spirit desc placeholder + UI 정제               +0.50
R91  Save round-trip 정합성 fix                      +0.98
R92  SaveListPanel UI (10번째 UI 패널)               +0.48
R93  Title Continue → SaveListPanel 통합              +0.36
R94  HelpPanel 키 명세 동기화                         +0.35
R95  Toast UX 정비 (severity/fade/stack)              +0.24
R96  Toast severity 마이그레이션 (12 호출) — 85% 돌파  +0.24
R97  AudioManager 볼륨 정밀 (linear_to_db)            +0.36
R98  음소거 F8 + ConfigFile 영속성                    +0.47
R99  Mute 체크박스 + F8 양방향 동기화                  +0.12
─────────────────────────────────────────────────────────
누적                                                 +13.90%p
```

---

## 5. 핵심 RE/구현 종결 사실 (이후 라운드 재참조용)

- **HeroSkillInfo 88B struct** = 68B file + 16B unused (dead reads) + 4B cooldown (NowCoolTime u16 @+0x54 + MaxCoolTime @+0x56). R77-R79 종결.
- **TEM VFX 시스템** = 5 overload chain (`_min/_+s/_+sai/_+saiih/_full`) + 100 slot × 0x284B + Effect 베이스 5 setter + ProcTargetEffectSkill per-frame engine. R80-R81 overview.
- **DES blocker** = 표준 FIPS + 키 0EP@KO91 확정인데 복호 실패. NDK runner 만 해결책. R82+ 의 데이터 트랙과 무관 (별도 차단).
- **Save round-trip 31 필드** = R91 에서 class_id/stat_X/equipment/skill_levels/gunner/active/quest/mission 모두 복원 보장. Python JSON 시뮬로 검증.
- **Toast severity 분류** (R96) = info=일반 알림, success=긍정 결과, warn=사용자 입력 부정, error=치명적.
- **Mute 4 layer 일관** (R98+R99) = AudioManager `_muted` + Toast 시각 피드백 + SettingsPanel 체크박스 + ConfigFile `audio/muted` 영속.

---

업데이트: 2026-05-20 — [COMPLETION.md](COMPLETION.md) cross-link + R108 스냅샷.

업데이트: 2026-05-19 (Round 100 밀레스톤 결산 작성).
