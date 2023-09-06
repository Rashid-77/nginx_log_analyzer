#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER"  $request_time';

import json
from datetime import date
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
        for v in self.log.keys():
            self.log[v]["time_sum"] = sum(self.log[v]["data"])
            self.log[v]["count"] = len(self.log[v]["data"])

    def normalize_to_report_size(self, size: int):
        dtype = [
            ('url', '<U18'),    
            ('resp_time', float)
        ]
        data = []
        [data.append([v, self.log[v]["time_sum"]]) for v in self.log.keys()]
        data = np.array([tuple(d) for d in data], dtype=dtype) 
        data[::-1].sort(order=['resp_time'])
        return data[:size]


    def calc_stat(self):
        total_count = 0

        for v in self.log.keys():
            self.log[v]["count"] = len(self.log[v]["data"])
            total_count += self.log[v]["count"]
            self.log[v]["time_sum"] = sum(self.log[v]["data"])

        total_time = sum([self.log[v]["time_sum"] for v in self.log.keys()])

        for v in self.log.keys():
            time_sum = self.log[v]["time_sum"]
            self.log[v]["time_avg"] = time_sum / self.log[v]["count"]
            self.log[v]["time_max"] = max(self.log[v]["data"])

            self.log[v]["time_perc"] = time_sum / total_time * 100
            count_perc = self.log[v]["count"] / total_count * 100
            self.log[v]["count_perc"] = count_perc
        self.stat["count"] = total_count
        self.stat["time_sum"] = total_time

    def get_stat(self):
        data = []
        for k in self.log.keys():
            item = self.log[k]
            d = sorted(item.pop("data"))
            item["time_med"] = d[len(d) // 2]
            item["url"] = k
            data.append(item)
        return data


def render_html(data, template_fname: str):
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
    for line in right_log1:
        log_stat.add_url(get_link(line), get_resp_time(line))
    log_stat.calc_sums()
    log_stat.normalize_to_report_size(5)
    return
    # file = "log/sample.log"
    file = "log/nginx-access-ui.log-20170630"
    with open(file) as f:
        for line in f:
            log_stat.add_url(get_link(line), get_resp_time(line))

    log_stat.calc_stat()
    render_html(log_stat.get_stat(), "report.html")


if __name__ == "__main__":
    main()
