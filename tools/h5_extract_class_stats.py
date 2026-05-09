"""c_csv_class.json 의 extra_hex 에서 5 클래스 base stat 추출.

LoadResClassInfo 패턴 (Round 7):
- byte offset 0..7  : 4 short = str/dex/int/con base (V[60..63])
- byte offset 8..15 : 4 short = (zeroes / class init bonus?)
- byte offset 16..23: 4 short = (other init data)
- byte offset 24..27: 2 short = (other class info)
- byte offset 28+   : 6 short = atk_growth_coef + 5 secondary stat base
                       (V[111] + V[112..116])

5 클래스 비교를 통해 V[112..116] secondary stat 의 의미를 추정.
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSON = ROOT / "apps/hero5-godot/assets/gamedata/c_csv_class.json"
OUT = ROOT / "work/h5/analysis/class_stats_table.txt"


def parse_hex_to_shorts(hex_str: str) -> list[int]:
    """hex 문자열 → LE u16 리스트."""
    bs = bytes.fromhex(hex_str)
    shorts = []
    for i in range(0, len(bs) - 1, 2):
        shorts.append(int.from_bytes(bs[i:i+2], "little", signed=False))
    return shorts


def main() -> int:
    data = json.loads(JSON.read_text(encoding="utf-8"))
    rows = []
    for rec in data["records"]:
        name = rec["name"]
        shorts = parse_hex_to_shorts(rec["extra_hex"])
        rows.append((name, shorts))

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("# c_csv_class.json — 5 클래스 base stat 추출\n\n")
        f.write("LoadResClassInfo 가 sequential ByteToInt16 으로 읽어 store 하는 영역:\n")
        f.write("  - V[60..63] (0x236..0x23c)   = base str/dex/int/con   (idx 0..3)\n")
        f.write("  - V[111]    (0x278)          = atk_growth_coefficient (idx 14)\n")
        f.write("  - V[112..116] (0x27a..0x282) = secondary stat base    (idx 15..19)\n\n")

        # idx별 비교 (모든 클래스의 같은 idx 값)
        max_len = max(len(s) for _, s in rows)
        f.write("idx  byte_off  ")
        for n, _ in rows:
            f.write(f"{n:>10s}  ")
        f.write(" 추정\n")
        f.write("---  --------  ")
        for _ in rows:
            f.write(f"{'-'*10}  ")
        f.write(" -----------\n")

        # idx 라벨 추정 (위 LoadResClassInfo Round 7 매핑)
        idx_label = {
            0: "V[60] base_str",
            1: "V[61] base_dex",
            2: "V[62] base_int",
            3: "V[63] base_con",
            4: "(init bonus 0)",
            5: "(init bonus 1)",
            6: "(init bonus 2)",
            7: "(init bonus 3)",
            8: "(class info 0)",
            9: "(class info 1)",
            10: "(class info 2)",
            11: "(class info 3)",
            12: "(class info 4)",
            13: "(class info 5)",
            14: "V[111] atk_growth_coef",
            15: "V[112] secondary #1 base",
            16: "V[113] secondary #2 base",
            17: "V[114] secondary #3 base",
            18: "V[115] secondary #4 base",
            19: "V[116] secondary #5 base",
        }
        for idx in range(min(max_len, 25)):
            label = idx_label.get(idx, "")
            f.write(f"{idx:>3}  0x{idx*2:>4x}    ")
            for _, shorts in rows:
                v = shorts[idx] if idx < len(shorts) else None
                f.write(f"{str(v):>10s}  " if v is not None else f"{'--':>10s}  ")
            f.write(f" {label}\n")

        # 상세 분석
        f.write("\n")
        f.write("## V[112..116] 패턴 분석\n\n")
        f.write("(모든 값이 작거나 0 → secondary stat 단위는 raw point, 25/26 *10 multiplier 가\n")
        f.write(" calc_pl 공식에 있어 % rate 가 아닌 raw bonus point 단위로 봄)\n\n")
        for var_idx, (vlabel, hex_off) in enumerate([
            ("V[112]", 15), ("V[113]", 16), ("V[114]", 17), ("V[115]", 18), ("V[116]", 19),
        ]):
            f.write(f"{vlabel} (idx {hex_off}):\n")
            for n, shorts in rows:
                v = shorts[hex_off] if hex_off < len(shorts) else None
                f.write(f"  {n:>10s} = {v}\n")
            f.write("\n")

        # 추론
        f.write("## 추론 (5 클래스 RPG 직업 → secondary stat)\n\n")
        f.write("워리어 = 근접 탱커, 로그 = 도적/암살자, 건슬링어 = 원거리,\n")
        f.write("나이트 = 균형 탱커, 소서러 = 마법사 (모든 stat 1)\n\n")
        f.write("- V[112]: 워리어가 가장 큼 → 'block' or 'physical hit' or 'melee accuracy'\n")
        f.write("- V[113]: 건슬링어가 가장 큼 → 'long-range hit' or 'speed'\n")
        f.write("- V[114]: 워리어/로그 우세 → 'avoid' or 'crit'\n")
        f.write("- V[115]: 워리어 우세 + 작은 unit (5/3/2/4/1) → 'block rate' (% 단위)\n")
        f.write("- V[116]: 모두 0 (소서러만 1) → '마법 관련 stat' or 'magic resist'\n\n")
        f.write("정확 라벨은 status menu UI 함수 (drawStatus / DrawStatusFrame) 한글 string\n")
        f.write("매핑 RE 가 필요. 현재 추정 단계.\n")

    print(f"[+] {OUT}")
    # 콘솔 요약
    print()
    print("=== V[112..116] base values ===")
    print(f"{'class':>10s}  V[112]  V[113]  V[114]  V[115]  V[116]")
    for n, shorts in rows:
        vals = [shorts[i] if i < len(shorts) else None for i in (15, 16, 17, 18, 19)]
        print(f"{n:>10s}  " + "  ".join(f"{str(v):>6s}" for v in vals))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
