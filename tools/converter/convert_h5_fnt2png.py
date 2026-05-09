"""
Hero5 .fnt → PNG sprite sheet 변환기.

확정된 포맷:
  eng.fnt: HNF v1 magic + u8 width=8 + u8 height=11
           offset 6 부터 95 glyphs × 11 bytes (각 row 가 1 byte = 8 bits MSB first)
           total = 6 + 95×11 = 1051 ✓
  kor.fnt: HNF v0 magic + u8 width=16 + u8 height=11 + 25 bytes 메타
           offset 31 부터 581 glyphs × 22 bytes (각 row 가 2 bytes BE = 16 bits MSB first)
           total = 31 + 581×22 = 12813 ✓

table.dat: 2350 **Unicode** codepoints sorted (BE u16 array, range 0x8861-0xD3B7).
  - 0x8861-0x9FFF: Hanja (CJK Unified Ideographs subset)
  - 0xAC00-0xD3B7: Hangul Syllables subset
  EUC-KR 이 아니라 Unicode BMP 임 — 이전 가정 정정 (P5, 2026-05-09).
  581-glyph 매핑: type.dat (148B) 가 codepoint 분류, 정확한 lookup 은
  `_midas_funcFntInvalidate` 내부에 있음.

산출:
  apps/hero5-godot/assets/fonts/eng.png  (95 glyphs grid)
  apps/hero5-godot/assets/fonts/kor.png  (581 glyphs grid)
  apps/hero5-godot/assets/fonts/eucKR_index.json  (codepoint table)
"""
from __future__ import annotations
import pathlib, struct, csv, json
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print('PIL required'); raise

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT_DIR = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'fonts'


def find_file(name: str) -> pathlib.Path:
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['recovered_name'] == name:
                return ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"],16):08x}.bin'
    raise FileNotFoundError(name)


def render_glyph_sheet(fnt_data: bytes, header_size: int, glyph_count: int,
                       width: int, height: int, cols: int = 16) -> Image.Image:
    bytes_per_row = (width + 7) // 8
    glyph_bytes = bytes_per_row * height
    rows = (glyph_count + cols - 1) // cols
    sheet = Image.new('RGBA', (width * cols, height * rows), (0, 0, 0, 0))
    for g in range(glyph_count):
        gx = (g % cols) * width
        gy = (g // cols) * height
        gd_off = header_size + g * glyph_bytes
        for y in range(height):
            for x in range(width):
                byte_idx = y * bytes_per_row + x // 8
                bit = (fnt_data[gd_off + byte_idx] >> (7 - (x % 8))) & 1
                if bit:
                    sheet.putpixel((gx + x, gy + y), (255, 255, 255, 255))
    return sheet


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # eng.fnt
    eng = find_file('c/font/eng.fnt').read_bytes()
    eng_sheet = render_glyph_sheet(eng, 6, 95, 8, 11)
    eng_sheet.save(OUT_DIR / 'eng.png')
    print(f'eng.fnt → {OUT_DIR}/eng.png ({eng_sheet.size})')

    # kor.fnt
    kor = find_file('c/font/kor.fnt').read_bytes()
    kor_sheet = render_glyph_sheet(kor, 31, 581, 16, 11)
    kor_sheet.save(OUT_DIR / 'kor.png')
    print(f'kor.fnt → {OUT_DIR}/kor.png ({kor_sheet.size})')

    # table.dat → JSON of codepoints
    table = find_file('c/font/table.dat').read_bytes()
    cps = []
    for i in range(0, len(table), 2):
        cps.append(struct.unpack_from('>H', table, i)[0])
    # 분류: Hanja (CJK Unified, 0x4E00-0x9FFF) vs Hangul (0xAC00-0xD7AF)
    hanja = [c for c in cps if 0x4E00 <= c <= 0x9FFF]
    hangul = [c for c in cps if 0xAC00 <= c <= 0xD7AF]
    cps_data = {
        'note': ('2350 Unicode codepoints (sorted BE u16). Mix of CJK Hanja '
                 '(0x4E00-0x9FFF, 한자) and Hangul Syllables (0xAC00-0xD7AF). '
                 'NOT EUC-KR.'),
        'count': len(cps),
        'range': [f'0x{min(cps):04x}', f'0x{max(cps):04x}'],
        'hanja_count': len(hanja),
        'hangul_count': len(hangul),
        'codepoints_hex': [f'0x{c:04x}' for c in cps[:50]],
        'glyph_count': 581,
        'mapping_status': ('table.dat 의 2350 항목 → kor.fnt 의 581 글리프 매핑은 '
                           'type.dat (148B per-codepoint 분류) + native '
                           '_midas_funcFntInvalidate 내부 lookup 의존. '
                           '시스템 폰트(Noto Sans CJK KR) 우회로 게임 동작은 무관.'),
    }
    (OUT_DIR / 'eucKR_index.json').write_text(
        json.dumps(cps_data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'table.dat → {OUT_DIR}/eucKR_index.json ({len(cps)} codepoints)')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
