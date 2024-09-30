import concurrent.futures as cf
import itertools
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor as tpe
from fractions import Fraction
from functools import partial
from pathlib import Path
from pprint import pprint
from subprocess import PIPE
from traceback import print_exc
from typing import Any, Union

import click
import dearpygui.dearpygui as dpg
import ffmpeg

from VATS_Common import os_check


class EncoderCheckbox:
    def __init__(self, name: str, label: str, user_data: dict):
        """_summary_

        Args:
            name (str): _description_
            label (str): _description_
            user_data (dict): _description_
        """
        self.name = name
        self.label = label
        self.user_data = user_data

    def set_callback(self, callback):
        """_summary_

        Args:
            callback (function): _description_
        """
        self.callback = callback

    def get_label(self):
        """_summary_

        Returns:
            str: _description_
        """
        return self.label


def write_output(tag: str, msg: str):
    """_summary_

    Args:
        tag (str): _description_
        msg (str): _description_
    """
    dpg.set_value(tag, f"{dpg.get_value(tag)}{msg}\n")
    print(msg)


def do_thing(sender, app_data, args: dict):
    for arg_name, arg_val in args.items():
        write_output("Output_Box", f"{arg_name}: {arg_val}")


def encoder_callback(sender, app_data, user_data):
    if dpg.get_value(sender):
        write_output("Output_Box", f"Sender: {sender}")
        write_output("Output_Box", f"Label: {dpg.get_item_label(sender)}")
        write_output("Output_Box", f"App Data: {app_data}")
        write_output(
            "Output_Box", f"Test Success: {dpg.get_item_label(sender)}"
        )
        if user_data[dpg.get_item_label(sender)] is None:
            pix_fmt = "nv12"
            if "av1" in sender:
                pix_fmt = "nv12"
            stream = ffmpeg.input(
                str(Path("G:\\Shooters_HEVC_Preset-slow_QP_1.mp4")),
                hide_banner=None,
            )
            stream = ffmpeg.output(
                stream, "-", vcodec=sender, pix_fmt=pix_fmt, t=1, format="null"
            )
            write_output("Output_Box", stream.get_args())
            proc = ffmpeg.run_async(stream, quiet=True)
            out, err = proc.communicate()
            retcode = proc.poll()
            if retcode:
                print(
                    f"Encoder {dpg.get_item_label(sender)} failed to encode with error {err.decode()}"
                )
                dpg.set_value(sender, False)
                dpg.disable_item(sender)
            else:
                print(
                    f"Encoder {dpg.get_item_label(sender)} is available on this system."
                )
    else:
        write_output("Output_Box", f"Unchecked {dpg.get_item_label(sender)}")


def clear_output(sender, app_data, user_data):
    dpg.set_value("Output_Box", "")


