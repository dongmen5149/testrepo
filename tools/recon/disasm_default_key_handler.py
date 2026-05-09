"""§4.4 후속 — FUN_00064048 (default key handler) capstone 디스어셈블 (자동 분석 2G).

배경 (2026-05-10):
  state[0x94] 가 3-페이지 UI 탭 인덱스로 재해석됨에 따라 진짜 battle 트리거는 별도 위치.
  FUN_00070f34 (key handler) 의 default 분기는 FUN_00064048 호출 →
  키 '1'/'3'/'*' 외 모든 키가 여기로 흘러감 → 게임 상태 머신 본체 후보.

Ghidra 실패 모드:
  all_decompiled.c 에서 FUN_00064048 은 `{ FUN_0004ad10(); }` stub 처럼 보임.
  그러나 raw bytes 는 push {r4,r5,r7,lr} + push {r7} + sub sp,#0x3c + GOT setup → 진짜 함수.
  Ghidra 가 control flow 추적 실패 → "Subroutine does not return" 마크.

이번 도구:
  1. 0x64048 ~ 0x64852 (2058 bytes) capstone 디스어셈블 (auto-skip)
  2. BL 호출 통계 (top callees → 어떤 sub-system 호출하는지)
  3. cmp #imm 분포 (state machine 분기 식별)
  4. PC-rel LDR → 모든 literal 추출 + 카테고리화
  5. 키 코드 비교 패턴 자동 검색 (cmp Rn, #ASCII)
  6. state offset access 패턴 (str/ldr [Rn, #imm])
"""
from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
OUT = REPO / "work" / "h3" / "default_key_handler.json"

START = 0x00064048
END = 0x00064852  # FUN_00064852 시작 직전

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))


def walk_with_skip(data: bytes, start: int, end: int) -> tuple[list[dict], list[tuple[int, int]]]:
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    instrs: list[dict] = []
    blocks: list[tuple[int, int]] = []
    pos = start
    while pos < end:
        chunk = data[pos:end]
        block_first = pos
        last_addr = pos
        any_emitted = False
        for ins in md.disasm(chunk, pos):
            instrs.append({
                "addr": ins.address,
                "mnem": ins.mnemonic,
                "op_str": ins.op_str,
                "size": ins.size,
                "bytes": bytes(ins.bytes).hex(),
            })
            last_addr = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            blocks.append((block_first, last_addr))
            pos = last_addr
        pos += 2
        if pos > end:
            break
    return instrs, blocks


