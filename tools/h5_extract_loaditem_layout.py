"""ItemTable::LoadItemTable 의 csv read → struct store 시퀀스 자동 추출.

패턴:
  bl ByteToInt16 (r0=file, r1=csv_off) → r0 = u16 from csv[csv_off]
  bl ByteToInt32 (r0=file, r1=csv_off) → r0 = u32 from csv[csv_off]
  ldrb rN, [r7, csv_off]               → byte read

  직후:
  strh r0, [struct_ptr, #N]            → struct[N] = u16
  str r0, [struct_ptr, #N]             → struct[N] = u32
  strb rN, [struct_ptr, #N]            → struct[N] = u8

추적: r1 (csv_off) 와 store 의 struct offset 매핑.

산출: work/h5/analysis/loaditem_csv_layout.tsv
"""
from __future__ import annotations
import pathlib

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/loaditem_csv_layout.tsv"

TARGET = "_ZN9ItemTable13LoadItemTableEa"
B2I16 = "_ZN10StaticUtil11ByteToInt16EPhi"
B2I32 = "_ZN10StaticUtil11ByteToInt32EPhi"

# EquipItem 영역 (cat 1-11): 0xa3cf0 ~ 0xa4060
EQUIP_START = 0xa3cf0
EQUIP_END   = 0xa4060


def main() -> int:
    so = lief.parse(str(SO))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    addrs = {}
    for s in so.symbols:
        if s.value and s.size:
            addrs[s.name or ""] = s.value & ~1

    fn_addr = addrs.get(TARGET)
    fn_sz = next((s.size for s in so.symbols if s.name == TARGET and s.size), None)
    b2i16 = addrs.get(B2I16)
    b2i32 = addrs.get(B2I32)
    if not fn_addr or not b2i16:
        print(f"[!] symbol 없음")
        return 1

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def get_data(va, sz):
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0: va - v0 + sz])
        return None

    data = get_data(fn_addr, fn_sz)
    ins_list = list(md.disasm(data, fn_addr))
    # filter EquipItem 영역
    ins_eq = [ins for ins in ins_list if EQUIP_START <= ins.address < EQUIP_END]

    # register state — r1 (csv_off arg), r0 (read result), struct +offset 추적
    rows = []
    state: dict[str, int | None] = {}
    last_read_kind = None  # 'u16' / 'u32' / 'u8' (last read 의 결과 type)
    last_read_csv_off = None
    pending_struct_off = None  # next strh/str/strb 의 store 로 해석

    for ins in ins_eq:
        m = ins.mnemonic
        op = ins.op_str

        # mov r1, #imm — csv_off candidate
        if m in ("mov", "movs", "movw") and op.startswith("r1, #"):
            try:
                state["r1"] = int(op.split("#")[1], 0)
            except ValueError:
                state["r1"] = None
        elif m == "add" and op.startswith("r1,") and "#" in op:
            # add r1, rS, #imm
            parts = op.split(",")
            if len(parts) >= 3 and parts[2].strip().startswith("#"):
                src = parts[1].strip()
                src_val = state.get(src)
                if src_val is not None:
                    try:
                        state["r1"] = src_val + int(parts[2].strip()[1:], 0)
                    except ValueError:
                        state["r1"] = None
                else:
                    state["r1"] = None
        elif m in ("mov", "movs") and op.startswith("r1,"):
            # mov r1, rS
            parts = op.split(",")
            src = parts[1].strip() if len(parts) >= 2 else ""
            state["r1"] = state.get(src) if src in state else None
        # sb tracking (r9) — 자주 csv_off accumulator
        elif m in ("mov", "movs") and op.startswith("sb,"):
            parts = op.split(",")
            rhs = parts[1].strip() if len(parts) >= 2 else ""
            if rhs.startswith("#"):
                try:
                    state["sb"] = int(rhs[1:], 0)
                except ValueError:
                    state["sb"] = None
            else:
                state["sb"] = state.get(rhs)
        elif m == "add" and op.startswith("sb,"):
            parts = op.split(",")
            if len(parts) >= 3:
                src = parts[1].strip(); rhs = parts[2].strip()
                src_val = state.get(src)
                if rhs.startswith("#") and src_val is not None:
                    try:
                        state["sb"] = src_val + int(rhs[1:], 0)
                    except ValueError:
                        state["sb"] = None

        # bl ByteToInt16 / ByteToInt32
        if m == "bl" and op.startswith("#"):
            try:
                target = int(op[1:], 0) & ~1
            except ValueError:
                target = None
            if target == b2i16 or target == b2i32:
                kind = "u16" if target == b2i16 else "u32"
                last_read_kind = kind
                last_read_csv_off = state.get("r1")
            # call clobbers r0..r3
            for r in ("r0", "r1", "r2", "r3"):
                state[r] = None
            continue

        # ldrb rD, [r7, rOff] — direct csv byte read (r7 = csv buffer)
        if m == "ldrb" and "[r7," in op:
            # ldrb rD, [r7, rOff]  형태
            parts = op.split(",")
            if len(parts) >= 3:
                # parts[1] = "[r7", parts[2] = " rOff]"
                off_reg = parts[2].strip().rstrip("]")
                if off_reg in state and state[off_reg] is not None:
                    last_read_kind = "u8"
                    last_read_csv_off = state[off_reg]
                elif off_reg.startswith("#"):
                    try:
                        last_read_kind = "u8"
                        last_read_csv_off = int(off_reg[1:], 0)
                    except ValueError:
                        last_read_kind = None
                else:
                    last_read_kind = "u8"
                    last_read_csv_off = None
            continue

        # store: strh r0, [r?, #N] / str r0, [r?, #N] / strb rD, [r?, #N]
        # struct ptr 가 r3, fp, sb, r5 등 다양 — 패턴 무시하고 immediate offset 추출
        if m in ("strh", "str", "strb"):
            # 마지막 immediate offset 추출
            try:
                if "#" in op:
                    off_str = op.rsplit("#", 1)[-1].rstrip("]")
                    struct_off = int(off_str, 0)
                    val_kind = m  # strh/str/strb
                    if last_read_csv_off is not None:
                        rows.append((ins.address, last_read_csv_off, last_read_kind or "?", struct_off, val_kind))
                        last_read_kind = None
                        last_read_csv_off = None
            except ValueError:
                pass

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("code_va\tcsv_off\tread_kind\tstruct_off\tstore_kind\n")
        for va, csv_off, kind, sof, store in rows:
            csv_s = f"0x{csv_off:x}" if csv_off is not None else "?"
            f.write(f"0x{va:08x}\t{csv_s}\t{kind}\t0x{sof:x}\t{store}\n")
    print(f"[+] {OUT}  ({len(rows)} matches)")
    print()
    print(f"== EquipItem 영역 (0x{EQUIP_START:x}~0x{EQUIP_END:x}) csv→struct 매핑 ==")
    print(f"{'csv_off':>8s}  {'read':>4s}  {'struct_off':>10s}  {'store':>5s}")
    print("-" * 45)
    for va, csv_off, kind, sof, store in rows:
        csv_s = f"0x{csv_off:x}" if csv_off is not None else "?"
        print(f"  {csv_s:>8s}  {kind:>4s}  0x{sof:>8x}  {store:>5s}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
