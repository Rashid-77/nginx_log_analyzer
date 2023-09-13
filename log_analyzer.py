#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local]
#                     '"$request" $status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" '
#                     '"$http_X_REQUEST_ID" "$http_X_RB_USER"  $request_time';

import argparse
import configparser
import gzip
import json
import re
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from statistics import fmean, median

from http_methods import http_methods

config = {"REPORT_SIZE": 1000, "REPORT_DIR": "./reports", "LOG_DIR": "./log"}
DEFAULT_CONFIG_FILENAME = "config.ini"


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
        if isinstance(line, bytes):
            line = line.decode("utf-8")
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
        # fmt: off
        data = [
            {
                "url": k,
                "time_sum": self.log[k]["time_sum"]
            }
            for k in self.log.keys()
        ]
        # fmt: on
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

    def render_html(self, data, template_fname: str, dest: str):
        data = json.dumps(data)
        fname = f"{dest}/report-{date.today()}.html"

        with open(template_fname, mode="r") as f:
            file = f.read()

        with open(fname, mode="w") as f:
            file = file.replace("$table_json", data)
            f.write(file)


def is_log_filename(filename: str) -> str:
    """
    if filename consist "*.log-yyyymmdd" or "*.log-yyyymmdd.gz"
    it returns file extension empty string
    """
    result = re.findall(r"^.*\.(log-\d{8}|log-\d{8}.gz)$", filename)
    try:
        if "." in result[0]:
            return result[0].split(".")[-1]
        return result[0]
    except IndexError:
        return ""


def get_last_log_path(log_dir: str) -> str:
    p = Path(log_dir)
    last_date = date(1970, 1, 1)
    last_log = ""
    ext = ""
    for x in p.iterdir():
        if not x.is_file():
            continue
        result = is_log_filename(x.name)
        if result != "":
            date_str = re.findall(r"^.*\.log-(\d{8})", x.name)
            date_file = datetime.strptime(date_str[0], "%Y%m%d").date()
            if date_file > last_date:
                last_date = date_file
                last_log = str(x)
                ext = "gz" if result[0] == "gz" else ""
    LogInfo = namedtuple("LogInfo", ["path", "date", "ext"])
    return LogInfo(last_log, last_date, ext)


def get_config(config: dict) -> dict:
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    arg_parser.add_argument(
        "--config",
        help="Specify config file",
        nargs="?",
        const=DEFAULT_CONFIG_FILENAME,
        metavar="PATH",
    )

    args, _ = arg_parser.parse_known_args()

    cfg = {k.lower(): v for k, v in config.items()}
    if args.config:
        if Path(args.config).exists():
            config = configparser.ConfigParser()
            config.read([args.config])
            cfg.update(dict(config.items("Global")))
            if type(cfg["report_size"]) is str:
                cfg["report_size"] = int(cfg["report_size"])
        else:
            arg_parser.error(f"The file {args.config} does not exist!")

    return {k.upper(): v for k, v in cfg.items()}


def main():
    global config

    cfg = get_config(config)

    log_stat = LogStat()
    log_info = get_last_log_path(cfg["LOG_DIR"])
    open_fn = gzip.open if log_info.ext == "gz" else open

    with open_fn(log_info.path) as f:
        for line in f:
            log_stat.add_url(line)

    log_stat.calc_sums()
    urls = log_stat.get_sorted_urls_for_report(cfg["REPORT_SIZE"])
    data = log_stat.calc_stat(urls)
    log_stat.render_html(data, "report.html", cfg["REPORT_DIR"])


if __name__ == "__main__":
    main()
