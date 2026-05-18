"""Round 61: skill_dat (s4~s10) body 정밀 디코드.

각 skill body 구조 (byte 0 = category):

  Category 0 = 무기 마스터리 (passive 1-7, weapon damage tier up)
    +0  skill_category = 0
    +1  desc_len (0 = no description for tier 2-7)
    +2..+2+desc_len   EUC-KR description (only for tier 1)
    뒤따라 stat block (32B) — tier별 동일 패턴, 일부 byte 만 변화

  Category 1 = active 공격기
    +0  skill_category = 1
    +1  desc_len
    +2..+2+desc_len   EUC-KR description
    이후:
      +N   LE16 SP cost (예: 0x01f4 = 500, 0x0258 = 600)
      +N+2 LE16 cooldown / range
      +N+4 byte pad
      +N+5..+N+7  3 byte (요구레벨, ID, ?)
      +N+10..+N+11 LE16 damage_base (예: 0x14=20, 0x1e=30)
      +N+12..+N+13 LE16 damage_scale or duration
      ...

  Category 2 = active 버프
    +0  category = 2
    +1  desc_len
    동일하지만 damage 대신 bonus_type/value 쌍

  Category 3 = passive bonus
    +0  category = 3
    +1  desc_len
    여러 (bonus_type, bonus_value, ?, ?) pair
"""
import json
import struct
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


CATEGORY_NAMES = {0: "weapon_passive", 1: "active_attack", 2: "active_buff", 3: "passive_bonus"}


def parse_entry(data: bytes, pos: int) -> tuple[dict | None, int]:
    if pos + 3 > len(data):
        return None, pos
    size = data[pos]
    if size == 0:
        return None, pos
    nl = data[pos + 2]
    if nl == 0:
        return None, pos
    total = size + 2
    if pos + total > len(data) or total < 8:
        return None, pos
    name_bytes = data[pos + 3 : pos + 3 + nl]
    try:
        name = name_bytes.decode("cp949").rstrip("\x00")
    except UnicodeDecodeError:
        name = name_bytes.hex()
    body = data[pos + 3 + nl : pos + total]
    return {"pos": pos, "name": name, "body": body}, pos + total


def decode_body(body: bytes) -> dict:
    if len(body) < 3:
        return {"raw": body.hex(" ")}
    cat = body[0]
    desc_len = body[1]
    desc_end = 2 + desc_len
    if desc_end > len(body):
        desc_end = 2
        desc = ""
    else:
        desc_bytes = body[2:desc_end]
        try:
            desc = desc_bytes.decode("cp949").rstrip("\x00")
        except UnicodeDecodeError:
            desc = desc_bytes.hex()
    tail = body[desc_end:]

    out = {
        "category": cat,
        "category_name": CATEGORY_NAMES.get(cat, "?"),
        "desc": desc,
        "tail_len": len(tail),
        "tail_hex": tail.hex(" "),
    }

    # active attack / buff: SP cost @ tail+0, cooldown @ tail+2
    if cat in (1, 2) and len(tail) >= 4:
        out["sp_cost"] = struct.unpack_from("<H", tail, 0)[0]
        out["cooldown_or_range"] = struct.unpack_from("<H", tail, 2)[0]

    # damage_base / damage_scale 패턴 (offsets 좀 더 안정적인 위치):
    # tail end-22..end-21 = LE16 (대부분 damage_base 또는 stat bonus)
    if len(tail) >= 24:
        # primary effect values appear at tail[-22], tail[-21]
        out["effect_a"] = tail[-22] if len(tail) >= 22 else 0
        out["effect_b"] = tail[-21] if len(tail) >= 21 else 0

    # passive bonus pair (cat 3): tail[-13..-12] = (bonus_type, bonus_value)
    if cat == 3 and len(tail) >= 14:
        out["bonus_type"] = tail[-14] if len(tail) >= 14 else 0
        out["bonus_value"] = tail[-13] if len(tail) >= 13 else 0
        # Optional secondary
        if len(tail) >= 19:
            out["bonus2_type"] = tail[-9]
            out["bonus2_value"] = tail[-8]

    # last byte = rank/multiplier indicator (1,2,3,...)
    if tail:
        out["rank_or_level"] = tail[-1]
    return out


def main() -> None:
    EXT = Path("work/h3/extracted/skill")
    OUT = Path("work/h3/recon")
    OUT.mkdir(parents=True, exist_ok=True)

    results = {}
    for n in range(4, 11):
        fn = f"s{n}_dat"
        path = EXT / fn
        if not path.exists():
            continue
        data = path.read_bytes()
        entries = []
        pos = 0
        while True:
            e, npos = parse_entry(data, pos)
            if e is None:
                break
            decoded = decode_body(e["body"])
            entries.append({"pos": e["pos"], "name": e["name"], **decoded})
            pos = npos
        results[fn] = entries

        print(f"\n=== {fn} ({len(entries)} skills) ===")
        for i, e in enumerate(entries):
            cat = e.get("category_name", "?")
            desc = e.get("desc", "")[:36]
            extra = ""
            if "sp_cost" in e:
                extra += f" SP={e['sp_cost']:>4}"
            if "cooldown_or_range" in e:
                extra += f" CD/R={e['cooldown_or_range']:>4}"
            if "effect_a" in e:
                extra += f" ea/eb={e.get('effect_a',0):>3}/{e.get('effect_b',0):>3}"
            if "bonus_type" in e:
                extra += f" bonus={e['bonus_type']}/{e['bonus_value']}"
                if "bonus2_type" in e:
                    extra += f"+{e['bonus2_type']}/{e['bonus2_value']}"
            rank = e.get("rank_or_level", 0)
            print(f"  [{i:>2}] {e['name']:<10} cat={cat:<14} rank={rank}{extra}  desc={desc!r}")

    out_path = OUT / "skill_decoded.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")


if __name__ == "__main__":
    main()
