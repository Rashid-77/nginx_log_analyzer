import unittest

from log_parser import get_link, get_resp_time


class myTest(unittest.TestCase):
    right_log = [
        '3.3.3.3 - - [234 5ghd] "GET a h" 10.0',
        '"GET a h" 10.0',
        '"GET a h" 10.0',
        '"GET b h" 5.0',
        '"GET b h" 3.0',
    ]
    bad_log = [
        '"GET HTTP/1.1" 10.0',
        '"GET b h" A',
    ]

    def test_get_link(self):
        self.assertEqual(get_link(self.right_log[0]), "a")
        self.assertEqual(get_link(self.right_log[-1]), "b")

    def test_get_resp_time(self):
        self.assertAlmostEqual(get_resp_time(self.right_log[0]), 10.0)
        self.assertEqual(get_resp_time(self.bad_log[-1]), None)


if __name__ == "__main__":
    unittest.main()
