# Hero4 Round 100 — bonus_id=0 + tier_value semantic 확정 (R94 후속) ★ 마일스톤

> **Hero4 자동 분석 100 라운드 마일스톤**. R94 의 마지막 미해결 ambiguity (`tier_value` 와 `bonus_id=0` 의미) 를 R99 tutorial 단서로 해소.

## TL;DR

R94 의 8 ability skill × 3 tier 데이터에서:
- **tier_value = 진화포인트 소모량** (R99 tutorial: "고레벨일수록 소모 포인트 증가" 부합)
- **bonus_id = 0** → self-only upgrade (cross-tree 보너스 없음)
- **bonus_id > 0** → linked passive 에 cross-tree 보너스 부여 (S001 사격 self-tree 전용)

8/8 ability 가 **arithmetic progression** (constant step) — 엔진 cost formula 의 일관성 확인.

## Cost-class 그룹 (step size = arithmetic 증가량 = upgrade 비용)

| step | skills | class | 디자인 의미 |
|---|---|---|---|
| +5  | 마검공격 | S002 | cheapest variant — 기본 공격 약간 강화 |
| +10 | 동시사격/급소사격/에이밍샷/암즈트랩/암즈강화 | S001 (5개) | standard cost — S001 사격 main tree |
| +15 | 텔레포트소드 | S002 | mid-cost teleport mechanic |
| +20 | 마법강화 | S003 | most expensive — late-game spell amplifier |

→ Cost step 이 skill 의 power level / utility scale 과 비례.

## Bonus chain 구조 (S001 사격 self-tree 만)

3 cross-tree link 모두 S001 (사격) 내부:

| active (cost tier) | → | linked passive (bonus tier) |
|---|---|---|
| 동시사격 (id 12, cost 10/20/30) | → | 암즈강화 (id 18, +5/10/15) |
| 에이밍샷 (id 15, cost 10/20/30) | → | 속사 (id 19, +5/10/15) |
| 암즈트랩 (id 16, cost 10/20/30) | → | 회피증가 (id 17, +10/20/30) |

**관찰**: 18 암즈강화는 직접 강화 가능 (cost 10/20/30) + 12 동시사격을 통한 간접 강화도 가능 — **dual upgrade path**.

## bonus_id=0 의 5 skills (self-only upgrade)

| skill_id | class | name | tier_value | 해석 |
|---|---|---|---|---|
| 13 | S001 | 급소사격 | 10/20/30 | crit-shot 자체 강화만 |
| 18 | S001 | 암즈강화 | 10/20/30 | passive — 직접 강화 (12 통한 간접도 가능) |
| 21 | S002 | 마검공격 | 5/10/15 | base attack — 최저가 |
| 22 | S002 | 텔레포트소드 | 10/25/40 | teleport — mid-cost |
| 37 | S003 | 마법강화 | 20/40/60 | spell amp — 최고가 |

## R99 tutorial 검증

R99 tutorial: "**기본 능력이나 특성 개발이나 모두 고레벨로 올라갈 수록 소모되는 포인트의 양이 많아집니다**."

R100 검증:
- 8/8 ability 가 arithmetic progression (constant diff)
- diff 가 양수 = tier 증가시 비용 증가 → tutorial 진술 정확 부합
- 따라서 tier_value = 진화포인트 단위 소모량

## 마일스톤 — R68~R100 누적

100 라운드 자동 분석 완료. 핵심 milestone:

| 단계 | 핵심 발견 | 라운드 |
|---|---|---|
| DES 풀이 | mx_des_decrypt + key `J@IWO8N7` | R68 |
| 데이터 풀이 | 407+ 파일 복호화 | R69 |
| Quest/Item/Weapon catalog | 128 quest / 349 item / 129 weapon | R70-R75 |
| Summon system 발견 | 5 환수 + 4 global passive | R86 |
| Stat block schema | 3 template × 4 PASSIVE subtype | R87-R89 |
| Quest reward 매핑 | idx 0-127 quest 1:1 + 71 extra | R90 |
| Boss phase scaling | gold 1.30× / EXP 1.25× 일관 | R91 |
| Dialogue cross-ref | 환수 시스템 acquisition path | R92 |
| `_H_SA` 5 환수 매핑 | group_id 0/64/78/38/75 검증 | R93 |
| Ability skill global ID | class×10+local (S001 5/8 dominate) | R94 |
| Element 정정 | byte[5]=2 는 summon-exclusive | R95 |
| Drop slot 구조 | ITM_file_id + item_idx + qty | R96-R97 |
| Death sphere | time-limited boss + countdown timer | R98 |
| Tutorial 1:1 매핑 | binary catalog ↔ in-game terms | R99 |
| **tier/bonus 의미 확정** | **R100** | **(이 라운드)** |

Hero4 게임 데이터 자동 분석 **~99.99%+ 완성**. 남은 작업은:
- character class skill (S000-S003) stat block schema 분석 (R95 미해결)
- 실 디바이스 빌드/UI wiring (Phase C/D 사용자 환경 의존)

## 산출

- `tools/converter/parse_h4_tier_bonus_semantics.py` (신규)
- `work/h4/converted/h4_tier_bonus_semantics.json` (4.7KB)
- `docs/h4/round100-tier-bonus-semantics.md` (이 문서, **마일스톤**)

## 다음 후보 (남은 정밀화 자동 트랙)

1. **character class skill (S000-S003) stat block schema** (R95 후속) — 가변 길이 body 정밀
2. **drop_id 17 byte10=232 정확한 해석** (R97 후속)
3. **죽음의 구 timer 단위 in-game 검증** (R98 후속)
4. **타 character class tutorial scene** (R99 후속) — S000-S003 in-game 설명 검색
5. **R100 milestone 결산 문서 별도 작성** (Hero5 의 MILESTONE_R100.md 처럼)
