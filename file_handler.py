import configparser as confp
import csv
import json
import multiprocessing as mp
from pathlib import Path
import xml.etree.ElementTree as xml

class File_Handler:
    def __init__(self, file, config=False):
        try:
            tmp_file = Path(file)
            if tmp_file.exists():
                if tmp_file.is_file():
                    self.file = file
                elif tmp_file.is_dir():
                    if config:
                        self.find_config(file)
                    else:
                        self.find_report(file)
            else:
                if config:
                    raise FileNotFoundError("Config file \"{}\" does not exist. Using default config.".format(file))
                else:
                    raise FileNotFoundError("Report file \"{}\" does not exist. The program will now exit.".format(file))
        except FileNotFoundError as fnfe:
            print(fnfe)
            if config:
                self.generate_default_config()
            else:
                exit(1)

    def search_config(self, loc):
        loc_path = Path(loc)
        for entry in loc_path.iterdir():
            if entry.is_file():
                if entry.suffix == ".ini":
                    self.file = str(Path(entry.name).joinpath(entry.parent))
                    return
            else:
                pass

        print("Could not find any config files in path \"{0}\". Using default config.".format(loc))
        self.generate_config()

    def search_report(self, loc):
        loc_path = Path(loc)
        file_found = False
        for entry in loc_path.iterdir():
            if file_found:
                self.file = str(Path(entry.name).joinpath(entry.parent))
                return
            if entry.is_file():
                if entry.suffix == ".json":
                    self.report_type = "json"
                    file_found = True
                elif entry.suffix == ".xml":
                    self.report_type = "xml"
                    file_found = True
                elif entry.suffix == ".csv":
                    self.report_type = "csv"
                    file_found = True

        print("Could not find any report files in path \"{0}\". The program will nwo exit.".format(loc))
        exit(1)

    def generate_confg(self):
        self.config_data = {
            "General": {
                "vmaf_version": 2
            },
            "Calculations": {
                "ffmpeg_location": "ffmpeg",
                "threads": 0,
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

        self.config = confp.ConfigParser()
        self.config.read_dict(self.generate_default_config_dict())

        with open("config.ini", "w") as config_file:
            self.config.write(config_file)

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
