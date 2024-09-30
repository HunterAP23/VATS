import json
import re
from pathlib import Path
from pprint import pprint

import ffmpeg


class Encoder:
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name
        self.test_statements: list = []
        self.rc_modes: list = ["cbr", "vbr", "crf", "cqp"]
        self.presets: list = [
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ]
        self.hardware = []

    def get_hardware(self) -> list:
        return self.hardware

    def get_rc_modes(self) -> list:
        return self.rc_modes

    def get_presets(self) -> list:
        return self.presets

    def get_profiles(self) -> list:
        ...


def get_encoders():
    stream = ffmpeg.input("", **{"encoders": None})
    stream = ffmpeg.output(stream, "-", format="null")
    proc = ffmpeg.run_async(stream, quiet=True)
    out, err = proc.communicate()
    retcode = proc.poll()
    if retcode:
        print(err.decode())
        exit()
    lines = out.decode().strip().split("\n")
    skip = True
    encoders: dict = {}
    for line in lines:
        line = line.lstrip(" ").lstrip("\t")
        if skip and "------" in line:
            skip = False
        elif not skip:
            if line.startswith("V"):
                enc_type, enc_name, enc_desc = re.sub(" +", " ", line).split(
                    " ", 2
                )
                encoders[enc_name.strip()] = {"Description": enc_desc.strip()}
    del skip
    del stream
    del proc

    encnum = 0
    for encoder, vals in encoders.items():
        # print(f"{encoder}: {vals['Description']}")
        stream = ffmpeg.input("")
        stream = ffmpeg.output(stream, "-", format="null")
        stream = stream.global_args("-hide_banner", "-h", f"encoder={encoder}")
        proc = ffmpeg.run_async(stream, quiet=True)
        out, err = proc.communicate()
        if retcode:
            print(err.decode())
            exit()
        lines = re.sub(" +", " ", out.decode().strip()).split("\n")
        del lines[0]
        next_opt = None
        vals["Options"] = {}
        to_replace = ["E..V.......", "E..V......P"]
        for i, line in enumerate(lines):
            line = line.strip()
            for r in to_replace:
                line = line.replace(r, "")
            line = line.strip()
            if line.startswith(encoder) or "AVOptions" in line:
                continue
            elif list(filter(line.startswith, ["General capabilities", "Threading capabilities", "Supported hardware devices", "Supported pixel formats", "Supported framerates"])) != []:
                line = line.strip().replace(" capabilities", "").replace("Supported ", "").title()
                items = line.split(": ", 1)
                if len(items) == 2:
                    items[1] = items[1].split(" ")
                    if len(items[1]) == 1 and items[1][0] == "none":
                        items[1] = None
                    encoders[encoder][items[0]] = items[1]
            elif line.startswith("-"):
                opt, opt_desc = line.replace("-", "", 1).split(">", 1)
                opt, opt_type = opt.split("<", 1)
                opt = opt.strip()
                opt_type = opt_type.replace("<", "").replace(">", "").strip()
                opt_desc = opt_desc.strip()
                opt_range_min = None
                opt_range_max = None
                opt_default = None
                if "(from " in opt_desc:
                    opt_desc, opt_range = opt_desc.split("(from ", 1)
                    opt_range = opt_range.replace(")", "")
                    if "(default " in opt_range.lower():
                        if "(default " in opt_range:
                            opt_range, opt_default = opt_range.split(" (default ", 1)
                        else:
                            opt_range, opt_default = opt_range.split(" (Default ", 1)
                        opt_default = opt_default.replace(")", "").strip()
                    opt_range_min, opt_range_max = opt_range.split(" to ")
                elif "(default " in opt_desc:
                    opt_desc, opt_default = opt_desc.split("(default ", 1)
                    opt_default = opt_default.replace(")", "").strip()
                vals["Options"][opt] = {
                    "Type": opt_type,
                    "Description": opt_desc,
                    "Default": opt_default,
                }
                if all([opt_range_max, opt_range_min]):
                    vals["Options"][opt]["Range"] = {"Min": opt_range_min, "Max": opt_range_max}
                next_opt = opt
            elif not line.startswith("-"):
                try:
                    opt, opt_desc = line.split(" ", 1)
                    if vals["Options"][next_opt]["Type"] == "flags":
                        vals["Options"][next_opt][opt.strip()] = opt_desc.strip()
                    else:
                        if "  " in opt_desc.strip():
                            opt_val, opt_val_desc = opt_desc.strip().split("  ")
                            vals["Options"][next_opt][opt.strip()] = {"Value": opt_val.strip(), "Description": opt_val_desc.strip()}
                        else:
                            vals["Options"][next_opt][opt.strip()] = {"Value": opt_desc.strip()}
                except KeyError as ke:
                    print(ke)
                    print(line)
                    print(vals["Options"])
                    exit()
            else:
                print(line)
                exit()
        # if encoder == "libsvtav1":
        #     json.dump(encoders, open("encoders.json", "w"), indent=4)
        #     exit()
        
    for encoder, vals in encoders.items():
        if len(vals["Options"]) == 0:
            del vals["Options"]
    json.dump(encoders, open("encoders.json", "w"), indent=4)
    

