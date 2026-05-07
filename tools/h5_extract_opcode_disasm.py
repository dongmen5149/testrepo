"""Hero5 EventProc::onFunction 의 switch 본문을 ARM disasm 으로 분석.

Ghidra 없이 capstone + lief 만으로:
  1. ELF symbol 에서 onFunction (mangled `_ZN9EventProc10onFunctionEi...`) 찾기
  2. ARM 모드 디스어셈블 (Hero5 EventProc 는 ARM, Thumb 아님)
  3. `cmp r1, #0x4c; addls pc, pc, r1, lsl #2` jumptable 패턴 인식
  4. jumptable 의 77 b/branch 명령에서 case_target[op] 추출
  5. case_target 에서 첫 BL Event_* 호출 → opcode → name 매핑
  6. mangle suffix 로 arg_size 자동 계산

산출:
  work/h5/analysis/opcode_table.tsv         (opcode, event_name, arg_size)
  apps/hero5-godot/assets/scenes/opcode_table.json  (Godot 자동 로드용)
"""
from __future__ import annotations
import json, pathlib, re, sys
import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT_TSV = ROOT / "work/h5/analysis/opcode_table.tsv"
OUT_JSON = ROOT / "apps/hero5-godot/assets/scenes/opcode_table.json"

TYPE_SIZE = {
    'v': 0, 'b': 1, 'c': 1, 'a': 1, 'h': 1,
    's': 2, 't': 2, 'i': 4, 'j': 4, 'l': 4, 'm': 4, 'f': 4,
    'x': 8, 'y': 8, 'd': 8,
}


def mangle_to_argsize(suffix: str) -> int | None:
    size = 0; i = 0
    while i < len(suffix):
        c = suffix[i]
        if c in ('P', 'R'):
            size += 4; i += 2; continue
        if c in ('K', 'V'):
            i += 1; continue
        if c not in TYPE_SIZE:
            return None
        size += TYPE_SIZE[c]; i += 1
    return size


def find_event_funcs(b: lief.ELF.Binary) -> dict[int, tuple[str, int]]:
    out: dict[int, tuple[str, int]] = {}
    for sym in list(b.dynamic_symbols) + list(b.symtab_symbols):
        nm = sym.name
        if 'Event_' not in nm: continue
        m = re.search(r'(Event_[A-Za-z_]+?)E([a-zA-Z]{0,16})$', nm)
        if not m: continue
        sz = mangle_to_argsize(m.group(2))
        if sz is None: continue
        addr = sym.value & ~1   # thumb LSB
        if addr == 0: continue
        if addr not in out:
            out[addr] = (m.group(1), sz)
    return out


def find_onfunction(b: lief.ELF.Binary) -> tuple[int, int]:
    candidates = []
    for sym in list(b.dynamic_symbols) + list(b.symtab_symbols):
        nm = sym.name
        if 'onFunction' in nm and 'EventProc' in nm:
            addr = sym.value & ~1
            if addr and sym.size >= 1024:
                candidates.append((addr, sym.size, nm))
    candidates.sort(key=lambda x: -x[1])
    return (candidates[0][0], candidates[0][1]) if candidates else (0, 0)


