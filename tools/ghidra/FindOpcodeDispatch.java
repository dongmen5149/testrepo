// Interpreter::doScript 의 vtable[0x14] / vtable[0x18] 호출이 dispatch 하는
// EventProc 의 opcode 처리 함수를 찾는다. 큰 switch/case 가 있는 함수가 후보.
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

public class FindOpcodeDispatch extends GhidraScript {
    @Override
    protected void run() throws Exception {
        File out = new File("d:/testrepo/work/h5/analysis/opcode_dispatch.c");
        out.getParentFile().mkdirs();
        PrintWriter pw = new PrintWriter(new FileWriter(out));
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();

        // Heuristic: find functions that contain many "Event_*" call sites.
        // We'll rank functions by # of Event_ child calls.
        Map<Address, Integer> scoreByFunc = new HashMap<>();
        Map<Address, List<String>> calls = new HashMap<>();
        for (Function f : fm.getFunctions(true)) {
            if (monitor.isCancelled()) break;
            int score = 0;
            List<String> events = new ArrayList<>();
            for (Function called : f.getCalledFunctions(monitor)) {
                String n = called.getName();
                if (n.startsWith("Event_") || n.contains("::Event_")
                        || n.contains("Event_") || n.contains("Talk")
                        || n.contains("Warp") || n.contains("Camera")) {
                    score++;
                    events.add(n);
                }
            }
            if (score >= 5) {
                scoreByFunc.put(f.getEntryPoint(), score);
                calls.put(f.getEntryPoint(), events);
            }
        }

        List<Map.Entry<Address, Integer>> sorted = new ArrayList<>(scoreByFunc.entrySet());
        sorted.sort((a, b) -> b.getValue() - a.getValue());

        pw.println("// === top 20 functions by # of Event_* callees ===");
        for (int i = 0; i < Math.min(20, sorted.size()); i++) {
            Address fa = sorted.get(i).getKey();
            Function f = fm.getFunctionAt(fa);
            pw.println("//   score=" + sorted.get(i).getValue() + "  "
                    + f.getName(true) + " @ " + fa);
            for (String c : calls.get(fa)) pw.println("//      " + c);
        }
        pw.println();

        // Decompile top 5
        pw.println("// === decompile of top 5 dispatch candidates ===");
        for (int i = 0; i < Math.min(5, sorted.size()); i++) {
            if (monitor.isCancelled()) break;
            Address fa = sorted.get(i).getKey();
            Function f = fm.getFunctionAt(fa);
            DecompileResults r = ifc.decompileFunction(f, 120, monitor);
            pw.println();
            pw.println("// ============================================");
            pw.println("// " + f.getName(true) + " @ " + fa
                    + "  (Event_* callees: " + sorted.get(i).getValue() + ")");
            pw.println("// ============================================");
            if (r != null && r.decompileCompleted()) pw.print(r.getDecompiledFunction().getC());
            else pw.println("// failed");
        }
        pw.close();
        println("dumped top opcode dispatch candidates -> " + out);
    }
}
