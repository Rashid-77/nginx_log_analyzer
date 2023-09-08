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
    '"GET h" A',
    '"-" 33',
]


class TestLogAnalyzer(unittest.TestCase):
    def test_add_url(self):
        log_stat = LogStat()
        log_stat.add_url(right_log[0])
        self.assertEqual(len(log_stat.log), 1)
        self.assertEqual(log_stat.log["a"], {"data": [10.0]})

    def test_calc(self):
        log_stat = LogStat()
        for line in right_log:
            log_stat.add_url(line)

        log_stat.calc_sums()
        self.assertAlmostEqual(log_stat.stat["time_sum"], 38.0)
        self.assertEqual(log_stat.stat["count"], len(right_log))

        urls = log_stat.get_sorted_urls_for_report(2)
        data = log_stat.calc_stat(urls)
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
                "time_med": 4.0,
                "time_perc": 21.052631578947366,
                "time_sum": 8.0,
                "url": "b",
            },
        ]
        self.assertEqual(data, origin)

    def test_add_bad_urls_times(self):
        log_stat = LogStat()
        for line in bad_log:
            log_stat.add_url(line)
        log_stat.calc_sums()
        log_stat.get_sorted_urls_for_report(3)
        self.assertEqual(log_stat.stat["count"], 0)


if __name__ == "__main__":
    unittest.main()
