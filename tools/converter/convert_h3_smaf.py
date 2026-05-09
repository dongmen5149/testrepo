"""
Hero3 의 snd/_mf 파일 (Yamaha SMAF, magic 'MMMD') 헤더 분석 + 변환 가이드.

영웅서기3 의 33개 _mf 파일 (bgm0~18 + sd000~013) 모두 SMAF 포맷.
순수 Python 변환은 매우 복잡 (FM 합성 시뮬레이션 필요) - 외부 변환기 의존.

권장 워크플로 (2026-05-10 조사 갱신):
  1. smaf-converter (Java JAR, https://github.com/antanas-vasiliauskas/smaf-converter)
     `java -jar smaf-converter.jar input.mmf output.mid`
     - JRE 만 있으면 사전 빌드 JAR 다운로드해서 즉시 사용 가능
     - vavi-sound 기반 (au/Softbank YAMAHA 링톤). SKT GVM 호환은 직접 테스트 필요
  2. TiMidity++ (Windows 바이너리, https://sourceforge.net/projects/timidity/)
     + SF2 soundfont (예: OmegaGMGS2.sf2) 로 .mid + soundfont -> .wav
  3. FFmpeg (winget install Gyan.FFmpeg) 로 .wav -> .ogg

대체 옵션 (이전 후보 모두 불가 확인):
  - smaf2midi (Wohlstand) -> GitHub 404 (소멸)
  - vgmstream -> SMAF/MMF/MMMD 미지원
  - Pure Python -> FM 합성 시뮬레이션 필요, 비현실적

이 스크립트는 SMAF 파일 헤더만 분석해서 변환 가능성을 리포트.
실제 변환 미구현 - 외부 도구 설치 후 별도 진행.

사용:
  python tools/converter/convert_h3_smaf.py
"""
from __future__ import annotations
import pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SND = ROOT / 'work' / 'h3' / 'extracted' / 'snd'
OUT = ROOT / 'work' / 'h3' / 'analysis' / 'smaf_summary.txt'


def parse_smaf_header(data: bytes) -> dict | None:
    if data[:4] != b'MMMD':
        return None
    chunk_size = struct.unpack_from('>I', data, 4)[0]
    return {
        'magic': 'MMMD',
        'chunk_size': chunk_size,
        'first_chunk': data[8:16].hex() if len(data) >= 16 else '',
        'total_size': len(data),
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(SND.glob('*_mf'))
    out = [f'Hero3 SMAF (snd/_mf) 분석 - {len(files)} 파일\n']
    out.append('* SMAF (Synthetic music Mobile Application Format) = Yamaha 포맷')
    out.append('* 순수 Python 디코드 비현실적 (FM 합성 시뮬레이션 필요)')
    out.append('* 권장 (2026-05-10 갱신): smaf-converter (Java JAR) -> MID')
    out.append('  -> TiMidity++ + SF2 soundfont -> WAV -> ffmpeg -> OGG')
    out.append('* smaf2midi (Wohlstand) 는 GitHub 404 (소멸). vgmstream 은 SMAF 미지원\n')

    bgm_count = sum(1 for p in files if p.name.startswith('bgm'))
    sfx_count = sum(1 for p in files if p.name.startswith('sd'))
    out.append(f'분류: BGM {bgm_count}개, SFX {sfx_count}개\n')

    out.append('전체 파일 헤더:')
    total_bytes = 0
    valid = 0
    for p in files:
        d = p.read_bytes()
        info = parse_smaf_header(d)
        if info:
            valid += 1
            total_bytes += len(d)
            out.append(f'  {p.name:12s}  size={len(d):6d}  chunk_size={info["chunk_size"]:6d}  '
                       f'first_chunk={info["first_chunk"]}')
        else:
            out.append(f'  {p.name:12s}  (NOT SMAF - magic={d[:4]!r})')

    out.append(f'\n검증: {valid}/{len(files)} SMAF 포맷 확인. 총 {total_bytes:,} 바이트.')
    out.append('\n=== 다음 단계 (사용자 작업) ===')
    out.append('1. smaf-converter JAR 다운로드:')
    out.append('   https://github.com/antanas-vasiliauskas/smaf-converter/releases')
    out.append('   (Java JRE 21 권장)')
    out.append('2. 일괄 SMAF -> MIDI 변환 (PowerShell):')
    out.append('   Get-ChildItem work\\h3\\extracted\\snd\\*_mf | ForEach-Object {')
    out.append('     java -jar smaf-converter.jar $_.FullName "$($_.BaseName).mid"')
    out.append('   }')
    out.append('3. TiMidity++ + SF2 soundfont 로 MIDI -> WAV')
    out.append('   timidity *.mid -Ow -o output.wav')
    out.append('4. ffmpeg 로 WAV -> OGG')
    out.append('   ffmpeg -i input.wav -c:a libvorbis -q:a 4 output.ogg')
    out.append('5. Android assets/sounds/ 에 배포')
    out.append('\n검증 권장: bgm0_mf 1개로 먼저 시범 변환 후 음질/호환성 확인')

    OUT.write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
