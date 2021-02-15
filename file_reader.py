import configparser as confp
import csv
import json
import os
import xml.etree.ElementTree as xml


class File_Reader:
    def __init__(self, file):
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
                raise Exception(message="Report file {} does not exist.".format(file))
        except Exception as e:
            print(e)
            exit(1)

    def read_file(self):
        if self.ext == "unspecified":
            with open(self.file, "r") as fil:
                check = fil.read(1)
                if check == "{":
                    self.ext = "json"
                elif check == "<":
                    self.ext = "xml"
                elif check == "[":
                    self.ext = "ini"
                else:
                    self.ext = "csv"

        if self.ext == "json":
            return self.read_json()
        elif self.ext == "xml":
            return self.read_xml()
        elif self.ext == "csv":
            return self.read_csv()
        elif self.ext == "ini":
            return self.read_config()

    def read_config(self):
        config = confp.ConfigParser()
        config.read(self.file)

        self.config_data = dict()
        self.config_data["General"] = dict()
        if "General" in config.sections():
            self.config_data["General"]["ffmpeg_location"] = config["General"].get("ffmpeg_location", "ffmpeg")
            self.config_data["General"]["threads"] = int(config["General"].getint("threads", 0))
            self.config_data["General"]["instances"] = int(config["General"].getint("instances", 1))
        else:
            self.config_data["General"]["ffmpeg_location"] = "ffmpeg"
            self.config_data["General"]["threads"] = 0
            self.config_data["General"]["instances"] = 0

        self.config_data["Image Settings"] = dict()
        if "Image Settings" in config.sections():
            self.config_data["Image Settings"]["x"] = float(config["Image Settings"].getfloat("x", 1920))
            self.config_data["Image Settings"]["y"] = float(config["Image Settings"].getfloat("y", 1080))
            self.config_data["Image Settings"]["dpi"] = float(config["Image Settings"].getfloat("dpi", 100))
            self.config_data["Image Settings"]["format"] = config["Image Settings"].get("dpi", "svg"))
        else:
            self.config_data["Image Settings"]["x"] = 1920.0
            self.config_data["Image Settings"]["y"] = 1080.0
            self.config_data["Image Settings"]["dpi"] = 100.0
            self.config_data["Image Settings"]["format"] = "svg"

        self.config_data["Video Settings"] = dict()
        if "Video Settings" in config.sections():
            self.config_data["Video Settings"]["x"] = float(config["Video Settings"].getfloat("x", "1920"))
            self.config_data["Video Settings"]["y"] = float(config["Video Settings"].getfloat("y", "1080"))
            self.config_data["Video Settings"]["dpi"] = float(config["Video Settings"].getfloat("dpi", "100"))
            self.config_data["Video Settings"]["framerate"] = float(config["Video Settings"].getfloat("framerate", "60"))
        else:
            self.config_data["Video Settings"]["x"] = 1920.0
            self.config_data["Video Settings"]["y"] = 1080.0
            self.config_data["Video Settings"]["dpi"] = 100.0
            self.config_data["Video Settings"]["framerate"] = 60.0


    def get_config(self):
        return self.config_data


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
