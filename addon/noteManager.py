import re
from .constants import *
from .repair_logic import derive_missing_tags
import logging

logger = logging.getLogger('dict2Anki.noteManager')
try:
    from aqt import mw
    import anki
except ImportError:
    from test.dummy_aqt import mw
    from test import dummy_anki as anki


def getDeckList():
    return [deck['name'] for deck in mw.col.decks.all()]


def getWordsByDeck(deckName) -> [str]:
    notes = mw.col.find_notes(f'deck:"{deckName}"')
    words = []
    for nid in notes:
        note = mw.col.get_note(nid)
        model_name = note.note_type().get('name', '').lower()
        if re.match(r'dict2anki.*', model_name) and note['term']:
            words.append(note['term'])
    return words


def getNoteIDsOfWords(wordList, deckName) -> list:
    notes = []
    for word in wordList:
        note = mw.col.find_notes(f'deck:"{deckName}" term:"{word}"')
        if note:
            notes.append(note[0])
    return notes


def getOrCreateDeck(deckName, model):
    deck_id = mw.col.decks.id(deckName)
    deck = mw.col.decks.get(deck_id)
    mw.col.decks.select(deck['id'])
    mw.col.decks.save(deck)
    mw.col.models.set_current(model)
    model['did'] = deck['id']
    mw.col.models.save(model)
    mw.reset()
    return deck


def getOrCreateModel(modelName, recreate=False) -> (object, bool, bool):
    """Create Note Model (Note Type). return: (model, newCreated, fieldsUpdated)"""
    model = mw.col.models.by_name(modelName)
    if model:
        if not recreate:
            updated = mergeModelFields(model)
            return model, False, updated
        else:       # Dangerous action!!!  It would delete model, AND all its cards/notes!
            logger.warning(f"Force deleting and recreating model {modelName}")
            mw.col.models.remove(model)

    logger.info(f'Creating model {modelName}')
    newModel = mw.col.models.new(modelName)
    for field in MODEL_FIELDS:
        mw.col.models.add_field(newModel, mw.col.models.new_field(field))
    return newModel, True, True


def getOrCreateCardTemplate(modelObject, cardTemplateName, qfmt, afmt, css, add=True):
    """Create Card Template (Card Type)"""
    logger.info(f"Add card template {cardTemplateName}")
    existingCardTemplate = modelObject['tmpls']
    if cardTemplateName in [t.get('name') for t in existingCardTemplate]:
        logger.info(f"[Skip] Card Type '{cardTemplateName}' already exists.")
        return
    cardTemplate = mw.col.models.new_template(cardTemplateName)
    cardTemplate['qfmt'] = qfmt
    cardTemplate['afmt'] = afmt
    modelObject['css'] = css
    mw.col.models.add_template(modelObject, cardTemplate)
    if add:
        mw.col.models.add(modelObject)
    else:
        mw.col.models.save(modelObject)


def getOrCreateDict2AnkiCardTemplate(modelObject):
    """Create the single hardcoded Forward card type on the Dict2Anki model."""
    qfmt = dict2anki_card_template_qfmt()
    afmt = dict2anki_card_template_afmt()
    getOrCreateCardTemplate(modelObject, DICT2ANKI_CARD_TEMPLATE_NAME,
                            qfmt, afmt, DICT2ANKI_CSS, add=True)


def getOrCreateListeningCardTemplate(modelObject):
    """Create the single hardcoded Listening card type on the Dict2Anki-Listening model."""
    qfmt = listening_card_template_qfmt()
    afmt = listening_card_template_afmt()
    getOrCreateCardTemplate(modelObject, LISTENING_CARD_TEMPLATE_NAME,
                            qfmt, afmt, LISTENING_CSS, add=True)


def checkModelFields(modelObject) -> (bool, set, set):
    """Check if model fields are as expected. :return: (ok, unknown_fields, missing_fields)"""
    current_fields = [f['name'] for f in modelObject['flds']]
    expected_fields = MODEL_FIELDS

    set_current = set(current_fields)
    set_expected = set(expected_fields)
    if set_current == set_expected:
        return True, set(), set()
    else:
        unknown_fields = set_current - set_expected
        missing_fields = set_expected - set_current
        return False, unknown_fields, missing_fields


