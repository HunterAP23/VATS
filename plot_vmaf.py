#!/usr/bin/env python3

import argparse as argp
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
import os
import sys


def anim_progress(cur_frame, total_frames):
    percent = '{0:.2f}'.format(cur_frame * 100 / total_frames).zfill(5)
    sys.stdout.write("\rSaving frame " + str(cur_frame) + " out of " + str(total_frames) + " : " + percent + "%")
    sys.stdout.flush()


def plot_vmaf(vmafs, fps):
    # Create datapoints
    length = len(vmafs)
    x = [x for x in range(len(vmafs))]
    mean = round(sum(vmafs) / len(vmafs), 3)
    perc_001 = round(np.percentile(vmafs, 0.01), 3)
    perc_01 = round(np.percentile(vmafs, 0.1), 3)
    perc_1 = round(np.percentile(vmafs, 1), 3)
    perc_25 = round(np.percentile(vmafs, 25), 3)
    perc_75 = round(np.percentile(vmafs, 75), 3)

    # Plot
    plt.figure(figsize=(38.4, 21.6), dpi=800)
    [plt.axhline(i, color="grey", linewidth=0.4) for i in range(0, 100)]
    [plt.axhline(i, color="black", linewidth=0.6) for i in range(0, 100, 5)]
    plt.plot(x, vmafs, label=f"Frames: {len(vmafs)} \nMean:{mean}\n" f"0.01%: {perc_001} \n0.1%: {perc_01} \n1%: {perc_1} \n25%: {perc_25} \n75%: {perc_75}", linewidth=0.7)
    plt.ylabel("VMAF")
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True)
    plt.ylim(int(perc_001), 100)
    plt.tight_layout()
    plt.margins(0)

    # Save plot to image file
    print("Saving graph to image...")
    plt.savefig(args.output, dpi=500)
    print("Done!")

    plt.rcParams.update({'font.size': 32})
    fig, ax = plt.subplots()
    fig.patch.set_alpha(0.)
    fig.set_size_inches(38.4, 21.6)
    fig.dpi = 800

    ax.set_ylim(int(perc_001), 100)
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

    anim = animation.FuncAnimation(
        # fig, animate_fps, init_func=init_fps, frames=length, interval=100 / 6, blit=True, save_count=50)
        fig, animate, init_func=init, frames=length, interval=float(1000 / fps), blit=True, save_count=50)

    anim_file = args.output.split(".")[1].replace("\\", "") + ".mov"

    print("Saving animated graph to video...")
    anim.save(str(os.getcwd()) + "/" + anim_file, extra_args=['-c:v', 'prores_ks', '-pix_fmt', 'yuva444p10le', '-alpha_bits', '16', '-profile:v', '4444'], fps=60, dpi=100, savefig_kwargs={'transparent': True, 'facecolor': 'none'}, progress_callback=anim_progress)
    anim_progress(length, length)
    print("Done!")


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


def main():
    vmafs, fps = read_vmaf_xml(args.VMAF_FILE)
    plot_vmaf(vmafs, fps)


def parse_arguments():
    parser = argp.ArgumentParser(description="Plot VMAF to graph")
    parser.add_argument("VMAF_FILE", type=str, help="VMAF log file")
    parser.add_argument("-o", "--output", dest="output", type=str, default="vmaf.png", help="Graph output filename (default vmaf.png). Also defines the name of the output graph (default vmaf.mov)")

    return(parser.parse_args())


if __name__ == "__main__":
    args = parse_arguments()
    main()