def get_decoders():
    stream = ffmpeg.input("", **{"decoders": None})
    stream = ffmpeg.output(stream, "-", format="null")
    proc = ffmpeg.run_async(stream, quiet=True)
    out, err = proc.communicate()
    retcode = proc.poll()
    if retcode:
        print(err.decode())
        exit()
    lines = out.decode().strip().split("\n")
    skip = True
    decoders: dict = {}
    for line in lines:
        line = line.lstrip(" ").lstrip("\t")
        if skip and "------" in line:
            skip = False
        elif not skip:
            if line.startswith("V"):
                dec_type, dec_name, dec_desc = re.sub(" +", " ", line).split(
                    " ", 2
                )
                decoders[dec_name.strip()] = {"Description": dec_desc.strip()}
    del skip
    del stream
    del proc

    decnum = 0
    for decoder, vals in decoders.items():
        # print(f"{decoder}: {vals['Description']}")
        stream = ffmpeg.input("")
        stream = ffmpeg.output(stream, "-", format="null")
        stream = stream.global_args("-hide_banner", "-h", f"decoder={decoder}")
        proc = ffmpeg.run_async(stream, quiet=True)
        out, err = proc.communicate()
        if retcode:
            print(err.decode())
            exit()
        lines = re.sub(" +", " ", out.decode().strip()).split("\n")
        del lines[0]
        next_opt = None
        vals["Options"] = {}
        to_replace = [".D.V......P", ".D.V.......", ".D.V..X...."]
        for i, line in enumerate(lines):
            line = line.strip()
            for r in to_replace:
                line = line.replace(r, "")
            line = line.strip()
            if line.startswith(decoder) or "AVOptions" in line:
                continue
            elif list(filter(line.startswith, ["General capabilities", "Threading capabilities", "Supported hardware devices", "Supported pixel formats", "Supported framerates"])) != []:
                line = line.strip().replace(" capabilities", "").replace("Supported ", "").title()
                items = line.split(": ", 1)
                if len(items) == 2:
                    items[1] = items[1].split(" ")
                    if len(items[1]) == 1 and items[1][0] == "none":
                        items[1] = None
                    decoders[decoder][items[0]] = items[1]
            elif line.startswith("-"):
                opt, opt_desc = line.replace("-", "", 1).split(">", 1)
                opt, opt_type = opt.split("<", 1)
                opt = opt.strip()
                opt_type = opt_type.replace("<", "").replace(">", "").strip()
                opt_desc = opt_desc.strip()
                opt_range_min = None
                opt_range_max = None
                opt_default = None
                if "(from " in opt_desc:
                    opt_desc, opt_range = opt_desc.split("(from ", 1)
                    opt_range = opt_range.replace(")", "")
                    if "(default " in opt_range.lower():
                        if "(default " in opt_range:
                            opt_range, opt_default = opt_range.split(" (default ", 1)
                        else:
                            opt_range, opt_default = opt_range.split(" (Default ", 1)
                        opt_default = opt_default.replace(")", "").strip()
                    opt_range_min, opt_range_max = opt_range.split(" to ")
                elif "(default " in opt_desc:
                    opt_desc, opt_default = opt_desc.split("(default ", 1)
                    opt_default = opt_default.replace(")", "").strip()
                vals["Options"][opt] = {
                    "Type": opt_type,
                    "Description": opt_desc,
                    "Default": opt_default,
                }
                if all([opt_range_max, opt_range_min]):
                    vals["Options"][opt]["Range"] = {"Min": opt_range_min, "Max": opt_range_max}
                next_opt = opt
            elif not line.startswith("-"):
                try:
                    opt, opt_desc = line.split(" ", 1)
                    if vals["Options"][next_opt]["Type"] == "flags":
                        vals["Options"][next_opt][opt.strip()] = opt_desc.strip()
                    else:
                        if "  " in opt_desc.strip():
                            opt_val, opt_val_desc = opt_desc.strip().split("  ")
                            vals["Options"][next_opt][opt.strip()] = {"Value": opt_val.strip(), "Description": opt_val_desc.strip()}
                        else:
                            vals["Options"][next_opt][opt.strip()] = {"Value": opt_desc.strip()}
                except KeyError as ke:
                    print(ke)
                    print(line)
                    print(vals["Options"])
                    exit()
            else:
                print(line)
                exit()
        # if decoder == "libsvtav1":
        #     json.dump(decoders, open("decoders.json", "w"), indent=4)
        #     exit()
        
    for decoder, vals in decoders.items():
        if len(vals["Options"]) == 0:
            del vals["Options"]
    json.dump(decoders, open("decoders.json", "w"), indent=4)


if __name__ == "__main__":
    get_encoders()
    get_decoders()
