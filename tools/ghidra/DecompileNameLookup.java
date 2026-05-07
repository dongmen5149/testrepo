// Hero5 P1: AndroidService::getUniqueAssetNameFromID + getUniqueNumberFromStrings
// + getAssetSizeFromVFS 본문 + 이들이 참조하는 모든 데이터 심볼/문자열 dump.
//
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
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;
import ghidra.program.model.mem.Memory;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileNameLookup extends GhidraScript {

    private static final String OUT = "d:/testrepo/work/h5/analysis/name_lookup.c";

    private static final String[] TARGETS = {
        "getUniqueAssetNameFromID",
        "getUniqueNumberFromStrings",
        "getAssetSizeFromVFS",
        "getAssetSize",
        "hash",
    };

    @Override
    protected void run() throws Exception {
        new File(OUT).getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(OUT));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        SymbolTable st = currentProgram.getSymbolTable();
        FunctionManager fm = currentProgram.getFunctionManager();
        Memory mem = currentProgram.getMemory();

        for (String target : TARGETS) {
            SymbolIterator sit = st.getSymbols(target);
            while (sit.hasNext()) {
                Symbol sym = sit.next();
                Function f = fm.getFunctionAt(sym.getAddress());
                if (f == null) continue;
                pw.println();
                pw.println("// =================================================");
                pw.println("// " + f.getName(true) + " @ " + f.getEntryPoint());
                pw.println("//   parent=" + sym.getParentNamespace().getName());
                pw.println("// =================================================");
                DecompileResults r = ifc.decompileFunction(f, 90, monitor);
                if (r != null && r.decompileCompleted()) {
                    pw.print(r.getDecompiledFunction().getC());
                } else {
                    pw.println("// DECOMPILE FAILED");
                }

                // Dump every data ref made from inside this function
                pw.println();
                pw.println("// --- data references made by this function ---");
                Address start = f.getEntryPoint();
                Address end = f.getBody().getMaxAddress();
                InstructionIterator iit = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (iit.hasNext()) {
                    Instruction insn = iit.next();
                    Reference[] refs = insn.getReferencesFrom();
                    for (Reference ref : refs) {
                        if (ref.getReferenceType().isData()) {
                            Address ta = ref.getToAddress();
                            String label = "";
                            Symbol s = currentProgram.getSymbolTable().getPrimarySymbol(ta);
                            if (s != null) label = s.getName();
                            String preview = previewBytes(mem, ta, 64);
                            pw.println("//   " + insn.getAddress() + " -> " + ta
                                    + "  [" + label + "]  " + preview);
                        }
                    }
                }
            }
        }
        pw.close();
        println("wrote " + OUT);
    }

    private String previewBytes(Memory mem, Address a, int n) {
        StringBuilder hex = new StringBuilder();
        StringBuilder asc = new StringBuilder();
        for (int i = 0; i < n; i++) {
            try {
                byte b = mem.getByte(a.add(i));
                hex.append(String.format("%02x ", b & 0xff));
                int u = b & 0xff;
                asc.append((u >= 0x20 && u <= 0x7e) ? (char) u : '.');
            } catch (Exception e) { break; }
        }
        return hex.toString().trim() + "  |" + asc.toString() + "|";
    }
}
