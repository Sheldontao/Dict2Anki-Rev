from dataclasses import dataclass
from typing import Iterable, List, Set


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
