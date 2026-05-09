#!/usr/bin/env python3
"""Formula VM 디스어셈블러 — calc_*.dat 평문 → 사람이 읽을 수 있는 공식 dump.

`Formula::calcByFormula` (0x77244) 분석 결과:

파일 구조:
  [u8 magic=0x02][u8 formula_count][u8 padding=0x00]
  formulas[]
    [u8 size = total - 2][u8 padding][i32 lower][i32 upper][u8 body_count]
    body[body_count]:
      operator (op & 0x10): 1 byte
      operand (op == 0):     5 bytes (op + i32 immediate)
      operand (op == 0x0c):  5 bytes (op + i32 var_id → getValFunc 로 fetch)
      otherwise:             5 bytes (skipped — getNumberInStack 가 0 반환)

opcode (op - 0x11 → jump table 인덱스):
  0x11 ADD, 0x12 SUB, 0x13 MUL, 0x14 DIV, 0x15 MOD, 0x16 XOR

스택 머신:
  - operand → push
  - operator → pop B(top), pop A(2nd), push op(A,B)
  - 최종 결과 = stack 잔여 → clamp(lower, upper)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

OPCODES = {0x11: "ADD", 0x12: "SUB", 0x13: "MUL", 0x14: "DIV", 0x15: "MOD", 0x16: "XOR"}


def s32(b: bytes) -> int:
    """4 byte little-endian → signed int."""
    v = int.from_bytes(b, "little")
    return v - 0x100000000 if v & 0x80000000 else v


def parse_file(data: bytes) -> tuple[int, list[dict]]:
    """파일 헤더 + 모든 formula 파싱.

    Returns (formula_count, [formula, ...])
    formula = {'idx', 'size_byte', 'lower', 'upper', 'body_count', 'body': [(kind, op, operand), ...]}
    """
    if data[0] != 0x02:
        raise ValueError(f"unexpected magic byte 0x{data[0]:02x}")
    count = data[1]
    formulas: list[dict] = []
    pos = 3
    for fi in range(count):
        if pos >= len(data):
            break
        size_byte = data[pos]
        # padding byte at pos+1
        lower = s32(data[pos + 2 : pos + 6])
        upper = s32(data[pos + 6 : pos + 10])
        body_count = data[pos + 10]
        body: list[tuple[str, int, int]] = []
        bp = pos + 11
        for _ in range(body_count):
            op = data[bp]
            if op & 0x10:
                body.append(("op", op, 0))
                bp += 1
            else:
                operand = s32(data[bp + 1 : bp + 5])
                kind = "imm" if op == 0 else ("var" if op == 0x0c else f"op{op:#x}_skip")
                body.append((kind, op, operand))
                bp += 5
        formulas.append({
            "idx": fi,
            "size_byte": size_byte,
            "expected_total": size_byte + 2,
            "actual_total": bp - pos,
            "lower": lower,
            "upper": upper,
            "body_count": body_count,
            "body": body,
        })
        pos = bp
    return count, formulas


def evaluate(formula: dict) -> str | None:
    """상수만 있는 formula 면 평가, 아니면 None."""
    stack = []
    for kind, op, operand in formula["body"]:
        if kind == "imm":
            stack.append(operand)
        elif kind == "var":
            return None  # 변수 → 평가 불가
        elif kind == "op":
            if len(stack) < 2:
                return None
            b = stack.pop()
            a = stack.pop()
            try:
                if op == 0x11:
                    stack.append(a + b)
                elif op == 0x12:
                    stack.append(a - b)
                elif op == 0x13:
                    stack.append(a * b)
                elif op == 0x14:
                    stack.append(a // b if b else 0)
                elif op == 0x15:
                    stack.append(a % b if b else 0)
                elif op == 0x16:
                    stack.append(a ^ b)
            except Exception:
                return None
    if len(stack) != 1:
        return None
    val = max(formula["lower"], min(formula["upper"], stack[0]))
    return str(val)


def to_infix(formula: dict) -> str:
    """body 를 중위 표기식으로 변환 (가능하면)."""
    stack: list[str] = []
    OP_SYM = {0x11: "+", 0x12: "-", 0x13: "*", 0x14: "/", 0x15: "%", 0x16: "^"}
    for kind, op, operand in formula["body"]:
        if kind == "imm":
            stack.append(str(operand))
        elif kind == "var":
            stack.append(f"V[{operand}]")
        elif kind.startswith("op0x"):  # skipped operand
            stack.append("0")
        elif kind == "op":
            if len(stack) < 2:
                return "<malformed>"
            b = stack.pop()
            a = stack.pop()
            stack.append(f"({a}{OP_SYM.get(op, '?')}{b})")
    return stack[-1] if len(stack) == 1 else f"<stack={stack}>"


def format_body(body: list) -> str:
    parts: list[str] = []
    for kind, op, operand in body:
        if kind == "imm":
            parts.append(f"PUSH {operand}")
        elif kind == "var":
            parts.append(f"FETCH var[{operand}]")
        elif kind.startswith("op0x"):
            parts.append(f"SKIP op={op:#x}")
        elif kind == "op":
            parts.append(OPCODES.get(op, f"op{op:#x}"))
    return " ; ".join(parts)


def disasm_file(path: Path, name: str, id_offset: int) -> Iterator[str]:
    """ID 범위에 따른 base offset (calc_pl=0, calc_en=1000, calc_sk=2000)."""
    data = path.read_bytes()
    count, formulas = parse_file(data)
    yield f"# {name} — {count} formulas (file size {len(data)}B), id range {id_offset}..{id_offset + count - 1}"
    yield ""
    bytes_consumed = 3
    for f in formulas:
        infix = to_infix(f)
        const_eval = evaluate(f)
        eval_str = f"  ⇒ {const_eval}" if const_eval is not None else ""
        yield f"## id={id_offset + f['idx']} (idx={f['idx']})  bounds=[{f['lower']}, {f['upper']}]"
        yield f"   formula: clamp({infix}, {f['lower']}, {f['upper']}){eval_str}"
        yield f"   body[{f['body_count']}]: {format_body(f['body'])}"
        size_ok = f["expected_total"] == f["actual_total"]
        marker = "" if size_ok else f"  ⚠ size mismatch (header={f['expected_total']} actual={f['actual_total']})"
        yield f"   size: {f['actual_total']}B{marker}"
        yield ""
        bytes_consumed += f["actual_total"]
    yield f"# total bytes consumed: {bytes_consumed} / {len(data)}"


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    analysis = repo / "work" / "h5" / "analysis"
    out_path = analysis / "formulas_disasm.txt"
    files = [
        ("calc_pl_plain.bin", "calc_pl", 0),
        ("calc_en_plain.bin", "calc_en", 1000),
        ("calc_sk_plain.bin", "calc_sk", 2000),
    ]
    with out_path.open("w", encoding="utf-8") as fp:
        for fname, name, off in files:
            p = analysis / fname
            if not p.exists():
                fp.write(f"# missing: {p}\n\n")
                continue
            for line in disasm_file(p, name, off):
                fp.write(line + "\n")
            fp.write("\n\n")
    print(f"wrote {out_path}")
    # also print summary
    for fname, name, off in files:
        p = analysis / fname
        if p.exists():
            count, formulas = parse_file(p.read_bytes())
            mismatches = sum(1 for f in formulas if f["expected_total"] != f["actual_total"])
            print(f"  {name}: {count} formulas, {mismatches} size mismatches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
