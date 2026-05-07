// Hero5 P1: loadAssetFromVFS caller + .rodata string-pointer array 탐색.
//
// 목표:
//   1) loadAssetFromVFS / getAssetSizeFromVFS / loadMusicFromVFS / loadSoundFromVFS
//      함수의 모든 caller 디컴파일 → 인자 추적 (이름이 어디서 오는지)
//   2) .rodata / .data.rel.ro 등에서 "연속된 string pointer 배열" 패턴 탐지:
//      - 4바이트 정렬된 포인터들이
//      - 모두 ASCII 문자열 (길이 3~80, 인쇄 가능) 영역을 가리킴
//      - 16개 이상 연속
//      → 자산 이름 테이블 후보
//
// 산출:
//   work/h5/analysis/asset_callers.c     — caller 디컴파일
//   work/h5/analysis/string_arrays.tsv   — 후보 배열 (addr, count, sample 5개)
//
// @category Hero5
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolTable;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

public class FindAssetNameTable extends GhidraScript {

    private static final String OUT_CALLERS = "d:/testrepo/work/h5/analysis/asset_callers.c";
    private static final String OUT_ARRAYS  = "d:/testrepo/work/h5/analysis/string_arrays.tsv";

    private static final String[] TARGETS = {
        "loadAssetFromVFS", "getAssetSizeFromVFS",
        "loadMusicFromVFS", "loadSoundFromVFS",
        "loadAsset", "getAssetSize"
    };

    @Override
    protected void run() throws Exception {
        new File(OUT_CALLERS).getParentFile().mkdirs();
        dumpCallers();
        scanStringArrays();
    }

    private void dumpCallers() throws Exception {
        PrintWriter pw = new PrintWriter(new FileWriter(OUT_CALLERS));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        SymbolTable st = currentProgram.getSymbolTable();

        Set<Address> visited = new HashSet<>();
        int totalCallers = 0;

        for (String target : TARGETS) {
            SymbolIterator sit = st.getSymbols(target);
            while (sit.hasNext()) {
                Symbol sym = sit.next();
                Function tgt = fm.getFunctionAt(sym.getAddress());
                if (tgt == null) continue;
                pw.println("// ============================================");
                pw.println("// TARGET: " + tgt.getName() + " @ " + tgt.getEntryPoint());
                pw.println("// ============================================");

                ReferenceIterator rit = currentProgram.getReferenceManager()
                        .getReferencesTo(tgt.getEntryPoint());
                Set<Address> callers = new LinkedHashSet<>();
                while (rit.hasNext()) {
                    Reference r = rit.next();
                    Function caller = fm.getFunctionContaining(r.getFromAddress());
                    if (caller != null) callers.add(caller.getEntryPoint());
                }
                pw.println("// callers: " + callers.size());
                for (Address ca : callers) {
                    if (visited.contains(ca)) continue;
                    visited.add(ca);
                    Function cf = fm.getFunctionAt(ca);
                    if (cf == null) continue;
                    DecompileResults dr = ifc.decompileFunction(cf, 60, monitor);
                    if (dr != null && dr.decompileCompleted()) {
                        pw.println();
                        pw.println("// ----- caller: " + cf.getName() + " @ " + ca + " -----");
                        pw.print(dr.getDecompiledFunction().getC());
                        totalCallers++;
                    }
                    if (monitor.isCancelled()) break;
                }
                pw.println();
            }
        }
        pw.close();
        println("dumped " + totalCallers + " unique callers -> " + OUT_CALLERS);
    }

    private void scanStringArrays() throws Exception {
        PrintWriter pw = new PrintWriter(new FileWriter(OUT_ARRAYS));
        pw.println("array_addr\tcount\tfirst_string\tsample2\tsample3\tsample4\tsample5");

        Memory mem = currentProgram.getMemory();
        int found = 0;
        int minRun = 16;     // 최소 16개 연속 포인터
        int minStrLen = 3;
        int maxStrLen = 80;

        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String name = blk.getName().toLowerCase();
            // .rodata / .data.rel.ro / .data 모두 후보
            if (!(name.contains("rodata") || name.contains("data") || name.contains("text"))) continue;

            Address start = blk.getStart();
            Address end = blk.getEnd();
            long size = end.subtract(start);
            if (size < minRun * 4L) continue;
            println("scanning " + blk.getName() + " @ " + start + " size=0x" + Long.toHexString(size));

            Address cur = start;
            while (cur.compareTo(end) < 0 && !monitor.isCancelled()) {
                List<String> strs = new ArrayList<>();
                Address runStart = cur;
                while (cur.compareTo(end) < 0) {
                    long ptr;
                    try {
                        ptr = mem.getInt(cur) & 0xFFFFFFFFL;
                    } catch (Exception e) { break; }
                    if (ptr == 0) break;
                    Address pa;
                    try { pa = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(ptr); }
                    catch (Exception e) { break; }
                    String s = readAsciiAt(mem, pa, minStrLen, maxStrLen);
                    if (s == null) break;
                    strs.add(s);
                    cur = cur.add(4);
                }
                if (strs.size() >= minRun) {
                    found++;
                    StringBuilder row = new StringBuilder();
                    row.append(runStart).append('\t').append(strs.size());
                    for (int i = 0; i < 5; i++) {
                        row.append('\t');
                        if (i < strs.size()) row.append(escapeTab(strs.get(i)));
                    }
                    pw.println(row);
                    println("  ARRAY @ " + runStart + "  count=" + strs.size()
                            + "  first=" + strs.get(0));
                } else {
                    cur = cur.add(4);
                }
            }
        }
        pw.close();
        println("found " + found + " candidate string-pointer arrays -> " + OUT_ARRAYS);
    }

    private String readAsciiAt(Memory mem, Address a, int minLen, int maxLen) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < maxLen + 1; i++) {
            byte b;
            try { b = mem.getByte(a.add(i)); } catch (Exception e) { return null; }
            if (b == 0) {
                if (sb.length() >= minLen) return sb.toString();
                return null;
            }
            int u = b & 0xff;
            if (u < 0x20 || u > 0x7e) return null;
            sb.append((char) u);
        }
        return null;
    }

    private String escapeTab(String s) {
        return s.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ');
    }
}
