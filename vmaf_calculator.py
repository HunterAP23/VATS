import argparse as argp
import multiprocessing as mp
import os
import shlex
import subprocess as sp
import time

from file_reader import File_Reader


class VMAF_Calculator:
    """Calculates VMAF  and other visual score metric values using FFmpeg with multithreading and multiprocessing."""
    def __init__(self):
        # Parse arguments given by the user, if any
        self.args = self.parse_arguments()
        # Create a File_Reader object with the config file.
        self.config = File_Reader(self.args.config)

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
        optional_args.add_argument("-f", "--ffmpeg", dest="ffmpeg", default="ffmpeg", help=ffmpeg_help)

        threads_help = "Specify number of threads (Default is 0 for \"autodetect\").\n"
        threads_help += "Specifying more threads than there are available will clamp the value down to the maximum number of threads on the system.\n"
        threads_help += "A single VMAF instance will effectively max out at 12 threads - any more will provide little to no performance increase."
        optional_args.add_argument("-t", "--threads", dest="threads", type=int, default="0", help=threads_help)

        inst_help = "Specify number of simultaneous VMAF calculation instances to run (Default is 1).\n"
        inst_help += "Specifying more instances than there are available will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n"
        optional_args.add_argument("-i", "--instances", dest="instances", type=int, default="1", help=inst_help)

        psnr_help = "Enable calculating PSNR values (Default is off).\n"
        optional_args.add_argument("-p", "--psnr", dest="psnr", action="store_true", help=psnr_help)

        ssim_help = "Enable calculating SSIM values (Default is off).\n"
        optional_args.add_argument("-s", "--ssim", dest="ssim", action="store_true", help=ssim_help)

        ms_ssim_help = "Enable calculating MS-SSIM values (Default is off).\n"
        optional_args.add_argument("-ms", "--ms_ssim", dest="ms_ssim", action="store_true", help=ms_ssim_help)

        model_help = "Specify the VMAF model file to use (Default is \"vmaf_v0.6.1.pkl\" for VMAF version 1 and \"vmaf_v0.6.1.json\" for VMAF version 2).\n"
        model_help += "By default, this variable assumes the model file is located in the same location as this script."
        optional_args.add_argument("-m", "--model", dest="model", default=os.path.join(__file__, "vmaf_v0.6.1"), help=model_help)

        log_help = "Specify the VMAF output log format (Default is \"xml\").\n"
        optional_args.add_argument("-l", "--log", dest="log", default="xml", choices=["xml", "csv", "json"], help=log_help)

        config_help = "Specify a config file to import multiple settings with (Default is \"config.ini\" in the same folder as the script).\n"
        config_help += "Values specified with the arguments above will override the settings in the config file."
        optional_args.add_argument("-c", "--config", dest="config", default=os.path.join(__file__, "config.ini"), help=config_help)

        misc_args = parser.add_argument_group("Miscellaneous arguments")
        misc_args.add_argument("-h", "--help", action="help", default=argp.SUPPRESS, help="Show this help message and exit.\n")

        args = parser.parse_args()
        args.Threads = self.validate_threads(args.Threads, config)
        config = self.validate_file(self.args.config)
        return self.args

    def validate_threads(self, threads: int, config: str):
        """Validate that the number of threads specifieid by either the user or config file is not more than the number of threads available on the system."""
        if threads:
            if threads > mp.cpu_count():
                msg = "ERROR: User specified {0} threads which is more than the number the system supports ({1}), clamping the value to the available number of threads on this system."
                print(msg.format(threads, mp.cpu_count()))
                threads = mp.cpu_count()
        else:
            if "General" not in config:
                print("ERROR: \"global\" key does not exist in the configuration file. Manually asking user for input...")
                threads = mp.cpu_count()
            else:
                if "threads" not in config["global"]:
                    print("ERROR: \"threads\" key does not exist in the \"global\" section of the configuration file. Goign with default value of all threads ({})".format(mp.cpu_count()))
                    threads = mp.cpu_count()
                else:
                    try:
                        threads_int = int(config["global"]["threads"])
                        if threads_int > mp.cpu_count():
                            msg = "ERROR: Configuration file specified {0} threads which is more than the number the system supports ({1}), clamping the value to the available number of threads on this system."
                            print(msg.format(threads, mp.cpu_count()))
                            threads = mp.cpu_count()
                        else:
                            threads = threads_int
                    except ValueError:
                        print("ERROR: Value ({0}) for \"threads\" key is not an integer. Defaulting to all CPU threads ({1}).".format(config["global"]["threads"], mp.cpu_count()))
                        threads = mp.cpu_count()

        return threads

    def time_function(self, func, i: int, sema, rlock):
        sema.acquire()
        func(i, sema)
        sema.release()

    def run_in_parallel(self, fn, threads: int, lis: list, sema, rlock):
        proc = []
        for i in lis:
            p = mp.Process(target=time_function, args=(fn, i, sema, rlock))
            proc.append(p)

        for p in proc:
            p.start()

        for p in proc:
            try:
                p.join()
            except Exception as e:
                print("EXCEPTION: {}".format(e))

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
