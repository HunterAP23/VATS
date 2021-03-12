import configparser as confp
import math
import multiprocessing as mp
import os

from file_handler import File_Handler
from HunterAP_Process_Handler import *
from HunterAP_Common import *

class Config_Handler(File_Handler):
    def __init__(self, args, program="Calculations"):
        self.args = args
        self.program = program
        filename = ""
        if self.args.config:
            filename = self.args.config
        else:
            filename = "config.ini"

        # if the file exists and is a file then use it
        File_Handler.__init__(self, file=filename, config=True)
        if self.file is not None:
            self.config_data = self.read_config(self.file)
        else:
            self.config_data = self.generate_default_config()
            self.file = "config.ini"
        self.args.config = self.file

        # print_dict(dict(vars(self)))
        self.validate_options(self.file)

        # for k, v in config.items():
        #     for k2, v2 in v.items():
        #         print("{0}: {1}".format(k2, v2))
        # self.config = {s:dict(config.items(s)) for s in config.sections()}

    def get_config_data(self):
        return self.config_data

    def generate_default_config_dict(self):
        config_dict = {
            "General": {
                "vmaf_version": 2
            },
            "Calculations": {
                "ffmpeg_location": "ffmpeg",
                "psnr": False,
                "ssim": False,
                "ms_ssim": False,
                "model": "vmaf_v0.6.1",
                "log_name": "vmaf",
                "log_format": "xml",
                "threads": mp.cpu_count(),
                "instances": 1,
                "use_remaining_threads": False
            },
            "Graphing": {
                "output": "vmaf",
                "lower_boundary": "default",
                "custom": 0,
                "threads": mp.cpu_count(),
                "instances": 1,
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
            elif item == "threads" or item == "instances":
                accepted_values = [i for i in range(mp.cpu_count())]
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
                                raise OSError(msg.format(tmp_config))
                        # Otherwise throw an exception
                        else:
                            msg = "Could not find config file in directory {0} - generating a default one."
                            raise OSError(msg.format(tmp_config))
                else:
                    "The specified config file {0} does not exist - generating a default one.".format(filename)
                    raise OSError(msg.format(filename))
            except OSError as ose:
                print(ose)

            if config is None:
                return False
            else:
                return config

        def validate_threads(self):
            should_print = None
            try:
                if self.args.threads:
                    if self.args.threads > mp.cpu_count():
                        should_print = True
                        msg = "ERROR: User specified {0} threads which is more than the number the system supports ({1}). Checking config file for specified thread count."
                        raise HunterAP_Process_Handler_Error(msg.format(self.args.threads, mp.cpu_count()))
                    else:
                        self.config_data[self.program]["threads"] = self.args.threads
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)
                try:
                    if int(self.config_data[self.program]["threads"]) > mp.cpu_count():
                        msg = "ERROR: Config file specified {0} threads which is more than the number the system supports ({1}). Defaulting to 1 thread."
                        raise HunterAP_Process_Handler_Error(msg.format(self.config_data[self.program]["threads"], mp.cpu_count()))
                except HunterAP_Process_Handler_Error as hap_phe:
                    print(hap_phe)
                    self.config_data[self.program]["threads"] = 1

        def validate_instances(self):
            should_print = None
            try:
                if self.args.instances:
                    if self.args.instances > mp.cpu_count():
                        should_print = True
                        msg = "ERROR: User specified {0} instances which is more than the number of threads the system supports ({1}). Checking config file for specified instances count."
                        raise HunterAP_Process_Handler_Error(msg.format(self.args.instances, mp.cpu_count()))
                    else:
                        self.config_data[self.program]["instances"] = self.args.instances
                else:
                    should_print = False
                    raise HunterAP_Process_Handler_Error()
            except HunterAP_Process_Handler_Error as hap_phe:
                if should_print:
                    print(hap_phe)
                try:
                    if int(self.config_data[self.program]["instances"]) > mp.cpu_count():
                        msg = "ERROR: Config file specified {0} instances which is more than the number of threads the system supports ({1}). Defaulting to 1 instance."
                        raise HunterAP_Process_Handler_Error(msg.format(self.config_data[self.program]["instances"], mp.cpu_count()))
                except HunterAP_Process_Handler_Error as hap_phe:
                    print(hap_phe)
                    self.config_data[self.program]["threads"] = 1

        def validate_processes(self):
            total = int(self.config_data[self.program]["threads"]) * int(self.config_data[self.program]["instances"])
            try:
                if total > mp.cpu_count():
                    msg = "ERROR: The number of total threads used over all {0} instances is greater than the number of threads in the system {1}. Limiting instances down to allow as many instances as possible with {2} threads per instance."
                    raise HunterAP_Process_Handler_Error(msg.format(self.config_data[self.program]["instances"], mp.cpu_count(), self.config_data[self.program]["threads"]))
            except HunterAP_Process_Handler_Error as hap_phe:
                print(hap_phe)
                instances = math.floor(mp.cpu_count() / int(self.config_data[self.program]["threads"]))
                total_threads = self.config_data[self.program]["threads"] * instances
                rem_threads = mp.cpu_count() - total_threads
                msg = "The program will run {0} instances instead of {1}, with {2} threads per instance for a total of {3} total threads in use, with {4} threads remaining unused."
                print(msg.format(instances, self.config_data[self.program]["instances"], self.config_data[self.program]["threads"], total_threads, rem_threads))
                self.config_data[self.program]["instances"] = instances


        check = validate_config_file(filename)
        if check:
            self.read_config(filename)
        else:
            self.generate_default_config()

        validate_threads(self)

        validate_instances(self)

        validate_processes(self)
