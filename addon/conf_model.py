from dataclasses import dataclass


DEFAULT_CONGEST = 60


@dataclass
class AddonConfig:
    deck: str
    selectedDict: int
    selectedApi: int
    selectedGroup: list
    briefDefinition: bool
    syncTemplates: bool
    noPron: bool
    BrEPron: bool
    AmEPron: bool
    definition_en: bool
    image: bool
    pronunciation: bool
    phrase: bool
    sentence: bool
    exam_type: bool
    congest: int = DEFAULT_CONGEST

    @classmethod
    def from_raw(cls, raw: dict) -> "AddonConfig":
        return cls(
            deck=raw.get('deck', ''),
            selectedDict=raw.get('selectedDict', 0),
            selectedApi=raw.get('selectedApi', 0),
            selectedGroup=raw.get('selectedGroup') or [],
            briefDefinition=raw.get('briefDefinition', True),
            syncTemplates=raw.get('syncTemplates', True),
            noPron=raw.get('noPron', False),
            BrEPron=raw.get('BrEPron', False),
            AmEPron=raw.get('AmEPron', True),
            definition_en=raw.get('definition_en', True),
            image=raw.get('image', True),
            pronunciation=raw.get('pronunciation', True),
            phrase=raw.get('phrase', True),
            sentence=raw.get('sentence', True),
            exam_type=raw.get('exam_type', True),
            congest=int(raw.get('congest', DEFAULT_CONGEST) or DEFAULT_CONGEST),
        )
