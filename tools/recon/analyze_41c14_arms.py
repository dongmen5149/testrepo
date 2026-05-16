"""Inspect FUN_00041c14 cmp arms + show neighbor cluster #1 ldr context.

Round 37 / 2DQ deeper analysis."""
import json
from collections import Counter


def main() -> None:
    d = json.load(open("work/h3/record_disp_41c14_disasm.json", encoding="utf-8"))
    cluster1 = {0x9AFC, 0x9B00, 0x9B01, 0x9B04, 0x9B06, 0x9B08, 0x9B0C,
                0x9B10, 0x9B14, 0x9B18, 0x9B1C, 0x9B20, 0x9B3C}
    arms = d["arms"]
    pcrel = d["pcrel_literals"]
    cluster_sites = [int(l["site"], 16) for l in pcrel if int(l["value"], 16) in cluster1]
    cluster_sites_set = set(cluster_sites)

    print(f"=== FUN_00041c14 arms ({len(arms)} total) ===")
    for i, arm in enumerate(arms):
        site = arm.get("addr", arm.get("site", "?"))
        imm = arm.get("imm")
        op = arm.get("op") or arm.get("branch") or "?"
        target = arm.get("target", "?")
        print(f"  [{i:2}] @{site}: cmp #{imm} -> {op} {target}")

    print()
    print(f"=== cluster #1 LDR sites ({len(cluster_sites)} total) ===")
    for s in cluster_sites:
        # Find closest arm (within 32 instr = ~64 bytes either side)
        nearby = [a for a in arms if abs(int(a.get("addr","0x0"),16) - s) < 0x80]
        ctx = ", ".join(f"@{a.get('addr','?')}cmp#{a.get('imm','?')}" for a in nearby[:4])
        val = next((l["value"] for l in pcrel if int(l["site"], 16) == s), "?")
        print(f"  ldr@0x{s:08x} -> {val}  | nearby arms: {ctx}")

    print()
    print(f"=== interesting BLs ===")
    for b in d["interesting_bls"]:
        print(f"  {b}")


if __name__ == "__main__":
    main()
