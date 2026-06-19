VERSION = '7.3.0'
RELEASE_URL = 'https://github.com/lixvbnet/Dict2Anki'
VERSION_CHECK_API = 'https://api.github.com/repos/lixvbnet/Dict2Anki/releases/latest'
WINDOW_TITLE = f'Dict2Anki {VERSION}'
MODEL_NAMES = ['Dict2Anki', 'Dict2Anki-Listening'] # Support multiple note types
DEFAULT_GROUP_MODEL = MODEL_NAMES[0]  # Used when a group has no explicit model assignment.
MODEL_NAME_REGEX = r'Dict2Anki.*' # For regex matching

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
HEADERS = {
    'User-Agent': USER_AGENT
}

LOG_BUFFER_CAPACITY = 20    # number of log items
LOG_FLUSH_INTERVAL = 3      # seconds

# continue to use Dict2Anki 4.x model
ASSET_FILENAME_PREFIX = "MG"
NO_IMAGE_FIELD_TOKEN = "dict2anki:no-image"
NO_NOTES_FIELD_TOKEN = "dict2anki:no-notes"
MODEL_FIELDS = [
    'term', 'notes', 'definition',
    'definition_en',
    'uk', 'us', 'BrEPron', 'AmEPron',
    'phrase0', 'phrase1', 'phrase2', 'phrase_explain0', 'phrase_explain1', 'phrase_explain2',
    'sentence0', 'sentence1', 'sentence2', 'sentence_explain0', 'sentence_explain1', 'sentence_explain2', 'sentence_speech0', 'sentence_speech1', 'sentence_speech2',
    'image', 'pronunciation',
    'group', 'exam_type', 'modifiedTime',
]
CARD_SETTINGS = ['definition_en', 'image', 'pronunciation', 'phrase', 'sentence', 'exam_type']


# Each model has exactly one card type, identified by these names.
DICT2ANKI_CARD_TEMPLATE_NAME = "Forward"
LISTENING_CARD_TEMPLATE_NAME = "Listening"


def dict2anki_card_template_qfmt():
    """Hardcoded Dict2Anki front template.

    Replaces the previous FieldGroup-based dynamic template. Uses Anki's
    built-in {{#field}}{{/field}} conditionals to skip empty fields.
    """
    return """\
<table>
    <tr>
        <td>
            <h1 class="term">{{term}}{{pronunciation}}</h1>
            <div>
                <span class="phonetic"
                    ><a onclick="this.firstChild.play()"
                        ><audio src="{{BrEPron}}"></audio>UK[{{uk}}]</a
                    ></span
                >
                <span class="phonetic"
                    ><a onclick="this.firstChild.play()"
                        ><audio src="{{AmEPron}}"></audio>US[{{us}}]</a
                    ></span
                >
            </div>
            <div class="definition"></div>
            <div class="definition_en"></div>
        </td>
        <td style="width: 33%"></td>
    </tr>
</table>

<div class="divider"></div>

{{#phrase0}}
<table>
    <tr>
        <td class="phrase">{{phrase0}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase1}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase2}}</td>
    </tr>
</table>
<br>
{{/phrase0}}
<table>
    <tr>
<td class="sentence">
    {{sentence0}}

    {{#sentence_speech0}}
    <a href="javascript:void(0);"
       onclick="var a = this.querySelector('audio'); a.currentTime = 0; a.play();"
       style="text-decoration: none; cursor: pointer; margin-left: 5px;">
        <audio src="{{text:sentence_speech0}}"></audio>
        <span style="color: #666;">▶︎</span>
    </a>
    {{/sentence_speech0}}
</td>
    </tr>
<td class="sentence">
    {{sentence1}}

    {{#sentence_speech1}}
    <a href="javascript:void(0);"
       onclick="var a = this.querySelector('audio'); a.currentTime = 0; a.play();"
       style="text-decoration: none; cursor: pointer; margin-left: 5px;">
        <audio src="{{text:sentence_speech1}}"></audio>
        <span style="color: #666;">▶︎</span>
    </a>
    {{/sentence_speech1}}
</td>
    <tr>
<td class="sentence">
    {{sentence2}}

    {{#sentence_speech2}}
    <a href="javascript:void(0);"
       onclick="var a = this.querySelector('audio'); a.currentTime = 0; a.play();"
       style="text-decoration: none; cursor: pointer; margin-left: 5px;">
        <audio src="{{text:sentence_speech2}}"></audio>
        <span style="color: #666;">▶︎</span>
    </a>
    {{/sentence_speech2}}
</td>
    </tr>
</table>
"""


