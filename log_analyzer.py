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
from log import get_logger

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ERR_LIMIT": 1,
    "CFG_FNAME": "config.ini",
}


# maximum percent of parse errors, to decide if log successfully parsed
LOG_PARSE_ERRORS_LIMIT = 1

logger = get_logger(__name__)


class LogStat:
    def __init__(self, config: dict) -> None:
        self.log = dict()
        self.report = dict()
        self.par_err_lim = config["ERR_LIMIT"]
        self.stat = {
            "count": 0,
            "time_sum": 0.0,
            "log_lines": 0,
            "par_err": 0,
        }
        self.max_urllen = 0

    def add_url(self, line: str):
        self.stat["log_lines"] += 1
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        start = line.find('"') + 1
        end = line.find('"', start)
        url = line[start:end]

        if not any(method in url for method in http_methods):
            logger.error(f'method not found in "{url}"')
            return
        try:
            url = url.split()[1]
        except IndexError:
            logger.error(f'url has not url in "{url}"')
            return

        time = line[end:].split()[-1]
        time_ = time.replace(".", "")
        if not time_.isnumeric():
            logger.error(f'time is not numeric "{time}"')
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

        parse_errs = 100 * (1 - (self.stat["count"] / self.stat["log_lines"]))
        self.stat["par_err"] = parse_errs
        if parse_errs > self.get_parse_err_limit():
            msg = (
                f"Parse errors exceed the limit of "
                f"{self.get_parse_err_limit()}% "
                f"and are {parse_errs:.1f}%"
            )
            logger.error(msg)
            raise ValueError(msg)
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

    def render_html(self, data, template_fname: str, dest: Path):
        def round_floats(o):
            if isinstance(o, float):
                return round(o, 3)
            if isinstance(o, dict):
                return {k: round_floats(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [round_floats(x) for x in o]
            return o

        data = json.dumps(round_floats(data))
        with open(template_fname, mode="r") as f:
            file = f.read()

        with open(dest, mode="w") as f:
            file = file.replace("$table_json", data, 1)
            f.write(file)

    def get_parse_err_limit(self):
        return self.par_err_lim

    def __str__(self):
        return (
            f'log of {self.stat["log_lines"]} lines\n'
            f'parsed {self.stat["count"]} lines\n'
            f'not parsed {self.stat["par_err"]:.3f} %\n'
        )


def is_log_filename(filename: str) -> str:
    """
    if filename consist "*.log-yyyymmdd" or "*.log-yyyymmdd.gz"
    it returns file extension
    otherwise empty string
    """
    result = re.findall(r"^nginx-access-ui.log-(\d{8}|\d{8}.gz)$", filename)
    try:
        if "." in result[0]:
            return result[0].split(".")[-1]
        return result[0]
    except IndexError:
        return ""


def get_last_log_path(log_dir: str):
    last_date = date(1970, 1, 1)
    last_log, last_date_str, ext = "", "", ""
    LogInfo = namedtuple("LogInfo", ["path", "date", "ext"])
    for x in Path(log_dir).iterdir():
        if not x.is_file():
            continue
        result = is_log_filename(x.name)
        if result != "":
            date_str = re.findall(r"^.*\.log-(\d{8})", x.name)[0]
            date_file = datetime.strptime(date_str, "%Y%m%d").date()
            if date_file > last_date:
                last_date, last_date_str = date_file, date_str
                last_log = str(x)
                ext = "gz" if result[0] == "gz" else ""
    return LogInfo(last_log, last_date_str, ext)


def get_config(cfg_def: dict) -> str:
    """
    update the input config dict by values from file if it exist and parsed
    raise exception when config file hasn`t been parsed
    """
    arg_parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    arg_parser.add_argument(
        "--config",
        help="Specify config file",
        nargs="?",
        const=cfg_def["CFG_FNAME"],
        metavar="PATH",
    )

    args, _ = arg_parser.parse_known_args()

    cfg = {k.lower(): v for k, v in cfg_def.items()}
    if args.config:
        if Path(args.config).exists():
            config = configparser.ConfigParser()
            config.read([args.config])
            cfg.update(dict(config.items("Global")))
            for k, v in cfg_def.items():
                k = k.lower()
                if isinstance(v, int):
                    cfg[k] = int(cfg[k])
                elif isinstance(v, float):
                    cfg[k] = float(cfg[k])
        else:
            logger.error(f"The file {args.config} does not exist!")
            raise FileNotFoundError(f"The file {args.config} does not exist!")

    return {k.upper(): v for k, v in cfg.items()}


def main():
    global config
    logger.info("\nLog analyzer started")
    cfg = get_config(config)
    logger.info(
        f'config: LOG_DIR={cfg["LOG_DIR"]}, '
        f'REPORT_DIR={cfg["REPORT_DIR"]}, '
        f'REPORT_SIZE={cfg["REPORT_SIZE"]}, '
        f'ERR_LIMIT={cfg["ERR_LIMIT"]}'
    )

    log_info = get_last_log_path(cfg["LOG_DIR"])
    if log_info.path == "":
        logger.info("Log files not found")
        print("Log files not found")
        return

    rep_path = Path(cfg["REPORT_DIR"]) / f"report-{log_info.date}.html"
    if rep_path.exists():
        print("Latest report already exist")
        return

    log_stat = LogStat(cfg)
    open_fn = gzip.open if log_info.ext == "gz" else open
    with open_fn(log_info.path) as f:
        for line in f:
            log_stat.add_url(line)

    log_stat.calc_sums()
    urls = log_stat.get_sorted_urls_for_report(cfg["REPORT_SIZE"])
    data = log_stat.calc_stat(urls)
    log_stat.render_html(data, "report.html", rep_path)

    logger.info("render completed:")
    logger.info(f"\n{log_stat}")
    print(("Render completed\n"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(e)
        print(e)
