import re
import unittest

from addon.queryApi.eudict import Parser
from addon.misc import SimpleWord


URL_PATTERN = re.compile(r'^https?://')
SOUND_PATTERN = re.compile(r'\[sound:')


def _build_html(title, phonitic_line_inner=''):
    return (
        '<html><head><title>' + title + '</title></head>'
        '<body>'
        '<span class="phonitic-line">' + phonitic_line_inner + '</span>'
        '</body></html>'
    )


class EudicPronunciationsTests(unittest.TestCase):
    """Pin the URL-only contract for BrEUrl/AmEUrl on the Eudic Parser.

    Every populated pronunciation URL must:
    - be a string matching ^https?://
    - never contain '[sound:' (Anki's local-media reference syntax)
    """

    def _assert_url_only_contract(self, result):
        self.assertIsNone(SOUND_PATTERN.search(result['BrEPron'] or ''),
                          f"BrEPron contains [sound: reference: {result['BrEPron']!r}")
        self.assertIsNone(SOUND_PATTERN.search(result['AmEPron'] or ''),
                          f"AmEPron contains [sound: reference: {result['AmEPron']!r}")

        for field_name in ('BrEPron', 'AmEPron'):
            value = result[field_name]
            self.assertIsInstance(value, str,
                                  f"{field_name} must be a URL string, got {type(value).__name__}: {value!r}")
            self.assertRegex(value, URL_PATTERN,
                             f"{field_name} must start with http:// or https://: {value!r}")

    def test_query_string_data_rel_gets_prefixed(self):
        """data-rel query string is prefixed with api.frdic.com speakweb URL."""
        phonitic_line = (
            '<a data-rel="langid=en&amp;voicename=en_uk_male&amp;txt=QYNdGVzdA%3d%3d">'
            '<span>英</span><span class="Phonitic">/test/</span></a>'
            '<a data-rel="langid=en&amp;voicename=en_us_female&amp;txt=QYNdGVzdA%3d%3d">'
            '<span>美</span><span class="Phonitic">/test/</span></a>'
        )
        html = _build_html('test', phonitic_line)
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(
            result['BrEPron'],
            'https://api.frdic.com/api/v2/speech/speakweb?langid=en&voicename=en_uk_male&txt=QYNdGVzdA%3d%3d',
        )
        self.assertEqual(
            result['AmEPron'],
            'https://api.frdic.com/api/v2/speech/speakweb?langid=en&voicename=en_us_female&txt=QYNdGVzdA%3d%3d',
        )
        self._assert_url_only_contract(result)

    def test_absolute_https_data_rel_kept_verbatim(self):
        """An absolute https:// data-rel URL is preserved unchanged (no prefix)."""
        phonitic_line = (
            '<a data-rel="https://fs-gateway.esdict.cn/wordmp3/abc.mp3">'
            '<span>英</span><span class="Phonitic">/test/</span></a>'
            '<a data-rel="https://fs-gateway.esdict.cn/wordmp3/def.mp3">'
            '<span>美</span><span class="Phonitic">/test/</span></a>'
        )
        html = _build_html('test', phonitic_line)
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(result['BrEPron'], 'https://fs-gateway.esdict.cn/wordmp3/abc.mp3')
        self.assertEqual(result['AmEPron'], 'https://fs-gateway.esdict.cn/wordmp3/def.mp3')
        self._assert_url_only_contract(result)

    def test_absolute_http_data_rel_kept_verbatim(self):
        """An absolute http:// (not https://) data-rel URL is also preserved unchanged."""
        phonitic_line = (
            '<a data-rel="http://example.com/audio.mp3">'
            '<span>英</span><span class="Phonitic">/test/</span></a>'
            '<a data-rel="http://example.com/audio2.mp3">'
            '<span>美</span><span class="Phonitic">/test/</span></a>'
        )
        html = _build_html('test', phonitic_line)
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(result['BrEPron'], 'http://example.com/audio.mp3')
        self.assertEqual(result['AmEPron'], 'http://example.com/audio2.mp3')
        self._assert_url_only_contract(result)

    def test_login_page_returns_none_at_parser_level(self):
        """Login-page early-return at the Parser level yields all-None.

        The Youdao fallback for login pages lives one level up in API.query()
        (addon/queryApi/eudict.py:321-326) and is out of scope for Parser tests.
        """
        html = _build_html('登录')
        result = Parser(html, SimpleWord('test')).result

        self.assertIsNone(result['BrEPron'])
        self.assertIsNone(result['AmEPron'])

    def test_missing_phonitic_line_falls_back_to_youdao_dictvoice(self):
        """No .phonitic-line element → Youdao dictvoice URL fallback for both fields."""
        html = _build_html('test')
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(
            result['BrEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=1',
        )
        self.assertEqual(
            result['AmEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=2',
        )
        self._assert_url_only_contract(result)

    def test_malformed_anchors_swallow_exception_and_fall_back(self):
        """Anchors that raise AttributeError during parsing → Youdao dictvoice fallback."""
        phonitic_line = (
            '<a data-rel="langid=en&amp;txt=QYNdGVzdA%3d%3d">'
            '<span>英</span></a>'
        )
        html = _build_html('test', phonitic_line)
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(
            result['BrEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=1',
        )
        self.assertEqual(
            result['AmEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=2',
        )
        self._assert_url_only_contract(result)

    def test_empty_data_rel_falls_through_to_youdao(self):
        """Empty data-rel yields empty string → falls through to Youdao fallback."""
        phonitic_line = (
            '<a data-rel="">'
            '<span>英</span><span class="Phonitic">/test/</span></a>'
            '<a data-rel="">'
            '<span>美</span><span class="Phonitic">/test/</span></a>'
        )
        html = _build_html('test', phonitic_line)
        result = Parser(html, SimpleWord('test')).result

        self.assertEqual(
            result['BrEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=1',
        )
        self.assertEqual(
            result['AmEPron'],
            'http://dict.youdao.com/dictvoice?audio=test&type=2',
        )
        self._assert_url_only_contract(result)


if __name__ == '__main__':
    unittest.main()