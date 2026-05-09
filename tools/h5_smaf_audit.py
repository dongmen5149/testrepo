"""SMAF (.mmf) ↔ OGG 1:1 매칭 검증 + SMAF 청크 구조 dump.

핵심 발견: 42 SMAF 와 42 OGG 가 **완전히 동일한 자산 set 을 커버**.
즉 SMAF→OGG 변환이 불필요 — OGG 만 임포트하면 모든 BGM/SFX 가 채워진다.
이 도구는 그 사실을 정량적으로 증명 + SMAF 의 청크 트리(향후 자체 디코딩
또는 외부 변환 시 참조용)를 dump.

산출:
  work/h5/analysis/smaf_audit.tsv      ─ asset → (smaf_size, ogg_size, smaf_chunks)
  work/h5/analysis/smaf_chunks.txt     ─ 청크 트리 dump (앞 5개 파일)
"""
from __future__ import annotations
import csv, pathlib, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "work/h5/vfs_entries"
NAMES = ROOT / "work/h5/analysis/asset_names.tsv"
OUT_TSV = ROOT / "work/h5/analysis/smaf_audit.tsv"
OUT_TREE = ROOT / "work/h5/analysis/smaf_chunks.txt"


def parse_chunks(data: bytes) -> list[tuple[str, int]]:
    """MMMD 컨테이너 안의 top-level 청크 트리. (tag, size) list."""
    if data[:4] != b"MMMD":
        return []
    out = []
    i = 8  # MMMD + 4B BE size
    n = len(data)
    while i + 8 <= n:
        tag = data[i:i+4].decode("latin1", errors="replace")
        sz = struct.unpack_from(">I", data, i+4)[0]
        out.append((tag, sz))
        if sz == 0 or i + 8 + sz > n:
            break
        i += 8 + sz
    return out


def main() -> int:
    if not NAMES.exists():
        print("asset_names.tsv 없음 — h5_recover_names.py 먼저", file=sys.stderr)
        return 1

    name_by_idx: dict[int, str] = {}
    with NAMES.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            n = row.get("recovered_name", "")
            if n.startswith("c/snd/"):
                name_by_idx[int(row["index"])] = n

    # asset basename (확장자 제거) 별로 OGG/MMF 모음
    pairs: dict[str, dict[str, tuple[int, int]]] = {}  # base → {ext: (idx, size)}
    for idx, name in name_by_idx.items():
        base, _, ext = name.rpartition(".")
        if ext not in ("ogg", "mmf"):
            continue
        # vfs entry 파일 이름 = "{idx:05d}_{hash:08x}.{type}"
        hits = list(ENTRIES.glob(f"{idx:05d}_*"))
        if not hits:
            continue
        size = hits[0].stat().st_size
        pairs.setdefault(base, {})[ext] = (idx, size)

    # ── TSV ─────────────────────────────────────────────────────
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    paired = lonely_smaf = lonely_ogg = 0
    with OUT_TSV.open("w", encoding="utf-8") as f:
        f.write("asset_base\tsmaf_size\togg_size\tsmaf_chunks\n")
        for base in sorted(pairs):
            d = pairs[base]
            mmf = d.get("mmf"); ogg = d.get("ogg")
            mmf_size = mmf[1] if mmf else -1
            ogg_size = ogg[1] if ogg else -1

            chunk_str = ""
            if mmf:
                hits = list(ENTRIES.glob(f"{mmf[0]:05d}_*"))
                if hits:
                    data = hits[0].read_bytes()
                    chunks = parse_chunks(data)
                    chunk_str = " ".join(f"{t}({s})" for t, s in chunks)

            if mmf and ogg:
                paired += 1
            elif mmf:
                lonely_smaf += 1
            elif ogg:
                lonely_ogg += 1

            f.write(f"{base}\t{mmf_size}\t{ogg_size}\t{chunk_str}\n")

    # ── 청크 트리 dump (sample) ────────────────────────────────
    samples = []
    for base in sorted(pairs)[:5]:
        d = pairs[base]
        if "mmf" not in d:
            continue
        idx, _ = d["mmf"]
        hits = list(ENTRIES.glob(f"{idx:05d}_*"))
        if not hits:
            continue
        data = hits[0].read_bytes()
        samples.append((base, data))

    with OUT_TREE.open("w", encoding="utf-8") as f:
        f.write("# Hero5 SMAF top-level 청크 dump (앞 5개)\n\n")
        for base, data in samples:
            f.write(f"## {base}.mmf  size={len(data)}\n")
            outer_size = struct.unpack_from(">I", data, 4)[0]
            f.write(f"   outer MMMD size={outer_size}\n")
            for tag, sz in parse_chunks(data):
                f.write(f"   - {tag!r}  size={sz}\n")
            f.write("\n")

    # ── 콘솔 요약 ──────────────────────────────────────────────
    print(f"asset bases: {len(pairs)}")
    print(f"  paired (SMAF + OGG): {paired}")
    print(f"  SMAF only:           {lonely_smaf}")
    print(f"  OGG only:            {lonely_ogg}")
    if lonely_smaf == 0:
        print("\n→ OGG 가 SMAF 전체를 1:1 커버. SMAF→OGG 변환 불필요.")
    print(f"\nwrote {OUT_TSV.relative_to(ROOT)}")
    print(f"wrote {OUT_TREE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
