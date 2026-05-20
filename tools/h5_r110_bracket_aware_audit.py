#!/usr/bin/env python3
"""R110: 괄호 (}...|) 내부 #NN 와 bare #NN (skill-link) 분리 검증.

R108 의 `result.replace("#%02d", val)` 무차별 치환이 `#01돌격-스턴효과` 같은
skill-link 참조를 corruption — `0돌격-스턴효과` 처럼. R110 = bracket-aware
replace 로 `}...|` 내부의 #NN 만 치환.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "apps/hero5-godot/assets/gamedata/skills.json"


def main():
    data = json.loads(SKILLS.read_text(encoding="utf-8"))
    total_in_bracket = 0
    total_bare_link = 0
    labeled_examples = []
    bare_link_examples = []

    for cls_key in ("class_0", "class_1", "class_2", "class_3"):
        for sidx, sk in enumerate(data.get(cls_key, [])):
            desc = sk.get("desc", "")
            name = sk.get("name", "?")
            # 괄호 내부 placeholder (}...|)
            for m in re.finditer(r"\}([^|]*?)\|", desc):
                inner = m.group(1)
                for sub in re.finditer(r"#(\d{2})", inner):
                    total_in_bracket += 1
                    prefix = inner[: sub.start()].strip()
                    suffix = inner[sub.end():].strip()
                    if prefix and len(labeled_examples) < 4 and (sub.group(1) == "07"):
                        labeled_examples.append({
                            "cls": cls_key, "name": name,
                            "form": m.group(0)[:50], "nn": int(sub.group(1)),
                            "prefix": prefix, "suffix": suffix,
                        })
            # bare #NN (스킬-링크 후보)
            # `;` 다음 또는 \n 다음에 등장하는 `#NN`
            for m in re.finditer(r"[;\n]#(\d{2})(\S{0,10})", desc):
                total_bare_link += 1
                if len(bare_link_examples) < 6:
                    bare_link_examples.append({
                        "cls": cls_key, "name": name,
                        "nn": int(m.group(1)), "link_text": m.group(2),
                    })

    print(f"괄호 내부 #NN (true placeholder): {total_in_bracket}")
    print(f"bare #NN (skill-link): {total_bare_link}")
    print()
    print("=== Labeled placeholder examples (}<label> #NN<unit>|) ===")
    for e in labeled_examples:
        print(f"  {e['cls']}[{e['name']:<12}] {e['form']!r} → #{e['nn']:02d} prefix={e['prefix']!r}")
    print()
    print("=== Bare #NN skill-link examples ===")
    for e in bare_link_examples:
        print(f"  {e['cls']}[{e['name']:<12}] #{e['nn']:02d}{e['link_text']}")

    print()
    print("CONCLUSION:")
    print(f"  R108 의 'replace(#NN, val)' 가 {total_bare_link} 개 skill-link 를 corruption.")
    print(f"  R110 fix: 괄호 내부만 #NN 치환 (총 {total_in_bracket} 회 placeholder).")


if __name__ == "__main__":
    main()
