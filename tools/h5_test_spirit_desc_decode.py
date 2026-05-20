#!/usr/bin/env python3
"""R88: Spirit (class_5) description EUC-KR 디코딩 검증 (F 40→50%).

R87 의 Spirit extra_hex full mapping 후속. R77 file layout 의 desc_string
영역 (bytes[48..48+desc_len], EUC-KR 인코딩) 을 후처리 디코딩하여
c_csv_skill_05.json 의 각 record 에 desc_text 필드 추가.

검증:
- 16 spirit 모두 desc_text 비어있지 않음 + 한국어 포함
- 핵심 spirit (#0 암흑탄, #2 영혼의회복, #7 정신감응) 의 desc 키워드 매칭
- game_data._ensure_spirit_skills_loaded 가 desc_text → entry["desc"] 로 채움
- game_data.resolve_skill_desc 가 class_5 호출 시 spirit loader 자동 호출
- battle_system._skill_data 가 desc 반환 + SKILL action 발동 시 로그에 첫 라인 노출
- tools/converter/decode_h5_skill_desc.py 존재 + decode_record 함수
- R87 회귀 (explicit field + 8 spirit field) 잔존
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    # 1. tools/converter/decode_h5_skill_desc.py 존재 + 핵심 구조
    desc_tool = ROOT / "tools/converter/decode_h5_skill_desc.py"
    assert desc_tool.exists(), "decode_h5_skill_desc.py not found"
    tool_src = desc_tool.read_text(encoding='utf-8')
    assert "def decode_record" in tool_src, "decode_record function missing"
    assert "euc-kr" in tool_src or "euc_kr" in tool_src, "EUC-KR codec missing"
    assert "STATS_AREA_SIZE = 48" in tool_src, "stats area size 48 constant missing"
    assert "DESC_LEN_OFFSET = 0x2f" in tool_src, "desc_len offset 0x2f missing"
    print("[PASS] tools/converter/decode_h5_skill_desc.py 존재 + EUC-KR codec + 48B/0x2f 상수")

    # 2. c_csv_skill_05.json 모든 record 에 desc_text 필드
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    data = json.loads(spirit_path.read_text(encoding='utf-8'))
    records = data["records"]
    assert len(records) == 16, f"spirit count != 16: {len(records)}"
    n_with_desc = sum(1 for r in records if r.get("desc_text", ""))
    assert n_with_desc == 16, f"desc_text 가 없는 record: {16 - n_with_desc}"
    print(f"[PASS] c_csv_skill_05.json: 16/16 record 모두 desc_text 필드 보유")

    # 3. desc_text 가 실제 한국어 포함 (EUC-KR 디코딩 성공)
    def has_hangul(s: str) -> bool:
        return any('가' <= c <= '힣' for c in s)
    for i, r in enumerate(records):
        d = r.get("desc_text", "")
        assert has_hangul(d), f"spirit #{i} {r.get('name')} desc 한글 없음: {d!r}"
    print(f"[PASS] 16 spirit desc 모두 한국어 포함 (EUC-KR 디코딩 성공)")

    # 4. 핵심 spirit 의 desc 키워드 매칭
    s0 = records[0]
    assert s0["name"] == "암흑탄", f"spirit #0 name: {s0['name']}"
    assert "암흑탄" in s0["desc_text"], f"spirit #0 desc keyword: {s0['desc_text']!r}"
    assert "정령마력" in s0["desc_text"], f"spirit #0 desc 정령마력 키워드 누락"
    print(f"[PASS] spirit #0 암흑탄: '암흑탄' + '정령마력' 키워드 매칭")

    s2 = records[2]
    assert s2["name"] == "영혼의회복", f"spirit #2 name: {s2['name']}"
    assert "버프" in s2["desc_text"], f"spirit #2 desc '버프' 누락: {s2['desc_text']!r}"
    assert "HP" in s2["desc_text"], f"spirit #2 desc 'HP' 누락"
    print(f"[PASS] spirit #2 영혼의회복: '버프' + 'HP' 키워드 매칭")

    s7 = records[7]
    assert s7["name"] == "정신감응", f"spirit #7 name: {s7['name']}"
    assert "패시브" in s7["desc_text"], f"spirit #7 desc '패시브' 누락"
    assert "정령" in s7["desc_text"], f"spirit #7 desc '정령' 누락"
    print(f"[PASS] spirit #7 정신감응: '패시브' + '정령' 키워드 매칭")

    # 5. game_data.gd: _ensure_spirit_skills_loaded 가 desc_text → entry["desc"] 채움
    gd = read("scripts/core/game_data.gd")
    assert "Round 88" in gd, "missing R88 docstring"
    assert 'desc_text = str(r.get("desc_text"' in gd, \
        "missing desc_text retrieval"
    assert '"desc": desc_text' in gd, \
        "missing entry desc assignment"
    print("[PASS] game_data._ensure_spirit_skills_loaded: desc_text → entry['desc'] 채움")

    # 6. resolve_skill_desc class_5 분기 (spirit loader 자동 호출)
    assert "class_id == 5 and not _skills_cache.has" in gd, \
        "missing resolve_skill_desc class_5 fallback"
    print("[PASS] resolve_skill_desc class_5 호출 시 _ensure_spirit_skills_loaded 자동 호출")

    # 7. battle_system._skill_data 가 desc 반환
    bs = read("scripts/core/battle_system.gd")
    assert '"desc": str(rec.get("desc"' in bs, \
        "_skill_data missing desc field"
    assert "Round 88" in bs, "missing R88 docstring in battle_system"
    print("[PASS] battle_system._skill_data: desc 필드 반환 (외부 UI 조회용)")

    # 8. SKILL action 발동 시 spirit desc 첫 라인 로그 노출 (R90 이후 GameData 위임)
    has_r88_inline = 'desc_str: String = str(skill_data.get("desc"' in bs and 'split(";")[0]' in bs
    has_r90_helper = "GameData.resolve_skill_desc_first_line(5, skill_id)" in bs
    assert has_r88_inline or has_r90_helper, \
        "battle log 의 spirit desc 첫 라인 노출 누락 (R88 inline 또는 R90 GameData helper)"
    assert "▸" in bs, "log marker '▸' 누락"
    print("[PASS] battle_system SKILL action: spirit desc 첫 라인 로그 노출 (R90 GameData helper)")

    # 9. R87 회귀 (explicit field + 8 spirit field 유지)
    assert 'class_id == 5 and rec.has("effect_type")' in gd, \
        "R87 explicit field branch 손실"
    assert 'bytes[0x1a]' in gd, "R87 sub-rel offset 0x1a (effect_type) 손실"
    assert 'bytes[0x2f]' in gd, "R87 sub-rel offset 0x2f (desc_len) 손실"
    print("[PASS] R87 회귀: explicit field + 8 sub-rel offset 잔존")

    # 10. R87 spirit data effect_type 분포 검증 회귀
    def parse_effect_type(hex_str):
        b = bytes.fromhex(hex_str)
        return b[0x1a] if len(b) > 0x1a else -1
    effect_types = [parse_effect_type(r["extra_hex"]) for r in records]
    dist = {t: effect_types.count(t) for t in set(effect_types)}
    assert dist.get(0, 0) == 5, f"effect_type 0 count != 5: {dist}"
    assert dist.get(2, 0) == 9, f"effect_type 2 (curse) count != 9: {dist}"
    assert dist.get(7, 0) == 2, f"effect_type 7 (timestop) count != 2: {dist}"
    print(f"[PASS] R87 effect_type 분포 회귀: 0=5 / 2=9 / 7=2 (총 16)")

    # 11. desc 평균 길이 통계 (sanity check)
    desc_lens = [len(r["desc_text"]) for r in records]
    avg = sum(desc_lens) / len(desc_lens)
    assert 20 < avg < 100, f"desc 평균 길이 비정상: {avg:.1f}"
    print(f"[PASS] desc 평균 길이: {avg:.1f} 글자 (min={min(desc_lens)}, max={max(desc_lens)})")

    print("\n=== R88 Spirit desc EUC-KR decode: ALL PASSED ===")


if __name__ == "__main__":
    main()
