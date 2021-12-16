import csv
import json
from pathlib import Path

import defusedxml.ElementTree as xml

from vmaf_common import print_err

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_file_handler2 import VMAF_File_Handler


class VMAF_Report_Handler(VMAF_File_Handler):
    def __init__(
        self,
        file=None,
        config=False,
        datapoints=[
            "VMAF",
            "PSNR",
            "SSIM",
            "MS-SSIM",
        ],
    ):
        try:
            filename = ""
            if file:
                filename = file

                if Path(filename).exists() and Path(filename).is_file():
                    # Get file extension to determine report file type.
                    self.check_type(filename)
                else:
                    raise OSError("File {} does not exist.".format(filename))
            else:
                raise OSError("File {} does not exist.".format(filename))
        except OSError as ose:
            print_err(ose)
            exit(1)

        self.datapoints = datapoints

    def check_type(self, filename):
        ext = Path(filename).suffix.replace(".", "")
        if ext.lower() == "json":
            self.type = "json"
        elif ext.lower() == "xml":
            self.type = "xml"
        elif ext.lower() == "csv":
            self.type = "csv"
        else:
            tests = [self.check_csv, self.check_json, self.check_xml]
            filetype = list([func(filename) for func in tests])
            if any(filetype):
                tests[next((x for x in range(len(filetype)) if x))]
            else:
                msg = "File '{}' is not in any acceptable format."
                raise OSError(msg.format(self.file))

    def check_csv(self, filename):
        try:
            with open(filename, "r") as csv_file:
                csv.reader(csv_file)
            self.type = "csv"
            return True
        except csv.Error:
            return False

    def check_json(self, filename):
        try:
            json.load(filename)
            self.type = "json"
            return True
        except json.JSONDecodeError:
            return False

    def check_xml(self, filename):
        try:
            xml.parse(filename)
            self.type = "xml"
            return True
        except xml.ParseError:
            return False

    def read_file(self):
        # if self.type == "unspecified":
        # with open(self.file, "r") as f:
        #     check = f.read(1)
        #     if check == "{":
        #         self.type = "json"
        #     elif check == "<":
        #         self.type = "xml"
        #     else:
        #         self.type = "csv"

        if self.type == "json":
            return self.read_json()
        elif self.type == "xml":
            return self.read_xml()
        elif self.type == "csv":
            return self.read_csv()

    def read_xml(self):
        tree = xml.parse(self.file)
        root = tree.getroot()
        self.vmaf_version = root.attrib["version"]

        # frame_level = -1
        # for child in root:
        #     if str(child.attrib) != "frames":
        #         frame_level += 1

        data = {}
        with open(self.file, "r") as f:
            lines = f.readlines()

            for point in self.datapoints:
                data[point] = []

            for line in lines:
                sep = line.split(" ")
                for section in sep:
                    if "VMAF" in self.datapoints and section.strip().startswith('vmaf="'):
                        tmp = section.split('"')[1]
                        data["VMAF"].append(round(float(tmp), 3))
                    elif "PSNR" in self.datapoints and section.strip().startswith('psnr="'):
                        tmp = section.split('"')[1]
                        data["PSNR"].append(round(float(tmp), 3))
                    elif "SSIM" in self.datapoints and section.strip().startswith('ssim="'):
                        tmp = section.split('"')[1]
                        data["SSIM"].append(round(float(tmp), 3))
                    elif "MS-SSIM" in self.datapoints and section.strip().startswith('ms_ssim="'):
                        tmp = section.split('"')[1]
                        data["MS-SSIM"].append(round(float(tmp), 3))

        return data
