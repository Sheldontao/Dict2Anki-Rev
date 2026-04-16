import os
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Set, Tuple

from .constants import default_audio_filename


SENTENCE_AUDIO_STATUS_PENDING = 'pending'
SENTENCE_AUDIO_STATUS_FILLED = 'filled'
SENTENCE_AUDIO_STATUS_UNAVAILABLE_UPSTREAM = 'unavailable-upstream'
SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED = 'download-failed'
SENTENCE_AUDIO_STATUS_SKIPPED = 'skipped'


@dataclass
class CounterGroup:
    total: int = 0
    success: int = 0
    failed: int = 0

    def reset(self, total: int = 0) -> None:
        self.total = total
        self.success = 0
        self.failed = 0

    def inc_success(self) -> None:
        self.success += 1

    def inc_failed(self) -> None:
        self.failed += 1


def compute_missing_fields(query_result: dict) -> List[str]:
    missing = []

    has_definition = bool(query_result.get('definition_brief')) or bool(query_result.get('definition'))
    if not has_definition:
        missing.append('definition')

    if not query_result.get('definition_en'):
        missing.append('definition_en')

    if not query_result.get('image'):
        missing.append('image')

    has_phonetic = bool(query_result.get('AmEPhonetic') or query_result.get('BrEPhonetic'))
    if not has_phonetic:
        missing.append('phonetic')

    has_pron_url = bool(query_result.get('AmEPron') or query_result.get('BrEPron'))
    if not has_pron_url:
        missing.append('pronunciation')

    if not query_result.get('phrase'):
        missing.append('phrase')

    if not query_result.get('sentence'):
        missing.append('sentence')

    if not query_result.get('exam_type'):
        missing.append('exam_type')

    return missing


def derive_missing_tags(missing_fields: Iterable[str]) -> Set[str]:
    clean = [f for f in missing_fields if isinstance(f, str) and f]
    if len(clean) == 1:
        return {f"missing-{clean[0]}"}
    if len(clean) >= 2:
        return {'missing-several'}
    return set()


def collect_sentence_audio_repair_reasons(
    sentence_values: Iterable[str],
    speech_values: Iterable[str],
    media_dir: str,
    is_audio_file_missing: Callable[[str, str], bool],
) -> List[str]:
    reasons: List[str] = []
    sentence_items = list(sentence_values)
    speech_items = list(speech_values)
    for i, sentence_value in enumerate(sentence_items):
        sentence_value = sentence_value or ''
        speech_value = speech_items[i] if i < len(speech_items) else ''
        speech_value = speech_value or ''

        if not sentence_value.strip():
            continue

        if not speech_value.strip():
            reasons.append(f'sentence_speech{i}:empty')
            continue

        if is_audio_file_missing(speech_value, media_dir):
            reasons.append(f'sentence_speech{i}:file-missing')
    return reasons


def build_sentence_audio_download_plan(term: str, sentences: Iterable[tuple], max_slots: int = 3):
    tasks: List[Tuple[str, str]] = []
    slot_status: Dict[int, str] = {}
    slot_filename: Dict[int, str] = {}

    for i, sentence_tuple in enumerate(list(sentences)[:max_slots]):
        sentence_audio_url = ''
        if len(sentence_tuple) > 2:
            sentence_audio_url = sentence_tuple[2] or ''

        filename = default_audio_filename(f'{term}_s{i}')
        slot_filename[i] = filename

        if sentence_audio_url:
            tasks.append((filename, sentence_audio_url))
            slot_status[i] = SENTENCE_AUDIO_STATUS_PENDING
        else:
            slot_status[i] = SENTENCE_AUDIO_STATUS_UNAVAILABLE_UPSTREAM

    return tasks, slot_status, slot_filename


def finalize_sentence_audio_slot_status(
    slot_status: Dict[int, str],
    slot_filename: Dict[int, str],
    media_dir: str,
    download_status_by_filename: Dict[str, str] = None,
    file_exists: Callable[[str], bool] = os.path.exists,
) -> Dict[int, str]:
    download_status_by_filename = download_status_by_filename or {}
    finalized: Dict[int, str] = {}
    for i, status in slot_status.items():
        if status == SENTENCE_AUDIO_STATUS_UNAVAILABLE_UPSTREAM:
            finalized[i] = status
            continue

        if status == SENTENCE_AUDIO_STATUS_SKIPPED:
            finalized[i] = status
            continue

        filename = slot_filename.get(i)
        if not filename:
            finalized[i] = SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED
            continue

        filepath = os.path.join(media_dir, filename)
        file_present = file_exists(filepath)
        download_status = download_status_by_filename.get(filename)

        if file_present:
            finalized[i] = SENTENCE_AUDIO_STATUS_FILLED
            continue

        if download_status in ('download-failed', SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED):
            finalized[i] = SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED
            continue

        finalized[i] = SENTENCE_AUDIO_STATUS_DOWNLOAD_FAILED
    return finalized


def apply_sentence_audio_status_to_sentences(sentences: Iterable[tuple], slot_status: Dict[int, str], max_slots: int = 3):
    patched = []
    for i, sentence_tuple in enumerate(list(sentences)[:max_slots]):
        sentence_text = sentence_tuple[0] if len(sentence_tuple) > 0 else ''
        sentence_explain = sentence_tuple[1] if len(sentence_tuple) > 1 else ''
        sentence_audio_url = sentence_tuple[2] if len(sentence_tuple) > 2 else ''

        if slot_status.get(i) != SENTENCE_AUDIO_STATUS_FILLED:
            sentence_audio_url = ''

        patched.append((sentence_text, sentence_explain, sentence_audio_url))
    return patched
