"""Round 74 Phase A — Hero3 R73 DES 평문 8파일 정밀 파서.

Input  : work/h3/decrypted/*.0EP@KO91.plain (R73 산출)
Output : work/h3/recon/h3_dat_catalog.json + sibling per-file JSONs

R73 발견: 모든 DES 평문이 leading 16B "salt/IV" header 로 시작.
        진짜 payload 는 offset 16 부터 시작.

파일별 entry 구조 (R74 분석):

  i15_dat   (7400B = 16 + 7384 payload)
    entry = id(1) flag(1) nlen(1) name(nlen, '|' prefix) extra(4) body(text) term(3='0f ff 00')

  drop_dat  (3080B = 16 + 3064 payload)
    entry = 16 또는 17 bytes data + sep(2='11 00')
    가변 길이 enemy drop record

  smith_dat (896B = 16 + 880 payload, 11B stride)
    80 entries × 11B = (?,?,?,?,?,?,?,?,?,?,?). i14 조합재료 ↔ 결과물

  shop_dat  (72B = 16 + 50 payload + 6 trailer)
    5 entries × 10B = item ID set per NPC/region

  getitem_dat (400B = 16 + 384 payload, 4B stride)
    96 entries × 4B = (type, ?, slot, id) — fixed drop / quest reward

  des_dat 등은 알고리즘 테이블 (R57 처리됨, 본 스크립트 제외).
"""
from __future__ import annotations
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEC = ROOT / "work" / "h3" / "decrypted"
OUT = ROOT / "work" / "h3" / "recon"
OUT.mkdir(parents=True, exist_ok=True)

SALT = 16  # leading DES salt/IV bytes (R73 finding)


def euc_kr_decode(b: bytes) -> str:
    """EUC-KR bytes → Python str (errors=replace)."""
    try:
        return b.decode("cp949", errors="replace")
    except Exception:
        return b.hex(" ")


# ─── i15_dat: master shop catalog ─────────────────────────────────────────

def parse_i15(data: bytes) -> dict[str, Any]:
    """i15_dat = master item description catalog.

    각 entry 의 name 은 '|' (0x7c) + EUC-KR text 로 시작.
    nlen byte (= name 의 '|' 포함 길이) 는 '|' 바로 앞 byte.
    entry 경계 = 인접한 '|'+EUC-KR positions 의 중간.

    구조 (가설, name marker 기준):
        ...header(N) nlen('|' 포함) | name(EUC-KR, nlen-1 B) extra(4) body... ...
    """
    # find all '|'+EUC-KR markers
    marks: list[int] = []
    for i in range(SALT, len(data) - 2):
        if data[i] == 0x7c and 0xa1 <= data[i+1] <= 0xfe and 0xa1 <= data[i+2] <= 0xfe:
            marks.append(i)

    entries: list[dict] = []
    for idx, p in enumerate(marks):
        nlen = data[p - 1]  # name length incl. '|'
        if nlen < 3 or nlen > 60 or p + nlen > len(data):
            continue
        name_raw = data[p+1 : p + nlen]  # skip '|'
        name = euc_kr_decode(name_raw).strip("\x00")

        # header bytes (everything between previous entry-end and this nlen byte)
        prev_end = marks[idx-1] + 1 if idx > 0 else SALT
        # find next entry start (next marker's header begins ~3-5B before its '|')
        if idx + 1 < len(marks):
            next_hdr_guess = marks[idx+1] - 1 - 6  # rough heuristic
            entry_end = next_hdr_guess
        else:
            entry_end = len(data)

        # header = bytes from prev_end to (p - 1) inclusive => to before nlen
        header = data[prev_end : p - 1]
        body_start = p + nlen
        body_raw = data[body_start : entry_end]
        body = euc_kr_decode(body_raw).strip("\x00").strip()

        entries.append({
            "marker_offset": p,
            "header_hex":    header.hex(" "),
            "nlen":          nlen,
            "name":          name,
            "body":          body,
        })

    return {
        "file":      "i15_dat",
        "size":      len(data),
        "salt_hex":  data[:SALT].hex(" "),
        "count":     len(entries),
        "entries":   entries,
    }


# ─── drop_dat: enemy drop table ────────────────────────────────────────────

def parse_drop(data: bytes, name: str) -> dict[str, Any]:
    """drop_dat = variable-length enemy drop records separated by '11 00'.

    R73 finding: first 16B = DES salt. payload 시작 직후 첫 '11 00' 은 separator-as-prefix
    (즉 entries 가 '11 00' 으로 시작하는 게 아니라 '11 00' 으로 끝남).
    """
    # split payload on '11 00'; drop empty fragments
    payload = data[SALT:]
    raw = payload.split(b"\x11\x00")
    records: list[dict] = []
    offset = SALT
    for frag in raw:
        if not frag:
            offset += 2
            continue
        records.append({
            "offset":   offset,
            "size":     len(frag),
            "hex":      frag.hex(" "),
            "bytes":    list(frag),
        })
        offset += len(frag) + 2

    # size 분포
    size_hist: dict[int, int] = {}
    for r in records:
        size_hist[r["size"]] = size_hist.get(r["size"], 0) + 1

    return {
        "file":       name,
        "size":       len(data),
        "salt_hex":   data[:SALT].hex(" "),
        "count":      len(records),
        "size_hist":  dict(sorted(size_hist.items())),
        "records":    records,
    }


