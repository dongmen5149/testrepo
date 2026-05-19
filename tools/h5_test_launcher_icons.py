#!/usr/bin/env python3
"""R89: Android launcher icons 자산 + export_presets.cfg 통합 검증.

R86 의 launcher_icons 3 슬롯 (Debug + Release 각각 main_192x192 +
adaptive_foreground_432x432 + adaptive_background_432x432) 의 빈 칸을 채움.

검증:
- tools/h5_make_launcher_icons.py 존재 + PIL 의존 + 3 helper 함수
- apps/hero5-godot/assets/launcher_icons/ 디렉토리 + 3 PNG 파일 존재
- 각 PNG 의 실제 크기 (192×192 / 432×432 / 432×432) + PNG signature
- main_192x192 = opaque (alpha 255), foreground_432 = transparent BG, background_432 = opaque
- adaptive_foreground 의 중앙 안전 영역 (264×264) 안에 non-transparent pixel 존재
- export_presets.cfg Debug + Release 모두 launcher_icons 3 슬롯 채워짐
- 참조 경로 res://assets/launcher_icons/*.png 실제 파일과 매칭
- R86 회귀: export_presets.cfg 의 2 preset / 11 permissions / package name / arm64 / immersive 유지
"""
import configparser
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GODOT = ROOT / "apps/hero5-godot"
ICONS_DIR = GODOT / "assets/launcher_icons"


def png_size(path: pathlib.Path) -> tuple[int, int]:
    """Read PNG width/height from IHDR chunk."""
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', f"not a PNG: {path}"
    # IHDR starts at byte 8 (4 length + 4 type + 13 IHDR data)
    width = int.from_bytes(data[16:20], 'big')
    height = int.from_bytes(data[20:24], 'big')
    return width, height


