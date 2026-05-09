"""HERO/CHAR/BATTLER 의 stat 관련 메서드 이름 추출.

목적: V[112..116] 5 secondary stat 라벨 식별 단서 수집.
GetHit / GetAvoid / GetCritical / GetBlock / GetSpeed 같은 wrapper 가
존재하면 그 이름이 stat 라벨을 그대로 반영함.
"""
from __future__ import annotations
import pathlib
import re

import lief

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/stat_methods.txt"


def simple_demangle(mangled: str) -> str | None:
    """Itanium ABI mangled name → 'Class::Method' (인수 무시)."""
    if not mangled.startswith("_ZN"):
        return None
    s = mangled[3:]
    parts = []
    while s and s[0].isdigit():
        n = 0
        while s and s[0].isdigit():
            n = n * 10 + int(s[0])
            s = s[1:]
        if len(s) < n:
            break
        parts.append(s[:n])
        s = s[n:]
        if s.startswith("E"):
            break
    if not parts:
        return None
    return "::".join(parts)


def main() -> int:
    so = lief.parse(str(SO))
    rows = []
    for s in so.symbols:
        n = s.name or ""
        if not n.startswith("_ZN") or not s.value or not s.size:
            continue
        d = simple_demangle(n)
        if not d:
            continue
        rows.append((d, n, s.value & ~1, s.size))

    # 핵심 stat name 분류
    cats = {
        "ATK": r"\bA(tk|ttack)\b",
        "DEF": r"\bDef(en[cs]e)?\b",
        "Hit": r"\bHit(Rate)?\b",
        "Avoid": r"\bAvoid|\bEvasion|\bDodge",
        "Crit": r"\bCrit(ical)?",
        "Block": r"\bBlock(Rate)?",
        "Speed": r"\bSpeed|\bSpd|\bInitiative|\bAct(ion)?Speed",
        "Recover": r"\bRecover|\bRegen",
        "Resist": r"\bResist",
        "Penetration": r"\bPenetration|\bPierce",
        "Reflect": r"\bReflect|\bCounter",
        "Spirit": r"\bSpirit",
        "MaxHP": r"\bMaxHP\b|\bHpMax\b",
        "MaxMP": r"\bMaxMP\b|\bMpMax\b",
        "Magic": r"\bMagic(Atk|Def)?",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("# stat-related method names (HERO/CHAR/BATTLER)\n")
        for label, pat in cats.items():
            regex = re.compile(pat)
            matches = sorted({(d, a) for d, _, a, _ in rows if regex.search(d)})
            f.write(f"\n## {label} ({len(matches)})\n")
            for d, a in matches:
                f.write(f"  0x{a:08x}  {d}\n")
            print(f"-- {label} ({len(matches)})")
            for d, a in matches[:25]:
                print(f"   0x{a:08x}  {d}")
            if len(matches) > 25:
                print(f"   ... +{len(matches) - 25} more")

    print(f"\n[+] {OUT}")

    # HERO 와 CHAR 의 모든 Get* 메서드만 별도 dump (큰 단서)
    hero_get = sorted({d for d, _, _, _ in rows if d.startswith(("HERO::Get", "CHAR::Get", "BATTLER::Get"))})
    print(f"\n== HERO/CHAR/BATTLER Get* 메서드 ({len(hero_get)}) ==")
    for d in hero_get:
        print(f"   {d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
