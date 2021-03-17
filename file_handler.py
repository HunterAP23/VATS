import configparser as confp
import csv
import json
import multiprocessing as mp
import os
from pathlib import Path
import xml.etree.ElementTree as xml


class File_Handler:
    def __init__(self, file, file_type="config"):
        self.file = None
        self.file_type = file_type
        try:
            tmp_file = Path(file)
            if tmp_file.exists():
                if tmp_file.is_file():
                    self.file = file
                elif tmp_file.is_dir():
                    self.find_file(file)
            else:
                if file_type == "config":
                    raise FileNotFoundError("WARNING: Config file \"{}\" does not exist. Generating default config.".format(file))
                elif file_type == "log":
                    raise FileNotFoundError("ERROR: Log file \"{}\" does not exist. The program will now exit.".format(file))
                else:
                    raise FileNotFoundError("ERROR: File \"{}\" does not exist. The program will now exit.".format(file))
        except FileNotFoundError as fnfe:
            print(fnfe)
            if file_type == "config":
                self.file = "config.ini"
            else:
                exit(1)

    def find_file(self, loc):
        try:
            loc_path = Path(loc)
            for entry in loc_path.iterdir():
                if entry.is_file():
                    if self.file_type == "config":
                        if entry.suffix == ".ini":
                            if str(Path(entry.name)) == "config.ini":
                                # print("CONFIG: {0}".format(Path(os.getcwd()).joinpath(entry.name)))
                                self.file = str(Path(os.getcwd()).joinpath(entry.name))
                            else:
                                # print("CONFIG: {0}".format(Path(entry.name).joinpath(entry.parent)))
                                self.file = str(Path(entry.name).joinpath(entry.parent))
                            return
                    elif self.file_type == "log":
                        if entry.suffix in [".json", ".xml", ".csv"]:
                            # self.file =
                            return
                        else:
                            pass
                    elif self.file_type == "model":
                        if entry.suffix in [".pkl", ".json"]:
                            # self.file =
                            return
                        else:
                            pass
                else:
                    pass

            if self.file_type == "config":
                raise FileNotFoundError("WARNING: Could not find any config files in path \"{0}\". Generating default config.".format(loc))
            elif self.file_type == "log":
                raise FileNotFoundError("ERROR: Could not find any log files in path \"{0}\". The program will now exit.".format(loc))
            elif self.file_type == "model":
                raise FileNotFoundError("ERROR: Could not find any model files in path \"{0}\". The program will now exit.".format(loc))


        except FileNotFoundError as fnfe:
            print(fnfe)
            if type == "config":
                self.file = None
            else:
                print("ERROR: Could not find {0} file specified. The program will now exit.".format(type))
                exit(1)

    def find_log(self, loc):
        loc_path = Path(loc)
        file_found = False
        for entry in loc_path.iterdir():
            if file_found:
                if str(Path(entry.name)) == "config.ini":
                    self.file = str(Path(os.getcwd()).joinpath(entry.name))
                else:
                    self.file = str(Path(entry.name).joinpath(entry.parent))
                return
            if entry.is_file():
                if entry.suffix == ".json":
                    self.log_type = "json"
                    file_found = True
                elif entry.suffix == ".xml":
                    self.log_type = "xml"
                    file_found = True
                elif entry.suffix == ".csv":
                    self.log_type = "csv"
                    file_found = True

        print("ERROR: Could not find any log files in path \"{0}\". The program will now exit.".format(loc))
        exit(1)
