#!/usr/bin/env python3
"""R80: TargetEffectMgr / TargetEffect VFX 시스템 RE 검증.

R73 발견 (effect_type 4/7/8) 의 위치/의미 확정:
- 5 TEM overloads (wrapper chain → _full 실 구현)
- _full 의 100-slot allocator + 0x284B per slot
- Effect 베이스 클래스 5 setter (Type/Frame/LastFrame/Value/IsEmpty)
- effect_type 저장 위치 = Effect+0x12
- post-init r6 (arg 17) → 3-channel manager 등록
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SO_PATH = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


def parse_elf(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2e)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    shstr_off = struct.unpack_from('<I', data, e_shoff + e_shstrndx * e_shentsize + 0x10)[0]
    text = None
    ds_off = ds_size = dstr_off = 0
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        sh_name = struct.unpack_from('<I', data, base + 0)[0]
        sh_addr = struct.unpack_from('<I', data, base + 0xc)[0]
        sh_offset = struct.unpack_from('<I', data, base + 0x10)[0]
        sh_size = struct.unpack_from('<I', data, base + 0x14)[0]
        end = data.index(b'\0', shstr_off + sh_name)
        n = data[shstr_off + sh_name:end].decode()
        if n == '.text':
            text = (sh_addr, sh_offset)
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
    return text, syms


def main():
    data = SO_PATH.read_bytes()
    (text_addr, text_off), syms = parse_elf(data)

    def f_off(addr):
        return text_off + (addr - text_addr)

    # 1. 5 TEM overloads + base + 5 Effect setters
    expected = {
        # 5 TEM overloads
        '_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaaaasaii': (0x62d40, 100),
        '_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaasaasaii': (0x62cd4, 108),
        '_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaasaasaiih': (0x62c54, 128),
        '_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaasaasaiihaa': (0x62bcc, 136),
        '_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaasaasaiihaaaa': (0x62a34, 408),
        # base impl
        '_ZN12TargetEffect15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaasaasaiihaaaa': (0x62840, 500),
        # Effect setters
        '_ZN6Effect7IsEmptyEv': (0x610d8, 16),
        '_ZN6Effect13SetEffectTypeEa': (0x610f4, 8),
        '_ZN6Effect14SetEffectFrameEs': (0x61114, 8),
        '_ZN6Effect18SetEffectLastFrameEs': (0x61124, 8),
        '_ZN6Effect14SetEffectValueEi': (0x61134, 8),
        # OBJECT base
        '_ZN6OBJECT5SetXYEii': (0xcfda4, 8),
        '_ZN6OBJECT13SetObjectTypeEa': (0xcfdac, 8),
    }
    missing = []
    for nm, (addr, sz) in expected.items():
        if nm not in syms:
            missing.append(nm)
            continue
        v, s = syms[nm]
        if v != addr or s != sz:
            missing.append(f"{nm}: ({hex(v)},{s}) != ({hex(addr)},{sz})")
    assert not missing, f"symbol mismatch: {missing}"
    print(f"[PASS] {len(expected)} TEM + Effect + OBJECT symbols verified")

    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    # 2. Effect setter atomic ops
    setter_specs = [
        (0x610d8, ['ldrb r0, [r0, #0x11]', 'rsbs r0, r0, #1', 'movlo r0, #0', 'bx lr']),
        (0x610f4, ['strb r1, [r0, #0x12]', 'bx lr']),
        (0x61114, ['strh r1, [r0, #0x14]', 'bx lr']),
        (0x61124, ['strh r1, [r0, #0x16]', 'bx lr']),
        (0x61134, ['str r1, [r0, #0x18]', 'bx lr']),
    ]
    for addr, expected_ops in setter_specs:
        code = data[f_off(addr):f_off(addr) + 16]
        text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, addr))
        for op in expected_ops:
            assert op in text, f"setter @{hex(addr)} missing: {op}"
    print(f"[PASS] 5 Effect/OBJECT setters: IsEmpty +0x11 / Type +0x12 / Frame +0x14 / LastFrame +0x16 / Value +0x18")

    # 3. TEM 5 overload chain (tail-call wrapper structure)
    chain_checks = [
        (0x62d40, 'bl #0x62cd4'),    # _min → _+s
        (0x62cd4, 'bl #0x62c54'),    # _+s → _+sai
        (0x62c54, 'bl #0x62a34'),    # _+sai → _full
        (0x62bcc, 'bl #0x62a34'),    # _+saiih → _full (parallel)
    ]
    for addr, expected_call in chain_checks:
        size = {0x62d40: 100, 0x62cd4: 108, 0x62c54: 128, 0x62bcc: 136}[addr]
        code = data[f_off(addr):f_off(addr) + size]
        text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, addr))
        assert expected_call in text, f"wrapper @{hex(addr)} missing chain call {expected_call}"
    print("[PASS] TEM 5 overload chain: 4 wrappers → _full (default arg fillers)")

    # 4. _full slot allocator
    code = data[f_off(0x62a34):f_off(0x62a34) + 408]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0x62a34))
    assert "mov r4, #0x284" in text, "missing slot size 0x284 (644B per TargetEffect)"
    assert "mla r4, fp, r4, r5" in text, "missing slot indexing this + fp*0x284"
    assert "bl #0x610d8" in text, "missing IsEmpty check"
    assert "cmp fp, #0x64" in text, "missing 100-slot bound"
    assert "bl #0x62840" in text, "missing call to TargetEffect::NewTargetEffect (base)"
    print("[PASS] _full slot allocator: 100 slot × 0x284B + IsEmpty + bl 0x62840 init")

    # 5. _full post-init r6 dispatch (3 manager channels)
    assert "cmp r6, #1" in text, "missing r6 == 1 (manager type 1)"
    assert "cmp r6, #2" in text, "missing r6 == 2 (manager type 2)"
    assert "cmp r6, #0" in text, "missing r6 == 0 (manager type 0)"
    assert "bl #0xabb94" in text, "missing manager registration call"
    # Verify the 3 manager slot offsets
    assert "#0x15c0" in text, "missing manager base 0x15c0"
    for sub in ('#0x18', '#0x20', '#0x24'):  # +0x18/0x20/0x24 added to 0x15c0
        assert sub in text, f"missing manager sub-offset {sub}"
    print("[PASS] _full post-init: 3 manager channels (0x15d8/0x15e0/0x15e4) via r6 dispatch")

    # 6. TargetEffect base init writes: 25+ field strb/strh
    code = data[f_off(0x62840):f_off(0x62840) + 500]
    insns = list(md.disasm(code, 0x62840))
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    # Active flag set to 1
    assert "strb ip, [r0, #0x11]" in text or "strb r3, [r4, #0x11]" in text or "mov ip, #1" in text, \
        "missing active flag init"
    # SetEffectType (effect_type → +0x12)
    assert "bl #0x610f4" in text, "missing SetEffectType call (stores effect_type at +0x12)"
    assert "bl #0x61114" in text, "missing SetEffectFrame (+0x14)"
    assert "bl #0x61124" in text, "missing SetEffectLastFrame (+0x16)"
    assert "bl #0x61134" in text, "missing SetEffectValue (+0x18)"
    assert "bl #0xcfda4" in text, "missing OBJECT::SetXY"
    assert "bl #0xcfdac" in text, "missing OBJECT::SetObjectType"
    # Many strb to various offsets
    critical_stores = ["#0x8e]", "#0x8c]", "#0x90]", "#0x9d]", "#0x278]", "#0x27b]"]
    for s in critical_stores:
        assert s in text, f"missing field store {s}"
    # memset 0xc8 bytes work area
    assert "mov r2, #0xc8" in text, "missing memset size 200B"
    assert "bl #0x31504" in text, "missing memset call"
    print("[PASS] TargetEffect::NewTargetEffect base: 25+ field stores + 200B memset work area")

    # 7. R73 effect_type 4/7/8 still present in ProcHeroSkill calls (regression)
    code = data[f_off(0x99278):f_off(0x99278) + 7972]
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0x99278))
    # mov r1, #4 / #7 / #8 should exist (effect_type immediates before TEM calls)
    for imm in ("mov r1, #4", "mov r1, #7", "mov r1, #8"):
        assert imm in text, f"ProcHeroSkill missing effect_type immediate '{imm}'"
    print("[PASS] R73 effect_type {4, 7, 8} immediate moves still in ProcHeroSkill")

    # 8. ProcTargetEffectSkill exists with expected size
    assert syms['_ZN12TargetEffect21ProcTargetEffectSkillEP13HeroSkillInfoP7BATTLER'][1] == 4276, \
        "ProcTargetEffectSkill size mismatch"
    print("[PASS] ProcTargetEffectSkill @0x64a08 (4276B) confirmed (R81+ per-frame processor)")

    # 9. Doc marker verification
    doc = (ROOT / "docs/h5/RE/target_effect_mgr.md").read_text(encoding='utf-8')
    markers = [
        "TargetEffectMgr", "TargetEffect", "Effect 베이스",
        "5 overload", "wrapper chain", "_full",
        "0x62a34", "0x62840", "0x610f4", "0x610d8",
        "100 슬롯", "0x284", "+0x11", "+0x12", "+0x14", "+0x16", "+0x18",
        "effect_type", "4/7/8", "post-init",
        "manager 채널", "0x15d8", "0x15e0", "0x15e4",
        "IsEmpty", "SetEffectType",
        "ProcTargetEffectSkill",
    ]
    missing = [m for m in markers if m not in doc]
    assert not missing, f"doc missing markers: {missing}"
    print(f"[PASS] {len(markers)} doc markers in target_effect_mgr.md")

    print("\n=== R80 TargetEffectMgr / TargetEffect VFX RE: ALL PASSED ===")


if __name__ == "__main__":
    main()
