# Process related
import multiprocessing as mp
import subprocess as sp

# Scheduling related
import sched
import time

# System related
import os
import platform as plat
import sys

# Debugging related
import errno
import inspect
import traceback

# Miscellaneous
from typing import AnyStr
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple


class HunterAP_Process_Handler_Error(Exception):
    pass


class HunterAP_Process_Handler:
    def __init__(self, max_procs: Optional[int] = 1, max_threads: Optional[int] = 1, funcs: Optional[Dict] = {}):
        self._pid = os.getpid()
        self._core_count = mp.cpu_count()
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
                print("max_procs: {}".format(max_procs))
                try:
                    self._pool_proc = mp.Pool(max_procs)
                except Exception as e:
                    print(e)
                    inp = input("Wait...")
        else:
            if any(check) or max_procs >= self._usable_cores_count:
                self._pool_proc = mp.Pool(self._usable_cores_count)
            elif max_procs < self._usable_cores_count:
                self._pool_proc = mp.Pool(max_procs)

    # def get_pid(self):
    #     return self._pid
    #
    # def get_affinity(self):
    #     return self._usable_cores

    def _get_sys_platform(self):
        return self._sys_platform

    def _get_core_count(self):
        return self._core_count

    def _time_function(self, func, i: int, sema, rlock):
        sema.acquire()
        func(i, sema)
        sema.release()

    def _run_in_parallel(self, fn, threads: int, lis: list, sema, rlock):
        proc = []
        for i in lis:
            p = mp.Process(target=self._time_function, args=(fn, i, sema, rlock))
            proc.append(p)

        for p in proc:
            p.start()

        for p in proc:
            try:
                p.join()
            except Exception as e:
                print(e)
