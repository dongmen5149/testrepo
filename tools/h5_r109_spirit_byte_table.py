#!/usr/bin/env python3
"""R109: spirit extra_hex 의 0x00..0x32 byte 비교 — 차이 byte 식별."""
import json
from pathlib import Path

p = Path("apps/hero5-godot/assets/gamedata/c_csv_skill_05.json")
spirits = json.loads(p.read_text(encoding="utf-8"))["records"]

WIDTH = 0x32
print(f"{'idx':>3}  {'name':<10}  bytes[0x00..{WIDTH:#x}]")
print("-" * 130)
for i, sp in enumerate(spirits):
    b = bytes.fromhex(sp["extra_hex"])
    hx = " ".join(f"{b[j]:02x}" for j in range(min(WIDTH, len(b))))
    print(f"{i:>3}  {sp['name']:<10}  {hx}")
