"""Round 65: equip trailer 177 case 의 0x14/0x19 분포 재집계.

R62 발견: 346 equip 중 177 (51%) 가 trailer 4B 에 (bonus_type, value) × 2 보유.
R64 발견: 0x14/0x19 가 i*_dat stat enum 에서는 부재 / equip trailer 에는 출현.

가설: 0x14/0x19 = **boss-only stat code** (boss drop equip 의 trailer 에 집중 출현).

방법:
  1. 모든 equip item 의 4B trailer parse — (bt1, v1, bt2, v2)
  2. rarity prefix 별 bt1/bt2 빈도 표 — boss_drop ({...) vs magic (|...) vs epic ($...) 비교
  3. 0x14 / 0x19 / 0x01 (희귀) 출현 case 모두 dump
  4. weapon (i4-i10) vs armor (i0-i3, i11) 차이

Output: work/h3/recon/trailer_bonus.{json,log}
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "work/h3/recon"


# R63 master stat enum (24 codes)
STAT_NAME = {
    0x00: "ATT1_BASE", 0x01: "HP_HEAL_INSTANT", 0x02: "HP_MAX", 0x03: "HP_REGEN",
    0x04: "SP_MAX", 0x05: "ATT1", 0x06: "ATT2", 0x07: "P_DEF", 0x08: "M_DEF",
    0x09: "ACC", 0x0a: "DOD", 0x0b: "BLOCK", 0x0c: "CRI_RATE", 0x0d: "CRI_DEF",
    0x0e: "SP_COST_REDUCE", 0x0f: "SP_REGEN", 0x10: "HP_DRAIN", 0x11: "CD_REDUCE",
    0x12: "SHIELD_PIERCE", 0x14: "?? (R64 미식별, equip trailer 전용 후보)",
    0x16: "BUFF_REMOVE", 0x17: "CURE_STATUS",
    0x19: "?? (R64 미식별, equip trailer 전용 후보)", 0x1c: "REVIVE",
}

RARITY = {"|": "magic", "'": "legendary", "$": "epic", "{": "boss_drop",
          "@": "endgame", "}": "quest_reward"}

EQUIP_FILES = [f"i{n}_dat" for n in range(12)]  # i0~i11 (12 categories)

# slot grouping (R62 카테고리)
ARMOR_FILES = ["i0_dat", "i1_dat", "i2_dat", "i3_dat", "i11_dat"]  # 헬멧/갑옷/장갑/신발/방패
WEAPON_FILES = ["i4_dat", "i5_dat", "i6_dat", "i7_dat", "i8_dat", "i9_dat", "i10_dat"]


def detect_rarity(name: str) -> str:
    if not name:
        return "normal"
    return RARITY.get(name[0], "normal")


def main() -> None:
    d = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))

    # parse all equip20 trailers
    rows = []
    for fn in EQUIP_FILES:
        if fn not in d:
            continue
        for it in d[fn].get("items", []):
            if it.get("layout") != "equip20":
                continue
            tr = it.get("trailer", "")
            if not tr:
                continue
            try:
                b = bytes.fromhex(tr.replace(" ", ""))
            except ValueError:
                continue
            if len(b) < 4:
                b = b + bytes(4 - len(b))
            bt1, v1, bt2, v2 = b[0], b[1], b[2], b[3]
            rows.append({
                "file": fn,
                "slot": "weapon" if fn in WEAPON_FILES else "armor",
                "name": it.get("name", ""),
                "rarity": detect_rarity(it.get("name", "")),
                "bt1": bt1, "v1": v1, "bt2": bt2, "v2": v2,
                "trailer_hex": tr,
                "tier": it.get("tier", 0),
                "req_level": it.get("req_level", 0),
            })

    total = len(rows)
    nz = [r for r in rows if r["bt1"] or r["v1"] or r["bt2"] or r["v2"]]
    has_pair2 = [r for r in nz if r["bt2"] != 0]
    has_pair1 = [r for r in nz if r["bt1"] != 0]

    # 1. bt1 / bt2 distribution by rarity
    rarity_x_bt1: dict = defaultdict(Counter)
    rarity_x_bt2: dict = defaultdict(Counter)
    for r in nz:
        if r["bt1"]:
            rarity_x_bt1[r["rarity"]][r["bt1"]] += 1
        if r["bt2"]:
            rarity_x_bt2[r["rarity"]][r["bt2"]] += 1

    # 2. slot × bt distribution
    slot_x_bt1: dict = defaultdict(Counter)
    slot_x_bt2: dict = defaultdict(Counter)
    for r in nz:
        if r["bt1"]:
            slot_x_bt1[r["slot"]][r["bt1"]] += 1
        if r["bt2"]:
            slot_x_bt2[r["slot"]][r["bt2"]] += 1

    # 3. 0x14 / 0x19 / 0x01 / 0x03 / 0x04 / 0x08 / 0x09 / 0x0b / 0x10 / 0x11 specific cases
    target_codes = [0x01, 0x03, 0x04, 0x08, 0x09, 0x0b, 0x10, 0x11, 0x14, 0x15, 0x19, 0x1a, 0x1b, 0x1d]
    code_cases: dict = defaultdict(list)
    for r in nz:
        for c in target_codes:
            if r["bt1"] == c:
                code_cases[f"0x{c:02x} (as bt1)"].append({
                    "file": r["file"], "name": r["name"], "rarity": r["rarity"],
                    "trailer": r["trailer_hex"], "tier": r["tier"]
                })
            if r["bt2"] == c:
                code_cases[f"0x{c:02x} (as bt2)"].append({
                    "file": r["file"], "name": r["name"], "rarity": r["rarity"],
                    "trailer": r["trailer_hex"], "tier": r["tier"]
                })

    # 4. boss_drop 전용 vs 일반 비교
    boss_drop = [r for r in nz if r["rarity"] == "boss_drop"]
    epic = [r for r in nz if r["rarity"] == "epic"]
    magic = [r for r in nz if r["rarity"] == "magic"]
    endgame = [r for r in nz if r["rarity"] == "endgame"]
    boss_drop_codes = Counter(r["bt1"] for r in boss_drop if r["bt1"]) + Counter(r["bt2"] for r in boss_drop if r["bt2"])
    epic_codes = Counter(r["bt1"] for r in epic if r["bt1"]) + Counter(r["bt2"] for r in epic if r["bt2"])
    magic_codes = Counter(r["bt1"] for r in magic if r["bt1"]) + Counter(r["bt2"] for r in magic if r["bt2"])
    endgame_codes = Counter(r["bt1"] for r in endgame if r["bt1"]) + Counter(r["bt2"] for r in endgame if r["bt2"])

    out = {
        "doc": "Round 65: equip trailer bonus distribution by rarity (boss-only stat 검증)",
        "summary": {
            "total_equip20": total,
            "nonzero_trailer": len(nz),
            "ratio": f"{len(nz)/total*100:.1f}%",
            "pair1_count": len(has_pair1),
            "pair2_count": len(has_pair2),
        },
        "rarity_x_bt1": {r: {f"0x{k:02x}": v for k, v in c.items()} for r, c in rarity_x_bt1.items()},
        "rarity_x_bt2": {r: {f"0x{k:02x}": v for k, v in c.items()} for r, c in rarity_x_bt2.items()},
        "slot_x_bt1": {s: {f"0x{k:02x}": v for k, v in c.items()} for s, c in slot_x_bt1.items()},
        "slot_x_bt2": {s: {f"0x{k:02x}": v for k, v in c.items()} for s, c in slot_x_bt2.items()},
        "target_code_cases": code_cases,
        "rarity_code_distribution": {
            "boss_drop": {f"0x{k:02x}": v for k, v in sorted(boss_drop_codes.items())},
            "epic":      {f"0x{k:02x}": v for k, v in sorted(epic_codes.items())},
            "magic":     {f"0x{k:02x}": v for k, v in sorted(magic_codes.items())},
            "endgame":   {f"0x{k:02x}": v for k, v in sorted(endgame_codes.items())},
        },
    }

    out_path = RECON / "trailer_bonus.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    # log
    log_lines: list[str] = []
    log_lines.append("===== Hero3 equip trailer bonus distribution (R65) =====\n")
    log_lines.append(f"Total equip20 items: {total}")
    log_lines.append(f"Non-zero trailers:    {len(nz)} ({len(nz)/total*100:.1f}%)")
    log_lines.append(f"  has bt1:            {len(has_pair1)}")
    log_lines.append(f"  has bt2 (paired):   {len(has_pair2)}")

    log_lines.append("\n[Rarity × bt1/bt2 cross-tab]")
    log_lines.append(f"\n  {'rarity':<14} → bt1 distribution (top 8)")
    for r, c in rarity_x_bt1.items():
        items = sorted(c.items(), key=lambda x: -x[1])[:8]
        cell = ", ".join(f"0x{k:02x}({STAT_NAME.get(k,'?')[:10]})={v}" for k, v in items)
        log_lines.append(f"  {r:<14} {cell}")
    log_lines.append(f"\n  {'rarity':<14} → bt2 distribution (top 8)")
    for r, c in rarity_x_bt2.items():
        items = sorted(c.items(), key=lambda x: -x[1])[:8]
        cell = ", ".join(f"0x{k:02x}({STAT_NAME.get(k,'?')[:10]})={v}" for k, v in items)
        log_lines.append(f"  {r:<14} {cell}")

    log_lines.append("\n[Slot × bt1 cross-tab]")
    for s, c in slot_x_bt1.items():
        items = sorted(c.items(), key=lambda x: -x[1])
        cell = ", ".join(f"0x{k:02x}={v}" for k, v in items)
        log_lines.append(f"  {s:<8} {cell}")
    log_lines.append("\n[Slot × bt2 cross-tab]")
    for s, c in slot_x_bt2.items():
        items = sorted(c.items(), key=lambda x: -x[1])
        cell = ", ".join(f"0x{k:02x}={v}" for k, v in items)
        log_lines.append(f"  {s:<8} {cell}")

    log_lines.append("\n[★ Target codes (R63 미식별 + R62 unmapped) — case list]")
    for code_label in sorted(code_cases.keys()):
        cases = code_cases[code_label]
        log_lines.append(f"\n  {code_label}: {len(cases)} cases")
        for cs in cases[:15]:
            log_lines.append(f"    {cs['file']:<8} {cs['rarity']:<12} {cs['name'][:18]:<18} tier={cs['tier']} trailer={cs['trailer']}")
        if len(cases) > 15:
            log_lines.append(f"    ... ({len(cases)-15} more)")

    log_lines.append("\n[Rarity 별 master code distribution (bt1+bt2 합산)]")
    for rar in ["boss_drop", "epic", "magic", "endgame"]:
        cd = out["rarity_code_distribution"][rar]
        log_lines.append(f"\n  {rar}:")
        for k, v in cd.items():
            log_lines.append(f"    {k} ({STAT_NAME.get(int(k,16),'?'):<22}) = {v}")

    log_path = RECON / "trailer_bonus.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print(f"\n--- Top findings ---")
    print(f"  Total: {total}, Non-zero: {len(nz)} ({len(nz)/total*100:.1f}%)")
    print(f"  Target code occurrences (R63 미식별 0x14/0x19 + R62 unmapped):")
    for lbl in sorted(code_cases.keys()):
        print(f"    {lbl}: {len(code_cases[lbl])}")


if __name__ == "__main__":
    main()
