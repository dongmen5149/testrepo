"""Round 68 — NPC Dialog 시스템 RE 검증.

`DIALOG_INFO::DialogWindow_Proc` (@0x71b48) 의 state machine + DIALOG_INFO struct
field layout + Event_SituateDialogText sub_state 분기를 .so 디스어셈블 결과로
재검증하고, docs/h5/RE/npc_dialog.md + apps/.../dialog_box.gd 의 상수가 RE 와
일치하는지 확인.

검증 항목:
  1. ELF symbol 9종 cross-verify (Event_DialogWindow / DialogWindow_Proc /
     Event_SituateDialogText / SetDialogWindow / SetFacePosition / GetNpcNameText /
     DrawDialogBox / NameBox / Strings::getString)
  2. DialogWindow_Proc 의 `cmp r2, #7` jumptable + `ldrsb r2, [r0, #0x2b]`
     state 진입 패턴 추출
  3. phase 진입별 strb pattern (+0x29 sub-step 증가 + +0x2d/+0x2f animation key)
  4. docs/h5/RE/npc_dialog.md 의 DIALOG_STATE_* / helper 주소 / phase data pool
     offset 표 일치 검증
  5. dialog_box.gd 의 8개 DIALOG_STATE_* 상수 + 3개 DIALOG_TRIGGER_* 상수 +
     DIALOG_SUBSTEP_FINAL=4 검증
  6. R67 PASS 1 추정 (state byte = +0x29) 가 R68 에서 +0x2b 로 정정된 docstring
     명시 확인
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DIALOG_GD = ROOT / "apps/hero5-godot/scripts/ui/dialog_box.gd"
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
RE_DOC = ROOT / "docs/h5/RE/npc_dialog.md"


def main() -> None:
    print("# Round 68 NPC Dialog 시스템 RE 검증\n")
    for p in (DIALOG_GD, RE_DOC):
        assert p.exists(), f"missing {p}"

    # 1. ELF symbol cross-verify
    print("# 1. ELF symbol cross-verify (Dialog 9종)")
    if not SO_PATH.exists():
        print(f"  [skip] {SO_PATH} 미발견")
    else:
        try:
            import lief  # type: ignore
            b = lief.parse(str(SO_PATH))
            targets = {
                "_ZN9EventProc18Event_DialogWindowEa":
                    (0x6eb38, 656, "EventProc::Event_DialogWindow"),
                "_ZN11DIALOG_INFO17DialogWindow_ProcEv":
                    (0x71b48, 912, "DIALOG_INFO::DialogWindow_Proc"),
                "_ZN9EventProc23Event_SituateDialogTextEhahh":
                    (0x73030, 600, "EventProc::Event_SituateDialogText"),
                "_ZN11DIALOG_INFO15SetDialogWindowEaa":
                    (0x6ab40, None, "DIALOG_INFO::SetDialogWindow"),
                "_ZN11DIALOG_INFO15SetFacePositionEha":
                    (0x72f54, None, "DIALOG_INFO::SetFacePosition"),
                "_ZN7TextMgr14GetNpcNameTextEi":
                    (0x1431a0, None, "TextMgr::GetNpcNameText"),
                "_ZN5GMenu13DrawDialogBoxEiiiiiah":
                    (0x8245c, None, "GMenu::DrawDialogBox"),
                "_ZN5GMenu7NameBoxEiiiiiPca":
                    (0x82248, None, "GMenu::NameBox"),
                "_ZN11Interpreter7Strings9getStringEiPi":
                    (0x9e540, None, "Interpreter::Strings::getString"),
            }
            found = {}
            for s in b.symbols:
                if s.name in targets:
                    found[s.name] = (int(s.value), int(s.size))
            for name, (expect_addr, expect_size, label) in targets.items():
                assert name in found, f"missing symbol: {name}"
                actual_addr, actual_size = found[name]
                actual_addr_clean = actual_addr & ~1
                assert actual_addr_clean == expect_addr, (
                    f"{label}: expected addr {expect_addr:#x}, got {actual_addr:#x}"
                )
                if expect_size is not None:
                    assert actual_size == expect_size, (
                        f"{label}: expected size {expect_size}, got {actual_size}"
                    )
                size_str = f"size={actual_size}" if expect_size else "(size N/A)"
                print(f"  ✓ {label}: addr={actual_addr:#x} {size_str}")
            print(f"  ✓ 9/9 symbol all match")

            # 2 & 3. DialogWindow_Proc 의 jumptable + phase strb 패턴 추출
            print("\n# 2. DialogWindow_Proc jumptable + state entry 패턴")
            try:
                from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
                addr, size = found["_ZN11DIALOG_INFO17DialogWindow_ProcEv"]
                thumb = bool(addr & 1)
                addr_aligned = addr & ~1
                file_offset = None
                for seg in b.segments:
                    if seg.virtual_address <= addr_aligned < seg.virtual_address + seg.virtual_size:
                        file_offset = seg.file_offset + (addr_aligned - seg.virtual_address)
                        break
                assert file_offset is not None
                with open(SO_PATH, "rb") as f:
                    f.seek(file_offset)
                    chunk = f.read(size)
                md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
                md.detail = True
                instrs = list(md.disasm(chunk, addr_aligned))

                # state byte 위치: ldrsb r2, [r0, #0x2b]
                state_byte_load = [
                    ins for ins in instrs
                    if ins.mnemonic == "ldrsb" and "[r0, #0x2b]" in ins.op_str
                ]
                assert state_byte_load, "ldrsb r2, [r0, #0x2b] 패턴 미발견 (state byte)"
                print(f"  ✓ state byte load: {state_byte_load[0].address:#x} ldrsb r2, [r0, #0x2b]")

                # jumptable: cmp r2, #7 + addls pc, pc, r2, lsl #2
                cmp7 = [
                    ins for ins in instrs
                    if ins.mnemonic == "cmp" and ins.op_str == "r2, #7"
                ]
                assert cmp7, "cmp r2, #7 (state jumptable) 미발견"
                print(f"  ✓ jumptable dispatch: {cmp7[0].address:#x} cmp r2, #7")

                addls = [
                    ins for ins in instrs
                    if ins.mnemonic == "addls" and "pc, pc, r2, lsl #2" in ins.op_str
                ]
                assert addls, "addls pc, pc, r2, lsl #2 (state PC adder) 미발견"
                print(f"  ✓ pc adder: {addls[0].address:#x} addls pc, pc, r2, lsl #2")

                # +0x29 sub-step counter increment + strb
                strb_29 = [
                    ins for ins in instrs
                    if ins.mnemonic == "strb" and "[r4, #0x29]" in ins.op_str
                ]
                assert len(strb_29) >= 4, (
                    f"sub-step counter strb to +0x29 4회 이상 기대, {len(strb_29)} 회"
                )
                print(f"  ✓ sub-step (+0x29) strb {len(strb_29)} 회 (phase 마다 1회)")

                # +0x2d animation key A strb
                strb_2d = [
                    ins for ins in instrs
                    if ins.mnemonic == "strb" and "[r4, #0x2d]" in ins.op_str
                ]
                assert len(strb_2d) >= 2, (
                    f"animation key A strb to +0x2d 2회 이상 기대, {len(strb_2d)} 회"
                )
                print(f"  ✓ anim key A (+0x2d) strb {len(strb_2d)} 회")

                # +0x2f animation key B strb
                strb_2f = [
                    ins for ins in instrs
                    if ins.mnemonic == "strb" and "[r4, #0x2f]" in ins.op_str
                ]
                assert len(strb_2f) >= 2, (
                    f"animation key B strb to +0x2f 2회 이상 기대, {len(strb_2f)} 회"
                )
                print(f"  ✓ anim key B (+0x2f) strb {len(strb_2f)} 회")

                # sub-step finalize check: cmp r3, #4 + bne (return busy)
                cmp_4 = [
                    ins for ins in instrs
                    if ins.mnemonic == "cmp" and ins.op_str == "r3, #4"
                ]
                assert len(cmp_4) >= 2, (
                    f"sub-step finalize (cmp r3, #4) 2회 이상 기대, {len(cmp_4)} 회"
                )
                print(f"  ✓ sub-step finalize (cmp r3, #4) {len(cmp_4)} 회")

                # state 2 의 fast-jump: cmp r1, #5 → state 7 (cmp r2, #3 도 함께)
                cmp_5 = [
                    ins for ins in instrs
                    if ins.mnemonic == "cmp" and ins.op_str == "r1, #5"
                ]
                assert cmp_5, "state 2 의 fast-jump (cmp r1, #5) 미발견"
                print(f"  ✓ state 2 → state 7 fast-jump: {cmp_5[0].address:#x} cmp r1, #5")

                # SetDialogWindow (helper) bl 호출 검증 (0x6ab40 = 0x6ab40)
                bl_setdialog = [
                    ins for ins in instrs
                    if ins.mnemonic == "bl" and ins.op_str == "#0x6ab40"
                ]
                assert bl_setdialog, "SetDialogWindow bl #0x6ab40 미발견"
                print(f"  ✓ SetDialogWindow bl: {len(bl_setdialog)} 회 (phase finalize)")

                # RestorePal (0x59400) bl 호출 검증 (phase 5/7)
                bl_pal = [
                    ins for ins in instrs
                    if ins.mnemonic == "bl" and ins.op_str == "#0x59400"
                ]
                assert bl_pal, "RestorePal bl #0x59400 미발견 (phase 5/7)"
                print(f"  ✓ Graphic::RestorePal bl: {len(bl_pal)} 회 (phase 5/7)")

                # ChangeHSB (0x5f000) bl 호출 검증 (phase 5/7)
                bl_hsb = [
                    ins for ins in instrs
                    if ins.mnemonic == "bl" and ins.op_str == "#0x5f000"
                ]
                assert bl_hsb, "ChangeHSB bl #0x5f000 미발견 (phase 5/7)"
                print(f"  ✓ Graphic::ChangeHSB bl: {len(bl_hsb)} 회 (phase 5/7)")

            except ImportError:
                print("  [skip] capstone 미설치 — disasm pattern 검증 skip")

        except ImportError:
            print("  [skip] lief 미설치 — symbol 검증 skip")

    # 4. RE 문서 일치
    print("\n# 3. docs/h5/RE/npc_dialog.md 내용 검증")
    doc = RE_DOC.read_text(encoding="utf-8")
    required_doc_markers = [
        "DialogWindow_Proc",
        "+0x2b",       # main state byte 정정
        "+0x29",       # sub-step counter
        "+0x2d",       # anim key A
        "+0x2f",       # anim key B
        "cmp r2, #7",
        "SetDialogWindow",
        "RestorePal",
        "ChangeHSB",
        "Event_SituateDialogText",
        "+0xdf",       # sub_state 분기
        "R67 → R68 정정",
    ]
    for marker in required_doc_markers:
        assert marker in doc, f"RE 문서에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    # 5. dialog_box.gd 상수
    print("\n# 4. dialog_box.gd 의 DIALOG_STATE_* 상수")
    gd = DIALOG_GD.read_text(encoding="utf-8")
    expected_consts = {
        "DIALOG_STATE_INACTIVE": "0",
        "DIALOG_STATE_IDLE_ACTIVE": "1",
        "DIALOG_STATE_FADE_IN_A": "2",
        "DIALOG_STATE_IDLE_ACTIVE_2": "3",
        "DIALOG_STATE_FADE_IN_B": "4",
        "DIALOG_STATE_FADE_HSB_A": "5",
        "DIALOG_STATE_IDLE_ACTIVE_3": "6",
        "DIALOG_STATE_FADE_HSB_B": "7",
        "DIALOG_SUBSTEP_FINAL": "4",
    }
    for name, value in expected_consts.items():
        pat = rf"const\s+{re.escape(name)}\s*=\s*{re.escape(value)}\b"
        assert re.search(pat, gd), f"{name} = {value} 가 dialog_box.gd 에 없음"
        print(f"  ✓ {name} = {value}")

    # SetDialogWindow trigger 3종
    expected_triggers = [
        ("DIALOG_TRIGGER_FIRST",  "Vector2i(1, 2)"),
        ("DIALOG_TRIGGER_TYPE2",  "Vector2i(4, 2)"),
        ("DIALOG_TRIGGER_PAIR",   "Vector2i(6, 5)"),
    ]
    for name, value in expected_triggers:
        pat = rf"const\s+{re.escape(name)}\s*=\s*{re.escape(value)}"
        assert re.search(pat, gd), f"{name} = {value} 가 dialog_box.gd 에 없음"
        print(f"  ✓ {name} = {value}")

    # 6. R67 → R68 docstring 명시
    print("\n# 5. dialog_box.gd R68 RE docstring")
    r68_markers = [
        "Round 68 RE",
        "DialogWindow_Proc",
        "+0x2b",       # main state offset
        "0..7",        # jumptable range
        "+0x29",       # sub-step
    ]
    for marker in r68_markers:
        assert marker in gd, f"dialog_box.gd 의 docstring 에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    # 7. R67 PASS 1 추정 정정 (R67 hyptohesis correction)
    print("\n# 6. R67 → R68 가설 정정 검증 (RE 문서)")
    correction_markers = [
        ("R67 PASS 1 추정", "R68 확정"),
        ("0x29", "0x2b"),
    ]
    for old, new in correction_markers:
        assert old in doc and new in doc, f"정정 표 marker '{old}'/'{new}' 누락"
        print(f"  ✓ '{old}' → '{new}' 정정 명시")

    print("\n# All Round 68 NPC Dialog RE checks passed.")


if __name__ == "__main__":
    main()
