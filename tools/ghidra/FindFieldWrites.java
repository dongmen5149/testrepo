// Map class 의 this+0x94 (collision base ptr) 에 쓰기를 하는 함수 찾기.
// ARM 에서 STR Rx, [this, #0x94] 패턴 (또는 부근) 검색.
// @category Hero5
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import java.io.*;
import java.util.*;

public class FindFieldWrites extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/field_writes_94.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();

        Set<Address> hits = new LinkedHashSet<>();
        // Walk all instructions in Map::* functions, look for STR with offset 0x94
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            String n = f.getName(true);
            if (!n.startsWith("Map::") && !n.contains("::Map::")) continue;
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction insn = it.next();
                String mn = insn.getMnemonicString();
                if (!mn.startsWith("str") && !mn.startsWith("STR")) continue;
                String repr = insn.toString();
                // ARM offset display can be "#0x94" or "0x94" or with stack reg
                if (repr.contains("0x94") || repr.contains("#0x94")
                        || repr.contains("#148")) {
                    hits.add(f.getEntryPoint());
                    break;
                }
            }
        }

        pw.println("// Map::* functions that contain STR ..., #0x94 instruction:");
        pw.println("// (potential writers of collision base ptr field)");
        for (Address fa : hits) {
            Function f = fm.getFunctionAt(fa);
            if (f == null) continue;
            pw.println("//   " + f.getName(true) + " @ " + fa);
        }
        pw.println();
        pw.println("// === decompile of each candidate ===");
        for (Address fa : hits) {
            if (monitor.isCancelled()) break;
            Function f = fm.getFunctionAt(fa);
            DecompileResults r = ifc.decompileFunction(f, 90, monitor);
            pw.println();
            pw.println("// ===== " + f.getName(true) + " @ " + fa + " =====");
            if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
            else pw.println("// failed");
        }
        pw.close();
        println("found " + hits.size() + " functions");
    }
}
