// .scn 안의 Interpreter 바이트코드 OPCODE 들을 추출.
// @category Hero5
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;

public class DumpInterpreter extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File outF = new File("d:/testrepo/work/h5/analysis/interpreter.c");
        outF.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(outF));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        SymbolTable st = currentProgram.getSymbolTable();
        FunctionManager fm = currentProgram.getFunctionManager();

        Set<Address> done = new HashSet<>();
        for (String k : new String[]{"open", "step", "exec", "Process", "next",
                "Strings", "Interpreter", "Event_", "Map::LoadData", "Map::LoadImage",
                "LoadRes", "loadRes"}) {
            SymbolIterator sit = st.getSymbols(k);
            while (sit.hasNext()) {
                Symbol s = sit.next();
                Function f = fm.getFunctionAt(s.getAddress());
                if (f == null) continue;
                String full = f.getName(true);
                if (!(full.contains("Interpreter") || full.contains("Event_") ||
                      full.contains("Map::Load") || full.equals("StaticUtil::LoadRes"))) continue;
                if (!done.add(f.getEntryPoint())) continue;
                DecompileResults r = ifc.decompileFunction(f, 90, monitor);
                pw.println();
                pw.println("// ===== " + full + " @ " + f.getEntryPoint() + " =====");
                if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
                else pw.println("// failed");
                if (monitor.isCancelled()) break;
            }
        }
        pw.close();
        println("dumped " + done.size() + " functions");
    }
}
