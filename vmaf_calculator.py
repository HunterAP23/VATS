import argparse as argp
# from multiprocessing import cpu_count

from ffmpy_handler import FFmpy_Handler
from vmaf_config_handler import VMAF_Config_Handler
from HunterAP_Process_Handler import HunterAP_Process_Handler as proc_handler


class VMAF_Calculator:
    """Calculates VMAF and other visual score metric values using FFmpeg with multithreading and multiprocessing."""
    def __init__(self):
        """Run general class creation fnctions and begin calculating VMAF"""
        self._mp_handler = proc_handler()

        # Parse arguments given by the user, if any
        self._args = vars(self.parse_arguments())

        # Create a Config_Reader object with the config file.
        self._config = VMAF_Config_Handler(args=self._args, mp_handler=self._mp_handler).get_config_data()

        self._ffmpy = FFmpy_Handler(self._config["General"]["ffmpeg"])

        self._mp_handler = proc_handler(
            max_procs=self._config["Calculations"]["processes"],
            max_threads=self._config["Calculations"]["threads"]
        )

        self.calculate_vmaf(self._args["distorted"], self._args["reference"])

    def parse_arguments(self) -> argp.Namespace:
        """Parse user given arguments for calculating VMAF."""
        main_help = "Multithreaded VMAF log file generator through FFmpeg.\n"
        main_help += "The 1st required argument is the Distorted Video file.\n"
        main_help += "The 2nd required argument is the Reference Video file that the Distorted Video is compared against.\n"
        parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False)
        parser.add_argument("distorted", type=str, help="distorted video file.")
        parser.add_argument("reference", type=str, help="reference video file.")

        optional_args = parser.add_argument_group("Optional arguments")
        ffmpeg_help = "Specify the path to the FFmpeg executable (Default is \"ffmpeg\" which assumes that FFmpeg is part of your \"Path\" environment variable).\n"
        ffmpeg_help += "The path must either point to the executable itself, or to the directory that contains the executable named \"ffmpeg\".\n\n"
        optional_args.add_argument("-f", "--ffmpeg", dest="ffmpeg", help=ffmpeg_help)

        threads_help = "Specify number of threads to be used for each process (Default is 0 for \"autodetect\").\n"
        threads_help += "Specifying more threads than there are available will clamp the value down to 1 thread for safety purposes.\n"
        threads_help += "A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.\n"
        threads_help += "The recommended value of threads to use per process is 4-6.\n\n"
        # optional_args.add_argument("-t", "--threads", dest="threads", type=int, choices=[i for i in range(cpu_count())], help=threads_help)
        optional_args.add_argument("-t", "--threads", dest="threads", type=int, help=threads_help)

        proc_help = "Specify number of simultaneous VMAF calculation processes to run (Default is 1).\n"
        proc_help += "Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n\n"
        # optional_args.add_argument("-p", "--processes", dest="processes", type=int, choices=[i for i in range(1, cpu_count())], help=proc_help)
        optional_args.add_argument("-p", "--processes", dest="processes", type=int, help=proc_help)

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

        subsamples_help = "Specify the number of subsamples to use (default 1).\n"
        subsamples_help += "This value only samples the VMAF and related metrics' values once every N frames.\n"
        subsamples_help += "Higher values may improve calculation performance at the cost of less accurate results.\n\n"
        subsamples_help += "This variable corresponds to VMAF's \"n_subsample\" variable.\n\n"
        optional_args.add_argument("--subsamples", dest="subsamples", help=subsamples_help)

        model_help = "Specify the VMAF model file to use (Default is \"vmaf_v0.6.1.pkl\" for VMAF version 1 and \"vmaf_v0.6.1.json\" for VMAF version 2).\n"
        model_help += "By default, this variable assumes the model file is located in the same location as this script.\n\n"
        optional_args.add_argument("-m", "--model", dest="model", help=model_help)

        log_format_help = "Specify the VMAF log file format (Default is \"xml\").\n\n"
        optional_args.add_argument("-l", "--log-format", dest="log_format", choices=["xml", "csv", "json"], help=log_format_help)

        log_path_help = "Specify the VMAF log path and file name (Default is \"vmaf\").\n\n"
        optional_args.add_argument("-n", "--log-name", dest="log_path", help=log_path_help)


        config_help = "Specify a config file to import multiple settings with (Default is \"config.ini\" in the same folder as the script).\n"
        config_help += "Values specified with the arguments above will override the settings in the config file."
        optional_args.add_argument("-c", "--config", dest="config", help=config_help)

        misc_args = parser.add_argument_group("Miscellaneous arguments")
        misc_args.add_argument("-h", "--help", action="help", default=argp.SUPPRESS, help="Show this help message and exit.\n")

        args = parser.parse_args()
        return args

    def calculate_vmaf(self, distorted: str, reference: str) -> None:
        output_cmd = "-hide_banner -filter_complex "

        tmp_filter = "libvmaf=model_path={}".format(self._config["Calculations"]["model"])
        tmp_filter += ":log_fmt={}".format(self._config["Calculations"]["log_format"])
        tmp_filter += ":log_path={}".format(self._config["Calculations"]["log_path"])

        if self._config["Calculations"]["psnr"]:
            tmp_filter += ":psnr=1"
        if self._config["Calculations"]["ssim"]:
            tmp_filter += ":ssim=1"
        if self._config["Calculations"]["ms_ssim"]:
            tmp_filter += ":ms_ssim=1"
        tmp_filter += ":n_threads={}".format(self._config["Calculations"]["threads"])

        output_cmd += repr(tmp_filter)

        output_cmd += " -f null"
        output_cmd = output_cmd.replace(r"\\", "\\")

        cmd_args = {
            "ff_inputs": {
                distorted: None,
                reference: None
            },
            "ff_outputs": {
                "-": output_cmd
            }
        }

        # cmd = self._ffmpy.run_command(**cmd_args, get_cmd=True)

        out, err = self._ffmpy.run_command(**cmd_args)

        # for line in out.decode("utf-8").split("\n"):
        #     print(line)

        for line in err.decode("utf-8").split("\n"):
            if "VMAF score" in line:
                print(line)


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
    #
    # run_in_parallel(boring_task, threads, lis, sema, rlock)
