"""한 _scn 파일의 구조 덤프 — 화자 태그 + 텍스트 + opcode 영역 분리.

사용:
    python dump_scn_structure.py [filename]
        filename 미지정 시 e0000_scn 사용.
"""
from __future__ import annotations
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'


def is_kr_lead(b: int) -> bool: return 0xa1 <= b <= 0xfe


def hexbytes(data: bytes) -> str:
    return ' '.join(f'{b:02x}' for b in data)


def main(argv):
    name = argv[1] if len(argv) > 1 else 'e0000_scn'
    path = SCN / name
    if not path.exists():
        print(f'  ERROR: {path} not found'); return 1
    data = path.read_bytes()
    print(f'=== {name}  {len(data)} bytes ===\n')

    i = 0
    while i < len(data):
        # 화자 태그 [...]
        if data[i] == 0x5b:
            end = data.find(b']', i + 1)
            if end > 0 and end - i < 32:
                speaker = data[i+1:end].decode('euc-kr', errors='replace')
                print(f'  [{i:#06x}] SPEAKER  [{speaker}]')
                i = end + 1
                continue
        # 한국어 텍스트 런
        if i + 1 < len(data) and is_kr_lead(data[i]) and is_kr_lead(data[i+1]):
            start = i
            while i + 1 < len(data) and is_kr_lead(data[i]) and is_kr_lead(data[i+1]):
                i += 2
            text = data[start:i].decode('euc-kr', errors='replace')
            print(f'  [{start:#06x}] TEXT     {text!r}')
            continue
        # 그 외: opcode 영역 — 다음 [ 또는 한국어까지 범위 dump
        opc_start = i
        while i < len(data):
            if data[i] == 0x5b: break
            if i + 1 < len(data) and is_kr_lead(data[i]) and is_kr_lead(data[i+1]): break
            i += 1
            if i - opc_start >= 32: break
        opc = data[opc_start:i]
        if opc:
            print(f'  [{opc_start:#06x}] OPCODES  {hexbytes(opc)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
