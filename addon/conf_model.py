from dataclasses import dataclass, field

from .constants import MODEL_NAMES


DEFAULT_CONGEST = 60
DEFAULT_GROUP_MODEL = MODEL_NAMES[0]  # "Dict2Anki"


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
    groupModel: dict = field(default_factory=dict)

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
            groupModel=raw.get('groupModel') or {},
        )
