import argparse as argp
import multiprocessing as mp
import os
import shlex
import subprocess as sp
import time

import ffmpy
import numpy as np

from config_handler import Config_Handler


class VMAF_Calculator:
    """Calculates VMAF and other visual score metric values using FFmpeg with multithreading and multiprocessing."""
    def __init__(self):
        # Parse arguments given by the user, if any
        self.args = self.parse_arguments()

        # Create a Config_Reader object with the config file.
        conf_reader = Config_Handler(self.args)
        self.config = conf_reader.get_config_data()

        self.validate_options()

        if self.args.vmaf_version:
            self.vmaf_version = self.args.vmaf_version
        else:
            self.vmaf_version = self.config["Calculations"]["vmaf_version"]

        if self.args.psnr:
            self.psnr = self.args.psnr
        else:
            self.psnr = self.config["Calculations"]["psnr"]

        if self.args.ssim:
            self.ssim = self.args.ssim
        else:
            self.ssim = self.config["Calculations"]["ssim"]

        if self.args.ms_ssim:
            self.ms_ssim = self.args.ms_ssim
        else:
            self.ms_ssim = self.config["Calculations"]["ms_ssim"]

        if self.args.model:
            self.model = self.args.model
        else:
            self.model = self.config["Calculations"]["model"]

        if self.args.log:
            self.log = self.args.log
        else:
            self.log = self.config["Calculations"]["log_format"]

        for k, v in dict(vars(self)).items():
            if k == "args" or k == "config":

                self.print_dict(v)
            else:
                print("{0}: {1}".format(k, v))

    def print_dict(self, key, val):
        print(key)
        for k, v in val.items():
            if type(v) == dict:
                print(k)
                self.print_dict(v)
            elif type(v) == list:
                print(k)
                for i in v:
                    print(i)
            else:
                print("{0}: {1}".format(k, v))

    def validate_options(self):
        """Validate all user specified, config-specified, and remaining default options."""
        def validate_threads(self):
            if len(os.sched_getaffinity(0)) != mp.cpu_count()
            try:
                if self.args.threads:
                    if self.args.threads > mp.cpu_count():
                        raise ValueError

            try:
                try:
                    if self.config["Calculations"]["threads"] > mp.cpu_count():
                        raise ValueError("ERROR: User specified {0} threads which is more than the number the system supports ({1}), clamping the value to the available number of threads on this system.".format(self.args.threads, mp.cpu_count()))
                        self.args.threads = mp.cpu_count()

                except KeyError as ke:
                    print(ke)
                    self.args.threads = mp.cpu_count()
            except KeyError as ke:
                print(ke)
                self.threads = 0

        def validate_instances(self):
            try:
                if self.config["Calculations"]["instances"] is not None:
                    return
            except KeyError as ke:
                print(ke)
                self.instances = 1

        def validate_processes(self):
            return

        self.validate_threads()

        self.validate_instances()

        self.validate_processes()


    def parse_arguments(self):
        """Parse user given arguments for calculating VMAF."""
        main_help = "Multithreaded VMAF report file generator through FFmpeg.\n"
        main_help += "The 1st required argument is the Distorted Video file.\n"
        main_help += "The 2nd required argument is the Reference Video file that the Distorted Video is compared against.\n"
        parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False)
        parser.add_argument("Distorted_File", type=str, help="Distorted video file.")
        parser.add_argument("Reference_File", type=str, help="Reference video file.")

        optional_args = parser.add_argument_group("Optional arguments")
        ffmpeg_help = "Specify the path to the FFmpeg executable (Default is \"ffmpeg\" which assumes that FFmpeg is part of your \"Path\" environment variable).\n"
        ffmpeg_help += "The path must either point to the executable itself, or to the directory that contains the exectuable named \"ffmpeg\"."
        optional_args.add_argument("-f", "--ffmpeg", dest="ffmpeg", help=ffmpeg_help)

        threads_help = "Specify number of threads (Default is 0 for \"autodetect\").\n"
        threads_help += "Specifying more threads than there are available will clamp the value down to the maximum number of threads on the system.\n"
        threads_help += "A single VMAF instance will effectively max out at 12 threads - any more will provide little to no performance increase."
        optional_args.add_argument("-t", "--threads", dest="threads", type=int, help=threads_help)

        inst_help = "Specify number of simultaneous VMAF calculation instances to run (Default is 1).\n"
        inst_help += "Specifying more instances than there are available will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n"
        optional_args.add_argument("-i", "--instances", dest="instances", type=int, help=inst_help)

        vmaf_version_help = "Specify the VMAF version to use (Default is 2).\n"
        optional_args.add_argument("-v", "--vmaf_version", dest="vmaf_version", type=int, choices=[1, 2], help=vmaf_version_help)

        psnr_help = "Enable calculating PSNR values (Default is off).\n"
        optional_args.add_argument("-p", "--psnr", dest="psnr", action="store_true", help=psnr_help)

        ssim_help = "Enable calculating SSIM values (Default is off).\n"
        optional_args.add_argument("-s", "--ssim", dest="ssim", action="store_true", help=ssim_help)

        ms_ssim_help = "Enable calculating MS-SSIM values (Default is off).\n"
        optional_args.add_argument("-ms", "--ms_ssim", dest="ms_ssim", action="store_true", help=ms_ssim_help)

        model_help = "Specify the VMAF model file to use (Default is \"vmaf_v0.6.1.pkl\" for VMAF version 1 and \"vmaf_v0.6.1.json\" for VMAF version 2).\n"
        model_help += "By default, this variable assumes the model file is located in the same location as this script."
        optional_args.add_argument("-m", "--model", dest="model", help=model_help)

        log_help = "Specify the VMAF output log format (Default is \"xml\").\n"
        optional_args.add_argument("-l", "--log", dest="log", choices=["xml", "csv", "json"], help=log_help)

        config_help = "Specify a config file to import multiple settings with (Default is \"config.ini\" in the same folder as the script).\n"
        config_help += "Values specified with the arguments above will override the settings in the config file."
        optional_args.add_argument("-c", "--config", dest="config", help=config_help)

        misc_args = parser.add_argument_group("Miscellaneous arguments")
        misc_args.add_argument("-h", "--help", action="help", default=argp.SUPPRESS, help="Show this help message and exit.\n")

        args = parser.parse_args()
        return args

    def time_function(self, func, i: int, sema, rlock):
        sema.acquire()
        func(i, sema)
        sema.release()

    def run_in_parallel(self, fn, threads: int, lis: list, sema, rlock):
        proc = []
        for i in lis:
            p = mp.Process(target=self.time_function, args=(fn, i, sema, rlock))
            proc.append(p)

        for p in proc:
            p.start()

        for p in proc:
            try:
                p.join()
            except Exception as e:
                print(e)

    def multi_vmaf(self, i, sema):
        command = "ffmpeg -i {0}"
        sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)


if __name__ == "__main__":
    calculator = VMAF_Calculator()
    # threads = 2
    # manager = mp.Manager()
    # sema = mp.Semaphore(threads)
    # rlock = manager.RLock()
    # lis = manager.list()
    #
    # files_list = []
    #
    # # for root, directories, filenames in os.walk():
    #
    # run_in_parallel(boring_task, threads, lis, sema, rlock)
