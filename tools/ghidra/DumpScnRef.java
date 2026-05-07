// `/c/map/%05d.scn` 참조 함수만 깊게 추적.
//
// @category Hero5
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

public class DumpScnRef extends GhidraScript {
    private static final String OUT = "d:/testrepo/work/h5/analysis/scn_loader.c";

    @Override
    protected void run() throws Exception {
        new File(OUT).getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(OUT));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        Memory mem = currentProgram.getMemory();
        FunctionManager fm = currentProgram.getFunctionManager();

        // Find string addresses for the two scn format strings
        List<Address> targets = new ArrayList<>();
        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String n = blk.getName().toLowerCase();
            if (!(n.contains("rodata") || n.contains("data"))) continue;
            int len = (int) Math.min(blk.getEnd().subtract(blk.getStart()), 0x100000);
            byte[] buf = new byte[len];
            mem.getBytes(blk.getStart(), buf);
            int i = 0;
            while (i < buf.length) {
                int j = i;
                while (j < buf.length && buf[j] >= 0x20 && buf[j] <= 0x7e) j++;
                if (j - i >= 3) {
                    String s = new String(buf, i, j - i);
                    if (s.contains(".scn") || s.contains(".gbm")) {
                        Address sa = blk.getStart().add(i);
                        targets.add(sa);
                        pw.println("// string @ " + sa + ": '" + s + "'");
                    }
                }
                i = (j == i) ? i + 1 : j + 1;
            }
        }
        pw.println();

        // Find functions referencing each
        Set<Address> funcs = new LinkedHashSet<>();
        Map<Address, List<String>> funcRefs = new LinkedHashMap<>();
        for (Address sa : targets) {
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(sa);
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function f = fm.getFunctionContaining(r.getFromAddress());
                if (f != null) {
                    funcs.add(f.getEntryPoint());
                    funcRefs.computeIfAbsent(f.getEntryPoint(), k -> new ArrayList<>())
                            .add(sa.toString());
                }
            }
        }
        pw.println("// functions referencing scn/gbm strings: " + funcs.size());

        for (Address fa : funcs) {
            if (monitor.isCancelled()) break;
            Function f = fm.getFunctionAt(fa);
            if (f == null) continue;
            DecompileResults r = ifc.decompileFunction(f, 90, monitor);
            pw.println();
            pw.println("// ===== " + f.getName(true) + " @ " + fa
                    + "  (refs: " + funcRefs.get(fa) + ") =====");
            if (r != null && r.decompileCompleted()) {
                pw.print(r.getDecompiledFunction().getC());
            } else {
                pw.println("// decompile failed");
            }
        }
        pw.close();
        println("dumped " + funcs.size() + " functions -> " + OUT);
    }
}
