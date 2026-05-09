"""§4.4 dispatcher 후보 v3 — UNRECOVERED_JUMPTABLE + 강화된 sprite 제외.

v2 에서 0x19770 이 또 sprite drawer 로 판정. RGB565 만으로는 4-bit palette 기반 sprite 제외 불가.

v3 변경:
  - UNRECOVERED_JUMPTABLE 변수 사용 함수 추출 (jump-table 기반 dispatcher 표지)
  - palette lookup 패턴 (`& 0xf`, `>> 4`, `* 4 + local`) 도 sprite drawer 로 제외
  - 작은 함수 (< 100 lines) 우선 — 진짜 dispatcher 는 보통 분기만 있고 작음
  - switch case 조건 >= 3 으로 완화
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "dispatcher_candidates_v3.json"

FUNC_HEADER = re.compile(r"^[\w\s\*]+\s(FUN_[0-9a-fA-F]+|UndefinedFunction_[0-9a-fA-F]+)\s*\(")
ADDR_FROM_NAME = re.compile(r"(FUN_|UndefinedFunction_)([0-9a-fA-F]+)")

CALL_PAT = re.compile(r"\b(FUN_[0-9a-fA-F]+|UndefinedFunction_[0-9a-fA-F]+|thunk_FUN_[0-9a-fA-F]+)\s*\(")
SWITCH_PAT = re.compile(r"\bswitch\s*\(")
CASE_PAT = re.compile(r"\bcase\s+(0x[0-9a-fA-F]+|\d+)\s*:")
VAR_CMP = re.compile(r"(\w+)\s*==\s*(0x[0-9a-fA-F]+|\d+)\b")

# Sprite drawer disqualifiers
SPRITE_TELLS = [
    re.compile(r"0x(f81f|07e0|f800|3e0|1ff8|003f|001f)\b", re.IGNORECASE),  # RGB565 masks
    re.compile(r"&\s*0xf\b"),                       # 4-bit nibble (low)
    re.compile(r">>\s*4\b"),                        # 4-bit nibble (high)
    re.compile(r"\*\s*4\s*\+\s*local_\w+\b"),       # palette index lookup
    re.compile(r"<<\s*0x18\)\s*>>\s*0x1c"),         # 4-bit extract trick
    re.compile(r"frameBuf|pixelBuf|drawSprite", re.IGNORECASE),
]
ROW_COL = re.compile(r"for\s*\([^)]*\bwidth\b|while\s*\(.*?\bwidth\b", re.IGNORECASE)

# Strong dispatcher indicators
JUMPTABLE = re.compile(r"\bUNRECOVERED_JUMPTABLE\b")
FP_CALL = re.compile(r"\(\s*\*\s*\(\s*code\s*\*\*?\s*\)|\(\*\s*UNRECOVERED_JUMPTABLE\s*\)")


def parse_value(s: str) -> int | None:
    try:
        return int(s, 16) if s.startswith("0x") else int(s)
    except ValueError:
        return None


def find_function_boundaries(text: str) -> list[tuple[int, int]]:
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        if FUNC_HEADER.match(lines[i]):
            start = i
            j = i
            while j < len(lines) and "{" not in lines[j]:
                j += 1
            if j >= len(lines):
                break
            depth = 0
            k = j
            while k < len(lines):
                depth += lines[k].count("{") - lines[k].count("}")
                if depth == 0:
                    out.append((start, k + 1))
                    i = k + 1
                    break
                k += 1
            else:
                break
        else:
            i += 1
    return out


def is_sprite_drawer(body: str) -> tuple[bool, str]:
    if ROW_COL.search(body):
        return True, "row/col loop"
    hits = []
    for pat in SPRITE_TELLS:
        m = pat.search(body)
        if m:
            hits.append(pat.pattern[:30])
    # need ≥ 2 sprite tells (any single one is too aggressive)
    if len(hits) >= 2:
        return True, f"sprite tells: {hits[:3]}"
    return False, ""


def analyze(text: str, lines: list[str], start: int, end: int) -> dict:
    body = "\n".join(lines[start:end])
    addr_match = ADDR_FROM_NAME.search(lines[start])
    addr = "0x" + addr_match.group(2).lower() if addr_match else "?"
    name = addr_match.group(0) if addr_match else "?"

    sprite, sprite_reason = is_sprite_drawer(body)

    cmps = VAR_CMP.findall(body)
    var_to_vals: dict[str, list[int]] = {}
    for var, val in cmps:
        v = parse_value(val)
        if v is None or v > 0xFF:
            continue
        var_to_vals.setdefault(var, []).append(v)
    best_var = None
    best_vals: list[int] = []
    for var, vals in var_to_vals.items():
        small = sorted(set(v for v in vals if v <= 0x40))
        if len(small) > len(best_vals):
            best_var = var
            best_vals = small

    cases = [parse_value(c) for c in CASE_PAT.findall(body)]
    cases = sorted(set(c for c in cases if c is not None))

    callees = set(CALL_PAT.findall(body)) - {name}

    return {
        "addr": addr,
        "name": name,
        "lines": end - start,
        "is_sprite": sprite,
        "sprite_reason": sprite_reason,
        "switches": len(SWITCH_PAT.findall(body)),
        "cases": cases[:30],
        "case_count": len(cases),
        "best_cmp_var": best_var,
        "small_cmp_distinct": len(best_vals),
        "small_cmp_vals": best_vals[:15],
        "fp_calls": len(FP_CALL.findall(body)),
        "jumptable": len(JUMPTABLE.findall(body)),
        "distinct_callees": len(callees),
    }


BLACKLIST = {
    "0x10ea4", "0x10fe4", "0x14e68", "0x158c6", "0x15a2c", "0x15b8c",
    "0x182c4", "0x1a568", "0x186c8", "0x18d08", "0x190f8",
    "0x33016", "0x410b0", "0x41172", "0x4ac40",
    "0x9889c", "0x98ef8", "0x4ad10", "0x19b5a",
    "0x19770",  # 2026-05-09 (이번 세션) sprite drawer 추가 확인
}


def main() -> None:
    print(f"reading {SRC} ...")
    text = SRC.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    print(f"  {len(lines):,} lines")

    boundaries = find_function_boundaries(text)
    print(f"  {len(boundaries):,} functions")

    print("analyzing ...")
    funcs = [analyze(text, lines, s, e) for s, e in boundaries]
    for f in funcs:
        f["blacklisted"] = f["addr"] in BLACKLIST

    # === [A] UNRECOVERED_JUMPTABLE 사용자 (가장 강한 후보) ===
    jt_cands = [
        f for f in funcs
        if f["jumptable"] >= 1
        and not f["is_sprite"]
        and not f["blacklisted"]
    ]
    jt_cands.sort(key=lambda f: (f["jumptable"], f["small_cmp_distinct"]), reverse=True)

    # === [B] switch 문 (case ≥ 3) ===
    switch_cands = [
        f for f in funcs
        if f["switches"] >= 1
        and f["case_count"] >= 3
        and not f["is_sprite"]
        and not f["blacklisted"]
    ]
    switch_cands.sort(key=lambda f: (f["case_count"], f["lines"]), reverse=True)

    # === [C] chain dispatch (작은 함수 우선) ===
    chain_cands = [
        f for f in funcs
        if f["small_cmp_distinct"] >= 5
        and not f["is_sprite"]
        and f["lines"] < 600  # dispatcher 는 보통 작거나 중간
        and not f["blacklisted"]
    ]
    chain_cands.sort(
        key=lambda f: (f["small_cmp_distinct"], f["fp_calls"], -f["lines"]),
        reverse=True,
    )

    # === [D] 모든 함수 — sprite 제외 + small dispatcher signal ===
    all_disp = [
        f for f in funcs
        if (f["small_cmp_distinct"] >= 4 or f["case_count"] >= 3 or f["jumptable"] >= 1)
        and not f["is_sprite"]
        and not f["blacklisted"]
    ]
    all_disp.sort(
        key=lambda f: (
            f["jumptable"] * 10
            + (f["case_count"] if f["case_count"] >= 3 else 0)
            + f["small_cmp_distinct"]
            + f["fp_calls"]
        ),
        reverse=True,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "jumptable_candidates": jt_cands[:30],
                "switch_candidates": switch_cands[:30],
                "chain_candidates": chain_cands[:30],
                "combined_top": all_disp[:30],
                "sprite_count": sum(1 for f in funcs if f["is_sprite"]),
                "total_funcs": len(funcs),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    def show(group, header):
        print()
        print("=" * 78)
        print(header)
        print("=" * 78)
        print(f"{'addr':<11} {'lines':>5} {'jt':>3} {'sw':>3} {'cases':>5} {'cmps':>4} {'fp':>3} {'callees':>7} sample")
        for f in group[:15]:
            vals = ",".join(f"0x{v:02x}" for v in f["small_cmp_vals"][:5])
            print(
                f"{f['addr']:<11} {f['lines']:>5} {f['jumptable']:>3} "
                f"{f['switches']:>3} {f['case_count']:>5} {f['small_cmp_distinct']:>4} "
                f"{f['fp_calls']:>3} {f['distinct_callees']:>7} {vals}"
            )

    show(jt_cands, "[A] UNRECOVERED_JUMPTABLE candidates (strongest)")
    show(switch_cands, "[B] switch candidates (cases >= 3)")
    show(chain_cands, "[C] chain candidates (small fn, >= 5 cmps)")
    show(all_disp, "[D] combined ranked top")

    print()
    print(f"sprite drawers excluded: {sum(1 for f in funcs if f['is_sprite']):,}/{len(funcs):,}")
    print(f"full result: {OUT}")


if __name__ == "__main__":
    main()
