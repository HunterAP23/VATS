#!/usr/bin/env python3

import argparse as argp
import concurrent.futures as cf
import itertools
import time
import warnings
from collections import OrderedDict
from multiprocessing import Manager, cpu_count
from pathlib import Path
from traceback import print_exc

import matplotlib as mpl

mpl.use("agg", force=True)
import numpy as np
import pandas as pd
from gooey import Gooey, GooeyParser
from matplotlib import pyplot as plt
from tqdm import tqdm

from vmaf_common import VMAF_Timer, search_handler

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_report_handler import VMAF_Report_Handler


@Gooey(program_name="VMAF Plotter", default_size=(1280, 720), use_cmd_args=True)
def parse_arguments():
    main_help = "Plot VMAF to graph, save it as both a static image and as a transparent animated video file.\n"
    main_help += "All of the following arguments have default values within the config file.\n"
    main_help += "Arguments will override the values for the variables set in the config file when specified.\n"
    main_help += (
        "Settings that are not specified in the config file will use default values as deemed by the program.\n\n"
    )
    # parser = argp.ArgumentParser(
    #     description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False, prog="VMAF Plotter"
    # )
    parser = GooeyParser(description=main_help)

    vmaf_help = (
        "Directories containing subdirectories, which should contain the VMAF report files and distorted video files.\n"
    )
    vmaf_help += (
        'The program will scan for inside the provided directories for subdirectories ending with "_results".\n'
    )
    vmaf_help += 'The subdirectories are expected to contain reports in CSV, JSON, and XML format that end with "_statistics" and be alongside the distorted video files.\n\n'
    # parser.add_argument("VMAF", type=str, nargs="*", help=vmaf_help)
    parser.add_argument("VMAF report files directory", help=vmaf_help, widget="MultiFileChooser")

    optional_args = parser.add_argument_group("Optional arguments")
    config_help = "Config file (default: config.ini).\n"
    # optional_args.add_argument("-c", "--config", dest="config", type=str, help=config_help)
    optional_args.add_argument("Config file", help=config_help)

    output_help = "Output files location, also defines the name of the output graph.\n"
    output_help += "Not specifying an output directory will write the output data to the same directory as the inputs, for each input given.\n"
    output_help += "Specifying a directory will save the output data of all inputs to that location.\n\n"
    optional_args.add_argument("-o", "--output", dest="output", type=str, help=output_help)

    out_types_help = "Choose whether to output a graph image, graph video, stats, or all three (Default: all).\n"
    out_types_help += "The options are separated by a space if you want to specify only one or two of the choices.\n"
    out_types_help += '- "image" will output the image graph.\n'
    out_types_help += '- "video" will output the video graph.\n'
    out_types_help += '- "stats" will print out the statistics to the console and to a file.\n'
    out_types_help += '- "agg" will collect the stats and write the aggregated statistics.\n'
    out_types_help += '- "all" will output all the other options.\n\n'
    optional_args.add_argument(
        "-t",
        "--output_types",
        "--output-types",
        dest="output_types",
        nargs="*",
        type=str,
        default="all",
        choices=["image", "video", "stats", "agg", "all"],
        help=out_types_help,
    )

    data_help = "Choose which data points to show on the graphs and statistics outputs (Default: all).\n"
    data_help += "The options are separated by a space if you want to specify only one or more.\n"
    data_help += '- "vmaf" will only graph the VMAF scores.\n'
    data_help += '- "psnr" will only graph the PSNR scores.\n'
    data_help += '- "ssim" will only graph the SSIM scores.\n'
    data_help += '- "ms_ssim" will only graph the MS-SSIM scores.\n'
    data_help += '- "all" will graph the all of the above scores.\n\n'
    optional_args.add_argument(
        "-dp",
        "--datapoints",
        dest="datapoints",
        nargs="*",
        type=str,
        default="all",
        choices=["vmaf", "psnr", "ssim", "ms_ssim", "all"],
        help=data_help,
    )

    res_help = "Choose the resolution for the graph video (Default is 1080).\n"
    res_help += "Note that higher values will mean drastically larger files and take substantially longer to encode.\n"
    res_help += 'This option is ignored when using option "-t" / "--output_types" with "none" value.\n\n'
    optional_args.add_argument(
        "-r",
        "--resolution",
        dest="res",
        type=str,
        default="1080",
        choices=["720", "1080", "1440", "4k"],
        help=res_help,
    )

    fps_help = "Specify the FPS for the video file (Default is 60).\n"
    optional_args.add_argument("-f", "--fps", dest="fps", default=60.0, type=float, help=fps_help)

    misc_args = parser.add_argument_group("Miscellaneous arguments")
    # misc_args.add_argument(
    #     "-h",
    #     "--help",
    #     action="help",
    #     default=argp.SUPPRESS,
    #     help="Show this help message and exit.\n",
    # )
    misc_args.add_argument("-v", "--version", action="version", version="2021-10-10")

    args = parser.parse_args()
    if args.VMAF is None or len(args.VMAF) == 0:
        parser.exit(status=1, message="No VMAF files or directories were provided.")

    print("Collecting list of files...")
    original_location = None
    if len(args.VMAF) == 1:
        original_location = args.VMAF[0]
    vmaf_files = []
    for VMAF in args.VMAF:
        vmaf_files += search_handler(VMAF, recurse=True, search_for="report")

    args.VMAF = vmaf_files

    if args.fps <= 0.0:
        parser.exit(status=1, message="Can't use FPS value less than or equal to 0.")

    output_files = {}
    if not args.output:
        for v in args.VMAF:
            output_files[v] = str(Path(v).parent)
    else:
        out_path = Path(args.output)
        if out_path.exists():
            if out_path.is_dir():
                for v in args.VMAF:
                    output_files[v] = str(out_path)
            else:
                raise OSError('Output location "{}" is not a directory.'.format(out_path))
        elif not Path(args.output).exists():
            if out_path.parent.exists():
                out_path.mkdir(exist_ok=True)
                for v in args.VMAF:
                    output_files[v] = str(out_path)
            else:
                raise OSError('Output path parent "{}" does not exist.'.format(out_path.parent))

    args.output = output_files

    if type(args.output_types) == str:
        args.output_types = [
            args.output_types,
        ]

    if "all" in args.output_types:
        args.output_types = ["image", "video", "stats", "agg"]

    if type(args.datapoints) == str:
        args.datapoints = [
            args.datapoints,
        ]

    if "all" in args.datapoints:
        args.datapoints = ["VMAF", "PSNR", "SSIM", "MS-SSIM"]
    else:
        dp = []
        for point in args.datapoints:
            if point == "ms_ssim":
                dp.append("MS-SSIM")
            else:
                dp.append(point.upper())
        args.datapoints = dp

    return args, original_location


