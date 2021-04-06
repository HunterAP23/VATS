# Process related
import asyncio
import multiprocessing as mp
import multiprocessing.dummy as mpd
import subprocess as sp

# Scheduling related
import sched

# System related
import os
import platform as plat
import sys

# Debugging related
import errno
import inspect
import logging as lg
import traceback

# Miscellaneous
from typing import Optional
from typing import Union


class HunterAP_Process_Handler_Error(Exception):
    pass


class HunterAP_Process_Handler:
    def __init__(self, log: lg.RootLogger, max_procs: Optional[int] = 1, max_threads: Optional[int] = 1, funcs: Optional[Union[dict, list, set, tuple]] = None, args: Optional[Union[dict, list, set, tuple]] = None):
        self._log = log
        self._max_threads = max_threads
        self._max_procs = max_procs
        self._funcs = funcs
        self._args = args

        self._pid = os.getpid()
        self._core_count = mp.cpu_count()
        self._usable_cores = None
        self._usable_cores_count = None

        if sys.platform.startswith("freebsd"):
            self._sys_platform = "FreeBSD"
        elif sys.platform.startswith("linux"):
            self._sys_platform = "Linux"
        elif sys.platform.startswith("aix"):
            self._sys_platform = "AIX"
        elif sys.platform.startswith("win32"):
            self._sys_platform = "Windows"
            import win32api
            import win32con
            import win32process
        elif sys.platform.startswith("darwin"):
            self._sys_platform = "MacOS"

        ret = plat.uname()
        self._platform_system = ret[0]
        self._platform_node = ret[1]
        self._platform_release = ret[2]
        self._platform_version = ret[3]
        self._platform_machine = ret[4]
        self._platform_cpu = ret[5]
        del ret

        if self._sys_platform != "Windows":
            self._usable_cores = os.sched_getaffinity(0)
            self._usable_cores_count = len(self._usable_cores)
        else:
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, self._pid)
            mask = win32process.GetProcessAffinityMask(handle)
            mask_proc = mask[0]
            mask_sys = mask[1]
            bitmask_proc = "{0:08b}".format(mask_proc)
            bitmask_sys = "{0:08b}".format(mask_sys)

            temp_cores_proc = []
            temp_cores_sys = []

            for i in range(len(bitmask_proc)):
                x = list(reversed(bitmask_proc))[i]
                if int(x):
                    temp_cores_proc.append(i)

            for i in range(len(bitmask_sys) - 1, -1, -1):
                x = list(reversed(bitmask_sys))[i]
                if int(x):
                    temp_cores_sys.append(i)

            self._usable_cores = set(temp_cores_proc)
            self._usable_cores_sys = set(temp_cores_sys)
            self._usable_cores_count = len(self._usable_cores)

        ret = plat.python_version_tuple()
        self._python_version_major = ret[0]
        self._python_version_minor = ret[1]
        self._python_version_patch = ret[2]

        check = (max_procs is None, max_procs == 0)
        if self._usable_cores_count is not None:
            if any(check) or max_procs >= self._core_count:
                self._pool_proc = mp.pool.Pool(self._core_count)
            elif max_procs < self._core_count:
                if max_procs == 0:
                    max_procs = 1
                try:
                    self._pool_proc = mp.Pool(max_procs)
                except Exception as e:
                    self._log.error(e)
        else:
            if any(check) or max_procs >= self._usable_cores_count:
                self._pool_proc = mp.Pool(self._usable_cores_count)
            elif max_procs < self._usable_cores_count:
                self._pool_proc = mp.Pool(max_procs)

    def _test_callable(self, name, method):
        try:
            if callable(method):
                return True
            else:
                msg = "{} is not a callable method and will be removed from the pool."
                raise TypeError(msg.format(name))
        except TypeError as te:
            self._log.error(te)
            return False

    def _run_in_parallel(self, funcs: Union[dict, list, tuple], args: Union[dict, list, tuple], threads: int, sema: mp.Semaphore, rlock: mp.RLock):
        # proc = []
        # for func in funcs:
        #     p = mp.Process(target=self._time_function, args=(func, args[func], sema, rlock))
        #     proc.append(p)
        #
        # for p in proc:
        #     p.start()
        #
        # for p in proc:
        #     try:
        #         p.join()
        #     except Exception as e:
        #         self._log.error(e)
        funcs_data = dict()
        try:
            if type(funcs) is dict:
                if len(funcs) == 1:
                    (name, func), = funcs.items()
                    if self._test_callable(name, func):
                        funcs_data[name] = dict()
                        funcs_data[name]["Function"] = func
                    else:
                        raise IndexError()
                else:
                    for name, func in funcs.items():
                        if self._test_callable(name, func):
                            funcs_data[name] = dict()
                            funcs_data[name]["Function"] = func
                    if len(funcs_data) == 0:
                        raise IndexError()
            elif type(args) in (list, tuple):
                if len(funcs) == 1:
                    func = funcs[0]
                    name = func.__name__
        except IndexError as ie:
            msg = "{}: There are no valid functons given from arguments {} and {}."
            self._log.critical(msg.format(ie, funcs, args))
            exit(1)

        arg = None
        if name in args.keys():
            arg = args[name]
        elif func.__name__ in args:
            arg = args[func.__name__]

        self._run_map(func)

    def _run_map(self, func, args, name: Optional[str]):
        return

    def _time_function(self, func, args: Union[dict, list, set, tuple], sema, rlock):
        sema.acquire()
        func(**args, sema=sema)
        sema.release()

    def get_pid(self) -> int:
        return self._pid

    def get_affinity(self) -> Union[list, tuple]:
        return self._usable_cores

    def set_affinity(self, affinity: Union[list, tuple]) -> bool:
        # Remove duplicate entries
        new_affinity = set(affinity)

        # Make sure there are elements
        if len(new_affinity) == 0:
            return False

        # Get rid of any elements greater than the highest core number
        while max(new_affinity) > max(self._usable_cores):
            new_affinity.discard(max(new_affinity))

        # Make sure there are no entries less than 0
        while 0 in new_affinity:
            new_affinity.discard(min(new_affinity))

        # Make sure we still have elements after removing the above values
        if len(new_affinity) == 0:
            return False

            self._usable_cores = tuple(new_affinity)
            return True

    def get_sys_platform(self) -> str:
        return self._sys_platform

    def get_core_count(self) -> int:
        return self._core_count

    def get_threads(self) -> int:
        return self._max_threads

    def set_threads(self, threads: int) -> bool:
            return self._max_threads

    def get_args(self):
        return self._args

    def set_args(self, args: Union[dict, list, set, tuple]) -> bool:
        return True

    def get_funcs(self):
        return self._funcs

    def set_funcs(self, funcs: Union[dict, list, set, tuple]) -> bool:
        if type(funcs) in (list, tuple):
            self._funcs = set()
        return True

    def get_args(self):
        return self._args

    def set_args(self, args: Union[dict, list, set, tuple]) -> bool:
        return True


# if __name__ == "__main__":
#     inst = HunterAP_Process_Handler()
#     for k, v in vars(inst).items():
#         print("{}: {}".format(k, v))
