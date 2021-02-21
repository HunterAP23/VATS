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
        for entry in loc_path.iterdir()
            if entry.is_file():
                if entry.suffix == ".ini"
                    self.file = str(Path(entry.name).joinpath(entry.parent)
                    return
            else:
                pass

        try:
            if self.file is None:
                raise FileNotFoundError("could not find any config files in path \"{0}\". The program will not exit.".format(loc))


    def search_report(self, loc):
        return
