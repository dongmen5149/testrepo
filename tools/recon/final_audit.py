"""Hero4 자동 영역 종결 검증 — 매우 꼼꼼한 점검."""
import pathlib, json
from collections import Counter, defaultdict

ROOT = pathlib.Path('work/h4/extracted')
CONV = pathlib.Path('work/h4/converted')
ASSETS = pathlib.Path('apps/hero4-android/app/src/main/assets')

print('='*70)
print('Hero4 자동 영역 종결 검증')
print('='*70)

# 모든 디렉토리 + 파일 카운트
all_files = [f for f in ROOT.rglob('*') if f.is_file()]
by_dir = defaultdict(list)
for f in all_files:
    parent = str(f.parent.relative_to(ROOT)).replace('\\', '/')
    by_dir[parent].append(f)

print(f'\n총 디렉토리: {len(by_dir)}, 총 파일: {len(all_files)}\n')
print(f'{"Directory":<30} {"Files":>6} {"Bytes":>10}')
for d in sorted(by_dir.keys()):
    files = by_dir[d]
    total_bytes = sum(f.stat().st_size for f in files)
    print(f'  {d:<28} {len(files):>6} {total_bytes:>10}')

# 산출물 인벤토리
print('\n## work/h4/converted/ 산출물:')
conv_files = list(CONV.glob('*.json')) + list(CONV.glob('*.txt'))
for f in sorted(conv_files):
    print(f'  {f.name} ({f.stat().st_size}B)')

# Hero4 전용 도구
TOOLS = pathlib.Path('tools')
print('\n## Hero4 전용 도구:')
h4_tools = list(TOOLS.rglob('*h4*.py'))
for t in sorted(h4_tools):
    print(f'  {t.relative_to(TOOLS)}')

# 각 미점검 디렉토리 점검
print('\n## 미분석 가능성 있는 디렉토리들:')
for d in ['CM', 'H4/000', 'H4/001', 'H4/002', 'H4/003', 'H4/004', 'H4/005',
          'H4/006', 'H4/007', 'l', 'META-INF', 'MAP/EFFECT', 'tdf']:
    p = ROOT / d
    if p.exists() and p.is_dir():
        files = list(p.iterdir())
        if files:
            total = sum(f.stat().st_size for f in files if f.is_file())
            print(f'\n  {d}/ ({len(files)} files, {total}B):')
            for f in files[:8]:
                if f.is_file():
                    d_bytes = f.read_bytes()[:16]
                    print(f'    {f.name:30} {f.stat().st_size:6}B  {d_bytes.hex()}')
            if len(files) > 8:
                print(f'    ... +{len(files)-8} more')

# __adf__, __class__ 단일 파일
for spec in ['__adf__', '__class__']:
    p = ROOT / spec
    if p.exists() and p.is_file():
        d = p.read_bytes()
        print(f'\n  {spec} ({len(d)}B): {d[:120]!r}')

# E/ 전체
print(f'\n## E/ 전체 파일 (총 {len(list((ROOT/"E").iterdir()))} files):')
for f in sorted((ROOT/'E').iterdir()):
    if f.is_file():
        d = f.read_bytes()[:12]
        print(f'  {f.name:20} {f.stat().st_size:6}B  {d.hex()}')

# NPC/ 전체
print(f'\n## NPC/ 전체 파일 (총 {len(list((ROOT/"NPC").iterdir()))} files):')
for f in sorted((ROOT/'NPC').iterdir()):
    if f.is_file():
        d = f.read_bytes()[:12]
        print(f'  {f.name:30} {f.stat().st_size:6}B  {d.hex()}')

# ITM/ 전체
print(f'\n## ITM/ 전체 파일:')
for f in sorted((ROOT/'ITM').iterdir()):
    if f.is_file():
        d = f.read_bytes()[:12]
        print(f'  {f.name:20} {f.stat().st_size:6}B  {d.hex()}')
    elif f.is_dir():
        sub = list(f.iterdir())
        print(f'  {f.name}/ ({len(sub)} files)')

# tdf/ 검사
tdf = ROOT / 'tdf'
if tdf.exists():
    print(f'\n## tdf/ 상세 ({len(list(tdf.iterdir()))} files):')
    for f in sorted(tdf.iterdir())[:20]:
        if f.is_file():
            d = f.read_bytes()[:32]
            print(f'  {f.name:20} {f.stat().st_size:6}B  {d.hex()}')

# FR/, FT/ 분석 도구 존재 확인
print('\n## FR/ + FT/ + GMenu/ + CM/ 도구 작성 상태:')
for kw in ['fr', 'ft', 'font', 'gmenu', 'cm_', 'tdf']:
    matches = list(TOOLS.rglob(f'*{kw}*.py'))
    if matches:
        print(f'  "{kw}": {[str(m.relative_to(TOOLS)) for m in matches]}')
    else:
        print(f'  "{kw}": NONE')
