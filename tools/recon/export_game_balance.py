"""Round 64: Hero3 game_balance.json 통합 출력 (Android 리메이크용 single source of truth).

R56-R63 의 모든 recon 산출물을 master stat enum 으로 통일된 JSON 으로 출력.

Inputs (기존 산출물 재사용):
  - work/h3/recon/item_decoded.json        (R61 decode_item_body.py 출력, 18 카테고리 480+ items)
  - work/h3/recon/skill_dat_all.json       (R60 parse_all_skill_dat.py 출력, 7 파일 × 15 skills)
  - work/h3/recon/skill_rank_decoded.json  (R62 decode_skill_rank.py 출력, +0x1d rank class)
  - work/h3/recon/quest_item_xref.json     (R62 cross_ref_quest_item.py 출력)
  - work/h3/recon/stat_enum.json           (R63 map_stat_enum.py 출력, 24 codes)
  - work/h3/extracted/dat/enemy_dat        (R56, 161 entries × 19B stat)
  - work/h3/extracted/dat/enemyh_dat       (R56, hard mode)
  - work/h3/extracted/boss/boss_dat        (R58, 15 bosses)
  - work/h3/extracted/boss/bossh_dat       (R58, hard mode)
  - work/h3/extracted/dat/quest_{00,01,10,11}_dat  (R58, 44+ quests)
  - work/h3/extracted/dat/char_dat         (R59, 10 playable classes)

Output:
  work/h3/game_balance.json  (master, ~1-2MB)
  work/h3/game_balance_summary.log (text overview)

Schema (top-level):
{
  "meta":      { "version":..., "round":64, "date":..., "stat_enum_count":24, ... },
  "stat_enum": { 0x00..0x1c: {name, desc, ...} },
  "rarity":    { prefix:str → {name, modifier_armor, modifier_weapon, ...} },
  "items":     { i0~i18: {category, layout, items:[{...}]} },
  "skills":    { s4~s10: {weapon, n_total, skills:[{...}]} },
  "enemies":   { normal:[{...}], hard:[{...}] },
  "bosses":    { normal:[{...}], hard:[{...}] },
  "quests":    { quest_00, quest_01, quest_10, quest_11 },
  "char_classes": [{class_name, weapon, ...}],
  "des_status":{ pending:[i15_dat, drop, droph, getitem, smith, smithh, shop, shoph], algorithm, key }
}
"""
import json
import struct
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "work/h3/extracted"
RECON = ROOT / "work/h3/recon"
OUT = ROOT / "work/h3"


# ---------- helpers (parse_enemy_dat.py 재구현, dependency 회피) ----------
def parse_entries_19B(data: bytes) -> list[dict]:
    """enemy_dat / boss_dat 공통 19B stat layout 엔트리 파싱."""
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        name_len = data[pos + 2]
        total_size = size_byte + 2
        if total_size < 24 or pos + total_size > len(data):
            break
        name_bytes = data[pos + 3 : pos + 3 + name_len].rstrip(b"@")
        stat_start = pos + 3 + name_len
        stat_block = data[stat_start : stat_start + 19]
        trailer = data[stat_start + 19 : pos + total_size]
        try:
            name = name_bytes.decode("cp949")
        except UnicodeDecodeError:
            name = name_bytes.hex()
        entries.append({
            "pos": pos,
            "name": name,
            "stat_block_hex": stat_block.hex(" "),
            "trailer_hex": trailer.hex(" "),
            "stat_block_bytes": stat_block,
        })
        pos += total_size
    return entries


def interpret_19B(stat: bytes) -> dict:
    """19B stat block → field mapping (R60 boss_hp 검증 결과 사용).

    R60: +0x0a..+0x0b BE16 = MaxHP, +0x0c..+0x0d = CurrentHP, +0x0e..+0x0f = EXP/Gold.
    """
    if len(stat) < 19:
        return {"raw": stat.hex(" ")}
    return {
        "lvl":      stat[0],
        "f4_5":     (stat[4] << 8) | stat[5],     # MP (?)
        "f6_7":     (stat[6] << 8) | stat[7],
        "f8_9":     (stat[8] << 8) | stat[9],
        "hp_max":   (stat[10] << 8) | stat[11],  # R60 확정
        "hp_cur":   (stat[12] << 8) | stat[13],
        "exp_gold": (stat[14] << 8) | stat[15],
        "f16":      stat[16],
        "agi_or":   stat[17],
        "f18":      stat[18],
    }


