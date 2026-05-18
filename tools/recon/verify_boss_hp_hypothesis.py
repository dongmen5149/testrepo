"""Round 60: boss_dat / bossh_dat 의 HP 필드 위치를 정밀 검증.

R58 가설: byte 0x08..0x0a (stat block 내) = 24-bit BE HP.
실제 데이터로 검증 — Ritz boss 6 entries (lvl 14/24/32/51/56/60) HP scaling 확인.

각 byte 위치를 16-bit BE, 16-bit LE, 24-bit BE 로 모두 해석해서
"level 과 가장 잘 상관되는" 위치를 찾는다.
"""
import struct
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from parse_enemy_dat import parse_entries


def hex_to_int_be16(b: bytes, off: int) -> int:
    return (b[off] << 8) | b[off + 1]

def hex_to_int_le16(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8)

def hex_to_int_be24(b: bytes, off: int) -> int:
    return (b[off] << 16) | (b[off + 1] << 8) | b[off + 2]

def hex_to_int_le24(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8) | (b[off + 2] << 16)


def main() -> None:
    paths = [Path("work/h3/extracted/boss/boss_dat"),
             Path("work/h3/extracted/boss/bossh_dat")]

    # Collect Ritz entries (first 4 normal + first 4 hard).
    # Entries follow ordering: ritz1, ritz2, ritz3, ritz+kei pair, kei1, kei2, kei3, kei(pair),
    # then misc bosses.
    ritz_entries = []
    for path in paths:
        data = path.read_bytes()
        entries = parse_entries(data)
        # First 3 ritz, then mel(pair=entry3), then 3 kei, then kei-pair (entry7)
        # entry 0,1,2 = ritz lvl14/24/32  (and entry 4,5,6 = kei lvl14/24/32 since they share lvls)
        for idx in [0, 1, 2]:
            if idx < len(entries):
                ritz_entries.append((path.stem, idx, entries[idx]))

    print(f"\n===== Ritz HP scaling test (lvl 14→24→32→51→56→60) =====\n")
    print(f"{'file':<12} {'idx':>3} {'lvl':>3}  byte dump (19B stat block)")
    print("-" * 100)
    for src, idx, e in ritz_entries:
        b = e["stats_bytes"]
        print(f"{src:<12} {idx:>3} {b[0]:>3}  {' '.join(f'{x:02x}' for x in b)}")

    # For each byte offset (0..16), compute candidate values and check monotonicity
    print(f"\n===== HP location hunt: candidate offsets for ritz monotonic scaling =====\n")
    levels = [e[2]["stats_bytes"][0] for e in ritz_entries]
    print(f"Levels (ritz×3 normal + ritz×3 hard): {levels}")

    print(f"\n{'off':>4}  {'BE16':<30}  {'LE16':<30}  {'BE24':<22}")
    for off in range(0, 17):
        be16_vals = [hex_to_int_be16(e[2]["stats_bytes"], off) for e in ritz_entries]
        le16_vals = [hex_to_int_le16(e[2]["stats_bytes"], off) for e in ritz_entries]
        be24_vals = []
        for e in ritz_entries:
            b = e[2]["stats_bytes"]
            if off + 2 < len(b):
                be24_vals.append(hex_to_int_be24(b, off))
            else:
                be24_vals.append(-1)
        be16_str = ",".join(str(v) for v in be16_vals)
        le16_str = ",".join(str(v) for v in le16_vals)
        be24_str = ",".join(str(v) for v in be24_vals)
        # Mark monotonic increasing
        mono_be16 = all(be16_vals[i] <= be16_vals[i+1] for i in range(len(be16_vals)-1))
        mono_le16 = all(le16_vals[i] <= le16_vals[i+1] for i in range(len(le16_vals)-1))
        mono_be24 = all(be24_vals[i] <= be24_vals[i+1] for i in range(len(be24_vals)-1)) if all(v >= 0 for v in be24_vals) else False
        m1 = "✓" if mono_be16 else " "
        m2 = "✓" if mono_le16 else " "
        m3 = "✓" if mono_be24 else " "
        print(f"  +{off:02x}  {m1} {be16_str:<28}  {m2} {le16_str:<28}  {m3} {be24_str:<20}")

    # Apply discovered HP location to all 15 boss entries (normal + hard)
    print(f"\n\n===== Apply best candidate to ALL bosses =====")
    for path in paths:
        data = path.read_bytes()
        entries = parse_entries(data)
        print(f"\n--- {path.name} ({len(entries)} entries) ---")
        print(f"{'idx':>3} {'name':<14} {'lvl':>3}  raw(+10..+11)  raw(+12..+13)  raw(+8..+9)+(+10)  HP_BE16(+10)")
        for i, e in enumerate(entries):
            b = e["stats_bytes"]
            be10 = hex_to_int_be16(b, 10)
            be12 = hex_to_int_be16(b, 12)
            le10 = hex_to_int_le16(b, 10)
            try:
                name = e["name"][:14]
            except Exception:
                name = "?"
            print(f"{i:>3} {name:<14} {b[0]:>3}  BE={be10:>6}  BE12={be12:>6}  LE={le10:>6}")


if __name__ == "__main__":
    main()
