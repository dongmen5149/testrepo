"""binary base address 자동 추정.

전제: 'frameBuf is NULL' 같은 known 문자열은 file offset 0xa61c8 에 있음.
바이너리 코드 안에 이 문자열을 가리키는 literal 포인터가 있을 것.
포인터 = BASE + 0xa61c8.

여러 후보 BASE 를 시도해 매칭 횟수가 최대인 값을 채택.
"""
from __future__ import annotations
import struct, pathlib, collections

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

_g = select()
BIN = _g.binary_path
assert BIN is not None, f'{_g.id} has no native binary'

# 다중 known offset 으로 base 후보 검증
TARGETS = [
    0x0a61c8,  # frameBuf is NULL
    0x0a5d94,  # /hero/h00000_bm
    0x0a5db4,  # /boss/boss9000_bm
    0x0a8c28,  # /enemy/e1000_bm
    0x0aac6c,  # /map/map0_mp
    0x0a7f88,  # /font/table
    0x0a6888,  # onEventMessageOkKey()
    0x0a8c18,  # /enemy/e000_cif
]


def main():
    data = BIN.read_bytes()
    print(f'Loaded: {len(data)} bytes (0x{len(data):x})')

    # 모든 4-byte aligned 32-bit 값 수집 (코드 영역 후보)
    code_end = 0x0a5000
    values = []
    for off in range(0, min(code_end, len(data) - 4), 4):
        v = struct.unpack_from('<I', data, off)[0]
        values.append(v)
    print(f'Collected {len(values)} 32-bit aligned words from code region')

    # 각 후보 BASE 에 대해 (BASE + target) 가 코드 안에 몇 번 출현하는지
    val_set = set(values)
    base_hits: dict[int, int] = collections.defaultdict(int)

    # base 후보 = 각 값 - 각 target. 빈도 기반 ranking.
    for v in values:
        for t in TARGETS:
            candidate_base = v - t
            if candidate_base >= 0:
                base_hits[candidate_base] += 1

    # 동시에 여러 target 이 매칭되는 base 를 우선
    print(f'\nTop 10 candidate base addresses (by match count across all targets):')
    for base, count in sorted(base_hits.items(), key=lambda x: -x[1])[:10]:
        # 실제로 몇 개 target 이 매칭되는지 검증
        matched = []
        for t in TARGETS:
            if (base + t) in val_set:
                matched.append(t)
        print(f'  BASE = 0x{base:08x}  count={count}  matched_targets={[hex(t) for t in matched]}')


if __name__ == '__main__':
    main()
