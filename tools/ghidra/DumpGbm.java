// .gbm 로더 + GbmImage 클래스 dump.
// @category Hero5
// @runtime Java
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import java.io.*;
import java.util.*;

public class DumpGbm extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/gbm_loader.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        Set<Address> done = new LinkedHashSet<>();
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            String n = f.getName(true);
            if (n.startsWith("GbmImage::") || n.contains("::loadGbm")
                    || n.contains("::LoadData") || n.contains("::LoadImage")
                    || n.equals("Map::LoadData") || n.equals("Map::LoadImage")
                    || n.contains("MapTile") || n.contains("loadTile")
                    || (n.startsWith("Map::") && (n.contains("Load") || n.contains("Tile")
                            || n.contains("Fgi") || n.contains("Obj") || n.contains("Face")))) {
                if (done.add(f.getEntryPoint())) {
                    DecompileResults r = ifc.decompileFunction(f, 90, monitor);
                    pw.println();
                    pw.println("// ===== " + n + " @ " + f.getEntryPoint() + " =====");
                    if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
                    else pw.println("// failed");
                }
            }
        }
        pw.close();
        println("dumped " + done.size() + " functions");
    }
}
