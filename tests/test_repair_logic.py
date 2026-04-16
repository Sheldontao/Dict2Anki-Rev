import unittest

from addon.repair_logic import CounterGroup, compute_missing_fields, derive_missing_tags


class RepairLogicTests(unittest.TestCase):
    def test_counter_group(self):
        c = CounterGroup()
        c.reset(total=3)
        c.inc_success()
        c.inc_failed()
        self.assertEqual(c.total, 3)
        self.assertEqual(c.success, 1)
        self.assertEqual(c.failed, 1)

    def test_compute_missing_fields(self):
        sample = {
            'definition': ['a'],
            'definition_en': [],
            'image': None,
            'BrEPhonetic': '/a/',
            'AmEPhonetic': '',
            'BrEPron': '',
            'AmEPron': '',
            'phrase': [],
            'sentence': [('x', 'y')],
            'exam_type': [],
        }
        missing = compute_missing_fields(sample)
        self.assertIn('definition_en', missing)
        self.assertIn('image', missing)
        self.assertIn('pronunciation', missing)
        self.assertIn('phrase', missing)
        self.assertIn('exam_type', missing)

    def test_derive_missing_tags(self):
        self.assertEqual(derive_missing_tags([]), set())
        self.assertEqual(derive_missing_tags(['image']), {'missing-image'})
        self.assertEqual(derive_missing_tags(['image', 'pronunciation']), {'missing-several'})


if __name__ == '__main__':
    unittest.main()
