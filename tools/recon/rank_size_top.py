"""사용자가 Ghidra Function 표에서 size sort 한 top 후보들을 우선순위 정렬.

각 함수의 다음을 본다:
  - 인자 갯수 (dispatcher 는 보통 1~4개)
  - 변수 선언 갯수 (적을수록 dispatcher 가능성 ↑)
  - byte deref 갯수
  - 작은 정수 비교 갯수
  - sprite 표지
  - 이미 검증된 함수 (blacklist) 제외
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"
V3 = REPO / "work" / "h3" / "dispatcher_candidates_v3.json"

# 사용자 캡처에서 가져온 size sort top 34
TOP_LIST = [
    ("0x6d89c", 3444), ("0x15ba0", 3390), ("0x650bc", 3308), ("0x1281a", 2992),
    ("0x14e68", 2612), ("0x19b5a", 2556), ("0x11bc2", 2320), ("0x113cc", 2038),
    ("0xa145e", 1982), ("0x702d8", 1924), ("0x4b9b4", 1824), ("0xa01ba", 1764),
    ("0x78eea", 1718), ("0x6c31c", 1702), ("0x190f8", 1622), ("0x56248", 1596),
    ("0x6cbcc", 1536), ("0x98904", 1520), ("0x72fe8", 1438), ("0x83b92", 1433),
    ("0x38dbc", 1412), ("0x3ee28", 1406), ("0x186c8", 1368), ("0x8e112", 1246),
    ("0x8b726", 1242), ("0x6ea3c", 1150), ("0x1719c", 1102), ("0x98ef8", 1100),
    ("0x168fc", 1100), ("0x175f4", 1090), ("0x16d50", 1090), ("0x17a40", 1086),
    ("0x17e88", 1084), ("0x4c450", 1074),
]

# 이미 검증된/제외 함수
BLACKLIST = {
    "0x10ea4", "0x10fe4", "0x14e68", "0x158c6", "0x15a2c", "0x15b8c",
    "0x182c4", "0x1a568", "0x186c8", "0x18d08", "0x190f8",
    "0x33016", "0x410b0", "0x41172", "0x4ac40",
    "0x9889c", "0x98ef8", "0x4ad10", "0x19b5a",
    "0x19770", "0x11bc2",
}

# Sprite drawer 모듈 (인접 주소 클러스터)
SPRITE_NEAR = {
    "0x15ba0": "0x15a2c/0x158c6/0x15b8c sprite cluster",
    "0x113cc": "0x10ea4/0x10fe4 BM decoder cluster",
    "0x98904": "0x9889c boss data getter cluster",
    "0x18d08": "0x18xxx sprite cluster (verified false positive)",
    "0x190f8": "0x19xxx sprite cluster (verified false positive)",
    "0x19b5a": "0x19xxx sprite cluster (verified false positive)",
    "0x186c8": "0x18xxx sprite cluster (verified false positive)",
}

FUNC_HEADER = re.compile(r"^[\w\s\*]+\s(FUN_[0-9a-fA-F]+|UndefinedFunction_[0-9a-fA-F]+)\s*\(([^)]*)\)")


def extract(text: str, addr: str) -> tuple[str, int, int] | None:
    a = addr.removeprefix("0x").lower().zfill(8)
    pat = re.compile(rf"^[\w\s\*]+\s(FUN_|UndefinedFunction_){a}\s*\(([^)]*)\)", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return None
    args_blob = m.group(2)
    args = [a.strip() for a in args_blob.split(",") if a.strip() and a.strip() != "void"]
    arg_count = len(args)
    # function body
    start = m.start()
    depth = 0
    seen = False
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
            seen = True
        elif text[i] == "}":
            depth -= 1
            if seen and depth == 0:
                body = text[start : i + 1]
                # local var declarations (rough: lines ending with ; before first non-decl statement)
                decl_section = body[: body.find("\n  \n") if "\n  \n" in body else 2000]
                local_count = decl_section.count(";\n")
                return body, arg_count, local_count
        i += 1
    return None


def stats(body: str) -> dict:
    has_rgb565 = bool(re.search(r"0x(f81f|07e0|f800|3e0|1ff8|003f|001f|7e0)\b", body, re.IGNORECASE))
    has_palette = bool(re.search(r"&\s*0xf\b") if False else re.search(r"&\s*0xf\b", body))
    has_nibble = bool(re.search(r">>\s*4\b", body))
    has_pal_lookup = bool(re.search(r"\*\s*4\s*\+\s*local_\w+", body))
    has_inf_loop = bool(re.search(r"while\s*\(\s*true\s*\)|for\s*\(\s*;\s*;\s*\)", body))
    do_while = body.count("do {") + body.count("do{")
    fp_call = len(re.findall(r"\(\s*\*\s*\(\s*code\s*\*\*?\s*\)|\(\*\s*UNRECOVERED_JUMPTABLE\s*\)", body))
    jt = body.count("UNRECOVERED_JUMPTABLE")
    byte_deref = len(re.findall(r"\*\s*\(?\s*\(?\s*(byte|char|undefined1|uchar)\s*\*\)?", body))
    # small int compares on same var
    cmps = re.findall(r"(\w+)\s*==\s*(0x[0-9a-fA-F]+|\d+)\b", body)
    var_to_vals: dict[str, list[int]] = {}
    for var, val in cmps:
        try:
            v = int(val, 16) if val.startswith("0x") else int(val)
        except ValueError:
            continue
        if v <= 0x40:
            var_to_vals.setdefault(var, []).append(v)
    best_n = max((len(set(v)) for v in var_to_vals.values()), default=0)
    best_var = max(var_to_vals.items(), key=lambda kv: len(set(kv[1])), default=(None, []))[0]
    best_vals = sorted(set(var_to_vals.get(best_var, []))) if best_var else []
    sprite_score = sum([has_rgb565, has_palette, has_nibble, has_pal_lookup])
    return {
        "rgb565": has_rgb565,
        "nibble": has_nibble,
        "pal_lookup": has_pal_lookup,
        "sprite_score": sprite_score,
        "inf_loop": has_inf_loop,
        "do_while": do_while,
        "fp_call": fp_call,
        "jumptable": jt,
        "byte_deref": byte_deref,
        "small_cmp_n": best_n,
        "small_cmp_var": best_var,
        "small_cmp_vals": best_vals[:8],
    }


def main() -> None:
    text = SRC.read_text(encoding="utf-8", errors="replace")

    rows = []
    for addr, size in TOP_LIST:
        if addr in BLACKLIST:
            rows.append({"addr": addr, "size": size, "status": "BLACKLIST", "reason": "이미 검증됨"})
            continue
        if addr in SPRITE_NEAR:
            note = f"인접: {SPRITE_NEAR[addr]}"
        else:
            note = ""
        result = extract(text, addr)
        if result is None:
            rows.append({"addr": addr, "size": size, "status": "NOT_FOUND"})
            continue
        body, arg_count, local_count = result
        s = stats(body)
        # priority score
        # - args 적을수록 ↑, RGB565/sprite 표지 있으면 ↓, byte_deref+cmp+jt+fp 있으면 ↑
        score = 0
        if arg_count <= 4:
            score += 10
        elif arg_count <= 7:
            score += 3
        score -= s["sprite_score"] * 5
        score += s["byte_deref"] // 3
        score += s["small_cmp_n"] * 2
        score += s["jumptable"]
        score += s["fp_call"]
        if s["inf_loop"]:
            score += 5
        if s["do_while"]:
            score += 2
        rows.append({
            "addr": addr,
            "size": size,
            "args": arg_count,
            "locals": local_count,
            "score": score,
            "note": note,
            **s,
        })

    # sort: BLACKLIST/NOT_FOUND last, others by score desc
    def key(r):
        if r.get("status") in ("BLACKLIST", "NOT_FOUND"):
            return (1, 0)
        return (0, -r["score"])

    rows.sort(key=key)

    print()
    print("=" * 100)
    print(f"{'rank':<5} {'addr':<11} {'size':>5} {'args':>4} {'spr':>3} {'b_d':>3} {'cmp':>3} {'jt':>2} {'fp':>3} {'loop':>4} score note")
    print("=" * 100)
    rank = 1
    for r in rows:
        if r.get("status") == "BLACKLIST":
            print(f"---  {r['addr']:<11} {r['size']:>5}  ❌ BLACKLIST — {r['reason']}")
            continue
        if r.get("status") == "NOT_FOUND":
            print(f"---  {r['addr']:<11} {r['size']:>5}  ⚠ not in decompiled output")
            continue
        loop = ("inf" if r["inf_loop"] else (f"d{r['do_while']}" if r["do_while"] else "-"))
        print(
            f"{rank:>3}.  {r['addr']:<11} {r['size']:>5} {r['args']:>4} "
            f"{r['sprite_score']:>3} {r['byte_deref']:>3} {r['small_cmp_n']:>3} "
            f"{r['jumptable']:>2} {r['fp_call']:>3} {loop:>4} "
            f"{r['score']:>5}  {r['note']}"
        )
        rank += 1
    print()
    print("표지: spr=sprite점수(낮을수록↑) / b_d=byte deref / cmp=같은변수 small int 비교수")
    print("       jt=UNRECOVERED_JUMPTABLE / fp=함수포인터호출 / loop=무한루프/do-while")


if __name__ == "__main__":
    main()
