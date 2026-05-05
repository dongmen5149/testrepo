"""모든 sprite frame PNG 를 scale4x 로 일괄 업스케일.

입력:  work/<game>/converted/<cat>/<bm>/frame_*.png
출력:  work/<game>/converted_hd/<cat>/<bm>/frame_*.png
게임 선택: HERO_GAME 환경변수 (default h3)

scale4x 는 픽셀 아트 스타일 보존 + 대각선 매끄럽게.
"""
from __future__ import annotations
import pathlib, sys
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from upscale_poc import scale4x  # noqa: E402

_g = select()
CONVERTED = _g.converted_root
HD_OUT = _g.converted_hd_root


def main():
    HD_OUT.mkdir(exist_ok=True)
    n = 0
    for png in CONVERTED.rglob('*.png'):
        rel = png.relative_to(CONVERTED)
        out = HD_OUT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            continue
        img = Image.open(png).convert('RGBA')
        # 매우 큰 이미지는 메모리 폭주 방지
        if img.width * img.height > 50000:
            # 단순 nearest 4x 로 대체
            img4 = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
        else:
            img4 = scale4x(img)
        img4.save(out)
        n += 1
        if n % 100 == 0:
            print(f'  processed {n}...')
    print(f'\nDone: {n} files upscaled to {HD_OUT}')


if __name__ == '__main__':
    main()
