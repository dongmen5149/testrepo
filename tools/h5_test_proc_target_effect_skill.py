#!/usr/bin/env python3
"""R81: TargetEffect::ProcTargetEffectSkill (@0x64a08, 4276B) overview 검증.

검증 항목:
- 함수 크기 4276B, ~1069 instr, jumptable 없음 (pure if/else cascade)
- skill_info 12 distinct file-loaded field 읽기 (R77 영역 광범위 활용)
- R79 dead reads +0x4a/+0x4e 의 본 함수 read 존재 (default 0 path)
- Top call graph: Formula::calc 14x / TEM::NewTargetEffect 6x / IncreaseHP 4x /
  AddCurseSkill 3x / NewHitEffect 2x / ApplyAddEffect 2x
- class_id (HERO+0x22c) 6 회 read + GUNNER combo (HERO+0x269) 6 회 read
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

    # 1. Symbol verification
    name = '_ZN12TargetEffect21ProcTargetEffectSkillEP13HeroSkillInfoP7BATTLER'
    assert name in syms, f"missing {name}"
    addr, size = syms[name]
    assert addr == 0x64a08, f"addr {hex(addr)} != 0x64a08"
    assert size == 4276, f"size {size} != 4276"
    print(f"[PASS] ProcTargetEffectSkill @0x64a08 (4276B) verified")

    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)

    code = data[f_off(0x64a08):f_off(0x64a08) + 4276]
    insns = list(md.disasm(code, 0x64a08))
    assert len(insns) >= 1060, f"expected ~1069 instructions, got {len(insns)}"
    print(f"[PASS] disassembled {len(insns)} ARM instructions (~1069 expected)")

    # 2. NO jumptables (no addls pc)
    text = "\n".join(f"{i.mnemonic} {i.op_str}" for i in insns)
    jt_count = sum(1 for i in insns if i.mnemonic == 'addls' and 'pc' in i.op_str)
    assert jt_count == 0, f"expected 0 jumptables (pure cascade), got {jt_count}"
    print("[PASS] 0 jumptables (pure if/else cascade dispatch, 4276B/1069 instr)")

    # 3. Top call graph counts
    call_specs = [
        ('0x7749c', 14, 'Formula::calc'),
        ('0x49b6c', 15, 'CHAR::GetSpritePtr'),
        ('0xda51c', 12, 'SPRITE::GetExtraDataPtr'),
        ('0xcfd8c', 8, 'OBJECT::GetX'),
        ('0xcfd9c', 8, 'OBJECT::GetY'),
        ('0x62d40', 6, 'TEM::NewTargetEffect_min (recursive VFX spawn)'),
        ('0x4b41c', 4, 'BATTLER::IncreaseHP'),
        ('0x4b134', 3, 'BATTLER::AddCurseSkill'),
        ('0x646ec', 2, 'TargetEffect::NewHitEffect'),
        ('0x4bdb4', 2, 'BATTLER::ApplyAddEffect'),
    ]
    for tgt, expected, desc in call_specs:
        actual = text.count(f"bl #{tgt}")
        assert actual == expected, f"bl {tgt} ({desc}): expected {expected}, got {actual}"
    print(f"[PASS] {len(call_specs)} top call counts verified (Formula::calc 14x, TEM recursive 6x, IncreaseHP 4x, AddCurseSkill 3x)")

    # 4. skill_info file-loaded field reads (R77 영역 활용)
    skill_info_reads = {
        '#0x32]': 3,    # R70 4xu16 primary
        '#0x36]': 3,    # R70 4xu16 #3
        '#0x2f]': 3,    # R77 file byte
        '#0x29]': 3,    # R70 effect2
        '#0xa]': 3,     # R70 flag
        '#0x3a]': 2,    # R72 special_dispatch
        '#0x1c]': 2,    # R70 mode
        '#0x2a]': 1,    # R70 formula_arg
        '#0x2b]': 1,    # R77 file byte
    }
    for off_marker, min_count in skill_info_reads.items():
        actual = text.count(off_marker)
        assert actual >= min_count, f"skill_info {off_marker} reads: expected >={min_count}, got {actual}"
    print(f"[PASS] {len(skill_info_reads)} distinct skill_info file-loaded fields read (R77 영역 광범위 활용)")

    # 5. R79 dead reads still present in ProcTargetEffectSkill (default 0 path)
    dead_reads = {
        '#0x4a]': 1,   # R72 SP delta (dead)
        '#0x4e]': 1,   # R73 knight_threshold (dead)
    }
    for off, min_count in dead_reads.items():
        actual = text.count(off)
        assert actual >= min_count, f"R79 dead read {off}: expected >={min_count}, got {actual}"
    print(f"[PASS] R79 dead reads {list(dead_reads.keys())} present (default 0 → no-op path 일관성)")

    # 6. HERO field reads (class dispatch)
    hero_reads = [
        ('#0x22c]', 6, 'HERO::class_id (5-class dispatch)'),
        ('#0x269]', 6, 'HERO::gunner_combo (R72)'),
        ('#0x294]', 2, 'HERO+0x294 skill state flag (R72)'),
    ]
    for off, expected, desc in hero_reads:
        actual = text.count(off)
        assert actual >= expected, f"HERO {off} ({desc}): expected >={expected}, got {actual}"
    print(f"[PASS] HERO field reads: class_id 6x + gunner_combo 6x + skill_state 2x (class 분기 + GUNNER 추가 처리)")

    # 7. TargetEffect state cluster reads (per-frame state machine)
    state_cluster = ['#0xab]', '#0xac]', '#0xad]', '#0xae]', '#0xaf]', '#0xc0]']
    found = sum(1 for marker in state_cluster if marker in text)
    assert found >= 5, f"expected ≥5 TargetEffect state cluster reads, got {found}/{len(state_cluster)}"
    print(f"[PASS] TargetEffect state cluster +0xab..+0xc0: {found}/{len(state_cluster)} reads (per-frame state machine)")

    # 8. Doc marker verification
    doc = (ROOT / "docs/h5/RE/proc_target_effect_skill.md").read_text(encoding='utf-8')
    markers = [
        "ProcTargetEffectSkill", "0x64a08", "4276B",
        "Jumptable 없음", "cascade",
        "Formula::calc", "14x",
        "TEM", "재귀", "IncreaseHP", "AddCurseSkill",
        "NewHitEffect", "ApplyAddEffect",
        "+0x22c", "+0x269", "class_id", "GUNNER",
        "+0x4a", "+0x4e", "dead read",
        "R77", "R79", "+0x32", "+0x36",
        "R82+",
    ]
    missing = [m for m in markers if m not in doc]
    assert not missing, f"doc missing markers: {missing}"
    print(f"[PASS] {len(markers)} doc markers in proc_target_effect_skill.md")

    print("\n=== R81 ProcTargetEffectSkill overview RE: ALL PASSED ===")


if __name__ == "__main__":
    main()
