"""변환된 자산을 Android app/src/main/assets/ 로 복사.

배치:
    assets/sprites/<category>/<file>.png   <- _bm 변환 결과 (frame 0)
    assets/strings/<file>.json             <- _txt 변환 결과
    assets/palettes/<file>.json            <- _pa 변환 결과

사용:
    python prepare_android_assets.py <converted_dir> <android_assets_dir>
예:
    python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
"""
from __future__ import annotations
import sys, shutil, pathlib


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    converted = pathlib.Path(argv[1]).resolve()
    out = pathlib.Path(argv[2]).resolve()
    if not converted.is_dir():
        print(f'  ERROR: not a directory: {converted}')
        return 1
    out.mkdir(parents=True, exist_ok=True)

    counts = {'sprites': 0, 'strings': 0, 'palettes': 0}

    # _bm → sprites/<category>/
    sprites_root = out / 'sprites'
    for png in converted.rglob('*.png'):
        rel = png.relative_to(converted)
        dst = sprites_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(png, dst)
        counts['sprites'] += 1

    # _txt JSONs → strings/
    strings_root = out / 'strings'
    strings_root.mkdir(parents=True, exist_ok=True)
    for json_path in (converted / 'dat').glob('*_txt.json') if (converted / 'dat').exists() else []:
        shutil.copy2(json_path, strings_root / json_path.name)
        counts['strings'] += 1
    # 추가 위치 (예: menu/menu_txt.json) 도 수집
    for json_path in converted.rglob('*_txt.json'):
        rel = json_path.relative_to(converted)
        dst = strings_root / rel.name  # 평탄 배치 (이름 충돌 시 마지막 wins; 충돌 적음)
        if dst.exists() and dst.read_bytes() == json_path.read_bytes():
            continue
        shutil.copy2(json_path, dst)
        counts['strings'] += 1

    # _pa JSONs → palettes/
    palettes_root = out / 'palettes'
    palettes_root.mkdir(parents=True, exist_ok=True)
    for json_path in converted.rglob('*_pa.json'):
        rel = json_path.relative_to(converted)
        dst = palettes_root / rel.name
        if dst.exists():
            continue
        shutil.copy2(json_path, dst)
        counts['palettes'] += 1

    # 추가 단일 JSON 파일 (대사 코퍼스, 번역, 자산 카탈로그)
    counts['extras'] = 0
    for special in ('dialogue_corpus.json', 'dialogue_top_texts.json',
                    'dialogue_translations_en.json', 'asset_catalog.json'):
        src = converted / special
        if src.exists():
            shutil.copy2(src, out / special)
            counts['extras'] += 1

    print(f'Copied to {out}:')
    print(f'  sprites:  {counts["sprites"]}')
    print(f'  strings:  {counts["strings"]}')
    print(f'  palettes: {counts["palettes"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
