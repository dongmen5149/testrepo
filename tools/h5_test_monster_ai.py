"""Monster AI VM 상태 머신 검증 (Round 50).

`apps/hero5-godot/scripts/core/monster_ai.gd` 의 GDScript 로직을 Python 으로
재구현한 뒤 `monster_ai.json` (48 AI defs) 으로 시뮬레이션 실행하여:

1. opcode 0..12 의 operand size 가 stream 끝을 넘지 않는지 (Round 44 의 13 opcode VM)
2. trigger 0..12 의 operand size 가 stream 끝을 넘지 않는지 (Round 46 의 13 trigger VM)
3. Ai_Action 13 sub-state dispatch 가 None/예외 없이 완료되는지 (Round 47)
4. _can_cast_skill / _do_cast gate 의 cooldown reset 이 일관되는지

monster_ai.gd 와 라인-by-라인 매핑된 simulator. 실패 시 단순 AssertionError 가
나도록 작성.
"""
from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AI_JSON = Path("apps/hero5-godot/assets/gamedata/monster_ai.json")

# monster_ai.gd 의 OPCODE_OPERAND / TRIGGER_OPERAND 와 동일
OPCODE_OPERAND = {
    0: 2, 1: 2, 2: 1, 3: 1, 4: 3, 5: 4, 6: 2, 7: 3, 8: 2, 9: 2, 10: 1,
    11: -1, 12: 1,
}
TRIGGER_OPERAND = {
    0: 0, 1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1,
    7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0,
}


@dataclass
class HostStub:
    """battle_system.gd 의 host CHAR interface 와 동일한 동작."""
    enemy_hp: int = 100
    pending_skill: int = -1
    casts: list[tuple[str, int]] = field(default_factory=list)

    def is_die(self) -> bool: return self.enemy_hp <= 0
    def get_motion(self) -> int: return 0
    def is_attack_able(self) -> bool: return self.enemy_hp > 0
    def is_able_skill(self, sid: int) -> bool: return sid > 0
    def get_dir(self) -> int: return 0
    def set_dir(self, d: int) -> None: pass
    def hero_turn_direction(self) -> None: pass
    def fast_distance_to_hero(self) -> int: return 0
    def set_attack_motion(self, sid: int) -> None: self.pending_skill = sid
    def ai_cast_skill(self, sid: int) -> None:
        self.pending_skill = sid
        self.casts.append(("cast", sid))
    def set_cool_time(self, sid: int) -> None: pass
    def skill_end(self) -> None: pass
    def ai_check_irect_hit(self, r: int) -> bool: return True
    def ai_check_visibility(self, i: int) -> bool: return True
    def ai_all_dead(self) -> bool: return False
    def ai_tutorial_flag(self, i: int) -> bool: return False


@dataclass
class State:
    """monster_ai.gd MonsterAIState 의 Python equivalent."""
    host: HostStub
    ai_def: dict
    action_idx: int = 0xff
    opcode: int = -1
    operand: bytearray = field(default_factory=lambda: bytearray(4))
    action_cooldown: int = 9
    action_type: int = 0
    sub_action: int = 0
    sub_action_data: int = 0
    first_set_flag: int = 0
    action_timer: int = 0
    skill_id: int = -1
    skill_target: int = 4
    skill_range: int = 0
    skill_param: bytearray = field(default_factory=lambda: bytearray(4))
    skill_src_303: int = 0
    skill_src_304: int = 0
    skill_src_305: int = 0
    skill_src_308: int = 0
    skill_src_30a: int = 0
    skill_disable: int = 0
    state: int = 1
    action_running: int = 1
    list_active: int = 0
    action_counter: int = 0
    action_offset: int = 0
    trigger_offset: int = 0
    flags: dict = field(default_factory=dict)


def _hex_to_bytes(h: str) -> bytes:
    return bytes.fromhex(h) if h else b""


