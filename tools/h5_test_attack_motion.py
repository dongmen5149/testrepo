"""Round 69 — HERO::ChangeAttackMotion + CheckWeaponMotion RE 검증.

R67 PASS 1 의 미해결 dispatch (cmp r0, #0xd/#0xe/#0x14/#0x17 + mov r1, #0x16/0x18/0x26/0xa/0xf)
가 R69 에서 모두 정정됨:
  - input = `CHAR::GetMotion()` 반환값 (현재 motion), NOT skill_type
  - mov imm = SetMotion 의 새 motion (0x16/0x18/0x26/0xf) OR KB strength (0xa)
  - dispatch key = `this->class_id` (HERO+0x22c), 0=워리어 / 3=나이트 만 active
  - ChangeAttackMotion 호출자 = HERO::ProcHeroSkill @0x99278 offset +0x488 (1회)
  - CheckWeaponMotion 호출자 = 4 클래스의 Draw() 메서드 5회 (WARRIOR/ROGUE/KNIGHT/GUNNER)

검증 항목:
  1. ELF symbol 2종 cross-verify (ChangeAttackMotion 340B / CheckWeaponMotion 256B)
  2. ChangeAttackMotion 의 dispatch 패턴 추출 (`ldrb [r0, #0x22c]` + class 비교)
  3. class 0 (워리어) 의 motion 13→38 / 20→22 swap dispatch
  4. class 3 (나이트) 의 motion 14→15(NULL)+KB10 / 23→24+variable KB
  5. helper 함수 7종 호출 검증 (GetMotion / SetMotion / SetDir / CharTurnDirection /
     AddEffectKnockBack / SetRevengeXY / IsNoneWeapon)
  6. ChangeAttackMotion 호출자 = HERO::ProcHeroSkill @ 0x99700 (offset +0x488 within
     ProcHeroSkill @ 0x99278) 1회. CheckWeaponMotion 호출자 = 0건.
  7. docs/h5/RE/attack_motion_dispatch.md 의 dispatch 표 + helper 표 + R67→R69 정정 표
  8. character.gd 의 SO_MOTION_WARRIOR_*/KNIGHT_*/WEAPON_*_HIGH 10 상수 검증
"""
from __future__ import annotations
import re
import struct
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHAR_GD = ROOT / "apps/hero5-godot/scripts/core/character.gd"
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
RE_DOC = ROOT / "docs/h5/RE/attack_motion_dispatch.md"


