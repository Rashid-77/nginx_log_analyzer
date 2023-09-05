import unittest

from log_analyzer import LogStat
from log_parser import get_link, get_resp_time

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


class TestParser(unittest.TestCase):
    def test_get_link(self):
        self.assertEqual(get_link(right_log[0]), "a")
        self.assertEqual(get_link(right_log[-1]), "b")

    def test_get_resp_time(self):
        self.assertAlmostEqual(get_resp_time(right_log[0]), 10.0)
        self.assertEqual(get_resp_time(bad_log[-1]), None)


class TestLogAnalyzer(unittest.TestCase):
    log_stat = LogStat()

    def test_add_url(self):
        url = get_link(right_log[0])
        time = get_resp_time(right_log[0])
        self.log_stat.add_url(url, time)
        self.assertEqual(len(self.log_stat.log), 1)

        self.log_st = LogStat()

        for line in right_log:
            self.log_st.add_url(get_link(line), get_resp_time(line))

        self.log_st.calc_stat()
        self.assertEqual(self.log_st.stat["count"], len(right_log))
        self.assertAlmostEqual(self.log_st.stat["time_sum"], 38.0)


if __name__ == "__main__":
    unittest.main()
