"""
Hero4 _EXD 파서 (캐릭터 확장 데이터, 117개).

부분 해독:
- 8 byte header: [count][00][01][00][01][b5][00][00]
  - byte 0 = count (frame? entry?), 1~35 분포
  - byte 5 = 1/2/3 (subtype, 대부분 3)
- 그 이후 payload = entry table (정확한 layout 은 Ghidra 분석 후)

지금은 헤더 추출 + payload hex 보존만.
"""
from __future__ import annotations
import json, sys, pathlib


def parse_exd(data: bytes) -> dict:
    if len(data) < 8:
        raise ValueError('file too short')
    return {
        'count': data[0],
        'header': data[:8].hex(),
        'subtype': data[5],
        'payload_size': len(data) - 8,
        'payload_first_64': data[8:72].hex() if len(data) > 8 else '',
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    info = parse_exd(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
