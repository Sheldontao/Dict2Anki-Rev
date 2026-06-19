import re
import unittest

from addon.queryApi.youdao import Parser
from addon.misc import SimpleWord


URL_PATTERN = re.compile(r'^https?://')
SOUND_PATTERN = re.compile(r'\[sound:')


def _build_result(simple=None):
    """Construct a minimal Youdao JSON-API response shape consumed by Parser."""
    return {
        'simple': simple if simple is not None else {},
        'ec': {'word': [{'trs': []}], 'exam_type': []},
        'web_trans': {'web-translation': [{'trans': []}]},
    }


def _word_entry(ukphone='', ukspeech=None, usphone='', usspeech=None):
    """Real Youdao responses include '&type=N' suffix on ukspeech/usspeech."""
    return {
        'ukphone': ukphone,
        'ukspeech': ukspeech,
        'usphone': usphone,
        'usspeech': usspeech,
    }


class YoudaoPronunciationsTests(unittest.TestCase):
    """Pin the URL-only contract for BrEUrl/AmEUrl on the Youdao Parser."""

    def _assert_url_only_contract(self, value):
        self.assertIsNotNone(value)
        self.assertIsInstance(value, str)
        self.assertRegex(value, URL_PATTERN)
        self.assertIsNone(SOUND_PATTERN.search(value),
                          f"Value contains [sound: reference: {value!r}")

    def test_both_speech_fields_populated(self):
        """Both ukspeech and usspeech present → both URLs are dictvoice URLs."""
        result = _build_result(simple={'word': [_word_entry(ukspeech='supposition&type=1', usspeech='supposition&type=2')]})
        parser = Parser(result, SimpleWord('supposition'))

        self._assert_url_only_contract(parser.BrEPron)
        self._assert_url_only_contract(parser.AmEPron)
        self.assertEqual(parser.BrEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=1')
        self.assertEqual(parser.AmEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=2')

    def test_only_usspeech_populated_keeps_brephonetic_none(self):
        """Only usspeech present → AmEUrl is a URL, BrEUrl stays None (no fallback because one is set)."""
        result = _build_result(simple={'word': [_word_entry(usspeech='supposition&type=2')]})
        parser = Parser(result, SimpleWord('supposition'))

        self._assert_url_only_contract(parser.AmEPron)
        self.assertIsNone(parser.BrEPron)
        self.assertNotIn('[sound:', parser.AmEPron)

    def test_only_ukspeech_populated_keeps_amephonetic_none(self):
        """Only ukspeech present → BrEUrl is a URL, AmEUrl stays None."""
        result = _build_result(simple={'word': [_word_entry(ukspeech='supposition&type=1')]})
        parser = Parser(result, SimpleWord('supposition'))

        self._assert_url_only_contract(parser.BrEPron)
        self.assertIsNone(parser.AmEPron)
        self.assertNotIn('[sound:', parser.BrEPron)

    def test_empty_simple_falls_back_to_dictvoice(self):
        """Empty 'simple' block → both URLs fall back to dictvoice URLs."""
        result = _build_result(simple={'word': [_word_entry()]})
        parser = Parser(result, SimpleWord('supposition'))

        self._assert_url_only_contract(parser.BrEPron)
        self._assert_url_only_contract(parser.AmEPron)
        self.assertEqual(parser.BrEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=1')
        self.assertEqual(parser.AmEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=2')

    def test_missing_simple_key_falls_back_to_dictvoice(self):
        """Missing 'simple' key entirely → both URLs fall back to dictvoice URLs."""
        result = _build_result()
        del result['simple']
        parser = Parser(result, SimpleWord('supposition'))

        self._assert_url_only_contract(parser.BrEPron)
        self._assert_url_only_contract(parser.AmEPron)
        self.assertEqual(parser.BrEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=1')
        self.assertEqual(parser.AmEPron, 'http://dict.youdao.com/dictvoice?audio=supposition&type=2')

    def test_result_dict_branches_pin_url_contract(self):
        """Parser.result['BrEPron'] and ['AmEPron'] are URL strings, never [sound:]."""
        result = _build_result(simple={'word': [_word_entry(ukspeech='supposition&type=1', usspeech='supposition&type=2')]})
        result_dict = Parser(result, SimpleWord('supposition')).result

        self._assert_url_only_contract(result_dict['BrEPron'])
        self._assert_url_only_contract(result_dict['AmEPron'])


if __name__ == '__main__':
    unittest.main()