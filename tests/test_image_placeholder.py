import unittest

from addon.constants import default_no_image_field_value, is_no_image_field_value


class ImagePlaceholderTests(unittest.TestCase):
    def test_placeholder_is_detectable(self):
        value = default_no_image_field_value()
        self.assertTrue(is_no_image_field_value(value))


if __name__ == '__main__':
    unittest.main()
