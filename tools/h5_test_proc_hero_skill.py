"""Round 70+71 — HERO::ProcHeroSkill (@0x99278, 7972B) 골격 + Formula::calc + r5 base RE 검증.

R69 에서 발견된 ChangeAttackMotion 호출자 (ProcHeroSkill +0x488) 의 고수준 골격을
정밀화. R71 추가: Formula::calc dispatch + r5 base 추적.

검증 항목 (R70):
  1. ELF symbol 확정 (ProcHeroSkill 7972B + 핵심 helper 10종)
  2. Entry sequence — class 2 분기 + 59-iter skill slot 초기화
  3. Jumptable 1 (@0x9a398, 5-way) — dispatch key = skill_info[+0x28]
  4. Jumptable 2 (@0x9a8d8, 7-way) — dispatch key = HERO::GetCurActSkillIdx()
  5. 0x99700 ChangeAttackMotion 호출 + Formula 0x6f/0x63 cmp #0x63 pre/post
  6. Formula::calc 27회 + TargetEffectMgr 11회 + 핵심 helper 호출 빈도
  7. HeroSkillInfo struct field 매핑 (r6 ldrsb/ldrh 18+ fields)
  8. HERO this field +0x22c (class_id) + +0x269/+0x294-296 cluster

R71 추가 검증:
  9. Formula::calc dispatch — id < 1000 → calc_pl, < 2000 → calc_en, ≤ 3007 → calc_sk
 10. r5 base 추적 — `add r5, r4, #0x1ec0` + `add r5, r5, #0xc` → r5 = HERO+0x1ecc
 11. 0x99704 의 `ldr r3, [r5, #-0x190]` → r3 = *(HERO + 0x1d3c)
 12. 0x99710 의 `cmp r2, #0x63` (level cap 99)
 13. docs/h5/RE/proc_hero_skill.md §11 (Formula dispatch + r5 base) 마커
"""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
RE_DOC = ROOT / "docs/h5/RE/proc_hero_skill.md"


