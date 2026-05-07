// Hero5 P3-prep: c/map/%05d.scn 로더 함수 추적.
// 전략:
//   1) 문자열 풀에서 "%05d.scn" / "scn" / "scene" / "Scene" 포함 문자열 찾고
//      이를 참조하는 함수들 디컴파일
//   2) loadAssetFromVFS / MC_knlGetResource 의 caller 중 scene 관련 함수 추가 dump
//
// 산출:
//   work/h5/analysis/scene_loader.c

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressIterator;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

public class FindSceneLoader extends GhidraScript {
    private static final String OUT = "d:/testrepo/work/h5/analysis/scene_loader.c";

    private static final String[] KEYWORDS = {
        "%05d.scn", ".scn", "scn", "scene", "Scene",
        "loadScene", "Scene_", "scn_", "loadMap", "Map_",
        "knlScene", "knlMap", "MapMgr", "loadStage",
    };

    private static final String[] FUNC_NAMES = {
        "loadScene", "loadMap", "loadStage", "MC_knlLoadScene",
        "MC_knlLoadMap", "Scene", "Map", "knlMap", "MapManager",
    };

    @Override
    protected void run() throws Exception {
        new File(OUT).getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(OUT));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();
        SymbolTable st = currentProgram.getSymbolTable();

        // 1. Find string literals containing keywords
        pw.println("// === STEP 1: keyword string literals ===");
        Set<Address> stringAddrs = new HashSet<>();
        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String name = blk.getName().toLowerCase();
            if (!(name.contains("rodata") || name.contains("data"))) continue;
            Address start = blk.getStart();
            Address end = blk.getEnd();
            int len = (int) Math.min(end.subtract(start), 0x100000);
            byte[] buf = new byte[len];
            mem.getBytes(start, buf);

            int i = 0;
            while (i < buf.length) {
                int j = i;
                while (j < buf.length && buf[j] >= 0x20 && buf[j] <= 0x7e) j++;
                if (j - i >= 3) {
                    String s = new String(buf, i, j - i);
                    for (String kw : KEYWORDS) {
                        if (s.contains(kw)) {
                            Address sa = start.add(i);
                            stringAddrs.add(sa);
                            pw.println("//   " + sa + "  '" + s.replace('\n','.').replace('\r','.') + "'");
                            break;
                        }
                    }
                }
                i = (j == i) ? i + 1 : j + 1;
            }
        }
        pw.println("// total candidate strings: " + stringAddrs.size());
        pw.println();

        // 2. For each candidate string, find functions that reference it; decompile them
        Set<Address> funcsToDump = new LinkedHashSet<>();
        for (Address sa : stringAddrs) {
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(sa);
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f != null) funcsToDump.add(f.getEntryPoint());
            }
        }
        pw.println("// === STEP 2: functions referencing those strings: " + funcsToDump.size() + " ===");

        // 3. Also pick functions whose name contains scene/map keywords
        for (String kw : FUNC_NAMES) {
            SymbolIterator sit = st.getSymbols(kw);
            while (sit.hasNext()) {
                Symbol s = sit.next();
                Function f = fm.getFunctionAt(s.getAddress());
                if (f != null) funcsToDump.add(f.getEntryPoint());
            }
        }
        // Also iterate all functions and match by partial name
        for (Function f : fm.getFunctions(true)) {
            String n = f.getName().toLowerCase();
            if (n.contains("scene") || n.contains("map") || n.contains("stage")
                || n.contains("scn")) {
                if (!n.startsWith("_") && !n.startsWith("std::")) {
                    funcsToDump.add(f.getEntryPoint());
                }
            }
            if (monitor.isCancelled()) break;
        }
        pw.println("// total functions to dump: " + funcsToDump.size());
        pw.println();

        // 4. Decompile each
        int ok = 0;
        for (Address fa : funcsToDump) {
            if (monitor.isCancelled()) break;
            Function f = fm.getFunctionAt(fa);
            if (f == null) continue;
            DecompileResults r = ifc.decompileFunction(f, 60, monitor);
            pw.println();
            pw.println("// ===== " + f.getName(true) + " @ " + fa + " =====");
            if (r != null && r.decompileCompleted()) {
                pw.print(r.getDecompiledFunction().getC());
                ok++;
            } else {
                pw.println("// (decompile failed)");
            }
        }
        pw.close();
        println("dumped " + ok + " / " + funcsToDump.size() + " scene-related functions -> " + OUT);
    }
}
