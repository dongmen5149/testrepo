"""client.bin64000 / client.bin387872 에서 ASCII/EUC-KR 문자열 추출.
파일 I/O 시그니처, 에러 메시지, 디버그 라벨 등이 보이면 함수 식별의 단서.

CLI:
    python tools/recon/extract_strings.py            # stdout 보고
    python tools/recon/extract_strings.py --json OUT # path-like + 라벨을 JSON 으로 dump
                                                     # (recon TARGETS 자동 생성용)
    HERO_GAME=h4 python tools/recon/extract_strings.py --json work/h4/converted/string_offsets.json
"""
from __future__ import annotations
import argparse, json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402


def is_printable(b: int) -> bool:
    return 0x20 <= b < 0x7f


def find_ascii_strings(data: bytes, min_len: int = 4) -> list[tuple[int, str]]:
    out = []
    i = 0
    while i < len(data):
        if is_printable(data[i]):
            j = i
            while j < len(data) and is_printable(data[j]):
                j += 1
            if j - i >= min_len:
                out.append((i, data[i:j].decode('ascii', errors='replace')))
            i = j
        else:
            i += 1
    return out


def find_euckr_strings(data: bytes, min_chars: int = 3) -> list[tuple[int, str]]:
    """EUC-KR 한글 시퀀스 탐지: 0xA1-0xFE 첫 바이트 + 0xA1-0xFE 두번째."""
    out = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i + 1] <= 0xfe:
            j = i
            chars = 0
            while j < len(data) - 1 and 0xa1 <= data[j] <= 0xfe and 0xa1 <= data[j + 1] <= 0xfe:
                j += 2
                chars += 1
            if chars >= min_chars:
                try:
                    s = data[i:j].decode('euc-kr')
                    out.append((i, s))
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    return out


# JSON dump 시 포함할 디버그 라벨 키워드 (대소문자 무시).
# 'frameBuf is NULL', 'Font data not loaded', 'Palette Index Not Found' 등.
LABEL_KEYWORDS = (
    'null', 'error', 'not found', 'not loaded', 'failed',
    'onevent', 'eventidx',
)


def is_path_like(s: str) -> bool:
    """`/hero/h00000_bm`, `/H4/PAL/_H_%03d_PAL` 같은 자산 경로 패턴."""
    if not s.startswith('/'):
        return False
    # 최소 두 segment + 길이 5+ (너무 짧은 / 패턴 노이즈 제거)
    return s.count('/') >= 2 and len(s) >= 5


def collect_targets(ascii_strs: list[tuple[int, str]]) -> dict[int, str]:
    """recon TARGETS 후보: path-like + 라벨."""
    out: dict[int, str] = {}
    for off, s in ascii_strs:
        if is_path_like(s):
            out[off] = s
            continue
        ls = s.lower()
        if any(kw in ls for kw in LABEL_KEYWORDS):
            out[off] = s
    return out


def estimate_code_end(ascii_strs: list[tuple[int, str]]) -> int:
    """asset path string 의 최소 offset 을 code/data 경계로 추정.
    `/H4/...`, `/MAP/...`, `/hero/...` 같은 path-like 가 시작되는 곳이 ROdata 구역."""
    paths = [o for o, s in ascii_strs if is_path_like(s)]
    if not paths:
        return 0
    # 4KB align (보수적으로 한 페이지 앞)
    return (min(paths) // 0x1000) * 0x1000


def dump_json(out_path: pathlib.Path, data: bytes, ascii_strs: list[tuple[int, str]], game_id: str, bin_name: str) -> None:
    targets = collect_targets(ascii_strs)
    payload = {
        'game': game_id,
        'binary': bin_name,
        'binary_size': len(data),
        'code_end_estimate': estimate_code_end(ascii_strs),
        # 16진 키로 dump (사람이 읽기 편하게). JSON 표준은 string key 라 hex 그대로.
        'targets': {f'0x{o:08x}': s for o, s in sorted(targets.items())},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\n[dump] {len(targets)} targets -> {out_path}')
    print(f'[dump] code_end_estimate = {payload["code_end_estimate"]:#x}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', dest='json_out', help='path-like + 라벨 offsets 을 JSON 으로 dump')
    ap.add_argument('--game', help="게임 id (h3/h4/h5). 미지정시 HERO_GAME 환경변수")
    ap.add_argument('--quiet', action='store_true', help='보고 출력 생략 (JSON dump 모드용)')
    args = ap.parse_args()

    _g = select(args.game)
    BIN = _g.binary_path
    assert BIN is not None, f'{_g.id} has no native binary'

    data = BIN.read_bytes()
    print(f'Loaded {BIN.name}: {len(data)} bytes')

    ascii_strs = find_ascii_strings(data)
    if not args.quiet:
        print(f'\n=== ASCII strings (>=4 chars): {len(ascii_strs)} ===')
        # 파일 경로/확장자 패턴 우선
        interesting_keywords = ('boss', 'enemy', 'hero', 'npc', 'map', 'menu', 'comm', 'snd', 'event',
                                'logo', 'skill', 'fgi', 'font', '.bm', '.cif', '.pa', '.mp', '.dat',
                                '.scn', '.txt', '.mf', '_bm', '_cif', '_pa', '_mp', '_dat',
                                'open', 'read', 'load', 'draw', 'render', 'sprite', 'frame', 'palette')
        print('\n  -- file/loader related --')
        for off, s in ascii_strs:
            ls = s.lower()
            if any(k in ls for k in interesting_keywords):
                print(f'  {off:#08x}: {s!r}')

        print('\n  -- top 50 longest --')
        for off, s in sorted(ascii_strs, key=lambda x: -len(x[1]))[:50]:
            print(f'  {off:#08x}: {s!r}')

        eu = find_euckr_strings(data)
        print(f'\n=== EUC-KR strings (>=3 chars): {len(eu)} ===')
        for off, s in eu[:30]:
            print(f'  {off:#08x}: {s!r}')

    if args.json_out:
        dump_json(pathlib.Path(args.json_out), data, ascii_strs, _g.id, BIN.name)
