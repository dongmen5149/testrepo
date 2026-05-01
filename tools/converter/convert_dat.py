"""
dat/*_dat 파일에서 추출 가능한 정보를 JSON 으로 변환.

대부분 dat 파일은 가변 record 구조 (rec_size + flag + name_len + EUC-KR name + payload).
정확한 payload 의미는 미확정이지만 EUC-KR 한글 시퀀스를 모두 추출해 의미 있는 라벨 생성.

사용:
    python convert_dat.py <input.dat> <output.json>
"""
from __future__ import annotations
import json, sys, pathlib


def extract_strings(data: bytes, min_chars: int = 2) -> list[dict]:
    """EUC-KR 한글 시퀀스 추출 (offset, text)."""
    out = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i + 1] <= 0xfe:
            j = i
            while j < len(data) - 1 and 0xa1 <= data[j] <= 0xfe and 0xa1 <= data[j+1] <= 0xfe:
                j += 2
            chars = (j - i) // 2
            if chars >= min_chars:
                try:
                    out.append({'offset': i, 'text': data[i:j].decode('euc-kr')})
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    return out


def parse_dat(data: bytes) -> dict:
    return {
        'size': len(data),
        'header_8_hex': data[:8].hex() if len(data) >= 8 else data.hex(),
        'korean_strings': extract_strings(data),
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    info = parse_dat(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({len(info["korean_strings"])} strings)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
