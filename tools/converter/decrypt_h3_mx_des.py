"""Round 73 — Hero3 의 8 DES 파일을 Hero5 `mx_des_decrypt` 변종으로 시도.

R57: Hero3 key = "0EP@KO91"
R58: 표준 ECB / CBC+zero / CBC+key / parity / bit-reverse 5 변종 모두 실패
R68 (Hero4): Hero5 `mx_des_decrypt` 변종 으로 407 파일 복호화 성공 (key J@IWO8N7)
R73 가설: Hero3 도 동일 mx 변종 사용 가능 (벤더 공통 cipher)

검증 (Hero4 R69 패턴):
  1. 8-byte align 통과
  2. 복호 후 entropy 감소 (7.x → 5.x 미만이면 평문 후보)
  3. EUC-KR Korean pair runs 발견
  4. 구조적 패턴 (size byte + name_len + EUC-KR + body) 존재

Output: work/h3/decrypted/{file}, work/h3/converted/h3_des_decryption.{json,log}
"""
from __future__ import annotations
import json
import math
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from h5_des import mx_des_decrypt

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXTRACTED = ROOT / "work" / "h3" / "extracted" / "dat"
DECRYPTED = ROOT / "work" / "h3" / "decrypted"
DECRYPTED.mkdir(parents=True, exist_ok=True)
OUT_JSON = ROOT / "work" / "h3" / "converted" / "h3_des_decryption.json"
OUT_LOG  = ROOT / "work" / "h3" / "converted" / "h3_des_decryption.log"

# R57 확정 키
KEY_H3 = b"0EP@KO91"
# Hero4 키 (벤더 공통 가능성)
KEY_H4 = b"J@IWO8N7"

TARGETS = [
    "i15_dat", "drop_dat", "droph_dat", "getitem_dat",
    "smith_dat", "smithh_dat", "shop_dat", "shoph_dat",
]


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    h = 0.0
    for c in counts.values():
        p = c / n
        h -= p * math.log2(p)
    return h


def korean_run_count(data: bytes, min_len: int = 4) -> int:
    """EUC-KR Korean (pair 0xa1-0xfe) run 개수."""
    runs = 0
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            if i - start >= min_len:
                runs += 1
        else:
            i += 1
    return runs


def sample_korean(data: bytes, max_samples: int = 5) -> list[str]:
    samples: list[str] = []
    i = 0
    while i < len(data) - 1 and len(samples) < max_samples:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            chunk = data[start:i]
            if len(chunk) >= 4:
                try:
                    samples.append(chunk.decode("cp949", errors="replace"))
                except Exception:
                    pass
        else:
            i += 1
    return samples


def looks_like_plaintext(data: bytes, threshold_entropy: float = 6.5,
                        min_korean_runs: int = 1) -> bool:
    """평문 후보 판정."""
    if shannon_entropy(data) > threshold_entropy:
        # ASCII-heavy 파일도 평문일 수 있음 (entropy 가 낮지 않아도 됨)
        ascii_ratio = sum(1 for b in data if 0x20 <= b < 0x7f) / max(1, len(data))
        if ascii_ratio > 0.5:
            return True
        return False
    if korean_run_count(data) >= min_korean_runs:
        return True
    # entropy 가 낮으면서 EUC-KR 없으면 binary 구조 가능 (size-prefixed table 등)
    return shannon_entropy(data) < 5.0


def try_decrypt(path: pathlib.Path, key: bytes, label: str) -> dict:
    raw = path.read_bytes()
    n = len(raw)
    if n % 8 != 0:
        return {
            "file": path.name, "key": label, "size": n,
            "status": "skip_align", "entropy_in": round(shannon_entropy(raw), 3),
        }
    try:
        plain = mx_des_decrypt(raw, key)
    except Exception as e:
        return {"file": path.name, "key": label, "size": n,
                "status": "decrypt_error", "error": str(e)}

    ent_in = shannon_entropy(raw)
    ent_out = shannon_entropy(plain)
    ko_runs = korean_run_count(plain)
    plaintext = looks_like_plaintext(plain)
    samples = sample_korean(plain) if ko_runs > 0 else []

    return {
        "file": path.name, "key": label, "size": n,
        "entropy_in": round(ent_in, 3),
        "entropy_out": round(ent_out, 3),
        "entropy_delta": round(ent_in - ent_out, 3),
        "korean_runs": ko_runs,
        "samples": samples[:3],
        "looks_plaintext": plaintext,
        "first_64_hex": plain[:64].hex(" "),
        "status": "PASS" if plaintext else "fail",
        "_plain_bytes": plain,
    }


def main() -> int:
    results: list[dict] = []
    summary_lines: list[str] = [
        "===== Hero3 DES decryption (R73 mx_des_decrypt 변종) =====\n",
    ]

    for fn in TARGETS:
        path = EXTRACTED / fn
        if not path.exists():
            print(f"  ! missing: {path}")
            continue
        for label, key in [("0EP@KO91", KEY_H3), ("J@IWO8N7", KEY_H4)]:
            r = try_decrypt(path, key, label)
            results.append({k: v for k, v in r.items() if k != "_plain_bytes"})
            mark = "✓" if r.get("status") == "PASS" else "✗"
            summary_lines.append(
                f"  {mark} {fn:<14} key={label} "
                f"entropy {r.get('entropy_in','?'):>5} → {r.get('entropy_out','?'):>5} "
                f"(Δ{r.get('entropy_delta','?'):>5}) "
                f"ko_runs={r.get('korean_runs','?')} "
                f"status={r.get('status','?')}"
            )
            # PASS 인 경우 plain bytes 저장
            if r.get("status") == "PASS":
                out_path = DECRYPTED / f"{fn}.{label}.plain"
                out_path.write_bytes(r["_plain_bytes"])
                summary_lines.append(f"      → wrote {out_path}")
                if r.get("samples"):
                    summary_lines.append(f"      → 한글 samples: {r['samples'][:2]}")

    # Aggregate
    pass_count = sum(1 for r in results if r.get("status") == "PASS")
    summary_lines.insert(1, f"Targets: {len(TARGETS)} files × 2 keys = {len(results)} attempts")
    summary_lines.insert(2, f"PASS:    {pass_count} / {len(results)}")
    summary_lines.append("")
    if pass_count == 0:
        summary_lines.append("결과: mx_des_decrypt 변종 + (0EP@KO91 / J@IWO8N7) 모두 실패")
        summary_lines.append("후속: binary 의 다른 8-byte ASCII 후보 + Ghidra MX_desDecrypt 함수 ARM disasm 필요")
    else:
        summary_lines.append(f"결과: {pass_count} 파일 복호화 성공. boss skill ID / smith 레시피 / shop 매핑 가능")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_LOG.write_text("\n".join(summary_lines), encoding="utf-8")

    print("\n".join(summary_lines))
    print(f"\nWrote {OUT_JSON}")
    print(f"Wrote {OUT_LOG}")
    return 0 if pass_count > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
