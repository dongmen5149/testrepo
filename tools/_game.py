"""게임별 설정 (path/binary name) 중앙 관리.

사용:
    from _game import select
    g = select()                # HERO_GAME 환경변수 또는 default 'h3'
    g = select('h4')            # 명시
    BIN = g.binary_path
    OUT = g.converted_root / 'asset_catalog.json'

신규 게임 추가 시 GAMES dict 에만 항목 추가.
"""
from __future__ import annotations
import os, pathlib
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Game:
    id: str
    name: str
    src_dir: pathlib.Path           # 원본 JAR/APK 폴더 (수정 금지)
    archive_path: pathlib.Path      # 원본 아카이브 파일
    binary_name: str | None         # 네이티브 client 바이너리명 (있으면)
    work_root: pathlib.Path
    android_module: str             # apps/<module>/

    @property
    def extracted_root(self) -> pathlib.Path:
        return self.work_root / 'extracted'

    @property
    def converted_root(self) -> pathlib.Path:
        return self.work_root / 'converted'

    @property
    def converted_hd_root(self) -> pathlib.Path:
        return self.work_root / 'converted_hd'

    @property
    def binary_path(self) -> pathlib.Path | None:
        if self.binary_name is None:
            return None
        return self.extracted_root / self.binary_name

    @property
    def android_assets_root(self) -> pathlib.Path:
        return ROOT / 'apps' / self.android_module / 'app' / 'src' / 'main' / 'assets'


GAMES: dict[str, Game] = {
    'h3': Game(
        id='h3',
        name='영웅서기3 - 운명의수레바퀴',
        src_dir=ROOT / 'Hero3',
        archive_path=ROOT / 'Hero3' / '0103EFD4.jar',
        binary_name='client.bin64000',
        work_root=ROOT / 'work' / 'h3',
        android_module='hero3-android',
    ),
    'h4': Game(
        id='h4',
        name='영웅서기4 - 환영의검',
        src_dir=ROOT / 'Hero4',
        archive_path=ROOT / 'Hero4' / '010100D4.jar',
        binary_name='client.bin387872',
        work_root=ROOT / 'work' / 'h4',
        android_module='hero4-android',
    ),
    'h5': Game(
        id='h5',
        name='영웅서기5',
        src_dir=ROOT / 'Hero5',
        archive_path=ROOT / 'Hero5' / '영웅서기5(최신폰전용).apk',
        binary_name='lib/armeabi/libHeroesLore5.so',
        work_root=ROOT / 'work' / 'h5',
        android_module='hero5-android',
    ),
}


def select(game_id: str | None = None) -> Game:
    """게임 선택. 우선순위: 인자 > HERO_GAME 환경변수 > 'h3' default."""
    gid = game_id or os.environ.get('HERO_GAME', 'h3')
    if gid not in GAMES:
        raise ValueError(f'Unknown game id: {gid!r}. Choose from {list(GAMES)}')
    return GAMES[gid]