# ---------- rarity prefix (R62) ----------
RARITY_PREFIX = {
    "|": {"name": "magic",        "color": "blue",   "modifier_armor": 1.13, "modifier_weapon": 1.01},
    "'": {"name": "legendary",    "color": "gold",   "modifier_armor": 1.06, "modifier_weapon": 1.00},
    "$": {"name": "epic",         "color": "purple", "modifier_armor": 1.15, "modifier_weapon": 0.93},
    "{": {"name": "boss_drop",    "color": "orange", "modifier_armor": 1.50, "modifier_weapon": 0.03},  # weapon = essentially free
    "@": {"name": "endgame",      "color": "red",    "modifier_armor": 1.00, "modifier_weapon": 1.00},
    "}": {"name": "quest_reward", "color": "green",  "modifier_armor": 0.00, "modifier_weapon": 0.00},
}


def detect_rarity(name: str) -> str:
    if not name:
        return "normal"
    return RARITY_PREFIX.get(name[0], {"name": "normal"})["name"]


def clean_name(name: str) -> str:
    if name and name[0] in RARITY_PREFIX:
        return name[1:]
    return name


# ---------- DES status (R57-R63) ----------
DES_STATUS = {
    "algorithm": "standard FIPS DES (ECB-like, see Hero5 NDK runner)",
    "key": "0EP@KO91",
    "tables_file": "dat/des_dat (824B FIPS tables: IP, IP^-1, E, P, S1-S8, PC1, PC2)",
    "pending_files": [
        {"path": "dat/i15_dat",       "size_bytes": 7400, "entropy": 7.97, "role": "?? master item table (largest)"},
        {"path": "dat/drop_dat",      "size_bytes": 3080, "entropy": ">=7.8", "role": "enemy loot table"},
        {"path": "dat/droph_dat",     "size_bytes": 3080, "entropy": ">=7.8", "role": "hard-mode loot table"},
        {"path": "dat/getitem_dat",   "size_bytes": 400,  "entropy": ">=7.8", "role": "fixed item drops"},
        {"path": "dat/smith_dat",     "size_bytes": 896,  "entropy": 7.76, "role": "smith recipe (i14 → i0~i12)"},
        {"path": "dat/smithh_dat",    "size_bytes": 896,  "entropy": 7.76, "role": "smith recipe hard-mode"},
        {"path": "dat/shop_dat",      "size_bytes": "?", "entropy": ">=7.8", "role": "shop catalog"},
        {"path": "dat/shoph_dat",     "size_bytes": "?", "entropy": ">=7.8", "role": "shop catalog hard-mode"},
    ],
    "blocker": "user environment NDK runner required (Hero5 path, see reference_h5_des_blocker.md)",
}


