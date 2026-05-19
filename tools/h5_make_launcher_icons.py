"""
Hero5 (영웅서기5) Android launcher icons 생성기 (R89).

R86 export_presets.cfg 의 launcher_icons 3 슬롯 (Debug + Release 각각) 의 빈 칸을
채우기 위한 PNG 자산 생성. icon.svg 디자인을 PIL 로 재현.

생성물 (assets/launcher_icons/):
  - main_192x192.png            : legacy launcher (Android API <26), 검정 BG + 원 + 검 + 별 + "HERO 5"
  - adaptive_foreground_432x432.png : adaptive icon 전경 레이어, 안전영역 (264×264 중앙) 안의 검 + 별 (BG 투명)
  - adaptive_background_432x432.png : adaptive icon 배경 레이어, 검정+자주 BG + 황금 테두리

Adaptive icon 시스템 (Android 8.0+):
  - 432×432 전체 중 시스템이 임의 마스크 적용 (원/사각/물방울 등)
  - 안전 영역 = 중앙 264×264 (외곽 84px 마진 가려질 수 있음)
  - foreground = 로고 (안전영역 안), background = 단색/패턴

색상 (icon.svg 매칭):
  BG_NIGHT     = #1a1a2e (검정 자주)
  RING_BLUE    = #2d2d5f (원 채움)
  GOLD         = #e8c468 (별/텍스트)
  GOLD_DARK    = #c89a3a (별 윤곽)
  SILVER       = #c0c0d0 (검 블레이드)
  HILT_BROWN   = #8b5a2b (크로스가드)
  HILT_DARK    = #6b3e1c (손잡이)

사용:
  python tools/h5_make_launcher_icons.py
  → apps/hero5-godot/assets/launcher_icons/*.png 3 개 생성
"""
from __future__ import annotations
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "apps" / "hero5-godot" / "assets" / "launcher_icons"

BG_NIGHT = (26, 26, 46, 255)
RING_BLUE = (45, 45, 95, 255)
GOLD = (232, 196, 104, 255)
GOLD_DARK = (200, 154, 58, 255)
SILVER = (192, 192, 208, 255)
HILT_BROWN = (139, 90, 43, 255)
HILT_DARK = (107, 62, 28, 255)


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVu-Sans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for p in candidates:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _star_points(cx: int, cy: int, r_outer: int, r_inner: int) -> list[tuple[int, int]]:
    """5-pointed star centered at (cx, cy)."""
    import math
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))
    return pts


def _draw_sword(d: ImageDraw.ImageDraw, cx: int, top: int, length: int, width: int,
                color_blade=SILVER, color_hilt=HILT_BROWN, color_grip=HILT_DARK,
                color_tip=GOLD) -> None:
    """수직 검 (cx 중심선, top 상단)."""
    blade_h = int(length * 0.66)
    cross_y = top + blade_h
    cross_h = max(4, int(width * 0.6))
    grip_h = length - blade_h - cross_h
    half = width // 2
    cross_half = int(width * 2.3)
    # Blade
    d.rectangle((cx - half, top + max(2, width // 2), cx + half, cross_y), fill=color_blade)
    # Tip triangle
    tip_h = max(6, width)
    d.polygon([(cx, top), (cx - half - 1, top + tip_h), (cx + half + 1, top + tip_h)],
              fill=color_tip)
    # Crossguard
    d.rectangle((cx - cross_half, cross_y, cx + cross_half, cross_y + cross_h), fill=color_hilt)
    # Grip
    grip_half = max(2, width // 2 - 1)
    d.rectangle((cx - grip_half, cross_y + cross_h,
                 cx + grip_half, cross_y + cross_h + grip_h), fill=color_grip)


def make_main_192() -> Image.Image:
    """Legacy launcher icon (Android API <26)."""
    size = 192
    img = Image.new("RGBA", (size, size), BG_NIGHT)
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Ring (filled circle + gold outline)
    r = 84
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RING_BLUE, outline=GOLD, width=4)
    # Sword (vertical, centered)
    sword_top = 30
    sword_len = 100
    _draw_sword(d, cx, sword_top, length=sword_len, width=12)
    # Star (top-right)
    star_pts = _star_points(cx + 42, cy - 48, r_outer=15, r_inner=7)
    d.polygon(star_pts, fill=GOLD, outline=GOLD_DARK)
    # "HERO 5" text (bottom)
    font = _load_font(22)
    text = "HERO 5"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((cx - tw // 2, size - th - 12), text, fill=GOLD, font=font)
    return img


def make_adaptive_foreground_432() -> Image.Image:
    """Adaptive icon foreground (Android API 26+).

    432×432 캔버스, 안전영역 = 중앙 264×264 (외곽 84px 마진).
    BG 는 transparent (system 이 background layer 와 합성).
    """
    size = 432
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))   # transparent
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # Sword (안전영역 264 내부에 들어가도록 크기 조절)
    sword_top = cy - 110
    sword_len = 220
    _draw_sword(d, cx, sword_top, length=sword_len, width=24)
    # Star
    star_pts = _star_points(cx + 85, cy - 95, r_outer=30, r_inner=14)
    d.polygon(star_pts, fill=GOLD, outline=GOLD_DARK)
    # "5" 큰 문자 (안전영역 안 좌하단)
    font = _load_font(48)
    text = "5"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((cx - 80 - tw // 2, cy + 50), text, fill=GOLD, font=font)
    return img


def make_adaptive_background_432() -> Image.Image:
    """Adaptive icon background (Android API 26+).

    432×432 단색 (검정-자주) + 황금 테두리 원 (안전영역 표시).
    """
    size = 432
    img = Image.new("RGBA", (size, size), BG_NIGHT)
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    # 큰 어두운 원 (전체 배경 위에 layered)
    d.ellipse((cx - 200, cy - 200, cx + 200, cy + 200), fill=RING_BLUE)
    # 황금 테두리 원 (안전영역 264×264 = r 132 부근)
    d.ellipse((cx - 135, cy - 135, cx + 135, cy + 135), outline=GOLD, width=6)
    return img


def main(argv: list[str]) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        ("main_192x192.png", make_main_192),
        ("adaptive_foreground_432x432.png", make_adaptive_foreground_432),
        ("adaptive_background_432x432.png", make_adaptive_background_432),
    ]
    for name, fn in outputs:
        img = fn()
        path = OUT_DIR / name
        img.save(path, format="PNG", optimize=True)
        print(f"  {path.relative_to(ROOT)}  ({img.size[0]}×{img.size[1]}, {path.stat().st_size}B)")
    print(f"generated {len(outputs)} launcher icons → {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
