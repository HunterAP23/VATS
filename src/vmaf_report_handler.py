import csv
import json
from pathlib import Path

import defusedxml.ElementTree as xml

from vmaf_common import print_err

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_file_handler import VMAF_File_Handler


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

        self._datapoints = datapoints

    def check_type(self, filename):
        ext = Path(filename).suffix.replace(".", "")
        if ext.lower() == "json":
            self._type = "json"
        elif ext.lower() == "xml":
            self._type = "xml"
        elif ext.lower() == "csv":
            self._type = "csv"

        tests = {
            "csv": self.check_csv,
            "json": self.check_json,
            "xml": self.check_xml,
        }
        filetype = {ftype: func(filename) for ftype, func in tests.items()}
        if any(filetype.values()):
            self._type = list(filter(lambda x: x[1], filetype.items()))[0][0]
        else:
            msg = "File '{}' is not in any acceptable format."
            raise OSError(msg.format(self.file))

    def check_csv(self, filename):
        try:
            with open(filename, "r") as csv_file:
                csv.reader(csv_file)
            self._type = "csv"
            return True
        except Exception:
            return False

    def check_json(self, filename):
        try:
            json.load(filename)
            self._type = "json"
            return True
        except Exception:
            return False

    def check_xml(self, filename):
        try:
            for item in xml.iterparse(filename, events="end"):
                break
            self._type = "xml"
            return True
        except Exception:
            return False

    def read_file(self):
        # if self._type == "unspecified":
        # with open(self.file, "r") as f:
        #     check = f.read(1)
        #     if check == "{":
        #         self._type = "json"
        #     elif check == "<":
        #         self._type = "xml"
        #     else:
        #         self._type = "csv"

        if self._type == "json":
            return self.read_json()
        elif self._type == "xml":
            return self.read_xml()
        elif self._type == "csv":
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

            for point in self._datapoints:
                data[point] = []

            for line in lines:
                sep = line.split(" ")
                for section in sep:
                    if "VMAF" in self._datapoints and section.strip().startswith('vmaf="'):
                        tmp = section.split('"')[1]
                        data["VMAF"].append(round(float(tmp), 3))
                    elif "PSNR" in self._datapoints and section.strip().startswith('psnr="'):
                        tmp = section.split('"')[1]
                        data["PSNR"].append(round(float(tmp), 3))
                    elif "SSIM" in self._datapoints and section.strip().startswith('ssim="'):
                        tmp = section.split('"')[1]
                        data["SSIM"].append(round(float(tmp), 3))
                    elif "MS-SSIM" in self._datapoints and section.strip().startswith('ms_ssim="'):
                        tmp = section.split('"')[1]
                        data["MS-SSIM"].append(round(float(tmp), 3))

        return data