def mergeModelFields(modelObject) -> bool:
    """Merge model fields. Only need to do updates when there are missing fields. return: updated"""
    ok, unknown_fields, missing_fields = checkModelFields(modelObject)
    if ok or (not missing_fields):
        return False
    logger.warning(f"unknown fields: {unknown_fields}")
    logger.warning(f"missing fields: {missing_fields}")
    logger.info(f"Merge model fields...")
    fields = modelObject['flds']
    # field_map = {f["name"]: (f["ord"], f) for f in fields}
    field_map = mw.col.models.field_map(modelObject)

    fields.clear()
    logger.info(f"step 1. add MODEL_FIELDS: {MODEL_FIELDS}")
    for f_name in MODEL_FIELDS:
        if f_name in field_map:
            index, field = field_map[f_name]
        else:
            field = mw.col.models.new_field(f_name)
        fields.append(field)
    logger.info(f"step 2. add unknown_fields: {unknown_fields}")
    for f_name in unknown_fields:
        index, field = field_map[f_name]
        fields.append(field)
    mw.col.models.save(modelObject)
    return True


def _expected_card_template_for_model(modelName: str):
    """Return (qfmt, afmt, css, expected_template_name) for a given model."""
    if modelName == MODEL_NAMES[0]:
        return (
            dict2anki_card_template_qfmt(),
            dict2anki_card_template_afmt(),
            DICT2ANKI_CSS,
            DICT2ANKI_CARD_TEMPLATE_NAME,
        )
    if modelName == MODEL_NAMES[1]:
        return (
            listening_card_template_qfmt(),
            listening_card_template_afmt(),
            LISTENING_CSS,
            LISTENING_CARD_TEMPLATE_NAME,
        )
    raise ValueError(f"Unknown model name: {modelName!r}")


def checkModelCardTemplates(modelObject) -> bool:
    """Check if model card templates are as expected."""
    expected_qfmt, expected_afmt, expected_css, expected_name = _expected_card_template_for_model(
        modelObject['name'])

    templates = modelObject['tmpls']
    if len(templates) != 1 or templates[0]['name'] != expected_name:
        logger.info(f"Expected exactly one card template named '{expected_name}' for model {modelObject['name']!r}; found {[t['name'] for t in templates]}")
        return False
    tmpl = templates[0]
    if tmpl['qfmt'] != expected_qfmt or tmpl['afmt'] != expected_afmt:
        logger.info(f"Changes detected in template '{expected_name}' for model {modelObject['name']!r}")
        return False
    if modelObject.get('css', '') != expected_css:
        logger.info(f"Changes detected in card CSS for model {modelObject['name']!r}")
        return False
    return True


def resetModelCardTemplates(modelObject):
    """Reset Card Templates and CSS to default for the given model."""
    expected_qfmt, expected_afmt, expected_css, expected_name = _expected_card_template_for_model(
        modelObject['name'])

    logger.info(f"Reset card templates for model {modelObject['name']!r}")
    templates = modelObject['tmpls']
    # Remove any extra templates; the per-model architecture only allows one.
    for tmpl in list(templates):
        if tmpl['name'] != expected_name:
            logger.info(f"Removing stale card template {tmpl['name']!r} from model {modelObject['name']!r}")
            mw.col.models.remove_template(modelObject, tmpl)

    if not any(t['name'] == expected_name for t in templates):
        logger.info(f"Creating card template '{expected_name}' on model {modelObject['name']!r}")
        new_tmpl = mw.col.models.new_template(expected_name)
        new_tmpl['qfmt'] = expected_qfmt
        new_tmpl['afmt'] = expected_afmt
        mw.col.models.add_template(modelObject, new_tmpl)
    else:
        tmpl = next(t for t in templates if t['name'] == expected_name)
        tmpl['qfmt'] = expected_qfmt
        tmpl['afmt'] = expected_afmt

    modelObject['css'] = expected_css
    mw.col.models.save(modelObject)


def setNoteFieldValue(note, key: str, value: str, isNewNote: bool, overwrite: bool) -> bool:
    """set note field value. :return isWritten"""
    try:
        _ = note[key]
    except KeyError:
        logger.warning(f"[Skip] Field '{key}' does not exist in note type '{note.note_type().get('name', '')}'")
        return False

    if not value:
        return False
    if isNewNote or overwrite:
        note[key] = value
        return True
    if not note[key]:   # field value of the Existing Note is missing
        note[key] = value
        return True
    return False


def _note_remove_tag(note, tag: str) -> bool:
    if tag in note.tags:
        note.remove_tag(tag)
        return True
    return False


