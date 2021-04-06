# Native Libraries
import datetime as dt
import logging as lg
from pathlib import Path
import sys
from typing import Optional


# Levels:
# 0 -> DEBUG
# 1 -> INFO
# 2 -> WARNING
# 3 -> ERROR
# 4 -> CRITICAL
class HunterAP_Logger():
    def __init__(self, name: Optional[str] = "log", debug: Optional[bool] = False):
        self._debug = debug
        self._name = name

        tmp_path = Path(__file__).parent
        cur_dt = dt.datetime.now()
        tmp_name = "{}_{}_{:02d}_{:02d}_{}-{}-{}.log".format(
            self._name,
            cur_dt.year,
            cur_dt.month,
            cur_dt.day,
            cur_dt.hour,
            cur_dt.minute,
            cur_dt.second
        )
        log_name = tmp_path.joinpath(tmp_name)

        self._log = lg.getLogger()

        c_handler = lg.StreamHandler(sys.stdout)
        f_handler = lg.FileHandler(log_name)

        if self._debug:
            c_handler.setLevel(lg.DEBUG)
            f_handler.setLevel(lg.DEBUG)
        else:
            c_handler.setLevel(lg.INFO)
            f_handler.setLevel(lg.INFO)

        handler_fmt = {
            "fmt": "%(asctime)s [%(levelname)s]: %(message)s",
            "datefmt": "%Y-%m-%d_%H:%M:%S"
        }
        c_format = lg.Formatter(**handler_fmt)
        f_format = lg.Formatter(**handler_fmt)
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        self._log.addHandler(c_handler)
        self._log.addHandler(f_handler)

        self._log.setLevel(lg.NOTSET)

    def get_debug(self):
        return self._debug

    def debug(self, message, *args, **kwargs):
        return self._log.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        return self._log.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        return self._log.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        return self._log.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        return self._log.critical(message, *args, **kwargs)
