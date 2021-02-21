#!/usr/bin/env python3

import argparse as argp
import os
import statistics
import sys
import time

from matplotlib import pyplot as plt
from matplotlib import animation
import numpy as np

from config_handler import Config_Handler
from report_handler import Report_Handler


def anim_progress(cur_frame, total_frames):
    percent = "{0:.2f}".format(cur_frame * 100 / total_frames).zfill(5)
    sys.stdout.write("\rSaving frame " + str(cur_frame) + " out of " + str(total_frames) + " : " + percent + "%")
    sys.stdout.flush()


def plot_vmaf(vmafs, fps, low, res, custom, dpi):
    # Create datapoints
    x = [x for x in range(len(vmafs))]
    mean = round(statistics.fmean(vmafs), 3)
    median = round(statistics.median(vmafs), 3)
    perc_001 = round(np.percentile(vmafs, 0.01), 3)
    perc_01 = round(np.percentile(vmafs, 0.1), 3)
    perc_1 = round(np.percentile(vmafs, 1), 3)

    # Plot
    if res == "720":
        plt.figure(figsize=(12.8, 7.2), dpi=800)
    elif res == "1080":
        plt.figure(figsize=(19.2, 10.8), dpi=800)
    elif res == "1440":
        plt.figure(figsize=(25.6, 14.4), dpi=800)
    elif res == "4k":
        plt.figure(figsize=(38.4, 21.6), dpi=800)

    plt.rcParams.update({
        "figure.facecolor": (0.0, 0.0, 0.0, 0.0),
        "figure.edgecolor": "black",
        "axes.facecolor": (0.0, 0.0, 0.0, 0.0),
        "savefig.facecolor": (0.0, 0.0, 0.0, 0.0),
        "legend.facecolor": (0.0, 0.0, 0.0, 0.0),
        "legend.edgecolor": "black",
        "legend.frameon": False,
        "savefig.transparent": True,
        "animation.codec": "qtrle",
        "font.size": 26,
    })

    [plt.axhline(i, color="grey", linewidth=0.4) for i in range(0, 100)]
    [plt.axhline(i, color="black", linewidth=0.6) for i in range(0, 100, 5)]
    plt.plot(x, vmafs, label=f"Frames: {len(vmafs)} \nMean:{mean}\nMedian:{median}\n" f"0.01%: {perc_001} \n0.1%: {perc_01} \n1%: {perc_1}", linewidth=0.7)
    plt.ylabel("VMAF")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=False)
    plt.locator_params(axis="y", tight=True, nbins=5)

    lower_limit = 0
    if low == "default":
        if int(perc_001) > 5:
            lower_limit = int(perc_001 - 5)
    elif low == "min":
        lower_limit = int(perc_001)
    elif low == "zero":
        lower_limit = 0
    elif low == "custom":
        lower_limit = int(args.custom)

    plt.ylim(lower_limit, 100)
    plt.tight_layout()
    plt.margins(0)

    # Save plot to image file
    image_paths = os.path.split(args.output)
    image_name = "".join(image_paths)
    image_file = "{0}_{1}_{2}_dpi{3}.png".format("".join(image_name), res, low, int(dpi))

    print("Saving graph to {0}...".format(image_file))
    plt.savefig(image_file, dpi=800)
    print("Done!")

    fig, ax = plt.subplots()
    fig.patch.set_alpha(0.0)
    if res == "720":
        fig.set_size_inches(12.8, 7.2)
    elif res == "1080":
        fig.set_size_inches(19.2, 10.8)
    elif res == "1440":
        fig.set_size_inches(25.6, 14.4)
    elif res == "4k":
        fig.set_size_inches(38.4, 21.6)
    fig.dpi = dpi

    ax.set_ylim(lower_limit, 100)
    ax.set_xlim(x[0] - x[60], x[60])
    ax.set_xticklabels([])
    line, = ax.plot(x, vmafs)
    fig.patch.set_alpha(0.0)

    def init():
        line.set_data([], [])
        return line,

    def animate(i):
        line.set_data(x[:i], vmafs[:i])
        ax.set_xlim(x[i] - x[60], x[i] + x[60])
        return line,

    length = len(vmafs)

    anim = animation.FuncAnimation(
        fig, animate, init_func=init, frames=length, interval=float(1000 / fps), blit=True, save_count=50)

    anim_file = "{0}_{1}_{2}_dpi{3}.mov".format("".join(image_name), res, low, int(dpi))

    print("Saving animated graph to video...")
    start = time.time()
    anim.save(anim_file, extra_args=["-c:v", "qtrle"], fps=fps, dpi="figure", savefig_kwargs={"transparent": True}, progress_callback=anim_progress)
    anim_progress(length, length)
    end = time.time()
    time_taken = end - start
    minutes = int(time_taken / 60)
    hours = int(minutes / 60)
    seconds = time_taken % 60
    print("")
    print("Done! Video took took {0}H : {1}M : {2:0.2f}S to export.".format(hours, minutes, seconds))


