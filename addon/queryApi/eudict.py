import html
import logging
import os
import requests
from urllib.parse import urlparse
from urllib3 import Retry
from requests.adapters import HTTPAdapter
from ..constants import HEADERS
from ..misc import AbstractQueryAPI, SimpleWord
from bs4 import BeautifulSoup
from .langeek import LangeekImageResolver

logger = logging.getLogger('search.queryApi.eudict')
__all__ = ['API']


class Parser:
    def __init__(self, html, word: SimpleWord):
        self._soap = BeautifulSoup(html, 'html.parser')
        self.word = word

    @staticmethod
    def __fix_url_without_http(url):
        if url[0:2] == '//':
            return 'https:' + url
        else:
            return url

    @property
    def definition(self) -> list:
        ret = []
        exp_head_el = self._soap.select_one('div #ExpFC .expHead a')
        if exp_head_el:
            ret.append(exp_head_el.get_text(strip=True))

        div = self._soap.select_one('div #ExpFCchild')
        if not div:
            return ret

        # Part 1: Main definition from <div class="exp">
        exp_divs = div.select('.exp')
        for d in exp_divs:
            text = d.get_text(strip=True)
            if text:
                ret.append(text)

        # Part 2: Transformations from <div id="trans">
        trans_div = div.select_one('#trans')
        if trans_div:
            # Replace <br> tags with a unique separator to split into lines
            for br in trans_div.find_all("br"):
                br.replace_with("||BR||")
            
            # Get text content; spans will be merged automatically
            full_text = trans_div.get_text()
            
            # Split by our separator and add non-empty, stripped lines to the result
            lines = [line.strip() for line in full_text.split("||BR||") if line.strip()]
            ret.extend(lines)

        # Fallback for completely different structures (e.g., definitions in <li>)
        if not ret:
            els = div.select('li')
            if els:
                for el in els:
                    ret.append(el.get_text(strip=True))

        return ret

    @property
    def definition_en(self) -> list:
        # TODO
        return []

    @property
    def phrase(self) -> list:
        els = self._soap.select('div #ExpSPECchild #phrase')
        ret = []
        for el in els:
            try:
                phrase = el.find('i').get_text(strip=True)
                exp = el.find(class_='exp').get_text(strip=True)
                ret.append((phrase, exp))
            except AttributeError:
                pass
        return ret

    @property
    def sentence(self) -> list:
        els = self._soap.select('div #ExpLJchild .lj_item')
        ret = []
        url_prefix = 'https://api.frdic.com/api/v2/speech/speakweb?'
        for el in els:
            try:
                sentence_p_tag = el.select_one('p.line')
                if not sentence_p_tag:
                    continue
                
                sentence_translation_tag = el.select_one('p.exp')
                if not sentence_translation_tag:
                    continue
                sentence_translation = sentence_translation_tag.get_text(strip=True)

                sentence_speech = ""
                
                # Find and process the voice button
                voice_button = el.select_one('a.voice-js')

                if voice_button and voice_button.has_attr('data-rel'):
                    data_rel = html.unescape(voice_button['data-rel'])
                    sentence_speech = url_prefix + data_rel
                    # Remove the button before getting the HTML
                    voice_button.decompose()

                sentence_html = "".join([str(c) for c in sentence_p_tag.contents]).strip()
                ret.append((sentence_html, sentence_translation, sentence_speech))
            except Exception as e:
                logger.error(f"[{self.word.term}] Error parsing sentence: {e}")
                pass
        return ret

    @property
    def image(self) -> str:
        els = self._soap.select('div .word-thumbnail-container img')
        ret = None
        if els:
            try:
                img = els[0]
                src = img.get('src', '').strip()
                if not src:
                    return None

                # Placeholder image should not be imported as word image.
                if 'dict_comment_img_thumbnail' in src:
                    return None

                normalized_src = self.__fix_url_without_http(src)
                parsed = urlparse(normalized_src)

                # Only accept absolute HTTP(S) URLs.
                if parsed.scheme in ('http', 'https') and parsed.netloc:
                    ret = normalized_src
            except KeyError:
                pass
        return ret

    @property
    def pronunciations(self) -> dict:
        if self._soap.title and '登录' in self._soap.title.string:
            logger.warning(f"[{self.word.term}] Eudic API returned a login page. Cookie might be invalid. Falling back.")
            return {
                'AmEPhonetic': None,
                'AmEUrl': None,
                'BrEPhonetic': None,
                'BrEUrl': None,
            }

        pron = {
            'AmEPhonetic': None,
            'AmEUrl': None,
            'BrEPhonetic': None,
            'BrEUrl': None
        }

        phonetic_line_el = self._soap.select_one('.phonitic-line')
        if phonetic_line_el:
            logger.debug(f"[{self.word.term}] Found phonetic line element: {phonetic_line_el}")
            try:
                br_phonetic_span = phonetic_line_el.find('span', string='英')
                if br_phonetic_span:
                    pron['BrEPhonetic'] = br_phonetic_span.find_next_sibling('span', class_='Phonitic').get_text(strip=True)
                    pron['BrEUrl'] = html.unescape(br_phonetic_span.find_parent('a')['data-rel'])
                    logger.debug(f"[{self.word.term}] Found BrEPhonetic: {pron['BrEPhonetic']}")
                else:
                    logger.warning(f"[{self.word.term}] BrE phonetic span not found.")

                am_phonetic_span = phonetic_line_el.find('span', string='美')
                if am_phonetic_span:
                    pron['AmEPhonetic'] = am_phonetic_span.find_next_sibling('span', class_='Phonitic').get_text(strip=True)
                    pron['AmEUrl'] = html.unescape(am_phonetic_span.find_parent('a')['data-rel'])
                    logger.debug(f"[{self.word.term}] Found AmEPhonetic: {pron['AmEPhonetic']}")
                else:
                    logger.warning(f"[{self.word.term}] AmE phonetic span not found.")

                # Construct full URLs if they are relative
                url_prefix = 'https://api.frdic.com/api/v2/speech/speakweb?'
                if pron['BrEUrl'] and 'http' not in pron['BrEUrl']:
                    pron['BrEUrl'] = f"{url_prefix}{pron['BrEUrl']}"
                if pron['AmEUrl'] and 'http' not in pron['AmEUrl']:
                    pron['AmEUrl'] = f"{url_prefix}{pron['AmEUrl']}"

            except (TypeError, KeyError, AttributeError) as e:
                logger.warning(f"[{self.word.term}] Error parsing phonetics: {e}")
                pass
        else:
            logger.warning(f"[{self.word.term}] Phonetic line element '.phonitic-line' not found in the page.")

        # Fallback to Youdao if no audio is found
        if not (pron['AmEUrl'] or pron['BrEUrl']):
            logger.warning(f"[{self.word.term}] No phonetics found on Eudic. Falling back to Youdao for audio.")
            fallback_audio_url = 'http://dict.youdao.com/dictvoice?audio='
            pron['AmEUrl'] = f"{fallback_audio_url}{self.word.term}&type=2"
            pron['BrEUrl'] = f"{fallback_audio_url}{self.word.term}&type=1"

        return pron

    @property
    def BrEPhonetic(self) -> str:
        """英式音标"""
        return self.pronunciations['BrEPhonetic']

    @property
    def AmEPhonetic(self) -> str:
        """美式音标"""
        return self.pronunciations['AmEPhonetic']

    @property
    def BrEPron(self) -> str:
        """英式发音url"""
        return self.pronunciations['BrEUrl']

    @property
    def AmEPron(self) -> str:
        """美式发音url"""
        return self.pronunciations['AmEUrl']

    @property
    def exam_type(self) -> list:
        els = self._soap.select('h1.explain-Word span.tag')
        return [el.get_text(strip=True) for el in els]

    @property
    def result(self):
        return {
            'term': self.word.term,
            'bookId': self.word.bookId,
            'bookName': self.word.bookName,
            'modifiedTime': self.word.modifiedTime,
            'definition_brief': self.word.trans,

            'definition': self.definition,
            'definition_en': self.definition_en,
            'phrase': self.phrase,
            'sentence': self.sentence,
            'image': self.image,
            'BrEPhonetic': self.BrEPhonetic,
            'AmEPhonetic': self.AmEPhonetic,
            'BrEPron': self.BrEPron,
            'AmEPron': self.AmEPron,
            'exam_type': self.exam_type,
        }


