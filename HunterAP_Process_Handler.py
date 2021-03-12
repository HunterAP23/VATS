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
from typing import AnyStr, Dict, List, Optional, Set, Tuple

class HunterAP_Process_Handler_Error(Exception):
    pass


class HunterAP_Handler_Handler:
    def __init__(self, max_procs: Optional[int], max_threads: Optional[int], funcs: Optional[Dict]):
        self.pid = os.getpid()
        self.core_count = mp.cpu_count()
        self.usable_cores_count = None

        if sys.platform.startswith("freebsd"):
            self.sys_platform = "FreeBSD"
        elif sys.platform.startswith("linux"):
            self.sys_platform = "Linux"
        elif sys.platform.startswith("aix"):
            self.sys_platform = "AIX"
        elif sys.platform.startswith("win32"):
            self.sys_platform = "Windows"
            import win32api, win32con, win32process
        elif sys.platform.startswith("darwin"):
            self.sys_platform = "MacOS"

        ret = plat.uname()
        self.platform_system = ret[0]
        self.platform_node = ret[1]
        self.platform_release = ret[2]
        self.platform_version = ret[3]
        self.platform_machine = ret[4]
        self.platform_cpu = ret[5]
        del ret

        if self.sys_platform != "Windows":
            self.usable_cores = os.sched_getaffinity(0)
            self.usable_cores_count = len(self.usable_cores)
        else:
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, self.pid)
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

            self.usable_cores = set(temp_cores_proc)
            self.usable_cores_sys = set(temp_cores_sys)
            self.usable_cores_count = len(self.usable_cores)

        ret = plat.python_version_tuple()
        self.python_version_major = ret[0]
        self.python_version_minor = ret[1]
        self.python_version_patch = ret[2]

        check = (max_procs is None, max_procs == 0)
        if self.usable_cores_count is not None:
            if any(check) or max_procs >= self.core_count:
                self.pool_proc = mp.Pool(self.core_count)
            elif max_procs < self.core_count:
                self.pool_proc = mp.Pool(max_procs)
        else:
            if any(check) or max_procs >= self.usable_cores_count:
                self.pool_proc = mp.Pool(self.usable_cores_count)
            elif max_procs < self.usable_cores_count:
                self.pool_proc = mp.Pool(max_procs)

    def get_pid(self):
        return self.pid

    def get_affinity(self):
        return self.usable_cores
