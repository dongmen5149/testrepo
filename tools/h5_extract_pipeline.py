"""Hero5 자산 추출 → Godot 임포트 통합 파이프라인.

처음부터 복원하는 새 클론에서 한 번에 실행 가능.
필수: ``Hero5/영웅서기5(최신폰전용).apk`` 가 있어야 한다.
권장: ``pip install lief capstone Pillow`` (capstone+lief 가 있으면 P1/P2
의 .so 자동 분석 단계가 같이 돌아 ``opcode_table.json`` 77/77 이 만들어짐).

기본 동작은 누락된 단계만 채우는 incremental run. ``--force`` 로 전체 재실행.
"""
from __future__ import annotations
import argparse, importlib.util, pathlib, runpy, shutil, subprocess, sys, time
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
APK = ROOT / "Hero5" / "영웅서기5(최신폰전용).apk"
WORK = ROOT / "work" / "h5"
EXTRACTED = WORK / "extracted"
VFS_ENTRIES = WORK / "vfs_entries"
ANALYSIS = WORK / "analysis"
CONVERTED = WORK / "converted"
GODOT_ASSETS = ROOT / "apps" / "hero5-godot" / "assets"

# 단계별 (id, 표시명, sentinel 경로 리스트, 실행 함수)
def _has(*paths: pathlib.Path) -> bool:
    return all(p.exists() for p in paths)


def _step_unzip_apk(force: bool) -> None:
    sentinel = EXTRACTED / "lib" / "armeabi" / "libHeroesLore5.so"
    if sentinel.exists() and not force:
        return
    if not APK.exists():
        raise FileNotFoundError(f"APK 없음: {APK}")
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(APK) as z:
        z.extractall(EXTRACTED)


def _run_module(rel: str) -> None:
    """tools/<rel>.py 를 main 으로 실행."""
    runpy.run_path(str(ROOT / rel), run_name="__main__")


def _step_vfs(force: bool) -> None:
    if (WORK / "vfs_catalog.tsv").exists() and not force:
        return
    _run_module("tools/h5_vfs_unpack.py")


def _step_names(force: bool) -> None:
    if (ANALYSIS / "asset_names.tsv").exists() and not force:
        return
    _run_module("tools/h5_recover_names.py")


def _step_sprite(force: bool) -> None:
    if (CONVERTED / "sprites").exists() and (CONVERTED / "palettes").exists() and not force:
        return
    _run_module("tools/h5_batch_sprite.py")


def _step_text(force: bool) -> None:
    if (CONVERTED / "text" / "_corpus.txt").exists() and not force:
        return
    _run_module("tools/h5_extract_text.py")


def _step_converters(force: bool) -> None:
    """tools/converter/{convert,decode}_h5_*.py 일괄 — argv 가 필요한 두 개는 제외."""
    skip = {"convert_h5_pa.py", "convert_h5_sprite.py"}
    cdir = ROOT / "tools" / "converter"
    targets = sorted([p for p in cdir.glob("convert_h5_*.py") if p.name not in skip])
    targets += sorted(cdir.glob("decode_h5_*.py"))
    for p in targets:
        try:
            subprocess.run([sys.executable, str(p)], check=False,
                           cwd=str(ROOT), stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=300)
        except Exception as e:
            print(f"  [warn] {p.name}: {e}")


def _step_disasm(force: bool) -> None:
    """capstone+lief 있으면 .so 자동 분석 (P1/P2)."""
    if importlib.util.find_spec("capstone") is None or importlib.util.find_spec("lief") is None:
        print("  [skip] capstone/lief 없음 — opcode_table 38 fallback 사용")
        return
    for rel, sentinel in [
        ("tools/h5_extract_opcode_disasm.py", ANALYSIS / "opcode_table.tsv"),
        ("tools/h5_event_arg_sizes.py", ANALYSIS / "event_arg_sizes.tsv"),
        ("tools/h5_extract_enemy_layout.py", ANALYSIS / "enemy_g_layout.tsv"),
    ]:
        if sentinel.exists() and not force:
            continue
        try:
            _run_module(rel)
        except SystemExit:
            pass
        except Exception as e:
            print(f"  [warn] {rel}: {e}")


def _step_godot(force: bool) -> None:
    _run_module("tools/import_to_godot.py")


def _step_verify(force: bool) -> None:
    _run_module("tools/verify_godot_project.py")


STEPS = [
    ("apk",       "APK unzip",                 _step_unzip_apk),
    ("vfs",       "VFS unpack",                _step_vfs),
    ("names",     "asset name recover",        _step_names),
    ("sprite",    "sprite + palette decode",   _step_sprite),
    ("text",      "한글 코퍼스",                _step_text),
    ("converters","converter/decoder 일괄",    _step_converters),
    ("disasm",    ".so disasm (capstone+lief)", _step_disasm),
    ("godot",     "Godot 임포트",               _step_godot),
    ("verify",    "Godot reference 검증",       _step_verify),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="sentinel 무시하고 모든 단계 재실행")
    ap.add_argument("--only", nargs="+", choices=[s[0] for s in STEPS],
                    help="지정한 단계만 실행")
    ap.add_argument("--skip", nargs="+", choices=[s[0] for s in STEPS],
                    default=[], help="지정한 단계는 건너뜀")
    args = ap.parse_args()

    selected = [s for s in STEPS
                if (not args.only or s[0] in args.only) and s[0] not in args.skip]

    print(f"=== Hero5 extract pipeline — {len(selected)} steps ===\n")
    t0 = time.time()
    for sid, name, fn in selected:
        print(f"[{sid}] {name} ...")
        ts = time.time()
        try:
            fn(args.force)
        except SystemExit:
            pass
        except Exception as e:
            print(f"  [error] {sid}: {e}")
            return 1
        print(f"    done in {time.time()-ts:.1f}s\n")

    print(f"=== all done in {time.time()-t0:.1f}s ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
