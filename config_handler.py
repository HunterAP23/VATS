import configparser as confp
import multiprocessing as mp
import os

from file_handler import File_Handler

class Config_Handler(File_Handler):
    def __init__(self, args):
        try:
            filename = ""
            if args.config:
                filename = args.config
            else:
                filename = "config.ini"

            # if the file exists and is a file then use it
            if os.path.exists(filename) and os.path.isfile(filename):
                self.file = filename
            else:
                raise OSError("File {} does not exist.".format(filename))
        except OSError as ose:
            print(ose)
            exit(1)

        check = self.validate_config_file(filename)
        if check:
            self.config_data = self.read_config(filename)
        else:
            self.config_data = self.generate_default_config()

        # for k, v in config.items():
        #     for k2, v2 in v.items():
        #         print("{0}: {1}".format(k2, v2))
        # self.config = {s:dict(config.items(s)) for s in config.sections()}

    def get_config_data(self):
        return self.config_data

    def validate_config_file(self, filename):
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
                            raise OSError("Could not find config file in directory {0} - generating a default one.".format(tmp_config))
                    # Otherwise throw an exception
                    else:
                        raise OSError("Could not find config file in directory {0} - generating a default one.".format(tmp_config))
            else:
                raise OSError("The specified config file {0} does not exist - generating a default one.".format(filename))
        except OSError as ose:
            print(ose)

        if config is None:
            return False
        else:
            return config

    def generate_default_config_dict(self):
        config_dict = {
            "General": {
                "vmaf_version": 2
            },
            "Calculations": {
                "ffmpeg_location": "ffmpeg",
                "threads": mp.cpu_count(),
                "instances": 1,
                "psnr": False,
                "ssim": False,
                "ms_ssim": False,
                "model": "vmaf_v0.6.1",
                "log_name": "vmaf",
                "log_format": "xml"
            },
            "Graphing": {
                "output": "vmaf",
                "lower_boundary": "default",
                "custom": 0
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
        default_config = confp.ConfigParser()
        default_config.read_dict(self.generate_default_config_dict())

        with open("example.ini", "w") as config_file:
            default_config.write(config_file)

        return dict(default_config)

    def read_config(self, filename):
        self.config = confp.ConfigParser()
        self.config.read(filename)

        config_dict = self.generate_default_config_dict()

        self.config_data = dict()

        try:
            for section, option in config_dict.items():
                self.config_data[section] = dict()
                for k, v in option.items():
                    try:
                        if type(v) == str:
                            self.config_data[section][k] = self.config[section].get(k, v)
                        elif type(v) == bool:
                            self.config_data[section][k] = self.config[section].getboolean(k, v)
                        elif type(v) == int:
                            self.config_data[section][k] = self.config[section].getint(k, v)
                        elif type(v) == float:
                            self.config_data[section][k] = self.config[section].getfloat(k, v)
                    except confp.NoOptionError:
                        self.config_data[section][k] = v
        except confp.NoSectionError:
            for k, v in config_dict.items():
                self.config_data[section][k] = v

        return self.config_data
