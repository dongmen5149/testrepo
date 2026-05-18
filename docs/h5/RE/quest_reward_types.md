# Quest Reward Type — RE 결과 (Round 65)

> Round 56 sweep 미해석 reward type 6/10/11/12 의 의미 확정.
> R60 의 type 15 = "item" 가설을 일반화 → **type 0-16 모두 item 보상**.

## 1. 핵심 발견

**reward.type = item category (= items.json 의 slot 번호)**
**reward.sub  = idx within that slot**
**reward.value = quantity**

R60 에서 type 15 만 item 이라고 봤던 것은 부분 표본이었고, .so 분석 결과 reward type 0-16 전체가
같은 dispatch (`ItemTable::NewItemToBagEx`) 로 처리됨.

## 2. .so 디스어셈블 근거

대상: `QuestMgr::QuestRewardData` @ `0xd458c` (1552B, ARM mode).

### dispatch 코드 (0xd470c..0xd476c)

```arm
000d46f8: ldrb     r1, [r4, #0x26c]   ; r1 = reward.type (signed byte)
000d4700: asr      r1, r1, #0x18
000d4704: cmn      r1, #1             ; -1 sentinel?
000d4708: beq      0xd4724            ; skip
000d470c: cmp      r1, #0x10          ; type ≤ 16?
000d4710: bgt      0xd4748            ; type > 16 → high-type handler
000d4714: ldr      r0, [r7, #0x274]   ; r0 = reward.value
000d4718: cmp      r0, #0
000d471c: bgt      0xd4770            ; value > 0 → item add
000d4720: bne      0xd49f4            ; value < 0 → item remove (음수)

;; type > 16 handler:
000d4748: cmp      r1, #0x16
000d474c: beq      0xd4864            ; type 22 = special item add (cat=17?)
000d4750: sub      r1, r1, #0x11      ; r1 = type - 17
000d4754: cmp      r1, #3
000d4758: addls    pc, pc, r1, lsl #2 ; jumptable case 0..3
000d475c: b        0xd4724            ; fallthrough (type > 20)
000d4760: b        0xd4948            ; type 17 → money
000d4764: b        0xd4984            ; type 18 → exp
000d4768: b        0xd48c4            ; type 19 → HP boost
000d476c: b        0xd4908            ; type 20 → INT boost (sb=0x246)
```

### type ≤ 16 의 단일 handler (0xd4770)

```arm
000d4770: ldr      lr, [sp, #0x24]
000d4774: ldrb     r2, [r4, #0x26f]   ; r2 = reward.sub
000d4778: lsl      r3, r0, #0x10       ; r3 = value (sign extended)
000d4790: mov      ip, #1
000d4794: str      ip, [sp]            ; 4th arg = 1 (flag)
000d4798: bl       0xa7450             ; ItemTable::NewItemToBagEx
```

심볼:
- `0xa7450 = _ZN9ItemTable14NewItemToBagExEaash`
  = `ItemTable::NewItemToBagEx(char cat, char idx, short qty, signed short flag)`

즉 type 0-16 모든 reward 가 `NewItemToBagEx(cat=type, idx=sub, qty=value, flag=1)` 로 처리됨.
**type 자체가 cat 으로 직접 전달** — slot 번호와 일치.

### type 17/18/19/20 handler

| 주소 | type | 함수/연산 | 의미 |
|---|---:|---|---|
| 0xd4948 | 17 | `BagItem::IncreaseMoney(value)` @ `0xa28e0` | money +value |
| 0xd4984 | 18 | `*(HERO+0x230) += value` | EXP +value |
| 0xd48c4 | 19 | `*(HERO+0x234) += value` (u16) | HP/stat[0] +value |
| 0xd4908 | 20 | `*(HERO+0x246) += value` (u16) | INT/stat[5] +value |

심볼:
- `0x890c8 = HERO::GetBagItemPtr()` (instance accessor)
- `0xa28e0 = BagItem::IncreaseMoney(int)`

HERO struct offset 매핑 (Round 43 의 LoadHeroData 분석과 일치):
- `+0x230` = u32 EXP/gold area
- `+0x234` = u16 stat[0] = HP (R41 의 +0xa..+0x19 = HP/MP/STR/DEX/CON/INT)
- `+0x23e..+0x24a` = u16 stat[1..7] (10 byte gap 사이 derived stat 5개)
- `+0x246` = u16 stat[5] = INT

