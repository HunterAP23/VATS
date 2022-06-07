# import concurrent.futures as cf
import configparser as confp
import datetime as dt
import sys
from itertools import chain
from pathlib import Path
from string import digits
from typing import Iterable, Literal, Optional, Union


def print_dict(
    item,
    tablevel=0,
    show_hidden=False,
):
    for key, val in item.items():
        # if type(key) is str and key.startswith("__"):
        #     continue

        iter = None
        if type(val) in (dict, confp.SectionProxy):
            print("{0}{1}:".format("\t" * tablevel, key))
            iter = dict(val)
        elif type(val) in [int, float, bool, str] or val is None:
            print("{0}{1}: {2}".format("\t" * tablevel, key, val))
            continue
        else:
            if type(val) in (list, set, tuple):
                print("{0}{1}: {2}".format("\t" * tablevel, key, str(val).ljust(10)))
                continue
            else:
                if hasattr(val, "__dict__"):
                    print("{0}{1}:".format("\t" * tablevel, key))
                    iter = vars(val)
                else:
                    print("{0}{1}: {2}".format("\t" * tablevel, key, str(val).ljust(10)))
                    continue

        for k, v in sorted(iter.items()):
            # if k.startswith("__"):
            #     continue

            if type(v) in (dict, confp.SectionProxy):
                print("{0}{1}:".format("\t" * (tablevel + 1), str(k).ljust(10)))
                print_dict(v, tablevel + 2)
            elif type(v) in (list, set, tuple):
                # print("{0}{1}:".format("\t" * (tablevel + 1), str(k).ljust(10)))
                # for i in v:
                #     print("{0}{1}".format("\t" * (tablevel + 2), str(i).ljust(10)))
                print("{0}{1}: {2}".format("\t" * tablevel, k, str(v).ljust(10)))
            elif type(v) == type:
                print("{0}{1}: {2}".format("\t" * (tablevel + 1), str(k).ljust(10), str(v).ljust(10)))
            elif callable(v):
                try:
                    print("{0}{1}: {2}".format("\t" * (tablevel + 1), str(k).ljust(10), str(v()).ljust(10)))
                except Exception:
                    print("{0}{1}: {2}".format("\t" * (tablevel + 1), str(k).ljust(10), str(v).ljust(10)))
            else:
                print("{0}{1}: {2}".format("\t" * (tablevel + 1), str(k).ljust(10), str(v).ljust(10)))


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_glob_from_ext(ext: str) -> str:
    pattern_parts = []
    ext = ext.rstrip(".")
    for c in ext:
        if c in digits:
            pattern_parts.append(c)
        else:
            c_lower, c_upper = c.lower(), c.upper()
            if c_lower == c_upper:
                pattern_parts.append(c)
            else:
                pattern_parts.append("[{}{}]".format(c_lower, c_upper))
    return "*." + "".join(pattern_parts)


def find_by_exts(
    loc: Union[str, Path],
    exts: Iterable[str],
    rec=False,
    should_print: Optional[bool] = True,
) -> Iterable[Union[str, Path]]:
    globs = map(build_glob_from_ext, exts)
    if rec:
        for loc in chain.from_iterable(map(Path(loc).rglob, globs)):
            if should_print:
                print("Found file {}".format(loc))
            yield str(loc).replace("\\", "/")
    else:
        for loc in chain.from_iterable(map(Path(loc).glob, globs)):
            if should_print:
                print("Found file {}".format(loc))
            yield str(loc).replace("\\", "/")


def search_handler(
    item,
    search_for: Literal[
        "reference",
        "encoded",
        "model",
        "report",
    ] = "reference",
    recurse: Optional[bool] = False,
):
    item_path = Path(item)
    if item_path.exists():
        # When searching for reference file
        if search_for == "reference":
            if item_path.is_dir():
                raise OSError('ERROR: Reference argument must be a file, but "{}" is a directory.'.format(item))
            return
        # When searching for encoded video files
        elif search_for == "encoded":
            print("looking inside {}".format(item_path))
            if item_path.is_dir():
                # Scan for MKV and MP4 files
                return list(find_by_exts(item_path, exts=["mkv", "mp4"], rec=recurse, should_print=False))
            # If the given dist is a file, return it
            elif item_path.is_file():
                # Naive method of checking if the file is a video
                if item_path.suffix.lower() in [".mkv", ".mp4"]:
                    return [
                        item_path,
                    ]
                else:
                    print("Encoded file {} is not a video file.".format(item))
        # When searching for VMAF model file
        elif search_for == "model":
            if item_path.is_dir():
                print('VMAF model should be a file, but "{}" is a directory.'.format(item))
            elif item_path.is_file():
                # Naive method of checking if the file is a VMAF model
                ext = item_path.suffix.lower()
                if ext == ".json":
                    return [
                        item,
                    ]
                else:
                    print("VMAF model file {} is not valid.".format(item))
                    return
        # When searching for VMAF reports
        elif search_for == "report":
            if item_path.is_dir():
                tmp_reports = list(
                    find_by_exts(item_path, exts=["xml", "json", "txt"], rec=recurse, should_print=False)
                )
                return list(
                    [report for report in tmp_reports if "aggregate" not in report and "statistics" not in report]
                )
                # print('VMAF report should be a file, but "{}" is a directory.'.format(item))
            elif item_path.is_file():
                # Naive method of checking if the file is a VMAF report
                ext = item_path.suffix.lower()
                if ext in [".xml", ".json", ".txt"]:
                    return [
                        item,
                    ]
                else:
                    print("VMAF model file {} is not valid.".format(item))
                    return
    else:
        # If item does not exist, raise an OSError
        raise OSError("ERROR: Could not find {} file {}".format(search_for, item))


def bytes2human(
    n,
    format="%(value).1f%(symbol)s",
):
    """Used by various scripts. See:
    http://goo.gl/zeJZl
    >>> bytes2human(10000)
    '9.8K'
    >>> bytes2human(100001221)
    '95.4M'
    """
    symbols = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)


class VMAF_Timer:
    def __init__(self):
        self._start = dt.datetime.now()
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
        msg += "{} seconds".format(seconds)
        return msg