def check_report(report, config, datapoints):
    # print("Reading file {}...".format(Path(report).name))
    return (report, VMAF_Report_Handler(report, config, datapoints=datapoints).read_file())


def get_name_model(name: str):
    name_new, model = name.split("_vmaf")
    model = "vmaf" + model.strip(".csv").strip(".json").strip(".xml")
    return name_new, model


def quantile_abs_dev(array, quantile):
    quantile = array.quantile(quantile)
    x = pd.DataFrame(array - quantile).abs()
    return round(float(x.mean()), 3)


def create_datapoint(data):
    point = {}
    point["list"] = data
    point["dataset"] = pd.Series(data)

    point["Mean"] = point["dataset"].mean()
    point["Median"] = point["dataset"].median()
    point["Standard Deviation"] = point["dataset"].std()
    point["Mean Absolute Deviation"] = point["dataset"].mad()
    point["Median Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.5)
    point["99th Percentile"] = point["dataset"].quantile(0.99)
    point["95th Percentile"] = point["dataset"].quantile(0.95)
    point["90th Percentile"] = point["dataset"].quantile(0.90)
    point["75th Percentile"] = point["dataset"].quantile(0.75)
    point["25th Percentile"] = point["dataset"].quantile(0.25)
    point["1st Percentile"] = point["dataset"].quantile(0.01)
    point["0.1st Percentile"] = point["dataset"].quantile(0.001)
    point["0.01st Percentile"] = point["dataset"].quantile(0.0001)
    # point["Minimum"] = min(data)
    point["99th Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.99)
    point["95th Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.95)
    point["90th Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.9)
    point["75th Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.75)
    point["25th Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.25)
    point["1st Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.01)
    point["0.1st Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.001)
    point["0.01st Percentile Absolute Deviation"] = point["dataset"].agg(quantile_abs_dev, quantile=0.0001)

    # ewm = point["dataset"].ewm(com=0.5)

    # ewm_mean = ewm.mean()
    # point["EWM Average Mean"] = ewm_mean.mean()
    # point["EWM Average Median"] = ewm_mean.median()
    # point["EWM Average Standard Deviation"] = ewm_mean.std()
    # point["EWM Average Mean Absolute Deviation"] = ewm_mean.mad()
    # point["EWM Average Median Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.5)
    # point["EWM Average 99th Percentile"] = ewm_mean.quantile(0.99)
    # point["EWM Average 95th Percentile"] = ewm_mean.quantile(0.95)
    # point["EWM Average 90th Percentile"] = ewm_mean.quantile(0.90)
    # point["EWM Average 75th Percentile"] = ewm_mean.quantile(0.75)
    # point["EWM Average 25th Percentile"] = ewm_mean.quantile(0.25)
    # point["EWM Average 1st Percentile"] = ewm_mean.quantile(0.01)
    # point["EWM Average 0.1st Percentile"] = ewm_mean.quantile(0.001)
    # point["EWM Average 0.01st Percentile"] = ewm_mean.quantile(0.0001)
    # point["EWM Average 99th Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.99)
    # point["EWM Average 95th Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.95)
    # point["EWM Average 90th Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.9)
    # point["EWM Average 75th Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.75)
    # point["EWM Average 25th Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.25)
    # point["EWM Average 1st Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.01)
    # point["EWM Average 0.1st Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.001)
    # point["EWM Average 0.01st Percentile Absolute Deviation"] = ewm_mean.agg(quantile_abs_dev, quantile=0.0001)

    # ewm_std = ewm.std()
    # point["EWM Standard Deviation Mean"] = ewm_std.mean()
    # point["EWM Standard Deviation Median"] = ewm_std.median()
    # point["EWM Standard Deviation Standard Deviation"] = ewm_std.std()
    # point["EWM Standard Deviation Mean Absolute Deviation"] = ewm_std.mad()
    # point["EWM Standard Deviation Median Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.5)
    # point["EWM Standard Deviation 99th Percentile"] = ewm_std.quantile(0.99)
    # point["EWM Standard Deviation 95th Percentile"] = ewm_std.quantile(0.95)
    # point["EWM Standard Deviation 90th Percentile"] = ewm_std.quantile(0.90)
    # point["EWM Standard Deviation 75th Percentile"] = ewm_std.quantile(0.75)
    # point["EWM Standard Deviation 25th Percentile"] = ewm_std.quantile(0.25)
    # point["EWM Standard Deviation 1st Percentile"] = ewm_std.quantile(0.01)
    # point["EWM Standard Deviation 0.1st Percentile"] = ewm_std.quantile(0.001)
    # point["EWM Standard Deviation 0.01st Percentile"] = ewm_std.quantile(0.0001)
    # point["EWM Standard Deviation 99th Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.99)
    # point["EWM Standard Deviation 95th Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.95)
    # point["EWM Standard Deviation 90th Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.9)
    # point["EWM Standard Deviation 75th Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.75)
    # point["EWM Standard Deviation 25th Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.25)
    # point["EWM Standard Deviation 1st Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.01)
    # point["EWM Standard Deviation 0.1st Percentile Absolute Deviation"] = ewm_std.agg(quantile_abs_dev, quantile=0.001)
    # point["EWM Standard Deviation 0.01st Percentile Absolute Deviation"] = ewm_std.agg(
    #     quantile_abs_dev, quantile=0.0001
    # )

    return point


def get_stats(data, output, datapoints, report):
    main = {}

    for point in datapoints:
        main[point] = create_datapoint(data[point])
        if point in ["SSIM", "MS-SSIM"]:
            main[point]["Maximum"] = 1
        else:
            main[point]["Maximum"] = 100
    main["index"] = [x for x in range(len(data["VMAF"]))]

    main["File Path"] = Path(output)
    main["File Name"] = Path(report).stem
    name, model = get_name_model(main["File Name"])
    # main["File Size"] = bytes2human(main["File Path"].joinpath(name + ".mp4").stat().st_size)
    main["File Size"] = main["File Path"].joinpath(name + ".mp4").stat().st_size

    return main


def write_stats(main, datapoints, metrics):
    # def write_stats(main, datapoints, metrics):
    stats_file = str(main["File Path"].joinpath("{0}_statistics.txt".format(main["File Name"])))

    # print("Saving statistics to {0}...".format(stats_file))
    with open(str(stats_file), "w") as stat:
        stat.write("Number of frames: {}\n".format(len(main["index"])))
        for point in datapoints:
            for metric in metrics.keys():
                stat.write("{} {} Score: {}\n".format(metric, point.upper(), main[point][metric]))
    # print("Done!")


def create_plot(main, index, metrics, font_size):
    fig, ax = plt.subplots()

    # [
    #     ax.axhline(
    #         int(i),
    #         color="grey",
    #         linewidth=0.4,
    #         antialiased=True,
    #         rasterized=True,
    #     )
    #     for i in np.linspace(start=0, stop=main["Maximum"], num=100)
    # ]
    [
        ax.axhline(
            int(i),
            color="black",
            linewidth=0.6,
            antialiased=True,
            rasterized=True,
        )
        for i in np.linspace(start=0, stop=main["Maximum"], num=20)
    ]

    fig.dpi = 100
    plt.yticks(fontsize=font_size)
    plt.xticks(fontsize=font_size)

    label = "Frames: {0}".format(len(index))
    for metric in metrics.keys():
        if metric.lower() in ["mean", "median"]:
            label += " | {0}: {1}".format(metric, main[metric])

    plt.legend(
        labels=[
            label,
        ],
        loc="best",
        bbox_to_anchor=(0.5, -0.1),
        fancybox=True,
        shadow=False,
    )
    plt.locator_params(axis="y", tight=True, nbins=5)

    plt.ylim(0, main["Maximum"])
    # fig.tight_layout()
    plt.margins(0)

    return fig, ax, label


def create_image(main, point, res, fig, ax, font_size, label):
    # Save plot to image file
    image_file = str(main["File Path"].joinpath("{0}_{1}_{2}.png".format(main["File Name"], point, res)))

    ax.plot(
        main[point]["list"],
        linewidth=0.7,
        antialiased=True,
        figure=fig,
        rasterized=True,
    )

    ax.set_ylabel(point.upper(), fontsize=font_size)
    ax.set_xlabel(label, fontsize=font_size)

    # print("Saving graph to {0}...".format(image_file))
    fig.savefig(image_file, dpi=100, transparent=True)
    # print("Done!")


def create_video(main, point, res, fps, fig, ax):
    ax.set_ylim(0, main[point]["Maximum"])
    ax.set_xlim(
        main["index"][0] - main["index"][60],
        main["index"][60],
    )
    ax.set_xticklabels([])
    fig.patch.set_alpha(0.0)

    def init():
        line.set_data([], [])
        return (line,)

    def animate(i):
        line.set_data(main["index"][:i], main[point]["list"][:i])
        ax.set_xlim(
            main["index"][i] - main["index"][60],
            main["index"][i] + main["index"][60],
        )
        return (line,)

    length = len(main["index"])

    (line,) = ax.plot(main["index"], main[point]["dataset"])
    anim = mpl.animation.FuncAnimation(
        fig,
        animate,
        init_func=init,
        frames=length,
        interval=float(1000 / fps),
        blit=True,
        save_count=50,
    )

    # anim_file = str(main["File Path"].joinpath("{0}_{1}_{2}.mov".format(main["File Name"], point, res)))
    anim_file = str(main["File Path"].joinpath("{0}_{1}_{2}.webm".format(main["File Name"], point, res)))

    # print("Saving animated graph to video file {}...".format(anim_file))
    # start = time()
    anim.save(
        anim_file,
        # extra_args=["-c:v", "prores_ks", "-threads", "0"],
        extra_args=[
            "-pix_fmt",
            "yuva420p",
            "-c:v",
            "libvpx-vp9",
            "-threads",
            "0",
            "-crf",
            "0",
            "-b:v",
            "0",
            "-lossless",
            "1",
            "-row-mt",
            "1",
            "-tile-columns",
            "6",
            "-tile-rows",
            "2",
            "-frame-parallel",
            "1",
        ],
        fps=fps,
        dpi="figure",
        savefig_kwargs={"transparent": True},
        # progress_callback=calc_progress,
    )
    # calc_progress(length, length)
    # print("")
    # end = time()
    # time_taken = end - start
    # minutes = int(time_taken / 60)
    # hours = int(minutes / 60)
    # seconds = time_taken % 60
    # print("Done! Video took took {0}H : {1}M : {2:0.2f}S to export.".format(hours, minutes, seconds))


def handle_plotting(data, args, metrics, font_size, pos, sema):
    plots = {}
    images = []
    videos = []
    with cf.ProcessPoolExecutor() as pool_plot, cf.ProcessPoolExecutor() as pool_image, cf.ProcessPoolExecutor(
        max_workers=1
    ) as pool_video:
        for point in args.datapoints:
            plots[pool_plot.submit(create_plot, data[point], data["index"], metrics, font_size)] = point

        for task in cf.as_completed(plots):
            fig, ax, label = task.result()
            point = plots[task]
            sema.acquire()

            if "image" in args.output_types:
                images.append(pool_image.submit(create_image, data, point, args.res, fig, ax, font_size, label))

            if "video" in args.output_types:
                videos.append(pool_video.submit(create_video, data, point, args.res, args.fps, fig, ax))

        if "image" in args.output_types:
            cf.wait(images, return_when=cf.ALL_COMPLETED)

        if "video" in args.output_types:
            cf.wait(videos, return_when=cf.ALL_COMPLETED)

        sema.release()
        plt.close(fig)


def main(args, original_location):
    timer = VMAF_Timer()
    # 0 means that higher values rank better, and 1 means lower values rank better
    metrics = {
        "Mean": 0,
        "Median": 0,
        "Standard Deviation": 1,
        "Mean Absolute Deviation": 1,
        "Median Absolute Deviation": 1,
        "99th Percentile": 0,
        "95th Percentile": 0,
        "90th Percentile": 0,
        "75th Percentile": 0,
        "25th Percentile": 0,
        "1st Percentile": 0,
        "0.1st Percentile": 0,
        "0.01st Percentile": 0,
        "99th Percentile Absolute Deviation": 1,
        "95th Percentile Absolute Deviation": 1,
        "90th Percentile Absolute Deviation": 1,
        "75th Percentile Absolute Deviation": 1,
        "25th Percentile Absolute Deviation": 0,
        "1st Percentile Absolute Deviation": 0,
        "0.1st Percentile Absolute Deviation": 0,
        "0.01st Percentile Absolute Deviation": 0,
        # "EWM Average Mean": 0,
        # "EWM Average Median": 0,
        # "EWM Average Standard Deviation": 1,
        # "EWM Average Mean Absolute Deviation": 1,
        # "EWM Average Median Absolute Deviation": 1,
        # "EWM Average 99th Percentile": 0,
        # "EWM Average 95th Percentile": 0,
        # "EWM Average 90th Percentile": 0,
        # "EWM Average 75th Percentile": 0,
        # "EWM Average 25th Percentile": 0,
        # "EWM Average 1st Percentile": 0,
        # "EWM Average 0.1st Percentile": 0,
        # "EWM Average 0.01st Percentile": 0,
        # "EWM Average 99th Percentile Absolute Deviation": 1,
        # "EWM Average 95th Percentile Absolute Deviation": 1,
        # "EWM Average 90th Percentile Absolute Deviation": 1,
        # "EWM Average 75th Percentile Absolute Deviation": 1,
        # "EWM Average 25th Percentile Absolute Deviation": 0,
        # "EWM Average 1st Percentile Absolute Deviation": 0,
        # "EWM Average 0.1st Percentile Absolute Deviation": 0,
        # "EWM Average 0.01st Percentile Absolute Deviation": 0,
        # "EWM Standard Deviation Mean": 0,
        # "EWM Standard Deviation Median": 0,
        # "EWM Standard Deviation Standard Deviation": 1,
        # "EWM Standard Deviation Mean Absolute Deviation": 1,
        # "EWM Standard Deviation Median Absolute Deviation": 1,
        # "EWM Standard Deviation 99th Percentile": 0,
        # "EWM Standard Deviation 95th Percentile": 0,
        # "EWM Standard Deviation 90th Percentile": 0,
        # "EWM Standard Deviation 75th Percentile": 0,
        # "EWM Standard Deviation 25th Percentile": 0,
        # "EWM Standard Deviation 1st Percentile": 0,
        # "EWM Standard Deviation 0.1st Percentile": 0,
        # "EWM Standard Deviation 0.01st Percentile": 0,
        # "EWM Standard Deviation 99th Percentile Absolute Deviation": 1,
        # "EWM Standard Deviation 95th Percentile Absolute Deviation": 1,
        # "EWM Standard Deviation 90th Percentile Absolute Deviation": 1,
        # "EWM Standard Deviation 75th Percentile Absolute Deviation": 1,
        # "EWM Standard Deviation 25th Percentile Absolute Deviation": 0,
        # "EWM Standard Deviation 1st Percentile Absolute Deviation": 0,
        # "EWM Standard Deviation 0.1st Percentile Absolute Deviation": 0,
        # "EWM Standard Deviation 0.01st Percentile Absolute Deviation": 0,
    }
    manager = Manager()
    sema = None
    cpus = None
    if "video" in args.output_types:
        # cpus = int(cpu_count() / 4)
        # sema = manager.Semaphore(cpus)
        cpus = 1
        sema = manager.Semaphore(1)
    else:
        cpus = cpu_count()
        sema = manager.Semaphore(cpus)

    data = {}
    models = list(set(list([get_name_model(vmaf)[1] for vmaf in args.VMAF])))
    # configs = [args.config for i in range(len(args.VMAF))]
    print("Reading files for VMAF data...")

    had_exception = False
    exception_item = None

    pool_main = cf.ProcessPoolExecutor()
    try:
        with tqdm(desc="Getting VMAF reports", total=len(args.VMAF), unit="reports", position=0, leave=True) as pbar:
            ret = []
            for vmaf in args.VMAF:
                ret.append(pool_main.submit(check_report, vmaf, args.config, datapoints=args.datapoints))

            for task in cf.as_completed(ret):
                pbar.update()
                item = task.result()
                data[item[0]] = item[1]
    except KeyboardInterrupt as ke:
        print("KeyboardInterrupt detected, working on shutting down pool...")
        exception_item = ke
        had_exception = True
        pool_main.shutdown(cancel_futures=True)
    except Exception:
        had_exception = True
        pool_main.shutdown(cancel_futures=True)
    pool_main.shutdown()
    del pool_main

    if had_exception:
        if exception_item:
            print(exception_item)
        else:
            print_exc()
        exit(1)

    font_size = 16
    if any(item in ["image", "video"] for item in args.output_types):
        plt.rcParams.update(
            {
                "figure.facecolor": (0.0, 0.0, 0.0, 0.0),
                "figure.edgecolor": "black",
                "axes.facecolor": (0.0, 0.0, 0.0, 0.0),
                "savefig.facecolor": (0.0, 0.0, 0.0, 0.0),
                "legend.facecolor": (0.0, 0.0, 0.0, 0.0),
                "legend.edgecolor": "black",
                "legend.frameon": False,
                "savefig.transparent": True,
                # "animation.codec": "qtrle",
                "animation.codec": "libvpx-vp9",
                # "agg.path.chunksize": 1000000,
                "path.simplify_threshold": 1,
            }
        )

        if args.res == "720":
            plt.rcParams.update({"font.size": 22})
            plt.rcParams.update(
                {
                    "figure.figsize": (
                        12.8,
                        7.2,
                    )
                }
            )
        elif args.res == "1080":
            plt.rcParams.update({"font.size": 24})
            plt.rcParams.update(
                {
                    "figure.figsize": (
                        19.2,
                        10.8,
                    )
                }
            )
            font_size = 19
        elif args.res == "1440":
            plt.rcParams.update({"font.size": 26})
            plt.rcParams.update(
                {
                    "figure.figsize": (
                        25.6,
                        14.4,
                    )
                }
            )
            font_size = 22
        elif args.res == "4k":
            plt.rcParams.update({"font.size": 28})
            plt.rcParams.update(
                {
                    "figure.figsize": (
                        38.4,
                        21.6,
                    )
                }
            )
            font_size = 25

    ret_get_stats = {}
    ret_write_stats = {}
    ret_plots = {}
    ret_images = []
    ret_videos = []
    main = {}
    figs = {}
    for key in data.keys():
        figs[key] = {}
        figs[key]["figure"] = None
        if "image" in args.output_types:
            figs[key]["image"] = "Not Started"
        if "video" in args.output_types:
            figs[key]["video"] = "Not Started"

    ret_len = len(data.keys())
    mbar = tqdm(desc="Creating metrics", total=ret_len, unit="metrics", position=0, leave=True)

    pos = 1
    sbar = (
        tqdm(desc="Writing statistics", total=ret_len, unit="files", position=pos, leave=True)
        if "stats" in args.output_types
        else None
    )
    if sbar is not None:
        pos += 1

    pbar = (
        tqdm(desc="Creating graphs", total=ret_len, unit="plots", position=pos, leave=True)
        if any(item in args.output_types for item in ["image", "video"])
        else None
    )

    with cf.ProcessPoolExecutor() as pool_main, cf.ProcessPoolExecutor() as pool_writer, cf.ProcessPoolExecutor() as pool_graph:
        try:
            for key, value in data.items():
                ret_get_stats[
                    pool_main.submit(
                        get_stats, data=value, output=args.output[key], datapoints=args.datapoints, report=key
                    )
                ] = key

            for task in cf.as_completed(ret_get_stats):
                mbar.update()
                main[ret_get_stats[task]] = task.result()

                if "stats" in args.output_types:
                    ret_write_stats[
                        pool_writer.submit(write_stats, main[ret_get_stats[task]], args.datapoints, metrics)
                    ] = key

                if any(item in args.output_types for item in ["image", "video"]):
                    ret_plots[
                        pool_graph.submit(
                            handle_plotting, main[ret_get_stats[task]], args, metrics, font_size, pos, sema
                        )
                    ] = key
            for task in cf.as_completed(ret_write_stats):
                sbar.update()
            for task in cf.as_completed(ret_plots):
                pbar.update()

        except KeyboardInterrupt as ke:
            print("KeyboardInterrupt detected, working on shutting down pool...")
            exception_item = ke
            had_exception = True
            pool_main.shutdown(cancel_futures=True)
        except Exception as e:
            exception_item = e
            had_exception = True
            pool_main.shutdown(cancel_futures=True)
        finally:
            pool_main.shutdown()
            pool_video.shutdown()

        if mbar is not None:
            mbar.close()

        if sbar is not None:
            sbar.close()

        if pbar is not None:
            pbar.close()

    del pool_main

    if had_exception:
        if exception_item is not None:
            print(exception_item)
        print_exc()
        exit(1)

    plt.close()

    if "agg" in args.output_types:
        print("Calculating aggregate statistics.")

        print("Aggregating initial data for all reports...")

        # Create dict for tracking scores of individual dists using a specific model
        dict_scores = {}
        dict_scores_dist = {}
        for model in models:
            dict_scores[model] = {}

        for rep in sorted(main.keys()):
            name, model = get_name_model(Path(rep).name)
            dict_scores[model][name] = {}
            if name not in dict_scores_dist.keys():
                dict_scores_dist[name] = {}
            for point in args.datapoints:
                for metric, value in main[rep][point].items():
                    if metric.lower() in ["dataset", "maximum"]:
                        continue
                    dict_scores[model][name]["{} {}".format(point, metric)] = value
                    dict_scores_dist[name]["{} {} {}".format(model, point, metric)] = value
            dict_scores_dist[name]["File Size"] = main[rep]["File Size"]

        dist_tmp = OrderedDict()
        for k in sorted(dict_scores_dist.keys()):
            dist_tmp[k] = {}
            for key in sorted(dict_scores_dist[k].keys()):
                dist_tmp[k][key] = dict_scores_dist[k][key]

        dict_scores_dist = dict(dist_tmp)
        del dist_tmp

        df_scores = {}
        df_rankings = {}

        for model in sorted(dict_scores.keys()):
            df_scores[model] = pd.DataFrame(dict_scores[model], dtype="float64").transpose()
            df_rankings[model] = pd.DataFrame(dtype="float64")

        df_scores_dist = pd.DataFrame(dict_scores_dist, dtype="float64")
        dict_scores_dist_rankings = {}

        print("Aggregating rankings for each metric...")
        # Rankings for distorted files on a per-model basis
        for model in sorted(df_scores.keys()):
            for point in args.datapoints:
                for metric, metric_rank in metrics.items():
                    item = "{} {}".format(point, metric)
                    item_rank = "{} RANK".format(item)
                    if metric_rank == 1 or metric == "File Size":
                        df_rankings[model][item_rank] = df_scores[model][item].rank()
                    else:
                        df_rankings[model][item_rank] = df_scores[model][item].rank(ascending=False)

            df_rankings[model]["OVERALL SCORE"] = df_rankings[model].sum(axis=1)
            df_scores[model] = df_scores[model].transpose()

        # Rankings for distorted files among all models
        for name in sorted(df_scores_dist.keys()):
            if name not in dict_scores_dist_rankings:
                dict_scores_dist_rankings[name] = pd.Series(dtype="float64")
            for model in df_scores.keys():
                for point in args.datapoints:
                    dict_scores_dist_rankings[name]["File Size"] = df_scores_dist.transpose()["File Size"].rank()[name]
                    for metric, metric_rank in metrics.items():
                        model_item = "{} {} {}".format(model, point, metric)
                        model_item_rank = "{} RANK".format(model_item)
                        if metric_rank == 1:
                            dict_scores_dist_rankings[name][model_item_rank] = df_scores_dist.transpose()[
                                model_item
                            ].rank()[name]
                        else:
                            dict_scores_dist_rankings[name][model_item_rank] = df_scores_dist.transpose()[
                                model_item
                            ].rank(ascending=False)[name]
        df_scores_dist = df_scores_dist.transpose()
        dist_rank_temp = OrderedDict()
        for k in sorted(dict_scores_dist_rankings.keys()):
            dist_rank_temp[k] = dict_scores_dist_rankings[k].sort_values()
        dict_scores_dist_rankings = dict(dist_rank_temp)
        del dist_rank_temp
        df_scores_dist_rankings = pd.DataFrame(dict_scores_dist_rankings, dtype="float64")
        df_scores_dist_rankings = df_scores_dist_rankings.transpose()
        df_scores_dist_rankings["OVERALL SCORE"] = df_scores_dist_rankings.sum(axis=1)

        for name in sorted(df_scores_dist.keys()):
            df_scores_dist[name] = df_scores_dist[name].transpose()

        print("Adding rows for top scores to main table...")
        for model in sorted(df_scores.keys()):
            top_score = {}
            top_score_file = {}
            for point in args.datapoints:
                for metric, metric_rank in metrics.items():
                    item = "{} {}".format(point, metric)
                    if metric_rank == 1 or metric == "File Size":
                        top_score[item] = df_scores[model].transpose().min()[item]
                        top_score_file[item] = df_scores[model].transpose().idxmin()[item]
                    else:
                        top_score[item] = df_scores[model].transpose().max()[item]
                        top_score_file[item] = df_scores[model].transpose().idxmax()[item]

            df_scores[model]["Top Score"] = pd.Series(top_score, dtype="float64")
            df_scores[model]["Top Score File"] = pd.Series(top_score_file)
            del top_score
            del top_score_file

            df_scores[model] = df_scores[model].transpose()

        agg_size = sum([frame.memory_usage(deep=True).sum() for frame in df_scores.values()]) + sum(
            [frame.memory_usage(deep=True).sum() for frame in df_rankings.values()]
        )
        print("Aggregate data is {} bytes".format(agg_size))

        df_file = None
        if original_location:
            df_file = str(Path(original_location).joinpath("aggregate_stats.xlsx"))
        else:
            df_file = str(Path(__file__).parent.joinpath("aggregate_stats.xlsx"))
        print("Saving aggregate statistics to file {}...".format(df_file))
        Path(df_file).unlink(missing_ok=True)
        with pd.ExcelWriter(df_file, mode="w") as writer:
            for model in df_scores.keys():
                df_scores[model].to_excel(writer, sheet_name="{} Scores".format(model))
                df_rankings[model].to_excel(writer, sheet_name="{} Rankings".format(model))
            df_scores_dist.to_excel(writer, sheet_name="Dist Scores")
            df_scores_dist_rankings.to_excel(writer, sheet_name="Dist Rankings")

    print("Program has finished!")
    timer.end()
    time.sleep(3)
    print(timer.get_runtime_formatted())


if __name__ == "__main__":
    warnings.filterwarnings("ignore", module="matplotlib\\..*")
    args, original_location = parse_arguments()
    main(args, original_location)
