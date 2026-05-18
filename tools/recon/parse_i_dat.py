"""Round 60: dat/i0_dat ~ i18_dat (19 files) 일괄 파싱.

각 파일은 size_byte + 00 + name_len + name(EUC-KR) + body 형식 (enemy_dat 와 동일).

i = 'item' 또는 'inventory' 가설. 19 카테고리 = 무기/방어구/소비/재료 등.

i0_dat header: 1b 00 06 b8 d3 b8 ae b6 (size=0x1b, name_len=6, EUC-KR name)
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from parse_char_npcg_s4_dat import parse_s4_dat


def main() -> None:
    EXT = Path("work/h3/extracted/dat")
    OUT = Path("work/h3/recon")
    OUT.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[dict]] = {}
    summary_rows: list[tuple[str, int, int, str]] = []

    for n in range(0, 19):
        fn = f"i{n}_dat"
        path = EXT / fn
        if not path.exists():
            print(f"  MISSING: {fn}")
            continue
        data = path.read_bytes()
        entries = parse_s4_dat(data)
        clean = [{k: v for k, v in e.items() if k != "stats_bytes"} for e in entries]
        all_results[fn] = clean

        first_name = entries[0]["name"] if entries else "?"
        summary_rows.append((fn, len(data), len(entries), first_name))

        print(f"\n========== {fn} ({len(data)}B) ==========")
        print(f"Parsed {len(entries)} entries")
        for e in entries[:5]:
            print(f"  0x{e['pos']:03x} size={e['size']}  name={e['name']!r:<18}  body({e['body_len']}B): {e['desc_preview']!r}")
        if len(entries) > 5:
            print(f"  ... ({len(entries) - 5} more)")

    print(f"\n\n========== SUMMARY ==========")
    print(f"{'file':<10} {'bytes':>6} {'#entries':>9}  first_name (category title?)")
    print(f"{'-'*10} {'-'*6} {'-'*9}  {'-'*30}")
    for fn, sz, n, name in summary_rows:
        print(f"{fn:<10} {sz:>6} {n:>9}  {name!r}")

    out_path = OUT / "i_dat_all.json"
    out_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")


if __name__ == "__main__":
    main()
