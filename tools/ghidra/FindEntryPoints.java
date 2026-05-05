// Ghidra GhidraScript (Java) — §4.1~4.4 진입점 자동 식별 + 디컴파일.
// 결과: d:/testrepo/work/ghidra_out/entry_points.json + decompiled .c
//
// @category Hero3
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.listing.Program;
import ghidra.program.model.listing.Data;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.listing.DataIterator;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class FindEntryPoints extends GhidraScript {

    private static final String OUT_DIR = "c:/gameRemake/testrepo/work/ghidra_out";

    private static final String[][] TARGETS = {
        {"4.1_bitmap_decoder", "frameBuf is NULL"},
        {"4.2_mp_extras",      "Event_freeID", "loadDataID"},
        {"4.3_cif_animation",  "Hero_Free", "freeBossType"},
        {"4.4_scn_opcodes",    "onEventMessageOkKey", "eventManager"},
    };

    @Override
    protected void run() throws Exception {
        new File(OUT_DIR).mkdirs();
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);

        StringBuilder json = new StringBuilder();
        json.append("{\n");

        for (int t = 0; t < TARGETS.length; t++) {
            String[] row = TARGETS[t];
            String tag = row[0];
            File tagDir = new File(OUT_DIR, tag);
            tagDir.mkdirs();

            json.append("  \"").append(tag).append("\": {\n");
            json.append("    \"matches\": [\n");
            boolean firstMatch = true;

            for (int i = 1; i < row.length; i++) {
                String needle = row[i];
                println("[" + tag + "] searching '" + needle + "' ...");

                List<Address> stringAddrs = findStrings(needle);
                for (Address sa : stringAddrs) {
                    // 1) Ghidra 가 잡은 직접 xref
                    List<Reference> refs = xrefsTo(sa);
                    for (Reference r : refs) {
                        Address fromAddr = r.getFromAddress();
                        Function f = currentProgram.getFunctionManager().getFunctionContaining(fromAddr);
                        if (f == null) continue;
                        emitFunc(json, ifc, tagDir, needle, sa, fromAddr, f, "direct_xref", firstMatch);
                        firstMatch = false;
                    }
                    // 2) literal pool 스캔 (PIC GOT 우회)
                    List<Address> lps = findLiteralPoolReferences(sa);
                    println("  literal-pool refs for " + sa + " : " + lps.size());
                    for (Address lp : lps) {
                        Function f = findFunctionNearLiteral(lp);
                        if (f == null) continue;
                        emitFunc(json, ifc, tagDir, needle, sa, lp, f, "lit_pool", firstMatch);
                        firstMatch = false;
                    }
                }

                Function byName = findFunctionByName(needle);
                if (byName != null) {
                    String fentry = byName.getEntryPoint().toString();
                    File outC = new File(tagDir, "byname_" + sanitize(needle) + "_" + fentry + ".c");
                    if (!outC.exists()) {
                        String c = decompile(ifc, byName);
                        if (c != null) {
                            PrintWriter pw = new PrintWriter(new FileWriter(outC));
                            pw.println("// function found by name: " + needle + " @ " + fentry);
                            pw.println();
                            pw.print(c);
                            pw.close();
                        }
                    }
                    if (!firstMatch) json.append(",\n");
                    json.append("      {\"needle\":\"").append(esc(needle)).append("\",")
                        .append("\"by_name\":true,")
                        .append("\"func_entry\":\"").append(fentry).append("\"}");
                    firstMatch = false;
                }
            }

            json.append("\n    ]\n  }");
            if (t < TARGETS.length - 1) json.append(",");
            json.append("\n");
        }

        json.append("}\n");
        File summary = new File(OUT_DIR, "entry_points.json");
        PrintWriter pw = new PrintWriter(new FileWriter(summary));
        pw.print(json.toString());
        pw.close();
        println("Wrote summary: " + summary.getAbsolutePath());
    }

    private List<Address> findStrings(String needle) throws Exception {
        List<Address> out = new ArrayList<>();
        Memory mem = currentProgram.getMemory();
        println("  mem.minAddr=" + mem.getMinAddress() + "  maxAddr=" + mem.getMaxAddress());

        // 정의된 데이터에서 needle 검색 (타입 무관, value 문자열 포함 여부)
        DataIterator dit = currentProgram.getListing().getDefinedData(true);
        int dataCount = 0;
        while (dit.hasNext()) {
            Data d = dit.next();
            dataCount++;
            Object v = d.getValue();
            if (v != null && v.toString().contains(needle)) {
                out.add(d.getAddress());
                println("  defined-data hit @ " + d.getAddress() + " : " + v);
            }
        }
        println("  scanned " + dataCount + " defined-data items");

        // raw byte 검색 — 모든 매치 수집
        byte[] pattern = needle.getBytes("ASCII");
        Address cur = mem.getMinAddress();
        int rawMatches = 0;
        while (cur != null && rawMatches < 20) {
            Address found = mem.findBytes(cur, pattern, null, true, monitor);
            if (found == null) break;
            if (!out.contains(found)) {
                out.add(found);
                println("  raw hit @ " + found);
            }
            rawMatches++;
            try { cur = found.add(1); } catch (Exception e) { break; }
        }
        return out;
    }

    private List<Reference> xrefsTo(Address a) {
        List<Reference> out = new ArrayList<>();
        ReferenceManager rm = currentProgram.getReferenceManager();
        Iterator<Reference> it = rm.getReferencesTo(a).iterator();
        while (it.hasNext()) out.add(it.next());
        return out;
    }

    /**
     * GOT-기반 PIC 코드는 자동 xref가 안 잡힘. 대신 문자열 주소를 4-byte LE
     * 리터럴로 보유한 위치를 직접 스캔. 이 위치 자체는 데이터(literal pool)이고,
     * 그 근처 또는 직전 함수가 진짜 사용처일 가능성이 높음.
     */
    private List<Address> findLiteralPoolReferences(Address strAddr) throws Exception {
        List<Address> hits = new ArrayList<>();
        Memory mem = currentProgram.getMemory();
        long offs = strAddr.getOffset();
        // 4-byte LE
        byte[] pat = new byte[] {
            (byte)(offs & 0xff),
            (byte)((offs >> 8) & 0xff),
            (byte)((offs >> 16) & 0xff),
            (byte)((offs >> 24) & 0xff),
        };
        Address cur = mem.getMinAddress();
        int n = 0;
        while (cur != null && n < 50) {
            Address found = mem.findBytes(cur, pat, null, true, monitor);
            if (found == null) break;
            hits.add(found);
            n++;
            try { cur = found.add(1); } catch (Exception e) { break; }
        }
        return hits;
    }

    /**
     * literal pool 위치 lpAddr 가 속한, 또는 직전에 위치한 함수를 찾는다.
     * ARM Thumb 코드는 literal pool 이 함수 끝에 붙어 있는 경우가 많음.
     */
    private Function findFunctionNearLiteral(Address lpAddr) {
        Function f = currentProgram.getFunctionManager().getFunctionContaining(lpAddr);
        if (f != null) return f;
        // 직전 함수: lpAddr 이전 entry point 중 최대값
        Function best = null;
        long bestOffs = -1;
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        long target = lpAddr.getOffset();
        while (fit.hasNext()) {
            Function ff = fit.next();
            long off = ff.getEntryPoint().getOffset();
            if (off < target && off > bestOffs) {
                bestOffs = off;
                best = ff;
            }
        }
        if (best != null) {
            long delta = target - bestOffs;
            // literal pool 은 함수 바로 뒤. 2KB 이내면 같은 함수의 풀로 본다.
            if (delta < 0x800) return best;
        }
        return null;
    }

    private Function findFunctionByName(String name) {
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext()) {
            Function f = fit.next();
            if (f.getName().equals(name)) return f;
        }
        return null;
    }

    private String decompile(DecompInterface ifc, Function f) {
        DecompileResults r = ifc.decompileFunction(f, 60, monitor);
        if (r != null && r.decompileCompleted()) {
            return r.getDecompiledFunction().getC();
        }
        return null;
    }

    private static String sanitize(String s) {
        return s.replaceAll("[^A-Za-z0-9_]", "_");
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private void emitFunc(StringBuilder json, DecompInterface ifc, File tagDir,
                          String needle, Address strAddr, Address refAddr, Function f,
                          String mode, boolean isFirst) throws Exception {
        String fname = f.getName();
        String fentry = f.getEntryPoint().toString();
        File outC = new File(tagDir, sanitize(fname) + "_" + fentry + ".c");
        if (!outC.exists()) {
            String c = decompile(ifc, f);
            if (c != null) {
                PrintWriter pw = new PrintWriter(new FileWriter(outC));
                pw.println("// mode: " + mode);
                pw.println("// needle: '" + needle + "' @ " + strAddr);
                pw.println("// ref point: " + refAddr);
                pw.println("// function: " + fname + " @ " + fentry);
                pw.println();
                pw.print(c);
                pw.close();
            }
        }
        if (!isFirst) json.append(",\n");
        json.append("      {\"needle\":\"").append(esc(needle)).append("\",")
            .append("\"mode\":\"").append(mode).append("\",")
            .append("\"string_addr\":\"").append(strAddr).append("\",")
            .append("\"ref_addr\":\"").append(refAddr).append("\",")
            .append("\"func_name\":\"").append(esc(fname)).append("\",")
            .append("\"func_entry\":\"").append(fentry).append("\"}");
    }
}
