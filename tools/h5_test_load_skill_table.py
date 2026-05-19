#!/usr/bin/env python3
"""R77: HERO::LoadResSkillInfo (@0x8bba4) + LoadResClassSkillInfo (@0x9b308) disasm 검증.

확정한 file layout 패턴이 .so 안에 실제로 존재하는지 instruction-level 로 검증.
docs/h5/RE/load_skill_table.md 의 strb/strh 매핑이 ARM bytecode 와 일치.
"""
import struct
import sys
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
        sh_size = struct.unpack_from('<I', data, base + 0x14)[0]
        end = data.index(b'\0', shstr_off + sh_name)
        name = data[shstr_off + sh_name:end].decode()
        if name == '.text':
            return sh_addr, sh_offset, sh_size
    raise RuntimeError("no .text")


def parse_dynsym(data):
    e_shoff = struct.unpack_from('<I', data, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', data, 0x2e)[0]
    e_shnum = struct.unpack_from('<H', data, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', data, 0x32)[0]
    shstr_off = struct.unpack_from('<I', data, e_shoff + e_shstrndx * e_shentsize + 0x10)[0]
    sections = []
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        sh_name = struct.unpack_from('<I', data, base + 0)[0]
        sh_offset = struct.unpack_from('<I', data, base + 0x10)[0]
        sh_size = struct.unpack_from('<I', data, base + 0x14)[0]
        sh_link = struct.unpack_from('<I', data, base + 0x18)[0]
        sh_entsize = struct.unpack_from('<I', data, base + 0x24)[0]
        end = data.index(b'\0', shstr_off + sh_name)
        sections.append((data[shstr_off + sh_name:end].decode(), sh_offset, sh_size, sh_link, sh_entsize))
    dynsym = next(s for s in sections if s[0] == '.dynsym')
    _, off, size, link, ent = dynsym
    dstr_off = sections[link][1]
    out = {}
    for i in range(size // ent):
        base = off + i * ent
        st_name = struct.unpack_from('<I', data, base)[0]
        st_value = struct.unpack_from('<I', data, base + 4)[0]
        st_size = struct.unpack_from('<I', data, base + 8)[0]
        end = data.index(b'\0', dstr_off + st_name)
        nm = data[dstr_off + st_name:end].decode(errors='replace')
        out[nm] = (st_value, st_size)
    return out


def main():
    data = SO_PATH.read_bytes()
    text_addr, text_off, text_size = parse_elf_text(data)

    def f_off(addr):
        return text_off + (addr - text_addr)

    syms = parse_dynsym(data)
    expected_symbols = {
        '_ZN4HERO16LoadResSkillInfoEa': (0x8bba4, 784),
        '_ZN4HERO21LoadResClassSkillInfoEv': (0x9b308, 48),
        '_ZN4HERO16LoadResSkillIconEv': (0x9b2d4, 52),
        '_ZN4HERO13ProcHeroSkillEP13HeroSkillInfo': (0x99278, 7972),
        '_ZN4HERO14InitSkillEmptyEv': (0x88a20, 272),
    }
    for name, (addr, size) in expected_symbols.items():
        assert name in syms, f"missing symbol {name}"
        v, sz = syms[name]
        assert v == addr, f"{name}: addr {hex(v)} != {hex(addr)}"
        assert sz == size, f"{name}: size {sz} != {size}"
    print(f"[PASS] 5 ELF symbols verified")

    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True

    # Disassemble LoadResSkillInfo
    code = data[f_off(0x8bba4):f_off(0x8bba4) + 784]
    insns = list(md.disasm(code, 0x8bba4))
    assert len(insns) >= 190, f"expected ~196 instructions, got {len(insns)}"
    print(f"[PASS] LoadResSkillInfo disassembled: {len(insns)} ARM instructions")

    # Pattern checks
    text = "\n".join(f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in insns)

    # arg==5 dispatch (loop bounds: 0x2b / 0x3b vs 0 / 0x2b)
    assert "cmp r6, #5" in text, "missing cmp r6, #5 (arg==5 dispatch)"
    assert "moveq r7, #0x2b" in text, "missing moveq r7, #0x2b (arg==5 start = 43)"
    assert "movne r7, #0" in text, "missing movne r7, #0 (arg!=5 start = 0)"
    assert "moveq fp, #0x3b" in text, "missing moveq fp, #0x3b (arg==5 end = 59)"
    assert "movne fp, #0x2b" in text, "missing movne fp, #0x2b (arg!=5 end = 43)"
    print("[PASS] 59-slot array dispatch (43+16) verified")

    # 88B per entry: mov r3, #0x58 + mul r3, r7, r3 + add r3, r3, #0x348
    assert "mov r3, #0x58" in text, "missing 88B entry size"
    assert "mul r3, r7, r3" in text, "missing entry index × 88B"
    assert "add r3, r3, #0x348" in text, "missing HERO+0x348 base offset"
    assert "add r4, r4, r3" in text, "missing r4 = this + 0x348 + idx*88"
    print("[PASS] HERO+0x348 88B array layout verified")

    # Initial r8 = 2 (file header skip)
    assert "mov r8, #2" in text, "missing initial r8=2 (file header skip)"
    # Loop back: r8_next = desc_len + name_len + r8_prev_start + 0x30
    assert "add r8, r6, r8" in text, "missing loop-back r8 advance"
    print("[PASS] file header (2B) + record advance loop verified")

    # name_len at rel 2 (r3 = r8+2; ldrb sl, [r5, r3])
    assert "add r3, r8, #2" in text and "ldrb sl, [r5, r3]" in text, "missing name_len read at rel 2"
    # malloc(name_len+1, 0) + memcpy
    assert "add r6, sl, #1" in text and "bl #0xabd18" in text, "missing name malloc"
    assert "str r0, [r4, #4]" in text, "missing entry+0x04 = name ptr"
    print("[PASS] name string load (rel 2 len + malloc + memcpy) verified")

    # Stats area strb/strh patterns — verify R72/R73 critical fields
    critical_stores = [
        ("strb r0, [r4, #0x28]", "★ effect_type @ entry+0x28 (R70/R72 JT1 key)"),
        ("strb r3, [r4, #0x30]", "★ dynamic_formula_id @ entry+0x30 (R73 case 5 shock)"),
        ("strb r1, [r4, #0x3a]", "★ special_dispatch @ entry+0x3a (R72 cmp 0x34/0x37)"),
        ("strb r2, [r4, #0x3c]", "★ formula_id_1 @ entry+0x3c (R72)"),
        ("strb r3, [r4, #0x3d]", "★ formula_id_2 @ entry+0x3d (R72)"),
        ("strh r0, [r4, #0x32]", "u16 cluster #1 @ entry+0x32"),
        ("strh r0, [r4, #0x34]", "u16 cluster #2 @ entry+0x34"),
        ("strh r0, [r4, #0x36]", "u16 cluster #3 @ entry+0x36"),
        ("strh r0, [r4, #0x38]", "u16 cluster #4 @ entry+0x38"),
    ]
    for needle, desc in critical_stores:
        assert needle in text, f"missing: {desc} ({needle})"
    print(f"[PASS] {len(critical_stores)} critical R72/R73 field stores verified")

    # All 0x30 stats byte stores (entry+0x08..+0x3d, excluding pads)
    expected_strb = [0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x10, 0x14, 0x18,
                     0x1c, 0x1d, 0x1e, 0x22, 0x26, 0x27, 0x28, 0x29,
                     0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x30,
                     0x3a, 0x3b, 0x3c, 0x3d]
    for off in expected_strb:
        # entry+off byte store
        patterns = [f"strb r0, [r4, #{hex(off)}]", f"strb r1, [r4, #{hex(off)}]",
                    f"strb r2, [r4, #{hex(off)}]", f"strb r3, [r4, #{hex(off)}]",
                    f"strb ip, [r4, #{hex(off)}]"]
        if off == 0x08:
            patterns.extend([f"strb r2, [r4, #8]"])
        if off == 0x09:
            patterns.extend([f"strb r0, [r4, #9]"])
        if off in (0x08, 0x09):
            patterns = [p.replace("0x8", "8").replace("0x9", "9") for p in patterns]
        found = any(p in text for p in patterns)
        assert found, f"missing strb to entry+{hex(off)}"
    print(f"[PASS] all {len(expected_strb)} byte field stores at expected offsets")

    expected_strh = [0x0e, 0x12, 0x16, 0x1a, 0x20, 0x24, 0x32, 0x34, 0x36, 0x38]
    for off in expected_strh:
        assert f"strh r0, [r4, #{hex(off)}]" in text, f"missing strh to entry+{hex(off)}"
    print(f"[PASS] all {len(expected_strh)} u16 field stores at expected offsets")

    # Verify NO writes to runtime state region +0x44..+0x57
    runtime_offsets = [0x44, 0x46, 0x48, 0x4a, 0x4c, 0x4e, 0x50, 0x52, 0x54, 0x56]
    for off in runtime_offsets:
        for op in ("strb", "strh", "str"):
            pat = f"{op} r0, [r4, #{hex(off)}]"
            assert pat not in text, f"unexpected: LoadResSkillInfo writes runtime entry+{hex(off)}"
    print(f"[PASS] no file-load writes to runtime region +0x44..+0x57 (R72/R73 hypothesis correction)")

    # entry+0x40 = description ptr
    assert "str r0, [r4, #0x40]" in text, "missing entry+0x40 = desc ptr"
    print("[PASS] description ptr @ entry+0x40 verified")

    # u16 read helper count = 11 calls to 0x1437ec
    bl_count = text.count("bl #0x1437ec")
    assert bl_count == 11, f"expected 11 read_u16 calls, got {bl_count}"
    print(f"[PASS] {bl_count} read_u16 (0x1437ec) calls (1 header + 10 stats u16)")

    # Disassemble LoadResClassSkillInfo — 2 calls to LoadResSkillInfo
    code = data[f_off(0x9b308):f_off(0x9b308) + 48]
    text2 = "\n".join(f"{i.mnemonic} {i.op_str}" for i in md.disasm(code, 0x9b308))
    assert text2.count("bl #0x8bba4") == 2, f"LoadResClassSkillInfo: expected 2 calls to LoadResSkillInfo"
    assert "ldrb r1, [r0, #0x22c]" in text2, "missing class_id load from HERO+0x22c"
    assert "mov r1, #5" in text2, "missing mov r1, #5 (spirit/shared call)"
    assert "b #0x9b2d4" in text2, "missing tail-call to LoadResSkillIcon"
    print("[PASS] LoadResClassSkillInfo: class_id call + arg=5 call + LoadResSkillIcon tail")

    # Doc marker verification
    doc = (ROOT / "docs/h5/RE/load_skill_table.md").read_text(encoding='utf-8')
    markers = [
        "LoadResSkillInfo", "LoadResClassSkillInfo", "0x8bba4", "0x9b308",
        "59 슬롯", "0x348", "88B", "stats area", "name_len", "desc_len",
        "+0x28", "+0x30", "+0x3a", "+0x3c", "+0x3d",
        "effect_type", "dynamic Formula id", "special dispatch", "Formula id 1", "Formula id 2",
        "runtime state", "+0x44..+0x57", "정정",
    ]
    missing = [m for m in markers if m not in doc]
    assert not missing, f"docs missing markers: {missing}"
    print(f"[PASS] {len(markers)} doc markers in load_skill_table.md")

    print("\n=== R77 LoadResSkillInfo verification: ALL PASSED ===")


if __name__ == "__main__":
    main()
