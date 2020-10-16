#!/usr/bin/env python3

import argparse as argp
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
import os
import sys
import time


def anim_progress(cur_frame, total_frames):
    percent = "{0:.2f}".format(cur_frame * 100 / total_frames).zfill(5)
    sys.stdout.write("\rSaving frame " + str(cur_frame) + " out of " + str(total_frames) + " : " + percent + "%")
    sys.stdout.flush()


def plot_vmaf(vmafs, fps, low, res, custom):
    # Create datapoints
    x = [x for x in range(len(vmafs))]
    mean = round(sum(vmafs) / len(vmafs), 3)
    perc_001 = round(np.percentile(vmafs, 0.01), 3)
    perc_01 = round(np.percentile(vmafs, 0.1), 3)
    perc_1 = round(np.percentile(vmafs, 1), 3)
    perc_25 = round(np.percentile(vmafs, 25), 3)
    perc_75 = round(np.percentile(vmafs, 75), 3)

    # Plot
    if res == "720p":
        plt.figure(figsize=(12.8, 7.2), dpi=800)
        plt.rcParams.update({"font.size": 14})
    elif res == "1080p":
        plt.figure(figsize=(19.2, 10.8), dpi=800)
        plt.rcParams.update({"font.size": 20})
    elif res == "1440p":
        plt.figure(figsize=(25.6, 14.4), dpi=800)
        plt.rcParams.update({"font.size": 26})
    elif res == "4k":
        plt.figure(figsize=(38.4, 21.6), dpi=800)
        plt.rcParams.update({"font.size": 32})
    [plt.axhline(i, color="grey", linewidth=0.4) for i in range(0, 100)]
    [plt.axhline(i, color="black", linewidth=0.6) for i in range(0, 100, 5)]
    plt.plot(x, vmafs, label=f"Frames: {len(vmafs)} \nMean:{mean}\n" f"0.01%: {perc_001} \n0.1%: {perc_01} \n1%: {perc_1} \n25%: {perc_25} \n75%: {perc_75}", linewidth=0.7)
    plt.ylabel("VMAF")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True)
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
    image_name = args.output.replace(".\\", "").split(".")
    image_file = "{0}_{1}_{2}.{3}" .format("".join(image_name[0:-1]), res, low, image_name[-1])
    print("Saving graph to image...")
    plt.savefig(image_file, dpi=500)
    print("Done!")

    fig, ax = plt.subplots()
    fig.patch.set_alpha(0.)
    fig.set_size_inches(19.2, 10.8)
    fig.dpi = 800

    ax.set_ylim(lower_limit, 100)
    ax.set_xlim(x[0] - x[60], x[60])
    ax.set_xticklabels([])
    line, = ax.plot(x, vmafs)

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

    anim_name = args.output.replace(".\\", "").split(".")
    anim_file = "{0}_{1}_{2}.{3}" .format("".join(anim_name[0:-1]), res, low, "mov")

    print("Saving animated graph to video...")
    start = time.time()
    anim.save(str(os.getcwd()) + "/" + anim_file, extra_args=["-c:v", "prores_ks", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-profile:v", "4444"], fps=60, dpi=100, savefig_kwargs={"transparent": True, "facecolor": "none"}, progress_callback=anim_progress)
    anim_progress(length, length)
    end = time.time()
    time_taken = end - start
    print("")
    print("Done! Video took took {0}H : {1}M : {2:0.2f}S to export.".format(int(time_taken / 3600), int(time_taken / 60), time_taken))


def read_vmaf_xml(file):
    with open(file, "r") as f:
        file = f.readlines()
        fps = [x.strip() for x in file if "execFps=\"" in x][0].split(" ")
        file = [x.strip() for x in file if "vmaf=\"" in x]
        vmafs = []
        for i in file:
            vmf = i[i.rfind("=\"") + 2: i.rfind("\"")]
            vmafs.append(float(vmf))
        fps2 = None
        for i in fps:
            if "execFps=\"" in i:
                fps2 = i[i.rfind("=\"") + 2: i.rfind("\"")]

        vmafs = [round(float(x), 3) for x in vmafs if type(x) == float]

    return(vmafs, float(fps2))


def main(args):
    vmafs, fps = read_vmaf_xml(args.VMAF_FILE)
    plot_vmaf(vmafs, fps, args.low, args.res, args.custom)


def parse_arguments():
    main_help = "Plot VMAF to graph, save it as both a static image and as a transparent animated video file.\n"
    parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter)
    parser.add_argument("VMAF_FILE", type=str, help="VMAF report file.")

    o_help = "Output filename (default: vmaf.png).\nAlso defines the name of the output graph (default: vmaf.mov)."
    parser.add_argument("-o", "--output", dest="output", type=str, default="vmaf.png", help=o_help)

    l_help = "Choose what the lowest value of the graph will be.\n"
    l_help += "* \"default\" uses the lowest VMAF value minus 5  as the lowest point of the y-axis so the values aren't so stretched vertically.\n"
    l_help += "* \"min\" will use whatever the lowest VMAF value is as the lowest point of the y-axis. Makes the data look a bit stretched vertically.\n"
    l_help += "* \"zero\" will explicitly use 0 as the lowest point on the y-axis. Makes the data look a bit compressed vertically.\n"
    l_help += "* \"custom\" will use the value entered by the user in the \"-c\" / \"--custom\" option."
    parser.add_argument("-l", "--lower-boundary", dest="low", type=str, default="default", choices=["default", "min", "zero", "custom"], help=l_help)

    c_help = "Enter custom minimum point for y-axis. Requires \"-l\" / \"--lower-boundary\" set to \"custom\" to work.\nThis option expects an integer value."
    parser.add_argument("-c", "--custom", dest="custom", type=int, help=c_help)

    r_help = "Choose the resolution for the graph image and video. Note that higher values will mean drastically larger files."
    parser.add_argument("-r", "--resolution", dest="res", type=str, default="1080p", choices=["720p", "1080p", "1440p", "4k"], help=r_help)

    args = parser.parse_args()

    if args.low == "custom":
        try:
            if args.custom < 0 or args.custom > 100:
                parser.error("Value {0} for \"custom\" argument was not in the valid range of 0 to 100.".format(float(args.custom)))
                exit()
        except ValueError as ve:
            print(ve)
            exit()

    return(args)


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
