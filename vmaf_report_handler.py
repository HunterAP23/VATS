import csv
import json
import os
import xml.etree.ElementTree as xml
from pathlib import Path

from HunterAP_Common import print_err

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_file_handler import VMAF_File_Handler


class VMAF_Report_Handler(VMAF_File_Handler):
    def __init__(self, file=None, config=False):
        try:
            filename = ""
            if file:
                filename = file

                if Path(filename).exists() and Path(filename).is_file():
                    # Get file extension to determine report file type.
                    ext = filename.split(".")[-1]
                    if ext.lower() == "json":
                        self.type = "json"
                    elif ext.lower() == "xml":
                        self.type = "xml"
                    elif ext.lower() == "csv":
                        self.type = "csv"
                    elif ext.lower() == "ini":
                        self.type = "ini"
                    else:
                        self.type = "unspecified"

                    self.file = filename
                else:
                    raise OSError("File {} does not exist.".format(filename))
            else:
                raise OSError("File {} does not exist.".format(filename))
        except OSError as ose:
            print_err(ose)
            exit(1)

        # try:
        #     if config:
        #         if Path(filename).exists() and Path(filename).is_file():
        #             self._config = VMAF_Config_Handler(config)
        #         else:
        #             raise OSError("File {} does not exist.".format(filename))
        #     else:
        #         config = Path(__file__).parent.joinpath("config.ini")
        #         if Path(filename).exists() and Path(filename).is_file():
        #             self._config = VMAF_Config_Handler(config)
        #         else:
        #             raise OSError("File {} does not exist.".format(filename))
        # except OSError as ose:
        #     print_err(ose)
        #     exit(1)

    def validate_file(self, filename):
        """Validate the file."""

        try:
            # Check if path given actually exists
            if filename is None:
                return False
            elif Path(filename).exists():
                # Check if path is a file or a directory
                if Path(filename).is_file():
                    return filename
                else:
                    raise OSError("The specified report file {0} does not exist.".format(filename))
            else:
                raise OSError("The specified report file {0} does not exist.".format(filename))
        except OSError as ose:
            print_err(ose)
            exit(1)

    def read_file(self):
        if self.type == "unspecified":
            with open(self.file, "r") as fil:
                check = fil.read(1)
                if check == "{":
                    self.type = "json"
                elif check == "<":
                    self.type = "xml"
                else:
                    self.type = "csv"

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

            vmaf_lines = []
            psnr_lines = []
            ssim_lines = []
            ms_ssim_lines = []
            for line in lines:
                sep = line.split(" ")
                for section in sep:
                    if section.strip().startswith('vmaf="'):
                        tmp = section.split('"')[1]
                        vmaf_lines.append(round(float(tmp), 3))
                    elif section.strip().startswith('psnr="'):
                        tmp = section.split('"')[1]
                        psnr_lines.append(round(float(tmp), 3))
                    elif section.strip().startswith('ssim="'):
                        tmp = section.split('"')[1]
                        ssim_lines.append(round(float(tmp), 3))
                    elif section.strip().startswith('ms_ssim="'):
                        tmp = section.split('"')[1]
                        ms_ssim_lines.append(round(float(tmp), 3))

            data["vmaf"] = vmaf_lines
            data["psnr"] = psnr_lines
            data["ssim"] = ssim_lines
            data["ms_ssim"] = ms_ssim_lines

        return data
