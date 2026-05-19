#!/usr/bin/env python3
"""R86: Android export preset 정합성 검증 (G 카테고리 35→55%).

검증 항목:
- export_presets.cfg 존재 + 2 preset (Debug + Release)
- 필수 옵션 (gradle_build, target_sdk, min_sdk, version, package name)
- 아키텍처 (arm64-v8a only, 32-bit + x86_64 false)
- Permissions (모두 false — 싱글 플레이)
- Release 의 compress_native_libraries=true
- icon.svg 존재 (project.godot 의 res://icon.svg 참조 만족)
- .gitignore 에 export_presets.cfg ignore 제거 (commit 허용)
- BUILD_ANDROID.md 문서
"""
import configparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def main():
    # 1. export_presets.cfg 존재
    cfg_path = GODOT / "export_presets.cfg"
    assert cfg_path.exists(), "export_presets.cfg 미존재"
    print(f"[PASS] export_presets.cfg 존재 ({cfg_path.stat().st_size} bytes)")

    # 2. INI parse
    cp = configparser.ConfigParser()
    cp.read(cfg_path, encoding='utf-8')
    sections = cp.sections()
    assert "preset.0" in sections, "preset.0 (Debug) 누락"
    assert "preset.0.options" in sections, "preset.0.options 누락"
    assert "preset.1" in sections, "preset.1 (Release) 누락"
    assert "preset.1.options" in sections, "preset.1.options 누락"
    print(f"[PASS] 2 preset 발견 (Debug + Release) — 총 {len(sections)} sections")

    # 3. preset.0 (Debug) 필수 필드
    p0 = cp["preset.0"]
    assert p0.get("name", "").strip('"') == "Android (Debug)", f"Debug name mismatch: {p0.get('name')}"
    assert p0.get("platform", "").strip('"') == "Android", "Debug platform != Android"
    assert p0.get("runnable") == "true", "Debug runnable != true"
    assert "Hero5-debug.apk" in p0.get("export_path", ""), "Debug export_path 미설정"
    print("[PASS] preset.0 (Debug): name + platform + runnable + export_path")

    # 4. preset.0.options gradle_build
    p0o = cp["preset.0.options"]
    assert p0o.get("gradle_build/use_gradle_build") == "true", "Debug gradle_build off"
    assert int(p0o.get("gradle_build/min_sdk", "0")) == 23, \
        f"Debug min_sdk != 23 (Android 6.0): {p0o.get('gradle_build/min_sdk')}"
    assert int(p0o.get("gradle_build/target_sdk", "0")) == 34, \
        f"Debug target_sdk != 34 (Android 14): {p0o.get('gradle_build/target_sdk')}"
    print("[PASS] Debug gradle_build: use=true / min_sdk=23 (Android 6.0) / target_sdk=34 (Android 14)")

    # 5. Architecture: arm64-v8a only
    assert p0o.get("architectures/arm64-v8a") == "true", "Debug arm64-v8a off"
    assert p0o.get("architectures/armeabi-v7a") == "false", "Debug armeabi-v7a (32-bit) 켜져 있음"
    assert p0o.get("architectures/x86_64") == "false", "Debug x86_64 켜져 있음"
    print("[PASS] Architecture: arm64-v8a only (32-bit + x86_64 disabled)")

    # 6. Package + version
    assert "heroeslore5" in p0o.get("package/unique_name", ""), "package unique_name 미설정"
    assert "Hero5" in p0o.get("package/name", ""), "package name 미설정"
    assert int(p0o.get("version/code", "0")) >= 1, "version/code missing"
    assert "0.1" in p0o.get("version/name", ""), "version/name (semver) missing"
    print(f"[PASS] Package: {p0o.get('package/unique_name')} {p0o.get('package/name')} v{p0o.get('version/name')}")

    # 7. Permissions: 모두 false (싱글 플레이, 외부 통신 없음)
    perm_keys = [k for k in p0o.keys() if k.startswith("permissions/")]
    assert len(perm_keys) >= 8, f"permissions 항목 ≥8 필요, got {len(perm_keys)}"
    for k in perm_keys:
        assert p0o.get(k) == "false", f"unexpected permission ENABLED: {k} = {p0o.get(k)}"
    print(f"[PASS] All {len(perm_keys)} permissions disabled (싱글 플레이, no network/storage/camera)")

    # 8. preset.1 (Release) 차이점: compress_native_libraries=true + runnable=false
    p1 = cp["preset.1"]
    p1o = cp["preset.1.options"]
    assert p1.get("name", "").strip('"') == "Android (Release)", "Release name mismatch"
    assert p1.get("runnable") == "false", "Release runnable should be false"
    assert "Hero5-release.apk" in p1.get("export_path", ""), "Release export_path 미설정"
    assert p1o.get("gradle_build/compress_native_libraries") == "true", \
        "Release compress_native_libraries off (size 절감 누락)"
    # Same gradle setup
    assert p1o.get("gradle_build/use_gradle_build") == "true", "Release gradle off"
    assert int(p1o.get("gradle_build/target_sdk", "0")) == 34, "Release target_sdk != 34"
    print("[PASS] preset.1 (Release): runnable=false + compress_native_libraries=true (size 절감)")

    # 9. Immersive mode (system bar 숨김)
    assert p0o.get("screen/immersive_mode") == "true", "Debug immersive_mode off"
    assert p1o.get("screen/immersive_mode") == "true", "Release immersive_mode off"
    print("[PASS] Both presets: immersive_mode=true (system bar 숨김)")

    # 10. icon.svg 존재 + 내용
    icon_path = GODOT / "icon.svg"
    assert icon_path.exists(), "icon.svg 미존재 (project.godot 의 res://icon.svg 참조)"
    icon_content = icon_path.read_text(encoding='utf-8')
    assert "<svg" in icon_content and "</svg>" in icon_content, "icon.svg 형식 오류"
    assert "HERO" in icon_content or "Hero" in icon_content, "icon 에 HERO 텍스트 없음"
    print(f"[PASS] icon.svg 존재 ({icon_path.stat().st_size} bytes, HERO 5 logo)")

    # 11. project.godot 의 icon 참조 일치
    proj = (GODOT / "project.godot").read_text(encoding='utf-8')
    assert 'config/icon="res://icon.svg"' in proj, "project.godot icon 참조 미일치"
    print("[PASS] project.godot 의 icon 참조 = res://icon.svg (R86 icon.svg 일치)")

    # 12. .gitignore: export_presets.cfg commit 허용 + *.keystore ignore
    gi = (GODOT / ".gitignore").read_text(encoding='utf-8')
    assert "export_presets.cfg" not in gi or "Round 86" in gi, \
        ".gitignore 에 export_presets.cfg 잔존 (Round 86 주석 없음)"
    assert "*.keystore" in gi, ".gitignore 에 *.keystore 보안 미설정"
    print("[PASS] .gitignore: export_presets.cfg commit 허용 + *.keystore ignore (보안)")

    # 13. BUILD_ANDROID.md
    build_doc = ROOT / "docs/h5/BUILD_ANDROID.md"
    assert build_doc.exists(), "docs/h5/BUILD_ANDROID.md 미존재"
    content = build_doc.read_text(encoding='utf-8')
    markers = [
        "Round 86", "JDK", "Android SDK", "NDK",
        "Install Android Build Template", "export_presets.cfg",
        "Debug", "Release", "keystore", "Hero5-debug.apk", "Hero5-release.apk",
        "adb install", "R82", "R83", "R84", "R85",
        "min_sdk", "target_sdk", "arm64-v8a", "permissions",
    ]
    missing = [m for m in markers if m not in content]
    assert not missing, f"BUILD_ANDROID.md markers missing: {missing}"
    print(f"[PASS] BUILD_ANDROID.md: {len(markers)} doc markers (빌드 절차 + R82-R85 검증 + 차단 이슈)")

    print("\n=== R86 Android export preset + distribution build doc: ALL PASSED ===")


if __name__ == "__main__":
    main()
