#!/usr/bin/env python3
"""Hero4 R106 ITM_OPTION struct + R107 death sphere timer verify — regression checks."""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONVERTED = ROOT / 'work' / 'h4' / 'converted'
CATALOG = CONVERTED / 'h4_catalog.json'
ANDROID_CATALOG = ROOT / 'apps' / 'hero4-android/app/src/main/assets/h4_catalog.json'

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def main() -> int:
    # R106
    opt_path = CONVERTED / 'h4_itm_option_struct.json'
    check(opt_path.exists(), 'h4_itm_option_struct.json missing')
    opt = json.loads(opt_path.read_text(encoding='utf-8'))
    check(opt['meta']['round'] == 'R106', 'R106 meta.round')
    check(opt['entry_count'] == 122, f"entry_count={opt['entry_count']} != 122")
    hist = opt['payload_len_histogram']
    check(hist.get('3') == 122 or hist.get(3) == 122, f'payload 3B only: {hist}')
    check(opt['header']['le32_first4'] == 4, 'header LE32=4')

    parse_py = ROOT / 'tools/converter/parse_h4_itm_option_struct.py'
    check(parse_py.exists(), 'parse_h4_itm_option_struct.py missing')
    doc = ROOT / 'docs/h4/round106-itm-option-structure.md'
    check(doc.exists(), 'round106 doc missing')

    # R107
    tv_path = CONVERTED / 'h4_death_sphere_timer_verify.json'
    check(tv_path.exists(), 'h4_death_sphere_timer_verify.json missing')
    tv = json.loads(tv_path.read_text(encoding='utf-8'))
    c = tv['conclusion']
    check(c['timer_field_confirmed'], 'timer sequence not confirmed')
    check(c['sequence'] == [600, 480, 360], f"sequence={c['sequence']}")
    check(c['uniqueness'], 'timer values not unique to death sphere')
    check(c['unit_verdict'].startswith('seconds'), c['unit_verdict'])
    check(c['step_per_stage'] == 120, 'step_per_stage')
    doc107 = ROOT / 'docs/h4/round107-death-sphere-timer-verify.md'
    check(doc107.exists(), 'round107 doc missing')

    # catalog merge
    if CATALOG.exists():
        cat = json.loads(CATALOG.read_text(encoding='utf-8'))
        check('itm_option_struct' in cat, 'catalog missing itm_option_struct')
        check(cat['itm_option_struct']['entry_count'] == 122, 'catalog itm_option_struct')
        ds = cat.get('death_sphere', {})
        check('timer_unit_verify' in ds, 'catalog death_sphere.timer_unit_verify')
        check(ds['timer_unit_verify']['uniqueness'], 'catalog uniqueness')

    build_py = (ROOT / 'tools/converter/build_h4_catalog.py').read_text(encoding='utf-8')
    check('h4_itm_option_struct.json' in build_py, 'build_h4_catalog R106 hook')
    check('h4_death_sphere_timer_verify.json' in build_py, 'build_h4_catalog R107 hook')

    passed = 15 - len(FAILURES)
    total = 15
    for f in FAILURES:
        print(f'FAIL: {f}')
    print(f'R106+R107: {total - len(FAILURES)}/{total} checks passed')
    return 1 if FAILURES else 0


if __name__ == '__main__':
    sys.exit(main())