# ─── smith_dat: forge / recipe table ───────────────────────────────────────

def parse_smith(data: bytes, name: str) -> dict[str, Any]:
    """smith_dat = 80 × 11B entries.
    가설: cat(1) ?(1) input1(1) input2(1) input3(1) outA(1) outB(1) outC(1) gold(1) result_cat(1) result_id(1)
    """
    p = SALT
    stride = 11
    recipes: list[dict] = []
    while p + stride <= len(data):
        e = data[p:p+stride]
        if e == b"\x00" * stride:
            break
        recipes.append({
            "offset": p,
            "hex":    e.hex(" "),
            "bytes":  list(e),
        })
        p += stride
    return {
        "file":     name,
        "size":     len(data),
        "salt_hex": data[:SALT].hex(" "),
        "stride":   stride,
        "count":    len(recipes),
        "recipes":  recipes,
    }


# ─── shop_dat: NPC shop sell list ──────────────────────────────────────────

def parse_shop(data: bytes, name: str) -> dict[str, Any]:
    """shop_dat = 5 × 10B entries (또는 가변).
    각 entry = u8 count + u8 ? + u8 ? + u8 ? + items(...).
    """
    p = SALT
    stride = 10
    shops: list[dict] = []
    while p + stride <= len(data) - 0:
        e = data[p:p+stride]
        if e[:2] == b"\x00\x00":
            break
        shops.append({
            "offset":  p,
            "hex":     e.hex(" "),
            "bytes":   list(e),
        })
        p += stride
    return {
        "file":     name,
        "size":     len(data),
        "salt_hex": data[:SALT].hex(" "),
        "stride":   stride,
        "count":    len(shops),
        "trailer":  data[p:].hex(" "),
        "shops":    shops,
    }


# ─── getitem_dat: fixed drop table ─────────────────────────────────────────

def parse_getitem(data: bytes) -> dict[str, Any]:
    """getitem_dat = 96 × 4B entries (type, ?, cat, id).
    예: 02 00 0f 00 → type=2, cat=0x0f, id=0
    """
    p = SALT
    stride = 4
    items: list[dict] = []
    while p + stride <= len(data):
        e = data[p:p+stride]
        if e == b"\x00" * stride:
            break
        items.append({
            "offset":  p,
            "type":    e[0],
            "flag":    e[1],
            "cat":     e[2],
            "id":      e[3],
            "hex":     e.hex(" "),
        })
        p += stride
    return {
        "file":     "getitem_dat",
        "size":     len(data),
        "salt_hex": data[:SALT].hex(" "),
        "stride":   stride,
        "count":    len(items),
        "items":    items,
    }


# ─── Driver ────────────────────────────────────────────────────────────────

def run() -> int:
    catalog: dict[str, Any] = {}

    f = DEC / "i15_dat.0EP@KO91.plain"
    if f.exists():
        catalog["i15_dat"] = parse_i15(f.read_bytes())

    for fn in ("drop_dat", "droph_dat"):
        f = DEC / f"{fn}.0EP@KO91.plain"
        if f.exists():
            catalog[fn] = parse_drop(f.read_bytes(), fn)

    for fn in ("smith_dat", "smithh_dat"):
        f = DEC / f"{fn}.0EP@KO91.plain"
        if f.exists():
            catalog[fn] = parse_smith(f.read_bytes(), fn)

    for fn in ("shop_dat", "shoph_dat"):
        f = DEC / f"{fn}.0EP@KO91.plain"
        if f.exists():
            catalog[fn] = parse_shop(f.read_bytes(), fn)

    f = DEC / "getitem_dat.0EP@KO91.plain"
    if f.exists():
        catalog["getitem_dat"] = parse_getitem(f.read_bytes())

    # write per-file JSON
    for fn, payload in catalog.items():
        p = OUT / f"h3_{fn}.json"
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  wrote {p.relative_to(ROOT)} ({payload.get('count','?')} entries)")

    # master catalog
    master = OUT / "h3_dat_catalog.json"
    summary = {
        fn: {k: v for k, v in payload.items()
             if k in ("file", "size", "count", "stride", "size_hist")}
        for fn, payload in catalog.items()
    }
    master.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {master.relative_to(ROOT)} (summary)")

    print("\nSummary:")
    for fn, s in summary.items():
        print(f"  {fn:<14} {s.get('count','?'):>4} entries "
              f"({s.get('size','?')}B, stride={s.get('stride','var')})")
    return 0


if __name__ == "__main__":
    sys.exit(run())
