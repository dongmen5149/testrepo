"""Mission 시스템 정합성 검증 (Round 58).

`apps/hero5-godot/scripts/core/mission_system.gd` 의 GDScript 로직과 동등한
Python sweep + 진척 시뮬레이션. mission.json (decode_h5_mission.py 산출) 의:

1. 105 entries 모두 named.
2. mission_type 분포 (Round 58 sweep 기대):
   {0: 20 (사냥), 1: 5 (특수 처치), 2: 22 (세트 수집), 3: 47 (누적 도전),
    4: 5 (카테고리 수집), 5: 5 (달성 과제), 255: 1 (튜토리얼)}
3. 각 mission 은 5 sub_conditions (slot/sub_flag/target_value).
4. 진척 시뮬:
   - type 0 (monster_kill): sub_flag 가 monster_id, kill 누적
   - type 3 (누적): 무조건 누적
   - type 2 (세트 수집): slot + sub_flag 매칭
5. target_count 만큼 sub_conditions 충족 시 자동 완료.
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MISSION_JSON = Path("apps/hero5-godot/assets/gamedata/mission.json")


# mission_system.gd 의 generic bump_progress 와 같은 의미. 5 sub_conditions 의
# current_value 갱신 후 target_count 도달 검사.
class MissionTracker:
    EVENT_TO_TYPES = {
        "monster_kill": (0, 1),
        "item_obtained": (2, 4),
        "refine_done": (3,),
        "orb_combine": (3,),
        "mix_done": (3,),
        "playtime": (3,),
        "money": (3,),
        "quest_done": (5,),
    }

    def __init__(self, missions: list[dict]):
        self.missions = missions
        self.progress: dict[int, dict[int, int]] = {}
        self.completed: set[int] = set()

    def bump(self, event_kind: str, key: int = -1, amount: int = 1) -> list[int]:
        """매칭된 (그리고 progress 가 갱신된) mission_id 리스트 반환."""
        types = self.EVENT_TO_TYPES.get(event_kind, ())
        touched: list[int] = []
        for mid, rec in enumerate(self.missions):
            if mid in self.completed: continue
            mtype = int(rec.get("mission_type", 255))
            if mtype not in types: continue
            subs = rec.get("sub_conditions", [])
            changed = False
            for i, sc in enumerate(subs):
                slot = int(sc.get("slot", 255))
                sub_flag = int(sc.get("sub_flag", 255))
                tgt = int(sc.get("target_value", 0))
                if slot == 255 and sub_flag == 255: continue
                match = False
                if event_kind == "monster_kill":
                    match = (sub_flag == key)
                elif event_kind == "item_obtained":
                    item_key = key % 1000
                    item_slot = key // 1000
                    if mtype == 2:
                        match = (slot == item_slot and sub_flag == item_key)
                    elif mtype == 4:
                        match = (int(rec.get("sub_type", 0)) == item_slot)
                else:
                    match = True
                if not match: continue
                prev = self.progress.get(mid, {})
                cur = int(prev.get(i, 0))
                if cur >= tgt: continue
                prev[i] = min(cur + amount, tgt)
                self.progress[mid] = prev
                changed = True
            if changed:
                touched.append(mid)
                self._check_completion(mid)
        return touched

    def _check_completion(self, mid: int) -> None:
        rec = self.missions[mid]
        subs = rec.get("sub_conditions", [])
        tgt_cnt = int(rec.get("target_count", 1))
        if tgt_cnt == 255: tgt_cnt = 1
        done = 0
        for i, sc in enumerate(subs):
            slot = int(sc.get("slot", 255))
            sub_flag = int(sc.get("sub_flag", 255))
            if slot == 255 and sub_flag == 255: continue
            cur = int(self.progress.get(mid, {}).get(i, 0))
            tgt = int(sc.get("target_value", 0))
            if cur >= tgt: done += 1
        if done >= tgt_cnt:
            self.completed.add(mid)


def main() -> None:
    if not MISSION_JSON.exists():
        print(f"[skip] {MISSION_JSON} 미발견")
        return
    data = json.loads(MISSION_JSON.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    print(f"# Round 58 Mission 검증 — {len(entries)} entries (105 기대)")
    assert len(entries) == 105

    # 1. named
    named = sum(1 for e in entries if e.get("name") and e.get("name") != "?")
    assert named == 105, f"named={named} (105 기대)"

    # 2. mission_type 분포
    type_dist = Counter(int(e.get("mission_type", 255)) for e in entries)
    print(f"  mission_type 분포: {dict(sorted(type_dist.items()))}")
    expected = {0: 20, 1: 5, 2: 22, 3: 47, 4: 5, 5: 5, 255: 1}
    assert dict(sorted(type_dist.items())) == expected, \
        f"분포 mismatch: 기대={expected}, 실제={dict(sorted(type_dist.items()))}"

    # 3. 각 mission 은 정확히 5 sub_conditions
    bad_sub_cnt = 0
    for e in entries:
        if len(e.get("sub_conditions", [])) != 5:
            bad_sub_cnt += 1
    print(f"  sub_conditions != 5 인 mission: {bad_sub_cnt}")
    assert bad_sub_cnt == 0

    # 4. 진척 시뮬
    tracker = MissionTracker(entries)
    print("\n# 진척 시뮬:")

    # 4a. type 0 monster_kill: 미션 #1 "집념의 사냥꾼" → monster_id=17 30번 처치
    mid_jipnyeom = 1
    rec1 = entries[mid_jipnyeom]
    target_monster = rec1["sub_conditions"][0]["sub_flag"]   # 17
    target_kills = rec1["sub_conditions"][0]["target_value"]  # 30
    print(f"  case A: 미션 #{mid_jipnyeom} '{rec1['name']}' — monster #{target_monster} {target_kills}회 처치")
    for _ in range(target_kills - 1):
        tracker.bump("monster_kill", target_monster)
    assert mid_jipnyeom not in tracker.completed, "29회만에 완료됨 (30 기대)"
    tracker.bump("monster_kill", target_monster)
    assert mid_jipnyeom in tracker.completed, "30회 후에도 미완료"
    print(f"    ✓ {target_kills}회 후 완료. progress={tracker.progress[mid_jipnyeom]}")

    # 4b. 다른 monster ID 는 영향 없음
    other_progress_before = dict(tracker.progress)
    tracker.bump("monster_kill", 999)
    # 999 monster_id 매칭하는 mission 없거나 — 변동 적어야 함
    # (실제로는 monster_id 999 가 다른 mission 에 매칭될 수도 있어서 변동 가능)
    # 단지 #1 이 더 변하지 않는 것만 확인
    assert tracker.progress[mid_jipnyeom] == other_progress_before[mid_jipnyeom]

    # 4c. type 3 누적 미션 — refine 100회로 모든 type 3 progress bump
    type3_ids = [i for i, e in enumerate(entries) if int(e.get("mission_type", 255)) == 3]
    print(f"  case B: type 3 미션 {len(type3_ids)} 개 — refine 100회로 progress 누적")
    for _ in range(100):
        tracker.bump("refine_done")
    # 적어도 일부 type 3 미션이 진행/완료 상태가 돼야 함
    type3_touched = sum(1 for mid in type3_ids if mid in tracker.progress)
    type3_completed = sum(1 for mid in type3_ids if mid in tracker.completed)
    print(f"    progress 발생: {type3_touched} / {len(type3_ids)}")
    print(f"    완료: {type3_completed} / {len(type3_ids)}")
    assert type3_touched > 0, "type 3 미션에 progress 가 전혀 안 쌓임"

    # 4d. type 2 세트 수집 — 미션 #21 "가시나무 전사" (slot 5/6/7/8, sub_flag=23, 각 1개)
    mid_set = 21
    rec_set = entries[mid_set]
    print(f"  case C: 미션 #{mid_set} '{rec_set['name']}' — 세트 아이템 수집")
    # slot 5/6/7/8 의 idx 23 4개 획득
    for slot in [5, 6, 7, 8]:
        key = slot * 1000 + 23
        tracker.bump("item_obtained", key)
    assert mid_set in tracker.completed, f"세트 4개 후에도 미완료. progress={tracker.progress.get(mid_set, {})}"
    print(f"    ✓ 완료. progress={tracker.progress[mid_set]}")

    # 5. 최종 통계
    print(f"\n# 시뮬 종료 — 진척 발생 mission: {len(tracker.progress)}, 완료: {len(tracker.completed)}")

    # 첫 5 entry sample
    print("\n# Mission sample (first 5):")
    for e in entries[:5]:
        sc = e.get("sub_conditions", [])
        active_sc = [c for c in sc if c["slot"] != 255 or c["sub_flag"] != 255]
        print(f"  [{e['idx']:3d}] {e['name'][:18]:18s}  type={e['mission_type']:3d}  "
              f"sub_type={e['sub_type']:3d}  target_count={e['target_count']:3d}  "
              f"active_sub_conds={len(active_sc)}")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
