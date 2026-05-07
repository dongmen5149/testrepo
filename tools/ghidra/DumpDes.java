// MX_desInit + caller + LoadDecryptFile/LoadResDecrypt 디컴파일.
// __DES_KEY__ 가 어디서 어떤 string 으로 set 되는지 추적.
// @category Hero5
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;
import java.io.*;
import java.util.*;

public class DumpDes extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/des_key.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        SymbolTable st = currentProgram.getSymbolTable();

        // 1. dump MX_des*
        Set<Address> dumped = new LinkedHashSet<>();
        for (String n : new String[]{"MX_desInit", "MX_desEncrypt", "MX_desDecrypt",
                "MX_desEncryptPKCS7", "MX_desDecryptPKCS7",
                "LoadDecryptFile", "SaveEncryptFile", "LoadResDecrypt"}) {
            SymbolIterator sit = st.getSymbols(n);
            while (sit.hasNext()) {
                Symbol s = sit.next();
                Function f = fm.getFunctionAt(s.getAddress());
                if (f == null || !dumped.add(f.getEntryPoint())) continue;
                DecompileResults r = ifc.decompileFunction(f, 90, monitor);
                pw.println();
                pw.println("// ===== " + f.getName(true) + " @ " + f.getEntryPoint() + " =====");
                if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
                else pw.println("// failed");
            }
        }

        // 2. find callers of MX_desInit
        SymbolIterator sit = st.getSymbols("MX_desInit");
        Set<Address> callerAddrs = new LinkedHashSet<>();
        while (sit.hasNext()) {
            Symbol s = sit.next();
            ReferenceIterator rit = currentProgram.getReferenceManager()
                    .getReferencesTo(s.getAddress());
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function caller = fm.getFunctionContaining(r.getFromAddress());
                if (caller != null) callerAddrs.add(caller.getEntryPoint());
            }
        }
        pw.println();
        pw.println("// === callers of MX_desInit ===");
        for (Address ca : callerAddrs) {
            if (dumped.contains(ca)) continue;
            Function f = fm.getFunctionAt(ca);
            if (f == null) continue;
            DecompileResults r = ifc.decompileFunction(f, 90, monitor);
            pw.println();
            pw.println("// ===== " + f.getName(true) + " @ " + ca + " =====");
            if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
            else pw.println("// failed");
        }

        // 3. dump KEY4* symbols + their initialization site
        pw.println();
        pw.println("// === DES key symbols ===");
        for (String n : new String[]{"KEY4ENCRYPT", "KEY4REAL", "__DES_KEY__"}) {
            SymbolIterator sit2 = st.getSymbols(n);
            while (sit2.hasNext()) {
                Symbol s = sit2.next();
                pw.println("//   " + n + " @ " + s.getAddress());
                // dump 16 bytes there
                StringBuilder hex = new StringBuilder();
                for (int i = 0; i < 16; i++) {
                    try {
                        hex.append(String.format("%02x ",
                                currentProgram.getMemory().getByte(s.getAddress().add(i)) & 0xff));
                    } catch (Exception e) { break; }
                }
                pw.println("//     bytes: " + hex);
            }
        }

        pw.close();
        println("dumped DES analysis -> " + out);
    }
}