def main() -> None:
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return
    data = bytes(BIN.read_bytes())
    print(f"=== FUN_00064048 (default key handler, {END-START:#x} bytes / {(END-START)/1024:.1f} KB) ===")

    instrs, code_blocks = walk_with_skip(data, START, END)
    total_code = sum(e - s for s, e in code_blocks)
    print(f"\ncode_blocks: {len(code_blocks)}, total decoded: {total_code} bytes ({total_code/(END-START)*100:.1f}%)")
    for s, e in code_blocks[:5]:
        print(f"  0x{s:08x} ~ 0x{e:08x}  ({e-s:4d} bytes)")
    if len(code_blocks) > 5:
        print(f"  ... ({len(code_blocks)-5} more)")

    # BL targets
    bl_targets = []
    for ins in instrs:
        if ins["mnem"] in ("bl", "blx"):
            tok = ins["op_str"].strip().lstrip("#")
            if tok.startswith("0x"):
                try:
                    bl_targets.append(int(tok, 16))
                except ValueError:
                    pass
    bl_freq = Counter(bl_targets)
    print(f"\n=== BL stats: {len(bl_targets)} calls ({sum(c for t,c in bl_freq.items() if t in VENEERS)} veneer / {sum(c for t,c in bl_freq.items() if t not in VENEERS)} direct) ===")
    print("top BL targets:")
    for tgt, c in bl_freq.most_common(25):
        v_marker = " (veneer)" if tgt in VENEERS else ""
        print(f"  0x{tgt:08x}: {c}{v_marker}")

    # cmp Rn, #imm distribution → state machine arm detection
    cmp_imms = Counter()
    cmp_imm_sites = []  # (addr, value)
    for ins in instrs:
        if ins["mnem"] in ("cmp", "cmn"):
            for tok in ins["op_str"].split(","):
                tok = tok.strip()
                if tok.startswith("#"):
                    try:
                        v = int(tok[1:], 0)
                        cmp_imms[v] += 1
                        cmp_imm_sites.append((ins["addr"], v))
                    except ValueError:
                        pass
    print("\n=== cmp Rn, #imm dist (state arm / key code detection) ===")
    for v, c in cmp_imms.most_common(30):
        # ASCII-printable key code marker
        ascii_marker = ""
        if 0x20 <= v < 0x7F:
            ascii_marker = f"  ('{chr(v)}')"
        if v == 0xF0 or v == -0x10 or v == 0xFFF0:
            ascii_marker = "  (-0x10 special)"
        print(f"  cmp #0x{v:02x} ({v:4d}): {c}{ascii_marker}")

    # Show all cmp sites in code order (state machine flow)
    print("\n=== cmp sites in code order (head 40) - state machine flow ===")
    for addr, v in cmp_imm_sites[:40]:
        ascii_marker = ""
        if 0x20 <= v < 0x7F:
            ascii_marker = f" ('{chr(v)}')"
        print(f"  0x{addr:08x}: cmp #0x{v:02x}{ascii_marker}")
    if len(cmp_imm_sites) > 40:
        print(f"  ... ({len(cmp_imm_sites)-40} more)")

    # PC-rel LDR resolution
    pcrel_ldrs = []
    for ins in instrs:
        mnem = ins["mnem"]
        op_str = ins["op_str"]
        addr = ins["addr"]
        if mnem in ("ldr", "ldr.w") and "[pc," in op_str.replace(" ", ""):
            try:
                imm_str = op_str.split("#", 1)[1].rstrip(" ]")
                imm = int(imm_str, 0)
            except (IndexError, ValueError):
                continue
            pc = (addr + 4) & ~3
            target = pc + imm
            if 0 <= target < len(data) - 4:
                value = struct.unpack("<I", data[target:target+4])[0]
                pcrel_ldrs.append({
                    "site": addr, "target": target, "value": value,
                })

    print(f"\n=== PC-rel LDR: {len(pcrel_ldrs)} sites ===")
    # Group by value distribution
    vals = Counter(p["value"] for p in pcrel_ldrs)
    print("top distinct literal values:")
    for v, c in vals.most_common(20):
        sv = struct.unpack("<i", struct.pack("<I", v))[0]
        marker = ""
        if v >= 0xFFFFF000:
            marker = " (negative GOT-rel offset)"
        elif 0x9000 <= v <= 0xC000:
            marker = " (GOT slot offset)"
        elif 0x10000 <= v <= 0xB0000:
            marker = " (binary addr)"
        elif v < 0x100:
            marker = " (small int / state arm)"
        print(f"  0x{v:08x} ({sv:11d}): {c}x{marker}")

    # str/strb [Rn, #imm] — state offset write
    state_writes = []  # (addr, base_reg, offset)
    state_reads = []
    for ins in instrs:
        op_str = ins["op_str"]
        if "[" not in op_str or "#" not in op_str:
            continue
        mnem = ins["mnem"]
        # Parse "Rt, [Rn, #imm]"
        try:
            parts = op_str.split(",", 1)  # "Rt", "[Rn, #imm]"
            if len(parts) < 2:
                continue
            mem_part = parts[1].strip()
            if not mem_part.startswith("["):
                continue
            inside = mem_part.strip("[]").strip()
            if "#" not in inside:
                continue
            base, off = inside.split(",", 1)
            off = off.strip().rstrip("]")
            if not off.startswith("#"):
                continue
            imm = int(off[1:], 0)
            if mnem in ("str", "strb", "strh", "str.w", "strb.w", "strh.w"):
                state_writes.append((ins["addr"], base.strip(), imm))
            elif mnem in ("ldr", "ldrb", "ldrh", "ldr.w", "ldrb.w", "ldrh.w") and "pc" not in inside:
                state_reads.append((ins["addr"], base.strip(), imm))
        except (ValueError, IndexError):
            continue

    print(f"\n=== state writes (str/strb/strh): {len(state_writes)} sites ===")
    write_off_counter = Counter(o for _, _, o in state_writes)
    print("top write offsets (state machine fields):")
    for off, c in write_off_counter.most_common(20):
        marker = ""
        if off == 0x94:
            marker = " ⭐ state[0x94] (page index)"
        elif off == 0x460:
            marker = " ⭐ state[0x460] (flag from FUN_00070f34)"
        elif off == 0x9c:
            marker = " (state[0x9c] from FUN_00070f34)"
        print(f"  +0x{off:03x} ({off:4d}): {c}x{marker}")

    print(f"\n=== state reads (ldr/ldrb/ldrh): {len(state_reads)} sites ===")
    read_off_counter = Counter(o for _, _, o in state_reads)
    print("top read offsets:")
    for off, c in read_off_counter.most_common(20):
        marker = ""
        if off == 0x94:
            marker = " ⭐ state[0x94] (page index)"
        elif off == 0x460:
            marker = " ⭐ state[0x460]"
        print(f"  +0x{off:03x} ({off:4d}): {c}x{marker}")

    # Save JSON
    out = {
        "function": "FUN_00064048",
        "label": "default_key_handler",
        "addr_start": f"0x{START:08x}",
        "addr_end": f"0x{END:08x}",
        "size_bytes": END - START,
        "code_blocks": [
            {"start": f"0x{s:08x}", "end": f"0x{e:08x}", "size": e - s}
            for s, e in code_blocks
        ],
        "instr_count": len(instrs),
        "total_code_bytes": total_code,
        "bl_total": len(bl_targets),
        "bl_targets_top": [
            {"target": f"0x{t:08x}", "count": c, "is_veneer": t in VENEERS}
            for t, c in bl_freq.most_common(40)
        ],
        "cmp_imm_dist": [
            {"imm": v, "count": c, "ascii": chr(v) if 0x20 <= v < 0x7F else None}
            for v, c in cmp_imms.most_common(50)
        ],
        "cmp_sites": [
            {"addr": f"0x{a:08x}", "imm": v, "ascii": chr(v) if 0x20 <= v < 0x7F else None}
            for a, v in cmp_imm_sites
        ],
        "pcrel_ldr_count": len(pcrel_ldrs),
        "pcrel_ldr_top_values": [
            {"value": f"0x{v:08x}", "count": c}
            for v, c in vals.most_common(40)
        ],
        "state_write_offsets": [
            {"offset": f"0x{o:03x}", "count": c}
            for o, c in write_off_counter.most_common(40)
        ],
        "state_read_offsets": [
            {"offset": f"0x{o:03x}", "count": c}
            for o, c in read_off_counter.most_common(40)
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
