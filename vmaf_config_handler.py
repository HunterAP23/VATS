# File parsing & handling
import configparser as confp
from pathlib import Path

# Variable typing
from typing import Optional

# Process related
import subprocess as sp

# Misc
import math

# 3rd party
import ffmpy

# Made for this project
from vmaf_file_handler import VMAF_File_Handler
from HunterAP_Process_Handler import HunterAP_Process_Handler as proc_handler
from HunterAP_Process_Handler import HunterAP_Process_Handler_Error
from HunterAP_Common import print_dict


class VMAF_Config_Handler(VMAF_File_Handler):
    def __init__(self, args: dict, mp_handler: proc_handler, program: Optional[str] = "Calculations"):
        self._args = args
        self._program = program
        self._mp_handler = mp_handler
        filename = ""
        if self._args["config"]:
            filename = self._args["config"]
        else:
            filename = "config.ini"

        # if the file exists and is a file then use it
        VMAF_File_Handler.__init__(self, file=filename, file_type="config", os_name=self._mp_handler._get_sys_platform())
        if self._file is not None:
            self._config_data = self.read_config(self._file)
        else:
            self._config_data = self.generate_default_config()
            self._file = "config.ini"
        self._args["config"] = self._file

        self.validate_options(self._file)

    def get_config_data(self):
        return self._config_data

    def generate_default_config_dict(self):
        config_dict = {
            "General": {
                "vmaf_version": 2,
                "ffmpeg": "ffmpeg"
            },
            "Calculations": {
                "psnr": False,
                "ssim": False,
                "ms_ssim": False,
                "model": "vmaf_v0.6.1",
                "log_path": "vmaf",
                "log_format": "xml",
                "threads": self._mp_handler._get_core_count(),
                "processes": 1,
                "use_remaining_threads": False
            },
            "Graphing": {
                "output": "vmaf",
                "lower_boundary": "default",
                "custom": 0,
                "threads": self._mp_handler._get_core_count(),
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
        if self._file is None:
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

        self._config_data = dict()

        try:
            for section, option in config_dict.items():
                self._config_data[section] = dict()
                for k, v in option.items():
                    try:
                        if type(v) == str:
                            self._config_data[section][k] = config[section].get(k, v)
                        elif type(v) == bool:
                            self._config_data[section][k] = config[section].getboolean(k, v)
                        elif type(v) == int:
                            self._config_data[section][k] = config[section].getint(k, v)
                        elif type(v) == float:
                            self._config_data[section][k] = config[section].getfloat(k, v)
                    except confp.NoOptionError:
                        self._config_data[section][k] = v
        except confp.NoSectionError:
            for k, v in config_dict.items():
                self._config_data[section][k] = v

        return self._config_data

    def validate_options(self, filename):
        """Validate all user specified, config-specified, and remaining default options."""
        def validate_config_file(filename):
            """Validate the config file."""

            config = None
            file = Path(filename)
            try:
                # Check if path given actually exists
                if file.exists():
                    # Check if path is a file or a directory
                    if file.is_file():
                        config = filename
                    elif file.is_dir():
                        # If user gave a directory instead of a config file,
                        # check if default config file exists in that directory
                        tmp_config = file.joinpath("config.ini")
                        if tmp_config.exists():
                            if tmp_config.is_file():
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
                if self._args["threads"]:
                    if self._args["threads"] > self._mp_handler._get_core_count():
                        should_print = True
                        msg = "ERROR: User specified {0} threads which is more than the number the system supports ({1}). Checking config file for specified thread count."
                        msg = msg.format(self._args["threads"], self._mp_handler._get_core_count())
                        raise HunterAP_Process_Handler_Error(msg)
                    else:
                        self._config_data[self._program]["threads"] = self._args["threads"]
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)
                if int(self._config_data[self._program]["threads"]) > self._mp_handler._get_core_count():
                    msg = "WARNING: Config file specified {0} threads which is more than the number the system supports ({1}). Defaulting to 1 thread."
                    msg = msg.format(self._config_data[self._program]["threads"], self._mp_handler._get_core_count())
                    print(msg)
                    self._config_data[self._program]["threads"] = 1

        def validate_processes(self):
            print("Validating process count...")
            should_print = None
            try:
                if self._args["processes"]:
                    if self._args["processes"] > self._mp_handler._get_core_count():
                        should_print = True
                        msg = "WARNING: User specified {0} processes which is more than the number of threads the system supports ({1}). Checking config file for specified processes count."
                        msg = msg.format(self._args["processes"], self._mp_handler._get_core_count())
                        raise HunterAP_Process_Handler_Error(msg)
                    else:
                        self._config_data[self._program]["processes"] = self._args["processes"]
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)

                if int(self._config_data[self._program]["processes"]) > self._mp_handler._get_core_count():
                    msg = "WARNING: Config file specified {0} processes which is more than the number of threads the system supports ({1}). Defaulting to 1 process."
                    msg = msg.format(self._config_data[self._program]["processes"], self._mp_handler._get_core_count())
                    print(msg)
                    self._config_data[self._program]["threads"] = 1

        def validate_threads_processes(self):
            print("Validating total process count...")
            total = int(self._config_data[self._program]["threads"]) * int(self._config_data[self._program]["processes"])
            try:
                if total > self._mp_handler._get_core_count():
                    msg = "WARNING: Can not run {0} processes with {1} threads per process as that exceeds the number of threads in the system ({2} threads). Limiting processes down to allow as many processes as possible with {1} threads per process."
                    msg = msg.format(self._config_data[self._program]["processes"], self._config_data[self._program]["threads"], self._mp_handler._get_core_count())
                    raise HunterAP_Process_Handler_Error(msg)
                else:
                    msg = "Running {0} processes with {1} threads per process. Continuing..."
                    print(msg.format(self._config_data[self._program]["processes"], self._config_data[self._program]["threads"]))
            except HunterAP_Process_Handler_Error as hap_phe:
                print(hap_phe)
                processes = math.floor(self._mp_handler._get_core_count() / int(self._config_data[self._program]["threads"]))
                total_threads = self._config_data[self._program]["threads"] * processes
                rem_threads = self._mp_handler._get_core_count() - total_threads
                msg = "The program will run {0} processes instead of {1}, with {2} threads per process for a total of {3} total threads in use, with {4} threads remaining unused."
                print(msg.format(processes, self._config_data[self._program]["processes"], self._config_data[self._program]["threads"], total_threads, rem_threads))
                self._config_data[self._program]["processes"] = processes

        def validate_ffmpeg(self):
            print("Checking FFmpeg executable...")

            if self._args["ffmpeg"]:
                self._config_data["General"]["ffmpeg"] = VMAF_File_Handler(self._args["ffmpeg"], file_type="executable", os_name=self._mp_handler._get_sys_platform()).get_file()
            else:
                self._config_data["General"]["ffmpeg"] = VMAF_File_Handler(self._config_data["General"]["ffmpeg"], file_type="executable", os_name=self._mp_handler._get_sys_platform()).get_file()

            print("ffmpeg: {}".format(self._config_data["General"]["ffmpeg"]))

            try:
                ff = ffmpy.FFmpeg(
                    executable=self._config_data["General"]["ffmpeg"],
                    global_options=["-h"]
                )

                out, err = ff.run(stdout=sp.PIPE, stderr=sp.PIPE)

                if self._program == "Calculations":
                    if "--enable-libvmaf" in out.decode("utf-8"):
                        msg = "FFmpeg is not built with VMAF support (\"--enable-libvmaf\"). The program can not continue and will now exit."
                        raise OSError(msg)

                print("FFmpeg executable \"{0}\" is valid and contains the libvmaf library. Continuing...".format(self._config_data["General"]["ffmpeg"]))
            except ffmpy.FFExecutableNotFoundError as ffenfe:
                if self._mp_handler._get_sys_platform() == "Windows":
                    msg = "ERROR: FFmpeg executable was not found in given path \"{0}\".\n"
                    msg += "FFmpeg is required for this program to run.\n"
                    msg += "Please make sure you have FFmpeg installed correctly and that you pointing the program to the executable through either your config file or through runtime arguments."
                    msg = msg.format(self._config_data["General"]["ffmpeg"])
                    print(msg)
                else:
                    print(ffenfe)
                exit(1)

        def validate_model(self):
            tmp_model = None
            print("Validating VMAF model file...")
            if self._args["model"]:
                tmp_model = VMAF_File_Handler(self._args["model"], file_type="model").get_file()
            else:
                tmp_model = VMAF_File_Handler(self._config_data["Calculations"]["model"], file_type="model").get_file()

            if self._mp_handler._get_sys_platform() == "Windows":
                if len(Path(tmp_model).resolve().parts) == 1:
                    tmp_model = Path(Path.cwd().joinpath(tmp_model))
                paths = list(Path(tmp_model).resolve().parts)
                drive = paths[0].replace("\\", "")
                paths[0] = drive[0] + r"\\" + drive[1]
                newfile = "/".join(paths)
                tmp_model = newfile
            else:
                if len(Path(tmp_model).resolve().parts) == 1:
                    tmp_model = Path(Path.cwd().joinpath(tmp_model))

            try:
                if self._config_data["General"]["vmaf_version"] == 1:
                    if not tmp_model.endswith(".pkl"):
                        tmp_model += ".pkl"
                else:
                    if not tmp_model.endswith(".json"):
                        tmp_model += ".json"

                output_cmd = "-t 1 -filter_complex "
                output_cmd += repr("libvmaf=model_path={0}")
                output_cmd += " -f null"
                output_cmd = str(output_cmd).format(tmp_model)
                ff = ffmpy.FFmpeg(
                    executable=self._config_data["General"]["ffmpeg"],
                    inputs={
                        "video_samples/sample1.mp4": None,
                        "video_samples/sample2.mp4": None
                    },
                    outputs={
                        "-": output_cmd
                    }
                )

                out, err = ff.run(stdout=sp.PIPE, stderr=sp.PIPE)

                if "could not read model from path" in err.decode("utf-8"):
                    raise FileNotFoundError("Could not find VMAF model file {0}.".format(self._args["model"]))
                else:
                    msg = "VMAF model file {0} is valid for running with VMAF version {1}. Continuing..."
                    msg = msg.format(self._config_data["Calculations"]["model"], self._config_data["General"]["vmaf_version"])
                    print(msg)
                    self._config_data["Calculations"]["model"] = tmp_model
                    print("ff.cmd: {}".format(ff.cmd))
            except FileNotFoundError as fnfe:
                print(fnfe)
                exit(1)

        def validate_log(self):
            if self._args["log_format"]:
                if self._args["log_format"] == "json":
                    self._config_data["Calculations"]["log_format"] = "json"
                elif self._args["log_format"] == "xml":
                    self._config_data["Calculations"]["log_format"] = "xml"
                elif self._args["log_format"] == "csv":
                    self._config_data["Calculations"]["log_format"] = "csv"

            tmp_log = None
            if self._args["log_path"]:
                tmp_log = VMAF_File_Handler(self._args["log_path"], file_type="log").get_file()
                self._config_data["Calculations"]["log_path"] = tmp_log
                self._config_data["Calculations"]["log_format"] = Path(tmp_log).suffix.replace(".", "")
            else:
                tmp_log = VMAF_File_Handler(self._config_data["Calculations"]["log_path"], file_type="log").get_file()
                self._config_data["Calculations"]["log_path"] = tmp_log
                self._config_data["Calculations"]["log_format"] = Path(tmp_log).suffix.replace(".", "")

            if self._mp_handler._get_sys_platform() == "Windows":
                if len(Path(tmp_log).resolve().parts) == 1:
                    tmp_log = Path(Path.cwd().joinpath(tmp_log))
                paths = list(Path(tmp_log).resolve().parts)
                drive = paths[0].replace("\\", "")
                paths[0] = drive[0] + r"\\" + drive[1]
                newfile = "/".join(paths)
                self._config_data["Calculations"]["log_path"] = newfile
            else:
                if len(Path(tmp_log).resolve().parts) == 1:
                    tmp_log = Path(Path.cwd().joinpath(tmp_log))

        check = validate_config_file(filename)
        if check:
            self.read_config(filename)
        else:
            self.generate_default_config()

        validate_threads(self)

        validate_processes(self)

        validate_threads_processes(self)

        if self._args["vmaf_version"]:
            self._config_data["General"]["vmaf_version"] = self._args["vmaf_version"]

        if self._program == "Calculations":
            validate_ffmpeg(self)

            if self._args["psnr"]:
                self._config_data["Calculations"]["psnr"] = self._args["psnr"]

            if self._args["ssim"]:
                self._config_data["Calculations"]["ssim"] = self._args["ssim"]

            if self._args["ms_ssim"]:
                self._config_data["Calculations"]["ms_ssim"] = self._args["ms_ssim"]

            validate_model(self)

            validate_log(self)

        # for k, v in self._config_data.items():
        #     if k == "args" or k == "config":
        #         print_dict(k)
        #     else:
        #         print("{0}: {1}".format(k, v))
