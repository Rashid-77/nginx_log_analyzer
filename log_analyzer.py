#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER"  $request_time';

config = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}


class LogStat:
    def __init__(self) -> None:
        self.log = dict()
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

    def calc_stat(self):
        total_count = 0
        total_time_sum = 0.0
        for v in self.log.keys():
            self.log[v]["count"] = len(self.log[v]["data"])
            time_sum = sum(self.log[v]["data"])
            self.log[v]["time_sum"] = time_sum
            self.log[v]["time_avg"] = time_sum / self.log[v]["count"]
            self.log[v]["time_max"] = max(self.log[v]["data"])

            total_count += self.log[v]["count"]
            total_time_sum += self.log[v]["time_sum"]

            self.log[v]["time_perc"] = time_sum / total_time_sum * 100
            count_perc = self.log[v]["count"] / total_count * 100
            self.log[v]["count_perc"] = count_perc
        self.stat["count"] = total_count
        self.stat["time_sum"] = total_time_sum


def main():
    pass


if __name__ == "__main__":
    main()
