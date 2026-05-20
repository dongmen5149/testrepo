#!/usr/bin/env python3
"""Hero4 COMPLETION.md + cross-doc completion metrics — consistency checks."""
from __future__ import annotations
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPLETION = ROOT / 'docs' / 'h4' / 'COMPLETION.md'
HANDOFF = ROOT / 'docs' / 'h4' / 'SESSION_HANDOFF.md'
PROGRESS = ROOT / 'docs' / 'h4' / 'PROGRESS.md'
METHODOLOGY = ROOT / 'docs' / 'REMAKE_METHODOLOGY.md'
MAIN_ACTIVITY = ROOT / 'apps' / 'hero4-android' / 'app' / 'src' / 'main' / 'java' / 'com' / 'hero4' / 'remake' / 'MainActivity.kt'

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding='utf-8')


def main() -> int:
    comp = read(COMPLETION)
    handoff = read(HANDOFF)
    progress = read(PROGRESS)
    methodology = read(METHODOLOGY)

    # Strict beta definition
    check('원작과 거의 동일' in comp or '원작 동일' in comp, 'strict beta definition in COMPLETION')
    check('시나리오' in comp and '정상' in comp, 'scenario + normal play in COMPLETION')
    check('12–18%' in comp or '12-18%' in comp, 'strict beta range 12-18%')
    check('~15%' in comp, 'strict beta center ~15%')
    check('베타 오픈' in comp, 'beta open terminology')

    # Must not present old ~35% as primary headline
    lines = [ln for ln in comp.splitlines() if ln.startswith('| **A.') or '출시 베타 플레이 가능** ★' in ln]
    check(not any('35%' in ln and '★' in ln for ln in lines), 'old 35% not primary in COMPLETION table')

    check('12–18%' in handoff or '12-18%' in handoff, 'HANDOFF strict beta range')
    check('~15%' in progress, 'PROGRESS beta center')
    check('베타 오픈' in methodology or '~15%' in methodology, 'METHODOLOGY updated')

    check('COMPLETION.md' in handoff and 'COMPLETION.md' in progress, 'cross-links')

    check(MAIN_ACTIVITY.exists(), 'MainActivity exists')
    ma = read(MAIN_ACTIVITY)
    check('Hero4CatalogLoader' in ma, 'catalog PoC')
    check('MapWalkScene' not in ma and 'BattleScene' not in ma, 'no play scenes')

    check('55–65%' in comp and '혼용' in comp, 'stale 55-65 warning retained')

    total = 14
    for f in FAILURES:
        print(f'FAIL: {f}')
    passed = total - len(FAILURES)
    print(f'h4 completion doc: {passed}/{total} checks passed')
    return 1 if FAILURES else 0


if __name__ == '__main__':
    sys.exit(main())
