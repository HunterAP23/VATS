import configparser as confp
import math
import os
from pathlib import Path
# from pathlib import PurePath
import shlex
import subprocess as sp
from typing import AnyStr
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import ffmpy

from file_handler import File_Handler
from HunterAP_Process_Handler import HunterAP_Process_Handler as proc_handler
from HunterAP_Process_Handler import HunterAP_Process_Handler_Error
from HunterAP_Common import print_dict


class Config_Handler(File_Handler):
    def __init__(self, args, program: Optional[AnyStr] = "Calculations", mp_handler: Optional[proc_handler] = None):
        self.args = args
        self.program = program
        self.mp_handler = mp_handler
        filename = ""
        if self.args.config:
            filename = self.args.config
        else:
            filename = "config.ini"

        # if the file exists and is a file then use it
        File_Handler.__init__(self, file=filename, file_type="config", os_name=self.mp_handler.sys_platform)
        if self.file is not None:
            self.config_data = self.read_config(self.file)
        else:
            self.config_data = self.generate_default_config()
            self.file = "config.ini"
        self.args.config = self.file

        self.validate_options(self.file)

    def get_config_data(self):
        return self.config_data

    def generate_default_config_dict(self):
        config_dict = {
            "General": {
                "vmaf_version": 2
            },
            "Calculations": {
                "ffmpeg": "ffmpeg",
                "psnr": False,
                "ssim": False,
                "ms_ssim": False,
                "model": "vmaf_v0.6.1",
                "log_name": "vmaf",
                "log_format": "xml",
                "threads": self.mp_handler.core_count,
                "processes": 1,
                "use_remaining_threads": False
            },
            "Graphing": {
                "output": "vmaf",
                "lower_boundary": "default",
                "custom": 0,
                "threads": self.mp_handler.core_count,
                "processes": 1,
                "use_remaining_threads": False
            },
            "Image Settings": {
                "x": 1920.0,
                "y": 1080.0,
                "dpi": 100.0,
                "format": "svg",
                "transparent": True
            },
            "Video Settings": {
                "x": 1920.0,
                "y": 1080.0,
                "framerate": 60.0,
                "transparent": True
            }
        }
        return config_dict

    def generate_default_config(self):
        default_config_dict = self.generate_default_config_dict()
        if self.file is None:
            default_config = confp.ConfigParser()
            default_config.read_dict(default_config_dict)

            with open("config.ini", "w") as config_file:
                default_config.write(config_file)

        return default_config_dict

    def read_config(self, filename):
        config = confp.ConfigParser()
        config.read(filename)

        config_dict = self.generate_default_config_dict()

        # print_dict(config_dict)

        self.config_data = dict()

        try:
            for section, option in config_dict.items():
                self.config_data[section] = dict()
                for k, v in option.items():
                    try:
                        if type(v) == str:
                            self.config_data[section][k] = config[section].get(k, v)
                            # self.config_data[section][k] = self.default_validator(section, k, v)
                        elif type(v) == bool:
                            self.config_data[section][k] = config[section].getboolean(k, v)
                        elif type(v) == int:
                            self.config_data[section][k] = config[section].getint(k, v)
                        elif type(v) == float:
                            self.config_data[section][k] = config[section].getfloat(k, v)
                    except confp.NoOptionError:
                        self.config_data[section][k] = v
        except confp.NoSectionError:
            for k, v in config_dict.items():
                self.config_data[section][k] = v

        return self.config_data

    def default_validator(self, section, item, default):
        accepted_values = []
        if item in vars(self.args).keys():
            if item == "vmaf_version":
                accepted_values = [i for i in range(1, 2)]
            elif item == "threads" or item == "processes":
                accepted_values = [i for i in range(self.mp_handler.core_count)]
            # elif :

    def validate_options(self, filename):
        """Validate all user specified, config-specified, and remaining default options."""
        def validate_config_file(filename):
            """Validate the config file."""

            config = None
            try:
                # Check if path given actually exists
                if os.path.exists(filename):
                    # Check if path is a file or a directory
                    if os.path.isfile(filename):
                        config = filename
                    elif os.path.isdir(filename):
                        # If user gave a directory instead of a config file,
                        # check if default config file exists in that directory
                        tmp_config = os.path.join(filename, "config.ini")
                        if os.path.exists(tmp_config):
                            if os.path.isfile(tmp_config):
                                config = tmp_config
                            else:
                                msg = "Could not find config file in directory {0} - generating a default one."
                                msg = msg.format(tmp_config)
                                raise OSError(msg)
                        # Otherwise throw an exception
                        else:
                            msg = "Could not find config file in directory {0} - generating a default one."
                            msg = msg.format(tmp_config)
                            raise OSError(msg)
                else:
                    msg = "The specified config file {0} does not exist - generating a default one."
                    msg = msg.format(filename)
                    raise OSError(msg)
            except OSError as ose:
                print(ose)

            if config is None:
                return False
            else:
                return config

        def validate_threads(self):
            print("Validating thread count...")
            should_print = None
            try:
                if self.args.threads:
                    if self.args.threads > self.mp_handler.core_count:
                        should_print = True
                        msg = "ERROR: User specified {0} threads which is more than the number the system supports ({1}). Checking config file for specified thread count."
                        msg = msg.format(self.args.threads, self.mp_handler.core_count)
                        raise HunterAP_Process_Handler_Error(msg)
                    else:
                        self.config_data[self.program]["threads"] = self.args.threads
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)
                if int(self.config_data[self.program]["threads"]) > self.mp_handler.core_count:
                    msg = "WARNING: Config file specified {0} threads which is more than the number the system supports ({1}). Defaulting to 1 thread."
                    msg = msg.format(self.config_data[self.program]["threads"], self.mp_handler.core_count)
                    print(msg)
                    self.config_data[self.program]["threads"] = 1

        def validate_processes(self):
            print("Validating process count...")
            should_print = None
            try:
                if self.args.processes:
                    if self.args.processes > self.mp_handler.core_count:
                        should_print = True
                        msg = "WARNING: User specified {0} processes which is more than the number of threads the system supports ({1}). Checking config file for specified processes count."
                        msg = msg.format(self.args.processes, self.mp_handler.core_count)
                        raise HunterAP_Process_Handler_Error(msg)
                    else:
                        self.config_data[self.program]["processes"] = self.args.processes
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)

                if int(self.config_data[self.program]["processes"]) > self.mp_handler.core_count:
                    msg = "WARNING: Config file specified {0} processes which is more than the number of threads the system supports ({1}). Defaulting to 1 process."
                    msg = msg.format(self.config_data[self.program]["processes"], self.mp_handler.core_count)
                    print(msg)
                    self.config_data[self.program]["threads"] = 1

        def validate_threads_processes(self):
            print("Validating total process count...")
            total = int(self.config_data[self.program]["threads"]) * int(self.config_data[self.program]["processes"])
            try:
                if total > self.mp_handler.core_count:
                    msg = "WARNING: Can not run {0} processes with {1} threads per process as that exceeds the number of threads in the system ({2} threads). Limiting processes down to allow as many processes as possible with {1} threads per process."
                    msg = msg.format(self.config_data[self.program]["processes"], self.config_data[self.program]["threads"], self.mp_handler.core_count)
                    raise HunterAP_Process_Handler_Error(msg)
                else:
                    msg = "Running {0} processes with {1} threads per process. Continuing..."
                    print(msg.format(self.config_data[self.program]["processes"], self.config_data[self.program]["threads"]))
            except HunterAP_Process_Handler_Error as hap_phe:
                print(hap_phe)
                processes = math.floor(self.mp_handler.core_count / int(self.config_data[self.program]["threads"]))
                total_threads = self.config_data[self.program]["threads"] * processes
                rem_threads = self.mp_handler.core_count - total_threads
                msg = "The program will run {0} processes instead of {1}, with {2} threads per process for a total of {3} total threads in use, with {4} threads remaining unused."
                print(msg.format(processes, self.config_data[self.program]["processes"], self.config_data[self.program]["threads"], total_threads, rem_threads))
                self.config_data[self.program]["processes"] = processes

        def validate_ffmpeg(self):
            print("Checking FFmpeg executable...")

            if self.args.ffmpeg:
                self.config_data[self.program]["ffmpeg"] = File_Handler(self.args.ffmpeg, file_type="executable", exec_name="ffmpeg", os_name=self.mp_handler.sys_platform).file
            else:
                self.config_data[self.program]["ffmpeg"] = File_Handler(self.config_data[self.program]["ffmpeg"], file_type="executable", exec_name="ffmpeg", os_name=self.mp_handler.sys_platform).file

            print("ffmpeg: {}".format(self.config_data[self.program]["ffmpeg"]))

            try:
                ff = ffmpy.FFmpeg(
                    executable = self.config_data[self.program]["ffmpeg"],
                    global_options = ["-h"]
                )

                out, err = ff.run(stdout=sp.PIPE, stderr=sp.PIPE)

                if self.program == "Calculations":
                    if "--enable-libvmaf" in out.decode("utf-8"):
                        msg = "FFmpeg is not built with VMAF support (\"--enable-libvmaf\"). The program can not continue and will now exit."
                        raise OSError(msg)

                print("FFmpeg executable \"{0}\" is valid and contains the libvmaf library. Continuing...".format(self.config_data[self.program]["ffmpeg"]))
            except ffmpy.FFExecutableNotFoundError as ffenfe:
                if self.mp_handler.sys_platform == "Windows":
                    msg = ""
                    # if exc.winerror == 5:
                    #     msg = "ERROR: FFmpeg executable was not found in given path \"{0}\".\n"
                    #     msg = msg.format(self.config_data[self.program]["ffmpeg"])
                    # elif exc.winerror == 193:
                    #     msg = "ERROR: The provided file ({0}) is not a valid FFmpeg executable.\n"
                    #     msg = msg.format(self.config_data[self.program]["ffmpeg"])
                    msg = "ERROR: FFmpeg executable was not found in given path \"{0}\".\n"
                    msg += "FFmpeg is required for this program to run.\n"
                    msg += "Please make sure you have FFmpeg installed correctly and that you pointing the program to the executable through either your config file or through runtime arguments."
                    msg = msg.format(self.config_data[self.program]["ffmpeg"])
                    print(msg)
                else:
                    print(ffenfe)
                exit(1)

        def validate_model(self):
            print("Validating VMAF model file...")
            model_finder = None
            if self.args.model:
                model_finder = File_Handler(self.args.model, file_type="model").file
            else:
                model_finder = File_Handler(self.config_data[self.program]["model"], file_type="model").file

            if self.mp_handler.sys_platform == "Windows":
                paths = list(Path(model_finder).parts)
                drive = paths[0].replace("\\", "")
                paths[0] = drive[0] + r"\\" + drive[1]
                newfile = "/".join(paths)
                model_finder = newfile

            try:
                if self.config_data["General"]["vmaf_version"] == 1:
                    if not model_finder.endswith(".pkl"):
                        model_finder += ".pkl"
                else:
                    if not model_finder.endswith(".json"):
                        model_finder += ".json"

                ff = ffmpy.FFmpeg(
                    executable = self.config_data[self.program]["ffmpeg"],
                    inputs = {
                        "video_samples/sample1.mp4": None,
                        "video_samples/sample2.mp4": None
                    },
                    outputs = {
                        "-": "-t 1 -filter_complex \"libvmaf=model_path={0}\" -f null".format(repr(model_finder).replace("'", "\""))
                    }
                )

                out, err = ff.run(stdout=sp.PIPE, stderr=sp.PIPE)

                if "could not read model from path" in err.decode("utf-8"):
                    raise FileNotFoundError("Could not find VMAF model file {0}.".format(model_finder))
                else:
                    msg = "VMAF model file {0} is valid for running with VMAF version {1}. Continuing..."
                    msg = msg.format(self.config_data[self.program]["model"], self.config_data["General"]["vmaf_version"])
                    print(msg)
            except FileNotFoundError as fnfe:
                print(fnfe)
                exit(1)

        check = validate_config_file(filename)
        if check:
            self.read_config(filename)
        else:
            self.generate_default_config()

        validate_threads(self)

        validate_processes(self)

        validate_threads_processes(self)

        if self.args.vmaf_version:
            self.config_data["General"]["vmaf_version"] = self.args.vmaf_version

        if self.program == "Calculations":
            validate_ffmpeg(self)

            if self.args.psnr:
                self.config_data[self.program]["psnr"] = self.args.psnr

            if self.args.ssim:
                self.config_data[self.program]["ssim"] = self.args.ssim

            if self.args.ms_ssim:
                self.config_data[self.program]["ms_ssim"] = self.args.ms_ssim

            validate_model(self)

            if self.args.log_format:
                self.config_data[self.program]["log_name"] = self.args.log_format

            if self.args.log_name:
                self.config_data[self.program]["log_name"] = self.args.log_name

        # for k, v in self.config_data.items():
        #     if k == "args" or k == "config":
        #         print_dict(k)
        #     else:
        #         print("{0}: {1}".format(k, v))
