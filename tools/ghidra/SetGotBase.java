// r10 (sl, GOT base) 레지스터 값을 0xb2c40 으로 설정하고 재분석 트리거.
// 그 후 모든 PIC indirect references 가 자동 해소된다.
//
// @category Hero3
// @runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.lang.Register;
import ghidra.program.model.lang.RegisterValue;
import ghidra.program.model.listing.ProgramContext;
import ghidra.program.model.mem.Memory;
import ghidra.app.services.ProgramManager;
import ghidra.app.plugin.core.analysis.AutoAnalysisManager;

import java.math.BigInteger;

public class SetGotBase extends GhidraScript {

    private static final long GOT_BASE = 0xb2c40L;

    @Override
    protected void run() throws Exception {
        Register r10 = currentProgram.getRegister("r10");
        if (r10 == null) r10 = currentProgram.getRegister("sl");
        if (r10 == null) {
            println("r10/sl register not found");
            return;
        }
        ProgramContext ctx = currentProgram.getProgramContext();
        Memory mem = currentProgram.getMemory();
        Address start = mem.getMinAddress();
        Address end = mem.getMaxAddress();

        RegisterValue rv = new RegisterValue(r10, BigInteger.valueOf(GOT_BASE));
        ctx.setRegisterValue(start, end, rv);
        println("Set " + r10.getName() + "=0x" + Long.toHexString(GOT_BASE) + " across " + start + "-" + end);

        // 모든 함수 재해석 / 분석 재실행
        AutoAnalysisManager mgr = AutoAnalysisManager.getAnalysisManager(currentProgram);
        AddressSet allCode = new AddressSet(start, end);
        mgr.reAnalyzeAll(allCode);
        mgr.startAnalysis(monitor);
        println("Re-analysis triggered");
    }
}
