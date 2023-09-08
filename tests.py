import unittest

from log_analyzer import LogStat

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
right_log1 = [
    '3.3.3.3 - - [234 5ghd] "GET a h" 10.0',
    '"GET a h" 10.0',
    '"GET a h" 10.0',
    '"GET b h" 5.0',
    '"GET b h" 3.0',
    '"GET c h" 0.01',
    '"GET c h" 1.0',
    '"GET d h" 33.0',
    '"GET d h" 99.0',
    '"GET e h" 2.0',
    '"GET e h" 7.0',
    '"GET e h" 6.8',
    '"GET f h" 2.0',
    '"GET f h" 12.0',
]


# class TestParser(unittest.TestCase):
#     def test_get_link(self):
#         self.assertEqual(get_link(right_log[0]), "a")
#         self.assertEqual(get_link(right_log[-1]), "b")

#     def test_get_resp_time(self):
#         self.assertAlmostEqual(get_resp_time(right_log[0]), 10.0)
#         self.assertEqual(get_resp_time(bad_log[-1]), None)


class TestLogAnalyzer(unittest.TestCase):

    def test_add_url(self):
        log_stat = LogStat()
        log_stat.add_url(right_log[0])
        self.assertEqual(len(log_stat.log), 1)

        # self.log_st = LogStat()

        for line in right_log:
            log_stat.add_url(line)

        log_stat.calc_sums()
        urls = log_stat.get_sorted_urls_for_report(2)
        log_stat.calc_stat(urls)
        self.assertEqual(log_stat.stat["count"], len(right_log))
        self.assertAlmostEqual(log_stat.stat["time_sum"], 38.0)

    def test_get_stat(self):
        self.log_stat = LogStat()
        for line in right_log:
            self.log_stat.add_url(line)

        self.log_stat.calc_stat()
        self.assertEqual(self.log_stat.stat["count"], len(right_log))
        self.assertAlmostEqual(self.log_stat.stat["time_sum"], 38.0)
        data = self.log_stat.get_stat()
        origin = [
            {
                "count": 3,
                "count_perc": 60.0,
                "time_avg": 10.0,
                "time_max": 10.0,
                "time_med": 10.0,
                "time_perc": 78.94736842105263,
                "time_sum": 30.0,
                "url": "a",
            },
            {
                "count": 2,
                "count_perc": 40.0,
                "time_avg": 4.0,
                "time_max": 5.0,
                "time_med": 5.0,
                "time_perc": 21.052631578947366,
                "time_sum": 8.0,
                "url": "b",
            },
        ]

        self.assertEqual(data, origin)


if __name__ == "__main__":
    unittest.main()