def main():
    print("# Round 70 HERO::ProcHeroSkill 골격 RE 검증\n")
    assert RE_DOC.exists(), f"missing {RE_DOC}"

    # 1. ELF symbol cross-verify
    print("# 1. ELF symbol cross-verify (ProcHeroSkill + 10 helper)")
    if not SO_PATH.exists():
        print(f"  [skip] {SO_PATH} 미발견")
        return

    try:
        import lief
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    except ImportError:
        print("  [skip] lief/capstone 미설치")
        return

    b = lief.parse(str(SO_PATH))
    targets = {
        "_ZN4HERO13ProcHeroSkillEP13HeroSkillInfo":
            (0x99278, 7972, "HERO::ProcHeroSkill"),
        "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase":
            (0x7749c, None, "Formula::calc"),
        "_ZN4HERO17GetCurActSkillIdxEv":
            (0x88c9c, None, "HERO::GetCurActSkillIdx"),
        "_ZN4HERO18ChangeAttackMotionEP13HeroSkillInfo":
            (0x91e7c, 340, "HERO::ChangeAttackMotion"),
        "_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaaaasaii":
            (0x62d40, None, "TargetEffectMgr::NewTargetEffect"),
        "_ZN7BATTLER10IncreaseHPEi":
            (0x4b41c, None, "BATTLER::IncreaseHP"),
        "_ZN7BATTLER14ApplyAddEffectEasP13HeroSkillInfo":
            (0x4bdb4, None, "BATTLER::ApplyAddEffect"),
        "_ZN4HERO10IncreaseSPEi":
            (0x88e2c, None, "HERO::IncreaseSP"),
        "_ZN4HERO16GetTempAtkProPtrEv":
            (0x88cf8, None, "HERO::GetTempAtkProPtr"),
        "_ZN14AttackProperty10GetHitTypeEv":
            (0x74538, None, "AttackProperty::GetHitType"),
        "_ZN10StaticUtil4RandEii":
            (0x143c98, None, "StaticUtil::Rand"),
    }
    found = {}
    for s in b.symbols:
        if s.name in targets:
            found[s.name] = (int(s.value), int(s.size))
    for name, (expect_addr, expect_size, label) in targets.items():
        assert name in found, f"missing symbol: {name}"
        actual_addr, actual_size = found[name]
        actual_clean = actual_addr & ~1
        assert actual_clean == expect_addr, (
            f"{label}: expected {expect_addr:#x}, got {actual_addr:#x}"
        )
        if expect_size is not None:
            assert actual_size == expect_size, (
                f"{label}: expected size {expect_size}, got {actual_size}"
            )
        sz_str = f"size={actual_size}" if expect_size else "(size N/A)"
        print(f"  ✓ {label}: addr={actual_addr:#x} {sz_str}")
    print(f"  ✓ {len(targets)}/{len(targets)} symbol all match")

    # 2-8. ProcHeroSkill 디스어셈블 + 패턴 검증
    print("\n# 2-8. ProcHeroSkill disasm pattern 검증")
    addr, size = found["_ZN4HERO13ProcHeroSkillEP13HeroSkillInfo"]
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
    md.detail = True
    instrs = list(md.disasm(chunk, addr_aligned))
    assert len(instrs) == 1993, (
        f"instruction 1993 기대, {len(instrs)} 개"
    )
    print(f"  ✓ Total instructions: {len(instrs)}")

    # Entry: ldrb [r4, #0x22c] + cmp #2 + beq class2 path
    class_id_load = [ins for ins in instrs
                     if ins.mnemonic == "ldrb" and "[r4, #0x22c]" in ins.op_str]
    assert class_id_load, "class_id load (ldrb [r4, #0x22c]) 미발견"
    first = class_id_load[0]
    assert first.address < addr + 0x80, (
        f"class_id load 가 entry 영역 (+0x80) 안이어야 함, got {first.address:#x}"
    )
    print(f"  ✓ entry class_id load: {first.address:#x} ldrb r3, [r4, #0x22c]")

    cmp_2 = [ins for ins in instrs
             if ins.mnemonic == "cmp" and ins.op_str == "r3, #2"
             and ins.address < addr + 0x80]
    assert cmp_2, "entry 영역의 class 2 분기 (cmp r3, #2) 미발견"
    print(f"  ✓ class 2 분기 (cmp r3, #2): {cmp_2[0].address:#x}")

    # 59-iter loop: cmp r5, #0x3b
    cmp_3b = [ins for ins in instrs
              if ins.mnemonic == "cmp" and ins.op_str == "r5, #0x3b"]
    assert cmp_3b, "59-iter skill slot 초기화 loop (cmp r5, #0x3b) 미발견"
    print(f"  ✓ 59-iter loop (cmp r5, #0x3b): {cmp_3b[0].address:#x}")

    # Jumptable 1 @ 0x9a398
    jt1_addr = 0x9a398
    jt1 = [ins for ins in instrs
           if ins.address == jt1_addr and ins.mnemonic == "addls"
           and "pc, pc, r3, lsl #2" in ins.op_str]
    assert jt1, f"Jumptable 1 @ {jt1_addr:#x} (addls pc, pc, r3, lsl #2) 미발견"
    print(f"  ✓ Jumptable 1: @{jt1_addr:#x} addls pc, pc, r3, lsl #2")

    # Jumptable 1 dispatch key: ldrsb r3, [r6, #0x28] + cmp r3, #4
    jt1_key_load = [ins for ins in instrs
                    if ins.mnemonic == "ldrsb" and "[r6, #0x28]" in ins.op_str
                    and ins.address < jt1_addr and ins.address > jt1_addr - 0x20]
    assert jt1_key_load, "Jumptable 1 dispatch key load (ldrsb [r6, #0x28]) 미발견"
    print(f"  ✓ Jumptable 1 dispatch key: skill_info[+0x28] @ {jt1_key_load[0].address:#x}")

    jt1_cmp = [ins for ins in instrs
               if ins.mnemonic == "cmp" and ins.op_str == "r3, #4"
               and ins.address == jt1_addr - 4]
    assert jt1_cmp, "Jumptable 1 cmp r3, #4 미발견"
    print(f"  ✓ Jumptable 1 range: cmp r3, #4 (case 0..4)")

    # Jumptable 2 @ 0x9a8d8
    jt2_addr = 0x9a8d8
    jt2 = [ins for ins in instrs
           if ins.address == jt2_addr and ins.mnemonic == "addls"
           and "pc, pc, r3, lsl #2" in ins.op_str]
    assert jt2, f"Jumptable 2 @ {jt2_addr:#x} 미발견"
    print(f"  ✓ Jumptable 2: @{jt2_addr:#x} addls pc, pc, r3, lsl #2")

    # Jumptable 2 dispatch key: bl GetCurActSkillIdx 직후
    jt2_bl = [ins for ins in instrs
              if ins.mnemonic == "bl" and ins.op_str == "#0x88c9c"
              and ins.address < jt2_addr and ins.address > jt2_addr - 0x20]
    assert jt2_bl, "Jumptable 2 dispatch (bl GetCurActSkillIdx) 미발견"
    print(f"  ✓ Jumptable 2 dispatch key: HERO::GetCurActSkillIdx() @ {jt2_bl[0].address:#x}")

    jt2_cmp = [ins for ins in instrs
               if ins.mnemonic == "cmp" and ins.op_str == "r3, #6"
               and ins.address == jt2_addr - 4]
    assert jt2_cmp, "Jumptable 2 cmp r3, #6 미발견"
    print(f"  ✓ Jumptable 2 range: cmp r3, #6 (case 0..6, 7 active skill slots)")

    # ChangeAttackMotion 호출 @ 0x99700 (offset +0x488)
    call_change = [ins for ins in instrs
                   if ins.mnemonic == "bl" and ins.op_str == "#0x91e7c"]
    assert len(call_change) == 1, (
        f"ChangeAttackMotion 호출 1회 기대, {len(call_change)} 회"
    )
    assert call_change[0].address == 0x99700, (
        f"ChangeAttackMotion 호출 위치 {call_change[0].address:#x}, expected 0x99700"
    )
    print(f"  ✓ ChangeAttackMotion 호출 @ 0x99700 (offset +0x488)")

    # Formula::calc 27회 호출
    formula_calls = [ins for ins in instrs
                     if ins.mnemonic == "bl" and ins.op_str == "#0x7749c"]
    assert len(formula_calls) == 27, (
        f"Formula::calc bl 27회 기대, {len(formula_calls)} 회"
    )
    print(f"  ✓ Formula::calc bl: {len(formula_calls)} 회 (= 27)")

    # TargetEffectMgr::NewTargetEffect 11회
    tem_calls = [ins for ins in instrs
                 if ins.mnemonic == "bl" and ins.op_str == "#0x62d40"]
    assert len(tem_calls) == 11, (
        f"TargetEffectMgr::NewTargetEffect 11회 기대, {len(tem_calls)} 회"
    )
    print(f"  ✓ TargetEffectMgr::NewTargetEffect bl: {len(tem_calls)} 회 (= 11)")

    # BATTLER::IncreaseHP 10회
    hp_calls = [ins for ins in instrs
                if ins.mnemonic == "bl" and ins.op_str == "#0x4b41c"]
    assert len(hp_calls) == 10, (
        f"BATTLER::IncreaseHP 10회 기대, {len(hp_calls)} 회"
    )
    print(f"  ✓ BATTLER::IncreaseHP bl: {len(hp_calls)} 회 (= 10)")

    # GetCurActSkillIdx 18회
    skill_idx_calls = [ins for ins in instrs
                       if ins.mnemonic == "bl" and ins.op_str == "#0x88c9c"]
    assert len(skill_idx_calls) == 18, (
        f"GetCurActSkillIdx 18회 기대, {len(skill_idx_calls)} 회"
    )
    print(f"  ✓ HERO::GetCurActSkillIdx bl: {len(skill_idx_calls)} 회 (= 18)")

    # HeroSkillInfo (r6) struct fields — 핵심 4종
    r6_field_28 = [ins for ins in instrs
                   if ins.mnemonic == "ldrsb" and "[r6, #0x28]" in ins.op_str]
    assert r6_field_28, "skill_info[+0x28] (skill effect type) 미발견"
    print(f"  ✓ skill_info[+0x28] ldrsb: {len(r6_field_28)} 회 (skill effect type)")

    r6_field_30 = [ins for ins in instrs
                   if ins.mnemonic == "ldrsb" and "[r6, #0x30]" in ins.op_str]
    assert len(r6_field_30) >= 8, (
        f"skill_info[+0x30] ldrsb 8회 이상 기대, {len(r6_field_30)} 회"
    )
    print(f"  ✓ skill_info[+0x30] ldrsb: {len(r6_field_30)} 회 (skill behavior)")

    r6_field_34 = [ins for ins in instrs
                   if ins.mnemonic == "ldrh" and "[r6, #0x34]" in ins.op_str]
    assert len(r6_field_34) >= 8, (
        f"skill_info[+0x34] ldrh 8회 이상 기대, {len(r6_field_34)} 회"
    )
    print(f"  ✓ skill_info[+0x34] ldrh: {len(r6_field_34)} 회 (primary value)")

    r6_field_38 = [ins for ins in instrs
                   if ins.mnemonic == "ldrh" and "[r6, #0x38]" in ins.op_str]
    assert len(r6_field_38) >= 8, (
        f"skill_info[+0x38] ldrh 8회 이상 기대, {len(r6_field_38)} 회"
    )
    print(f"  ✓ skill_info[+0x38] ldrh: {len(r6_field_38)} 회 (secondary value)")

    # HERO this (r4) field +0x22c — 16회
    r4_22c = [ins for ins in instrs
              if ins.mnemonic == "ldrb" and "[r4, #0x22c]" in ins.op_str]
    assert len(r4_22c) == 16, (
        f"HERO+0x22c class_id ldrb 16회 기대, {len(r4_22c)} 회"
    )
    print(f"  ✓ HERO+0x22c class_id ldrb: {len(r4_22c)} 회")

    # === R72 추가 검증 ===
    # JT1 case 별 helper 호출 검증
    print("\n# === R72 추가 검증 ===")
    print("# X. JT1 case 별 helper 호출 (AddCurseSkill / AddBuffSkill / AddStanceSkill / IncreaseSP)")

    # case 1+2 (0x9ac68 영역) — BATTLER::AddCurseSkill (@0x4b134) 호출
    addr_curse = 0x4b134
    bl_curse_in_case12 = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == f"#{addr_curse:#x}"
        and 0x9ac68 <= ins.address < 0x9ad68
    ]
    assert bl_curse_in_case12, "case 1+2 (0x9ac68) 영역에서 AddCurseSkill bl 미발견"
    print(f"  ✓ case 1+2 BATTLER::AddCurseSkill: {bl_curse_in_case12[0].address:#x}")

    # case 3+5 (0x9abfc 영역) — BATTLER::AddBuffSkill (@0x4b198) 호출
    addr_buff = 0x4b198
    bl_buff_in_case35 = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == f"#{addr_buff:#x}"
        and 0x9abfc <= ins.address < 0x9acfc
    ]
    assert bl_buff_in_case35, "case 3+5 (0x9abfc) 영역에서 AddBuffSkill bl 미발견"
    print(f"  ✓ case 3+5 BATTLER::AddBuffSkill: {bl_buff_in_case35[0].address:#x}")

    # case 4 (0x9ab98 영역) — HERO::AddStanceSkill (@0x91d7c) 호출
    addr_stance = 0x91d7c
    bl_stance_in_case4 = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == f"#{addr_stance:#x}"
        and 0x9ab98 <= ins.address < 0x9ac98
    ]
    assert bl_stance_in_case4, "case 4 (0x9ab98) 영역에서 AddStanceSkill bl 미발견"
    print(f"  ✓ case 4 HERO::AddStanceSkill: {bl_stance_in_case4[0].address:#x}")

    # case 0 NO_HIT path (0x99978 영역) — HERO::IncreaseSP 호출 (skill_info[+0x4a] s16)
    bl_sp_in_case0 = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == "#0x88e2c"
        and 0x99978 <= ins.address < 0x999fc
    ]
    assert bl_sp_in_case0, "case 0 NO_HIT path (0x99978) 에서 IncreaseSP 미발견"
    print(f"  ✓ case 0 HERO::IncreaseSP: {bl_sp_in_case0[0].address:#x}")

    # case 0 entry: ldrsb r3, [r6, #0x1c]
    case0_lds_1c = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsb" and "[r6, #0x1c]" in ins.op_str
        and ins.address == 0x99978
    ]
    assert case0_lds_1c, "case 0 entry (ldrsb [r6, #0x1c]) 미발견"
    print(f"  ✓ case 0 entry: ldrsb r3, [r6, #0x1c] (alternate path flag)")

    # case 0 secondary check: ldrb r3, [r4, #0x294]
    r4_294 = [
        ins for ins in instrs
        if ins.mnemonic == "ldrb" and "[r4, #0x294]" in ins.op_str
    ]
    assert r4_294, "HERO+0x294 skill state flag (ldrb [r4, #0x294]) 미발견"
    print(f"  ✓ HERO+0x294 skill state flag ldrb: {len(r4_294)} 회")

    # case 0 secondary formula id: ldrb r1, [r4, #0x295]
    r4_295 = [
        ins for ins in instrs
        if ins.mnemonic == "ldrb" and "[r4, #0x295]" in ins.op_str
    ]
    assert r4_295, "HERO+0x295 secondary formula id (ldrb [r4, #0x295]) 미발견"
    print(f"  ✓ HERO+0x295 secondary formula id ldrb: {len(r4_295)} 회")

    # case 0 SP delta: ldrsh r1, [r6, #0x4a]
    sp_4a = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsh" and "[r6, #0x4a]" in ins.op_str
    ]
    assert sp_4a, "skill_info+0x4a SP cost/heal (ldrsh [r6, #0x4a]) 미발견"
    print(f"  ✓ skill_info+0x4a SP delta ldrsh: {len(sp_4a)} 회")

    # case 1+2 special dispatch: cmp r2, #0x34 / #0x37
    cmp_34 = [
        ins for ins in instrs
        if ins.mnemonic == "cmp" and ins.op_str == "r2, #0x34"
    ]
    cmp_37 = [
        ins for ins in instrs
        if ins.mnemonic == "cmp" and ins.op_str == "r2, #0x37"
    ]
    assert cmp_34 and cmp_37, "case 1+2 special dispatch (cmp #0x34/#0x37) 미발견"
    print(f"  ✓ case 1+2 special dispatch (cmp #0x34, #0x37): {cmp_34[0].address:#x}, {cmp_37[0].address:#x}")

    # === R73 추가 검증 ===
    print("\n# === R73 추가 검증 ===")
    print("# Y. JT2 case 별 동작 (기본 공격 / timestop / KNIGHT / shock)")

    # JT2 case 0/2/4/6 (0x99904 영역) — Formula 3 + BATTLER::IncreaseHP + Formula 4 + IncreaseSP
    mov_r1_3 = [
        ins for ins in instrs
        if ins.mnemonic == "mov" and ins.op_str == "r1, #3"
        and 0x99904 <= ins.address < 0x99928
    ]
    assert mov_r1_3, "JT2 case 0/2/4/6 의 Formula 3 setup (mov r1, #3) 미발견"
    print(f"  ✓ JT2 기본 공격: Formula id=3 (mov r1, #3) @ {mov_r1_3[0].address:#x}")

    mov_r1_4 = [
        ins for ins in instrs
        if ins.mnemonic == "mov" and ins.op_str == "r1, #4"
        and 0x99928 <= ins.address < 0x99948
    ]
    assert mov_r1_4, "JT2 case 0/2/4/6 의 Formula 4 setup (mov r1, #4) 미발견"
    print(f"  ✓ JT2 기본 공격: Formula id=4 (mov r1, #4) @ {mov_r1_4[0].address:#x}")

    # BATTLER::IncreaseHP @0x99928 직후 (formula 3 결과)
    bl_hp_in_basic = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == "#0x4b41c"
        and 0x99928 <= ins.address < 0x99934
    ]
    assert bl_hp_in_basic, "JT2 기본 공격 (0x99904) 에서 IncreaseHP 호출 미발견"
    print(f"  ✓ JT2 기본 공격: BATTLER::IncreaseHP @ {bl_hp_in_basic[0].address:#x}")

    # JT2 case 1/7 (0x9ad78) — OBJECT::SetTimestopFrame (@0xcfde0)
    bl_timestop = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == "#0xcfde0"
        and 0x9ad78 <= ins.address < 0x9ad88
    ]
    assert bl_timestop, "JT2 case 1/7 SetTimestopFrame 미발견"
    print(f"  ✓ JT2 case 1/7 (timestop): SetTimestopFrame @ {bl_timestop[0].address:#x}")

    # JT2 case 5 (0x9aa18) — NewShockAddEffect (@0x8fc20)
    bl_shock = [
        ins for ins in instrs
        if ins.mnemonic == "bl" and ins.op_str == "#0x8fc20"
        and 0x9aa18 <= ins.address < 0x9ab18
    ]
    assert bl_shock, "JT2 case 5 (shock) NewShockAddEffect 미발견"
    print(f"  ✓ JT2 case 5 (shock): HERO::NewShockAddEffect @ {bl_shock[0].address:#x}")

    # JT2 case 5 의 dynamic Formula id (skill_info[+0x30])
    ldrsb_30 = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsb" and "[r6, #0x30]" in ins.op_str
        and 0x9aa18 <= ins.address < 0x9ab00
    ]
    assert ldrsb_30, "JT2 case 5 의 skill_info[+0x30] dynamic Formula id 미발견"
    print(f"  ✓ JT2 case 5: skill_info[+0x30] dynamic Formula id (ldrsb [r6, #0x30])")

    # JT2 case 5 의 skill_info[+0x46] shock count
    ldrsb_46 = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsb" and "[r6, #0x46]" in ins.op_str
        and ins.address == 0x9aa18
    ]
    assert ldrsb_46, "JT2 case 5 entry (ldrsb [r6, #0x46]) 미발견"
    print(f"  ✓ JT2 case 5 entry: skill_info[+0x46] shock count")

    # JT2 case 3 의 class 3 secondary flag (HERO+0x1d36)
    # (mov r2, #0x1d00; add r2, r2, #0x36) → HERO+0x1d36
    cmp_1d36_case3 = [
        ins for ins in instrs
        if ins.mnemonic == "mov" and ins.op_str == "r2, #0x1d00"
        and 0x9acf8 <= ins.address < 0x9ad08
    ]
    assert cmp_1d36_case3, "JT2 case 3 의 HERO+0x1d36 load setup 미발견"
    print(f"  ✓ JT2 case 3: HERO+0x1d36 class 3 secondary flag load")

    # TEM 11회 호출 확인 + effect_type distinct values
    tem_calls = [ins for ins in instrs
                 if ins.mnemonic == "bl" and ins.op_str == "#0x62d40"]
    assert len(tem_calls) == 11, (
        f"TEM 호출 11회 기대, {len(tem_calls)} 회"
    )
    print(f"  ✓ TargetEffectMgr::NewTargetEffect 호출: 11 회")

    # effect_type 4/7/8 distinct 검증 — TEM 호출 직전 12 instr 안의 mov r1, #imm
    tem_effect_types = set()
    for tem_ins in tem_calls:
        idx_t = instrs.index(tem_ins)
        for ctx in reversed(instrs[max(0, idx_t-12):idx_t]):
            if ctx.mnemonic == "mov" and ctx.op_str.startswith("r1, #"):
                try:
                    imm = int(ctx.op_str.split("#")[1], 0)
                    tem_effect_types.add(imm)
                    break
                except ValueError:
                    pass
    for et in (4, 7, 8):
        assert et in tem_effect_types, f"TEM effect_type {et} 미관측 (관측: {sorted(tem_effect_types)})"
    print(f"  ✓ TEM static effect_type values: {sorted(tem_effect_types)} (4/7/8 모두 포함)")

    # case path 의 skill_info[+0x3c] / [+0x3d] formula id load
    ldrsb_3c = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsb" and "[r6, #0x3c]" in ins.op_str
    ]
    ldrsb_3d = [
        ins for ins in instrs
        if ins.mnemonic == "ldrsb" and "[r6, #0x3d]" in ins.op_str
    ]
    assert len(ldrsb_3c) >= 3, (
        f"skill_info[+0x3c] formula id 1 3회 이상 기대, {len(ldrsb_3c)} 회"
    )
    assert len(ldrsb_3d) >= 3, (
        f"skill_info[+0x3d] formula id 2 3회 이상 기대, {len(ldrsb_3d)} 회"
    )
    print(f"  ✓ skill_info[+0x3c] formula id 1 ldrsb: {len(ldrsb_3c)} 회")
    print(f"  ✓ skill_info[+0x3d] formula id 2 ldrsb: {len(ldrsb_3d)} 회")

    # class 2 GUNNER path entry: cmp r0, #0x5000000 (skill idx 5)
    cmp_5_signed = [
        ins for ins in instrs
        if ins.mnemonic == "cmp" and ins.op_str == "r0, #0x5000000"
        and 0x9a564 <= ins.address < 0x9a584
    ]
    assert cmp_5_signed, "class 2 GUNNER entry (cmp r0, #0x5000000) 미발견"
    print(f"  ✓ class 2 GUNNER entry: cmp r0, #0x5000000 @ {cmp_5_signed[0].address:#x}")

    # class 2 GUNNER combo state: ldrb [r4, #0x269]
    r4_269 = [
        ins for ins in instrs
        if ins.mnemonic == "ldrb" and "[r4, #0x269]" in ins.op_str
    ]
    assert len(r4_269) >= 2, (
        f"HERO+0x269 GUNNER combo state 2회 이상 기대, {len(r4_269)} 회"
    )
    print(f"  ✓ HERO+0x269 GUNNER combo state ldrb: {len(r4_269)} 회")

    # === R71 추가 검증 ===
    # 9. Formula::calc 자체 disasm 으로 dispatch 매핑 검증
    print("\n# === R71 추가 검증 ===")
    print("# 9. Formula::calc dispatch 매핑 (calc_pl < 1000 / calc_en < 2000 / calc_sk ≤ 3007)")
    formula_calc_addr = 0x7749c
    formula_calc_size = None
    for s in b.symbols:
        if s.name == "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase":
            formula_calc_size = int(s.size)
            break
    assert formula_calc_size == 172, (
        f"Formula::calc size 172 기대, {formula_calc_size}"
    )
    print(f"  ✓ Formula::calc size = 172B")

    fc_off = None
    for seg in b.segments:
        if seg.virtual_address <= formula_calc_addr < seg.virtual_address + seg.virtual_size:
            fc_off = seg.file_offset + (formula_calc_addr - seg.virtual_address)
            break
    assert fc_off is not None
    with open(SO_PATH, "rb") as f:
        f.seek(fc_off)
        fc_chunk = f.read(formula_calc_size)
    md2 = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    fc_instrs = list(md2.disasm(fc_chunk, formula_calc_addr))

    # 1000 (0x3e8) 비교
    cmp_3e8 = [ins for ins in fc_instrs
               if ins.mnemonic == "cmp" and "#0x3e8" in ins.op_str]
    assert cmp_3e8, "Formula::calc 안에 cmp #0x3e8 (1000) 미발견"
    print(f"  ✓ calc_pl 분기 (cmp #0x3e8 = 1000): {cmp_3e8[0].address:#x}")

    # 2000 (0x7d0) 비교
    cmp_7d0 = [ins for ins in fc_instrs
               if ins.mnemonic == "cmp" and "#0x7d0" in ins.op_str]
    assert cmp_7d0, "Formula::calc 안에 cmp #0x7d0 (2000) 미발견"
    print(f"  ✓ calc_en 분기 (cmp #0x7d0 = 2000): {cmp_7d0[0].address:#x}")

    # 3007 (0xbb7) 비교 (mov + add)
    cmp_bb0 = [ins for ins in fc_instrs
               if ins.mnemonic == "mov" and "#0xbb0" in ins.op_str]
    assert cmp_bb0, "Formula::calc 안에 mov #0xbb0 (3000) 미발견"
    print(f"  ✓ calc_sk 상한 setup (mov #0xbb0 = 3000): {cmp_bb0[0].address:#x}")

    # calcByFormula 호출
    bl_calcbyformula = [ins for ins in fc_instrs
                        if ins.mnemonic == "bl" and ins.op_str == "#0x77244"]
    assert bl_calcbyformula, "calcByFormula bl 미발견"
    print(f"  ✓ Formula::calcByFormula bl: {len(bl_calcbyformula)} 회")

    # 10. r5 base 추적 — ProcHeroSkill 안의 first r5 = HERO+0x1ec0 + 0xc
    print("\n# 10. r5 base 추적 (HERO+0x1ecc, R70 의 [r5, -0x190] base)")
    r5_1ec0 = [ins for ins in instrs
               if ins.mnemonic == "add" and ins.op_str == "r5, r4, #0x1ec0"]
    assert r5_1ec0, "add r5, r4, #0x1ec0 미발견 (r5 base setup)"
    print(f"  ✓ r5 setup A (add r5, r4, #0x1ec0): {r5_1ec0[0].address:#x}")

    r5_add_c = [ins for ins in instrs
                if ins.mnemonic == "add" and ins.op_str == "r5, r5, #0xc"
                and r5_1ec0[0].address < ins.address < r5_1ec0[0].address + 0x20]
    assert r5_add_c, "add r5, r5, #0xc (r5 = HERO+0x1ecc) 미발견"
    print(f"  ✓ r5 setup B (add r5, r5, #0xc → r5 = HERO+0x1ecc): {r5_add_c[0].address:#x}")

    # 11. 0x99704 ldr [r5, -0x190] = HERO+0x1d3c
    ldr_r5_neg190 = [ins for ins in instrs
                     if ins.mnemonic == "ldr" and "[r5, #-0x190]" in ins.op_str]
    assert len(ldr_r5_neg190) >= 1, (
        f"ldr [r5, #-0x190] 1회 이상 기대, {len(ldr_r5_neg190)} 회"
    )
    print(f"  ✓ ldr [r5, #-0x190] (HERO+0x1d3c) 등장: {len(ldr_r5_neg190)} 회")

    # 첫 ldr 의 위치 = 0x993ec 기대 (또는 그 근방)
    first_ldr = ldr_r5_neg190[0]
    print(f"  ✓ first [r5, #-0x190] @ {first_ldr.address:#x}")

    # 12. 0x99710 cmp #0x63 (level cap 99)
    cmp_99 = [ins for ins in instrs
              if ins.mnemonic == "cmp" and ins.op_str == "r2, #0x63"]
    assert cmp_99, "level cap 99 (cmp r2, #0x63) 미발견"
    print(f"  ✓ level cap 99 (cmp r2, #0x63): {cmp_99[0].address:#x}")

    # 13. RE 문서 R71 마커
    print("\n# 9. docs/h5/RE/proc_hero_skill.md 내용 검증")
    doc = RE_DOC.read_text(encoding="utf-8")
    required = [
        "ProcHeroSkill",
        "0x99278",            # 함수 주소
        "7972B",              # 함수 크기
        "1993",               # instruction 수
        "+0x488",             # ChangeAttackMotion 호출 offset
        "0x99700",            # 호출 절대 주소
        "Formula::calc",
        "27",                 # Formula 호출 횟수
        "0x9a398",            # Jumptable 1 주소
        "0x9a8d8",            # Jumptable 2 주소
        "+0x28",              # Jumptable 1 dispatch key
        "GetCurActSkillIdx",  # Jumptable 2 dispatch key
        "skill effect type",
        "active skill slot",
        "59-iter",            # entry loop
        "class 2",            # GUNNER 별도 path
        "HeroSkillInfo",
        "TargetEffectMgr::NewTargetEffect",
        "BATTLER::IncreaseHP",
        "0x6f",               # Formula 0x6f
        "0x63",               # Formula 0x63 / level cap
        "+0x22c",             # HERO class_id
        "+0x294",             # HERO state cluster
        "+0x34",              # HeroSkillInfo primary value
        "+0x38",              # HeroSkillInfo secondary value
        "knockback_idx",      # R69 cross-ref
        # R71 추가 markers
        "11. Formula::calc dispatch",  # §11 header
        "0x3e8",              # 1000 boundary
        "0x7d0",              # 2000 boundary
        "0xbb7",              # 3007 boundary
        "calcByFormula",
        "OOB",                # production OOB 결론
        "HERO + 0x1ecc",      # r5 base
        "HERO + 0x1d3c",      # [r5, -0x190] target
        "level cap",
        "R71 → R72",          # R71 잔여 작업
        # R72 markers
        "12. Jumptable 1",     # §12 header
        "AddCurseSkill",       # case 1+2 helper
        "AddBuffSkill",        # case 3+5 helper
        "AddStanceSkill",      # case 4 helper
        "NO_HIT",              # case 0 label
        "stance",              # case 4 정정 (heal+buff → stance)
        "GUNNER combo state",  # HERO+0x269
        "skill slot 5",        # GUNNER 전용
        "+0x3c",               # formula id 1
        "+0x3d",               # formula id 2
        "+0x4a",               # SP delta
        "+0x294",              # skill state flag
        "+0x269",              # GUNNER combo state
        "R72 → R73",           # R72 잔여 작업
        # R73 markers
        "13. Jumptable 2",     # §13 header
        "14. TargetEffectMgr", # §14 header
        "NewShockAddEffect",   # case 5 helper
        "SetTimestopFrame",    # case 1/7 helper
        "기본 공격",            # JT2 0/2/4/6 의미
        "shock skill",         # case 5 의미
        "formula_id = 3",      # 기본 공격 HP delta (asm comment)
        "Formula 3 (HP)",      # 기본 공격 표
        "dynamic Formula id",  # case 5 의 +0x30
        "+0x46",               # shock count
        "+0x4e",               # class 3 threshold
        "+0x1a8",              # HERO halfword storage
        "effect_type",         # TEM 인자
        "TEM 호출",            # TEM 호출 분포 표
        "R73 → R74",           # R73 잔여
    ]
    for marker in required:
        assert marker in doc, f"RE 문서에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    print("\n# All Round 70+71+72+73 ProcHeroSkill RE checks passed.")


if __name__ == "__main__":
    main()
