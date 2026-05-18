"""Round 61: dat/i0~i18 item body 정밀 디코드.

R60 발견: 17 평문 파일 × 480+ items, body 20B 또는 가변.

R61 hex 비교로 발견한 layout (장비류 20B 공통):

  +0..1  LE16   price (Gold cost) — monotonic per tier
  +2..3  pad
  +4     tier index (0,1,2,3,4,5,...)
  +5     color/variant (대개 0xff)
  +6..7  pad
  +8     required level — monotonic
  +9..11 pad
  +12..13 LE16  primary stat (DEF for armor, ATK for weapon)
  +14..15 LE16  secondary stat (sub-stat or zero)
  +16..19 trailing padding

i18_dat (소비) 별도 구조 — variable size:
  +0..1  LE16   price
  +2..3  pad
  +4     desc_len
  +5..   EUC-KR description
  +N..N+1  skill_id / effect_type
  +N+2..N+3  LE16 effect value (matches description's number)
"""
import json
import struct
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def parse_item(data: bytes, start: int) -> tuple[dict | None, int]:
    """Return (item_dict, next_pos) or (None, eof_pos) at end."""
    if start + 3 > len(data):
        return None, start
    size = data[start]
    if size == 0:
        return None, start
    nl = data[start + 2]
    if nl == 0 or size + 2 < 8:
        return None, start
    total = size + 2
    if start + total > len(data):
        return None, start
    name_bytes = data[start + 3 : start + 3 + nl]
    try:
        name = name_bytes.decode("cp949").rstrip("\x00")
    except UnicodeDecodeError:
        name = name_bytes.hex()
    body = data[start + 3 + nl : start + total]
    return {"pos": start, "name": name, "body": body}, start + total


def decode_equip_20B(body: bytes) -> dict:
    """20-byte body for equipment (armor/weapon/accessory)."""
    if len(body) < 20:
        return {"layout": "short", "raw": body.hex(" ")}
    return {
        "layout": "equip20",
        "price": struct.unpack_from("<H", body, 0)[0],
        "tier": body[4],
        "variant": body[5],
        "req_level": body[8],
        "stat_primary": struct.unpack_from("<H", body, 12)[0],
        "stat_secondary": struct.unpack_from("<H", body, 14)[0],
        "trailer": body[16:].hex(" "),
    }


def decode_consumable(body: bytes) -> dict:
    """Variable-size consumable (i18_dat): price + desc + effect.
       Also works for i13/i14/i17 (text-prefixed items)."""
    if len(body) < 6:
        return {"layout": "short", "raw": body.hex(" ")}
    price = struct.unpack_from("<H", body, 0)[0]
    desc_len = body[4]
    desc_end = 5 + desc_len
    if desc_end > len(body):
        return {"layout": "consumable_truncated", "price": price, "raw": body.hex(" ")}
    desc_bytes = body[5:desc_end]
    try:
        desc = desc_bytes.decode("cp949")
    except UnicodeDecodeError:
        desc = desc_bytes.hex()
    tail = body[desc_end:]
    effect_type = struct.unpack_from("<H", tail, 0)[0] if len(tail) >= 2 else 0
    effect_value = struct.unpack_from("<H", tail, 2)[0] if len(tail) >= 4 else 0
    extra = tail[4:].hex(" ") if len(tail) > 4 else ""
    return {
        "layout": "consumable",
        "price": price,
        "desc": desc,
        "effect_type": f"0x{effect_type:04x}",
        "effect_value": effect_value,
        "extra": extra,
    }


def decode_ring_18B(body: bytes) -> dict:
    """18-byte ring/accessory body (i12_dat).

       Pattern from raw hex:
         e8 03 00 00 | 00 00 | 01 00 | 00 00 | 02 00 00 00 | XX YY | 00 00
       +0..1  LE16 price (0x03e8=1000 default for rings)
       +2..3  pad
       +4..5  LE16 (always 0 — slot type?)
       +6..7  LE16 (always 1 — required level?)
       +8..9  pad
       +10..11 LE16 (always 2 — variant?)
       +12..13 pad
       +14    bonus_type (effect ID)
       +15    bonus_value (magnitude)
       +16..17 extra bonus (some rings have it)
    """
    if len(body) < 16:
        return {"layout": "short", "raw": body.hex(" ")}
    bonus_type = body[14]
    bonus_value = body[15]
    extra = body[16:].hex(" ")
    return {
        "layout": "ring18",
        "price": struct.unpack_from("<H", body, 0)[0],
        "f4_5": struct.unpack_from("<H", body, 4)[0],
        "f6_7": struct.unpack_from("<H", body, 6)[0],
        "f10_11": struct.unpack_from("<H", body, 10)[0],
        "bonus_type": bonus_type,
        "bonus_value": bonus_value,
        "extra": extra,
    }


