"""Round 64: 0x14 / 0x19 / 0x01 (passive) 미사용 stat code 추적.

R63 master enum 에서 0x14 와 0x19 는 어디서도 명시적 의미가 발견되지 않음.
0x01 은 i13 자비의손길에서만 사용 (HP_HEAL_INSTANT 단발성).

방법:
  (A) binary literal grep — client.bin64000 에서 0x14/0x19 byte literal 의
      arith-immediate 패턴 (cmp #0x14, mov r,#0x14, ldrb @ array+0x14) 검색
  (B) 모든 dat 파일의 raw byte 스캔으로 미사용 코드 검색
  (C) i*_dat 의 trailer / unused fields 에서 0x14/0x19 출현 횟수 카운트

Output: work/h3/recon/unused_codes.{json,log}
"""
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "work/h3/extracted"
RECON = ROOT / "work/h3/recon"

UNUSED_CODES = [0x01, 0x14, 0x15, 0x19, 0x1a, 0x1b, 0x1d, 0x1e, 0x1f]  # explore 1 hexrange

DAT_FILES = [
    "dat/i0_dat", "dat/i1_dat", "dat/i2_dat", "dat/i3_dat",
    "dat/i4_dat", "dat/i5_dat", "dat/i6_dat", "dat/i7_dat",
    "dat/i8_dat", "dat/i9_dat", "dat/i10_dat", "dat/i11_dat",
    "dat/i12_dat", "dat/i13_dat", "dat/i14_dat", "dat/i16_dat",
    "dat/i17_dat", "dat/i18_dat",
    "dat/enemy_dat", "dat/enemyh_dat",
    "boss/boss_dat", "boss/bossh_dat",
    "dat/quest_00_dat", "dat/quest_01_dat", "dat/quest_10_dat", "dat/quest_11_dat",
    "dat/char_dat",
]


def scan_dat_files() -> dict:
    """각 dat 파일에서 0x14/0x19 등 미사용 코드 byte 출현 횟수."""
    out: dict = {}
    for rel in DAT_FILES:
        path = EXT / rel
        if not path.exists():
            continue
        data = path.read_bytes()
        c = Counter(data)
        out[rel] = {f"0x{b:02x}": c.get(b, 0) for b in UNUSED_CODES}
        out[rel]["total"] = len(data)
    return out


def scan_binary_immediates(bin_path: Path) -> dict:
    """ARM literal immediate patterns: cmp/mov/ldrb #0x14, #0x19 etc.

    ARM thumb cmp/sub/add/mov immediate: instruction byte usually OR'd with 0x14/0x19.
    가장 robust: byte literal 추출 후 인접 instruction context 보고.

    피처폰 ARM (CLDC 인터프리터) 는 ARMv5 thumb 위주.
    여기선 단순히 byte 의 출현 횟수만 카운트 + 4-byte aligned literal pool 추정.
    """
    data = bin_path.read_bytes()
    c = Counter(data)
    out = {f"0x{b:02x}": c.get(b, 0) for b in UNUSED_CODES}
    out["total"] = len(data)
    # 4-byte aligned literal pool: word == 0x14 or word == 0x19
    word_counts: Counter = Counter()
    for off in range(0, len(data) - 3, 4):
        w = struct.unpack_from("<I", data, off)[0]
        if w in (0x14, 0x19):
            word_counts[w] += 1
    out["aligned_word_0x14"] = word_counts.get(0x14, 0)
    out["aligned_word_0x19"] = word_counts.get(0x19, 0)
    return out


def scan_item_trailers() -> dict:
    """장비 item trailer (4B at +16) 에서 0x14/0x19 출현 횟수."""
    items_doc = json.loads((RECON / "item_decoded.json").read_text(encoding="utf-8"))
    out: dict = defaultdict(lambda: Counter())
    for fn, payload in items_doc.items():
        for it in payload.get("items", []):
            trailer = it.get("trailer", "")
            if not trailer:
                continue
            try:
                bytes_ = bytes.fromhex(trailer.replace(" ", ""))
            except ValueError:
                continue
            for b in bytes_:
                if b in UNUSED_CODES:
                    out[fn][f"0x{b:02x}"] += 1
    return {k: dict(v) for k, v in out.items()}