def decode_thumb_bl(upper: int, lower: int, pc_after: int):
    """Thumb-2 BL 디코더."""
    if (upper & 0xf800) != 0xf000:
        return None
    if (lower & 0xd000) != 0xd000:
        return None
    S = (upper >> 10) & 1
    imm10 = upper & 0x3ff
    J1 = (lower >> 13) & 1
    J2 = (lower >> 11) & 1
    imm11 = lower & 0x7ff
    I1 = 1 ^ (J1 ^ S)
    I2 = 1 ^ (J2 ^ S)
    imm = (I1 << 23) | (I2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        imm |= 0xff000000
        imm = imm - 0x100000000
    return pc_after + imm


def main():
    print("# Round 69 ChangeAttackMotion + CheckWeaponMotion RE 검증\n")
    for p in (CHAR_GD, RE_DOC):
        assert p.exists(), f"missing {p}"

    # 1. ELF symbol cross-verify
    print("# 1. ELF symbol cross-verify (2종)")
    if not SO_PATH.exists():
        print(f"  [skip] {SO_PATH} 미발견")
    else:
        try:
            import lief  # type: ignore
            b = lief.parse(str(SO_PATH))
            targets = {
                "_ZN4HERO18ChangeAttackMotionEP13HeroSkillInfo":
                    (0x91e7c, 340, "HERO::ChangeAttackMotion"),
                "_ZN4HERO17CheckWeaponMotionEv":
                    (0x8dd58, 256, "HERO::CheckWeaponMotion"),
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
                    f"{label}: expected {expect_addr:#x}, got {actual_addr:#x}"
                )
                assert actual_size == expect_size, (
                    f"{label}: expected size {expect_size}, got {actual_size}"
                )
                print(f"  ✓ {label}: addr={actual_addr:#x} size={actual_size}")

            # 2-5. ChangeAttackMotion 디스어셈블 + 패턴 검증
            print("\n# 2-5. ChangeAttackMotion disasm pattern 검증")
            try:
                from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
                addr, size = found["_ZN4HERO18ChangeAttackMotionEP13HeroSkillInfo"]
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
                md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
                instrs = list(md.disasm(chunk, addr_aligned))

                # class_id ldrb
                class_load = [ins for ins in instrs
                              if ins.mnemonic == "ldrb" and "[r0, #0x22c]" in ins.op_str]
                assert class_load, "class_id load (ldrb [r0, #0x22c]) 미발견"
                print(f"  ✓ class_id load: {class_load[0].address:#x} ldrb r3, [r0, #0x22c]")

                # class 3 분기
                cmp_3 = [ins for ins in instrs
                         if ins.mnemonic == "cmp" and ins.op_str == "r3, #3"]
                assert cmp_3, "cmp r3, #3 (class 3 분기) 미발견"
                print(f"  ✓ class 3 분기: {cmp_3[0].address:#x} cmp r3, #3")

                # GetMotion 호출 (0x49b74) 2회 (class 0/3 각각)
                bl_getmotion = [ins for ins in instrs
                                if ins.mnemonic == "bl" and ins.op_str == "#0x49b74"]
                assert len(bl_getmotion) == 2, (
                    f"GetMotion bl 2회 기대, {len(bl_getmotion)} 회"
                )
                print(f"  ✓ GetMotion bl: 2 회 (class 0/3 각각)")

                # class 0 motion 13 / 20 분기
                cmp_d = [ins for ins in instrs
                         if ins.mnemonic == "cmp" and ins.op_str == "r0, #0xd"]
                cmp_14 = [ins for ins in instrs
                          if ins.mnemonic == "cmp" and ins.op_str == "r0, #0x14"]
                assert cmp_d and cmp_14, "class 0 의 motion 13/20 비교 미발견"
                print(f"  ✓ class 0 motion 13 (cmp r0, #0xd): {cmp_d[0].address:#x}")
                print(f"  ✓ class 0 motion 20 (cmp r0, #0x14): {cmp_14[0].address:#x}")

                # class 3 motion 14 / 23 분기
                cmp_e = [ins for ins in instrs
                         if ins.mnemonic == "cmp" and ins.op_str == "r0, #0xe"]
                cmp_17 = [ins for ins in instrs
                          if ins.mnemonic == "cmp" and ins.op_str == "r0, #0x17"]
                assert cmp_e and cmp_17, "class 3 의 motion 14/23 비교 미발견"
                print(f"  ✓ class 3 motion 14 (cmp r0, #0xe): {cmp_e[0].address:#x}")
                print(f"  ✓ class 3 motion 23 (cmp r0, #0x17): {cmp_17[0].address:#x}")

                # mov r1, #0x26 / 0x16 / 0x18 / 0xf / 0xa
                expected_movs = {0x26, 0x16, 0x18, 0xf, 0xa}
                seen = set()
                for ins in instrs:
                    if ins.mnemonic == "mov" and ins.op_str.startswith("r1, #"):
                        try:
                            imm = int(ins.op_str.split("#")[1], 0)
                            seen.add(imm)
                        except ValueError:
                            pass
                missing = expected_movs - seen
                assert not missing, f"mov r1, #imm 누락: {[hex(x) for x in missing]}"
                print(f"  ✓ mov r1, #imm 5종 모두 발견: {sorted(hex(x) for x in expected_movs)}")

                # SetMotion bl (0x4af5c) 5회 — beq 통해 tail-call b 도 포함되지만
                # tail-call 은 `b` 명령이라 별도. bl 명령만 카운트.
                bl_setmotion = [ins for ins in instrs
                                if ins.mnemonic == "bl" and ins.op_str == "#0x4af5c"]
                b_setmotion = [ins for ins in instrs
                               if ins.mnemonic == "b" and ins.op_str == "#0x4af5c"]
                total_setmotion = len(bl_setmotion) + len(b_setmotion)
                assert total_setmotion >= 4, (
                    f"SetMotion 호출 (bl+b) 4회 이상 기대, {total_setmotion} 회"
                )
                print(f"  ✓ SetMotion (bl + tail b): {total_setmotion} 회")

                # AddEffectKnockBack (0xc0a18) 2회 (class 3 의 motion 14/23 각각)
                bl_kb = [ins for ins in instrs
                         if ins.mnemonic == "bl" and ins.op_str == "#0xc0a18"]
                assert len(bl_kb) == 2, (
                    f"AddEffectKnockBack bl 2회 기대, {len(bl_kb)} 회"
                )
                print(f"  ✓ Monster::AddEffectKnockBack bl: {len(bl_kb)} 회")

                # SetRevengeXY (0xbacbc) 1회
                bl_revenge = [ins for ins in instrs
                              if ins.mnemonic == "bl" and ins.op_str == "#0xbacbc"]
                assert bl_revenge, "Monster::SetRevengeXY bl 미발견"
                print(f"  ✓ Monster::SetRevengeXY bl: {len(bl_revenge)} 회")

                # CharTurnDirection (0x4c5ec) 2회
                bl_turn = [ins for ins in instrs
                           if ins.mnemonic == "bl" and ins.op_str == "#0x4c5ec"]
                assert len(bl_turn) == 2, (
                    f"CHAR::CharTurnDirection bl 2회 기대, {len(bl_turn)} 회"
                )
                print(f"  ✓ CHAR::CharTurnDirection bl: {len(bl_turn)} 회")

            except ImportError:
                print("  [skip] capstone 미설치")

            # 6. 호출자 검증
            print("\n# 6. 호출자 검증 (ChangeAttackMotion = ProcHeroSkill 안 1회)")
            text_seg = None
            for seg in b.segments:
                if (int(seg.flags) & 1) and seg.virtual_size > 0:
                    text_seg = seg
                    break
            assert text_seg is not None
            base = int(text_seg.virtual_address)
            file_off = int(text_seg.file_offset)
            sz = int(text_seg.virtual_size)
            with open(SO_PATH, "rb") as f:
                f.seek(file_off)
                text_data = f.read(sz)

            # ARM bl raw 검색 + ProcHeroSkill 영역 매칭
            def find_callers(target_addr):
                hits = []
                for off in range(0, sz - 4, 4):
                    word = struct.unpack("<I", text_data[off:off+4])[0]
                    cond = (word >> 28) & 0xf
                    op = (word >> 24) & 0xf
                    if op == 0xb and cond != 0xf:
                        imm24 = word & 0xffffff
                        if imm24 & 0x800000:
                            imm24 |= 0xff000000
                            imm24 = imm24 - 0x100000000
                        tgt = base + off + 8 + (imm24 << 2)
                        if tgt == target_addr:
                            hits.append(base + off)
                return hits

            # ChangeAttackMotion 호출자 확인
            chg_locs = find_callers(0x91e7c)
            assert len(chg_locs) == 1, (
                f"ChangeAttackMotion 호출자 1회 기대, {len(chg_locs)} 회: "
                f"{[hex(x) for x in chg_locs]}"
            )
            caller_addr = chg_locs[0]
            print(f"  ✓ ChangeAttackMotion 호출자: {caller_addr:#x}")
            # ProcHeroSkill 영역 (0x99278 + 7972 = 0x9b1bc) 안인지 검증
            PROC_HERO_SKILL_START = 0x99278
            PROC_HERO_SKILL_SIZE = 7972
            assert PROC_HERO_SKILL_START <= caller_addr < PROC_HERO_SKILL_START + PROC_HERO_SKILL_SIZE, (
                f"호출자 {caller_addr:#x} 가 ProcHeroSkill 영역 [{PROC_HERO_SKILL_START:#x}..{PROC_HERO_SKILL_START + PROC_HERO_SKILL_SIZE:#x}) 밖"
            )
            offset_in_proc = caller_addr - PROC_HERO_SKILL_START
            print(f"  ✓ 호출자가 HERO::ProcHeroSkill (@{PROC_HERO_SKILL_START:#x}, 7972B) 의 offset +{offset_in_proc:#x}")

            # CheckWeaponMotion 호출자 = 4 클래스 Draw() 메서드 5회
            chk_locs = find_callers(0x8dd58)
            assert len(chk_locs) == 5, (
                f"CheckWeaponMotion 호출자 5 기대, {len(chk_locs)} 회: "
                f"{[hex(x) for x in chk_locs]}"
            )
            print(f"  ✓ CheckWeaponMotion 호출자: {len(chk_locs)} 회 (4 class Draw)")
            # 4 클래스 함수 영역 식별
            class_draw_ranges = {
                "WARRIOR::Draw": (0x146af0, 0x146af0 + 1792),
                "ROGUE::Draw":   (0xd7a18, 0xd7a18 + 1952),
                "KNIGHT::Draw":  (0xaa328, 0xaa328 + 1244),
                "GUNNER::Draw":  (0x87678, 0x87678 + 1376),
            }
            seen_classes = set()
            for loc in chk_locs:
                for cname, (start, end) in class_draw_ranges.items():
                    if start <= loc < end:
                        seen_classes.add(cname)
                        print(f"    @{loc:#x} in {cname} (offset +{loc-start:#x})")
                        break
                else:
                    raise AssertionError(f"CheckWeaponMotion 호출자 {loc:#x} 가 알려진 4 클래스 Draw 영역 밖")
            assert seen_classes == set(class_draw_ranges), (
                f"4 클래스 모두 기대, 발견: {sorted(seen_classes)}"
            )
            print(f"  ✓ 4 클래스 모두 호출 (WARRIOR/ROGUE/KNIGHT/GUNNER), SORCERER 제외 — R22 stub 가설 재확인")

            # Thumb-2 BL 검색 (2 byte align) — 0건 기대 (ARM bl 만 사용)
            thumb_bl_hits = 0
            for off in range(0, sz - 4, 2):
                upper = struct.unpack("<H", text_data[off:off+2])[0]
                lower = struct.unpack("<H", text_data[off+2:off+4])[0]
                pc_after = base + off + 4
                target = decode_thumb_bl(upper, lower, pc_after)
                if target is not None and (target & ~1) == 0x91e7c:
                    thumb_bl_hits += 1
            assert thumb_bl_hits == 0, f"Thumb BL 발견 unexpected: {thumb_bl_hits}"
            print(f"  ✓ Thumb-2 BL #0x91e7c: 0 hits (ARM 만 사용)")

        except ImportError:
            print("  [skip] lief 미설치 — symbol 검증 skip")

    # 7. RE 문서
    print("\n# 7. docs/h5/RE/attack_motion_dispatch.md 내용 검증")
    doc = RE_DOC.read_text(encoding="utf-8")
    required = [
        "ChangeAttackMotion",
        "CheckWeaponMotion",
        "ProcHeroSkill",    # caller 정정
        "+0x488",           # offset within ProcHeroSkill
        "+0x22c",           # class_id offset
        "class 0",          # 워리어
        "class 3",          # 나이트
        "0xd",              # cmp imm
        "0x14",
        "0xe",
        "0x17",
        "0x26",             # SetMotion 38
        "0x16",             # SetMotion 22
        "0x18",             # SetMotion 24
        "0xf",              # SetMotion 15
        "0xa",              # KB strength 10
        "AddEffectKnockBack",
        "SetRevengeXY",
        "CharTurnDirection",
        "GetMotion",
        "+0x1d36",          # class 3 secondary state
        "+0x1fb0",          # attack target
        "+0x1fea",          # knockback_idx
        "HeroSkillInfo",
        "+0x44",
        "R67 → R69",        # 정정 표 marker
    ]
    for marker in required:
        assert marker in doc, f"RE 문서에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    # 8. character.gd 상수
    print("\n# 8. character.gd 의 SO_MOTION_WARRIOR_*/KNIGHT_*/WEAPON_*_HIGH 상수")
    gd = CHAR_GD.read_text(encoding="utf-8")
    expected_consts = {
        "SO_MOTION_WARRIOR_WINDUP_A": "13",
        "SO_MOTION_WARRIOR_HIT_A":    "38",
        "SO_MOTION_WARRIOR_WINDUP_B": "20",
        "SO_MOTION_WARRIOR_HIT_B":    "22",
        "SO_MOTION_KNIGHT_WINDUP_A":  "14",
        "SO_MOTION_KNIGHT_HIT_A":     "15",
        "SO_MOTION_KNIGHT_WINDUP_B":  "23",
        "SO_MOTION_KNIGHT_HIT_B":     "24",
        "SO_MOTION_WEAPON_IDLE_HIGH": "32",
        "SO_MOTION_WEAPON_WALK_HIGH": "48",
    }
    for name, value in expected_consts.items():
        pat = rf"const\s+{re.escape(name)}\s*:?=?\s*:?=\s*{re.escape(value)}\b"
        # GDScript 의 const 표기는 `const NAME := value` 형식
        pat2 = rf"const\s+{re.escape(name)}\s*:=\s*{re.escape(value)}\b"
        assert re.search(pat2, gd), f"{name} = {value} 가 character.gd 에 없음"
        print(f"  ✓ {name} := {value}")

    # 9. R69 docstring 명시
    print("\n# 9. character.gd R69 RE docstring")
    r69_markers = [
        "Round 69 RE",
        "ChangeAttackMotion",
        "ProcHeroSkill",       # caller 정보
        "class_id 0/3 only",
    ]
    for marker in r69_markers:
        assert marker in gd, f"character.gd 의 docstring 에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    print("\n# All Round 69 Attack motion dispatch RE checks passed.")


if __name__ == "__main__":
    main()
