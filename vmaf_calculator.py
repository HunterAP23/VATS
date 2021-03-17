import argparse as argp
import multiprocessing as mp
import os
import shlex
import subprocess as sp
import time

import ffmpy
import numpy as np

from vmaf_config_handler import VMAF_Config_Handler
from HunterAP_Process_Handler import HunterAP_Process_Handler as proc_handler
from HunterAP_Process_Handler import HunterAP_Process_Handler_Error
from HunterAP_Common import print_dict


class VMAF_Calculator:
    """Calculates VMAF and other visual score metric values using FFmpeg with multithreading and multiprocessing."""
    def __init__(self):
        self.mp_handler = proc_handler()

        # Parse arguments given by the user, if any
        self.args = self.parse_arguments()


        # Create a Config_Reader object with the config file.
        self.config = VMAF_Config_Handler(self.args, mp_handler=self.mp_handler).get_config_data()

        print_dict(self.config)

        # self.Proccer = HunterAP_Process_Handler(
        #     max_procs=self.
        # )

    def parse_arguments(self):
        """Parse user given arguments for calculating VMAF."""
        main_help = "Multithreaded VMAF log file generator through FFmpeg.\n"
        main_help += "The 1st required argument is the Distorted Video file.\n"
        main_help += "The 2nd required argument is the Reference Video file that the Distorted Video is compared against.\n"
        parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False)
        parser.add_argument("Distorted_File", type=str, help="Distorted video file.")
        parser.add_argument("Reference_File", type=str, help="Reference video file.")

        optional_args = parser.add_argument_group("Optional arguments")
        ffmpeg_help = "Specify the path to the FFmpeg executable (Default is \"ffmpeg\" which assumes that FFmpeg is part of your \"Path\" environment variable).\n"
        ffmpeg_help += "The path must either point to the executable itself, or to the directory that contains the exectuable named \"ffmpeg\".\n\n"
        optional_args.add_argument("-f", "--ffmpeg", dest="ffmpeg", help=ffmpeg_help)

        threads_help = "Specify number of threads to be used for each process (Default is 0 for \"autodetect\").\n"
        threads_help += "Specifying more threads than there are available will clamp the value down to 1 thread for safety purposes.\n"
        threads_help += "A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.\n"
        threads_help += "The recommended value of threads to use per process is 4-6.\n\n"
        optional_args.add_argument("-t", "--threads", dest="threads", type=int, choices=[i for i in range(mp.cpu_count())], help=threads_help)

        proc_help = "Specify number of simultaneous VMAF calculation processes to run (Default is 1).\n"
        proc_help += "Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n\n"
        optional_args.add_argument("-p", "--processes", dest="processes", type=int, choices=[i for i in range(1, mp.cpu_count())], help=proc_help)

        rem_threads_help = "Specify whether or not to use remaining threads that don't make a complete process to use for an process (Default is off).\n"
        rem_threads_help += "For example, if your system has 16 threads, and you are running 5 processes with 3 threads each, then you will be using 4 * 3 threads, which is 12.\n"
        rem_threads_help += "This means you will have 1 thread that will remain unused.\n"
        rem_threads_help += "Using this option would run one more VMAF calculation process with only the single remaining thread.\n"
        rem_threads_help += "This option is not recommended, as the unused threads will be used to keep the system responsive during the VMAF calculations.\n\n"
        optional_args.add_argument("-u", "--use-rem-threads", dest="use_remaining_threads", action="store_true", help=rem_threads_help)

        vmaf_version_help = "Specify the VMAF version to use (Default is 2).\n\n"
        optional_args.add_argument("-v", "--vmaf-version", dest="vmaf_version", type=int, choices=[1, 2], help=vmaf_version_help)

        psnr_help = "Enable calculating PSNR values (Default is off).\n\n"
        optional_args.add_argument("--psnr", dest="psnr", action="store_true", help=psnr_help)

        ssim_help = "Enable calculating SSIM values (Default is off).\n\n"
        optional_args.add_argument("--ssim", dest="ssim", action="store_true", help=ssim_help)

        ms_ssim_help = "Enable calculating MS-SSIM values (Default is off).\n\n"
        optional_args.add_argument("--ms-ssim", dest="ms_ssim", action="store_true", help=ms_ssim_help)

        model_help = "Specify the VMAF model file to use (Default is \"vmaf_v0.6.1.pkl\" for VMAF version 1 and \"vmaf_v0.6.1.json\" for VMAF version 2).\n"
        model_help += "By default, this variable assumes the model file is located in the same location as this script.\n\n"
        optional_args.add_argument("-m", "--model", dest="model", help=model_help)

        log_format_help = "Specify the VMAF log file format (Default is \"xml\").\n\n"
        optional_args.add_argument("-l", "--log-format", dest="log_format", choices=["xml", "csv", "json"], help=log_format_help)

        log_name_help = "Specify the VMAF log file name (Default is \"vmaf\").\n\n"
        optional_args.add_argument("-n", "--log-name", dest="log_name", help=log_name_help)

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
