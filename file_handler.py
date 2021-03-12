import configparser as confp
import csv
import json
import multiprocessing as mp
import os
from pathlib import Path
import xml.etree.ElementTree as xml

class File_Handler:
    def __init__(self, file, config=False):
        self.file = None
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
                    raise FileNotFoundError("Config file \"{}\" does not exist. Generating default config.".format(file))
                else:
                    raise FileNotFoundError("Report file \"{}\" does not exist. The program will now exit.".format(file))
        except FileNotFoundError as fnfe:
            print(fnfe)
            if config:
                self.file = "config.ini"
            else:
                exit(1)

    def find_config(self, loc):
        loc_path = Path(loc)
        for entry in loc_path.iterdir():
            if entry.is_file():
                if entry.suffix == ".ini":
                    if str(Path(entry.name)) == "config.ini":
                        self.file = str(Path(os.getcwd()).joinpath(entry.name))
                    else:
                        self.file = str(Path(entry.name).joinpath(entry.parent))
                    return
            else:
                pass

        print("Could not find any config files in path \"{0}\". Generating default config.".format(loc))
        self.file = None

    def find_report(self, loc):
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
                    self.report_type = "json"
                    file_found = True
                elif entry.suffix == ".xml":
                    self.report_type = "xml"
                    file_found = True
                elif entry.suffix == ".csv":
                    self.report_type = "csv"
                    file_found = True

        print("Could not find any report files in path \"{0}\". The program will now exit.".format(loc))
        exit(1)
