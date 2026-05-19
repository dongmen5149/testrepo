#!/usr/bin/env python3
"""R78: HeroSkillInfo runtime field source 추적 검증.

R77 에서 +0x44..+0x57 (20B runtime) 가 LoadResSkillInfo 에서 채워지지 않음을 확정.
R78 은 그 출처를 추적:
- HeroSkillInfo:: 멤버 함수 4종 (SetNowCoolTime/Get/Decrease/GetMax) disasm
- +0x54 (NowCoolTime) / +0x56 (MaxCoolTime) cooldown pair 확정
- ProcHeroSkill entry 59-iter 루프 의미 정정 (init → cooldown tick)
- InitSkillEmpty / InitSpiritSkillMenu 는 HeroSkillInfo 무관
- R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e writer 미확정 (default 0)
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


def parse_elf_text(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2e)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    shstr_off = struct.unpack_from('<I', data, e_shoff + e_shstrndx * e_shentsize + 0x10)[0]
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        sh_name = struct.unpack_from('<I', data, base + 0)[0]
        sh_addr = struct.unpack_from('<I', data, base + 0xc)[0]
        sh_offset = struct.unpack_from('<I', data, base + 0x10)[0]
        end = data.index(b'\0', shstr_off + sh_name)
        if data[shstr_off + sh_name:end] == b'.text':
            return sh_addr, sh_offset
    raise RuntimeError("no .text")


def parse_syms(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2e)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    shstr_off = struct.unpack_from('<I', data, e_shoff + e_shstrndx * e_shentsize + 0x10)[0]
    ds_off = ds_size = dstr_off = 0
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        sh_name = struct.unpack_from('<I', data, base + 0)[0]
        sh_offset = struct.unpack_from('<I', data, base + 0x10)[0]
        sh_size = struct.unpack_from('<I', data, base + 0x14)[0]
        end = data.index(b'\0', shstr_off + sh_name)
        n = data[shstr_off + sh_name:end].decode()
        if n == '.dynsym':
            ds_off, ds_size = sh_offset, sh_size
        if n == '.dynstr':
            dstr_off = sh_offset
    syms = {}
    for i in range(ds_size // 16):
        b = ds_off + i * 16
        st_name = struct.unpack_from('<I', data, b)[0]
        st_value = struct.unpack_from('<I', data, b + 4)[0]
        st_size = struct.unpack_from('<I', data, b + 8)[0]
        end = data.index(b'\0', dstr_off + st_name)
        nm = data[dstr_off + st_name:end].decode(errors='replace')
        syms[nm] = (st_value, st_size)
    return syms


def main():
    data = SO_PATH.read_bytes()
    text_addr, text_off = parse_elf_text(data)
    syms = parse_syms(data)

    def f_off(addr):
        return text_off + (addr - text_addr)

    # 1. HeroSkillInfo:: 4 cooldown member functions
    expected = {
        '_ZN13HeroSkillInfo14SetNowCoolTimeEs': (0xd8d38, 12),
        '_ZN13HeroSkillInfo14GetNowCoolTimeEv': (0xd8d44, 8),
        '_ZN13HeroSkillInfo14GetMaxCoolTimeEv': (0xd8d4c, 8),
        '_ZN13HeroSkillInfo19DecreaseNowCoolTimeEv': (0xd8d54, 36),
        '_ZN4HERO19GetHeroSkillInfoPtrEa': (0x88ce4, 20),
        '_ZN4HERO14InitSkillEmptyEv': (0x88a20, 272),
        '_ZN4HERO19InitSpiritSkillMenuEv': (0x89198, 132),
        '_ZN4HERO20HeroSkillAtkHardCodeEP13HeroSkillInfoP7BATTLER': (0x9041c, 888),
    }
    for nm, (addr, sz) in expected.items():
        assert nm in syms, f"missing {nm}"
        v, s = syms[nm]
        assert v == addr and s == sz, f"{nm}: ({hex(v)}, {s}) != ({hex(addr)}, {sz})"
    print(f"[PASS] {len(expected)} ELF symbols verified")

    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # 2. SetNowCoolTime: strh +0x56 + strh +0x54
    code = data[f_off(0xd8d38):f_off(0xd8d38) + 12]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0xd8d38))
    assert "strh r1, [r0, #0x56]" in text, "SetNowCoolTime missing strh +0x56"
    assert "strh r1, [r0, #0x54]" in text, "SetNowCoolTime missing strh +0x54"
    print("[PASS] SetNowCoolTime writes both +0x54 (NowCoolTime) AND +0x56 (MaxCoolTime)")

    # 3. GetNowCoolTime: ldrsh +0x54
    code = data[f_off(0xd8d44):f_off(0xd8d44) + 8]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0xd8d44))
    assert "ldrsh r0, [r0, #0x54]" in text, "GetNowCoolTime missing ldrsh +0x54"
    print("[PASS] GetNowCoolTime reads s16 +0x54")

    # 4. GetMaxCoolTime: ldrsh +0x56
    code = data[f_off(0xd8d4c):f_off(0xd8d4c) + 8]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0xd8d4c))
    assert "ldrsh r0, [r0, #0x56]" in text, "GetMaxCoolTime missing ldrsh +0x56"
    print("[PASS] GetMaxCoolTime reads s16 +0x56")

    # 5. DecreaseNowCoolTime: ldrh +0x54, sub 1, underflow check, clamp 0
    code = data[f_off(0xd8d54):f_off(0xd8d54) + 36]
    insns = list(md.disasm(code, 0xd8d54))
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    assert "ldrh r3, [r0, #0x54]" in text, "missing ldrh +0x54"
    assert "sub r3, r3, #1" in text, "missing -1"
    assert "tst r3, #0x8000" in text, "missing underflow check"
    assert "strh r3, [r0, #0x54]" in text, "missing strh +0x54"
    assert "movne r3, #0" in text, "missing clamp 0"
    print("[PASS] DecreaseNowCoolTime: -1, clamp 0, store +0x54 (cooldown tick)")

    # 6. GetHeroSkillInfoPtr: return this + 0x348 + idx*0x58
    code = data[f_off(0x88ce4):f_off(0x88ce4) + 20]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0x88ce4))
    assert "mov r3, #0x58" in text, "missing 88B stride"
    assert "mul r3, r1, r3" in text, "missing idx*88"
    assert "add r3, r3, #0x348" in text, "missing +0x348 base"
    print("[PASS] GetHeroSkillInfoPtr(idx) = this + 0x348 + idx*0x58 (R70/R77 confirmed)")

    # 7. ProcHeroSkill entry 59-iter loop calls DecreaseNowCoolTime
    code = data[f_off(0x99278):f_off(0x99278) + 0x80]
    insns = list(md.disasm(code, 0x99278))
    text = "\n".join(f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in insns)
    # Verify the loop pattern: mul r0, r7, r5 + add r0, r0, #0x348 + bl 0xd8d54 + cmp r5, #0x3b
    assert "mov r5, #0" in text, "loop counter init"
    assert "mov r7, #0x58" in text, "stride 88B"
    assert "mul r0, r7, r5" in text, "i * 88"
    assert "add r0, r0, #0x348" in text, "+0x348 base"
    assert "bl #0xd8d54" in text, "call DecreaseNowCoolTime"
    assert "cmp r5, #0x3b" in text, "loop bound 59"
    print("[PASS] ProcHeroSkill entry: 59-slot cooldown tick (R70 'init' hypothesis CORRECTED)")

    # 8. InitSkillEmpty writes 0xFF to HERO+0x1b40..+0x1b5f (NOT skill array)
    code = data[f_off(0x88a20):f_off(0x88a20) + 272]
    insns = list(md.disasm(code, 0x88a20))
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    assert "mov r3, #0x1b40" in text, "missing 0x1b40 base"
    assert "mvn r2, #0" in text, "missing 0xFF init value"
    # Verify no writes to HERO+0x348 (skill array)
    assert "#0x348" not in text, "InitSkillEmpty unexpectedly touches skill array"
    # Count strb instructions (should be 32)
    strb_count = sum(1 for i in insns if i.mnemonic == "strb")
    assert strb_count == 32, f"expected 32 strb (one per byte), got {strb_count}"
    print(f"[PASS] InitSkillEmpty: 32B 0xFF init at HERO+0x1b40 (NOT skill array, new HERO cluster)")

    # 9. InitSpiritSkillMenu writes to global state, not skill_info
    code = data[f_off(0x89198):f_off(0x89198) + 132]
    insns = list(md.disasm(code, 0x89198))
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    # Sets HERO+0x1fb6 = 1
    assert "mov r4, #0x1f80" in text and "add r4, r4, #0x36" in text, "missing HERO+0x1fb6 flag"
    assert "strb sl, [r0, r4]" in text, "missing flag write"
    # Writes to global at +0x118/+0x11c/+0x120/+0x122/+0x124-+0x127
    assert "str r1, [r3, #0x118]" in text, "missing global +0x118"
    assert "str r1, [r3, #0x11c]" in text, "missing global +0x11c"
    print("[PASS] InitSpiritSkillMenu: global menu state init (NOT HeroSkillInfo)")

    # 10. HeroSkillAtkHardCode: reads skill_info but does NOT write runtime fields
    code = data[f_off(0x9041c):f_off(0x9041c) + 888]
    insns = list(md.disasm(code, 0x9041c))
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    assert "ldrsb r3, [sb, #0x45]" in text, "missing skill_info+0x45 read"
    # No strb/strh to skill_info struct (sb = r1 = skill_info)
    # Check no writes go through sb register
    skill_info_writes = [i for i in insns if i.mnemonic in ('strb', 'strh', 'str')
                        and ('sb' in i.op_str or 'r1' in i.op_str)
                        and '[sb' in i.op_str.replace(' ', '')]
    assert len(skill_info_writes) == 0, f"unexpected writes to skill_info in HeroSkillAtkHardCode: {skill_info_writes}"
    print("[PASS] HeroSkillAtkHardCode: reads skill_info+0x45 only, no runtime field writes")

    # 11. .dynsym 에 HeroSkillInfo:: 멤버 함수 ≥4 (cooldown 시리즈)
    hsi_members = [nm for nm in syms if nm.startswith('_ZN13HeroSkillInfo')]
    assert len(hsi_members) >= 4, f"expected ≥4 HeroSkillInfo:: members, got {len(hsi_members)}: {hsi_members}"
    print(f"[PASS] {len(hsi_members)} HeroSkillInfo:: direct members in .dynsym")

    # 12. Doc marker verification
    doc = (ROOT / "docs/h5/RE/skill_info_runtime.md").read_text(encoding='utf-8')
    markers = [
        "DecreaseNowCoolTime", "SetNowCoolTime", "GetNowCoolTime", "GetMaxCoolTime",
        "0xd8d38", "0xd8d44", "0xd8d4c", "0xd8d54",
        "+0x54", "+0x56", "NowCoolTime", "MaxCoolTime",
        "cooldown tick", "정정", "59-iter",
        "0x1b40", "InitSkillEmpty", "InitSpiritSkillMenu",
        "default 0", "writer 미확정", "GetHeroSkillInfoPtr",
        "0x88ce4", "0x348",
    ]
    missing = [m for m in markers if m not in doc]
    assert not missing, f"docs missing markers: {missing}"
    print(f"[PASS] {len(markers)} doc markers in skill_info_runtime.md")

    print("\n=== R78 HeroSkillInfo runtime field RE: ALL PASSED ===")


if __name__ == "__main__":
    main()
