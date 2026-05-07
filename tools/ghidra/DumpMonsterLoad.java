// Monster/EnemyG 로더 함수 dump (enemy_g.dat 121B record 의 field 매핑).
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

public class DumpMonsterLoad extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/monster_load.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        Set<Address> done = new LinkedHashSet<>();
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            String n = f.getName(true);
            if (n.startsWith("Monster::") || n.startsWith("BATTLER::") ||
                n.startsWith("ENEMY::") || n.contains("EnemyG_") ||
                n.contains("LoadEnemy") || n.contains("InitEnemy") ||
                n.contains("Init_ENEMY") || n.contains("InitMonster") ||
                n.contains("MapEnemyG") || n.contains("MapEnemy") ||
                (n.contains("Init_") && n.contains("ENEMY"))) {
                if (!done.add(f.getEntryPoint())) continue;
                DecompileResults r = ifc.decompileFunction(f, 90, monitor);
                pw.println();
                pw.println("// ===== " + n + " @ " + f.getEntryPoint() + " =====");
                if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
                else pw.println("// failed");
            }
        }
        pw.close();
        println("dumped " + done.size() + " functions");
    }
}
