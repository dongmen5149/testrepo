"""Round 75 — game_balance.json v1.1 → v1.2 in-place patch.

기존 v1.1 (R66, 582KB) 에 R74 산출물 8 DES plaintext JSON 을 통합.

Input :
  android/app/src/main/assets/game_balance.json  (v1.1, 582KB)
  work/h3/recon/h3_*.json                        (R74 산출, 8 파일)

Output (in-place 갱신):
  work/h3/game_balance.json                      (v1.2, ~700KB)
  android/app/src/main/assets/game_balance.json  (Android assets sync)

추가 키:
  meta.schema_version  = "1.2"
  meta.round           = 75
  des_status           = R73 confirmed (pending_files=[], decrypted_files=8)
  r74_des_data         = {shop_catalog, drop_table(_hard), recipes(_hard),
                          region_shops(_hard), fixed_drops}
"""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / "android" / "app" / "src" / "main" / "assets" / "game_balance.json"
RECON = ROOT / "work" / "h3" / "recon"
OUT_W = ROOT / "work" / "h3" / "game_balance.json"


def _load_json(p: pathlib.Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


DES_STATUS_V12 = {
    "algorithm": "Hero5 mx_des_decrypt (startDes mode=0 + swap halves) — R73 confirmed",
    "key": "0EP@KO91",
    "tables_file": "dat/des_dat (824B FIPS tables)",
    "pending_files": [],
    "decrypted_files": [
        {"path": "dat/i15_dat",    "size_bytes": 7400, "entries": 38,  "role": "master shop catalog (EUC-KR desc)"},
        {"path": "dat/drop_dat",   "size_bytes": 3080, "entries": 161, "role": "enemy drop table (17B stride)"},
        {"path": "dat/droph_dat",  "size_bytes": 3080, "entries": 161, "role": "hard-mode drop table"},
        {"path": "dat/getitem_dat","size_bytes": 400,  "entries": 96,  "role": "fixed item table (4B stride)"},
        {"path": "dat/smith_dat",  "size_bytes": 896,  "entries": 80,  "role": "forge recipes (11B stride)"},
        {"path": "dat/smithh_dat", "size_bytes": 896,  "entries": 80,  "role": "forge recipes hard-mode"},
        {"path": "dat/shop_dat",   "size_bytes": 72,   "entries": 5,   "role": "NPC region shops (10B stride)"},
        {"path": "dat/shoph_dat",  "size_bytes": 72,   "entries": 5,   "role": "NPC region shops hard-mode"},
    ],
    "blocker": None,
    "round": 73,
    "boss_skill_h4_confirmed": True,
    "boss_skill_h4_evidence": "drop_dat 98/161 records (61%) have >=3 byte matches with BSKILL set {1,2,3,5,7,8,9,10,13,14,19,20}",
}


def main() -> int:
    if not ASSETS.exists():
        print(f"  ! missing: {ASSETS}", file=sys.stderr)
        return 2

    catalog = json.loads(ASSETS.read_text(encoding="utf-8"))

    # bump meta
    meta = catalog.setdefault("meta", {})
    meta["schema_version"] = "1.2"
    meta["round"] = 75
    meta["round_label"] = "R75 = R74 DES 평문 정밀 파서 통합 (recipes/region_shops/drops/fixed_drops)"

    # R74 DES plaintext data
    r74 = {
        "shop_catalog":     _load_json(RECON / "h3_i15_dat.json"),
        "drop_table":       _load_json(RECON / "h3_drop_dat.json"),
        "drop_table_hard":  _load_json(RECON / "h3_droph_dat.json"),
        "recipes":          _load_json(RECON / "h3_smith_dat.json"),
        "recipes_hard":     _load_json(RECON / "h3_smithh_dat.json"),
        "region_shops":     _load_json(RECON / "h3_shop_dat.json"),
        "region_shops_hard":_load_json(RECON / "h3_shoph_dat.json"),
        "fixed_drops":      _load_json(RECON / "h3_getitem_dat.json"),
    }
    catalog["r74_des_data"] = r74

    # update des_status
    catalog["des_status"] = DES_STATUS_V12

    # write
    blob = json.dumps(catalog, ensure_ascii=False, indent=2)
    OUT_W.parent.mkdir(parents=True, exist_ok=True)
    OUT_W.write_text(blob, encoding="utf-8")
    ASSETS.write_text(blob, encoding="utf-8")

    print(f"  wrote {OUT_W.relative_to(ROOT)} ({OUT_W.stat().st_size:,}B)")
    print(f"  wrote {ASSETS.relative_to(ROOT)} ({ASSETS.stat().st_size:,}B)")

    counts = {k: v.get("count", 0) for k, v in r74.items()}
    print(f"\n  R74 entry counts: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
