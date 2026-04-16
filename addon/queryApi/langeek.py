import json
import logging
import re
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger('dict2Anki.queryApi.langeek')


class LangeekImageResolver:
    """Resolve image URL from Langeek word page first translation."""

    SEARCH_URL = 'https://api.langeek.co/v1/cs/en/word/'
    PAGE_URL = 'https://dictionary.langeek.co/en/word/{word_id}?entry={entry}'

    def __init__(self, session, timeout=10):
        self.session = session
        self.timeout = timeout

    def resolve(self, term: str) -> Optional[str]:
        term = (term or '').strip()
        if not term:
            return None

        try:
            word_item = self._search_entry(term)
            if not word_item:
                return None

            page_url = self.PAGE_URL.format(
                word_id=word_item['id'],
                entry=quote(word_item['entry']),
            )
            rsp = self.session.get(page_url, timeout=self.timeout)
            if rsp.status_code != 200:
                logger.debug(f'[{term}] Langeek word page status: {rsp.status_code}')
                return None

            return self._extract_first_translation_photo(rsp.text)
        except Exception as e:
            logger.debug(f'[{term}] Langeek image resolve failed: {e}')
            return None

    def _search_entry(self, term: str) -> Optional[dict]:
        rsp = self.session.get(
            self.SEARCH_URL,
            params={
                'term': term,
                'filter': ',inCategory,photo,withExamples',
            },
            timeout=self.timeout,
        )

        if rsp.status_code != 200:
            logger.debug(f'[{term}] Langeek search status: {rsp.status_code}')
            return None

        data = rsp.json()
        if not isinstance(data, list) or not data:
            return None

        normalized_term = term.lower()
        for item in data:
            if isinstance(item, dict) and str(item.get('entry', '')).strip().lower() == normalized_term:
                if item.get('id') and item.get('entry'):
                    return item

        first = data[0]
        if isinstance(first, dict) and first.get('id') and first.get('entry'):
            return first
        return None

    @staticmethod
    def _extract_first_translation_photo(page_html: str) -> Optional[str]:
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page_html)
        if not m:
            return None

        data = json.loads(m.group(1))
        word_entry = (
            data.get('props', {})
            .get('pageProps', {})
            .get('initialState', {})
            .get('static', {})
            .get('wordEntry', {})
        )
        words = word_entry.get('words') or []
        if not words:
            return None

        first_word = words[0] if isinstance(words[0], dict) else {}
        translations = first_word.get('translations') or []
        if not translations:
            return None

        first_translation = translations[0] if isinstance(translations[0], dict) else {}
        word_photo = first_translation.get('wordPhoto') or {}
        photo = word_photo.get('photo')

        if isinstance(photo, str) and photo.startswith(('http://', 'https://')):
            return photo
        return None
