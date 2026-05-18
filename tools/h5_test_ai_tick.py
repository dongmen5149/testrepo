"""Round 62 — demo.gd 의 monster spawn + AI tick 루프 정합성 검증.

검증 항목:
1. demo.gd 가 _monsters 배열 + _physics_process 가 AI_TICK_PERIOD 마다 process 호출.
2. spawn_monster 가 monster_id meta 를 저장 (dead 시 Mission.bump_progress 트리거).
3. 30 fps tick 가정 (AI_TICK_PERIOD = 1/30 — Monster::Ai_Process 가 frame-driven).
4. Python 시뮬: 매 tick 마다 dead 인 monster 가 list 에서 제거되며 mission progress 가 누적.
5. cooldown_tick 이 매 tick 마다 호출되어 cooldown 감소.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEMO_GD = Path("apps/hero5-godot/scripts/ui/demo.gd")


def main() -> None:
    print("# Round 62 demo.gd monster spawner + AI tick 루프 검증\n")
    if not DEMO_GD.exists():
        print(f"[skip] {DEMO_GD} 미발견"); return
    text = DEMO_GD.read_text(encoding="utf-8")

    # 1. 핵심 구조 존재 확인
    checks = [
        (r"var\s+_monsters\s*:\s*Array", "_monsters 배열"),
        (r"const\s+AI_TICK_PERIOD", "AI_TICK_PERIOD 상수"),
        (r"func\s+_physics_process", "_physics_process"),
        (r"MonsterAI\.process\(", "MonsterAI.process 호출"),
        (r"\.cooldown_tick\(", "cooldown_tick 호출"),
        (r"Mission\.bump_progress\(Mission\.EVENT_MONSTER_KILL", "Mission monster_kill 트리거"),
        (r'set_meta\("monster_id"', "monster_id meta 저장"),
        (r'set_meta\("ai_runtime"', "ai_runtime meta 저장"),
        (r"KEY_G", "G 키 바인딩 (테스트 spawn)"),
        (r"_monsters\.append\(c\)", "spawn 시 list 등록"),
        (r"_monsters\.erase\(c\)", "dead 시 list 제거"),
    ]
    failed = 0
    for pat, desc in checks:
        if re.search(pat, text):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc}  — pattern {pat!r} not found")
            failed += 1
    assert failed == 0, f"{failed} 구조 누락"

    # 2. AI_TICK_PERIOD 값 확인 (30 fps = 1/30 s)
    m = re.search(r"AI_TICK_PERIOD\s*:=\s*([\d.\s/]+?)(?:\s*$|\s*#|\n)", text, re.MULTILINE)
    assert m, "AI_TICK_PERIOD 값 추출 실패"
    val_expr = m.group(1).strip()
    expected = 1.0 / 30.0
    val = eval(val_expr)  # noqa: S307
    print(f"\n  AI_TICK_PERIOD = {val_expr} ≈ {val:.5f}s ({1/val:.0f} fps)")
    assert abs(val - expected) < 1e-6, f"AI_TICK_PERIOD {val} ≠ 1/30 ({expected})"

    # 3. Python 시뮬 — tick loop semantics
    print("\n# Python 시뮬: tick 루프 dead 정리 + mission progress")

    class MockMonster:
        def __init__(self, mid, hp=10):
            self.monster_id = mid
            self.hp, self.dead = hp, False
            self.cooldowns: dict[int, int] = {1: 30}   # skill 1 cd 30 frames
            self.runtime_ticks = 0
        def cooldown_tick(self):
            for k in list(self.cooldowns.keys()):
                self.cooldowns[k] = max(0, self.cooldowns[k] - 1)
        def take_damage(self, d):
            if self.dead: return
            self.hp -= d
            if self.hp <= 0: self.dead = True

    class MissionTracker:
        def __init__(self): self.kills = {}
        def bump(self, mid): self.kills[mid] = self.kills.get(mid, 0) + 1

    monsters: list[MockMonster] = []
    mission = MissionTracker()
    AI_TICK = 1/30.0

    def physics_process(delta, tick_accum):
        tick_accum += delta
        if tick_accum < AI_TICK: return tick_accum
        tick_accum = 0.0
        if not monsters: return tick_accum
        to_remove = []
        for c in monsters:
            if c.dead:
                to_remove.append(c)
                mission.bump(c.monster_id)
                continue
            c.runtime_ticks += 1   # process() 대용
            c.cooldown_tick()
        for c in to_remove:
            monsters.remove(c)
        return tick_accum

    # spawn 3 monsters
    for mid in [10, 20, 30]:
        monsters.append(MockMonster(mid))
    print(f"  spawn: {len(monsters)} monsters")

    # 30 frame (= 1초) tick — cooldown 30→0
    accum = 0.0
    for frame in range(30):
        accum = physics_process(1/60.0, accum)
    # 30 frame * (1/60) = 0.5s — AI_TICK_PERIOD 1/30 마다 fire → 15회 tick
    assert all(m.runtime_ticks >= 14 for m in monsters), \
        f"30 frame 후 tick 부족: {[m.runtime_ticks for m in monsters]}"
    print(f"  30 frame (0.5s) 후 monster tick count: {[m.runtime_ticks for m in monsters]} (≥14 기대)")

    # 한 monster damage 후 죽음
    monsters[0].take_damage(10)
    assert monsters[0].dead
    # 한 번 더 tick → dead monster list 에서 제거 + mission progress
    accum = physics_process(1.0, accum)   # 큰 delta 로 즉시 fire
    assert len(monsters) == 2, f"dead 제거 안 됨: {len(monsters)}"
    assert mission.kills.get(10) == 1, "mission 트리거 안 됨"
    print(f"  monster #10 사망 후: 남은 {len(monsters)}, mission kills={mission.kills}")

    # cooldown_tick — 누적 frame 만큼 감소 (16 tick 가량이면 cd 30→14 정도)
    final_cd = monsters[0].cooldowns.get(1, 0)
    assert final_cd < 30, f"cooldown 안 떨어짐: {final_cd}"
    print(f"  cooldown 30 → {final_cd} (tick {monsters[0].runtime_ticks}회) ✓")

    # 30 회 이상 tick → cooldown 0 도달
    for _ in range(30):
        accum = physics_process(1.0, accum)
    final_cd2 = monsters[0].cooldowns.get(1, 0)
    assert final_cd2 == 0, f"30회 tick 후에도 cooldown {final_cd2}"
    print(f"  추가 30 tick 후 cooldown = 0 ✓")

    print("\n# All Round 62 AI tick checks passed.")


if __name__ == "__main__":
    main()
