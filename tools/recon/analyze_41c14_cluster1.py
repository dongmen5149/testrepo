"""Re-analyze FUN_00041c14 disasm for cluster #1 (0x9afc~0x9b3c) reader patterns.

Round 37 / 2DQ: cluster #1 의 실제 use 위치 + 주변 cmp/BL 패턴 파악."""
import json
from collections import Counter


def main() -> None:
    d = json.load(open("work/h3/record_disp_41c14_disasm.json", encoding="utf-8"))
    cluster1 = {0x9AFC, 0x9B00, 0x9B01, 0x9B06, 0x9B14, 0x9B1C, 0x9B3C, 0x9B04, 0x9B08, 0x9B0C, 0x9B10, 0x9B18, 0x9B20}
    pcrel = d.get("pcrel_literals", [])
    hits = [l for l in pcrel if int(l["value"], 16) in cluster1]
    print(f"cluster #1 sites in FUN_00041c14: {len(hits)}")
    site_addrs = []
    for h in hits[:30]:
        print(f"  ldr@{h['site']} -> {h['value']}")
        site_addrs.append(int(h["site"], 16) if isinstance(h["site"], str) else h["site"])
    print()
    print(f"Total instructions: {d.get('instructions', '?')}")
    cmp_arms = d.get("cmp_arms", [])
    print(f"Cmp arms: {len(cmp_arms)}")
    print("cmp arm imm distribution:")
    c = Counter(h.get("imm") for h in cmp_arms)
    for imm, cnt in c.most_common(20):
        print(f"  cmp {imm}: {cnt}x")
    print()
    bls = d.get("bl_sites", [])
    print(f"BL sites: {len(bls)}")
    bl_targets = Counter(b.get("target_label") or b.get("target") for b in bls)
    print("BL target distribution (top 20):")
    for t, n in bl_targets.most_common(20):
        print(f"  {t}: {n}x")


if __name__ == "__main__":
    main()
