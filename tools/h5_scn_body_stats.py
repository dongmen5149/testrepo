"""scene body opcode 빈도 통계 + 미정의/이상 패턴 검출.

interpreter.gd 의 step() 과 동일한 디스패치 규칙을 Python 으로 재현하여
258 .scn body 를 정적으로 trace. Godot 실행 환경 없이도 어떤 opcode 가
얼마나 자주 등장하는지, 미정의 opcode 가 있는지, ESC 마커가 어디에
배치되는지를 한눈에 본다.

산출:
  work/h5/analysis/scn_body_stats.tsv     — opcode → count, scene 수
  work/h5/analysis/scn_body_anomalies.txt — 미정의 opcode / 잘림 / 이상 ESC

사용:
  python tools/h5_scn_body_stats.py
"""
from __future__ import annotations
import collections, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BODIES = ROOT / "apps/hero5-godot/assets/scenes/bodies"
TABLE = ROOT / "apps/hero5-godot/assets/scenes/opcode_table.json"
INDEX = ROOT / "apps/hero5-godot/assets/scenes/index.json"
OUT_TSV = ROOT / "work/h5/analysis/scn_body_stats.tsv"
OUT_ANOM = ROOT / "work/h5/analysis/scn_body_anomalies.txt"


def load_table() -> dict[int, tuple[str, int]]:
    if not TABLE.exists():
        print(f"[error] {TABLE} 없음 — import_to_godot.py 먼저 실행", file=sys.stderr)
        sys.exit(1)
    raw = json.loads(TABLE.read_text())
    out: dict[int, tuple[str, int]] = {}
    for e in raw["opcodes"]:
        out[int(e["op"])] = (str(e["name"]), int(e["size"]))
    return out


def trace(body: bytes, table: dict[int, tuple[str, int]]) -> dict:
    """interpreter.gd::step 과 동일 규칙. max_steps 없이 끝까지."""
    pos = 0
    n = len(body)
    counts: collections.Counter = collections.Counter()
    esc_count = 0
    end_marker = False
    truncated = False
    unknown: list[tuple[int, int]] = []  # (pos, op)

    while pos < n:
        op = body[pos]; pos += 1

        if op == 0xFF:
            if pos >= n:
                truncated = True; break
            argc = body[pos]; pos += 1
            if argc > 0x13:
                end_marker = True
                break
            if pos + argc > n:
                truncated = True; break
            sizes = list(body[pos:pos+argc]); pos += argc
            total = sum(sizes)
            if pos + total > n:
                truncated = True; break
            pos += total
            esc_count += 1
            continue

        entry = table.get(op)
        if entry is None:
            unknown.append((pos - 1, op))
            counts[("?", op)] += 1
            # 진행 안전장치: 알 수 없는 opcode → 1B 만 소비하고 계속.
            continue
        name, sz = entry
        if pos + sz > n:
            truncated = True; break
        counts[(name, op)] += 1
        pos += sz

    return {
        "counts": counts,
        "esc": esc_count,
        "end": end_marker,
        "trunc": truncated,
        "unknown": unknown,
        "consumed": pos,
        "total": n,
    }


def main() -> int:
    table = load_table()
    if not BODIES.exists():
        print(f"[error] {BODIES} 없음 — import_to_godot.py 먼저 실행", file=sys.stderr)
        return 1

    scene_index = {e["index"]: e for e in json.loads(INDEX.read_text())}

    global_counts: collections.Counter = collections.Counter()
    scene_counts: collections.Counter = collections.Counter()  # opcode → 등장한 씬 수
    anomalies: list[str] = []
    unknown_total: collections.Counter = collections.Counter()
    end_ok = trunc_n = 0

    files = sorted(BODIES.glob("*.bin"))
    for fp in files:
        body = fp.read_bytes()
        r = trace(body, table)

        seen = set()
        for k, v in r["counts"].items():
            global_counts[k] += v
            seen.add(k)
        for k in seen:
            scene_counts[k] += 1

        for pos, op in r["unknown"]:
            unknown_total[op] += 1

        if r["end"]:
            end_ok += 1
        if r["trunc"]:
            trunc_n += 1
            idx = int(fp.stem)
            meta = scene_index.get(idx, {})
            anomalies.append(
                f"trunc {fp.name} consumed={r['consumed']}/{r['total']} "
                f"name={meta.get('name', '?')}"
            )

    # ── TSV ───────────────────────────────────────────────────────────
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("op\tname\tcount\tscenes\n")
        for (name, op), c in sorted(global_counts.items(), key=lambda kv: -kv[1]):
            f.write(f"0x{op:02x}\t{name}\t{c}\t{scene_counts[(name, op)]}\n")

    # ── 이상 보고 ────────────────────────────────────────────────────
    with OUT_ANOM.open("w", encoding="utf-8") as f:
        f.write(f"# Hero5 .scn body 정적 trace 보고\n")
        f.write(f"파일: {len(files)}    end_marker: {end_ok}    trunc: {trunc_n}\n")
        f.write(f"unknown opcodes: {len(unknown_total)} distinct, {sum(unknown_total.values())} occurrences\n\n")

        f.write("## 미정의 opcode (table 에 없음)\n")
        if unknown_total:
            for op, c in sorted(unknown_total.items(), key=lambda kv: -kv[1]):
                f.write(f"  0x{op:02x}  ×{c}\n")
        else:
            f.write("  (없음 — 77/77 dispatch 완전)\n")
        f.write("\n## 잘린(truncated) body\n")
        if anomalies:
            f.write("\n".join(anomalies) + "\n")
        else:
            f.write("  (없음)\n")

    # ── 콘솔 요약 ────────────────────────────────────────────────────
    print(f"scenes: {len(files)}")
    print(f"end marker: {end_ok}/{len(files)}    truncated: {trunc_n}")
    print(f"unknown opcodes: {len(unknown_total)} distinct ({sum(unknown_total.values())} occurrences)")
    print(f"\nTOP 15 opcodes:")
    print(f"{'op':>5}  {'name':<32}  {'count':>6}  {'scenes':>6}")
    for (name, op), c in sorted(global_counts.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  0x{op:02x}  {name:<32}  {c:>6}  {scene_counts[(name, op)]:>6}")
    print(f"\nwrote {OUT_TSV.relative_to(ROOT)}")
    print(f"wrote {OUT_ANOM.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