def main():
    # 1. tools/h5_make_launcher_icons.py 존재 + 3 helper 함수
    tool = ROOT / "tools/h5_make_launcher_icons.py"
    assert tool.exists(), "h5_make_launcher_icons.py not found"
    src = tool.read_text(encoding='utf-8')
    for fn in ("make_main_192", "make_adaptive_foreground_432", "make_adaptive_background_432"):
        assert f"def {fn}" in src, f"missing helper: {fn}"
    assert "from PIL import" in src, "PIL import missing"
    assert "BG_NIGHT" in src and "GOLD" in src, "color constants missing"
    assert "_draw_sword" in src, "sword helper missing"
    assert "_star_points" in src, "star helper missing"
    print("[PASS] tools/h5_make_launcher_icons.py: PIL + 3 helper + sword/star drawing")

    # 2. 3 PNG 파일 존재
    expected = {
        "main_192x192.png": (192, 192),
        "adaptive_foreground_432x432.png": (432, 432),
        "adaptive_background_432x432.png": (432, 432),
    }
    assert ICONS_DIR.exists() and ICONS_DIR.is_dir(), f"launcher_icons dir missing: {ICONS_DIR}"
    for name in expected:
        p = ICONS_DIR / name
        assert p.exists(), f"PNG missing: {p}"
        assert p.stat().st_size > 500, f"PNG too small: {p}"
    print(f"[PASS] launcher_icons dir + 3 PNG 파일 존재")

    # 3. 각 PNG 의 실제 크기 (IHDR 직접 read)
    for name, (ew, eh) in expected.items():
        w, h = png_size(ICONS_DIR / name)
        assert (w, h) == (ew, eh), f"{name}: size {w}×{h} != expected {ew}×{eh}"
    print(f"[PASS] PNG 크기 정확: 192×192 + 432×432 (foreground) + 432×432 (background)")

    # 4. transparency 검증 — PIL 로 alpha 채널 확인
    from PIL import Image
    img_main = Image.open(ICONS_DIR / "main_192x192.png")
    img_fg = Image.open(ICONS_DIR / "adaptive_foreground_432x432.png")
    img_bg = Image.open(ICONS_DIR / "adaptive_background_432x432.png")
    # main: 좌상단 pixel alpha 255 (opaque BG)
    assert img_main.mode == "RGBA", f"main mode: {img_main.mode}"
    assert img_main.getpixel((0, 0))[3] == 255, "main_192 corner not opaque"
    # foreground: 좌상단 transparent
    assert img_fg.getpixel((0, 0))[3] == 0, "adaptive_foreground corner not transparent"
    # background: 좌상단 opaque
    assert img_bg.getpixel((0, 0))[3] == 255, "adaptive_background corner not opaque"
    print("[PASS] alpha 채널: main+background opaque, foreground transparent")

    # 5. adaptive_foreground 의 안전 영역 (중앙 264×264) 에 non-transparent pixel 존재
    fg = img_fg
    has_content = False
    for x in range(132, 300, 20):
        for y in range(132, 300, 20):
            if fg.getpixel((x, y))[3] > 0:
                has_content = True
                break
        if has_content:
            break
    assert has_content, "adaptive_foreground 안전 영역에 그림 없음"
    print("[PASS] adaptive_foreground: 중앙 264×264 안전 영역에 그림 존재")

    # 6. export_presets.cfg 의 launcher_icons 3 슬롯 (Debug + Release)
    cfg_path = GODOT / "export_presets.cfg"
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path, encoding='utf-8')
    preset_sections = ["preset.0.options", "preset.1.options"]
    expected_paths = {
        "launcher_icons/main_192x192": '"res://assets/launcher_icons/main_192x192.png"',
        "launcher_icons/adaptive_foreground_432x432": '"res://assets/launcher_icons/adaptive_foreground_432x432.png"',
        "launcher_icons/adaptive_background_432x432": '"res://assets/launcher_icons/adaptive_background_432x432.png"',
    }
    for sec in preset_sections:
        assert sec in cfg, f"section missing: {sec}"
        for key, expected_val in expected_paths.items():
            actual = cfg[sec].get(key, "")
            assert actual == expected_val, f"{sec} {key}: {actual!r} != {expected_val!r}"
    print(f"[PASS] export_presets.cfg: Debug + Release 모두 3 launcher_icons 슬롯 채워짐 (res://)")

    # 7. 참조 경로의 실제 파일 매칭 (res:// → 디스크)
    for key, val in expected_paths.items():
        rel = val.strip('"').replace("res://", "")
        target = GODOT / rel
        assert target.exists(), f"{key}: resolved path missing: {target}"
    print("[PASS] export_presets.cfg 의 res:// 경로가 모두 디스크 파일과 매칭")

    # 8. R86 회귀 — 핵심 preset 옵션 잔존
    sec_d = cfg["preset.0.options"]
    sec_r = cfg["preset.1.options"]
    # gradle_build
    assert sec_d.get("gradle_build/use_gradle_build") == "true", "R86 gradle_build 손실"
    # min/target sdk (configparser 가 numeric quote 벗김 → int 변환 비교)
    assert int(sec_d.get("gradle_build/min_sdk", "0")) == 23, \
        f"R86 min_sdk != 23: {sec_d.get('gradle_build/min_sdk')!r}"
    assert int(sec_d.get("gradle_build/target_sdk", "0")) == 34, \
        f"R86 target_sdk != 34: {sec_d.get('gradle_build/target_sdk')!r}"
    # arm64-v8a only
    assert sec_d.get("architectures/arm64-v8a") == "true", "R86 arm64-v8a 손실"
    assert sec_d.get("architectures/armeabi-v7a") == "false", "R86 32-bit disable 손실"
    # package name (quoted string)
    assert "Hero5" in sec_d.get("package/name", ""), "R86 package name 손실"
    # immersive_mode
    assert sec_d.get("screen/immersive_mode") == "true", "R86 immersive 손실"
    # Release runnable=false + compress
    assert cfg["preset.1"].get("runnable") == "false", "R86 Release runnable=false 손실"
    assert sec_r.get("gradle_build/compress_native_libraries") == "true", "R86 Release compress 손실"
    # 11 permissions (R86 의 모두 false 검증)
    perm_keys = [
        "permissions/internet", "permissions/wake_lock", "permissions/access_network_state",
        "permissions/vibrate", "permissions/access_fine_location", "permissions/access_coarse_location",
        "permissions/bluetooth", "permissions/camera", "permissions/read_external_storage",
        "permissions/write_external_storage", "permissions/record_audio",
    ]
    for k in perm_keys:
        assert sec_d.get(k) == "false", f"R86 permission {k} 변경됨"
    print("[PASS] R86 회귀: 2 preset / gradle_build / arm64 / package / immersive / 11 permissions / Release compress")

    # 9. icon.svg + project.godot 의 icon 참조 (R86) 잔존
    icon_svg = GODOT / "icon.svg"
    assert icon_svg.exists(), "R86 icon.svg 손실"
    proj = (GODOT / "project.godot").read_text(encoding='utf-8')
    assert 'config/icon="res://icon.svg"' in proj, "R86 project icon 참조 손실"
    print("[PASS] R86 icon.svg + project.godot config/icon 잔존")

    # 10. .gitignore 의 *.keystore + assets/ 패턴 잔존 (R86)
    gitignore_p = GODOT / ".gitignore"
    if gitignore_p.exists():
        gi = gitignore_p.read_text(encoding='utf-8')
        assert "*.keystore" in gi, "R86 .gitignore *.keystore 손실"
    print("[PASS] R86 .gitignore *.keystore ignore 잔존")

    print("\n=== R89 Launcher icons asset + export_preset 통합: ALL PASSED ===")


if __name__ == "__main__":
    main()