from . import youdao


class API(AbstractQueryAPI):
    name = '欧陆词典 API'
    timeout = 10
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    url = 'https://dict.eudic.net/dicts/en/{}'
    parser = Parser

    def __init__(self, session=None):
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            self.session.headers = HEADERS
            self.session.mount('http://', HTTPAdapter(max_retries=self.retries))
            self.session.mount('https://', HTTPAdapter(max_retries=self.retries))
        self.langeek = LangeekImageResolver(self.session, timeout=self.timeout)

    def query(self, word) -> dict:
        try:
            rsp = self.session.get(self.url.format(word.term), timeout=self.timeout)
            soup = BeautifulSoup(rsp.text, 'html.parser')

            # Use the first word of a phrase for the check, as titles may be truncated.
            if not soup.title or word.term.split(' ')[0].lower() not in soup.title.string.lower():
                if soup.title and '登录' in soup.title.string:
                    logger.warning(f'[{word.term}] Eudic returned a login page. Falling back to Youdao API.')
                else:
                    logger.warning(f'[{word.term}] Eudic did not return a dictionary page (e.g., homepage or "not found"). Falling back to Youdao API.')
                return youdao.API().query(word) # Instantiate Youdao API
            
            logger.debug(f'code:{rsp.status_code}- word:{word.term} text:{rsp.text[:100]}')
            result = self.parser(rsp.text, word).result

            # Eudic page often lacks stable English definitions in the static HTML.
            # Enrich from Youdao only when key fields are missing.
            if not result.get('definition_en'):
                yd_result = youdao.API().query(word)
                if yd_result:
                    if yd_result.get('definition_en'):
                        result['definition_en'] = yd_result['definition_en']

            # Use Langeek first-sense image source.
            # If Langeek has no image, keep it empty.
            result['image'] = self.langeek.resolve(word.term)

            return result
        except Exception as e:
            logger.exception(f'[{word.term}] Eudic query failed with an exception. Falling back to Youdao API.')
            return youdao.API().query(word) # Instantiate Youdao API

    def close(self):
        self.session.close()