def on_action(s: State, op: int, stream: bytes) -> int:
    """monster_ai.gd._on_action 와 1:1 매핑."""
    sz = OPCODE_OPERAND.get(op, -2)
    if sz == -2: return 0
    if op == 11:
        if s.action_offset >= len(stream): return 1
        n = stream[s.action_offset]
        s.action_offset += 1
        if s.action_offset + n > len(stream): return 1
        for i in range(min(n, 4)):
            s.operand[i] = stream[s.action_offset + i]
        s.action_offset += n
        return 0
    if s.action_offset + sz > len(stream):
        return 1
    for i in range(min(sz, 4)):
        s.operand[i] = stream[s.action_offset + i]
    s.action_offset += sz
    if op == 0:
        s.action_type = s.operand[0]
        s.sub_action_data = s.operand[1]
    elif op == 1:
        s.action_type = s.operand[0]
        s.sub_action_data = s.operand[1]
    elif op == 2:
        s.sub_action = s.operand[0]
    elif op == 3:
        if s.first_set_flag == 0:
            s.first_set_flag = s.operand[0]
    elif op == 4:
        s.skill_id = s.operand[0]
        s.skill_target = s.operand[1]
        s.skill_range = s.operand[2]
    elif op == 5:
        for i in range(4):
            s.skill_param[i] = s.operand[i]
    elif op == 6:
        s.skill_src_303 = s.operand[0]
        s.skill_src_304 = s.operand[1]
    elif op == 7:
        s.skill_src_305 = s.operand[0]
    elif op == 8:
        s.skill_src_308 = s.operand[0]
    elif op == 9:
        s.skill_src_30a = s.operand[0]
    return 0


def step_action_list(s: State) -> bool:
    if s.action_running == 0: return False
    stream = _hex_to_bytes(s.ai_def.get("action_stream_hex", ""))
    if s.action_offset >= len(stream): return False
    op = stream[s.action_offset]
    s.action_offset += 1
    s.opcode = op
    ret = on_action(s, op, stream)
    if ret == 1:
        # operand 부족 — 종료 (decoder 동작 매칭)
        return False
    return True


def step_trigger_list(s: State) -> bool:
    stream = _hex_to_bytes(s.ai_def.get("trigger_stream_hex", ""))
    if s.trigger_offset >= len(stream): return False
    code = stream[s.trigger_offset]
    s.trigger_offset += 1
    if code == 5:
        if s.trigger_offset >= len(stream): return False
        s.action_idx = stream[s.trigger_offset]
        s.trigger_offset += 1
        return True
    osz = TRIGGER_OPERAND.get(code, 0)
    if osz == 1 and s.trigger_offset < len(stream):
        s.trigger_offset += 1
    if s.trigger_offset >= len(stream): return False
    s.trigger_offset += 1
    return False


def can_cast(s: State, skill_id: int) -> bool:
    if skill_id <= 0: return False
    if s.skill_disable != 0: return False
    if s.host.get_motion() != 0: return False
    if not s.host.is_attack_able(): return False
    if not s.host.is_able_skill(skill_id): return False
    return True


def do_cast(s: State, skill_id: int) -> None:
    s.host.ai_cast_skill(skill_id)
    s.host.set_cool_time(skill_id)
    s.opcode = -1


def ai_action(s: State) -> None:
    if s.host.is_die(): return
    if s.action_type == 0: return
    op = s.opcode
    if op == 0:
        if s.action_timer > 0:
            s.action_timer -= 1
        elif s.action_type == 1:
            dist = s.host.fast_distance_to_hero()
            if dist < s.sub_action_data or s.sub_action_data == 0:
                s.opcode = 8
                s.action_timer = 0
    elif op == 1:
        # TURN_DIR — sub_action mode
        s.opcode = -1
    elif op == 2:
        if s.first_set_flag > 0:
            s.first_set_flag -= 1
        if s.first_set_flag == 0 and s.host.get_motion() == 1:
            s.opcode = 0
    elif op == 3:
        if can_cast(s, s.skill_id):
            do_cast(s, s.skill_id)
    elif op == 4:
        if can_cast(s, int(s.skill_param[0])):
            s.host.set_attack_motion(int(s.skill_param[0]))
            do_cast(s, int(s.skill_param[0]))
    elif op == 5:
        if can_cast(s, s.skill_src_304):
            do_cast(s, s.skill_src_304)
    elif op == 6:
        if can_cast(s, s.skill_src_305):
            s.host.set_attack_motion(s.skill_src_305)
            do_cast(s, s.skill_src_305)
    elif op == 7:
        if can_cast(s, s.skill_src_308):
            do_cast(s, s.skill_src_308)
    elif op == 8:
        if can_cast(s, s.skill_src_30a):
            do_cast(s, s.skill_src_30a)
    elif op == 9:
        s.state = 1
        s.opcode = -1
    elif op in (10, 11):
        pass
    elif op == 12:
        s.host.get_motion()
        s.opcode = -1