def _note_add_tag(note, tag: str) -> bool:
    if tag not in note.tags:
        note.add_tag(tag)
        return True
    return False


def _note_list_tags(note) -> [str]:
    return list(note.tags)


def sync_missing_tags(note, word: dict) -> bool:
    missing_fields = [f for f in (word.get('_missing_fields') or []) if isinstance(f, str) and f]
    target_tags = derive_missing_tags(missing_fields)

    current_missing_tags = {tag for tag in _note_list_tags(note) if tag.startswith('missing-')}
    changed = False

    for tag in sorted(current_missing_tags - target_tags):
        if _note_remove_tag(note, tag):
            logger.info(f"移除标签[{tag}]：{note['term']}")
            changed = True

    for tag in sorted(target_tags - current_missing_tags):
        if _note_add_tag(note, tag):
            logger.info(f"添加标签[{tag}]：{note['term']}")
            changed = True

    return changed


def addNoteToDeck(deck, model, config: dict, word: dict, whichPron: str, existing_note=None, overwrite=False):
    """
    Add note
    :param deck: deck
    :param model: model
    :param config: currentConfig
    :param word: (dict) query result of a word
    :param whichPron:
    :param existing_note: if not None, then do not create new note
    :param overwrite: True to overwrite existing note, and False to fill missing values only. (Only relevant when
                        'existing_note' is not None.
    :return: None
    """
    if not word:
        logger.warning(f'查询结果{word} 异常，忽略')
        return

    isNewNote = (existing_note is None)
    if isNewNote:
        model['did'] = deck['id']
        note = anki.notes.Note(mw.col, model)   # create new note
    else:
        note = existing_note                    # existing note

    term = word['term']
    setNoteFieldValue(note, 'term', term, isNewNote, overwrite)
    # note['term'] = term

    # ================================== Required fields ==================================
    # 1. Required fields are always included in Anki cards and cannot be toggled off
    # 2. Always add to note if it has a value

    # group (bookName)
    if word['bookName']:
        key, value = 'group', word['bookName']
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['group'] = word['bookName']

    # exam_type
    if word['exam_type']:       # [str]
        key, value = 'exam_type', " / ".join(word['exam_type'])
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['exam_type'] = " / ".join(word['exam_type'])

    # modifiedTime
    if word['modifiedTime']:    # int
        key, value = 'modifiedTime', str(word['modifiedTime'])
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['modifiedTime'] = str(word['modifiedTime'])

    # phonetic
    if word['BrEPhonetic']:
        key, value = 'uk', word['BrEPhonetic']
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['uk'] = word['BrEPhonetic']
    if word['AmEPhonetic']:
        key, value = 'us', word['AmEPhonetic']
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['us'] = word['AmEPhonetic']
    
    # Keep pronunciation URLs in dedicated fields for template-level playback controls.
    if word['BrEPron']:
        key, value = 'BrEPron', word['BrEPron']
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
    if word['AmEPron']:
        key, value = 'AmEPron', word['AmEPron']
        setNoteFieldValue(note, key, value, isNewNote, overwrite)

    # definition
    definitions = []
    if not word['definition_brief'] and not word['definition']:         # both empty
        logger.warning(f"NO DEFINITION FOR WORD {word['term']}!!!")
    elif word['definition_brief'] and word['definition']:               # both non-empty
        definitions = [word['definition_brief']] if config['briefDefinition'] else word['definition']
    else:                                                               # one is empty and the other is non-empty
        definitions = [word['definition_brief']] if word['definition_brief'] else word['definition']

    key, value = 'definition', '<br>\n'.join(definitions)
    setNoteFieldValue(note, key, value, isNewNote, overwrite)
    # note['definition'] = '<br>\n'.join(definitions)

    # ================================== Optional fields ==================================
    # 1. Ignore "query settings"
    # 2. Always add to note if it has a value
    # 3. Toggle visibility by dynamically updating card template

    # definition_en
    if word['definition_en']:
        key, value = 'definition_en', '<br>\n'.join(word['definition_en'])
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['definition_en'] = '<br>\n'.join(word['definition_en'])

    # notes (personal notes from Eudic ExpNote, fetched via CustomizeInfo XHR)
    key = 'notes'
    current_notes_value = ''
    try:
        current_notes_value = note[key]
    except KeyError:
        current_notes_value = ''

    if word.get('notes'):
        value = word['notes']
        replace_placeholder = is_no_notes_field_value(current_notes_value)
        logger.info(f"[{term}] notes from API, value_len={len(value)}, replace_placeholder={replace_placeholder}")
        setNoteFieldValue(note, key, value, isNewNote, overwrite or replace_placeholder)
    else:
        # Only persist a no-notes marker if the field is empty or already a placeholder.
        # If it already has real content, don't overwrite it (the API may have legitimately
        # returned no notes for this query - the user's existing content is still valid).
        if current_notes_value and not is_no_notes_field_value(current_notes_value):
            logger.debug(f"[{term}] notes field already has content, skip writing placeholder")
        else:
            value = default_no_notes_field_value()
            logger.info(f"[{term}] writing no-notes placeholder, current_value={repr(current_notes_value)[:50]}")
            setNoteFieldValue(note, key, value, isNewNote, overwrite)

    # image
    key = 'image'
    current_image_value = ''
    try:
        current_image_value = note[key]
    except KeyError:
        current_image_value = ''

    if word['image']:
        imageFilename = default_image_filename_by_url(term, word['image'])
        value = f'<div><img src="{imageFilename}" /></div>'
        # Keep legacy notes healthy: if image filename pattern changed (e.g. wrong extension
        # from old versions), rewrite image field even when not doing a global overwrite.
        image_needs_repair = (not isNewNote) and (current_image_value != value)
        replace_placeholder = is_no_image_field_value(current_image_value)
        setNoteFieldValue(note, key, value, isNewNote, overwrite or image_needs_repair or replace_placeholder)
        # note['image'] = f'<div><img src="{imageFilename}" /></div>'
    elif config.get('image'):
        # Only persist a no-image marker if the field is empty or already a placeholder.
        if current_image_value and not is_no_image_field_value(current_image_value):
            logger.debug(f"[{term}] image field already has content, skip writing placeholder")
        else:
            value = default_no_image_field_value()
            setNoteFieldValue(note, key, value, isNewNote, overwrite)

    # pronunciation
    if whichPron and whichPron != 'noPron' and word[whichPron]:
        pronFilename = default_audio_filename(term)
        key, value = 'pronunciation', f"[sound:{pronFilename}]"
        setNoteFieldValue(note, key, value, isNewNote, overwrite)
        # note['pronunciation'] = f"[sound:{pronFilename}]"

    # phrase
    if word['phrase']:
        for i, phrase_tuple in enumerate(word['phrase'][:3]):       # at most 3 phrases
            key, value = f'phrase{i}', phrase_tuple[0]
            setNoteFieldValue(note, key, value, isNewNote, overwrite)
            key, value = f'phrase_explain{i}', phrase_tuple[1]
            setNoteFieldValue(note, key, value, isNewNote, overwrite)
            # note[f'phrase{i}'], note[f'phrase_explain{i}'] = phrase_tuple

    # sentence
    if word['sentence']:
        for i, sentence_tuple in enumerate(word['sentence'][:3]):   # at most 3 sentences
            s_overwrite = overwrite
            # Sentence may have changed over time.
            # To avoid sentence-speech mismatch, overwrite sentence info if sentence_speech is missing.
            # Also overwrite sentence info if term is not highlighted.
            sentence_speech_value = ""
            sentence_value = ""
            try:
                sentence_speech_value = note[f'sentence_speech{i}']
            except KeyError:
                pass
            try:
                sentence_value = note[f'sentence{i}']
            except KeyError:
                pass

            if (
                not sentence_speech_value
                or sentence_speech_value.strip().startswith('[sound:')
                or f"<b>{term}</b>" not in sentence_value
            ):
                s_overwrite = True

            key, value = f'sentence{i}', sentence_tuple[0]
            setNoteFieldValue(note, key, value, isNewNote, s_overwrite)
            key, value = f'sentence_explain{i}', sentence_tuple[1]
            setNoteFieldValue(note, key, value, isNewNote, s_overwrite)
            if sentence_tuple[2]:
                key, value = f'sentence_speech{i}', sentence_tuple[2]
                setNoteFieldValue(note, key, value, isNewNote, s_overwrite)
            # note[f'sentence{i}'], note[f'sentence_explain{i}'] = sentence_tuple

    sync_missing_tags(note, word)

    if isNewNote:
        mw.col.add_note(note, deck['id'])
        logger.info(f"添加笔记{term}")
    else:
        mw.col.update_note(note)
        logger.info(f"更新笔记{term}")
