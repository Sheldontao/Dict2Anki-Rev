VERSION = '7.1.0'
RELEASE_URL = 'https://github.com/lixvbnet/Dict2Anki'
VERSION_CHECK_API = 'https://api.github.com/repos/lixvbnet/Dict2Anki/releases/latest'
WINDOW_TITLE = f'Dict2Anki {VERSION}'
MODEL_NAMES = ['Dict2Anki', 'Dict2Anki-Listening'] # Support multiple note types
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


class FieldGroup:
    def __init__(self):
        self.definition_en = "{{definition_en}}"
        self.image = "{{image}}"
        self.pronunciation = "{{pronunciation}}"
        self.phrase = [
            ("{{phrase0}}", "{{phrase_explain0}}"),
            ("{{phrase1}}", "{{phrase_explain1}}"),
            ("{{phrase2}}", "{{phrase_explain2}}"),
        ]
        self.sentence = [
            ("{{sentence0}}", "{{sentence_explain0}}", '<a onclick="this.firstChild.play()"><audio src="{{sentence_speech0}}"></audio>▶︎</a>'),
            ("{{sentence1}}", "{{sentence_explain1}}", '<a onclick="this.firstChild.play()"><audio src="{{sentence_speech1}}"></audio>▶︎</a>'),
            ("{{sentence2}}", "{{sentence_explain2}}", '<a onclick="this.firstChild.play()"><audio src="{{sentence_speech2}}"></audio>▶︎</a>'),
        ]
        self.exam_type = "{{exam_type}}"

    def toggleOff(self, field):
        if field not in CARD_SETTINGS:
            raise RuntimeError(f"Unexpected field: {field}. Must be in {CARD_SETTINGS}!")
        if field == 'phrase':
            setattr(self, field, [
                ("", ""),
                ("", ""),
                ("", "")
            ])
        elif field == 'sentence':
            setattr(self, field, [
                ("", "", ''),
                ("", "", ''),
                ("", "", '')
            ])
        else:
            setattr(self, field, "")

    def toString(self) -> str:
        return f"definition_en={self.definition_en}, image={self.image}, pronunciation={self.pronunciation}, phrase={self.phrase}, sentence={self.sentence}"

    def __str__(self) -> str:
        return self.toString()

    def __repr__(self) -> str:
        return self.toString()


def normal_card_template_qfmt(fg: FieldGroup):
    _ = fg
    return """\
<table>
    <tr>
        <td>
            <h1 class="term">{{term}}{{pronunciation}}</h1>
            <div class="pronounce">
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
<table>
    <tr>
        <td class="phrase">{{phrase0}}</td>
        <td>{{hint:phrase_explain0}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase1}}</td>
        <td>{{hint:phrase_explain1}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase2}}</td>
        <td>{{hint:phrase_explain2}}</td>
    </tr>
</table>
<table>
    <tr>
        <td class="sentence">
            {{sentence0}} {{#sentence0}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech0}}"></audio>▶︎</a
            >{{/sentence0}}
        </td>
        <td>{{hint:sentence_explain0}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence1}} {{#sentence1}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech1}}"></audio>▶︎</a
            >{{/sentence1}}
        </td>
        <td>{{hint:sentence_explain1}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence2}} {{#sentence2}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech2}}"></audio>▶︎</a
            >{{/sentence2}}
        </td>
        <td>{{hint:sentence_explain2}}</td>
    </tr>
</table>
"""


def normal_card_template_afmt(fg: FieldGroup):
    _ = fg
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
            <div class="pronounce">
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
            <div class="definition_en">{{definition_en}}</div>
            <br />
            <div class="definition">{{hint:definition}}</div>
            <div class="exam_type">{{exam_type}}</div>
        </td>
        {{#image}}
        <td style="width: 33%">{{image}}</td>
        {{/image}}
    </tr>
</table>
<div class="divider"></div>
<table>
    <tr>
        <td class="phrase">{{phrase0}}</td>
        <td>{{hint:phrase_explain0}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase1}}</td>
        <td>{{hint:phrase_explain1}}</td>
    </tr>
    <tr>
        <td class="phrase">{{phrase2}}</td>
        <td>{{hint:phrase_explain2}}</td>
    </tr>
</table>
<table>
    <tr>
        <td class="sentence">
            {{sentence0}} {{#sentence0}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech0}}"></audio>▶︎</a
            >{{/sentence0}}
        </td>
        <td>{{hint:sentence_explain0}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence1}} {{#sentence1}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech1}}"></audio>▶︎</a
            >{{/sentence1}}
        </td>
        <td>{{hint:sentence_explain1}}</td>
    </tr>
    <tr>
        <td class="sentence">
            {{sentence2}} {{#sentence2}}<a onclick="this.firstChild.play()"
                ><audio src="{{sentence_speech2}}"></audio>▶︎</a
            >{{/sentence2}}
        </td>
        <td>{{hint:sentence_explain2}}</td>
    </tr>
</table>
"""


def backwards_card_template_qfmt(fg: FieldGroup):
    return f"""\
<table>
    <tr>
        <td>
        <h1 class="term"></h1>
            <div class="pronounce">
                <span class="phonetic">UK[Tap To View]</span>
                <span class="phonetic">US[Tap To View]</span>
            </div>
            <div class="definition">{{{{definition}}}}</div>
            <div class="definition_en">{fg.definition_en}</div>
        </td>
        <td style="width: 33%;">
            {fg.image}
        </td>
    </tr>
</table>
<div class="divider"></div>
<table>
    <tr><td class="phrase">{fg.phrase[0][0]}</td><td>{fg.phrase[0][1]}</td></tr>
    <tr><td class="phrase">{fg.phrase[1][0]}</td><td>{fg.phrase[1][1]}</td></tr>
    <tr><td class="phrase">{fg.phrase[2][0]}</td><td>{fg.phrase[2][1]}</td></tr>
</table>
<table>
    <tr><td class="sentence">{fg.sentence[0][0]}</td><td>{fg.sentence[0][1]}</td></tr>
    <tr><td class="sentence">{fg.sentence[1][0]}</td><td>{fg.sentence[1][1]}</td></tr>
    <tr><td class="sentence">{fg.sentence[2][0]}</td><td>{fg.sentence[2][1]}</td></tr>
</table>
"""


def backwards_card_template_afmt(fg: FieldGroup):
    return normal_card_template_afmt(fg)


# Normal card template
NORMAL_CARD_TEMPLATE_NAME = "Normal"
# Backwards card template (using same AFMT and CSS with Normal card template)
BACKWARDS_CARD_TEMPLATE_NAME = "Backwards"
CARD_TEMPLATE_CSS = """\
.card {
  font-family: arial;
  font-size: 16px;
  text-align: left;
  color: #212121;
  background-color: white;
}
.pronounce {
  line-height: 30px;
  font-size: 26px;
  margin-bottom: 0;
}
.phonetic {
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
.phrase,
.sentence {
  color: #01848f;
  padding-right: 1em;
}
.no-image {
  color: #777;
  font-size: 13px;
  font-style: italic;
}
.no-notes {
  color: #777;
  font-size: 13px;
  font-style: italic;
}
img {
  max-height: 300px;
}
tr {
  vertical-align: top;
}
"""


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
