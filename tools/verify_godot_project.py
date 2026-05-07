"""
Hero5 Godot 프로젝트 정적 검증.

체크 항목:
  1. project.godot 의 autoload/main_scene 파일 존재
  2. 모든 .tscn 의 ext_resource path 존재
  3. 모든 .gd 의 preload("res://...") 경로 존재
  4. 자산 디렉토리 (assets/sprites, gbm, palettes, text, sounds, fonts,
     gamedata, maps, scenes) 가 import_to_godot.py 산출물 보유

실제 GDScript 컴파일 검증은 Godot Editor 필요 — 이 스크립트는 reference
무결성만 체크.
"""
from __future__ import annotations
import re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJ = ROOT / 'apps' / 'hero5-godot'

ERRORS: list[str] = []
WARNINGS: list[str] = []


def res_to_path(res: str) -> pathlib.Path:
    return PROJ / res.replace('res://', '', 1)


def check_file(ref: str, source: pathlib.Path) -> None:
    if not ref.startswith('res://'):
        return
    p = res_to_path(ref)
    if not p.exists():
        ERRORS.append(f'{source.name}: missing {ref}')


def check_tscn(p: pathlib.Path) -> None:
    text = p.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'path="(res://[^"]+)"', text):
        check_file(m.group(1), p)


def check_gd(p: pathlib.Path) -> None:
    text = p.read_text(encoding='utf-8', errors='replace')
    # preload("res://...")
    for m in re.finditer(r'preload\("(res://[^"]+)"\)', text):
        check_file(m.group(1), p)
    # load("res://...")
    for m in re.finditer(r'load\("(res://[^"]+)"\)', text):
        check_file(m.group(1), p)


def check_project_godot() -> None:
    pg = PROJ / 'project.godot'
    if not pg.exists():
        ERRORS.append('project.godot not found'); return
    text = pg.read_text(encoding='utf-8')
    # main_scene
    m = re.search(r'run/main_scene="(res://[^"]+)"', text)
    if m: check_file(m.group(1), pg)
    # autoload
    for m in re.finditer(r'^\w+="\*?(res://[^"]+)"', text, re.MULTILINE):
        check_file(m.group(1), pg)


def check_assets_present() -> None:
    expected = {
        'assets/sprites':    'sprite frames',
        'assets/gbm':        'map gbm images',
        'assets/palettes':   'palettes',
        'assets/text':       'text json',
        'assets/sounds':     'ogg sounds',
        'assets/fonts':      'fnt PNG sheets',
        'assets/gamedata':   'csv game data',
        'assets/maps':       'collision maps',
        'assets/scenes':     'scene index',
    }
    for sub, desc in expected.items():
        d = PROJ / sub
        if not d.exists():
            WARNINGS.append(f'asset dir missing: {sub} ({desc}) — run tools/import_to_godot.py')
            continue
        n_files = sum(1 for _ in d.rglob('*') if _.is_file())
        if n_files == 0:
            WARNINGS.append(f'asset dir empty: {sub}')


def main() -> int:
    print(f'verifying {PROJ}/...\n')
    check_project_godot()
    for p in PROJ.rglob('*.tscn'):
        check_tscn(p)
    for p in PROJ.rglob('*.gd'):
        check_gd(p)
    check_assets_present()

    if WARNINGS:
        print(f'WARNINGS ({len(WARNINGS)}):')
        for w in WARNINGS: print(f'  ⚠ {w}')
        print()
    if ERRORS:
        print(f'ERRORS ({len(ERRORS)}):')
        for e in ERRORS: print(f'  ✗ {e}')
        return 1
    print(f'✓ all references resolve  ({len(WARNINGS)} warnings)')
    print('\n(GDScript compile errors are not detected here — open in Godot 4 to verify.)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
