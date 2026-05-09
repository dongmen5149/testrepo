#!/usr/bin/env python3
"""calc_*.dat 평문 + var_dict TSV 를 GDScript 가 로드할 JSON 으로 export.

산출:
  apps/hero5-godot/assets/data/formula/formulas.json
    {"id": [{lower, upper, body: [["op",op_int]|["imm",val]|["var",var_id]]}], ...}
  apps/hero5-godot/assets/data/formula/var_dict.json
    {"var_id": {"struct": "skill"|"defender"|"item"|"gv_sub"|"global", "offset": int, "type": "s8|s16|u32|..."}}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from h5_formula_disasm import parse_file  # noqa: E402

ANALYSIS = REPO / "work" / "h5" / "analysis"
OUT_DIR = REPO / "apps" / "hero5-godot" / "assets" / "data" / "formula"


def encode_formula(formula: dict) -> dict:
    """parse_file 결과 → JSON-friendly form."""
    body: list[list] = []
    for kind, op, operand in formula["body"]:
        if kind == "imm":
            body.append(["imm", operand])
        elif kind == "var":
            body.append(["var", operand])
        elif kind == "op":
            body.append(["op", op])
        else:
            # op0xN_skip — 0 fallback
            body.append(["imm", 0])
    return {"lower": formula["lower"], "upper": formula["upper"], "body": body}


def export_formulas() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        ("calc_pl_plain.bin", 0),
        ("calc_en_plain.bin", 1000),
        ("calc_sk_plain.bin", 2000),
    ]
    out: dict[str, dict] = {}
    total = 0
    for fname, id_offset in files:
        p = ANALYSIS / fname
        if not p.exists():
            print(f"missing {p}", file=sys.stderr)
            return 1
        _, formulas = parse_file(p.read_bytes())
        for f in formulas:
            out[str(id_offset + f["idx"])] = encode_formula(f)
            total += 1
    out_path = OUT_DIR / "formulas.json"
    out_path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path} ({total} formulas)")
    return 0


# 변수 ID 의 의미 분류 (FORMULA_VAR_DICT.md 기반)
def classify_var(var_id: int, struct_hint: str, offset: int, type_str: str) -> dict:
    """var_id → {struct, offset, type, role}.

    struct_hint (gv_sub/skill/defender/item/r3/pc/...) 가 의미 있으면 우선.
    그 외에는 var_id range 로 분류.
    """
    # 특수 const ID (FORMULA_VAR_DICT.md 기반): 0, 248-253 = constant
    if var_id == 0:
        return {"struct": "const", "offset": 0, "type": "s32", "role": "constant_zero"}
    if 248 <= var_id <= 253 and struct_hint != "gv_sub":
        return {"struct": "const", "offset": 0, "type": "s32", "role": "constant_special"}
    # gv 오버레이 (정확한 disasm 기반) 우선
    if struct_hint == "gv_sub":
        return {"struct": "gv_sub", "offset": offset, "type": type_str, "role": "player_state"}
    if struct_hint in ("skill", "skill_sb"):
        role = "skill_stat" if struct_hint == "skill" else "skill_stat_sb"
        return {"struct": struct_hint, "offset": offset, "type": type_str, "role": role}
    if struct_hint == "defender":
        return {"struct": "defender", "offset": offset, "type": type_str, "role": "defender_stat"}
    if struct_hint == "item":
        return {"struct": "item", "offset": offset, "type": type_str, "role": "item_stat"}
    # range fallback
    if 1 <= var_id <= 60:
        return {"struct": "skill", "offset": offset, "type": type_str, "role": "skill_stat"}
    if 168 <= var_id <= 182:
        return {"struct": "item", "offset": offset, "type": type_str, "role": "item_stat"}
    if 192 <= var_id <= 251:
        return {"struct": "defender", "offset": offset, "type": type_str, "role": "defender_stat"}
    if 184 <= var_id <= 191:
        return {"struct": "skill_sb", "offset": offset, "type": type_str, "role": "skill_stat_sb"}
    if 58 <= var_id <= 167:
        return {"struct": "gv_sub", "offset": offset, "type": type_str, "role": "player_state"}
    if var_id == 0:
        return {"struct": "const", "offset": 0, "type": "s32", "role": "constant_zero"}
    if 248 <= var_id <= 253:
        return {"struct": "const", "offset": 0, "type": "s32", "role": "constant_special"}
    return {"struct": "unknown", "offset": offset, "type": type_str, "role": "unknown"}


def export_var_dict() -> int:
    """formula_var_dict.tsv + gv_substruct_layout.tsv 를 합쳐 JSON dict 로."""
    base = ANALYSIS / "formula_var_dict.tsv"
    gv = ANALYSIS / "gv_substruct_layout.tsv"
    if not base.exists() or not gv.exists():
        print("missing TSVs", file=sys.stderr)
        return 1

    # 베이스: skill/defender/item/sb 등
    base_lines = base.read_text(encoding="utf-8").splitlines()
    base_map: dict[int, dict] = {}
    for line in base_lines[1:]:
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        var_id = int(cols[0])
        struct = cols[2].strip()
        offset_str = cols[3].strip()
        try:
            offset = int(offset_str, 0) if offset_str else 0
        except ValueError:
            # Some rows have a function name (e.g. ObjectType callee) instead
            offset = 0
            struct = struct or "callee"
        type_guess = "u32"  # default
        first = cols[4] if len(cols) > 4 else ""
        if "ldrsh" in first:
            type_guess = "s16"
        elif "ldrh" in first:
            type_guess = "u16"
        elif "ldrb" in first:
            type_guess = "u8"
        elif "ldrsb" in first:
            type_guess = "s8"
        elif first.startswith("ldr ") or "ldr r" in first:
            type_guess = "u32"
        base_map[var_id] = {"struct": struct, "offset": offset, "type": type_guess}

    # gv overlay (정확한 offset/type)
    gv_lines = gv.read_text(encoding="utf-8").splitlines()
    for line in gv_lines[1:]:
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        var_id = int(cols[0])
        type_str = cols[1]
        offset = int(cols[2], 0)
        base_map[var_id] = {"struct": "gv_sub", "offset": offset, "type": type_str}

    # 분류 적용
    out: dict[str, dict] = {}
    for var_id, info in base_map.items():
        out[str(var_id)] = classify_var(var_id, info["struct"], info["offset"], info["type"])

    # 누락된 0..253 도 채움
    for vid in range(254):
        if str(vid) not in out:
            out[str(vid)] = classify_var(vid, "unknown", 0, "u32")

    out_path = OUT_DIR / "var_dict.json"
    out_path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path} ({len(out)} var_ids)")
    return 0


def main() -> int:
    return export_formulas() or export_var_dict()


if __name__ == "__main__":
    raise SystemExit(main())
