import re
import unittest

from addon.constants import (
    CARD_TEMPLATE_CSS,
    DICT2ANKI_CARD_TEMPLATE_NAME,
    DICT2ANKI_CSS,
    LISTENING_CARD_TEMPLATE_NAME,
    LISTENING_CSS,
    MODEL_NAMES,
    dict2anki_card_template_afmt,
    dict2anki_card_template_qfmt,
    listening_card_template_afmt,
    listening_card_template_qfmt,
)


SOUND_PATTERN = re.compile(r'\[sound:')
BR_EP_AUDIO_PATTERN = re.compile(r'src="\{\{BrEPron\}\}"')
AM_EP_AUDIO_PATTERN = re.compile(r'src="\{\{AmEPron\}\}"')


class HardcodedTemplatesTests(unittest.TestCase):
    """Pin the shape of the hardcoded card templates so future tweaks stay aligned
    with the user-provided Dict2Anki / Dict2Anki-Listening layouts."""

    def test_model_names(self):
        self.assertEqual(MODEL_NAMES, ['Dict2Anki', 'Dict2Anki-Listening'])

    def test_card_template_names(self):
        self.assertEqual(DICT2ANKI_CARD_TEMPLATE_NAME, 'Forward')
        self.assertEqual(LISTENING_CARD_TEMPLATE_NAME, 'Listening')

    def test_dict2anki_qfmt_uses_brp_and_amepron_audio(self):
        qfmt = dict2anki_card_template_qfmt()
        self.assertRegex(qfmt, BR_EP_AUDIO_PATTERN)
        self.assertRegex(qfmt, AM_EP_AUDIO_PATTERN)
        self.assertIn('UK[{{uk}}]', qfmt)
        self.assertIn('US[{{us}}]', qfmt)

    def test_dict2anki_qfmt_has_sentence_audio_block(self):
        qfmt = dict2anki_card_template_qfmt()
        self.assertIn('{{#sentence_speech0}}', qfmt)
        self.assertIn('{{#sentence_speech1}}', qfmt)
        self.assertIn('{{#sentence_speech2}}', qfmt)

    def test_dict2anki_qfmt_never_emits_sound_markup(self):
        qfmt = dict2anki_card_template_qfmt()
        self.assertIsNone(SOUND_PATTERN.search(qfmt))

    def test_dict2anki_afmt_reveals_definition_via_hint(self):
        afmt = dict2anki_card_template_afmt()
        self.assertIn('{{hint:definition}}', afmt)
        self.assertIn('{{hint:sentence_explain0}}', afmt)
        self.assertIn('{{hint:phrase_explain0}}', afmt)

    def test_listening_qfmt_uses_type_term(self):
        qfmt = listening_card_template_qfmt()
        self.assertIn('{{type:term}}', qfmt)

    def test_listening_qfmt_uses_brp_and_amepron_audio(self):
        qfmt = listening_card_template_qfmt()
        self.assertRegex(qfmt, BR_EP_AUDIO_PATTERN)
        self.assertRegex(qfmt, AM_EP_AUDIO_PATTERN)

    def test_listening_afmt_uses_frontside(self):
        afmt = listening_card_template_afmt()
        self.assertIn('{{FrontSide}}', afmt)
        self.assertIn('back-card', afmt)

    def test_listening_qfmt_never_emits_sound_markup(self):
        qfmt = listening_card_template_qfmt()
        self.assertIsNone(SOUND_PATTERN.search(qfmt))

    def test_dict2anki_css_has_phonetic_and_divider(self):
        self.assertIn('.phonetic', DICT2ANKI_CSS)
        self.assertIn('.divider', DICT2ANKI_CSS)
        self.assertIn('.right-align', DICT2ANKI_CSS)
        self.assertIn('.hint', DICT2ANKI_CSS)

    def test_listening_css_has_hide_on_front_and_back_card(self):
        self.assertIn('.hide-on-front', LISTENING_CSS)
        self.assertIn('.back-card', LISTENING_CSS)
        self.assertIn('display: none', LISTENING_CSS)
        self.assertIn('display: table-cell', LISTENING_CSS)

    def test_backward_compat_alias(self):
        # Old callers / docs reference CARD_TEMPLATE_CSS; should resolve to Dict2Anki CSS.
        self.assertEqual(CARD_TEMPLATE_CSS, DICT2ANKI_CSS)


if __name__ == '__main__':
    unittest.main()