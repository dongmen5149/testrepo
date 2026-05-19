#!/usr/bin/env python3
"""R87: Spirit (class_5) extra_hex full 의미 매핑 검증 (F 27→40%).

R77 LoadResSkillInfo file layout 의 정확한 sub-rel offset 으로 explicit field 추출:
- effect_type (sub-rel 0x1a)
- dynamic_formula_id (sub-rel 0x26)
- special_dispatch (sub-rel 0x2b)
- formula_id_1 / formula_id_2 (sub-rel 0x2d / 0x2e)
- primary_u16 / secondary_u16 (sub-rel 0x22 / 0x24 LE)

R83 의 spirit fallback (battle_system 의 _skill_data) 이 정확 field 사용 시
Sorcerer 의 정령 스킬이 의미있는 effect_type/formula 로 동작.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def parse_spirit_fields(hex_str):
    """R77 sub-rel offset → explicit fields."""
    b = bytes.fromhex(hex_str)
    if len(b) < 48:
        return None
    return {
        "effect_type": b[0x1a],
        "dynamic_formula_id": b[0x26],
        "special_dispatch": b[0x2b],
        "formula_id_1": b[0x2d],
        "formula_id_2": b[0x2e],
        "primary_u16": b[0x22] | (b[0x23] << 8),
        "secondary_u16": b[0x24] | (b[0x25] << 8),
        "desc_len": b[0x2f],
    }


def main():
    # 1. game_data.gd 에 R87 변경 markers
    gd = read("scripts/core/game_data.gd")
    assert "Round 87" in gd, "missing R87 docstring"
    assert "R77 sub-rel offset" in gd, "missing R77 sub-rel offset reference"
    assert "explicit field" in gd or "명시" in gd, "missing explicit field language"
    print("[PASS] game_data.gd: R87 docstring + R77 sub-rel offset 참조")

    # 2. _ensure_spirit_skills_loaded 의 8 명시적 field 추출
    explicit_fields = [
        ('bytes[0x1a]', '"effect_type"'),
        ('bytes[0x26]', '"dynamic_formula_id"'),
        ('bytes[0x2b]', '"special_dispatch"'),
        ('bytes[0x2d]', '"formula_id_1"'),
        ('bytes[0x2e]', '"formula_id_2"'),
        ('bytes[0x22]', '"primary_u16"'),
        ('bytes[0x24]', '"secondary_u16"'),
        ('bytes[0x2f]', '"desc_len"'),
    ]
    for byte_ref, field_key in explicit_fields:
        # Field assignment pattern
        assert field_key in gd, f"missing field assignment {field_key}"
    # Byte indexing patterns (with literal hex)
    for byte_ref, _ in explicit_fields:
        assert byte_ref in gd, f"missing byte indexing {byte_ref}"
    print(f"[PASS] _ensure_spirit_skills_loaded: 8 explicit fields ({', '.join(f for _, f in explicit_fields)})")

    # 3. skill_info() 가 class 5 일 때 explicit field 직접 반환
    assert 'class_id == 5 and rec.has("effect_type")' in gd, \
        "skill_info() missing class_5 explicit fallback"
    # Spirit 명시 분기 return 안에 명시적 키들
    assert 'rec.get("primary_u16", 0)' in gd, "missing primary_u16 in spirit return"
    print("[PASS] skill_info() class_5 명시적 field 직접 반환 (stats_u16 추정 안 거침)")

    # 4. Sample spirit data 의 R77 field 추출 검증 (Python parallel)
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    spirit = json.loads(spirit_path.read_text(encoding='utf-8'))
    records = spirit["records"]
    assert len(records) == 16, f"spirit count != 16: {len(records)}"

    # 거대탄 (spirit #0): effect_type=0, primary_u16=400 (큰 폭탄)
    s0 = parse_spirit_fields(records[0]["extra_hex"])
    assert s0["effect_type"] == 0, f"spirit #0 effect_type expected 0, got {s0['effect_type']}"
    assert s0["primary_u16"] == 400, f"spirit #0 primary_u16 expected 400, got {s0['primary_u16']}"
    print(f"[PASS] spirit #0 거대탄: effect_type=0 (NO_HIT base) / primary_u16=400 (big bomb)")

    # 마법기 (spirit #1): effect_type=2, dynamic_formula_id=116, special_dispatch=107, F_1=57, F_2=68
    s1 = parse_spirit_fields(records[1]["extra_hex"])
    assert s1["effect_type"] == 2, f"spirit #1 effect_type expected 2 (curse), got {s1['effect_type']}"
    assert s1["dynamic_formula_id"] == 116, f"spirit #1 dyn_F expected 116, got {s1['dynamic_formula_id']}"
    assert s1["special_dispatch"] == 107, f"spirit #1 sd expected 107, got {s1['special_dispatch']}"
    assert s1["formula_id_1"] == 57, f"spirit #1 formula_id_1 expected 57"
    assert s1["formula_id_2"] == 68, f"spirit #1 formula_id_2 expected 68"
    print(f"[PASS] spirit #1 마법기: effect_type=2 (curse) / dyn_F=116 / sd=107 / F_1=57 / F_2=68")

    # 매혹기술 (spirit #7): effect_type=7 (timestop), special_dispatch=44, F_1=57
    s7 = parse_spirit_fields(records[7]["extra_hex"])
    assert s7["effect_type"] == 7, f"spirit #7 effect_type expected 7 (timestop), got {s7['effect_type']}"
    assert s7["special_dispatch"] == 44, f"spirit #7 sd expected 44, got {s7['special_dispatch']}"
    assert s7["formula_id_1"] == 57, f"spirit #7 formula_id_1 expected 57"
    print(f"[PASS] spirit #7 매혹기술: effect_type=7 (timestop) / sd=44 / F_1=57")

    # 5. effect_type 분포 검증 (16 spirit)
    effect_types = [parse_spirit_fields(r["extra_hex"])["effect_type"] for r in records]
    dist = {t: effect_types.count(t) for t in set(effect_types)}
    assert dist[0] == 5, f"effect_type 0 count != 5: {dist}"
    assert dist[2] == 9, f"effect_type 2 (curse) count != 9: {dist}"
    assert dist[7] == 2, f"effect_type 7 (timestop) count != 2: {dist}"
    assert sum(dist.values()) == 16, f"effect_type total != 16: {dist}"
    print(f"[PASS] effect_type 분포: 0={dist[0]} (base) / 2={dist[2]} (curse) / 7={dist[7]} (timestop) — total {sum(dist.values())} debuff 위주")

    # 6. R83 spirit fallback 유지 (battle_system 의 class 5 lookup)
    bs = read("scripts/core/battle_system.gd")
    assert '"class_5"' in bs, "R83 spirit fallback 손실"
    assert '[정령]' in bs, "R83 spirit prefix 손실"
    print("[PASS] R83 battle_system spirit fallback (class_5 + [정령] prefix) 잔존")

    # 7. R84 _hex_to_bytes / stats_u16 유지 (회귀)
    assert "_hex_to_bytes" in gd, "R84 hex helper 손실"
    assert "stats_u16" in gd, "R84 stats_u16 cache 손실"
    print("[PASS] R84 _hex_to_bytes + stats_u16 cache 잔존")

    # 8. formula_id_1 분포 검증 (대부분 57)
    f1_dist = [parse_spirit_fields(r["extra_hex"])["formula_id_1"] for r in records]
    f1_count = {f: f1_dist.count(f) for f in set(f1_dist)}
    assert f1_count[57] >= 9, f"formula_id_1=57 count expected >=9: {f1_count}"
    assert f1_count[0] >= 4, f"formula_id_1=0 (NO_HIT) count expected >=4: {f1_count}"
    print(f"[PASS] formula_id_1 분포: {f1_count} (대부분 Formula 57 — spirit 의 통일 공식)")

    print("\n=== R87 Spirit extra_hex full mapping: ALL PASSED ===")


if __name__ == "__main__":
    main()
