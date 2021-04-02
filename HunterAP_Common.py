import configparser as confp
import sys
import datetime as dt


def print_dict(item, tablevel=1):
    types = [int, float, bool, str]
    for key, val in item.items():
        iter = None
        if type(val) == dict:
            print("{0}{1}".format("\t" * (tablevel - 1), key))
            iter = val
        elif type(val) in types or val is None:
            print("{0}{1}: {2}".format("\t" * tablevel, str(key).ljust(10), val))
            continue
        else:
            print("{0}{1}".format("\t" * (tablevel - 1), key))
            iter = vars(val)

        for k, v in iter.items():
            if type(v) == dict or type(v) == confp.SectionProxy:
                print("{0}{1}".format("\t" * tablevel, k))
                print_dict(v, tablevel + 1)
            elif type(v) == list:
                print("{0}{1}".format("\t" * tablevel, k))
                for i in v:
                    print("{0}{1}".format("\t" * (tablevel + 1), i))
            else:
                print("{0}{1}: {2}".format("\t" * tablevel, str(k).ljust(10), v))


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class HunterAP_Timer:
    def __init__(self):
        self._start = None
        self._end = None
        self._runtime = None

    def start(self):
        self._start = dt.datetime.now()

    def end(self):
        self._end = dt.datetime.now()
        self._runtime = (self._end - self._start).total_seconds()

    def get_start(self):
        return self._start

    def get_end(self):
        return self._end

    def get_runtime(self):
        return self._runtime

    def get_runtime_formatted(self):
        seconds = self._runtime % 3600 % 60
        minutes = (self._runtime - seconds) % 3600 / 60
        hours = (self._runtime - seconds - (minutes * 60)) / 3600 / 60 % 24
        days = (self._runtime - seconds - (minutes * 60) - (hours * 3600)) / 3600 / 60 / 24
        weeks = (self._runtime - seconds - (minutes * 60) - (hours * 3600) - (days * 24)) / 3600 / 60 / 24 / 7
        msg = ""
        if weeks > 0:
            msg += "{} weeks, ".format(int(weeks))
        if days > 0:
            msg += "{} days, ".format(int(days))
        if hours > 0:
            msg += "{} hours, ".format(int(hours))
        if minutes > 0:
            msg += "{} minutes, ".format(int(minutes))
        msg += "{} seconds, ".format(seconds)
        print(msg)
