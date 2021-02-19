import csv
import json
import os
import xml.etree.ElementTree as xml


class File_Reader:
    def __init__(self, file=None, config=False):
        try:
            filename = ""
            if file:
                filename = file
            else:
                filename = "config.ini"

            if os.path.exists(filename) and os.path.isfile(filename):
                # Get file extension to determien report file type.
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
        except OSError as ose:
            print(ose)
            exit(1)

    def validate_file(self, filename):
        """Validate the file."""

        file = None
        try:
            # Check if path given actually exists
            if os.path.exists(filename):
                # Check if path is a file or a directory
                if os.path.isfile(filename):
                    file = filename
                else:
                    raise OSError("The specified report file {0} does not exist.".format(filename))
            else:
                raise OSError("The specified report file {0} does not exist.".format(filename))
        except OSError as ose:
            print(ose)
            exit(1)

        if file is None:
            return False
        else:
            return config

    def read_file(self):
        if self.ext == "unspecified":
            with open(self.file, "r") as fil:
                check = fil.read(1)
                if check == "{":
                    self.ext = "json"
                elif check == "<":
                    self.ext = "xml"
                else:
                    self.ext = "csv"

        if self.ext == "json":
            return self.read_json()
        elif self.ext == "xml":
            return self.read_xml()
        elif self.ext == "csv":
            return self.read_csv()

    def read_xml(self):
        tree = xml.parse(self.file)
        root = tree.getroot()
        self.vmaf_version = root.attrib["version"]

        frame_level = -1
        for child in root:
            # if str(child.attrib)

            if str(child.attrib) != "frames":
                frame_level += 1

        with open(self.file, "r") as f:
            lines = f.readlines()
            file = [x.strip() for x in lines if "vmaf=\"" in x]
            vmafs = []
            for i in file:
                vmf = i[i.rfind("=\"") + 2: i.rfind("\"")]
                vmafs.append(float(vmf))

            vmafs = [round(float(x), 3) for x in vmafs if type(x) == float]

        return(vmafs)