# ---------- main ----------
def load_json(p: Path) -> dict | list:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    out: dict = {}
    summary_lines: list[str] = []

    # 1. meta
    out["meta"] = {
        "project": "Hero3 Remake (영웅서기3)",
        "round": 64,
        "date": "2026-05-19",
        "round_label": "R64 = R56-R63 통합 game_balance.json",
        "stat_enum_count": 24,
        "items_categories": 18,
        "skills_files": 7,
        "enemies_count": 161,
        "bosses_count": 15,
        "quests_files": 4,
        "des_pending": 8,
        "schema_version": "1.0",
    }
    summary_lines.append("===== Hero3 game_balance.json =====")
    summary_lines.append(f"Generated: Round 64 (2026-05-19), schema v1.0")

    # 2. stat_enum (R63)
    stat_enum_doc = load_json(RECON / "stat_enum.json")
    out["stat_enum"] = stat_enum_doc.get("stat_enum_master", stat_enum_doc)
    summary_lines.append(f"\nStat enum: {len(out['stat_enum'])} codes")
    for k, v in out["stat_enum"].items():
        summary_lines.append(f"  {k}: {v.get('name'):<20} {v.get('desc','')[:50]}")

    # 3. rarity (R62)
    out["rarity"] = RARITY_PREFIX
    summary_lines.append(f"\nRarity prefixes: {len(RARITY_PREFIX)}")

    # 4. items (R60-R63)
    items_doc = load_json(RECON / "item_decoded.json")
    items_enriched: dict = {}
    item_total = 0
    for fn, payload in items_doc.items():
        cat = payload.get("category", "?")
        raw_items = payload.get("items", [])
        enriched = []
        for it in raw_items:
            rarity = detect_rarity(it.get("name", ""))
            cname = clean_name(it.get("name", ""))
            enriched.append({**it, "rarity": rarity, "clean_name": cname})
        items_enriched[fn] = {
            "category": cat,
            "n_items": len(enriched),
            "items": enriched,
        }
        item_total += len(enriched)
    out["items"] = items_enriched
    summary_lines.append(f"\nItems: {item_total} total across {len(items_enriched)} categories")
    for fn, p in items_enriched.items():
        rar_count = Counter(it.get("rarity") for it in p["items"])
        rar_str = ", ".join(f"{r}={c}" for r, c in sorted(rar_count.items()))
        summary_lines.append(f"  {fn} ({p['category']}): {p['n_items']} — {rar_str}")

    # 5. skills (R60-R63)
    skill_all = load_json(RECON / "skill_dat_all.json")
    skill_ranks = load_json(RECON / "skill_rank_decoded.json")
    weapon_class_map = {
        "s4_dat":  "창 (스피어)",   "s5_dat":  "검 (대검)",
        "s6_dat":  "단검",          "s7_dat":  "건 (피스톨)",
        "s8_dat":  "라이플",        "s9_dat":  "다크석 (흑마법)",
        "s10_dat": "홀리석 (백마법)",
    }
    skills_out: dict = {}
    skill_total = 0
    for fn, raw_skills in skill_all.items():
        weapon = weapon_class_map.get(fn, "?")
        rank_info = skill_ranks.get(fn, {})
        skills_out[fn] = {
            "weapon": weapon,
            "n_skills": len(raw_skills),
            "rank_info": rank_info,
            "skills": raw_skills,
        }
        skill_total += len(raw_skills)
    out["skills"] = skills_out
    summary_lines.append(f"\nSkills: {skill_total} total across {len(skills_out)} weapon classes")
    for fn, s in skills_out.items():
        summary_lines.append(f"  {fn} ({s['weapon']}): {s['n_skills']} skills")

    # 6. enemies (R56)
    def parse_dat(path: Path) -> list[dict]:
        if not path.exists():
            return []
        data = path.read_bytes()
        entries = parse_entries_19B(data)
        out_list = []
        for e in entries:
            interp = interpret_19B(e["stat_block_bytes"])
            out_list.append({
                "pos": e["pos"],
                "name": e["name"],
                "stats": interp,
                "stat_block_hex": e["stat_block_hex"],
                "trailer_hex": e["trailer_hex"],
            })
        return out_list

    enemies_n = parse_dat(EXT / "dat/enemy_dat")
    enemies_h = parse_dat(EXT / "dat/enemyh_dat")
    out["enemies"] = {"normal": enemies_n, "hard": enemies_h}
    summary_lines.append(f"\nEnemies: normal={len(enemies_n)}, hard={len(enemies_h)}")
    if enemies_n:
        lvls = [e["stats"]["lvl"] for e in enemies_n if "lvl" in e["stats"]]
        hps = [e["stats"]["hp_max"] for e in enemies_n if "hp_max" in e["stats"]]
        summary_lines.append(f"  normal lvl: {min(lvls)}-{max(lvls)}, hp_max: {min(hps)}-{max(hps)}")
    if enemies_h:
        lvls = [e["stats"]["lvl"] for e in enemies_h if "lvl" in e["stats"]]
        hps = [e["stats"]["hp_max"] for e in enemies_h if "hp_max" in e["stats"]]
        summary_lines.append(f"  hard   lvl: {min(lvls)}-{max(lvls)}, hp_max: {min(hps)}-{max(hps)}")

    # 7. bosses (R58)
    bosses_n = parse_dat(EXT / "boss/boss_dat")
    bosses_h = parse_dat(EXT / "boss/bossh_dat")
    out["bosses"] = {"normal": bosses_n, "hard": bosses_h}
    summary_lines.append(f"\nBosses: normal={len(bosses_n)}, hard={len(bosses_h)}")
    for b in bosses_n[:5]:
        summary_lines.append(f"  {b['name']} lvl={b['stats'].get('lvl')}, hp_max={b['stats'].get('hp_max')}")

    # 8. quests (R58/R62)
    quest_xref = load_json(RECON / "quest_item_xref.json")
    quests_out: dict = {}
    for fn in ["quest_00_dat", "quest_01_dat", "quest_10_dat", "quest_11_dat"]:
        path = EXT / "dat" / fn
        if not path.exists():
            continue
        data = path.read_bytes()
        # quest_*_dat 는 enemy 와 같은 layout 가정 (parse_quest_dat.py 동일 로직)
        entries = parse_entries_19B(data)
        quests_out[fn] = {
            "size_bytes": len(data),
            "n_entries": len(entries),
            "entries": [{"pos": e["pos"], "name": e["name"]} for e in entries[:20]],
        }
    out["quests"] = {
        "files": quests_out,
        "item_xref": quest_xref,
        "n_xref_items": len(quest_xref),
    }
    summary_lines.append(f"\nQuests: {sum(q['n_entries'] for q in quests_out.values())} entries across {len(quests_out)} files")
    summary_lines.append(f"  quest-item xref: {len(quest_xref)} items mapped (R62)")

    # 9. char_classes (R59)
    char_path = EXT / "dat/char_dat"
    char_classes = []
    if char_path.exists():
        char_data = char_path.read_bytes()
        # char_dat: 10 entries, header(3) + name1 + name2_len + name2 + 7B stat + 2B trailer
        pos = 0
        while pos < len(char_data):
            if pos + 3 > len(char_data):
                break
            size_byte = char_data[pos]
            name_len = char_data[pos + 2]
            total = size_byte + 2
            if total < 6 or pos + total > len(char_data):
                break
            try:
                name1 = char_data[pos + 3 : pos + 3 + name_len].rstrip(b"@\x00").decode("cp949", errors="replace")
            except Exception:
                name1 = ""
            tail = char_data[pos + 3 + name_len : pos + total]
            char_classes.append({
                "pos": pos,
                "name1": name1,
                "tail_hex": tail.hex(" "),
                "weapon_byte": tail[0] if tail else None,
            })
            pos += total
            if len(char_classes) >= 20:
                break
    out["char_classes"] = char_classes
    summary_lines.append(f"\nChar classes: {len(char_classes)} parsed")

    # 10. DES status
    out["des_status"] = DES_STATUS
    summary_lines.append(f"\nDES pending: {len(DES_STATUS['pending_files'])} files")
    summary_lines.append(f"  Algorithm: {DES_STATUS['algorithm']}")
    summary_lines.append(f"  Key: {DES_STATUS['key']}")
    summary_lines.append(f"  Blocker: {DES_STATUS['blocker']}")

    # ---- write ----
    bal_path = OUT / "game_balance.json"
    log_path = OUT / "game_balance_summary.log"
    bal_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log_path.write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"Wrote {bal_path} ({bal_path.stat().st_size:,}B)")
    print(f"Wrote {log_path} ({log_path.stat().st_size:,}B)")
    print("\n--- Summary ---")
    print("\n".join(summary_lines[:30]))
    print(f"... ({len(summary_lines)} total lines in log)")


if __name__ == "__main__":
    main()
