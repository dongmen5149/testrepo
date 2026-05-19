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
    "algorithm": "Hero5 mx_des_decrypt (startDes mode=0 + swap halves) — R73 confirmed",
    "key": "0EP@KO91",
    "tables_file": "dat/des_dat (824B FIPS tables: IP, IP^-1, E, P, S1-S8, PC1, PC2)",
    "pending_files": [],  # R73: all 8 files decrypted
    "decrypted_files": [
        {"path": "dat/i15_dat",       "size_bytes": 7400, "entries": 38,  "role": "master shop catalog (EUC-KR desc)"},
        {"path": "dat/drop_dat",      "size_bytes": 3080, "entries": 161, "role": "enemy drop table (17B stride)"},
        {"path": "dat/droph_dat",     "size_bytes": 3080, "entries": 161, "role": "hard-mode drop table"},
        {"path": "dat/getitem_dat",   "size_bytes": 400,  "entries": 96,  "role": "fixed item table (4B stride)"},
        {"path": "dat/smith_dat",     "size_bytes": 896,  "entries": 80,  "role": "forge recipes (11B stride)"},
        {"path": "dat/smithh_dat",    "size_bytes": 896,  "entries": 80,  "role": "forge recipes hard-mode (44/80 differ)"},
        {"path": "dat/shop_dat",      "size_bytes": 72,   "entries": 5,   "role": "NPC region shops (10B stride)"},
        {"path": "dat/shoph_dat",     "size_bytes": 72,   "entries": 5,   "role": "NPC region shops hard-mode"},
    ],
    "blocker": None,
    "round": 73,
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
        "schema_version": "1.2",
        "round": 75,
        "date": "2026-05-19",
        "round_label": "R75 = R74 DES 평문 정밀 파서 (recipes/region_shops/drops/fixed_drops/shop_catalog) 통합",
        "stat_enum_count": 24,
        "items_categories": 18,
        "skills_files": 7,
        "enemies_count": 161,
        "bosses_count": 15,
        "quests_files": 4,
        "des_pending": 8,
        "schema_version": "1.1",
        "v1.1_additions": [
            "skill effect block v2 (slot1/slot2/slot3 right-justified chain)",
            "boss combat_rating formula (round(lvl/2 + 44|64))",
            "debuff_code refined (11 distinct codes, stat enum 공유 + TAUNT/STUN/STUN_RESIST 추가)",
            "rarity × bt cross-tab",
        ],
    }
    summary_lines.append("===== Hero3 game_balance.json =====")
    summary_lines.append(f"Generated: Round 64 (2026-05-19), schema v1.0")

    # 2. stat_enum (R63 + R66 refined — 0x15 TAUNT 추가, 0x1c REVIVE/STUN dual)
    stat_enum_doc = load_json(RECON / "stat_enum.json")
    stat_enum = stat_enum_doc.get("stat_enum_master", stat_enum_doc)
    # R66 patches
    stat_enum["0x15"] = {
        "name": "TAUNT", "from": "skill 유도 0x15 (R66 신규)",
        "desc": "적의 공격을 자신에게 집중 (taunt/aggro draw)",
    }
    stat_enum["0x1c"]["context_split"] = {
        "i13_buff": "REVIVE (피닉스의숨결, 전투불능 회복)",
        "skill_debuff": "STUN (참혼/저격, 적을 기절)",
        "note": "동일 enum 코드, 컨텍스트별 의미 분리",
    }
    stat_enum["0x0d"]["context_split"] = {
        "i13/i16/equip": "CRI_DEF (크리피해 감소)",
        "skill_debuff": "STUN_RESIST_DEBUFF (위협, 적의 기절저항 감소)",
        "note": "R66 신규 발견. 동일 enum 코드, 컨텍스트별 의미 분리",
    }
    stat_enum["0x0b"]["context_buff"] = {
        "skill_buff": "BLOCK (자신에게 BLOCK +5, 유도)",
        "note": "skill 0x0b 가 양수 value 일 때는 자기 buff",
    }
    out["stat_enum"] = stat_enum

    # R66: debuff codes distinct usage (skill 디버프 11 codes)
    out["skill_debuff_codes"] = {
        "doc": "Round 66: skill effect block 의 11 distinct debuff codes (stat_enum 공유)",
        "codes": {
            "0x03": "HP_REGEN (음수 → BLEED)",
            "0x05": "ATT1 (망각 -)",
            "0x06": "ATT2 (망각 -)",
            "0x07": "P_DEF (전율 -)",
            "0x08": "M_DEF (전율 -)",
            "0x09": "ACC (압도/격광 -)",
            "0x0a": "DOD (전율 2차 -)",
            "0x0b": "BLOCK (유도 양수 → 자기 buff)",
            "0x0d": "STUN_RESIST_DEBUFF (위협 -)",
            "0x15": "TAUNT (유도)",
            "0x1c": "STUN_TRIGGER (참혼/저격 val=0)",
        },
        "chain_length_distribution": {"0_debuffs": 14, "1_debuff": 6, "2_debuffs": 3, "3_debuffs": 1},
    }
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

    # 5. skills (R60-R66)
    skill_all = load_json(RECON / "skill_dat_all.json")
    skill_ranks = load_json(RECON / "skill_rank_decoded.json")
    weapon_class_map = {
        "s4_dat":  "창 (스피어)",   "s5_dat":  "검 (대검)",
        "s6_dat":  "단검",          "s7_dat":  "건 (피스톨)",
        "s8_dat":  "라이플",        "s9_dat":  "다크석 (흑마법)",
        "s10_dat": "홀리석 (백마법)",
    }
    # R66: skill effect v2 디코드 결과
    effect_v2_path = RECON / "skill_effect_v2.json"
    skill_effects_by_name: dict = {}
    if effect_v2_path.exists():
        ev2 = load_json(effect_v2_path)
        for s in ev2.get("active_attack_skills", []):
            skill_effects_by_name[(s.get("file", ""), s.get("name", ""))] = {
                "rank": s.get("rank"),
                "n_debuffs": s.get("n_debuffs"),
                "slot1": s.get("slot1"),
                "slot2": s.get("slot2"),
                "slot3": s.get("slot3"),
                "header": s.get("header"),
            }
    skills_out: dict = {}
    skill_total = 0
    for fn, raw_skills in skill_all.items():
        weapon = weapon_class_map.get(fn, "?")
        rank_info = skill_ranks.get(fn, {})
        # enrich each skill with R66 effect v2 if available
        enriched_skills = []
        for sk in raw_skills:
            entry = dict(sk)
            ev2_data = skill_effects_by_name.get((fn, sk.get("name", "")))
            if ev2_data:
                entry["effect_v2"] = ev2_data
            enriched_skills.append(entry)
        skills_out[fn] = {
            "weapon": weapon,
            "n_skills": len(enriched_skills),
            "rank_info": rank_info,
            "skills": enriched_skills,
        }
        skill_total += len(enriched_skills)
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

    # 7. bosses (R58 + R65 trailer 6B + R66 combat_rating formula)
    def enrich_boss(b: dict, difficulty: str) -> dict:
        tr_hex = b.get("trailer_hex", "")
        try:
            tb = bytes.fromhex(tr_hex.replace(" ", ""))
        except ValueError:
            tb = b""
        if len(tb) >= 6:
            combat_rating = tb[0]
            sprite_idx    = tb[1]
            skill_slots   = list(tb[2:6])
            is_misc       = all(x == 0xFF for x in skill_slots)
            # R66 formula: rating = round(lvl/2 + offset)
            lvl = b.get("stats", {}).get("lvl") or 0
            expected_offset = 44 if difficulty == "normal" else 64
            expected = round(lvl / 2 + expected_offset)
            b["trailer_decoded"] = {
                "combat_rating":   combat_rating,
                "sprite_idx":      sprite_idx,
                "skill_slots":     skill_slots,
                "is_misc_boss":    is_misc,
                "expected_rating": expected,
                "rating_matches":  combat_rating == expected,
            }
        return b

    bosses_n = [enrich_boss(b, "normal") for b in parse_dat(EXT / "boss/boss_dat")]
    bosses_h = [enrich_boss(b, "hard")   for b in parse_dat(EXT / "boss/bossh_dat")]
    out["bosses"] = {
        "normal": bosses_n,
        "hard":   bosses_h,
        "combat_rating_formula": {
            "normal": "round(lvl/2 + 44)",
            "hard":   "round(lvl/2 + 64)",
            "note":   "R66 발견. 권장 player level 표시용 challenge equivalence.",
        },
    }
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
            "entries": [{"pos": e["pos"], "name": e["name"]} for e in entries],
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

    # 10a. R74 DES plaintext parsed data (from tools/recon/parse_h3_des_plain.py)
    def _load_recon_json(name: str) -> dict:
        p = RECON / name
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}

    r74 = {
        "shop_catalog":     _load_recon_json("h3_i15_dat.json"),
        "drop_table":       _load_recon_json("h3_drop_dat.json"),
        "drop_table_hard":  _load_recon_json("h3_droph_dat.json"),
        "recipes":          _load_recon_json("h3_smith_dat.json"),
        "recipes_hard":     _load_recon_json("h3_smithh_dat.json"),
        "region_shops":     _load_recon_json("h3_shop_dat.json"),
        "region_shops_hard":_load_recon_json("h3_shoph_dat.json"),
        "fixed_drops":      _load_recon_json("h3_getitem_dat.json"),
    }
    out["r74_des_data"] = r74
    summary_lines.append("\nR74 DES plaintext:")
    summary_lines.append(f"  shop_catalog:    {r74['shop_catalog'].get('count', 0)} entries")
    summary_lines.append(f"  drop_table:      {r74['drop_table'].get('count', 0)} entries")
    summary_lines.append(f"  recipes:         {r74['recipes'].get('count', 0)} entries")
    summary_lines.append(f"  region_shops:    {r74['region_shops'].get('count', 0)} entries")
    summary_lines.append(f"  fixed_drops:     {r74['fixed_drops'].get('count', 0)} entries")

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