def main(args):
    vmafs = read_vmaf_xml(args.VMAF_FILE)
    plot_vmaf(vmafs, args.fps, args.low, args.res, args.custom, args.dpi)


def parse_arguments():
    main_help = "Plot VMAF to graph, save it as both a static image and as a transparent animated video file.\n"
    main_help += "All of the following arguments have default values within the config file.\n"
    main_help += "Arguments will override the values for the variables set in the config file when sepcified.\n"
    main_help += "Settings that are not specified in the config file will use default values as deemed by the program."
    parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False)
    parser.add_argument("VMAF_FILE", type=str, help="VMAF report file.")

    optional_args = parser.add_argument_group("Optional arguments")
    o_help = "Output filename (Default: vmaf.png).\nAlso defines the name of the output graph (Default: vmaf.mov).\n"
    o_help += "Specifying a path will save the output image and video to that location.\n"
    o_help += "If no path is given, then the files are saved to this project folder."
    optional_args.add_argument("-o", "--output", dest="output", type=str, default="vmaf.png", help=o_help)

    l_help = "Choose what the lowest value of the graph will be.\n"
    l_help += "- \"default\" uses the lowest VMAF value minus 5 as the lowest point of the y-axis so the values aren't so stretched vertically.\n"
    l_help += "- \"min\" will use whatever the lowest VMAF value is as the lowest point of the y-axis. May make the data look a bit stretched vertically.\n"
    l_help += "- \"zero\" will explicitly use 0 as the lowest point on the y-axis. May make the data look a bit compressed vertically.\n"
    l_help += "- \"custom\" will use the value entered by the user in the \"-c\" / \"--custom\" option."
    optional_args.add_argument("-l", "--lower-boundary", dest="low", type=str, default="default", choices=["default", "min", "zero", "custom"], help=l_help)

    custom_help = "Enter custom minimum point for y-axis. Requires \"-l\" / \"--lower-boundary\" set to \"custom\" to work.\nThis option expects an integer value."
    optional_args.add_argument("-c", "--custom", dest="custom", type=int, help=custom_help)

    res_help = "Choose the resolution for the graph video (Default is 1080).\n"
    res_help += "Note that higher values will mean drastically larger files and take substantially longer to encode."
    optional_args.add_argument("-r", "--resolution", dest="res", type=str, default="1080", choices=["720", "1080", "1440", "4k"], help=res_help)

    dpi_help = "Choose the DPI for the graph image and video (Default is 100).\n"
    dpi_help += "Note that higher values will mean drastically larger files and take substantially longer to encode.\n"
    dpi_help += "This setting applies only to the video file, not the image file."
    optional_args.add_argument("-d", "--dpi", dest="dpi", type=float, default="100", help=dpi_help)

    vmaf_version_help = "Choose which VMAF version was used when generating the report file (Default is autodetect).\n"
    vmaf_version_help += "Note that the VMAF version can not be autodetected when using CSV files, so if you're using a CSV VMAF v1 report please specify this option as \"1\".\n"
    vmaf_version_help += "Also note that when using version 2, an FPS value should be specified for the video, the default FPS is 60.\n"
    optional_args.add_argument("-v", "--version", dest="version", type=int, default="2", choices=["1", "2"], help=vmaf_version_help)

    fps_help = "Specify the FPS for the video file (Default is 60).\n"
    fps_help += "Note that for VMAF version 2 (which is the default) this value should be specified manually, otherwise the default value of 60fps will be used."
    optional_args.add_argument("-f", "--fps", dest="fps", type=float, help=fps_help)

    misc_args = parser.add_argument_group("Miscellaneous arguments")
    misc_args.add_argument("-h", "--help", action="help", default=argp.SUPPRESS, help="Show this help message and exit.\n")

    args = parser.parse_args()

    if args.fps <= 0:
        parser.exit(status=1, message="Can't use FPS value less than or equal to 0.")
    # elif not args.fps:
    #     if int(args.version) == 2:
    #         parser.error("WANRING: User did not specify an FPS value when using VMAF version 2. The default FPS value of 60 will be used when generating the video file.")

    if args.low == "custom":
        try:
            if args.custom < 0 or args.custom > 100:
                parser.exit(status=1, message="Value {0} for \"custom\" argument was not in the valid range of 0 to 100.".format(float(args.custom)))
        except ValueError as ve:
            parser.exit(status=1, message=ve)

    if not args.output:
        report_name = os.path.split(args.VMAF_FILE)
        args.output = ".".join("".join(report_name).split(".")[:-1])

    return(args)


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