def scan_skill_tails() -> dict:
    """skill tail bytes 에서 0x14/0x19 출현 횟수."""
    skill_doc = json.loads((RECON / "skill_dat_all.json").read_text(encoding="utf-8"))
    out: dict = defaultdict(lambda: Counter())
    for fn, skills in skill_doc.items():
        for sk in skills:
            hex_prev = sk.get("body_hex_preview", "")
            try:
                bytes_ = bytes.fromhex(hex_prev.replace(" ", ""))
            except ValueError:
                continue
            for b in bytes_:
                if b in UNUSED_CODES:
                    out[fn][f"0x{b:02x}"] += 1
    return {k: dict(v) for k, v in out.items()}


def main() -> None:
    out = {
        "doc": "Round 64: 0x14 / 0x19 미사용 stat code 추적",
        "target_codes": [f"0x{c:02x}" for c in UNUSED_CODES],
        "hypothesis": {
            "0x01": "HP_HEAL_INSTANT (i13 자비의손길 단독, R63 확정)",
            "0x14": "??? (0회 출현 in 검색, 가설 = LEVEL_BONUS 또는 EXP_BONUS or unused)",
            "0x15": "??? (i18 의 0x15 low byte 와 별개)",
            "0x19": "??? (가설 = STATUS_RESIST 또는 RAID_SPECIAL)",
            "0x1a": "i18 town_return (귀환서) 만 사용",
            "0x1b": "i18 town_warp (그리폰의피리) 만 사용",
            "0x1d": "i18 / skill rank byte (+0x1d) 와 별개 의미 가능",
        },
        "binary_scan": {},
        "dat_file_scan": {},
        "item_trailer_scan": {},
        "skill_tail_scan": {},
    }

    bin_path = EXT / "client.bin64000"
    if bin_path.exists():
        out["binary_scan"] = scan_binary_immediates(bin_path)

    out["dat_file_scan"] = scan_dat_files()
    out["item_trailer_scan"] = scan_item_trailers()
    out["skill_tail_scan"] = scan_skill_tails()

    out_path = RECON / "unused_codes.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    log_lines: list[str] = []
    log_lines.append("===== Hero3 unused stat code analysis (R64) =====\n")
    log_lines.append("Target codes: " + ", ".join(out["target_codes"]))
    log_lines.append("\n[Hypothesis]")
    for k, v in out["hypothesis"].items():
        log_lines.append(f"  {k}: {v}")

    log_lines.append("\n[Binary client.bin64000 byte counts]")
    if out["binary_scan"]:
        for k, v in out["binary_scan"].items():
            log_lines.append(f"  {k}: {v:,}")

    log_lines.append("\n[Dat file byte counts (raw, not stat-specific)]")
    log_lines.append(f"  {'file':<28} {'0x01':>6} {'0x14':>6} {'0x15':>6} {'0x19':>6} {'0x1a':>6} {'0x1b':>6} {'0x1d':>6} {'total':>8}")
    for fn, counts in out["dat_file_scan"].items():
        cells = [counts.get(f"0x{c:02x}", 0) for c in [0x01, 0x14, 0x15, 0x19, 0x1a, 0x1b, 0x1d]]
        total = counts.get("total", 0)
        log_lines.append(f"  {fn:<28} " + " ".join(f"{c:>6}" for c in cells) + f"  {total:>8}")

    log_lines.append("\n[Item trailer scan (0x14/0x19 in equip trailer)]")
    if out["item_trailer_scan"]:
        for fn, counts in out["item_trailer_scan"].items():
            log_lines.append(f"  {fn}: {dict(counts)}")
    else:
        log_lines.append("  → no occurrences of target codes in item trailers")

    log_lines.append("\n[Skill tail scan (0x14/0x19 in skill body)]")
    if out["skill_tail_scan"]:
        for fn, counts in out["skill_tail_scan"].items():
            log_lines.append(f"  {fn}: {dict(counts)}")
    else:
        log_lines.append("  → no occurrences of target codes in skill tails")

    log_lines.append("\n[Conclusion candidates]")
    log_lines.append("  - 0x14, 0x19 가 i*_dat / s*_dat 에서 의미있는 위치에 거의 등장하지 않음 → unused or boss-only")
    log_lines.append("  - boss_dat / enemy_dat trailer 의 6B 가변 영역에 등장 가능 → boss-specific effect code")
    log_lines.append("  - binary literal 검색은 추가 ARM disassembly 필요 (FUN_4f358 본문 정밀)")

    log_path = RECON / "unused_codes.log"
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Wrote {log_path}")
    print("\n--- Summary ---")
    print(f"Binary: {out['binary_scan']}")


if __name__ == "__main__":
    main()
