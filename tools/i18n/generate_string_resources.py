"""
InGame_txt.json + translation_dict 를 결합하여
Android values/strings.xml (한국어, 베이스) 와 values-en/strings.xml (영어) 생성.

각 InGame_txt 인덱스 N → R.string.txt_N 으로 매핑.
인덱스 N이 한국어이고 사전에 없으면 영어판은 한국어 그대로 (TODO 마커).

사용:
    python generate_string_resources.py
"""
from __future__ import annotations
import json, pathlib, sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).parent.parent.parent
INGAME = ROOT / 'work' / 'converted' / 'dat' / 'InGame_txt.json'
TITLE = ROOT / 'work' / 'converted' / 'menu' / 'title_txt.json'
MENU = ROOT / 'work' / 'converted' / 'menu' / 'menu_txt.json'
RES_KO = ROOT / 'android' / 'app' / 'src' / 'main' / 'res' / 'values-ko' / 'strings.xml'
RES_EN = ROOT / 'android' / 'app' / 'src' / 'main' / 'res' / 'values' / 'strings.xml'

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from translation_dict import all_translations

TRANS = all_translations()


def xml_escape(s: str) -> str:
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace("'", '\\\'')
             .replace('"', '&quot;'))


def write_strings_xml(path: pathlib.Path, entries: list[tuple[str, str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<resources>\n')
        for key, value in entries:
            f.write(f'    <string name="{key}">{xml_escape(value)}</string>\n')
        f.write('</resources>\n')


def main():
    if not INGAME.exists():
        print(f'MISSING: {INGAME}', file=sys.stderr)
        return 1
    ko_strings = json.loads(INGAME.read_text(encoding='utf-8'))
    print(f'InGame_txt: {len(ko_strings)} strings')

    ko_entries = [('app_name', '영웅서기3 리메이크')]
    en_entries = [('app_name', 'Hero3 Remake')]

    # 추가 UI keys
    ko_entries += [
        ('press_start', '시작하려면 누르세요'),
        ('main_title', '영웅서기3'),
        ('main_subtitle', '운명의 수레바퀴'),
        ('press_pound_to_switch', '# 키로 화면 전환'),
        ('scene_sprite_gallery', '스프라이트 갤러리'),
        ('scene_map_gallery', '맵 갤러리'),
        ('scene_main_menu', '메인 메뉴'),
        ('scene_dialogue_demo', '대화 데모'),
        ('hint_dpad_navigate', '◀▶▲▼ 이동'),
        ('hint_ok_select', 'OK 선택'),
        ('hint_back_cancel', 'R 취소'),
        ('settings_language', '언어'),
        ('settings_quality', '화질'),
        ('settings_quality_sd', '표준'),
        ('settings_quality_hd', 'HD (4×)'),
        ('settings_save', '저장'),
        ('language_korean', '한국어'),
        ('language_english', 'English'),
        ('menu_new_game', '새 게임'),
        ('menu_continue', '이어하기'),
        ('menu_settings', '환경설정'),
        ('menu_gallery', '자산 갤러리'),
    ]
    en_entries += [
        ('press_start', 'Press any key to start'),
        ('main_title', 'Hero3'),
        ('main_subtitle', 'Wheel of Destiny'),
        ('press_pound_to_switch', 'Press # to switch screens'),
        ('scene_sprite_gallery', 'Sprite Gallery'),
        ('scene_map_gallery', 'Map Gallery'),
        ('scene_main_menu', 'Main Menu'),
        ('scene_dialogue_demo', 'Dialogue Demo'),
        ('hint_dpad_navigate', '<>^v Navigate'),
        ('hint_ok_select', 'OK Select'),
        ('hint_back_cancel', 'R Back'),
        ('settings_language', 'Language'),
        ('settings_quality', 'Quality'),
        ('settings_quality_sd', 'Standard'),
        ('settings_quality_hd', 'HD (4×)'),
        ('settings_save', 'Save'),
        ('language_korean', '한국어'),
        ('language_english', 'English'),
        ('menu_new_game', 'New Game'),
        ('menu_continue', 'Continue'),
        ('menu_settings', 'Settings'),
        ('menu_gallery', 'Asset Gallery'),
    ]

    # InGame_txt 196개를 txt_NNN 키로 export
    untranslated = 0
    for i, ko in enumerate(ko_strings):
        key = f'txt_{i:03d}'
        ko_entries.append((key, ko))
        en = TRANS.get(ko, ko)
        if en == ko and any(0xac00 <= ord(c) <= 0xd7af for c in ko):
            untranslated += 1
        en_entries.append((key, en))

    write_strings_xml(RES_KO, ko_entries)
    write_strings_xml(RES_EN, en_entries)

    print(f'Wrote {RES_KO}')
    print(f'Wrote {RES_EN}')
    print(f'Untranslated Korean entries (still 한글 in EN): {untranslated} / {len(ko_strings)}')
    print(f'Coverage: {(len(ko_strings) - untranslated) / len(ko_strings) * 100:.0f}%')


if __name__ == '__main__':
    sys.exit(main() or 0)