@click.command()
@click.option(
    "--reference_dir",
    type=click.Path(exists=True),
    required=False,
    help="Path to a folder containing all the reference files you want to use in the benchmark.",
)
@click.option(
    "--config_file",
    type=click.Path(exists=True),
    required=False,
    help="Config file path.",
)
@click.option(
    "--ffmpeg",
    type=click.Path(exists=True),
    required=False,
    help="FFmpeg argument.",
)
@click.option(
    "--nogui",
    is_flag=True,
    default=False,
    required=False,
    help="Run the application in console mode without a GUI.",
)
@click.option(
    "--psnr",
    is_flag=True,
    default=True,
    required=False,
    help="Use PSNR metric.",
)
@click.option(
    "--ssim",
    is_flag=True,
    default=True,
    required=False,
    help="Use SSIM metric.",
)
@click.option(
    "--ms_ssim",
    is_flag=True,
    default=True,
    required=False,
    help="Use MS-SSIM metric.",
)
@click.option(
    "--psnr_hvs",
    is_flag=True,
    default=True,
    required=False,
    help="Use PSNR-HVS metric.",
)
@click.option(
    "--subsamples",
    type=click.IntRange(1, 60),
    default=1,
    required=False,
    help="Number of subsamples.",
)
@click.option(
    "--models",
    type=click.Choice(["vmaf_v0.6.1", "vmaf_v0.6.1neg", "vmaf_4k_v0.6.1"]),
    default=["vmaf_v0.6.1", "vmaf_v0.6.1neg", "vmaf_4k_v0.6.1"],
    multiple=True,
    required=False,
    help="List of VMAF models to utilize.",
)
@click.option(
    "--log_format",
    type=click.Choice(["xml", "json", "csv"]),
    default="xml",
    required=False,
    help="VMAF log format.",
)
def run_app(
    reference_dir,
    config_file,
    ffmpeg,
    nogui,
    psnr,
    ssim,
    ms_ssim,
    psnr_hvs,
    subsamples,
    models,
    log_format,
):
    if nogui and not all(reference_dir, config_file, ffmpeg):
        print(
            "You must provide the reference_dir, config_file, and ffmpeg arguments in CLI mode."
        )
        sys.exit(1)
    args = {
        "No GUI": nogui,
        "Reference Directory": reference_dir,
        "Config File": config_file,
        "FFmpeg": ffmpeg,
        "PSNR": psnr,
        "SSIM": ssim,
        "MS-SSIM": ms_ssim,
        "PSNR-HVS": psnr_hvs,
        "Subsamples": subsamples,
        "Models": models,
        "Log Format": log_format,
        "Operating System": os_check(),
    }
    __encoder_tests: dict = {
        "libx264": {"Label": "libx264 / AVC", "Enabled": None},
        "libx265 / HEVC": {"Codec": "libx265", "Enabled": None},
        "NVENC H.264": {"Codec": "h264_nvenc", "Enabled": None},
        "NVENC HEVC": {"Codec": "hevc_nvenc", "Enabled": None},
        "AMF H.264": {"Codec": "h264_amf", "Enabled": None},
        "AME HEVC": {"Codec": "hevc_amf", "Enabled": None},
        "QuickSync H.264": {"Codec": "h264_qsv", "Enabled": None},
        "QuickSync HEVC": {"Codec": "hevc_qsv", "Enabled": None},
        "VideoToolbox H.264": {"Codec": "h264_videotoolbox", "Enabled": None},
        "VideoToolbox HEVC": {"Codec": "hevc_videotoolbox", "Enabled": None},
        "AOM AV1": {"Codec": "libaom-av1", "Enabled": None},
        "SVT AV1": {"Codec": "libsvtav1", "Enabled": None},
    }
    if args["No GUI"]:
        return
    else:
        dpg.create_context()
        dpg.create_viewport(
            title="VATS", width=1280, height=720, resizable=True
        )
        with dpg.window(
            label="VATS",
            width=1280,
            height=720,
            no_resize=True,
            no_move=True,
            no_title_bar=True,
        ):
            dpg.add_input_text(
                label="Reference Directory",
                default_value=args["Reference Directory"],
            )
            dpg.add_input_text(
                label="Config File", default_value=args["Config File"]
            )
            dpg.add_input_text(
                label="FFmpeg Argument", default_value=args["FFmpeg"]
            )
            dpg.add_checkbox(label="PSNR", default_value=args["PSNR"])
            dpg.add_checkbox(label="SSIM", default_value=args["SSIM"])
            dpg.add_checkbox(label="MS-SSIM", default_value=args["MS-SSIM"])
            dpg.add_checkbox(label="PSNR-HVS", default_value=args["PSNR-HVS"])
            dpg.add_slider_int(
                label="Subsamples",
                default_value=args["Subsamples"],
                min_value=1,
                max_value=60,
            )

            models = args["Models"]
            with dpg.group(label="Models"):
                for model in models:
                    dpg.add_checkbox(label=model, default_value=True)

            log_formats = ["xml", "json", "csv"]
            with dpg.group(label="Log Format"):
                dpg.add_combo(
                    label="##log_format_combo",
                    items=log_formats,
                    default_value=args["Log Format"],
                )

            with dpg.group(label="Encoder"):
                dpg.add_checkbox(
                    label="libx264 / AVC",
                    default_value=True,
                    tag="libx264",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                dpg.add_checkbox(
                    label="libx265 / HEVC",
                    default_value=True,
                    tag="libx265",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                if args["Operating System"] != "MacOS":
                    dpg.add_checkbox(
                        label="NVENC H.264",
                        default_value=False,
                        tag="nvenc_h264",
                        callback=encoder_callback,
                        user_data=__encoder_tests,
                    )
                    dpg.add_checkbox(
                        label="NVENC HEVC",
                        default_value=False,
                        tag="nvenc_hevc",
                        callback=encoder_callback,
                        user_data=__encoder_tests,
                    )
                dpg.add_checkbox(
                    label="AMF H.264",
                    default_value=False,
                    tag="amf_h264",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                dpg.add_checkbox(
                    label="AME HEVC",
                    default_value=False,
                    tag="amf_hevc",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                dpg.add_checkbox(
                    label="QuickSync H.264",
                    default_value=False,
                    tag="qsv_h264",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                dpg.add_checkbox(
                    label="QuickSync HEVC",
                    default_value=False,
                    tag="qsv_hevc",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                if args["Operating System"] == "MacOS":
                    dpg.add_checkbox(
                        label="VideoToolbox H.264",
                        default_value=False,
                        tag="vt_h264",
                        callback=encoder_callback,
                        user_data=__encoder_tests,
                    )
                    dpg.add_checkbox(
                        label="VideoToolbox HEVC",
                        default_value=False,
                        tag="vt_hevc",
                        callback=encoder_callback,
                        user_data=__encoder_tests,
                    )
                dpg.add_checkbox(
                    label="AOM AV1",
                    default_value=True,
                    tag="aom_av1",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )
                dpg.add_checkbox(
                    label="SVT AV1",
                    default_value=True,
                    tag="svt_av1",
                    callback=encoder_callback,
                    user_data=__encoder_tests,
                )

            dpg.add_button(label="Run", callback=do_thing, user_data=args)
            dpg.add_button(label="Clear", callback=clear_output)
            dpg.add_input_text(
                label="Output", tag="Output_Box", multiline=True, readonly=False
            )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    run_app()
