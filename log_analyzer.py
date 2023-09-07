#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER"  $request_time';

import json
from datetime import date
from statistics import fmean, median

import numpy as np

from log_parser import get_link, get_resp_time

config = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}


class LogStat:
    def __init__(self) -> None:
        self.log = dict()
        self.report = dict()
        self.stat = {
            "count": 0,
            "time_sum": 0.0,
        }

    def add_url(self, url: str, time: float):
        stat = self.log.get(url)
        if stat is None:
            self.log.update(
                {
                    url: {
                        "data": [
                            time,
                        ]
                    }
                }
            )
        else:
            self.log[url]["data"].append(time)

    def calc_sums(self):
        self.stat["count"] = 0
        for k in self.log.keys():
            self.log[k]["time_sum"] = sum(self.log[k]["data"])
            self.log[k]["count"] = len(self.log[k]["data"])
            self.stat["count"] += self.log[k]["count"]

        time_sums = [self.log[v]["time_sum"] for v in self.log.keys()]
        self.stat["time_sum"] = sum(time_sums)

    def get_sorted_urls_for_report(self, size: int) -> tuple:
        data = []
        [data.append([v, self.log[v]["time_sum"]]) for v in self.log.keys()]

        dtype = [("url", "<U256"), ("time_sum", float)]
        data = np.array([tuple(d) for d in data], dtype=dtype)
        data[::-1].sort(order=["time_sum"])
        return (arr["url"] for arr in data[:size])

    def calc_stat(self, urls: tuple) -> list[dict]:
        data = []
        for k in urls:
            print(k)
            count_perc = self.log[k]["count"] / self.stat["count"] * 100
            time_perc = self.log[k]["time_sum"] / self.stat["time_sum"] * 100
            i = {
                "url": k,
                "count": self.log[k]["count"],
                "count_perc": count_perc,
                "time_avg": fmean(self.log[k]["data"]),
                "time_max": max(self.log[k]["data"]),
                "time_med": median(sorted(self.log[k]["data"])),
                "time_perc": time_perc,
                "time_sum": self.log[k]["time_sum"],
            }
            data.append(i)
            self.log.pop(k)
        return data

    def render_html(self, data, template_fname: str):
        data = json.dumps(data)
        fname = f"{config['REPORT_DIR']}/report-{date.today()}.html"
        # fname = f"report-{date.today()}.html"

        with open(template_fname, mode="r") as f:
            file = f.read()

        with open(fname, mode="w") as f:
            file = file.replace("$table_json", data)
            f.write(file)


log_stat = LogStat()

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


def main():
    file = "log/nginx-access-ui.log-20170630"
    file = "log/sample.log"
    cnt = 0
    with open(file) as f:
        for line in f:
            log_stat.add_url(get_link(line), get_resp_time(line))
            cnt += 1
            if cnt % 1000 == 0:
                print(cnt)
    # for line in right_log1:
    #     log_stat.add_url(get_link(line), get_resp_time(line))
    log_stat.calc_sums()
    urls = log_stat.get_sorted_urls_for_report(500)
    data = log_stat.calc_stat(urls)
    log_stat.render_html(data, "report.html")


if __name__ == "__main__":
    main()
