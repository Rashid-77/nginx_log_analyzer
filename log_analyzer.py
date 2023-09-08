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
from http_methods import http_methods

config = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}


class LogStat:
    def __init__(self) -> None:
        self.log = dict()
        self.report = dict()
        self.stat = {
            "count": 0,
            "time_sum": 0.0,
        }
        
        self.max_urllen = 0

    def add_url(self, line: str):
        
        start = line.find('"') + 1
        end = line.find('"', start)
        url = line[start:end]

        if not any(method in url for method in http_methods):
            return
        try:
            url = url.split()[1]
        except IndexError:
            return

        time = line[end:].split()[-1]
        time_ = time.replace(".", "")
        if not time_.isnumeric():
            return
        time = float(time)

        stat = self.log.get(url)
        if len(url) > self.max_urllen:
            self.max_urllen = len(url)
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
        data = [{"url": k, "time_sum": self.log[k]["time_sum"]} for k in self.log.keys()]
        data.sort(key=lambda x: x["time_sum"], reverse=True)
        return (arr["url"] for arr in data[:size])

    def calc_stat(self, urls: tuple) -> list[dict]:
        data = []
        for k in urls:
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

    def _calc_stat(self, urls: tuple, data) -> list[dict]:
        dat = []
        for k in urls:
            count_perc = data[k]["count"] / self.stat["count"] * 100
            time_perc = data[k]["time_sum"] / self.stat["time_sum"] * 100
            i = {
                "url": k,
                "count": data[k]["count"],
                "count_perc": count_perc,
                "time_avg": fmean(data[k]["data"]),
                "time_max": max(data[k]["data"]),
                "time_med": median(sorted(data[k]["data"])),
                "time_perc": time_perc,
                "time_sum": data[k]["time_sum"],
            }
            dat.append(i)
            data.pop(k)
        return dat

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



def main():
    file = "log/nginx-access-ui.log-20170630"
    with open(file) as f:
        for line in f:
            log_stat.add_url(line)

    log_stat.calc_sums()
    urls = log_stat.get_sorted_urls_for_report(1000)
    data = log_stat.calc_stat(urls)
    log_stat.render_html(data, "report.html")


if __name__ == "__main__":
    main()
