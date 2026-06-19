import unittest

from addon.conf_model import AddonConfig, DEFAULT_CONGEST
from addon.constants import MODEL_NAMES


class ConfigModelTests(unittest.TestCase):
    def test_from_raw_applies_defaults(self):
        raw = {
            'deck': 'Default',
            'selectedDict': 0,
            'selectedApi': 1,
            'selectedGroup': None,
            'briefDefinition': True,
            'syncTemplates': True,
            'noPron': False,
            'BrEPron': False,
            'AmEPron': True,
            'definition_en': True,
            'image': True,
            'pronunciation': True,
            'phrase': True,
            'sentence': True,
            'exam_type': True,
        }
        cfg = AddonConfig.from_raw(raw)
        self.assertEqual(cfg.congest, DEFAULT_CONGEST)
        self.assertEqual(cfg.selectedGroup, [])
        self.assertEqual(cfg.groupModel, {})

    def test_from_raw_uses_given_congest(self):
        raw = {
            'deck': 'Default',
            'selectedDict': 0,
            'selectedApi': 1,
            'selectedGroup': [],
            'briefDefinition': True,
            'syncTemplates': True,
            'noPron': False,
            'BrEPron': False,
            'AmEPron': True,
            'definition_en': True,
            'image': True,
            'pronunciation': True,
            'phrase': True,
            'sentence': True,
            'exam_type': True,
            'congest': 120,
        }
        cfg = AddonConfig.from_raw(raw)
        self.assertEqual(cfg.congest, 120)

    def test_from_raw_uses_given_group_model(self):
        raw = {
            'deck': 'Default',
            'selectedDict': 0,
            'selectedApi': 1,
            'selectedGroup': [],
            'briefDefinition': True,
            'syncTemplates': True,
            'noPron': False,
            'BrEPron': False,
            'AmEPron': True,
            'definition_en': True,
            'image': True,
            'pronunciation': True,
            'phrase': True,
            'sentence': True,
            'exam_type': True,
            'groupModel': {'听力词汇': MODEL_NAMES[1]},
        }
        cfg = AddonConfig.from_raw(raw)
        self.assertEqual(cfg.groupModel, {'听力词汇': MODEL_NAMES[1]})


if __name__ == '__main__':
    unittest.main()
