// HERO::*, CHAR::* 함수 (캐릭터 시스템) dump.
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

public class DumpHeroChar extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/hero_char.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        Set<Address> done = new LinkedHashSet<>();
        // priority: HERO, CHAR, OBJECT classes + collision/movement
        String[] prefixes = {"HERO::", "CHAR::", "OBJECT::Set", "OBJECT::Move",
                "Map::Collision", "Map::MoveTile", "Map::CheckMove",
                "MapItem::", "PlayerInit"};
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            String n = f.getName(true);
            boolean match = false;
            for (String pre : prefixes) {
                if (n.startsWith(pre)) { match = true; break; }
            }
            if (!match) continue;
            if (!done.add(f.getEntryPoint())) continue;
            DecompileResults r = ifc.decompileFunction(f, 90, monitor);
            pw.println();
            pw.println("// ===== " + n + " @ " + f.getEntryPoint() + " =====");
            if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
            else pw.println("// failed");
        }
        pw.close();
        println("dumped " + done.size() + " functions");
    }
}
