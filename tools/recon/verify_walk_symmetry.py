"""
walk-cycle 4 dir 의 mirror 쌍을 픽셀 symmetry 로 자동 식별.

가설: 4 방향 중 LEFT/RIGHT 는 동일 sprite 의 horizontal flip.
=> dir{X} 를 좌우 flip 한 결과가 dir{Y} 에 가장 가까우면 (X, Y) = (LEFT, RIGHT) 쌍.

사용:
    python verify_walk_symmetry.py [path/to/h0_walk]
"""
from __future__ import annotations
import sys, pathlib
from PIL import Image, ImageChops


def diff_score(a: Image.Image, b: Image.Image) -> float:
    da = ImageChops.difference(a, b)
    px = list(da.getdata())
    return sum(p[0] + p[1] + p[2] + p[3] for p in px) / len(px)


def main(argv: list[str]) -> int:
    src = pathlib.Path(argv[1] if len(argv) > 1
                       else 'android/app/src/main/assets/sprites/hero/h0_walk')
    print(f'analyzing {src}')
    print('Symmetry score (dir{i} flipped vs dir{j}, lower = stronger mirror)')
    print('             dir0   dir1   dir2   dir3')
    best = (1e9, -1, -1)
    for i in range(4):
        a = Image.open(src / f'dir{i}_0.png').convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT)
        row = [f'dir{i}f:']
        for j in range(4):
            b = Image.open(src / f'dir{j}_0.png').convert('RGBA')
            s = diff_score(a, b)
            row.append(f'{s:6.1f}')
            if i != j and s < best[0]:
                best = (s, i, j)
        print(' '.join(row))
    print(f'\nstrongest mirror pair: dir{best[1]} <-> dir{best[2]} (score {best[0]:.1f})')
    print(f'=> {best[1]} / {best[2]} = LEFT / RIGHT (orientation 미정)')
    print(f'   나머지 {sorted(set(range(4)) - {best[1], best[2]})} = DOWN / UP')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
