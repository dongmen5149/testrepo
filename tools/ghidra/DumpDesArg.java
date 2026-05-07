// MX_desInit(arg) 의 arg pointer resolve.
// onStartApp 의 instruction stream 에서 MX_desInit 호출 직전 R0 (arg)
// 에 load 되는 데이터 주소 추적.
// @category Hero5
// @runtime Java
import ghidra.app.script.GhidraScript;
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
import java.io.*;

public class DumpDesArg extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/des_arg.txt");
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        SymbolTable st = currentProgram.getSymbolTable();
        FunctionManager fm = currentProgram.getFunctionManager();
        Memory mem = currentProgram.getMemory();

        // dump KEY4ENCRYPT 32 bytes for context
        for (String n : new String[]{"KEY4ENCRYPT", "KEY4REAL", "__DES_KEY__"}) {
            SymbolIterator sit = st.getSymbols(n);
            while (sit.hasNext()) {
                Symbol s = sit.next();
                pw.println("// " + n + " @ " + s.getAddress());
                StringBuilder hex = new StringBuilder("// bytes: ");
                StringBuilder asc = new StringBuilder("// ascii: ");
                for (int i = 0; i < 32; i++) {
                    try {
                        int b = mem.getByte(s.getAddress().add(i)) & 0xff;
                        hex.append(String.format("%02x ", b));
                        asc.append((b >= 0x20 && b <= 0x7e) ? (char) b : '.');
                    } catch (Exception e) { break; }
                }
                pw.println(hex);
                pw.println(asc);
            }
        }

        // find MX_desInit symbol address
        Address mxAddr = null;
        SymbolIterator sit = st.getSymbols("MX_desInit");
        if (sit.hasNext()) mxAddr = sit.next().getAddress();
        if (mxAddr == null) { pw.println("// MX_desInit not found"); pw.close(); return; }
        pw.println("\n// MX_desInit @ " + mxAddr);

        // walk callers and trace arg
        for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(mxAddr)) {
            if (!ref.getReferenceType().isCall()) continue;
            Address callSite = ref.getFromAddress();
            Function caller = fm.getFunctionContaining(callSite);
            if (caller == null) continue;
            pw.println("\n// caller: " + caller.getName(true) + " @ " + caller.getEntryPoint()
                    + ", call site " + callSite);
            // walk back up to 10 instructions, look for LDR that loads R0 from data
            Address cur = callSite;
            for (int i = 0; i < 12; i++) {
                Instruction insn;
                try { insn = currentProgram.getListing().getInstructionBefore(cur); }
                catch (Exception e) { break; }
                if (insn == null) break;
                pw.println("//   " + insn.getAddress() + ": " + insn);
                // collect any data refs from this insn
                Reference[] refs = insn.getReferencesFrom();
                for (Reference r : refs) {
                    if (r.getReferenceType().isData()) {
                        Address ta = r.getToAddress();
                        // dump bytes there
                        StringBuilder hex = new StringBuilder();
                        StringBuilder asc = new StringBuilder();
                        for (int k = 0; k < 32; k++) {
                            try {
                                int b = mem.getByte(ta.add(k)) & 0xff;
                                hex.append(String.format("%02x ", b));
                                asc.append((b >= 0x20 && b <= 0x7e) ? (char) b : '.');
                            } catch (Exception e) { break; }
                        }
                        pw.println("//     -> " + ta + "  hex: " + hex);
                        pw.println("//        ascii: " + asc);
                    }
                }
                cur = insn.getAddress();
            }
        }

        pw.close();
        println("dumped DES arg -> " + out);
    }
}
