# Ghidra headless post-script (Jython)
# §4.1~4.4 진입점 4종을 자동 식별:
#   §4.1 비트맵 디코더 — "frameBuf is NULL" xref 함수
#   §4.2 NPC/exit 자동 배치 — "Event_freeID" / "loadDataID" 함수
#   §4.3 캐릭터 애니메이션 — "Hero_Free" / "freeBossType" 함수
#   §4.4 이벤트 스크립트 명령 — "onEventMessageOkKey" / "eventManager" 함수
#
# 결과: d:/testrepo/work/ghidra_out/entry_points.json + decompiled .c 파일들
#
# 호출: analyzeHeadless ... -postScript find_entry_points.py
#
# @category Hero3

import json
import os

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

OUT_DIR = "d:/testrepo/work/ghidra_out"
TARGETS = [
    ("4.1_bitmap_decoder", ["frameBuf is NULL"]),
    ("4.2_mp_extras",      ["Event_freeID", "loadDataID"]),
    ("4.3_cif_animation",  ["Hero_Free", "freeBossType"]),
    ("4.4_scn_opcodes",    ["onEventMessageOkKey", "eventManager"]),
]

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p)

def find_string_addr(needle):
    """프로그램 메모리에서 문자열 needle 첫 등장 주소 반환."""
    listing = currentProgram.getListing()
    mem = currentProgram.getMemory()
    addr_set = mem.getLoadedAndInitializedAddressSet()
    matches = []
    # Ghidra 의 string finder
    from ghidra.program.util import DefinedDataIterator
    for data in DefinedDataIterator.definedStrings(currentProgram):
        s = str(data.getValue() or "")
        if needle in s:
            matches.append((data.getAddress(), s))
    if matches:
        return matches
    # 미정의 문자열도 찾기 — bytes 검색
    needle_b = bytes(needle.encode("ascii"))
    found = mem.findBytes(addr_set.getMinAddress(), needle_b, None, True, ConsoleTaskMonitor())
    if found:
        return [(found, needle)]
    return []

def xrefs_to(addr):
    refs = []
    rm = currentProgram.getReferenceManager()
    it = rm.getReferencesTo(addr)
    while it.hasNext():
        r = it.next()
        refs.append(r.getFromAddress())
    return refs

def func_containing(addr):
    fm = currentProgram.getFunctionManager()
    return fm.getFunctionContaining(addr)

def find_function_by_name(name):
    fm = currentProgram.getFunctionManager()
    for f in fm.getFunctions(True):
        if f.getName() == name:
            return f
    return None

def decompile(func, ifc):
    monitor = ConsoleTaskMonitor()
    res = ifc.decompileFunction(func, 60, monitor)
    if res and res.decompileCompleted():
        return res.getDecompiledFunction().getC()
    return None

def main():
    ensure_dir(OUT_DIR)
    ifc = DecompInterface()
    ifc.openProgram(currentProgram)

    summary = {}

    for tag, needles in TARGETS:
        tag_dir = os.path.join(OUT_DIR, tag)
        ensure_dir(tag_dir)
        tag_info = {"needles": needles, "matches": []}

        for needle in needles:
            print("[%s] searching string '%s' ..." % (tag, needle))
            matches = find_string_addr(needle)
            for (saddr, full) in matches:
                refs = xrefs_to(saddr)
                # 직접 xref가 없으면, 동일 주소를 const로 참조하는 PIC 시퀀스가 있을 수 있음
                # — Ghidra 가 데이터 참조 분석을 해놨다면 보통 잡힘.
                ref_funcs = []
                for ra in refs:
                    f = func_containing(ra)
                    if f is None:
                        continue
                    fname = f.getName()
                    fentry = "%s" % f.getEntryPoint()
                    ref_funcs.append({
                        "ref_addr": "%s" % ra,
                        "func_name": fname,
                        "func_entry": fentry,
                    })
                    # 디컴파일 해서 저장
                    out_c = os.path.join(tag_dir, "%s_%s.c" % (fname, fentry))
                    if not os.path.exists(out_c):
                        c = decompile(f, ifc)
                        if c:
                            with open(out_c, "w") as fh:
                                fh.write("// xref from %s ('%s')\n" % (saddr, full[:80].replace("\n"," ")))
                                fh.write("// function: %s @ %s\n\n" % (fname, fentry))
                                fh.write(c)
                tag_info["matches"].append({
                    "needle": needle,
                    "string_addr": "%s" % saddr,
                    "string_full": full[:200],
                    "xref_count": len(refs),
                    "xref_funcs": ref_funcs,
                })

            # 함수 이름 자체로 찾기 (이미 심볼화 된 함수)
            f = find_function_by_name(needle)
            if f:
                fentry = "%s" % f.getEntryPoint()
                out_c = os.path.join(tag_dir, "byname_%s_%s.c" % (needle, fentry))
                if not os.path.exists(out_c):
                    c = decompile(f, ifc)
                    if c:
                        with open(out_c, "w") as fh:
                            fh.write("// function found by name: %s @ %s\n\n" % (needle, fentry))
                            fh.write(c)
                tag_info["matches"].append({
                    "needle": needle,
                    "by_name": True,
                    "func_entry": fentry,
                })

        summary[tag] = tag_info

    summary_path = os.path.join(OUT_DIR, "entry_points.json")
    with open(summary_path, "w") as fh:
        json.dump(summary, fh, indent=2)
    print("\nWrote summary: %s" % summary_path)

main()
