import csv
import json
import xml.etree.ElementTree as xml

class Report_Reader:
    def __init__(self, file):
        try:
            if os.path.exists(file) and os.path.isfile(file):
                # Get file extension to determien report file type.
                ext = file.split(".")[-1]
                if ext.lower() == "json":
                    self.type = "json"
                elif ext.lower() == "xml":
                    self.type = "xml"
                elif ext.lower() == "csv":
                    self.type = "csv"
                else:
                    self.type = "unspecified"

                self.file = file
            else:
                raise Exception(message="Report file {} does not exist.".format(file))
        except Exception as e:
            print(e)
            exit(1)

    def read_file():
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

    def read_xml():
        tree = xml.parse(self.file)
        root = tree.getroot()
        vmaf_version = root.attrib["version"]

        frame_level = -1
        for child in root:
            if str(child.attrib)

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
