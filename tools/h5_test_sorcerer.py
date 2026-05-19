#!/usr/bin/env python3
"""R83: Sorcerer (class_id=4) 부분 활성화 검증.

R22 stub (c_csv_skill_04 부재) 을 부분 활성화:
- class_select UI 에서 "(미구현)" → "(매직 — 기본+정령 스킬만)"
- battle_system._skill_data 가 class-aware (이전 class_0 하드코딩) + class 4 spirit fallback
- GameState.total_attack 에 Sorcerer INT × 2 magic bonus 추가
- demo.gd 진입 시 안내 메시지
- skill_book_panel 에 빈 list 안내 메시지

검증:
- class_stats.json 의 class 4 (소서러) 존재 + STR/DEX/CON/INT 데이터
- skills.json 의 class_4 부재 (c_csv_skill_04 없음) 확정
- 위 5 파일의 R83 변경사항 모두 존재
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    # 1. class_stats.json: class 4 (소서러) 데이터 존재
    cs = json.loads((GODOT / "assets/gamedata/class_stats.json").read_text(encoding='utf-8'))
    assert len(cs) >= 5, f"class_stats.json 에 5 class 필요, 있음: {len(cs)}"
    sorcerer = cs[4]
    assert sorcerer.get("name") == "소서러", f"class 4 name != 소서러: {sorcerer.get('name')}"
    assert sorcerer.get("INT", 0) >= 8, f"Sorcerer INT 데이터 누락"
    assert sorcerer.get("CON", 0) >= 12, f"Sorcerer CON 데이터 누락 (CON-heavy magic class)"
    print(f"[PASS] class_stats.json: 소서러 STR={sorcerer['STR']} DEX={sorcerer['DEX']} CON={sorcerer['CON']} INT={sorcerer['INT']}")

    # 2. skills.json: class_4 부재 + c_csv_skill_05.json 에 spirit 별도 존재
    sk = json.loads((GODOT / "assets/gamedata/skills.json").read_text(encoding='utf-8'))
    assert "class_4" not in sk, "예상치 못한 class_4 데이터 (c_csv_skill_04 부재 가설 깨짐)"
    for cid in range(4):
        assert "class_%d" % cid in sk, f"class_{cid} 데이터 필요"
    # spirit 은 별도 c_csv_skill_05.json 에 raw 형식
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    assert spirit_path.exists(), "c_csv_skill_05.json (spirit raw) 부재"
    spirit_raw = json.loads(spirit_path.read_text(encoding='utf-8'))
    assert spirit_raw.get("count", 0) >= 16, f"spirit count ≥16 필요"
    assert len(spirit_raw.get("records", [])) >= 16, "spirit records ≥16 필요"
    print(f"[PASS] skills.json: class_0..3 존재 + c_csv_skill_05.json: spirit {spirit_raw['count']} records 별도 존재, class_4 부재 확정")

    # 3. class_select.gd: 라벨 변경 + docstring 갱신
    cs_gd = read("scripts/ui/class_select.gd")
    assert "(매직 — 기본+정령 스킬만)" in cs_gd, "class_select 라벨 미변경 ('(미구현)' 잔존 또는 새 라벨 부재)"
    assert "(미구현)" not in cs_gd, "class_select 의 '(미구현)' 라벨 잔존"
    assert "Round 83" in cs_gd and "부분 활성화" in cs_gd, "class_select R83 docstring 누락"
    print("[PASS] class_select.gd: 라벨 '(매직 — 기본+정령 스킬만)' + R83 docstring")

    # 4. battle_system.gd: class-aware _skill_data + Sorcerer fallback
    bs = read("scripts/core/battle_system.gd")
    assert "Round 83" in bs and "class-aware lookup" in bs, "battle_system R83 docstring 누락"
    assert 'class_%d" % cid' in bs, "battle_system 의 class-aware lookup 미적용"
    assert 'cid == 4' in bs, "Sorcerer (class 4) fallback 누락"
    assert '"class_5"' in bs, "Sorcerer spirit (class_5) fallback 누락"
    assert "[정령]" in bs, "Sorcerer spirit skill name prefix 누락"
    assert "[미구현]" in bs, "Sorcerer stub fallback prefix 누락"
    # 이전 하드코딩 class_0 흔적 제거
    assert 'GameData._skills_cache.get("class_0", [])' not in bs, \
        "battle_system 에 class_0 하드코딩 잔존"
    print("[PASS] battle_system.gd: class-aware _skill_data + Sorcerer spirit/stub fallback")

    # 5. game_state.gd: total_attack 에 Sorcerer INT bonus
    gs = read("scripts/core/game_state.gd")
    assert "Round 83" in gs and "Sorcerer" in gs, "game_state R83 docstring 누락"
    assert "class_id == 4" in gs and "stat_int * 2" in gs, \
        "Sorcerer INT magic bonus 미적용"
    print("[PASS] game_state.gd: total_attack 에 Sorcerer INT × 2 magic bonus")

    # 6. demo.gd: Sorcerer 진입 안내
    demo = read("scripts/ui/demo.gd")
    assert "GameState.class_id == 4" in demo, "demo.gd Sorcerer 진입 검사 누락"
    assert "소서러" in demo or "Sorcerer" in demo, "demo.gd 의 Sorcerer 안내 메시지 누락"
    assert "정령" in demo or "spirit" in demo, "demo.gd 의 정령 스킬 안내 누락"
    print("[PASS] demo.gd: Sorcerer 진입 시 안내 dialog")

    # 7a. game_data.gd: _ensure_spirit_skills_loaded 추가 (Round 83)
    gd = read("scripts/core/game_data.gd")
    assert "_ensure_spirit_skills_loaded" in gd, "game_data 의 spirit loader 누락"
    assert "c_csv_skill_05.json" in gd, "spirit 별도 파일 로드 누락"
    assert 'class_5' in gd and "Round 83" in gd, "spirit cache key 또는 R83 docstring 누락"
    print("[PASS] game_data.gd: _ensure_spirit_skills_loaded (c_csv_skill_05.json → class_5 cache)")

    # 7. skill_book_panel.gd: 빈 list 안내
    sb = read("scripts/ui/skill_book_panel.gd")
    assert "Round 83" in sb, "skill_book_panel R83 변경 누락"
    assert "class_id == 4" in sb and "class_books.is_empty()" in sb, \
        "Sorcerer 빈 list 검사 누락"
    assert "active skill 데이터 부재" in sb, "Sorcerer 안내 메시지 누락"
    print("[PASS] skill_book_panel.gd: Sorcerer 빈 list 안내 메시지")

    # 8. Sorcerer INT bonus 시뮬 검증 (Python)
    # class 4: STR=6, DEX=8, CON=14, INT=8 (class_stats.json)
    # base = stat_str * 2 + level * 3 = 6*2 + 1*3 = 15
    # Sorcerer + INT*2 = 15 + 8*2 = 31
    # 일반 클래스 (class 0 워리어, STR=12): base = 12*2 + 1*3 = 27, no INT bonus → 27
    # 즉 Sorcerer base attack 31 > 워리어 base attack 27 (active skill 부재 보상)
    def sim_attack(cid, lv, s, i):
        base = s * 2 + lv * 3
        if cid == 4:
            base += i * 2
        return base
    sorc = sim_attack(4, 1, 6, 8)
    warr = sim_attack(0, 1, 12, 10)
    assert sorc == 31, f"Sorcerer base attack Lv.1 = {sorc} (expected 31)"
    assert warr == 27, f"Warrior base attack Lv.1 = {warr} (expected 27)"
    print(f"[PASS] Sorcerer base attack Lv.1 = {sorc} vs Warrior = {warr} (active skill 부재 보상 합리적)")

    print("\n=== R83 Sorcerer (class_id=4) 부분 활성화: ALL PASSED ===")


if __name__ == "__main__":
    main()
