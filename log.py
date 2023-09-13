import logging
from datetime import datetime
from functools import lru_cache


@lru_cache
def get_logger(module_name, level=logging.INFO):
    logger = logging.getLogger(module_name)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh = logging.FileHandler(f"log-{datetime.now():%Y-%m-%d}.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(level)
    return logger
