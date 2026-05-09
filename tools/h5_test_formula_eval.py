#!/usr/bin/env python3
"""Formula VM 평가기 정합성 테스트 — Python 으로 GDScript 평가기와 동일 결과 산출.

GDScript 측의 formula_vm.gd 가 같은 알고리즘으로 동작하는지 확인 용도.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
from h5_formula_disasm import parse_file  # noqa: E402

OPS = {0x11: lambda a, b: a + b,
       0x12: lambda a, b: a - b,
       0x13: lambda a, b: a * b,
       0x14: lambda a, b: a // b if b else 0,
       0x15: lambda a, b: a % b if b else 0,
       0x16: lambda a, b: a ^ b}


def evaluate(formula: dict, var_lookup) -> int:
    """formula = parsed dict; var_lookup(var_id) → int."""
    stack: list[int] = []
    for kind, op, operand in formula["body"]:
        if kind == "imm":
            stack.append(operand)
        elif kind == "var":
            stack.append(var_lookup(operand))
        elif kind == "op":
            if len(stack) < 2:
                return 0
            b = stack.pop()
            a = stack.pop()
            stack.append(OPS.get(op, lambda x, y: 0)(a, b))
        else:  # opNN_skip → 0 fallback
            stack.append(0)
    if not stack:
        return 0
    return max(formula["lower"], min(formula["upper"], stack[-1]))


def main() -> int:
    plain = REPO / "work" / "h5" / "analysis" / "calc_pl_plain.bin"
    _, formulas = parse_file(plain.read_bytes())

    # Test fixture: player.atk = 100, level=10, str=20, all skill stats=0
    def lookup(var_id: int) -> int:
        if var_id == 0: return 0
        if var_id == 2: return 50         # skill base damage
        if var_id == 20: return 25         # skill multiplier %
        if var_id == 58: return 100        # player.atk
        if var_id == 153: return 30        # something
        if var_id == 154: return 20
        if var_id == 152: return 15
        if var_id == 151: return 10
        if var_id == 11: return 5
        if var_id == 12: return 5
        if var_id == 13: return 3
        if var_id == 14: return 2
        return 0

    # Expected: id=0 = clamp((50 + 32*100 + 10*30) * (100+25) / 100, 1, 30000)
    #         = (50 + 3200 + 300) * 125 / 100
    #         = 3550 * 125 / 100
    #         = 4437
    result = evaluate(formulas[0], lookup)
    expected = (50 + 32 * 100 + 10 * 30) * (100 + 25) // 100
    print(f"id=0: result={result}, expected={expected}, match={result == expected}")

    # Show a few more samples
    test_cases = [(1, "skill stats sum"), (2, "stat[1]+stat[16]"), (3, "stat[18]"), (4, "complex"), (10, "stat[8]+stat[27]+stat[152]/5")]
    for fid, desc in test_cases:
        result = evaluate(formulas[fid], lookup)
        print(f"id={fid} ({desc}): result={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
