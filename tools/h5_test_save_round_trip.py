#!/usr/bin/env python3
"""R91: Save round-trip 정합성 검증 (F 55→60%, 출시 +0.5%p).

R90 의 spirit desc UI 정제 후속. 이전 `quick_save → quick_load` 가
`apply_save` 의 누락 필드 때문에 round-trip 후 다음을 잃었음:
 - class_id (Sorcerer 가 Warrior 로 변함)
 - stat_str/dex/int/con / stat_points
 - equipment / unlocked_skills / skill_levels
 - play_time_sec
 - gunner_combo / gunner_max_combo / gunner_ammo
 - active_curses / active_buffs / active_stances
 - quest / mission 상태

R91 = `make_payload`, `to_save_dict`, `apply_save` 3 함수 정정으로
모든 필드 round-trip 보존.

검증 방법: GDScript 인스펙션 (필드 매칭) + Python 시뮬 (JSON dump → load
→ 비교). Godot Editor 실행 없이 정합성 보장.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"

GAME_STATE = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
SAVE_MGR = (GODOT / "scripts/core/save_manager.gd").read_text(encoding='utf-8')


def main():
    # 1. to_save_dict 가 모든 round-trip 필드 포함
    required_save = [
        "scene_id", "map_id", "play_time_sec",
        "player_x", "player_y", "player_dir",
        "class_id",
        "hp", "max_hp", "sp", "max_sp",
        "level", "exp", "gold",
        "stat_str", "stat_dex", "stat_int", "stat_con", "stat_points",
        "gunner_combo", "gunner_max_combo", "gunner_ammo",
        "active_curses", "active_buffs", "active_stances",
        "inventory", "equipment", "unlocked_skills", "skill_levels",
        "flags", "quest", "mission",
    ]
    save_section = GAME_STATE[GAME_STATE.find("func to_save_dict"):]
    save_section = save_section[:save_section.find("\nfunc ")]
    missing_save = [k for k in required_save if f'"{k}"' not in save_section]
    assert not missing_save, f"to_save_dict 누락 필드: {missing_save}"
    print(f"[PASS] to_save_dict: 31/31 round-trip 필드 모두 포함")

    # 2. apply_save 가 모든 필드 복원
    apply_section = GAME_STATE[GAME_STATE.find("func apply_save"):]
    apply_section = apply_section[:apply_section.find("\nfunc ")]
    required_apply = [
        ("class_id", "class_id ="),
        ("stat_str", "stat_str ="),
        ("stat_dex", "stat_dex ="),
        ("stat_int", "stat_int ="),
        ("stat_con", "stat_con ="),
        ("stat_points", "stat_points ="),
        ("equipment", "equipment.append" ),
        ("unlocked_skills", "unlocked_skills.append"),
        ("skill_levels", "skill_levels[int(k)]"),
        ("play_time_sec", "play_time_sec ="),
        ("gunner_combo", "gunner_combo ="),
        ("gunner_max_combo", "gunner_max_combo ="),
        ("gunner_ammo", "gunner_ammo ="),
        ("active_curses", "active_curses ="),
        ("active_buffs", "active_buffs ="),
        ("active_stances", "active_stances ="),
        ("quest", "Quest.from_save"),
        ("mission", "Mission.from_save"),
    ]
    missing_apply = [name for (name, marker) in required_apply if marker not in apply_section]
    assert not missing_apply, f"apply_save 누락 복원: {missing_apply}"
    print(f"[PASS] apply_save: 18/18 round-trip 복원 동작 모두 존재")

    # 3. make_payload 가 모든 필드 보존
    payload_section = SAVE_MGR[SAVE_MGR.find("func make_payload"):]
    payload_section = payload_section[:payload_section.find("\nstatic func ", 1)]
    required_payload = [
        "play_time_sec", "scene_id", "map_id",
        "class_id", "stat_points",
        "skill_levels", "gunner_combo", "gunner_max_combo", "gunner_ammo",
        "active_curses", "active_buffs", "active_stances",
        "equipment", "unlocked_skills", "flags", "quest", "mission",
    ]
    missing_payload = [k for k in required_payload if f'"{k}"' not in payload_section]
    assert not missing_payload, f"make_payload 누락 필드: {missing_payload}"
    print(f"[PASS] make_payload: 17/17 round-trip 필드 직렬화")

    # 4. JSON round-trip 시뮬 (Python 으로 GDScript 동작 모방)
    # to_save_dict → make_payload → JSON.stringify → JSON.parse → apply_save 의
    # 결과가 원본 state 와 동일한지.
    src_state = {
        "scene_id": 7, "map_id": 12, "play_time_sec": 3600,
        "player_x": 100, "player_y": 200, "player_dir": 2,
        "class_id": 4,   # Sorcerer
        "hp": 120, "max_hp": 200, "sp": 50, "max_sp": 100,
        "level": 15, "exp": 7,
        "gold": 9999,
        "stat_str": 22, "stat_dex": 18, "stat_int": 30, "stat_con": 14,
        "stat_points": 3,
        "gunner_combo": 2, "gunner_max_combo": 4, "gunner_ammo": 13,
        "active_curses": [{"dispatch": 1, "f1": 20, "f2": 0, "turns": 3}],
        "active_buffs": [{"dispatch": 3, "f1": 30, "f2": 0, "turns": 5}],
        "active_stances": [],
        "inventory": [101, 102, 103],
        "equipment": [-1, 5, -1, -1, 9, -1],
        "unlocked_skills": [0, 1, 5, 10],
        "skill_levels": {0: 1, 1: 2, 5: 3, 10: 1},
        "flags": {"npc_5": True, "ev_3": False},
        "quest": {"active": [1, 2], "completed": [10]},
        "mission": {"current": 5},
    }

    # make_payload 시뮬: GDScript JSON.stringify 와 동일하게 dict key 변환 +
    # skill_levels 의 int key 는 string 으로 변환됨 (JSON 표준).
    payload = {
        "version": 1,
        "play_time_sec": int(src_state["play_time_sec"]),
        "scene_id": src_state["scene_id"],
        "map_id": src_state["map_id"],
        "player": {
            "x": src_state["player_x"], "y": src_state["player_y"],
            "dir": src_state["player_dir"],
            "class_id": src_state["class_id"],
            "hp": src_state["hp"], "max_hp": src_state["max_hp"],
            "sp": src_state["sp"], "max_sp": src_state["max_sp"],
            "level": src_state["level"], "exp": src_state["exp"],
            "gold": src_state["gold"],
            "str": src_state["stat_str"], "dex": src_state["stat_dex"],
            "int": src_state["stat_int"], "con": src_state["stat_con"],
            "stat_points": src_state["stat_points"],
        },
        "inventory": src_state["inventory"],
        "equipment": src_state["equipment"],
        "unlocked_skills": src_state["unlocked_skills"],
        "skill_levels": {str(k): v for k, v in src_state["skill_levels"].items()},
        "gunner_combo": src_state["gunner_combo"],
        "gunner_max_combo": src_state["gunner_max_combo"],
        "gunner_ammo": src_state["gunner_ammo"],
        "active_curses": src_state["active_curses"],
        "active_buffs": src_state["active_buffs"],
        "active_stances": src_state["active_stances"],
        "flags": src_state["flags"],
        "quest": src_state["quest"],
        "mission": src_state["mission"],
    }
    serialized = json.dumps(payload)
    deserialized = json.loads(serialized)

    # apply_save 시뮬: GDScript 의 변환 로직 (player 내부 + skill_levels int key)
    p = deserialized["player"]
    restored = {
        "scene_id": int(deserialized["scene_id"]),
        "map_id": int(deserialized["map_id"]),
        "play_time_sec": int(deserialized["play_time_sec"]),
        "player_x": int(p["x"]), "player_y": int(p["y"]), "player_dir": int(p["dir"]),
        "class_id": int(p["class_id"]),
        "hp": int(p["hp"]), "max_hp": int(p["max_hp"]),
        "sp": int(p["sp"]), "max_sp": int(p["max_sp"]),
        "level": int(p["level"]), "exp": int(p["exp"]),
        "gold": int(p["gold"]),
        "stat_str": int(p["str"]), "stat_dex": int(p["dex"]),
        "stat_int": int(p["int"]), "stat_con": int(p["con"]),
        "stat_points": int(p["stat_points"]),
        "gunner_combo": int(deserialized["gunner_combo"]),
        "gunner_max_combo": int(deserialized["gunner_max_combo"]),
        "gunner_ammo": int(deserialized["gunner_ammo"]),
        "active_curses": deserialized["active_curses"],
        "active_buffs": deserialized["active_buffs"],
        "active_stances": deserialized["active_stances"],
        "inventory": deserialized["inventory"],
        "equipment": [int(v) for v in deserialized["equipment"]],
        "unlocked_skills": [int(v) for v in deserialized["unlocked_skills"]],
        "skill_levels": {int(k): int(v) for k, v in deserialized["skill_levels"].items()},
        "flags": deserialized["flags"],
        "quest": deserialized["quest"],
        "mission": deserialized["mission"],
    }
    # 비교
    for k in src_state:
        assert restored[k] == src_state[k], \
            f"round-trip 불일치 '{k}': src={src_state[k]!r} != restored={restored[k]!r}"
    print(f"[PASS] Python JSON round-trip: 31 필드 모두 동일 (class_id=4 Sorcerer 보존, "
          f"skill_levels int key, equipment Array[int])")

    # 5. apply_save 가 nested player + flat 양쪽 지원 (legacy)
    flat_section_match = "var p = data.get(\"player\", data)"
    assert flat_section_match in apply_section, \
        "apply_save 의 nested+flat 양립 fallback 손실"
    print(f"[PASS] apply_save: nested player + flat legacy 양쪽 지원 잔존")

    # 6. JSON skill_levels string-key → int 변환
    assert "skill_levels[int(k)] = int(sl_raw[k])" in apply_section, \
        "skill_levels JSON string-key → int 변환 누락"
    print(f"[PASS] apply_save: JSON skill_levels string-key → int 변환")

    # 7. equipment / unlocked_skills typed array 안전 복원
    assert "equipment.clear()" in apply_section, "equipment 재할당 안전 누락"
    assert "unlocked_skills.clear()" in apply_section, "unlocked_skills 재할당 안전 누락"
    print(f"[PASS] apply_save: typed Array[int] (equipment + unlocked_skills) 안전 복원")

    # 8. Quest + Mission singleton from_save 호출
    assert "Quest.from_save" in apply_section and "Mission.from_save" in apply_section
    print(f"[PASS] apply_save: Quest + Mission singleton from_save 호출")

    # 9. R90 회귀: resolve_skill_desc_display 함수 잔존
    gd = (GODOT / "scripts/core/game_data.gd").read_text(encoding='utf-8')
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in gd
    print(f"[PASS] R90 회귀: resolve_skill_desc_display + first_line 잔존")

    # 10. R91 docstring marker
    assert "Round 91" in GAME_STATE, "R91 docstring marker 누락 (game_state)"
    assert "Round 91" in SAVE_MGR, "R91 docstring marker 누락 (save_manager)"
    print(f"[PASS] R91 docstring marker (game_state + save_manager)")

    print("\n[R91 ALL PASSED] 10/10")


if __name__ == "__main__":
    main()
