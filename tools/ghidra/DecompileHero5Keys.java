// Hero5 전용: VFS / DES / JNI 핵심 함수만 디컴파일.
// 결과: d:/testrepo/hero5/analysis/key_funcs.c
// @category Hero5
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.regex.Pattern;

public class DecompileHero5Keys extends GhidraScript {
    private static final String OUT = "d:/testrepo/hero5/analysis/key_funcs.c";
    private static final Pattern PAT = Pattern.compile(
        "(MX_des|DES|KEY4|__DES_KEY__|loadAssetFromVFS|getAssetSizeFromVFS|loadMusicFromVFS|loadSoundFromVFS|nativeInitVFS|nativeInitKernel|JNI_OnLoad|LoadDecryptFile|SaveEncryptFile|LoadResDecrypt|setVFSInfo|MIDASKernelManager.*[Ii]nit|MIDASKernelManagerC[12]Ev|AndroidService.*loadAsset|StaticUtil)"
    );

    @Override
    protected void run() throws Exception {
        File outFile = new File(OUT);
        outFile.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(outFile));

        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        int total = 0, ok = 0, matched = 0;
        while (fit.hasNext()) {
            if (monitor.isCancelled()) break;
            Function f = fit.next();
            total++;
            String name = f.getName();
            if (!PAT.matcher(name).find()) continue;
            matched++;
            DecompileResults r = ifc.decompileFunction(f, 60, monitor);
            if (r != null && r.decompileCompleted()) {
                pw.println("// ===== " + name + " @ " + f.getEntryPoint() + " =====");
                pw.print(r.getDecompiledFunction().getC());
                pw.println();
                ok++;
            } else {
                pw.println("// ===== " + name + " @ " + f.getEntryPoint() + " (DECOMPILE FAILED) =====");
            }
        }
        pw.println();
        pw.println("// === DATA SYMBOLS ===");
        SymbolTable st = currentProgram.getSymbolTable();
        SymbolIterator sit = st.getAllSymbols(false);
        while (sit.hasNext()) {
            Symbol s = sit.next();
            String n = s.getName();
            if (n.equals("KEY4ENCRYPT") || n.equals("KEY4REAL") || n.equals("__DES_KEY__")) {
                pw.println("// " + n + " @ " + s.getAddress());
            }
        }
        pw.close();
        println("matched=" + matched + " decompiled=" + ok + "/" + total + " -> " + OUT);
    }
}
