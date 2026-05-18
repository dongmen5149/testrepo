"""Round 67 — Battle motion enum + CHAR state machine RE 검증.

R50 의 HOST_MOTION 가설 (walk=1, die=9 등) 이 .so 디스어셈블 결과 잘못 확인.
실제 motion enum (CHAR::SetMotion 의 인자) + main_state enum 정정.

검증 항목:
  1. ELF symbol 6종 cross-verify (CHAR::SetMotion / GetMotion / Set*State / SetWalkMotion 등)
  2. CHAR struct offset 확인 (+0x2c motion, +0x2d dir, +0x2e frame, +0xc4/c5/c6 cache)
  3. character.gd 의 SO_MAIN_STATE_* / SO_MOTION_* 상수 추가 검증
  4. R50 → R67 가설 정정 표 cross-check
  5. R50 의 HOST_MOTION_* 는 logical code 로 유지 (Godot 내부) — docstring 정정
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHAR_GD = ROOT / "apps/hero5-godot/scripts/core/character.gd"
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
RE_DOC = ROOT / "docs/h5/RE/battle_motion.md"


def main() -> None:
    print("# Round 67 Battle motion enum RE 검증\n")
    for p in (CHAR_GD, RE_DOC):
        assert p.exists(), f"missing {p}"

    # 1. ELF symbol cross-verify
    print("# 1. ELF symbol cross-verify (motion setter 6종)")
    if not SO_PATH.exists():
        print(f"  [skip] {SO_PATH} 미발견")
    else:
        try:
            import lief  # type: ignore
            b = lief.parse(str(SO_PATH))
            targets = {
                "_ZN4CHAR9SetMotionEa": (0x4af5c, 56, "CHAR::SetMotion"),
                "_ZN4CHAR9GetMotionEv": (0x49b74, 8, "CHAR::GetMotion"),
                "_ZN4CHAR12SetMainStateEa": (0x49b5c, 8, "CHAR::SetMainState"),
                "_ZN4CHAR6SetDirEa": (0x49b7c, 8, "CHAR::SetDir"),
                "_ZN4CHAR11GetMaxFrameEaa": (0x4af34, 40, "CHAR::GetMaxFrame"),
                "_ZN4HERO12SetNextStateEa": (0x88940, 16, "HERO::SetNextState"),
                "_ZN4HERO13SetWalkMotionEa": (0x98f6c, 116, "HERO::SetWalkMotion"),
                "_ZN4HERO15SetAttackMotionEaa": (0x98870, 160, "HERO::SetAttackMotion"),
                "_ZN4HERO17SetAttackedMotionEaa": (0x98e58, 112, "HERO::SetAttackedMotion"),
                "_ZN4HERO12SetDieMotionEv": (0x98dd8, 128, "HERO::SetDieMotion"),
            }
            n_ok = 0
            for sym in b.symbols:
                name = sym.name or ""
                if name in targets:
                    exp_addr, exp_size, label = targets[name]
                    got_addr = int(sym.value) & ~1
                    got_size = int(sym.size)
                    ok = got_addr == exp_addr and got_size == exp_size
                    if ok:
                        n_ok += 1
                        print(f"  ✓ {label}: addr=0x{got_addr:x} size={got_size}")
                    else:
                        print(f"  ✗ {label}: addr=0x{got_addr:x} size={got_size} "
                              f"(expect 0x{exp_addr:x}/{exp_size})")
            # 각 symbol 두 번 (symtab+dynsym) 잡힐 수 있음 — len >= unique × 1
            unique_n = len(targets)
            assert n_ok >= unique_n, f"{unique_n} unique symbol 필요 ({n_ok}/{unique_n})"
            print(f"  ✓ {unique_n}/{unique_n} symbol 모두 disasm 결과 일치")
        except ImportError:
            print(f"  [skip] lief 미설치")
    print()

    # 2. R50 → R67 가설 정정 표
    print("# 2. R50 가설 → R67 RE 정정")
    corrections = [
        ("WALK motion", 1, 3, "SetWalkMotion 의 mov r1, #3; bl SetMotion"),
        ("DIE motion", 9, 5, "SetDieMotion 의 mov r1, #5; bl SetMotion"),
        ("ATTACK motion", 6, "variable", "SetAttackMotion 의 mov r1, r5 (caller arg)"),
        ("ATTACKED motion", "(없음)", "variable", "SetAttackedMotion 의 mov r1, r5 (caller arg)"),
        ("WALK main_state", "(없음)", 1, "SetWalkMotion 의 mov r1, #1; bl SetMainState"),
        ("ATTACK main_state", "(없음)", 2, "SetAttackMotion 의 mov r1, #2; bl SetMainState"),
        ("ATTACKED main_state", "(없음)", 3, "SetAttackedMotion 의 mov r1, #3; bl SetMainState"),
        ("DIE main_state", "(없음)", 4, "SetDieMotion 의 mov r1, #4; bl SetMainState"),
    ]
    for desc, before, after, evidence in corrections:
        print(f"  {desc}: R50={before!s:8s} → R67={after!s:8s}  ({evidence})")
    print()

    # 3. character.gd 의 SO_* 상수 추가 검증
    print("# 3. character.gd 의 SO_* 상수 + R67 docstring")
    src = CHAR_GD.read_text(encoding="utf-8")
    checks = [
        (r"SO_MAIN_STATE_IDLE\s*:=\s*0", "SO_MAIN_STATE_IDLE = 0"),
        (r"SO_MAIN_STATE_WALK\s*:=\s*1", "SO_MAIN_STATE_WALK = 1"),
        (r"SO_MAIN_STATE_ATTACK\s*:=\s*2", "SO_MAIN_STATE_ATTACK = 2"),
        (r"SO_MAIN_STATE_ATTACKED\s*:=\s*3", "SO_MAIN_STATE_ATTACKED = 3"),
        (r"SO_MAIN_STATE_DIE\s*:=\s*4", "SO_MAIN_STATE_DIE = 4"),
        (r"SO_MOTION_WALK\s*:=\s*3", "SO_MOTION_WALK = 3 (R50 의 1 가설 정정)"),
        (r"SO_MOTION_DIE\s*:=\s*5", "SO_MOTION_DIE = 5 (R50 의 9 가설 정정)"),
        (r"R67 RE", "R67 RE 마커 docstring"),
        (r"R50.*잘못|잘못 확인", "R50 가설 잘못 확인 docstring"),
    ]
    failed = 0
    for pat, desc in checks:
        if re.search(pat, src):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} — {pat!r} not found")
            failed += 1
    assert failed == 0, f"{failed} 패턴 누락"
    print()

    # 4. R50 의 HOST_MOTION_* 유지 검증 (logical code, monster_ai 호환)
    print("# 4. R50 의 HOST_MOTION_* 유지 (Godot 내부 logical code)")
    legacy_checks = [
        (r"HOST_MOTION_IDLE\s*:=\s*0", "HOST_MOTION_IDLE 유지"),
        (r"HOST_MOTION_WALK\s*:=\s*1", "HOST_MOTION_WALK 유지 (logical)"),
        (r"HOST_MOTION_DIE\s*:=\s*9", "HOST_MOTION_DIE 유지 (logical)"),
    ]
    for pat, desc in legacy_checks:
        if re.search(pat, src):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} — 누락")
            assert False
    print()

    # 5. CHAR struct offset RE 문서 검증
    print("# 5. CHAR struct offset RE 문서")
    doc = RE_DOC.read_text(encoding="utf-8")
    doc_checks = [
        ("+0x2c = motion", "+0x2c motion field"),
        ("+0x2d = dir", "+0x2d dir field"),
        ("+0x2e = frame", "+0x2e frame field (u16)"),
        ("+0xc4", "+0xc4 motion_change_flag"),
        ("+0xc5", "+0xc5 prev_frame_low"),
        ("+0xc6", "+0xc6 max_frame_current"),
        ("CHAR::SetMotion @ 0x4af5c", "SetMotion 주소 확정"),
        ("WALK motion | 1 | **3**", "R50 walk 가설 정정"),
        ("DIE motion | 9 | **5**", "R50 die 가설 정정"),
    ]
    for token, desc in doc_checks:
        if token in doc:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} — {token!r} not in RE doc")
            assert False
    print()

    print("# All Round 67 Battle motion RE checks passed.")


if __name__ == "__main__":
    main()
