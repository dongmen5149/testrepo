"""
Hero3 _scn (event script) → JSON.

부분 분석:
    - 4-byte 헤더 + 가변 byte-code 스크립트 + 임베디드 EUC-KR 텍스트
    - 0xff 가 빈번한 separator/opcode terminator
    - 정확한 opcode mapping 은 Ghidra 분석 필요 (보류)

이 변환기는:
    - 헤더 4 byte 보존
    - EUC-KR 한국어 대사 추출 (≥ 3 char)
    - byte stream 16-bit hex preview

i18n 용도로 모든 대사를 한 곳에 모아 JSON 으로 export.

사용:
    python convert_scn.py <input.scn> <output.json>
"""
from __future__ import annotations
import sys, json, pathlib


def extract_euckr_strings(data: bytes, min_chars: int = 2) -> list[dict]:
    """EUC-KR 한글 시퀀스 추출 (offset, text)."""
    out = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            j = i
            while j < len(data) - 1 and 0xa1 <= data[j] <= 0xfe and 0xa1 <= data[j+1] <= 0xfe:
                j += 2
            chars = (j - i) // 2
            if chars >= min_chars:
                try:
                    s = data[i:j].decode('euc-kr')
                    out.append({'offset': i, 'text': s, 'char_count': chars})
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    return out


def parse_scn(data: bytes) -> dict:
    return {
        'size': len(data),
        'header_4_hex': data[:4].hex(),
        'dialogue': extract_euckr_strings(data),
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src = pathlib.Path(argv[1])
    dst = pathlib.Path(argv[2])
    info = parse_scn(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({len(info["dialogue"])} dialogues)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
