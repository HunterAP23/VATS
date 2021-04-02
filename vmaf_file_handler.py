import configparser as confp
import csv
import json
import os
from pathlib import Path
from typing import Optional
# import xml.etree.ElementTree as xml

from HunterAP_Common import print_err


class VMAF_File_Handler:
    def __init__(self, file: str, file_type: Optional[str] = "config", ext: Optional[str] = "json", os_name: Optional[str] = "Windows", vmaf_version: Optional[int] = 2, program: Optional[str] = "Calculations"):
        self._file = None
        self._file_type = file_type
        self._os_name = os_name
        self._vmaf = vmaf_version
        self._program = program

        if self._file_type == "config":
            self._ext = [".ini"]
        elif self._file_type == "model":
            if self._vmaf == 1:
                self._ext = [".pkl"]
            else:
                self._ext = [".json"]
        elif self._file_type == "log":
            if ext is None:
                self._ext = [".json", ".csv", ".xml"]
            else:
                self._ext = list(ext)
        elif self._os_name == "Windows" and self._file_type == "executable":
            self._ext = [".exe"]
        elif self._os_name != "Windows" and self._file_type == "executable":
            self._ext = [""]

        try:
            will_exit = False
            tmp_file = Path(file)
            if tmp_file.exists():
                if tmp_file.is_file():
                    self._validate_file(tmp_file, will_exit)
                elif tmp_file.is_dir():
                    if self._file_type in ["model", "executable"]:
                        will_exit = True
                    elif self._file_type == "log":
                        if self._program != "Calculations":
                            will_exit = True
                    self._find_file(tmp_file, will_exit)
            else:
                msg = ""
                if self._file_type == "config":
                    msg = "WARNING: Config file \"{}\" does not exist. Generating default config.".format(file)
                elif self._file_type == "log":
                    if self._program == "Calculations":
                        if tmp_file.suffix == "":
                            self._file = str(Path(file + ".json"))
                        else:
                            self._file = str(Path(file))
                        return
                    msg = "ERROR: Log file \"{}\" does not exist.".format(file)
                elif self._file_type == "model":
                    msg = "ERROR: VMAF model file \"{}\" does not exist.".format(file)
                elif self._file_type == "executable":
                    # msg = "ERROR: Executable \"{}\" does not exist.".format(file)
                    for item in os.environ["PATH"].split(";"):
                        if self._file is None:
                            if (self._os_name == "Windows" and item.lower() != "c") or self._os_name != "Windows":
                                self._find_file(Path(item))
                        else:
                            return
                    if self._file is None:
                        msg = "ERROR: File \"{}\" does not exist.".format(file)
                        raise FileNotFoundError(msg)
                else:
                    msg = "ERROR: File \"{}\" does not exist.".format(file)
                raise FileNotFoundError(msg)
        except FileNotFoundError as fnfe:
            print_err(fnfe)
            if file_type == "config":
                self._file = "config.ini"
            else:
                print_err("The program will now exit.")
                exit(1)

    def get_file(self) -> str:
        return self._file

    def _find_file(self, loc: str, filename: str = "", should_exit: bool = False) -> None:
        try:
            if loc.exists():
                for entry in loc.iterdir():
                    if entry.is_file():
                        if self._file is None:
                            self._validate_file(entry, should_exit)
                        else:
                            return
            raise FileNotFoundError("ERROR: Could not find {0} file in \"{1}\".".format(self._file_type, loc))
        except FileNotFoundError as fnfe:
            print_err(fnfe)
            if type == "config":
                self._file = None
            else:
                if should_exit:
                    print_err("The program will now exit.")
                    exit(1)

    def _validate_file(self, file: str, should_exit: bool) -> None:
        exec_check = None
        if self._file_type == "executable":
            if self._os_name == "Windows" and file.suffix == ".exe":
                exec_check = True
            elif self._os_name != "Windows":
                exec_check = True
            else:
                exec_check = False

        model_error_type = None

        if file.suffix in self._ext or exec_check:
            if self._file_type == "config":
                self._file = str(file)
                return
            elif self._file_type == "model":
                check1 = bool(file.suffix == ".pkl" and self._vmaf == 1)
                check2 = bool(file.suffix == ".json" and self._vmaf == 2)
                if check1 or check2:
                    self._file = str(file)
                    return
            elif self._file_type == "log":
                self._file = str(file)
            elif self._file_type == "executable":
                if os.access(file, os.X_OK):
                    if self._os_name == "Windows":
                        if file.suffix == "" and file.name == "ffmpeg":
                            self._file = str(file.joinpath(".exe"))
                            return
                        elif file.name == "ffmpeg.exe":
                            self._file = str(file)
                            return
                    else:
                        if file.name == "ffmpeg":
                            self._file = str(file)
                            return

        try:
            if self._file_type == "config":
                msg = "WARNING: File \"{0}\" is not a config file."
                msg = msg.format(file)
                raise FileNotFoundError(msg)
            elif self._file_type == "log":
                msg = "WARNING: File \"{0}\" is not a valid VMAF log."
                msg = msg.format(file)
                raise FileNotFoundError(msg)
            elif self._file_type == "model":
                msg = ""
                if model_error_type is None:
                    msg = "WARNING: File \"{0}\" is not a valid VMAF log."
                    msg = msg.format(file)
                else:
                    msg = "WARNING: File \"{0}\" is not valid for VMAF version {1}."
                    msg = msg.format(file, self._vmaf)
                raise FileNotFoundError(msg)
            elif self._file_type == "executable":
                msg = "WARNING: File \"{0}\" is not a valid executable.."
                msg = msg.format(file)
                raise FileNotFoundError(msg)
        except FileNotFoundError as fnfe:
            if should_exit:
                print_err(fnfe)
                print_err("The program will now exit.")
                exit(1)