def main() -> int:
    if not SO.exists():
        print('ERROR: .so missing'); return 1
    b = lief.ELF.parse(str(SO))
    funcs = find_event_funcs(b)
    print(f'Event_* funcs: {len(funcs)}')

    addr, size = find_onfunction(b)
    if addr == 0:
        print('onFunction not found'); return 1
    print(f'onFunction: 0x{addr:08x} size={size}')

    code = bytes(b.get_content_from_virtual_address(addr, size))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True
    insns = list(md.disasm(code, addr))
    print(f'decoded {len(insns)} ARM insns')

    # 1) jumptable head 찾기: `cmp Rn, #0x4c` + `addls pc, pc, Rn, lsl #2`
    jt_start = None
    n_cases = None
    for i, ins in enumerate(insns):
        if ins.mnemonic == 'cmp' and '#' in ins.op_str:
            m = re.search(r'#(0x[0-9a-fA-F]+|\d+)', ins.op_str)
            if m:
                num = int(m.group(1), 0)
                # 다음 명령이 addls pc, pc, ... ?
                if i + 1 < len(insns) and insns[i + 1].mnemonic.startswith('addls') \
                        and 'pc, pc' in insns[i + 1].op_str:
                    # ARM PC = current_insn+8. addls pc,pc,r1,lsl#2 시점:
                    #   PC=addls+8, r1=0 → jump to addls+8 = (jt_start+1) 위치
                    #   따라서 case 0 = insns[i+3], case N = insns[i+3+N]
                    #   insns[i+2] 는 default (r1 > num) fall-through.
                    jt_start = i + 3
                    n_cases = num + 1
                    break
    if jt_start is None:
        print('jumptable pattern not found'); return 1
    print(f'jumptable: cases={n_cases} starts at {insns[jt_start].address:#x}')

    # 2) 다음 n_cases 개 명령은 'b <target>' (각 4B)
    case_targets: list[int] = []
    for i in range(jt_start, jt_start + n_cases):
        ins = insns[i]
        if ins.mnemonic != 'b':
            print(f'  unexpected {ins.mnemonic} at case {i - jt_start}: {ins}'); break
        op = ins.operands[0]
        if op.type != capstone.arm.ARM_OP_IMM:
            break
        case_targets.append(op.imm)
    print(f'case_targets: {len(case_targets)}/{n_cases}')

    # 3) 각 case target 에서 첫 BL Event_* 호출 추적
    # 빠른 검색을 위해 addr → insn 인덱스 매핑
    addr_to_idx = {ins.address: i for i, ins in enumerate(insns)}

    rows = []  # (op, ev_name, arg_size, target_addr)
    for op_idx, tgt in enumerate(case_targets):
        if tgt not in addr_to_idx:
            rows.append((op_idx, '?out_of_func', 0, tgt))
            continue
        # 최대 80 명령 안에서 첫 BL 찾기
        ev_name = '?nobranch'
        arg_size = 0
        for j in range(addr_to_idx[tgt], min(addr_to_idx[tgt] + 80, len(insns))):
            cur = insns[j]
            if cur.mnemonic in ('bl', 'blx'):
                opn = cur.operands[0]
                if opn.type == capstone.arm.ARM_OP_IMM:
                    bt = opn.imm & ~1
                    if bt in funcs:
                        ev_name, arg_size = funcs[bt]
                        break
            # 다음 case head 도달하면 stop
            if cur.mnemonic == 'b' and j > addr_to_idx[tgt]:
                opn = cur.operands[0]
                if opn.type == capstone.arm.ARM_OP_IMM and opn.imm in case_targets:
                    break
        rows.append((op_idx, ev_name, arg_size, tgt))

    # 통계
    matched = sum(1 for _, ev, _, _ in rows if ev.startswith('Event_'))
    print(f'matched: {matched}/{len(rows)}')

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        f.write('opcode\tevent_name\targ_size\ttarget_addr\n')
        for op, ev, sz, tgt in rows:
            f.write(f'{op}\t{ev}\t{sz}\t{tgt:#x}\n')
    print(f'wrote {OUT_TSV}')

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_json = {"opcodes": [{"op": op, "name": ev, "size": sz}
                            for op, ev, sz, _ in rows if ev.startswith('Event_')]}
    OUT_JSON.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT_JSON} ({len(out_json["opcodes"])} entries)')

    # BASE_TABLE 검증
    REF = {
        0x00: 'Event_EnemyAction', 0x01: 'Event_EnemyChange',
        0x05: 'Event_EnemyImo', 0x18: 'Event_MapTileChange',
        0x1d: 'Event_PlayerChange', 0x33: 'Event_QuestStatus',
        0x35: 'Event_SituateBallon', 0x39: 'Event_SituateDialogText',
        0x3b: 'Event_SituateNarration', 0x3e: 'Event_SituatePopup',
        0x43: 'Event_Scene_ChangeBgm',
    }
    print('\nBASE_TABLE 비교:')
    for op, expected in REF.items():
        if op < len(rows):
            got = rows[op][1]
            mark = '✓' if got == expected else '✗'
            print(f'  {mark} 0x{op:02x}: expected={expected} got={got}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