def decode_enchant(body: bytes) -> dict:
    """i16_dat enchant option: variable size, uses similar prefix layout."""
    if len(body) < 6:
        return {"layout": "short", "raw": body.hex(" ")}
    price = struct.unpack_from("<H", body, 0)[0]
    desc_len = body[4]
    desc_end = 5 + desc_len
    if desc_end > len(body):
        return {"layout": "enchant_truncated", "price": price, "raw": body.hex(" ")}
    desc_bytes = body[5:desc_end]
    try:
        desc = desc_bytes.decode("cp949")
    except UnicodeDecodeError:
        desc = desc_bytes.hex()
    tail = body[desc_end:]
    return {
        "layout": "enchant",
        "price": price,
        "desc": desc,
        "tail": tail.hex(" "),
    }


# Category mapping (R60 + R61 refined)
CATEGORY = {
    0: "헬멧",   1: "갑옷",   2: "장갑",   3: "신발",
    4: "창",     5: "대검",   6: "단검",   7: "건",
    8: "라이플", 9: "다크석", 10: "홀리석", 11: "방패",
    12: "반지",  13: "패시브스크롤", 14: "조합재료",
    16: "enchant", 17: "퀘스트", 18: "소비",
}

# 카테고리별 layout 선택
def select_decoder(n: int, body: bytes):
    if n in (13, 14, 17, 18):
        return decode_consumable
    if n == 12:
        return decode_ring_18B
    if n == 16:
        return decode_enchant
    # 장비류 (헬멧/갑옷/장갑/신발/무기/방패/마법석)
    if len(body) >= 20:
        return decode_equip_20B
    return lambda b: {"layout": "short", "raw": b.hex(" ")}


def main() -> None:
    EXT = Path("work/h3/extracted/dat")
    OUT = Path("work/h3/recon")
    OUT.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    summary_rows = []

    for n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18]:
        fn = f"i{n}_dat"
        path = EXT / fn
        if not path.exists():
            continue
        data = path.read_bytes()
        items = []
        pos = 0
        while True:
            item, npos = parse_item(data, pos)
            if item is None:
                break
            body = item["body"]
            decoder = select_decoder(n, body)
            decoded = decoder(body)
            items.append({
                "pos": item["pos"], "name": item["name"], **decoded,
            })
            pos = npos

        cat = CATEGORY.get(n, "?")
        results[fn] = {"category": cat, "items": items}
        summary_rows.append((fn, cat, len(items)))

        print(f"\n=== {fn} ({cat}, {len(items)} items) ===")
        layout = items[0].get("layout", "?") if items else "?"
        if layout == "equip20":
            print(f"  {'name':<14} {'price':>7} tier var {'lvl':>3} {'stat1':>5} {'stat2':>5}  trailer")
            for it in items[:10]:
                print(f"  {it['name']:<14} {it['price']:>7} {it['tier']:>4} {it['variant']:>3} {it['req_level']:>3} "
                      f"{it['stat_primary']:>5} {it['stat_secondary']:>5}  {it['trailer']}")
            if len(items) > 10:
                print(f"  ... ({len(items) - 10} more)")
        elif layout == "consumable":
            print(f"  {'name':<14} {'price':>6} {'effect':<8} {'value':>6}  desc")
            for it in items[:10]:
                print(f"  {it['name']:<14} {it['price']:>6} {it['effect_type']:<8} {it['effect_value']:>6}  {it['desc']!r}")
            if len(items) > 10:
                print(f"  ... ({len(items) - 10} more)")
        elif layout == "ring18":
            print(f"  {'name':<14} {'price':>6} f4_5 f6_7 f10_11 bonus_type bonus_val  extra")
            for it in items[:10]:
                print(f"  {it['name']:<14} {it['price']:>6} {it['f4_5']:>4} {it['f6_7']:>4} {it['f10_11']:>6}    {it['bonus_type']:>4}      {it['bonus_value']:>4}  {it['extra']}")
            if len(items) > 10:
                print(f"  ... ({len(items) - 10} more)")
        elif layout == "enchant":
            print(f"  {'name':<14} {'price':>6}  desc  | tail")
            for it in items[:10]:
                print(f"  {it['name']:<14} {it['price']:>6}  {it['desc']!r:<60} | {it['tail']}")
            if len(items) > 10:
                print(f"  ... ({len(items) - 10} more)")
        else:
            for it in items[:5]:
                print(f"  {it['name']!r}: {it}")

    print(f"\n=== SUMMARY ===")
    for fn, cat, n in summary_rows:
        print(f"  {fn:<10} {cat:<10} {n} items")

    out_path = OUT / "item_decoded.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")


if __name__ == "__main__":
    main()
