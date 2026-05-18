"""Round 60: skill/s4_dat ~ s10_dat (7 files) 일괄 파싱.

R59 에서 s4_dat (창수) 1개만 검증 완료. 이번 라운드에서 s5~s10 6개 추가.
parse_s4_dat 패턴 재사용:
  size_byte (1) + reserved (1) + name_len (1) + name(EUC-KR) + body
  total = size_byte + 2

10 playable class (리츠 5 + 케이 5) vs 발견된 s_dat 파일: s4~s10 = 7개.
s1~s3 없음 → 가설:
  (a) s1~s3 = 공통/기본 skill (실제 파일 없음, 코드 하드코드)
  (b) class 번호가 4부터 시작 (예: 0=리츠 기본, 1=케이 기본, 2/3=예약)
  (c) 1=리츠, 2=케이, 3=공통, 4~10 = 각 분기 클래스 (7 클래스)

각 파일 파싱 결과를 work/h3/recon/skill_dat_all.json 으로 dump.
"""
import json
import sys
from pathlib import Path

# Force UTF-8 stdout on Windows (default is cp949 which can't encode U+FFFD)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Reuse parse_s4_dat from sibling module
sys.path.insert(0, str(Path(__file__).parent))
from parse_char_npcg_s4_dat import parse_s4_dat


def main() -> None:
    EXT = Path("work/h3/extracted/skill")
    OUT = Path("work/h3/recon")
    OUT.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, list[dict]] = {}
    summary_rows: list[tuple[str, int, int, str]] = []

    for n in range(4, 11):
        fn = f"s{n}_dat"
        path = EXT / fn
        if not path.exists():
            print(f"  MISSING: {fn}")
            continue
        data = path.read_bytes()
        entries = parse_s4_dat(data)
        # Strip raw bytes for json dump
        clean = [{k: v for k, v in e.items() if k not in ("stats_bytes",)} for e in entries]
        all_results[fn] = clean

        # Class title = first entry's name (skill book title?)
        first_name = entries[0]["name"] if entries else "?"
        summary_rows.append((fn, len(data), len(entries), first_name))

        print(f"\n========== {fn} ({len(data)}B) ==========")
        print(f"Parsed {len(entries)} entries")
        for e in entries:
            print(f"  0x{e['pos']:03x} size={e['size']}  name={e['name']!r:<18}  body({e['body_len']}B): {e['desc_preview']!r}")

    # Summary table
    print(f"\n========== SUMMARY ==========")
    print(f"{'file':<10} {'bytes':>6} {'#entries':>9}  first_name (class title?)")
    print(f"{'-'*10} {'-'*6} {'-'*9}  {'-'*30}")
    for fn, sz, n, name in summary_rows:
        print(f"{fn:<10} {sz:>6} {n:>9}  {name!r}")

    # Dump JSON
    out_path = OUT / "skill_dat_all.json"
    out_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")


if __name__ == "__main__":
    main()
