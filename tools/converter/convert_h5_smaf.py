"""
SMAF (Yamaha Synthetic music Mobile Application Format, magic 'MMMD') → OGG/WAV.

Hero5 의 c/snd/bgm_NN.mmf 와 c/snd/eff_NN.mmf 가 SMAF 포맷.
순수 Python 변환은 매우 복잡 (FM 합성 시뮬레이션 필요) — 외부 변환기 의존.

권장 워크플로:
  1. smafconv (https://github.com/Wohlstand/smaf2midi) 또는 smaf2mid 로 .smaf → .mid
  2. timidity 또는 fluidsynth 로 .mid + soundfont → .wav
  3. ffmpeg 로 .wav → .ogg

또는 합성 음원 무시하고 OGG 만 사용 (OGG 42개로 BGM/SFX 충분).

이 스크립트는 SMAF 파일 헤더만 분석해서 변환 가능성을 리포트.
실제 변환 미구현.
"""
from __future__ import annotations
import pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'smaf_summary.txt'


def parse_smaf_header(data: bytes) -> dict | None:
    if data[:4] != b'MMMD':
        return None
    # SMAF header: 'MMMD' + u32 BE chunk size + content
    # First chunk after MMMD is typically 'CNTI' (Content Info)
    chunk_size = struct.unpack_from('>I', data, 4)[0]
    return {
        'magic': 'MMMD',
        'chunk_size': chunk_size,
        'first_chunk': data[8:16].hex() if len(data) >= 16 else '',
        'total_size': len(data),
    }


def main() -> int:
    files = sorted(ENTRIES.glob('*.smaf'))
    out = [f'SMAF files: {len(files)}\n']
    out.append(f'\n* SMAF (Synthetic music Mobile Application Format) is a Yamaha format.')
    out.append(f'* Pure-Python decode is impractical (FM synthesis required).')
    out.append(f'* Recommended: use external smaf2mid + timidity + ffmpeg pipeline.')
    out.append(f'* Or rely on the 42 OGG sounds already imported.\n')
    out.append(f'\nFile list (showing first 10):')
    for p in files[:10]:
        d = p.read_bytes()
        info = parse_smaf_header(d)
        if info:
            out.append(f'  {p.name}  size={len(d)}  chunk_size={info["chunk_size"]}  '
                       f'first_chunk={info["first_chunk"]}')
        else:
            out.append(f'  {p.name}  (not SMAF?)')
    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
