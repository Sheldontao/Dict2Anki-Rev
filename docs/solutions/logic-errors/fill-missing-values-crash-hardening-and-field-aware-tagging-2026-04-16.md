---
title: Fill Missing Values crash hardening and field-aware missing tag sync
date: 2026-04-16
category: logic-errors
module: dict2anki-fill-missing-values
problem_type: logic_error
component: tooling
symptoms:
  - Fill Missing Values queried too many notes and took too long on large collections
  - Empty non-plugin fields were treated as missing and triggered unnecessary queries
  - Legacy note types missing fields like exam_type raised KeyError during updates
  - Missing tags drifted and did not accurately reflect current missing state
root_cause: logic_error
resolution_type: code_fix
severity: high
last_refreshed: 2026-04-16
related_components:
  - testing_framework
tags:
  - dict2anki
  - anki-addon
  - fill-missing-values
  - keyerror
  - missing-tags
  - media-repair
---

# Fill Missing Values crash hardening and field-aware missing tag sync

## Problem
`Fill Missing Values` in the Dict2Anki add-on was not scoped to actionable repairs. It over-queried notes, treated irrelevant empty fields as missing, and could crash on older note types that did not include newly added fields.

## Symptoms
- Running Fill Missing Values on large decks queried almost every note and felt slow/unfocused.
- Notes with custom template fields (outside plugin-managed fields) were incorrectly considered missing.
- Legacy notes threw `KeyError: 'exam_type'` during update flow.
- Missing tags became stale or too coarse to be useful for triage.

## What Didn't Work
- **Query-all strategy:** building a word list from all Dict2Anki notes caused unnecessary API calls and long operations.
- **Fixed missing-tag model:** a single hardcoded missing-media/phonetic tag did not represent broader missing states.
- **Direct note field access:** writing/reading `note[key]` without field-existence guards failed on old note schemas.

## Solution
Implemented a scoped, safe, and state-driven fill pipeline.

1. Candidate filtering before query (`addon/addonWindow.py`):
   - Added `_collect_fill_missing_reasons(note, config, media_dir)`.
   - Checks only plugin-managed fields and configured options.
   - Includes media integrity checks (`utils.is_image_file_missing`, `utils.is_image_file_broken`, `utils.is_audio_file_missing`).
   - Deduplicates by term and updates all notes sharing the same term.

2. Progress bar behavior for fill query (`addon/addonWindow.py`):
   - `queryWords()` now sets `progressBar` max/value and increments via worker tick.

3. Query-time missing classification (`addon/repair_logic.py`, `addon/workers.py`):
   - Added `compute_missing_fields(query_result)` in shared repair logic.
   - Stores normalized missing result in `queryResult['_missing_fields']`.

4. Field-aware missing tag synchronization (`addon/noteManager.py`):
   - Added `sync_missing_tags(note, word)`.
   - Maps missing state to tags:
     - one missing field -> `missing-<field>`
     - multiple missing fields -> `missing-several`
   - Removes obsolete `missing-*` tags before applying new state.

5. Legacy field safety and no-image stabilization (`addon/noteManager.py`, `addon/addonWindow.py`, `addon/constants.py`):
   - `setNoteFieldValue()` now guards missing fields and skips with warning.
   - Added guarded reads for sentence/audio fields in fill scan and sentence overwrite logic.
   - When picture dictionary has no image, `image` is filled with a no-image marker (`dict2anki:no-image`) to prevent repeated re-query loops.

6. Sentence audio URL backfill consistency (`addon/queryApi/eudict.py`, `addon/addonWindow.py`, `addon/noteManager.py`, `addon/repair_logic.py`):
   - Fill scan now treats empty `sentence_speech{i}` with non-empty `sentence{i}` as repairable, and also detects missing media for existing `sentence_speech{i}` values.
   - Fill updates now backfill `sentence_speech{i}` with source URL values directly instead of forcing local `[sound:...]` filename references.
   - Eudict sentence parsing now supports newer HTML structures (including `lj_item` `voice`/`data` attributes) to recover sentence speech URLs for words like `swollen`.

## Why This Works
The fill workflow is now driven by explicit repair criteria, not broad assumptions. Query scope shrinks to notes with real gaps or broken media, compatibility guards prevent crashes on older schemas, and missing tags are treated as computed state that is reconciled every update.

## Prevention
- Keep missing detection centralized in helper functions (`_collect_fill_missing_reasons`, `compute_missing_fields`).
- Treat `missing-*` tags as derived state and always sync (add + remove), never append-only.
- Use guarded field access in all note update paths where legacy note types may exist.
- Keep media integrity checks in repair workflows (missing + broken), not just empty-field checks.
- For sentence audio backfill, prefer durable source URLs in `sentence_speech{i}` over local downloaded filenames when templates consume URL-based playback.

## Related Issues
- None in `docs/solutions/` at creation time (knowledge store initialized by this doc).
