"""c_csv_buildup.json 의 entry type → 한글 stat label 사전 추출.

각 record 의 extra_hex 형식 (확인됨):
  byte 0..1: ffff (sentinel)
  byte 2   : effect type (1B) — buildup csv 자체 인덱싱
  byte 3   : sub category (0x28/0x29/0x2a — entity 종류 분류로 추정)
  byte 4..5: param value (LE u16)
  byte 6..  : 추가 entries (option 구성 시)

기능:
  1. 모든 entry decode → (csv_type, sub, val, kr_label) tsv.
  2. csv_type 별 unique 한글 라벨 사전 추출 (다중 record 공유 시 첫 라벨 사용).
  3. ApplyBuildupEffect entry table 과 매핑:
       buildup csv type N → ApplyBuildupEffect 호출 시 r1 = N+1
       (csv type 0x01 = 근력 → ApplyBuildupEffect type 2 = V[118] str bonus)

산출:
  work/h5/analysis/buildup_decoded.tsv      (record_idx, name, type, sub, val)
  work/h5/analysis/buildup_stat_labels.tsv  (csv_type → kr_label dict)
"""
from __future__ import annotations
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_JSON = ROOT / "apps/hero5-godot/assets/gamedata/c_csv_buildup.json"
OUT_RECORDS = ROOT / "work/h5/analysis/buildup_decoded.tsv"
OUT_LABELS = ROOT / "work/h5/analysis/buildup_stat_labels.tsv"


def parse_record(hex_s: str) -> list[tuple[int, int, int]]:
    """extra_hex 의 모든 (type, sub, val) entries 추출."""
    bs = bytes.fromhex(hex_s)
    entries = []
    # ffff sentinel skip (byte 0..1)
    if len(bs) < 6:
        return entries
    if bs[:2] == b"\xff\xff":
        bs = bs[2:]
    # 4 byte 단위로 읽기 (type, sub, val_lo, val_hi)
    for i in range(0, len(bs) - 3, 4):
        type_b = bs[i]
        sub = bs[i + 1]
        val = bs[i + 2] | (bs[i + 3] << 8)
        # sentinel zero 가 padding 이면 stop
        if type_b == 0 and sub == 0 and val == 0:
            continue
        entries.append((type_b, sub, val))
    return entries


def main() -> int:
    data = json.loads(CSV_JSON.read_text(encoding="utf-8"))
    records = data["records"]

    OUT_RECORDS.parent.mkdir(parents=True, exist_ok=True)

    # 1) 모든 entry dump
    rows = []
    for idx, rec in enumerate(records):
        name = rec["name"]
        for type_b, sub, val in parse_record(rec["extra_hex"]):
            rows.append((idx, name, type_b, sub, val))

    with OUT_RECORDS.open("w", encoding="utf-8") as f:
        f.write("rec_idx\tname\ttype\tsub\tval\n")
        for r_idx, name, t, sub, val in rows:
            f.write(f"{r_idx}\t{name}\t0x{t:02x}\t0x{sub:02x}\t{val}\n")

    print(f"[+] {OUT_RECORDS} ({len(rows)} entries)")

    # 2) csv_type 별 unique 라벨 — 단일 entry record 만 (다중 entry 는 복합 효과)
    # name 에서 stat label 부분만 추출 (e.g. "근력+#1" → "근력")
    LABEL_RE = re.compile(r"^([^+#]+)")

    # type → list of names 수집
    type_names: dict[int, list[str]] = {}
    for idx, rec in enumerate(records):
        entries = parse_record(rec["extra_hex"])
        if len(entries) == 1:
            t, sub, val = entries[0]
            m = LABEL_RE.match(rec["name"])
            label = m.group(1) if m else rec["name"]
            type_names.setdefault((t, sub), []).append((rec["name"], label, val))

    with OUT_LABELS.open("w", encoding="utf-8") as f:
        f.write("type\tsub\tcanonical_label\tall_names\n")
        labels_by_type: dict[int, str] = {}
        for (t, sub), names in sorted(type_names.items()):
            # canonical = 첫 번째 단순 라벨
            canonical = names[0][1]
            f.write(f"0x{t:02x}\t0x{sub:02x}\t{canonical}\t{' | '.join(n[0] for n in names[:5])}\n")
            if sub == 0x29:  # main effect category
                labels_by_type[t] = canonical

    print(f"[+] {OUT_LABELS}")

    # 3) ApplyBuildupEffect entry mapping (csv type N → AB type N+1)
    print()
    print("== buildup csv type → ApplyBuildupEffect type 매핑 ==")
    print("(csv type N → AB type N+1, jumptable idx = N)")
    print()
    print(f"{'csv':>5}  {'ABE':>5}  {'V slot':>10}  {'kr label':<20}  {'cache offset'}")
    print("-" * 70)
    # ApplyBuildupEffect entry (Round 9 추출)
    abe_table = {
        2: ("V[118]", "0x298", "bonus_str"),
        3: ("V[119]", "0x29a", "bonus_dex"),
        4: ("V[120]", "0x29c", "bonus_?"),
        5: ("V[121]", "0x29e", "bonus_?"),
        10: ("V[128]", "0x2ac", "atk_percent"),
        11: ("V[129]", "0x2ae", "secondary_bonus_1"),
        12: ("V[130]", "0x2b0", "secondary_bonus_2"),
        13: ("V[131]", "0x2b2", "secondary_bonus_3"),
        14: ("V[132]", "0x2b4", "secondary_bonus_4"),
        15: ("V[133]", "0x2b6", "secondary_bonus_5"),
        30: ("V[122]", "0x2a0", "buff_slot_1"),
        31: ("V[123]", "0x2a2", "buff_slot_2"),
        32: ("V[124]", "0x2a4", "buff_slot_3"),
        34: ("V[125]", "0x2a6", "buff_slot_4"),
        36: ("V[126]", "0x2a8", "buff_slot_5"),
        38: ("V[127]", "0x2aa", "def_reduction%"),
    }
    for csv_t, label in sorted(labels_by_type.items()):
        abe_t = csv_t + 1
        if abe_t in abe_table:
            v, off, note = abe_table[abe_t]
            print(f"  0x{csv_t:02x}  {abe_t:>5}  {v:>10}  {label[:20]:<20}  {off} ({note})")
        else:
            # not mapped → ApplyBuildupEffect 의 다른 dispatch (item bonus 등)
            print(f"  0x{csv_t:02x}  {abe_t:>5}  {'-':>10}  {label[:20]:<20}  (ABE default 또는 별도 dispatch)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