## 3. items.json 매핑 검증

| reward.type | slot kind | size | 의미 |
|---:|---|---:|---|
| 0-3 | weapon / weapon_2/3/4 | 86×4 | 무기 변형 4종 |
| 4 | armor | 1 | armor (Sorcerer stub) |
| 5 | helmet | 90 | 헬멧 |
| 6 | boots | 93 | 부츠 |
| 7-8 | accessory / accessory_2 | 81×2 | 액세서리 |
| 9 | shield | 81 | 방패 |
| 10 | spirit | 18 | 영혼석 |
| 11 | potion (BattleUseItem) | 16 | 포션/소비 |
| 12 | orb | 53 | 오브 |
| 13 | material | 86 | 합성 재료 |
| 14 | material_2 | 58 | **quest 전용 아이템** (예: "소녀의 사진") |
| 15 | recipe (mix_book) | 116 | 합성 레시피 |
| 16 | skill_book_wr | 95 | 스킬북 (Warrior/Rogue) |

## 4. Round 56 sweep 의 4 type 의미 확정

| type | sub | value | 의미 | 샘플 quest |
|---:|---:|---:|---|---|
| 6 | 84/88/92 | 1 | boots (부츠) — difficulty 별 grade ↑ | q#114 "불완전한 기록" → 엠프리스/실버 채리옷/더 월드 |
| 10 | 0/5/5 | 1 | spirit (영혼석) | q#125 "백곰" → 고렘의인장/독사의이빨 |
| 11 | 0/4/7/10 | 5/10/15 | potion (포션) — quantity | q#100 "분실물", q#102 "신장개업", q#142 "집게발" |
| 12 | 1 | 1 | orb (오브) | q#101 "조합개시" → 뇌제의 오브 |

## 5. 표시 라벨 (UI 정정)

기존 `quest_system.gd::reward_label` 의 `type_6/10/11/12` placeholder 를 정확한 이름으로 매핑:

```gdscript
# slot 번호 (kind) → items.json lookup
const REWARD_TYPE_LABEL := {
    0: "무기 A", 1: "무기 B", 2: "무기 C", 3: "무기 D",
    4: "갑옷",
    5: "헬멧",
    6: "부츠",       # ★ R65 확정
    7: "액세서리 A", 8: "액세서리 B",
    9: "방패",
    10: "영혼석",     # ★ R65 확정
    11: "포션",       # ★ R65 확정
    12: "오브",       # ★ R65 확정
    13: "재료",
    14: "퀘스트 아이템",
    15: "합성서",
    16: "스킬북",
    17: "골드",
    18: "경험치",
    19: "HP +",
    20: "INT +",
    255: "(미사용)",
}
```

label 함수:
```gdscript
func reward_label(rtype: int, sub: int, value: int) -> String:
    if rtype == 17: return "골드 +%d" % value
    if rtype == 18: return "경험치 +%d" % value
    if rtype == 19: return "HP +%d" % value
    if rtype == 20: return "INT +%d" % value
    if rtype == 255: return ""
    # 0-16: items.json lookup
    var slot_name = REWARD_TYPE_LABEL.get(rtype, "(?)")
    var item_name = GameData.item_name_at(rtype, sub)
    if value > 1:
        return "%s × %d" % [item_name if item_name else slot_name, value]
    return item_name if item_name else slot_name
```

## 6. 부수 효과

- R60 의 type 15 = "item" 가설은 정확하지만 좁은 표본이었음 — 사실 type 0-16 전체가 item.
- reward_type_table (quests.json) 의 `17: money / 18: exp / 255: unused` 만 유지 — 나머지 type 은 slot 번호.
- type 22 (0x16) 는 special path (`r1=#0x11`) — observation 없음, 코드만 식별.
- type 19/20 도 observation 없음 (quest data 에 없음) — disasm only.
- value < 0 (negative reward) path 도 존재 (0xd49f4 → 0xa1dd0) — item 회수 메커니즘 추정.

## 7. 검증 도구

`tools/h5_test_reward_types.py` — Python sweep:
- quests.json 3 difficulty × 151 quest 의 reward type 분포 추출
- type 0-18 sample 별 items.json cat/idx range 검증 (in-range 100%)
- ELF symbol cross-verify (`QuestRewardData`, `NewItemToBagEx`, `IncreaseMoney`, `GetBagItemPtr`)
- reward_label 함수 5+ case
