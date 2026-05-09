"""한글 stat 라벨 string 의 .so 내 위치 탐색.

StateInGameMenu::DrawPropertyMenu 같은 status UI 함수 분석을 위해,
"적중", "회피", "크리티컬", "블록", "속도" 등 한글 stat 라벨이 .so 의
어느 주소에 위치하는지 + 어느 함수에서 reference 되는지 추적.

산출: work/h5/analysis/kr_stat_string_refs.tsv
"""
from __future__ import annotations
import pathlib
import re
import struct

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/kr_stat_string_refs.tsv"

KR_LABELS = [
    "적중", "회피", "크리티컬", "블록", "속도",
    "공격력", "방어력", "근접공격력", "장거리공격력",
    "마법공격력", "마법방어력", "물리방어력", "마법적중",
    "회복", "정확도", "관통", "반사", "민첩", "회복속도",
    "이동속도", "공격속도", "회전속도",
    "치명타", "치명상", "긴급회피", "액티브블록",
    "정신력", "방어",
]


def simple_demangle(mangled: str) -> str:
    if not mangled.startswith("_ZN"):
        return mangled
    s = mangled[3:]
    parts = []
    while s and s[0].isdigit():
        n = 0
        while s and s[0].isdigit():
            n = n * 10 + int(s[0])
            s = s[1:]
        if len(s) < n:
            break
        parts.append(s[:n])
        s = s[n:]
        if s.startswith("E"):
            break
    return "::".join(parts) if parts else mangled


def main() -> int:
    so = lief.parse(str(SO))

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    # rodata / data 모든 영역에서 UTF-8 한글 stat label byte sequence 검색.
    label_addrs: dict[str, list[int]] = {}
    for label in KR_LABELS:
        # UTF-8 인코딩
        bs = label.encode("utf-8")
        # null terminator 가 있는 주소만 (C string)
        label_addrs[label] = []
        for v0, v1, d in seg:
            i = 0
            while True:
                i = d.find(bs, i)
                if i < 0:
                    break
                # null terminator (0x00) 또는 string boundary check —
                # 단순 string 매칭은 false positive 많음. 일단 모두 수집.
                # 시작 byte 가 한글 첫 byte (≥0xE0) 면 확률 높음
                if i > 0 and d[i-1] != 0:
                    # not at string start, skip
                    i += 1
                    continue
                addr = v0 + i
                label_addrs[label].append(addr)
                i += 1

    print("=== 한글 stat label 후보 주소 ===")
    for label, addrs in label_addrs.items():
        if addrs:
            print(f"  {label:>14s}  {len(addrs):>3} 개 주소")
            for a in addrs[:3]:
                print(f"     0x{a:08x}")
            if len(addrs) > 3:
                print(f"     ... +{len(addrs)-3} more")

    # text 의 모든 ldr [pc, #imm] 로딩 추적해서, literal pool 에 위 주소들 있는 곳 찾기
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    text_secs = [(sec.virtual_address, bytes(sec.content)) for sec in so.sections if sec.name == ".text"]
    if not text_secs:
        print("[!] .text 섹션 없음")
        return 1

    # 함수 mapping
    addr_to_sym = {}
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        addr_to_sym.setdefault(a, (s.name or "", s.size))

    # 후보 주소 set
    candidate_addrs: dict[int, str] = {}
    for label, addrs in label_addrs.items():
        for a in addrs:
            candidate_addrs[a] = label

    def read_u32(va: int) -> int | None:
        for v0, v1, d in seg:
            if v0 <= va < v1 - 3:
                return struct.unpack_from("<I", d, va - v0)[0]
        return None

    def find_func(va: int) -> tuple[int, str] | None:
        best = None; best_addr = -1
        for fa, (n, sz) in addr_to_sym.items():
            if fa <= va < fa + sz and fa > best_addr:
                best = (fa, n); best_addr = fa
        return best

    refs = []  # (label, str_addr, code_va, func_addr, func_name)

    for sec_va, sec_data in text_secs:
        # disasm 전체 .text — 큰 비용이지만 한 번만.
        for ins in md.disasm(sec_data, sec_va):
            if ins.mnemonic == "ldr" and "[pc," in ins.op_str:
                # ldr rN, [pc, #N]  → literal pool 에서 32-bit value load
                try:
                    off = int(ins.op_str.rsplit(",", 1)[-1].strip(" []#"), 0)
                    literal_va = (ins.address + 8 + off) & ~3
                    val = read_u32(literal_va)
                except (ValueError, IndexError):
                    continue
                if val is None:
                    continue
                # val 이 후보 주소 와 같은지 (또는 인근 — 16 byte 이내)
                for cand_addr, lbl in candidate_addrs.items():
                    if abs(val - cand_addr) < 32:
                        fn = find_func(ins.address)
                        if fn:
                            refs.append((lbl, val, ins.address, fn[0], fn[1]))

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("label\tstr_addr\tcode_va\tfunc_addr\tfunc_demangled\n")
        for lbl, addr, code_va, fn_addr, fn_n in refs:
            f.write(f"{lbl}\t0x{addr:08x}\t0x{code_va:08x}\t0x{fn_addr:08x}\t{simple_demangle(fn_n)}\n")

    print(f"\n[+] {OUT} ({len(refs)} reference)")

    # 함수별 unique 한글 라벨 요약 — DrawPropertyMenu 같은 핵심 함수 식별
    print()
    print("== 함수별 unique 한글 라벨 요약 ==")
    by_fn: dict[str, set[str]] = {}
    for lbl, _, _, _, fn_n in refs:
        d = simple_demangle(fn_n)
        by_fn.setdefault(d, set()).add(lbl)
    for fn, lbls in sorted(by_fn.items(), key=lambda r: -len(r[1])):
        if len(lbls) >= 2:  # 2 이상의 stat label reference 가 있는 함수만 (UI 추정)
            print(f"  {fn}")
            print(f"    labels: {', '.join(sorted(lbls))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
