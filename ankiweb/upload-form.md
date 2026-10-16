# AnkiWeb upload form — copy/paste values

Source: https://ankiweb.net/shared/upload
Package to upload: `dist/Dict2Anki-Rev-7.3.0.ankiaddon` (build with `python3 build_ankiaddon.py`)

---

## Title  (one line, < 80 chars)

```
Dict2Anki-Rev: Sync Eudic & Youdao word lists into Anki
```

Length: 52 characters.

---

## Tags  (optional, space-separated)

```
vocabulary dictionary eudic youdao english inflection pronunciation
```

---

## Support Page  (optional, must start with http)

```
https://github.com/Sheldontao/Dict2Anki-Rev/issues
```

---

## Branches

AnkiWeb asks: `Branch 1: Supports: ___ to ___`.

```
Branch 1: Supports:  2.1.50  to  -26.09.3
```

Why this range:

- **Lower bound `2.1.50`** — verified against the real `anki` 2.1.50 wheel: every
  backend call the add-on makes already exists there (`col.get_note`, `col.find_notes`,
  `col.add_note(note, deck_id)`, `col.remove_notes`, `col.update_note`, `col.models.by_name`,
  `models.new_field/add_field/new_template/add_template/remove_template/remove/field_map`,
  `note.note_type()`, `note.add_tag`, `note.remove_tag`). `beautifulsoup4` and `requests`
  are bundled dependencies of `aqt` 2.1.50.
- **Upper bound `-26.09.3`** — the leading `-` tells AnkiWeb **not** to offer this
  add-on on versions newer than 26.09.3. The add-on was migrated to the modern
  snake_case backend API specifically because Anki 26.09 began removing the legacy
  camelCase aliases; the next release after that is untested. Drop the `-` if you want
  newer Anki versions to keep downloading this build and accept the risk.

If you prefer a permissive upper bound instead, use `2.1.50 to 26.09.3`.

---

## Description  (Markdown + basic HTML)

Everything below the line is the description text.

---

**Dict2Anki-Rev** pulls your word lists out of **欧路词典 (Eudic)** or **有道词典 (Youdao)** and builds Anki notes with audio, images, definitions, phrases and example sentences.

A maintained fork of [Dict2Anki](https://github.com/megachweng/Dict2Anki) (original author [@megachweng](https://github.com/megachweng)), with features drawn from [joexzh's fork](https://github.com/joexzh/Dict2Anki).

### What it does

- Logs in to Eudic or Youdao and lists your **word books / groups**.
- Pick which groups to sync and, per group, which note type to use.
- For each word it fetches: term, British/American **phonetics + audio**, brief and English **definitions**, **image**, **phrases**, **example sentences (+ sentence audio)**, and **exam type** tags.
- Downloads all media into your collection and writes two ready-made note types:
  - **Dict2Anki** — classic term → recall-the-definition card, hint-revealed definitions, per-sentence audio icons.
  - **Dict2Anki-Listening** — a `{{type:term}}` **typing/listening** card; images, phrases and sentences stay hidden on the front and reveal on the back.
- **Repair tools**: "Download missing assets" and "Fill missing values" re-fetch only what a note is missing, without disturbing existing fields.

### Settings

Toggle each item on or off individually: brief definition, English definition, image, pronunciation, phrase, sentence, exam type. Choose British or American pronunciation, or no audio.

### Notes

- Requires an internet connection and your Eudic / Youdao account (username + password, or paste a browser cookie for Eudic).
- Definitions and example audio come from the dictionary providers; availability varies per word.
- The add-on is developed and tested on **Anki 26.09 (macOS)**.

### Links

- Source & changelog: <https://github.com/Sheldontao/Dict2Anki-Rev>
- Report a bug: <https://github.com/Sheldontao/Dict2Anki-Rev/issues>

MIT licensed.
