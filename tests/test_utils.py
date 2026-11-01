from unittest import TestCase as BaseTestCase

from wolframclient.utils.logger import str_trim


class TestCase(BaseTestCase):
    def test_str_trim_no_limit(self):
        self.assertEqual(str_trim("abcde"), "abcde")

    def test_str_trim_above_limit(self):
        self.assertEqual(str_trim("abcde", max_char=3), "abc...(2 more)")

    def test_str_trim_eq_limit(self):
        self.assertEqual(str_trim("abc", max_char=3), "abc")
