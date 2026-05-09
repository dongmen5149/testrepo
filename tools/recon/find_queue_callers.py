"""§4.4 후속 — GVM 이벤트 큐 API caller 매핑 (자동 분석 2J).

배경 (2026-05-10 PM-2 발견):
  FUN_0007e150 (byte buffer append) / FUN_0007e184 (memcpy read) /
  FUN_0007e890 (ring buffer flush+swap) / FUN_0007e1c4 (32-bit word append) /
  FUN_0007e204 (?) — GVM SDK 의 이벤트 큐 / 명령 큐 / 직렬화 API.

이번 도구의 목적:
  바이너리 전체에서 BL 로 큐 API 를 호출하는 사이트 발견 + 어떤 함수에서 호출하는지 매핑.
  → 게임 로직의 producer (큐에 데이터 쓰는 측) / consumer (큐를 읽는 측) 파악.

전략:
  1. capstone 으로 binary 전체 BL 명령 추출 (Thumb-2 BL 디코드)
  2. target ∈ QUEUE_FUNCS 인 BL 사이트 모두 수집
  3. 각 BL site 의 포함 함수 식별 (all_decompiled.c 의 entry 주소 sorted scan)
  4. 함수별 큐 API 호출 횟수 집계

추가:
  - producer (write-only: 0x7e150, 0x7e1c4) vs consumer (read: 0x7e184) 분류
  - flush (0x7e890) 호출 함수 식별 → 큐 lifecycle 관리자 후보
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "queue_callers.json"

# Known GVM event queue API addresses (2026-05-10 PM-2 발견)
QUEUE_FUNCS = {
    0x0007e150: ("byte_append", "producer"),
    0x0007e184: ("memcpy_read", "consumer"),
    0x0007e1c4: ("u32_append", "producer"),
    0x0007e204: ("u32_write_indirect", "producer"),
    0x0007e890: ("flush_swap", "lifecycle"),
    0x0007e7ac: ("init_or_helper", "lifecycle"),
    0x0007e0e4: ("alloc_buffer", "lifecycle"),
    0x0007ea98: ("buffer_status", "consumer"),
    0x0007e63c: ("?", "consumer"),
    0x0007e4c4: ("set_byte", "producer"),
}

ENTRY_RE = re.compile(
    r'^(?:void|undefined\d?|short|int|uint|char|byte|long|longlong|float|double|bool|ushort|ulong)\s+(FUN_([0-9a-f]+))\(',
    re.MULTILINE,
)


def collect_entries(text: str) -> list[tuple[str, int]]:
    seen = set()
    out = []
    for m in ENTRY_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, int(m.group(2), 16)))
    out.sort(key=lambda x: x[1])
    return out


def find_enclosing_func(addr: int, entries: list[tuple[str, int]]) -> str:
    """Binary search for enclosing function name."""
    lo, hi = 0, len(entries) - 1
    result = "?"
    while lo <= hi:
        mid = (lo + hi) // 2
        if entries[mid][1] <= addr:
            result = entries[mid][0]
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def main() -> None:
    if not BIN.exists() or not DECOMPILED.exists():
        print("!! input missing")
        return
    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")

    entries = collect_entries(text)
    print(f"=== {len(entries)} decompiled function entries ===")
    print(f"=== scanning binary ({len(data)} bytes) for BL to {len(QUEUE_FUNCS)} queue API targets ===")

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    bl_sites: list[tuple[int, int]] = []  # (call_site, target)
    pos = 0
    end = len(data)
    while pos < end:
        chunk = data[pos:end]
        any_emitted = False
        last = pos
        for ins in md.disasm(chunk, pos):
            if ins.mnemonic in ("bl", "blx"):
                tok = ins.op_str.strip().lstrip("#")
                if tok.startswith("0x"):
                    try:
                        target = int(tok, 16)
                        if target in QUEUE_FUNCS:
                            bl_sites.append((ins.address, target))
                    except ValueError:
                        pass
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2

    print(f"\n=== {len(bl_sites)} BL sites to queue API ===")
    target_counter = Counter(t for _, t in bl_sites)
    print("by target:")
    for t, c in sorted(target_counter.items()):
        label, role = QUEUE_FUNCS[t]
        print(f"  0x{t:08x} [{role:>10}] {label:<25}: {c} calls")

    # Group by enclosing function
    func_calls: defaultdict[str, list[tuple[int, int]]] = defaultdict(list)
    for site, target in bl_sites:
        func_name = find_enclosing_func(site, entries)
        func_calls[func_name].append((site, target))

    # Sort functions by total queue calls desc
    func_summary = []
    for func_name, calls in func_calls.items():
        c_counter = Counter(t for _, t in calls)
        # Compute role: producer / consumer / lifecycle / mixed
        roles = set()
        for t in c_counter:
            roles.add(QUEUE_FUNCS[t][1])
        if len(roles) == 1:
            role = next(iter(roles))
        else:
            role = "mixed"
        func_summary.append({
            "func": func_name,
            "call_count": len(calls),
            "role": role,
            "by_target": dict(c_counter),
            "first_site": calls[0][0] if calls else None,
        })
    func_summary.sort(key=lambda x: -x["call_count"])

    print(f"\n=== {len(func_summary)} distinct caller functions, top 30 ===")
    print(f"{'rank':<5} {'func':<24} {'calls':<6} {'role':<11} top targets")
    print("-" * 90)
    for i, f in enumerate(func_summary[:30], 1):
        targets_str = ", ".join(
            f"{QUEUE_FUNCS[t][0]}:{c}" for t, c in sorted(f["by_target"].items(), key=lambda x: -x[1])
        )
        print(f"{i:<5} {f['func']:<24} {f['call_count']:<6} {f['role']:<11} {targets_str}")

    # Producer-only callers (most likely game state machines that emit events)
    producer_only = [f for f in func_summary if f["role"] == "producer"]
    print(f"\n=== producer-only callers: {len(producer_only)} ===")
    for f in producer_only[:15]:
        targets_str = ", ".join(
            f"{QUEUE_FUNCS[t][0]}:{c}" for t, c in sorted(f["by_target"].items(), key=lambda x: -x[1])
        )
        print(f"  {f['func']:<24} calls={f['call_count']:<3} {targets_str}")

    # Consumer-only callers
    consumer_only = [f for f in func_summary if f["role"] == "consumer"]
    print(f"\n=== consumer-only callers: {len(consumer_only)} ===")
    for f in consumer_only[:15]:
        targets_str = ", ".join(
            f"{QUEUE_FUNCS[t][0]}:{c}" for t, c in sorted(f["by_target"].items(), key=lambda x: -x[1])
        )
        print(f"  {f['func']:<24} calls={f['call_count']:<3} {targets_str}")

    # Lifecycle callers
    lifecycle = [f for f in func_summary if f["role"] == "lifecycle"]
    print(f"\n=== lifecycle callers: {len(lifecycle)} ===")
    for f in lifecycle[:15]:
        targets_str = ", ".join(
            f"{QUEUE_FUNCS[t][0]}:{c}" for t, c in sorted(f["by_target"].items(), key=lambda x: -x[1])
        )
        print(f"  {f['func']:<24} calls={f['call_count']:<3} {targets_str}")

    out = {
        "queue_funcs": {f"0x{a:08x}": {"label": l, "role": r} for a, (l, r) in QUEUE_FUNCS.items()},
        "bl_site_count": len(bl_sites),
        "by_target": [
            {"target": f"0x{t:08x}", "label": QUEUE_FUNCS[t][0], "role": QUEUE_FUNCS[t][1], "count": c}
            for t, c in sorted(target_counter.items())
        ],
        "callers": [
            {
                "func": f["func"],
                "calls": f["call_count"],
                "role": f["role"],
                "by_target": {f"0x{t:08x}": c for t, c in f["by_target"].items()},
            }
            for f in func_summary
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
