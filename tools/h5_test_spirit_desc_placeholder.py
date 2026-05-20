#!/usr/bin/env python3
"""R90: Spirit/class skill desc placeholder resolution + display normalization (F 50→55%).

R88 의 EUC-KR 디코딩 + R89 의 launcher icons 후속. R88 의 raw desc 는
`}#NN<unit>|` placeholder + `;` 줄바꿈 마커를 포함한 채로 entry["desc"] 에
저장되어 있었음. R90 은 GameData 에 (1) `resolve_skill_desc_display`
(전체 desc 의 placeholder 치환 + `}...|` → `[...]` 강조 브래킷 + `;` → \\n)
와 (2) `resolve_skill_desc_first_line` (battle log 1줄용 첫 segment) 를
추가하고, battle_system 의 spirit 발동 로그가 후자를 사용하도록 정정.

검증:
- game_data.resolve_skill_desc_display 함수 시그니처 + 핵심 로직 (} ... | → [...],
  ; → 줄바꿈, resolve_skill_desc 위임).
- game_data.resolve_skill_desc_first_line 함수 시그니처 + 첫 줄 분리.
- battle_system 의 spirit 로그가 GameData.resolve_skill_desc_first_line 호출
  (이전 R88 의 raw desc split(";")[0] 직접 사용 → R90 GameData 위임).
- Python 시뮬: `}#05%|` placeholder + stats[5]=120 → `[120%]`,
  `;` → `\\n`, 짝 안 맞는 `}` 는 그대로 유지.
- R88/R87 회귀: c_csv_skill_05.json 의 16/16 desc_text 잔존,
  game_data 의 _ensure_spirit_skills_loaded + desc_text→desc wiring 잔존.
- R89 회귀: launcher_icons 3 PNG 존재 + export_presets.cfg launcher 경로.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    game_data = read("scripts/core/game_data.gd")
    battle = read("scripts/core/battle_system.gd")

    # 1. resolve_skill_desc_display 함수
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in game_data, \
        "resolve_skill_desc_display 시그니처 누락"
    # 위임 + 핵심 로직 marker
    for marker in [
        "var raw := resolve_skill_desc(class_id, skill_id)",
        'raw.find("|"',
        '"["',
        '"]"',
        '"\\n"',
    ]:
        assert marker in game_data, f"resolve_skill_desc_display 핵심 로직 누락: {marker!r}"
    print("[PASS] resolve_skill_desc_display 시그니처 + 핵심 로직 (} ... | → [...], ; → \\n)")

    # 2. resolve_skill_desc_first_line 함수
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in game_data, \
        "resolve_skill_desc_first_line 시그니처 누락"
    assert 'var full := resolve_skill_desc_display(class_id, skill_id)' in game_data, \
        "first_line 이 display 위임 안 함"
    assert 'full.find("\\n")' in game_data, "first_line 줄바꿈 분리 누락"
    print("[PASS] resolve_skill_desc_first_line 시그니처 + display 위임 + 줄바꿈 분리")

    # 3. battle_system 이 R90 helper 사용
    assert "GameData.resolve_skill_desc_first_line(5, skill_id)" in battle, \
        "battle_system spirit 로그가 R90 helper 미사용"
    # R88 의 raw split 직접 사용은 제거됐어야 함
    assert 'desc_str.split(";")[0].strip_edges()' not in battle, \
        "R88 raw split 잔존 (R90 helper 사용으로 정정 필요)"
    print("[PASS] battle_system spirit 발동 로그가 GameData.resolve_skill_desc_first_line 사용")

    # 4. Python 시뮬: } ... | → [...], ; → \n
    def simulate_display(raw: str, stats: list[int]) -> str:
        # resolve_skill_desc 치환 시뮬
        result = raw
        for i, v in enumerate(stats):
            result = result.replace(f"}}#{i:02d}", f"}}{v}")
            result = result.replace(f"#{i:02d}", str(v))
        # 강조 브래킷 변환
        out = []
        i = 0
        while i < len(result):
            c = result[i]
            if c == "}":
                close = result.find("|", i + 1)
                if close == -1:
                    out.append(c)
                    i += 1
                    continue
                out.append("[" + result[i + 1:close] + "]")
                i = close + 1
            elif c == ";":
                out.append("\n")
                i += 1
            else:
                out.append(c)
                i += 1
        return "".join(out)

    stats = [0, 0, 0, 0, 0, 120, 0, 30, 5, 600]
    raw = "거대한 암흑탄을 발사하여;정령마력 }#05%|의;피해를 준다."
    result = simulate_display(raw, stats)
    expected_lines = ["거대한 암흑탄을 발사하여", "정령마력 [120%]의", "피해를 준다."]
    actual = result.split("\n")
    assert actual == expected_lines, f"placeholder 치환 결과 불일치: {actual!r} vs {expected_lines!r}"
    print(f"[PASS] Python 시뮬 spirit desc: {expected_lines[1]!r} ← stats[5]=120")

    # 4b. 짝 안 맞는 `}` 는 그대로 유지
    weird = simulate_display("orphan } brace", [0] * 10)
    assert "}" in weird, "orphan } 가 사라짐"
    # 4c. 듀얼 placeholder
    dual = simulate_display("재사용 }#09초| + }#07MP|", [0, 0, 0, 0, 0, 0, 0, 30, 0, 600])
    assert "[600초]" in dual and "[30MP]" in dual, f"듀얼 치환 실패: {dual!r}"
    print("[PASS] Python 시뮬 추가: orphan }, 듀얼 placeholder ({dual!r})")

    # 5. R88 회귀: spirit desc_text 16/16
    spirit = json.loads((GODOT / "assets/gamedata/c_csv_skill_05.json").read_text(encoding='utf-8'))
    records = spirit["records"]
    assert len(records) == 16
    n_desc = sum(1 for r in records if r.get("desc_text", ""))
    assert n_desc == 16, f"R88 spirit desc_text 회귀 실패: {n_desc}/16"
    # game_data wiring
    assert 'var desc_text = str(r.get("desc_text", ""))' in game_data
    assert '"desc": desc_text,' in game_data
    print("[PASS] R88 회귀: spirit desc_text 16/16 + game_data wiring 잔존")

    # 6. R87 회귀: 8 explicit field
    for field in ["effect_type", "dynamic_formula_id", "special_dispatch",
                  "formula_id_1", "formula_id_2", "primary_u16",
                  "secondary_u16", "desc_len"]:
        assert f'entry["{field}"]' in game_data, f"R87 explicit field {field} 누락"
    print("[PASS] R87 회귀: 8 explicit field 잔존")

    # 7. R89 회귀: launcher icons 3 PNG + export_presets
    icons_dir = GODOT / "assets/launcher_icons"
    for f in ["main_192x192.png", "adaptive_foreground_432x432.png", "adaptive_background_432x432.png"]:
        assert (icons_dir / f).exists(), f"R89 launcher icon 누락: {f}"
    presets = (GODOT / "export_presets.cfg").read_text(encoding='utf-8')
    assert "main_192x192.png" in presets
    print("[PASS] R89 회귀: 3 launcher icons + export_presets.cfg")

    # 8. resolve_skill_desc 기존 함수 잔존 (R88 정상)
    assert "func resolve_skill_desc(class_id: int, skill_id: int) -> String:" in game_data
    assert '}#%02d" % i' in game_data, "resolve_skill_desc placeholder 패턴 누락"
    print("[PASS] resolve_skill_desc 기존 함수 잔존 + placeholder 패턴")

    # 9. R90 docstring marker
    assert "Round 90" in game_data, "R90 docstring marker 누락 (game_data)"
    assert "Round 90" in battle, "R90 docstring marker 누락 (battle_system)"
    print("[PASS] R90 docstring marker (game_data + battle_system)")

    # 10. 첫 줄 분리 시뮬
    def simulate_first_line(raw: str, stats: list[int]) -> str:
        full = simulate_display(raw, stats)
        if not full:
            return ""
        nl = full.find("\n")
        if nl == -1:
            return full.strip()
        return full[:nl].strip()

    fl = simulate_first_line(raw, stats)
    assert fl == "거대한 암흑탄을 발사하여", f"first_line 시뮬 실패: {fl!r}"
    # 단일 줄 (no `;`)
    fl_single = simulate_first_line("패시브 효과", [])
    assert fl_single == "패시브 효과"
    print(f"[PASS] Python 시뮬 first_line: {fl!r} (멀티 줄 첫 segment)")

    print("\n[R90 ALL PASSED] 10/10")


if __name__ == "__main__":
    main()
