# Hero4 Round 84 — `_ITM_OPTION` enchantment pool 51종 추출

> R83 의 부수 발견을 본격 정리. ARPG 옵션/접두/마법속성 시스템 전체.

## TL;DR

`_ITM_OPTION` 1928B = **120 text entries / 51 unique enchantment types / L1-L4 진행**.

레벨 분포: L1=28, L2=27, L3=19, L4=30 (총 104 + 16 무레벨 = 120).

## 51 enchantment 분류

### 기본 stat (HP/SP 계열, +/기본)
- HPmax, HPmax +, HP회복, HP회복 +, HP흡수, HP흡수 +
- SPmax (Spmax는 typo 변종), SP회복, SP분노, SP소모, SP소모 +
- 물약회복

### 공격
- 근접공격, 원거리공격, 마법공격, 특수공격
- 무기공격력 +
- 크리티컬, 크리티컬 +, 크리데미지
- 직격

### 방어
- 물리방어, 물리방어력 +
- 마법방어, 마법방어력 +
- 명중, 명중 +
- 회피, 회피 +
- 블록
- 저항, 저항 +
- 데미지반사

### Proc / 발동 (공격 시 부가효과)
- 화염발동, 결빙(냉기)
- 스턴발동 L1, L2, L4 (separate entries, L3 누락)
- 슬로우발동, 넉백발동
- 중독, 저주

### 상태이상 저항
- 기절저항, 기절저항 +

### 시스템
- 쿨타임, 쿨타임감소
- 레벨제한감소W

### 클래스 보완 (캐릭터 mode 한정)
- 양손검 보완 (티르 mode 0 한정)
- 사격/마법, 사격/마법 보완Z (루레인 mode 0 한정)

## R81 캐릭터 mode 와의 연계

R81 의 "2 영웅 × 2 mode" 구조와 직접 매칭:
- **티르 mode 0** (S000 양손검) ← `양손검 보완` enchant
- **루레인 mode 0** (S001 사격) ← `사격/마법 보완Z`
- 양 mode 모두 `사격/마법` enchant 호환 (보편 옵션)

→ enchantment 시스템에 **mode-locked affix** 존재 확정. R81 의 다중 mode 가설 강화.

## 다음 후보

1. ⭐ enchantment idx ↔ REPAY item_idx (R83 의 0x09, 0x0a, 0x24..0x26) 정확 매핑
2. 스턴발동 L3 누락 원인 — 데이터 오류 / 의도적 / 미발견 entry
3. 보스 phase stat 강화율 정량 (R80 후속, 미완 트랙)

## 산출

- `tools/analysis/parse_h4_itm_option.py`
- `work/h4/converted/h4_itm_option_pool.json`
- `docs/h4/round84-enchantment-pool.md` (이 문서)
