import argparse as argp
import multiprocessing as mp
import os
import subprocess as sp
import time


class VMAF_Calculator:
    def __init__(self):
        self.args = self.parse_arguments()

    def parse_arguments(self):
        main_help = "Multithreaded VMAF report file generator through FFmpeg.\n"
        main_help += "All of the following arguments have default values within the config file.\n"
        main_help += "Arguments will override the values for the variables set in the config file when sepcified.\n"
        main_help += "Settings that are not specified in the config file will use default values as deemed by the program."
        parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter)
        parser.add_argument("VMAF_FILE", type=str, help="VMAF report file.")

        ffmpeg_help = "Specify the path to the FFmpeg executable (Default is \"ffmpeg\" which assumes that FFmpeg is part of your \"Path\" environment variable).\n"
        ffmpeg_help += "The path must either point to the executable itself, or to the directory that contains the exectuable named \"ffmpeg\"."
        parser.add_argument("-f", "--ffmpeg", dest="fmpeg", default="ffmpeg", help=ffmpeg_help)

        threads_help = "Specify number of threads (Default is 0 for \"autodetect\").\n"
        threads_help += "Specifying more threads than there are available will clamp the value down to the maximum number of threads on the system.\n"
        threads_help += "A single VMAF instance will effectively max out at 12 threads - any more will provide little to no performance increase."
        parser.add_argument("-t", "--threads", dest="threads", type=int, default="0", help=threads_help)

        inst_help = "Specify number of simultaneous VMAF calculation instances to run (Default is 1).\n"
        inst_help += "Specifying more instances than there are available will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n"
        parser.add_argument("-i", "--instances", dest="instances", type=int, default="1", help=inst_help)

        psnr_help = "Enable calculating PSNR values (Default is off).\n"
        parser.add_argument("-p", "--psnr", dest="psnr", action="store_true", help=psnr_help)

        ssim_help = "Enable calculating SSIM values (Default is off).\n"
        parser.add_argument("-s", "--ssim", dest="ssim", action="store_true", help=ssim_help)

        ms_ssim_help = "Enable calculating MS-SSIM values (Default is off).\n"
        parser.add_argument("-ms", "--ms_ssim", dest="ms_ssim", action="store_true", help=ms_ssim_help)

        model_help = "Specify the VMAF model file to use (Default is \"vmaf_v0.6.1.pkl\" for VMAF version 1 and \"vmaf_v0.6.1.json\" for VMAF version 2).\n"
        model_help += "By default, this variable assumes the model file is located in the same location as this script."
        parser.add_argument("-m", "--model", dest="model", default="vmaf_v0.6.1", help=model_help)

    def validate_file(self, args):
        config_file = None
        try:
            if args.file:
                if os.path.exists(args.file) and os.path.isfile(args.file):
                    file_path = os.path.join(os.getcwd(), args.File)
                    if os.path.exists(file_path):
                        config_file = open(file_path, "r")
                    else:
                        print("ERROR: Settings file \"{}\" does not exist.".format(file_path))
                else:
                    raise Exception("")
            else:
                if os.path.exists(file) and os.path.isfile(file):
                    file_path = os.path.join(os.getcwd(), "Settings.json")
                    if os.path.exists(file_path):
                        config_file = open(file_path, "r")
                    else:
                        print("ERROR: Settings file \"{}\" does not exist.".format(file_path))
        except Exception as e:
            print(e)
            exit(1)
        config = json.load(config_file)
        config_file.close()
        return config


    def validate_threads(self, threads, config):
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


    def time_function(self, func, i, sema, rlock):
        sema.acquire()
        func(i, sema)
        sema.release()


    def run_in_parallel(self, fn, threads, lis, sema, rlock):
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

    threads = 2
    manager = mp.Manager()
    sema = mp.Semaphore(threads)
    rlock = manager.RLock()
    lis = manager.list()

    files_list = []

    # for root, directories, filenames in os.walk():

    run_in_parallel(boring_task, threads, lis, sema, rlock)
