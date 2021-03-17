import configparser as confp
import csv
import json
import multiprocessing as mp
import os
from pathlib import Path
from typing import AnyStr
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
import xml.etree.ElementTree as xml


class VMAF_File_Handler:
    def __init__(self, file, file_type="config", exec_name=None, os_name="Windows"):
        self.file = None
        self.file_type = file_type
        self.exec_name = exec_name
        self.os_name = os_name
        try:
            tmp_file = Path(file)
            if tmp_file.exists():
                if tmp_file.is_file():
                    self.file = file
                elif tmp_file.is_dir():
                    self.find_file(file, should_exit=True)

            else:
                msg = ""
                if file_type == "config":
                    msg = "WARNING: Config file \"{}\" does not exist. Generating default config.".format(file)
                elif file_type == "log":
                    msg = "ERROR: Log file \"{}\" does not exist. The program will now exit.".format(file)
                elif file_type == "model":
                    msg = "ERROR: VMAF model file \"{}\" does not exist. The program will now exit.".format(file)
                elif file_type == "executable":
                    # msg = "ERROR: Executable \"{}\" does not exist. The program will now exit.".format(file)
                    for item in os.environ["PATH"].split(";"):
                        if self.file is None:
                            if item.lower() != "c":
                                self.find_file(item)
                        else:
                            return
                else:
                    msg = "ERROR: File \"{}\" does not exist. The program will now exit.".format(file)
                raise FileNotFoundError(msg)
        except FileNotFoundError as fnfe:
            print(fnfe)
            if file_type == "config":
                self.file = "config.ini"
            else:
                exit(1)

    def find_file(self, loc, should_exit=False):
        try:
            loc_path = Path(loc)
            if loc_path.exists():
                for entry in loc_path.iterdir():
                    if entry.is_file():
                        if self.file_type == "config":
                            if entry.suffix == ".ini":
                                self.file = str(Path(entry))
                                return
                        elif self.file_type == "log":
                            if entry.suffix in [".json", ".xml", ".csv"]:
                                self.file = str(Path(entry))
                                return
                        elif self.file_type == "model":
                            if entry.suffix in [".pkl", ".json"]:
                                self.file = str(Path(entry))
                                return
                        elif self.file_type == "executable":
                            if os.access(entry, os.X_OK):
                                if self.os_name == "Windows":
                                    if ".exe" in self.exec_name:
                                        if entry.name == self.exec_name:
                                            self.file = str(Path(entry))
                                            return
                                    else:
                                        if entry.name == self.exec_name + ".exe":
                                            self.file = str(Path(entry))
                                            return
                                else:
                                    if entry.name == self.exec_name:
                                        self.file = str(Path(entry))
                                        return

                if should_exit:
                    if self.file_type == "config":
                        msg = "WARNING: Could not find any config files in path \"{0}\". Generating default config."
                        msg = msg.format(loc)
                        raise FileNotFoundError(msg)
                    elif self.file_type == "log":
                        msg = "ERROR: Could not find any VMAF log files in path \"{0}\". The program will now exit."
                        msg = msg.format(loc)
                        raise FileNotFoundError(msg)
                    elif self.file_type == "model":
                        msg = "ERROR: Could not find any VMAF model files in path \"{0}\". The program will now exit."
                        msg = msg.format(loc)
                        raise FileNotFoundError(msg)
                    elif self.file_type == "executable":
                        msg = "ERROR: Could not find any executables in path \"{0}\". The program will now exit."
                        msg = msg.format(loc)
                        raise FileNotFoundError(msg)

        except FileNotFoundError as fnfe:
            print(fnfe)
            if type == "config":
                self.file = None
            else:
                print("ERROR: Could not find {0} file specified. The program will now exit.".format(type))
                exit(1)

    # def find_log(self, loc):
    #     loc_path = Path(loc)
    #     file_found = False
    #     for entry in loc_path.iterdir():
    #         if file_found:
    #             if str(Path(entry.name)) == "config.ini":
    #                 self.file = str(Path(os.getcwd()).joinpath(entry.name))
    #             else:
    #                 self.file = str(Path(entry.name).joinpath(entry.parent))
    #             return
    #         if entry.is_file():
    #             if entry.suffix == ".json":
    #                 self.log_type = "json"
    #                 file_found = True
    #             elif entry.suffix == ".xml":
    #                 self.log_type = "xml"
    #                 file_found = True
    #             elif entry.suffix == ".csv":
    #                 self.log_type = "csv"
    #                 file_found = True
    #
    #     print("ERROR: Could not find any log files in path \"{0}\". The program will now exit.".format(loc))
    #     exit(1)
