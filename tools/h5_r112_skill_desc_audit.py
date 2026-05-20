#!/usr/bin/env python3
"""R112: 전 skill desc 의 resolve_skill_desc_display 출력 audit.

R111 까지의 fix 가 모든 skill 에 안전하게 적용됐는지 확인:
- 잔존 raw 마커 (`#NN`, `}`, `|`, `{`) 검출
- placeholder 해결률 (resolved vs unresolved)
- spirit (class_5) + class_0..3 전체 카운트

Python 시뮬 (GDScript resolve_skill_desc_display 동등 로직).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"

LABELS = {4: "효과", 5: "공격", 6: "마법", 7: "MP",
          8: "지속", 9: "쿨", 10: "값", 11: "강화",
          12: "수치", 13: "양"}
SOURCE = {4: True, 5: True, 6: True, 7: True, 8: True, 9: True}  # #12 R109 제거
THRESHOLD = 500


def format_display(nn, value):
    if value < 0 or value > THRESHOLD:
        return f"?({LABELS[nn]})" if nn in LABELS else "?"
    return str(value)


def eval_stat(nn, stats, info):
    """R108 eval_placeholder_stat 시뮬 (Formula null + explicit field 기반)."""
    if nn in SOURCE:
        # spirit explicit field 우선 — 시뮬에선 info 의 값 사용
        if nn == 5 or nn == 6:
            v = info.get("primary_u16", -1)
        elif nn == 4 or nn == 8:
            v = info.get("secondary_u16", -1)
        elif nn == 7:
            v = info.get("mp_cost", -1)
        elif nn == 9:
            v = info.get("cooldown", -1)
        else:
            v = -1
        if 0 <= v <= THRESHOLD:
            return v
    # stats fallback
    if 0 <= nn < len(stats):
        raw = stats[nn]
        if raw <= THRESHOLD:
            return raw
    return -1


def resolve_desc(desc, stats, info):
    """R111 resolve_skill_desc + indices 자동 수집 시뮬."""
    indices = set(SOURCE.keys())
    for i in range(len(stats)):
        indices.add(i)
    # 괄호 내부 #NN 자동 수집
    bi = 0
    while bi < len(desc):
        b_open = desc.find("}", bi)
        if b_open == -1:
            break
        b_close = desc.find("|", b_open + 1)
        if b_close == -1:
            break
        inner = desc[b_open + 1:b_close]
        for m in re.finditer(r"#(\d{2})", inner):
            indices.add(int(m.group(1)))
        bi = b_close + 1

    values = {}
    for i in indices:
        v = eval_stat(i, stats, info)
        values[i] = format_display(i, v)

    # bracket-aware replace
    out = ""
    i = 0
    while i < len(desc):
        if desc[i] == "}":
            close = desc.find("|", i + 1)
            if close == -1:
                out += desc[i:]
                break
            inner = desc[i + 1:close]
            for nn, val in values.items():
                inner = inner.replace(f"#{nn:02d}", val)
            out += "}" + inner + "|"
            i = close + 1
        else:
            out += desc[i]
            i += 1
    return out


def display(raw):
    """R112 resolve_skill_desc_display 시뮬 — quirk 흡수 포함."""
    out = ""
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "}":
            # R112: `|` 또는 `{` close marker, 더 가까운 쪽
            close_pipe = raw.find("|", i + 1)
            close_brace = raw.find("{", i + 1)
            if close_pipe == -1:
                close = close_brace
            elif close_brace == -1:
                close = close_pipe
            else:
                close = min(close_pipe, close_brace)
            if close == -1:
                out += c
                i += 1
                continue
            # R112: 중첩 `}` 평탄화
            inner = raw[i + 1:close].replace("}", "")
            out += "[" + inner + "]"
            i = close + 1
        elif c == "{":
            close = raw.find("|", i + 1)
            if close == -1:
                out += c
                i += 1
                continue
            header = raw[i + 1:close]
            if header == "관련특성":
                out += "▸ 관련 특성:"
            else:
                out += "▸ " + header + ":"
            i = close + 1
        elif c == "#" and i + 2 < len(raw) and raw[i + 1].isdigit() and raw[i + 2].isdigit() \
                and (not out or out.endswith("\n")):
            out += "• "
            i += 3
        elif c == ";":
            out += "\n"
            i += 1
        else:
            out += c
            i += 1
    return out


def parse_spirit(rec):
    b = bytes.fromhex(rec["extra_hex"])
    return {
        "primary_u16": (b[0x22] | (b[0x23] << 8)) if len(b) > 0x23 else 0,
        "secondary_u16": (b[0x24] | (b[0x25] << 8)) if len(b) > 0x25 else 0,
        "mp_cost": b[0x07] if len(b) > 7 else 0,
        "cooldown": b[0x0d] if len(b) > 0xd else 0,
    }


def audit():
    spirits = json.loads((GODOT / "assets/gamedata/c_csv_skill_05.json").read_text(encoding="utf-8"))["records"]
    skills = json.loads((GODOT / "assets/gamedata/skills.json").read_text(encoding="utf-8"))

    total = 0
    issues = []  # (cls, idx, name, issue, snippet)

    # spirit
    for sidx, sp in enumerate(spirits):
        total += 1
        desc = sp.get("desc_text", "")
        if not desc:
            continue
        info = parse_spirit(sp)
        # spirit stats_u16 — R88 의 file-loaded 0x00..0x2f 영역 부분
        b = bytes.fromhex(sp["extra_hex"])
        stats = [(b[i + 1] << 8) | b[i] for i in range(0, min(48, len(b)) - 1, 2)]
        resolved = resolve_desc(desc, stats, info)
        rendered = display(resolved)
        # 잔존 마커 검사
        for marker, name in [("}", "raw `}`"), ("|", "raw `|`"),
                              ("{", "raw `{`"), (re.compile(r"#\d{2}"), "raw `#NN`")]:
            if isinstance(marker, str):
                if marker in rendered:
                    issues.append(("class_5", sidx, sp.get("name", "?"), name,
                                   rendered[:80].replace("\n", "\\n")))
                    break
            else:
                if marker.search(rendered):
                    issues.append(("class_5", sidx, sp.get("name", "?"), name,
                                   rendered[:80].replace("\n", "\\n")))
                    break

    # class_0..3
    for cls_key in ("class_0", "class_1", "class_2", "class_3"):
        for sidx, sk in enumerate(skills.get(cls_key, [])):
            total += 1
            desc = sk.get("desc", "")
            if not desc:
                continue
            stats = sk.get("stats_u16", [])
            info = {}  # class_0..3 는 explicit field 부재
            resolved = resolve_desc(desc, stats, info)
            rendered = display(resolved)
            for marker, name in [("}", "raw `}`"), ("|", "raw `|`"),
                                  ("{", "raw `{`"), (re.compile(r"#\d{2}"), "raw `#NN`")]:
                if isinstance(marker, str):
                    if marker in rendered:
                        issues.append((cls_key, sidx, sk.get("name", "?"), name,
                                       rendered[:80].replace("\n", "\\n")))
                        break
                else:
                    if marker.search(rendered):
                        issues.append((cls_key, sidx, sk.get("name", "?"), name,
                                       rendered[:80].replace("\n", "\\n")))
                        break

    print(f"Total skills audited: {total}")
    print(f"Issues (잔존 raw marker): {len(issues)}")
    print()
    if issues:
        print("=== Issues ===")
        for iss in issues[:20]:
            print(f"  {iss[0]}[{iss[1]:>2}] {iss[2]:<10} — {iss[3]}: {iss[4]!r}")
        if len(issues) > 20:
            print(f"  ... ({len(issues) - 20} more)")
    else:
        print("✓ 잔존 raw marker 0 — 모든 스킬 정상 변환")


if __name__ == "__main__":
    audit()
