import json
import logging
import requests
from urllib3 import Retry
from urllib.parse import urlencode
from requests.adapters import HTTPAdapter
from ..constants import HEADERS
from ..misc import AbstractQueryAPI, SimpleWord
from .langeek import LangeekImageResolver

logger = logging.getLogger('dict2Anki.queryApi.youdao')
__all__ = ['API']
SENTENCE_SPEECH_URL_PREFIX = "http://dict.youdao.com/dictvoice?audio="


class Parser:
    def __init__(self, json_obj, word: SimpleWord):
        self._result = json_obj
        self.word = word

    @property
    def definition(self) -> list:
        """中文释义"""
        # print(json.dumps(self._result, ensure_ascii=False))
        try:
            ec = [d['tr'][0]['l']['i'][0] for d in self._result['ec']['word'][0]['trs']][:3]
        except KeyError:
            ec = []
        # Web trans
        try:
            web_trans = [w['value'] for w in self._result['web_trans']['web-translation'][0]['trans']][:3]
        except (KeyError, IndexError):
            web_trans = []
        return ec if ec else web_trans

    @property
    def definition_en(self) -> list:
        """英英释义"""
        try:
            ee = [d['pos'] + ' ' + d['tr'][0]['l']['i'] for d in self._result['ee']['word']['trs']][:3]
        except KeyError:
            ee = []
        return ee

    @property
    def phrase(self) -> list:
        phrase = self._result.get('phrs', dict()).get('phrs', [])
        return [
            (
                p.get('phr', dict()).get('headword', dict()).get('l', dict()).get('i', None),
                p.get('phr', dict()).get('trs', [dict()])[0].get('tr', dict()).get('l', dict()).get('i', None)
            )
            for p in phrase if phrase
        ][:3]

    @property
    def sentence(self) -> list:
        try:
            return [(s['sentence-eng'], s['sentence-translation'], SENTENCE_SPEECH_URL_PREFIX + s['sentence-speech']) for s in self._result['blng_sents_part']['sentence-pair']][:3]
        except KeyError:
            return []

    @property
    def image(self) -> str:
        try:
            return [i['image'] for i in self._result['pic_dict']['pic']][0]
        except (KeyError, IndexError):
            return None

    @property
    def pronunciations(self) -> dict:
        url = 'http://dict.youdao.com/dictvoice?audio='
        pron = {
            'AmEPhonetic': None,
            'AmEUrl': None,
            'BrEPhonetic': None,
            'BrEUrl': None
        }
        try:
            pron['AmEPhonetic'] = self._result['simple']['word'][0]['usphone']
        except KeyError:
            pass

        try:
            pron['BrEPhonetic'] = self._result['simple']['word'][0]['ukphone']
        except KeyError:
            pass

        try:
            pron['AmEUrl'] = url + self._result['simple']['word'][0]['usspeech']
        except (TypeError, KeyError):
            pass

        try:
            pron['BrEUrl'] = url + self._result['simple']['word'][0]['ukspeech']
        except (TypeError, KeyError):
            pass

        # if no audio, then set a default one
        if not (pron['AmEUrl'] or pron['BrEUrl']):
            pron['AmEUrl'] = f"{url}{self.word.term}&type=2"
            pron['BrEUrl'] = f"{url}{self.word.term}&type=1"

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
        try:
            exam_t = self._result['ec']['exam_type']
        except KeyError as err:
            exam_t = []
        return exam_t

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


class API(AbstractQueryAPI):
    name = '有道 API'
    timeout = 10
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    url = 'https://dict.youdao.com/jsonapi'
    params = {"dicts": {"count": 99, "dicts": [["ec", "ee", "phrs", "pic_dict"], ["web_trans"], ["fanyi"], ["blng_sents_part"]]}}
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

    def query(self, word: SimpleWord) -> dict:
        queryResult = None
        try:
            rsp = self.session.get(self.url, params=urlencode(dict(self.params, **{'q': word.term})), timeout=self.timeout)
            logger.debug(f'code:{rsp.status_code} term:{word.term} text:{rsp.text}')
            if rsp.status_code != 200:
                logger.error(f'code:{rsp.status_code} term:{word.term} text:{rsp.text}')
            json_obj = rsp.json()
            if 'simple' not in json_obj or 'word' not in json_obj['simple']:
                logger.warning(f'[{word.term}] Youdao API response does not contain phonetic information. Full response: {json.dumps(json_obj, ensure_ascii=False)}')
            queryResult = self.parser(json_obj, word).result
            if queryResult is not None:
                # Always prefer Langeek page first-sense image.
                queryResult['image'] = self.langeek.resolve(word.term)
        except Exception as e:
            logger.exception(e)
        finally:
            logger.debug(queryResult)
            return queryResult

    def close(self):
        self.session.close()
