"""Round 48 / 2OA-6: task[0xa848] 의 실제 write/read 패턴 (정확본).

이전 분석 정정: BL FUN_85578c 직후의 `str r2, [r3]` 는 사실 r3=local stack ptr
이고, &task[0xa848] 포인터를 로컬 변수에 저장하는 prelude. 실제 task[0xa848]
sub-struct access는 r2 (& task[0xa848] 사본) 를 통해 더 멀리에서 일어난다.

전략:
1. BL FUN_85578c 직후 r0/r2 가 &task[0xa848] 라는 사실을 추적.
2. 그 register 가 dead 가 될 때까지 (다음 BL 까지) 모든 LDRB/LDR/STRB/STR 의
   [Rb, #imm] 패턴에서 imm 을 수집.
3. r2 → 로컬 stack 으로 저장된 경우는 stack-relative ldr 로 reload 한 후 [Rx, #imm]
   사용 패턴도 추적. 단순화를 위해 BL 후 32 instructions 윈도우에서 r0/r2/r3/r5/r6
   를 base 로 한 LDR/STR offsets 모두 집계.
"""
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

SITES = [
    0x57036, 0x5707c, 0x575f6, 0x57602, 0x5760c, 0x579a0, 0x579aa,
    0x57bc6, 0x57bd2, 0x857ba, 0x85ab8, 0x85b2e, 0x85e98, 0x85f56,
    0x85f82, 0x85fe4, 0x86010, 0x86062, 0x861d2, 0x862de, 0x86a34,
    0x87c60, 0x88a44, 0x88ed2, 0x89b2c, 0x8a06a, 0x8ad44, 0x8d890,
    0x901c4, 0x905be,
]


def parse_off(op_str: str):
    if "#" in op_str:
        try:
            tail = op_str.split("#")[-1]
            off_str = tail.rstrip("]").strip()
            return int(off_str, 0)
        except Exception:
            return None
    if "[" in op_str and "]" in op_str:
        return 0
    return None


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ldr_offsets = Counter()
    str_offsets = Counter()
    ldrb_offsets = Counter()
    strb_offsets = Counter()

    per_site_accesses = defaultdict(list)

    for bl in SITES:
        end = min(bl + 4 + 0x100, len(DATA))  # 64-instr window (256 bytes)
        # Track which regs currently hold &task[0xa848]
        # Start: r0 = &task[0xa848] after BL
        tracked = {"r0"}
        # Also if `adds r2, r0, #0` etc., propagate
        saw_addr_count = 0

        for ins in md.disasm(DATA[bl + 4:end], bl + 4):
            mnem = ins.mnemonic
            op = ins.op_str

            # Stop at next BL/B (different function call invalidates r2)
            if mnem in ("bl", "blx"):
                break
            if mnem in ("pop", "bx") and "lr" in op:
                break

            # Track copies of tracked registers
            if mnem in ("adds", "mov", "movs"):
                # `adds r2, r0, #0` or `mov r2, r0` or `movs r2, r0`
                parts = [p.strip() for p in op.split(",")]
                if len(parts) >= 2:
                    dst = parts[0]
                    src = parts[1]
                    if mnem == "adds" and len(parts) == 3 and parts[2].strip() == "#0":
                        if src in tracked:
                            tracked.add(dst)
                            saw_addr_count += 1
                            continue
                    elif mnem in ("mov", "movs"):
                        if src in tracked:
                            tracked.add(dst)
                            saw_addr_count += 1
                            continue
                    # if dst was tracked but src isn't, dst loses tracking
                    if dst in tracked:
                        tracked.discard(dst)

            # Track LDR/STR through tracked register
            if mnem.startswith(("ldr", "str")):
                for reg in tracked:
                    if f"[{reg}" in op:
                        off = parse_off(op)
                        if off is None:
                            continue
                        if mnem == "ldr":
                            ldr_offsets[off] += 1
                        elif mnem == "ldrb":
                            ldrb_offsets[off] += 1
                        elif mnem == "ldrh":
                            ldr_offsets[off] += 1  # half-word, lump in
                        elif mnem == "str":
                            str_offsets[off] += 1
                        elif mnem == "strb":
                            strb_offsets[off] += 1
                        per_site_accesses[bl].append((ins.address, mnem, op))
                        # If STR via tracked reg, the tracked reg is being WRITTEN TO
                        # (data through it) — but tracked reg itself stays the same.
                        # If LDR loads into the tracked reg (e.g. ldr r0, [r0, #4]),
                        # the tracked reg is now CLOBBERED (no longer &task[0xa848]).
                        if mnem in ("ldr", "ldrb", "ldrh"):
                            parts = [p.strip() for p in op.split(",")]
                            if parts and parts[0] == reg:
                                tracked.discard(reg)
                        break

    print("=== task[0xa848]+offset access (corrected with reg-tracking) ===\n")
    print(f"--- WORD READ (LDR) ---")
    for off, cnt in sorted(ldr_offsets.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print(f"\n--- BYTE READ (LDRB) ---")
    for off, cnt in sorted(ldrb_offsets.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print(f"\n--- WORD WRITE (STR) ---")
    for off, cnt in sorted(str_offsets.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print(f"\n--- BYTE WRITE (STRB) ---")
    for off, cnt in sorted(strb_offsets.items()):
        print(f"  +0x{off:04x}: {cnt}")

    print("\n=== Per-site accesses ===")
    for bl in SITES:
        accs = per_site_accesses[bl]
        if accs:
            print(f"\n  BL@0x{bl:05x}: {len(accs)} accesses")
            for addr, mnem, op in accs[:8]:
                print(f"    0x{addr:05x} {mnem:6} {op}")


if __name__ == "__main__":
    main()
