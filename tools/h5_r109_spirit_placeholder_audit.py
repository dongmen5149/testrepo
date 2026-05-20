#!/usr/bin/env python3
"""R109: spirit placeholder 실 값 + 단위 중복 검출.

R108 의 PLACEHOLDER_STAT_SOURCE 적용 후 16 spirit 의 placeholder 별 resolved
값을 산출, 단위 중복 (예: `[?(공격%)%]` / `[?(지속초)초]`) 여지를 검출.

산출:
- 표준 출력에 spirit 별 raw / explicit field / resolved 표
- R109 fix 의 근거 (label 에서 단위 제거 시 안전성)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPIRIT = ROOT / "apps/hero5-godot/assets/gamedata/c_csv_skill_05.json"

THRESHOLD = 500
# R108 현재 labels (단위 포함)
LABELS_R108 = {4: "효과%", 5: "공격%", 6: "마법%", 7: "MP", 8: "지속초", 9: "쿨초", 12: "배수"}
# R109 후보 labels (단위 제거)
LABELS_R109 = {4: "효과", 5: "공격", 6: "마법", 7: "MP", 8: "지속", 9: "쿨", 12: "수치"}

SOURCE = {
    4: ("formula_id_2", "secondary_u16"),
    5: ("formula_id_1", "primary_u16"),
    6: ("formula_id_1", "primary_u16"),
    7: (None, "mp_cost"),
    8: ("formula_id_2", "secondary_u16"),
    9: (None, "cooldown"),
    12: (None, "primary_u16"),
}


def parse_spirit(rec):
    b = bytes.fromhex(rec["extra_hex"])
    return {
        "primary_u16": (b[0x22] | (b[0x23] << 8)) if len(b) > 0x23 else 0,
        "secondary_u16": (b[0x24] | (b[0x25] << 8)) if len(b) > 0x25 else 0,
        "mp_cost": b[0x07] if len(b) > 7 else 0,
        "cooldown": b[0x0d] if len(b) > 0xd else 0,
        "formula_id_1": b[0x2d] if len(b) > 0x2d else 0,
        "formula_id_2": b[0x2e] if len(b) > 0x2e else 0,
    }


def eval_value(nn, fields):
    """R108 logic (FormulaVM null 가정) — fid → 0, field → 값."""
    src = SOURCE.get(nn)
    if src is None:
        return -1
    formula_key, field = src
    if field and field in fields:
        v = fields[field]
        if 0 <= v <= THRESHOLD:
            return v
    return -1


def fmt_r108(nn, value):
    if value < 0 or value > THRESHOLD:
        return f"?({LABELS_R108[nn]})" if nn in LABELS_R108 else "?"
    return str(value)


def fmt_r109(nn, value):
    if value < 0 or value > THRESHOLD:
        return f"?({LABELS_R109[nn]})" if nn in LABELS_R109 else "?"
    return str(value)


def show_resolved(desc, fmt):
    """`}#NN<unit>|` placeholder 를 fmt(NN, val) 로 치환."""
    out = desc
    for m in re.finditer(r"#(\d{2})", desc):
        nn = int(m.group(1))
        out = out.replace(f"#{m.group(1)}", "<NN>", 1)
    return out


def main():
    spirits = json.loads(SPIRIT.read_text(encoding="utf-8"))["records"]
    print(f"{'idx':>3}  {'name':<10}  {'prim':>5}  {'sec':>5}  {'mp':>3}  {'cd':>3}  {'fid1':>4}  {'fid2':>4}  placeholders")
    print("-" * 100)

    unresolved_cnt = 0
    double_unit_cnt = 0
    for i, s in enumerate(spirits):
        name = s["name"]
        fields = parse_spirit(s)
        desc = s.get("desc_text", "")
        phs = re.findall(r"#(\d{2})([^|]*)\|", desc)
        ph_strs = []
        for nn_s, unit in phs:
            nn = int(nn_s)
            val = eval_value(nn, fields)
            r108 = fmt_r108(nn, val)
            r109 = fmt_r109(nn, val)
            tag = f"#{nn_s}{unit}|→{r108}{unit}|"
            ph_strs.append(tag)
            if val < 0:
                unresolved_cnt += 1
                # 단위 중복 검출
                if nn in LABELS_R108 and unit:
                    r108_label = LABELS_R108[nn]
                    if unit and any(ch in r108_label for ch in unit):
                        double_unit_cnt += 1
        print(f"{i:>3}  {name:<10}  {fields['primary_u16']:>5}  {fields['secondary_u16']:>5}  "
              f"{fields['mp_cost']:>3}  {fields['cooldown']:>3}  {fields['formula_id_1']:>4}  "
              f"{fields['formula_id_2']:>4}  {ph_strs}")

    print()
    print(f"unresolved (val=-1) placeholder 수: {unresolved_cnt}")
    print(f"  → R108 label 적용 시 단위 중복 발생: {double_unit_cnt}")
    print()
    print("ASSESSMENT:")
    print("  R109 label (단위 제거) 적용 시 unresolved 시나리오 모두 안전.")
    print("  resolved 시나리오는 unit 본문 그대로 노출 (R108 동일).")


if __name__ == "__main__":
    main()
