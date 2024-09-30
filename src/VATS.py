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
from PySide6.QtWidgets import QApplication

from VATS_MainWindow import MainWindow


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
@click.option(
    "--encoders",
    type=click.Choice(
        [
            "libx264",
            "libx265",
            "libaom-av1",
            "libsvtav1",
            "h264_nvenc",
            "hevc_nvenc",
            "av1_nvenc",
            "h264_amf",
            "hevc_amf",
            "av1_amf",
            "h264_qsv",
            "hevc_qsv",
            "av1_qsv",
            "h264_videotoolbox",
            "hevc_videotoolbox",
        ]
    ),
    default=[],
    multiple=True,
    required=False,
    help="List of FFmpeg encoders to test.",
)
@click.option(
    "--decoders",
    type=click.Choice(
        [
            "h264",
            "hevc",
            "libaom-av1",
            "libdav1d",
            "av1",
            "h264_cuvid",
            "hevc_cuvid",
            "av1_cuvid",
            "h264_qsv",
            "hevc_qsv",
            "av1_qsv",
            "prores",
        ]
    ),
    default=[],
    multiple=True,
    required=False,
    help="List of FFmpeg decoders to test.",
)
@click.option(
    "--hwaccels",
    type=click.Choice(
        [
            "cuda",
            "qsv",
            "dxva2",
            "d3d11va",
            "opencl",
            "vulkan",
            "vaapi",
        ]
    ),
    default=[],
    multiple=True,
    required=False,
    help="List of FFmpeg hwaccels to test. Note that not all hwaccels may be usable on your system (IE: CUDA with AMD GPU's, DXVA2 / D3D11VA on Linux, VAAPI on Windows).",
)
@click.option(
    "--hwaccel_output_format",
    "--hwaccel-output_format",
    type=click.Choice(
        [
            "auto",
            "cuda",
            "dxva2",
            "d3d11va",
            "vaapi",
        ]
    ),
    default=None,
    multiple=False,
    required=False,
    help="List of FFmpeg encoders to test. Note that not all hwaccel output formats may be usable on your system (IE: CUDA with AMD GU's, DXVA2 / D3D11VA on Linux, VAAPI on Windows) or usable with other hwaccels (IE: VAAPI hwaccel with CUDA output format).",
)
@click.option(
    "--pre_test_encoders",
    "--pre-test-encoders",
    is_flag=True,
    default=False,
    required=False,
    help="Preemptively test encoders. Startup time will be moderately impacted.",
)
@click.option(
    "--pre_test_decoders",
    "--pre-test-decoders",
    is_flag=True,
    default=False,
    required=False,
    help="Preemptively test decoders. Startup time will be slightly impacted.",
)
@click.option(
    "--pre_test_hwaccels",
    "--pre-test-hwaccels",
    is_flag=True,
    default=False,
    required=False,
    help="Preemptively test hwaccels. Startup time will be impacted.",
)
@click.option(
    "--pre_test_all",
    "--pre-test-all",
    is_flag=True,
    default=False,
    required=False,
    help="Preemptively test encoders, decoders, and hwaccels. Startup time will be significantly impacted.",
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
    encoders,
    decoders,
    hwaccels,
    hwaccel_output_format,
    pre_test_encoders,
    pre_test_decoders,
    pre_test_hwaccels,
    pre_test_all,
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
        "Encoders": encoders,
        "Decoders": decoders,
        "HWAccels": hwaccels,
        "HWAccel-Output-Format": hwaccel_output_format,
        "Pre-Test Encoders": pre_test_encoders,
        "Pre-Test Decoders": pre_test_decoders,
        "Pre-Test HWAccels": pre_test_hwaccels,
        "Pre-Test All": pre_test_all,
    }
    if args["No GUI"]:
        return
    else:
        app = QApplication([])
        window = MainWindow(args)
        window.resize(1280, 720)
        window.show()
        app.exec()


if __name__ == "__main__":
    run_app()