def dict2anki_card_template_afmt():
    """Hardcoded Dict2Anki back template."""
    return """\
<table>
    <tr>
        <td>
            <h1 class="term">
                {{term}}{{pronunciation}}
                <a
                    onclick="event.stopPropagation()"
                    href="eudic://dict/{{term}}"
                >
                    <img class="icon" src="_eudict_24.png" />
                </a>
                <a
                    onclick="event.stopPropagation()"
                    href="https://www.google.com/search?tbm=isch&q={{term}}"
                >
                    <img
                        class="icon"
                        src="https://img.icons8.com/color/28/google.png"
                        alt="Google Icon"
                    />
                </a>
            </h1>
            <div>
                <span class="phonetic"
                    ><a onclick="this.firstChild.play()"
                        ><audio src="{{BrEPron}}"></audio>UK[{{uk}}]</a
                    ></span
                >
                <span class="phonetic"
                    ><a onclick="this.firstChild.play()"
                        ><audio src="{{AmEPron}}"></audio>US[{{us}}]</a
                    ></span
                >
            </div><br>
<div class="note">{{notes}}</div>
            <div class="definition_en">{{definition_en}}</div>
            <br />
            <div class="definition">{{hint:definition}}</div>
            <div class="exam_type">{{exam_type}}</div>
        </td>
        {{#image}}
        <td class="right-align" style="width: 33%">{{image}}</td>
        {{/image}}
    </tr>
</table>
<div class="divider"></div>

{{#phrase0}}
<table>
    <tr>
        <td class="phrase">{{phrase0}}</td>
        <td class="right-align">{{hint:phrase_explain0}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase1}}</td>
        <td class="right-align">{{hint:phrase_explain1}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase2}}</td>
        <td class="right-align">{{hint:phrase_explain2}}</td>
    </tr>
</table>
<br>
{{/phrase0}}
<table>
    <tr>
        <td class="sentence">
            {{sentence0}} {{#sentence0}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech0}}"></audio>▶︎</a
            >{{/sentence0}}
        </td>
        <td class="right-align">{{hint:sentence_explain0}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence1}} {{#sentence1}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech1}}"></audio>▶︎</a
            >{{/sentence1}}
        </td>
        <td class="right-align">{{hint:sentence_explain1}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence2}} {{#sentence2}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech2}}"></audio>▶︎</a
            >{{/sentence2}}
        </td>
        <td class="right-align">{{hint:sentence_explain2}}</td>
    </tr>
</table>
"""


def listening_card_template_qfmt():
    """Hardcoded Dict2Anki-Listening front template (typing + listening)."""
    return """\
<table style="width: 100%; table-layout: fixed;">
    <tr>
        <td style="vertical-align: top; text-align: left;">
            <div class="type-box" style="margin-bottom: 10px;">
                {{type:term}}
            </div>

            <h1 class="term" style="margin: 0;">{{pronunciation}}<a
                    onclick="event.stopPropagation()"
                    href="eudic://dict/{{term}}"
                >
                    <img class="icon" src="_eudict_24.png" />
                </a>
                <a
                    onclick="event.stopPropagation()"
                    href="https://www.google.com/search?tbm=isch&q={{term}}"
                >
                    <img
                        class="icon"
                        src="https://img.icons8.com/color/28/google.png"
                        alt="Google Icon"
                    />
                </a>
            </h1>

            <div class="pronounce" style="margin-top: 5px;">
                {{#uk}}
                <span class="phonetic">
                    <a onclick="this.firstChild.play()"><audio src="{{BrEPron}}"></audio>UK[{{uk}}]</a>
                </span>
                {{/uk}}

                {{#us}}
                <span class="phonetic">
                    <a onclick="this.firstChild.play()"><audio src="{{AmEPron}}"></audio>US[{{us}}]</a>
                </span>
                {{/us}}
            </div>

            <div class="definition">{{hint:definition}}</div>

            {{#definition_en}}
            <div class="definition_en" style="color: #666; font-style: italic; margin-top: 5px;">
                {{definition_en}}
            </div>
            {{/definition_en}}
        </td>

        <td class="hide-on-front" style="width: 35%; vertical-align: top; text-align: right;">
            {{#image}}{{image}}{{/image}}
            </td>
    </tr>
</table>
<div class='hide-on-front'>

{{#phrase0}}
<hr> {{phrase0}}<br>
{{phrase_explain0}}
{{/phrase0}}

{{#sentence0}}
<hr> {{sentence0}}<br>
{{sentence_explain0}}
{{/sentence0}}

<div>
"""


