"""
translation_dict 단위 테스트.

실행:
    python -m unittest tools.i18n.test_translation_dict
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from translation_dict import (
    CHARACTERS_H3, PLACES_H3, UI_VOCAB, COMMON_WORDS,
    CHARACTERS, PLACES,
    for_game, all_translations,
)


class TestForGame(unittest.TestCase):
    def test_h3_bundle(self):
        b = for_game('h3')
        self.assertEqual(set(b.keys()), {'characters', 'places', 'ui_vocab', 'common_words'})
        self.assertIs(b['characters'], CHARACTERS_H3)
        self.assertIs(b['places'], PLACES_H3)
        self.assertIs(b['ui_vocab'], UI_VOCAB)

    def test_h4_bundle(self):
        b = for_game('h4')
        self.assertEqual(set(b.keys()), {'characters', 'places', 'ui_vocab', 'common_words'})
        # UI_VOCAB shared across games (Hanbit engine)
        self.assertIs(b['ui_vocab'], UI_VOCAB)

    def test_unknown_game_raises(self):
        with self.assertRaises(ValueError):
            for_game('h99')


class TestAllTranslations(unittest.TestCase):
    def test_default_is_h3(self):
        out = all_translations()
        # CHARACTERS_H3 keys must be subset
        for k in CHARACTERS_H3:
            self.assertIn(k, out)
        for k in PLACES_H3:
            self.assertIn(k, out)

    def test_h3_includes_kei_and_neosoltia(self):
        out = all_translations('h3')
        self.assertEqual(out['케이'], 'Kei')
        self.assertEqual(out['NEOSOLTIA'], 'Neo Soltia')

    def test_aliases_match_h3(self):
        # CHARACTERS / PLACES alias should equal _H3 versions (downstream compat)
        self.assertIs(CHARACTERS, CHARACTERS_H3)
        self.assertIs(PLACES, PLACES_H3)

    def test_h4_does_not_have_h3_chars(self):
        # Hero4 corpus 미해독 → CHARACTERS_H4 비어있음. Hero3 캐릭터 가 H4 결과 에 포함되면 안 됨.
        h4_out = all_translations('h4')
        # CHARACTERS_H4 가 비어있다는 가정 — UI/COMMON 어휘는 공통이지만 캐릭터는 별도
        self.assertNotIn('케이', h4_out, 'Hero3 character leaked into Hero4')


class TestDictIntegrity(unittest.TestCase):
    def test_no_empty_translations(self):
        """모든 사전 값 이 비어있지 않은 string 인지."""
        for name, d in [('CHARACTERS_H3', CHARACTERS_H3), ('PLACES_H3', PLACES_H3),
                        ('UI_VOCAB', UI_VOCAB), ('COMMON_WORDS', COMMON_WORDS)]:
            for k, v in d.items():
                self.assertIsInstance(v, str, f'{name}[{k!r}] not str')
                self.assertGreater(len(v), 0, f'{name}[{k!r}] empty')

    def test_h3_character_count_minimum(self):
        # PROGRESS.md 캐릭터 빈도 분포: 케이/리츠/일레느/시엔/레아/엘지스/케네스/이안/멜페토 9 핵심
        self.assertGreaterEqual(len(CHARACTERS_H3), 9)


if __name__ == '__main__':
    unittest.main()
