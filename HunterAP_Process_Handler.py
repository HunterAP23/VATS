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
import shlex
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
    def __init__(self, log: lg.RootLogger, procs: Optional[list, set, tuple] = [0], threads: Optional[list, set, tuple] = [0], funcs: Optional[Union[dict, list, set, tuple]] = None, args: Optional[Union[dict, list, set, tuple]] = None):
        self._log = log

        ret = plat.uname()
        self._platform_system = ret[0]
        self._platform_node = ret[1]
        self._platform_release = ret[2]
        self._platform_version = ret[3]
        self._platform_machine = ret[4]
        self._platform_cpu = ret[5]

        ret = plat.python_version_tuple()
        self._python_version_major = ret[0]
        self._python_version_minor = ret[1]
        self._python_version_patch = ret[2]

        del ret

        # Save this Python process' PID for future use.
        self._pid = os.getpid()
        # Get the reported number of CPU cores
        self._cores_count = mp.cpu_count()
        # For saving count of CPU sockets in systems, mostly for multi-socket use
        self._sockets_count = 0
        # Which cores are usable, based on the affinity for this process
        self._cores_usable = None
        # Number of usable cores
        self._cores_usable_count = None
        # List of physical cores - typically even numbered starting at 0
        self._cores_physical = []
        # List of logical cores - typically odd numbered starting at 1
        self._cores_logical = []
        # Whether the system has Simultaneous Multithreading / Hyperthreading
        # This is a list for measuring SMT on multiple sockets,
        self._smt = []

        if sys.platform.startswith("freebsd"):
            self._sys_platform = "FreeBSD"
        elif sys.platform.startswith("linux"):
            self._sys_platform = "Linux"
            self._get_info_linux()
        elif sys.platform.startswith("aix"):
            self._sys_platform = "AIX"
        elif sys.platform.startswith("win32"):
            self._sys_platform = "Windows"
            import win32api
            import win32com
            import win32con
            import win32process
            self._get_info_windows()
        elif sys.platform.startswith("darwin"):
            self._sys_platform = "MacOS"
            self._get_info_macos()

        self._threads = 1
        self._procs = 1
        self._threads = self.set_threads(threads)
        self._procs = self.set_procs(procs)
        self._funcs = self.set_funcs(funcs)
        self._args = self.set_args(args)

    def _get_info_freebsd(self):
        int(os.popen("sysctl -n hw.ncpu").readlines()[0])

    def _get_info_linux(self):
        self._cores_usable = os.sched_getaffinity(0)
        self._cores_usable_count = len(self._cores_usable)
        with open("/proc/cpuinfo") as cpu_info:
            for line in [line.split(":") for line in cpu_info.readlines()]:
                if (line[0].strip() == "physical id"):
                    sockets = np.maximum(sockets, int(line[1].strip()) + 1)
                if (line[0].strip() == "cpu cores"):
                    cores_per_socket = int(line[1].strip())

    # INCOMPLETE - NEEDS TESTING ON MAC OS
    def _get_info_macos(self):
        tmp_dict = dict()
        check = [
            "ncpu",
            "activecpu",
            "physicalcpu",
            "physicalcpu_max",
            "logicalcpu",
            "logicalcpu_max"
        ]
        cmd = shlex.split("sysctl hw")
        ret = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = ret.communicate()
        for line in out:
            for item in line.split(":"):
                key = item[0].replace(" ", "").replace("\"", "").strip("hw.").lower()
                value = item[1].strip(".\n ")
                if key in check:
                    tmp_dict[key] = value

    def _get_info_windows(self):
        # Get simultaneous multithreading info
        winmgmts_root = win32com.client.GetObject("winmgmts:root\\cimv2")
        cpus = winmgmts_root.ExecQuery("Select * from Win32_Processor")
        for cpu in cpus:
            self._socket_count += 1
            self._cores_physical.append(cpu.NumberOfCores)
            self._cores_logical.append(cpu.NumberOfLogicalProcessors)
            if cpu.NumberOfCores < cpu.NumberOfLogicalProcessors:
                self._smt.append(True)

        # Get affinity info
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

        self._cores_usable = set(temp_cores_proc)
        self._cores_usable_sys = set(temp_cores_sys)
        self._cores_usable_count = len(self._cores_usable)

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

    def _time_function(self, func, args: Union[dict, list, set, tuple], sema, rlock) -> bool:
        ret = dict()
        ret["Success"] = False
        was_acquired = False
        try:
            was_acquired = True
            sema.acquire()
            ret["return"] = func(**args, sema=sema)
            sema.release()
            was_acquired = False
            ret["Success"] = True
            return ret
        except Exception as e:
            if was_acquired:
                sema.release()
            ret["Success"] = False
            self._log.error(e)
            return ret

    def _validate_threads_processes(self, threads: Optional[int], processes: Optiona[int]) -> bool:
        tmp_threads = None
        tmp_procs = None
        if threads:
            tmp_threads = threads
        else:
            tmp_threads = self._threads

        if procs:
            tmp_procs = procs
        else:
            tmp_procs = self._procs

        if tmp_threads * tmp_procs > self._cores_usable_count:
            return False
        return True

    def create_pool(self):
        check = (self._procs is None, self._procs == 0)
        if self._cores_usable_count is not None:
            if any(check) or procs >= self._core_count:
                self._pool_proc = mp.pool.Pool(self._core_count)
            elif procs < self._core_count:
                if procs == 0:
                    procs = 1
                try:
                    self._pool_proc = mp.Pool(procs)
                except Exception as e:
                    self._log.error(e)
        else:
            if any(check) or max_procs >= self._cores_usable_count:
                self._pool_proc = mp.Pool(self._cores_usable_count)
            elif max_procs < self._cores_usable_count:
                self._pool_proc = mp.Pool(max_procs)

    def get_affinity(self) -> Union[list, set, tuple]:
        return self._cores_usable

    def set_affinity(self, affinity: Union[list, tuple]) -> bool:
        # Remove duplicate entries
        new_affinity = set(affinity)

        # Make sure there are elements
        if len(new_affinity) == 0:
            return False

        # Get rid of any elements greater than the highest core number
        while max(new_affinity) > max(self._cores_usable):
            new_affinity.discard(max(new_affinity))

        # Make sure there are no entries less than 0
        while 0 in new_affinity:
            new_affinity.discard(min(new_affinity))

        # Make sure we still have elements after removing the above values
        if len(new_affinity) == 0:
            return False

            self._cores_usable = tuple(new_affinity)
            return True

    def get_cores_count(self) -> int:
        return self._core_count

    def get_cores_count(self) -> int:
        return self._core

    def get_pid(self) -> int:
        return self._pid

    def get_sys_platform(self) -> str:
        return self._sys_platform

    def get_threads(self) -> int:
        return self._threads

    def set_threads(self, threads: int) -> bool:
        if self._validate_threads_processes(threads=threads):
            self._threads = threads
            return True
        return False

    def get_procs(self) -> int:
        return self._procs

    def set_procs(self, procs: int) -> bool:
        if self._validate_threads_processes(procs=procs):
            self._procs = procs
            return True
        return False

    def get_funcs(self) -> Union[dict, list, set, tuple]:
        return self._funcs

    def set_funcs(self, funcs: Union[dict, list, set, tuple]) -> bool:
        if type(funcs) in (list, tuple):
            self._funcs = set()
        return True

    def add_funcs(self, funcs: Union[dict, list, set, tuple]) -> bool:
        return True

    def get_args(self) -> Union[dict, list, set, tuple]:
        return self._args

    def set_args(self, args: Union[dict, list, set, tuple]) -> bool:
        return True


# if __name__ == "__main__":
#     inst = HunterAP_Process_Handler()
#     for k, v in vars(inst).items():
#         print("{}: {}".format(k, v))