def listening_card_template_afmt():
    """Hardcoded Dict2Anki-Listening back template."""
    return """\
<div class="back-card">
<!-- First, show the complete front content -->
{{FrontSide}}
</div>
"""


DICT2ANKI_CSS = """\
.card {
  font-family: arial;
  font-size: 16px;
  text-align: left;
  color: #212121;
  background-color: white;
}
.phonetic {
  line-height: 30px;
  font-size: 16px;
  font-family: "lucida sans unicode", arial, sans-serif;
  color: #32a852;
}
.phonetic a {
  color: inherit;
  text-decoration: none;
}
.phonetic a:hover {
  text-decoration: underline;
}
.term {
  margin-bottom: -5px;
}
.exam_type {
  margin: 1em 0 0em 0;
  color: gray;
}
.divider {
  margin: 1em 0 1em 0;
  border-bottom: 2px solid #4caf50;
}
.note {
  color: #01848f;
  padding-right: 1em;
}
/* 3. Limit max image width to prevent layout overflow */
img {
    max-width: 100%;
    height: auto;
}
/* 2. Position right column with right-aligned content */
.right-align {
    text-align: right;
    vertical-align: top;
}
/* 1. Ensure all tables occupy 100% of window width */
table {
    width: 100%;
    border-collapse: collapse;
}
tr {
  vertical-align: top;
}
/* Style the click-to-reveal hint text */
.hint {
    color: #808080
}
"""


LISTENING_CSS = """\
.card {
  font-family: Arial, sans-serif;
  font-size: 20px;
  text-align: left;
  color: #000;
  background-color: #fff;
}

.term {
  font-size: 35px;
}

hr#answer {
  border: none;
  height: 4px;
  margin: 20px auto;
}
/* Hide extra content by default (i.e., on the front) */
.hide-on-front {
    display: none;
}
/* Reveal hidden content when inside .back-card (i.e., on the back) */
.back-card .hide-on-front {
    display: table-cell;
}
"""


# Backward-compat aliases (referenced by tests / older callers). New code should
# use the per-model constants directly.
NORMAL_CARD_TEMPLATE_NAME = DICT2ANKI_CARD_TEMPLATE_NAME
BACKWARDS_CARD_TEMPLATE_NAME = LISTENING_CARD_TEMPLATE_NAME
CARD_TEMPLATE_CSS = DICT2ANKI_CSS


PRON_TYPES = ['noPron', 'BrEPron', 'AmEPron']


def get_pronunciation(word: dict, preferred_pron: int) -> (int, bool):
    """:return: pron_type: int, is_fallback: bool"""
    if preferred_pron == 0:
        return 0, False
    if word[PRON_TYPES[preferred_pron]]:
        return preferred_pron, False
    fallback_pron = 2 if preferred_pron == 1 else 1
    if word[PRON_TYPES[fallback_pron]]:
        return fallback_pron, True
    return 0, True


def default_image_filename(term: str) -> str:
    return f"{ASSET_FILENAME_PREFIX}-{term}.jpg"


def default_image_filename_by_url(term: str, image_url: str) -> str:
    ext = '.jpg'
    if image_url:
        try:
            parsed = urlparse(image_url)
            path = parsed.path or ''
            guessed = os.path.splitext(path)[1].lower()
            if guessed in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                ext = guessed
            else:
                query = parse_qs(parsed.query or '')
                image_type = (query.get('type') or query.get('format') or [''])[0].lower()
                query_type_map = {
                    'jpeg': '.jpg',
                    'jpg': '.jpg',
                    'png': '.png',
                    'webp': '.webp',
                    'gif': '.gif',
                }
                if image_type in query_type_map:
                    ext = query_type_map[image_type]
        except Exception:
            pass
    return f"{ASSET_FILENAME_PREFIX}-{term}{ext}"


def default_audio_filename(term: str) -> str:
    return f"{ASSET_FILENAME_PREFIX}-{term}.mp3"


def default_no_image_field_value() -> str:
    return f'<!-- {NO_IMAGE_FIELD_TOKEN} -->'


def is_no_image_field_value(field_value: str) -> bool:
    return bool(field_value) and (NO_IMAGE_FIELD_TOKEN in field_value)


def default_no_notes_field_value() -> str:
    return f'<!-- {NO_NOTES_FIELD_TOKEN} -->'


def is_no_notes_field_value(field_value: str) -> bool:
    return bool(field_value) and (NO_NOTES_FIELD_TOKEN in field_value)

import os
from urllib.parse import parse_qs, urlparse
