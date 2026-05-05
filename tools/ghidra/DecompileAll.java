// 모든 함수를 디컴파일해 단일 파일에 dump.
// 결과: d:/testrepo/work/ghidra_out/all_decompiled.c
// 그 후 grep "frameBuf" 등으로 진짜 사용처를 찾는다.
//
// @category Hero3
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileAll extends GhidraScript {

    private static final String OUT = "c:/gameRemake/testrepo/work/ghidra_out/all_decompiled.c";

    @Override
    protected void run() throws Exception {
        File outFile = new File(OUT);
        outFile.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(outFile));

        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        int total = 0, ok = 0;
        long lastReport = System.currentTimeMillis();
        while (fit.hasNext()) {
            if (monitor.isCancelled()) break;
            Function f = fit.next();
            total++;
            DecompileResults r = ifc.decompileFunction(f, 30, monitor);
            if (r != null && r.decompileCompleted()) {
                pw.println("// ===== " + f.getName() + " @ " + f.getEntryPoint() + " =====");
                pw.print(r.getDecompiledFunction().getC());
                pw.println();
                ok++;
            }
            if (System.currentTimeMillis() - lastReport > 5000) {
                println("decompiled " + ok + "/" + total + " ...");
                lastReport = System.currentTimeMillis();
                pw.flush();
            }
        }
        pw.close();
        println("done: " + ok + "/" + total + " functions written to " + OUT);
    }
}