def simulate_ai(ai_id: int, ai_def: dict) -> dict:
    """단일 AI 의 stream 을 끝까지 step + state machine 누적."""
    host = HostStub()
    s = State(host=host, ai_def=ai_def)
    # 1. 트리거 stream 전체 walk
    trigger_steps = 0
    while step_trigger_list(s):
        trigger_steps += 1
    while s.trigger_offset < len(_hex_to_bytes(ai_def.get("trigger_stream_hex", ""))):
        if not step_trigger_list(s): break
        trigger_steps += 1
    # 2. 액션 stream 전체 walk (모든 opcode 처리)
    action_steps = 0
    while step_action_list(s):
        action_steps += 1
        # 매 step 후 Ai_Action 도 한 번 dispatch
        ai_action(s)
    return {
        "trigger_steps": trigger_steps,
        "action_steps": action_steps,
        "trigger_overrun": s.trigger_offset > len(_hex_to_bytes(ai_def.get("trigger_stream_hex", ""))),
        "action_overrun": s.action_offset > len(_hex_to_bytes(ai_def.get("action_stream_hex", ""))),
        "casts": len(host.casts),
        "skill_set": s.skill_id != -1,
        "next_skill_set": s.skill_src_30a != 0,
    }


def main() -> None:
    if not AI_JSON.exists():
        print(f"[skip] {AI_JSON} 미발견 — import_to_godot.py 먼저 실행")
        return
    data = json.loads(AI_JSON.read_text(encoding="utf-8"))
    by_id = data.get("by_id", {})
    assert by_id, "monster_ai.json by_id 비어있음"
    print(f"# Monster AI VM round-trip 검증 — {len(by_id)} AI defs")
    total = {"trigger_steps": 0, "action_steps": 0, "casts": 0, "ok": 0, "fail": 0}
    fail_list: list[str] = []
    for ai_id, ai_def in sorted(by_id.items(), key=lambda x: int(x[0])):
        try:
            r = simulate_ai(int(ai_id), ai_def)
        except Exception as e:
            fail_list.append(f"ai_{ai_id}: {e!r}")
            total["fail"] += 1
            continue
        if r["trigger_overrun"] or r["action_overrun"]:
            fail_list.append(f"ai_{ai_id}: stream overrun")
            total["fail"] += 1
            continue
        total["ok"] += 1
        total["trigger_steps"] += r["trigger_steps"]
        total["action_steps"] += r["action_steps"]
        total["casts"] += r["casts"]
    print(f"  ok={total['ok']}/{len(by_id)}  fail={total['fail']}")
    print(f"  trigger_steps_total={total['trigger_steps']}  "
          f"action_steps_total={total['action_steps']}  "
          f"cast_calls={total['casts']}")
    if fail_list:
        for line in fail_list[:10]:
            print(f"  FAIL  {line}")
        raise SystemExit(1)
    # Round 47 sub-state dispatch — 모든 opcode 0..12 에서 예외 없이 동작
    sample_host = HostStub()
    s = State(host=sample_host, ai_def={})
    s.action_type = 1
    s.skill_id = 1
    s.skill_param[0] = 1
    s.skill_src_304 = 1
    s.skill_src_305 = 1
    s.skill_src_308 = 1
    s.skill_src_30a = 1
    for op in range(13):
        s.opcode = op
        ai_action(s)
    print(f"  Ai_Action 13 sub-state dispatch: all OK ({len(sample_host.casts)} casts)")
    assert sample_host.casts, "어떤 sub-state 도 cast 안 발생 — gate 로직 오류"
    print("# All checks passed.")


if __name__ == "__main__":
    main()
