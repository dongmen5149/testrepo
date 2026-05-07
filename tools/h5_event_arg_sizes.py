"""Hero5 .so 에서 Event_* 함수 mangled 이름 → arg_size 추출.

Itanium C++ ABI mangling type chars:
  v=void(0)  b/c/a/h=1   s/t=2   i/j/l/m/f=4   x/y/d=8
  P/R = pointer/reference (32bit ARM = 4)

`Event_NAMEE<types>` 형식에서 'E' 다음 type chars 를 합산.

산출:
  work/h5/analysis/event_arg_sizes.tsv  — Event_NAME → arg_size lookup
"""
from __future__ import annotations
import re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/event_arg_sizes.tsv"

TYPE_SIZE = {
    'v': 0,
    'b': 1, 'c': 1, 'a': 1, 'h': 1,
    's': 2, 't': 2,
    'i': 4, 'j': 4, 'l': 4, 'm': 4, 'f': 4,
    'x': 8, 'y': 8, 'd': 8,
}


def mangle_to_argsize(suffix: str) -> int | None:
    """`hhahhh` → 6. P/R 은 다음 char 와 함께 4B 로 처리. 모르는 char → None."""
    size = 0
    i = 0
    while i < len(suffix):
        c = suffix[i]
        if c in ('P', 'R'):
            size += 4
            i += 1
            if i < len(suffix):
                # consume one more (pointee type) — even if it's 'K' (const), 'V' (volatile)
                # we just skip simple single char
                i += 1
            continue
        if c == 'K' or c == 'V':  # cv qualifier
            i += 1
            continue
        if c == 'N':  # nested name — give up
            return None
        if c not in TYPE_SIZE:
            return None
        size += TYPE_SIZE[c]
        i += 1
    return size


def main() -> int:
    if not SO.exists():
        print(f'ERROR: {SO} missing — extract APK first'); return 1
    so = SO.read_bytes()
    pat = re.compile(rb'Event_([A-Za-z_]+)E([a-zA-Z]{0,16})(?=\x00|[^a-zA-Z])')
    seen = {}
    for m in pat.finditer(so):
        name = b'Event_' + m.group(1)
        sfx = m.group(2).decode('ascii', errors='ignore')
        nm = name.decode()
        if nm in seen: continue
        sz = mangle_to_argsize(sfx)
        if sz is None: continue
        seen[nm] = (sz, sfx)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('event_name\targ_size\tmangle_suffix\n')
        for nm in sorted(seen):
            sz, sfx = seen[nm]
            f.write(f'{nm}\t{sz}\t{sfx}\n')
    print(f'wrote {len(seen)} Event_* arg sizes -> {OUT}')

    # cross-check against BASE_TABLE (hardcoded reference list)
    REF = {
        0x00: ('Event_EnemyAction', 6), 0x01: ('Event_EnemyChange', 2),
        0x02: ('Event_EnemyChangeAction', 7), 0x03: ('Event_EnemyDir', 2),
        0x04: ('Event_EnemyEffect', 2), 0x05: ('Event_EnemyImo', 2),
        0x06: ('Event_EnemyMove', 5), 0x07: ('Event_EnemyMoveRelative', 5),
        0x08: ('Event_EnemyTeleport', 5), 0x09: ('Event_EventAction', 6),
        0x0a: ('Event_EventChangeCheck', 2), 0x0b: ('Event_EventChangeImg', 2),
        0x0c: ('Event_EvnetImgAction', 7), 0x0d: ('Event_EventChangeMoveType', 2),
        0x0e: ('Event_EventDirection', 2), 0x0f: ('Event_EventEffect', 2),
        0x10: ('Event_EventImo', 2), 0x11: ('Event_EventMove', 5),
        0x12: ('Event_EventMoveBreak', 1), 0x13: ('Event_EventMoveRelative', 5),
        0x14: ('Event_EventTeleport', 5), 0x15: ('Event_MapCollision', 3),
        0x16: ('Event_MapEncountPirate', 2), 0x17: ('Event_MapObjChangeAll', 2),
        0x18: ('Event_MapTileChange', 6), 0x19: ('Event_MapTileChangeAll', 4),
        0x1a: ('Event_MapWorldControl', 2), 0x1b: ('Event_PlayerAction', 5),
        0x1c: ('Event_PlayerAppearSpirit', 1), 0x1d: ('Event_PlayerChange', 1),
        0x31: ('Event_QuestBoss', 2), 0x32: ('Event_QuestTimer', 4),
        0x33: ('Event_QuestStatus', 2), 0x35: ('Event_SituateBallon', 2),
        0x39: ('Event_SituateDialogText', 4), 0x3a: ('Event_QuestSwitch', 2),
        0x3b: ('Event_SituateNarration', 3), 0x3e: ('Event_SituatePopup', 1),
        0x42: ('Event_QuestQSwitch', 2), 0x43: ('Event_Scene_ChangeBgm', 1),
    }
    mism = []
    for op, (nm, expected) in REF.items():
        if nm in seen and seen[nm][0] != expected:
            mism.append((op, nm, expected, seen[nm][0]))
    if mism:
        print('\nMISMATCHES (BASE_TABLE vs .so mangle):')
        for op, nm, exp, got in mism:
            print(f'  0x{op:02x} {nm}: expected={exp} mangle={got}')
    else:
        print('\nBASE_TABLE arg_size 모두 .so mangle 과 일치 ✓')
    return 0


if __name__ == '__main__':
    sys.exit(main())
