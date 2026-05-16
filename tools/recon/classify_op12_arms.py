"""Classify the 47 cmp arms of opcode 0x12 (scn_op12_8fc20) into semantic buckets.

Round 38 / 2EA: EUC-KR (0x89/0x8f) + ASCII (';','I','2') + sentinel (0xff)
+ state range (0~0x12) + escape (0x1f/0x7f) + other.

Includes nearby context_getter sites (which task_struct fields are read near each arm).
"""
import json
from collections import Counter
from pathlib import Path


JSON_PATH = Path("work/h3/scn_op12_8fc20_disasm.json")


def bucket(imm: int) -> str:
    if imm in (0x89, 0x8F, 0xA0, 0xA1, 0xA2):
        return "EUC-KR lead byte (0x80~)"
    if imm in (0x3B, 0x49, 0x32, 0x47, 0x4E, 0x59, 0x52):  # ; I 2 G N Y R
        return "ASCII format token"
    if imm == 0xFF:
        return "sentinel (0xff)"
    if 0 <= imm <= 0x12:
        return "small state (0~0x12)"
    if imm in (0x1F, 0x7F):
        return "escape/control"
    if imm > 0x80:
        return "high byte (>0x80, non-EUC)"
    return "other"


def main() -> None:
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    arms = d.get("arms", [])
    bls = d.get("interesting_bls", [])

    # Per-arm bucketing
    by_bucket: dict[str, list[dict]] = {}
    for arm in arms:
        imm = arm.get("imm")
        if imm is None:
            continue
        b = bucket(imm)
        by_bucket.setdefault(b, []).append(arm)

    print(f"=== opcode 0x12 (0x8fc20~0x929e8, 11.4KB) — 47 arms 분류 ===\n")
    total = sum(len(v) for v in by_bucket.values())
    for b, items in sorted(by_bucket.items(), key=lambda x: -len(x[1])):
        print(f"[{len(items):2}/{total}] {b}")
        for a in items:
            addr = a.get("cmp_addr") or a.get("addr") or a.get("site") or "?"
            imm = a.get("imm")
            op = a.get("branch_kind") or a.get("op") or "?"
            target = a.get("branch_target") or a.get("target") or "?"
            print(f"     @{addr} cmp {a.get('cmp_reg','?')} #{imm} (0x{imm:02x}) -> {op} {target}")
        print()

    # context_getter calls — task_struct fields referenced
    print("=== 41 context_getter call sites — task_struct field distribution ===")
    ctx_calls = [b for b in bls if b.get("label") == "context_getter"]
    ctx_field_counter: Counter[str] = Counter()
    for c in ctx_calls:
        # r0_pcrel = pcrel literal addr where r0 value came from
        pcr = c.get("r0_pcrel")
        imm = c.get("r0_imm_hex")
        if imm:
            ctx_field_counter[f"imm {imm}"] += 1
        elif pcr:
            ctx_field_counter[f"pcrel @{pcr}"] += 1
        else:
            ctx_field_counter["other/unknown"] += 1
    for k, v in ctx_field_counter.most_common(20):
        print(f"  {v:3}x  {k}")

    # Map pcrel literals to actual referenced values
    print("\n=== pcrel literals near context_getter (task_struct field offsets) ===")
    pcrel = d.get("pcrel_literals", [])
    pcrel_by_site = {l["site"]: l["value"] for l in pcrel}
    for c in ctx_calls:
        pcr = c.get("r0_pcrel")
        if pcr and pcr in pcrel_by_site:
            val = pcrel_by_site[pcr]
            site = c.get("site", "?")
            print(f"  ctx@{site} r0 from pcrel @{pcr} value = {val}")

    # All distinct pcrel values - find task_struct field clusters
    print("\n=== distinct pcrel literal values in opcode 0x12 (top 20 by frequency) ===")
    val_counter: Counter[str] = Counter(l["value"] for l in pcrel)
    for val, cnt in val_counter.most_common(20):
        print(f"  {cnt:3}x  {val}")


if __name__ == "__main__":
    main()
