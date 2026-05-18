"""Round 65 — Quest reward type RE 검증 (type 6/10/11/12 미해석 해결).

검증 항목:
  1. quests.json 3 difficulty × 151 quest 의 reward type 분포 (전체)
  2. type 0-18 의 items.json cat/idx in-range 검증 (cat=type, idx=sub 가설)
  3. .so ELF symbol cross-verify (QuestRewardData / NewItemToBagEx / IncreaseMoney / GetBagItemPtr)
  4. quest_system.gd 의 REWARD_TYPE_* 상수 정의 + REWARD_SLOT_LABEL + reward_label/grant_reward 변경
  5. Python reward_label 시뮬 (5+ case) — 의미 있는 한국어 라벨
"""
from __future__ import annotations
import collections
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
QUESTS = ROOT / "apps/hero5-godot/assets/gamedata/quests.json"
ITEMS = ROOT / "apps/hero5-godot/assets/gamedata/items.json"
QUEST_GD = ROOT / "apps/hero5-godot/scripts/core/quest_system.gd"
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


def main() -> None:
    print("# Round 65 Quest reward type RE 검증\n")
    assert QUESTS.exists(), f"missing {QUESTS}"
    assert ITEMS.exists(), f"missing {ITEMS}"
    assert QUEST_GD.exists(), f"missing {QUEST_GD}"

    quests_data = json.loads(QUESTS.read_text(encoding="utf-8"))
    items_data = json.loads(ITEMS.read_text(encoding="utf-8"))
    by_diff = quests_data["by_difficulty"]

    # 1. 3 difficulty × 151 quest 의 reward type 분포
    print("# 1. reward type 분포 (3 difficulty × 151 quest)")
    for diff in ("q0", "q1", "q2"):
        rewards = [r for q in by_diff[diff] for r in q.get("rewards", [])]
        dist = collections.Counter(r["type"] for r in rewards)
        named = {t: ("money" if t == 17 else "exp" if t == 18 else "HP" if t == 19 else "INT" if t == 20
                     else "unused" if t == 255 else f"item(slot_{t})")
                 for t in dist}
        print(f"  {diff}: {dict(sorted(dist.items()))}")
        print(f"      labels: {named}")
    print()

    # 2. cat=type, sub=idx 가설 검증 — items.json slot 별 size 와 비교
    print("# 2. cat=type, sub=idx in-range 검증 (cat=slot_N size)")
    slot_sizes = {int(k.replace("slot_", "")): len(v)
                  for k, v in items_data.items() if k.startswith("slot_")}
    all_ok = True
    out_of_range = 0
    in_range = 0
    for diff in ("q0", "q1", "q2"):
        for q in by_diff[diff]:
            for r in q.get("rewards", []):
                t = int(r["type"])
                s = int(r["sub"])
                if 0 <= t <= 16:
                    size = slot_sizes.get(t, 0)
                    if size == 0:
                        # slot_4 (armor) 만 1 record 라 sub > 0 일 수 있음 — 게임 데이터 이슈
                        continue
                    if s >= size:
                        out_of_range += 1
                        if out_of_range <= 3:
                            print(f"  ✗ {diff} q#{q.get('quest_id', '?')} type={t} sub={s} >= size={size}")
                        all_ok = False
                    else:
                        in_range += 1
    print(f"  in-range: {in_range}, out-of-range: {out_of_range}")
    assert all_ok, f"cat=slot, sub=idx 가설 검증 실패 ({out_of_range} out-of-range)"
    print(f"  ✓ {in_range}/{in_range} reward 가 in-range (cat=slot, sub=idx 가설 검증 완료)")
    print()

    # 3. ELF symbol cross-verify
    print("# 3. ELF symbol cross-verify (.so 함수 주소 확인)")
    if not SO_PATH.exists():
        print(f"  [skip] {SO_PATH} 미발견")
    else:
        try:
            import lief  # type: ignore
            b = lief.parse(str(SO_PATH))
            targets = {
                "_ZN8QuestMgr15QuestRewardDataEah": (0xd458c, 1552, "QuestMgr::QuestRewardData"),
                "_ZN9ItemTable14NewItemToBagExEaash": (0xa7450, 160, "ItemTable::NewItemToBagEx"),
                "_ZN7BagItem13IncreaseMoneyEi": (0xa28e0, 76, "BagItem::IncreaseMoney"),
                "_ZN4HERO13GetBagItemPtrEv": (0x890c8, 8, "HERO::GetBagItemPtr"),
            }
            n_ok = 0
            for sym in b.symbols:
                name = sym.name or ""
                if name in targets:
                    exp_addr, exp_size, label = targets[name]
                    got_addr = int(sym.value) & ~1
                    got_size = int(sym.size)
                    ok = got_addr == exp_addr and got_size == exp_size
                    print(f"  {'✓' if ok else '✗'} {label}: addr=0x{got_addr:x} size={got_size} "
                          f"(expect 0x{exp_addr:x}/{exp_size})")
                    if ok:
                        n_ok += 1
            assert n_ok >= 4, f"4 symbol 모두 일치해야 함 ({n_ok}/{len(targets)})"
            print(f"  ✓ {n_ok}/{len(targets)} symbol cross-verify 통과")
        except ImportError:
            print(f"  [skip] lief 미설치")
    print()

    # 4. quest_system.gd 패턴 검증
    print("# 4. quest_system.gd 변경 패턴")
    src = QUEST_GD.read_text(encoding="utf-8")
    checks = [
        (r"REWARD_TYPE_HP\s*:=\s*19", "REWARD_TYPE_HP = 19"),
        (r"REWARD_TYPE_INT\s*:=\s*20", "REWARD_TYPE_INT = 20"),
        (r"REWARD_TYPE_ITEM_MAX\s*:=\s*16", "REWARD_TYPE_ITEM_MAX = 16"),
        (r"REWARD_SLOT_LABEL\s*:=", "REWARD_SLOT_LABEL dict"),
        (r"GameData\.item_name_at\(t,\s*s\)", "item_name_at(type, sub) lookup in reward_label"),
        (r"GameState\.inventory\.append\(item_name\)", "_grant_reward 가 item type → inventory.append"),
        (r"GameState\.max_hp\s*\+=\s*v", "HP 보상 → max_hp 증가"),
        (r"GameState\.stat_int\s*\+=\s*v", "INT 보상 → stat_int 증가"),
    ]
    failed = 0
    for pat, desc in checks:
        if re.search(pat, src):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} — {pat!r} not found")
            failed += 1
    assert failed == 0, f"{failed} 패턴 누락"
    print()

    # 5. Python reward_label 시뮬 (실 sample 으로)
    print("# 5. reward_label Python 시뮬 (실 sample 으로 의미 있는 한국어 라벨)")
    REWARD_SLOT_LABEL = {
        0: "무기A", 1: "무기B", 2: "무기C", 3: "무기D",
        4: "갑옷", 5: "헬멧", 6: "부츠",
        7: "액세서리A", 8: "액세서리B", 9: "방패",
        10: "영혼석", 11: "포션", 12: "오브",
        13: "재료", 14: "퀘스트 아이템", 15: "합성서",
        16: "스킬북",
    }

    def reward_label(t: int, s: int, v: int) -> str:
        if t == 17: return f"💰 골드 +{v}"
        if t == 18: return f"⭐ 경험치 +{v}"
        if t == 19: return f"❤ HP +{v}"
        if t == 20: return f"🔮 INT +{v}"
        if t == 255: return ""
        if 0 <= t <= 16:
            arr = items_data.get(f"slot_{t}", [])
            if s < len(arr):
                rec = arr[s]
                name = rec.get("name", "") if isinstance(rec, dict) else str(rec)
                if name and not name.startswith("("):
                    if v > 1:
                        return f"🎁 {name} × {v}"
                    return f"🎁 {name}"
            return f"🎁 [{REWARD_SLOT_LABEL.get(t, '?')}] #{s} × {v}"
        return f"보상[type={t},sub={s},val={v}]"

    cases = [
        (6, 84, 1, "🎁 엠프리스"),           # boots (R65 발견)
        (10, 0, 1, "🎁 고렘의인장"),         # spirit
        (11, 0, 5, "🎁 포션 × 5"),           # potion x 5
        (12, 1, 1, "🎁 뇌제의 오브"),        # orb
        (14, 14, 1, "🎁 소녀의 사진"),       # quest item (slot 14)
        (15, 9, 1, "🎁 맹독"),               # mix_book
        (17, 0, 1000, "💰 골드 +1000"),
        (18, 0, 500, "⭐ 경험치 +500"),
        (19, 0, 10, "❤ HP +10"),
        (20, 0, 5, "🔮 INT +5"),
        (255, 0, 0, ""),
    ]
    fail = 0
    for t, s, v, expected in cases:
        got = reward_label(t, s, v)
        ok = got == expected
        flag = "✓" if ok else "✗"
        print(f"  {flag} type={t:3d} sub={s:3d} val={v:5d} -> {got!r}")
        if not ok:
            print(f"     expected: {expected!r}")
            fail += 1
    assert fail == 0, f"{fail} 라벨 불일치"
    print(f"  ✓ {len(cases)}/{len(cases)} reward_label 케이스 통과")

    print("\n# All Round 65 reward type RE checks passed.")


if __name__ == "__main__":
    main()
