#!/usr/bin/env python3

import argparse as argp
import concurrent.futures as cf
import time
from collections import OrderedDict
from pathlib import Path
from traceback import print_exc

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from tqdm import tqdm

from vmaf_common import bytes2human, print_dict, search_handler

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_report_handler import VMAF_Report_Handler

# def calc_progress(current, total, phrase="Saving frame"):
#     percent = "{0:.2f}".format(current * 100 / total).zfill(5)
#     sys.stdout.write("\r{0} {1} out of {2} : {3}%".format(phrase, current, total, percent))
#     sys.stdout.flush()


def quantile_abs_dev(array, quantile):
    quantile = array.quantile(quantile)
    x = pd.DataFrame(array - quantile).abs()
    return x.mean()


def create_datapoint(data):
    point = {}
    point["dataset"] = pd.Series(data)

    point["Mean"] = round(point["dataset"].mean(), 3)
    point["Median"] = round(point["dataset"].median(), 3)
    point["Standard Deviation"] = round(point["dataset"].std(), 3)
    point["Mean Absolute Deviation"] = round(point["dataset"].mad(), 3)
    point["Median Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.5), 3)
    point["99th Percentile"] = round(point["dataset"].quantile(0.99), 3)
    point["95th Percentile"] = round(point["dataset"].quantile(0.95), 3)
    point["90th Percentile"] = round(point["dataset"].quantile(0.90), 3)
    point["75th Percentile"] = round(point["dataset"].quantile(0.75), 3)
    point["25th Percentile"] = round(point["dataset"].quantile(0.25), 3)
    point["1st Percentile"] = round(point["dataset"].quantile(0.01), 3)
    point["0.1st Percentile"] = round(point["dataset"].quantile(0.001), 3)
    point["0.01st Percentile"] = round(point["dataset"].quantile(0.0001), 3)
    # point["Minimum"] = round(min(data), 3)
    point["99th Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.99), 3)
    point["95th Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.95), 3)
    point["90th Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.9), 3)
    point["75th Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.75), 3)
    point["25th Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.25), 3)
    point["1st Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.01), 3)
    point["0.1st Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.001), 3)
    point["0.01st Percentile Absolute Deviation"] = round(point["dataset"].agg(quantile_abs_dev, quantile=0.0001), 3)

    ewm = point["dataset"].ewm(com=0.5)

    ewm_mean = ewm.mean()
    point["EWM Average Mean"] = round(ewm_mean.mean(), 3)
    point["EWM Average Median"] = round(ewm_mean.median(), 3)
    point["EWM Average Standard Deviation"] = round(ewm_mean.std(), 3)
    point["EWM Average Mean Absolute Deviation"] = round(ewm_mean.mad(), 3)
    point["EWM Average Median Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.5), 3)
    point["EWM Average 99th Percentile"] = round(ewm_mean.quantile(0.99), 3)
    point["EWM Average 95th Percentile"] = round(ewm_mean.quantile(0.95), 3)
    point["EWM Average 90th Percentile"] = round(ewm_mean.quantile(0.90), 3)
    point["EWM Average 75th Percentile"] = round(ewm_mean.quantile(0.75), 3)
    point["EWM Average 25th Percentile"] = round(ewm_mean.quantile(0.25), 3)
    point["EWM Average 1st Percentile"] = round(ewm_mean.quantile(0.01), 3)
    point["EWM Average 0.1st Percentile"] = round(ewm_mean.quantile(0.001), 3)
    point["EWM Average 0.01st Percentile"] = round(ewm_mean.quantile(0.0001), 3)
    point["EWM Average 99th Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.99), 3)
    point["EWM Average 95th Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.95), 3)
    point["EWM Average 90th Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.9), 3)
    point["EWM Average 75th Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.75), 3)
    point["EWM Average 25th Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.25), 3)
    point["EWM Average 1st Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.01), 3)
    point["EWM Average 0.1st Percentile Absolute Deviation"] = round(ewm_mean.agg(quantile_abs_dev, quantile=0.001), 3)
    point["EWM Average 0.01st Percentile Absolute Deviation"] = round(
        ewm_mean.agg(quantile_abs_dev, quantile=0.0001), 3
    )

    ewm_std = ewm.std()
    point["EWM Standard Deviation Mean"] = round(ewm_std.mean(), 3)
    point["EWM Standard Deviation Median"] = round(ewm_std.median(), 3)
    point["EWM Standard Deviation Standard Deviation"] = round(ewm_std.std(), 3)
    point["EWM Standard Deviation Mean Absolute Deviation"] = round(ewm_std.mad(), 3)
    point["EWM Standard Deviation Median Absolute Deviation"] = round(ewm_std.agg(quantile_abs_dev, quantile=0.5), 3)
    point["EWM Standard Deviation 99th Percentile"] = round(ewm_std.quantile(0.99), 3)
    point["EWM Standard Deviation 95th Percentile"] = round(ewm_std.quantile(0.95), 3)
    point["EWM Standard Deviation 90th Percentile"] = round(ewm_std.quantile(0.90), 3)
    point["EWM Standard Deviation 75th Percentile"] = round(ewm_std.quantile(0.75), 3)
    point["EWM Standard Deviation 25th Percentile"] = round(ewm_std.quantile(0.25), 3)
    point["EWM Standard Deviation 1st Percentile"] = round(ewm_std.quantile(0.01), 3)
    point["EWM Standard Deviation 0.1st Percentile"] = round(ewm_std.quantile(0.001), 3)
    point["EWM Standard Deviation 0.01st Percentile"] = round(ewm_std.quantile(0.0001), 3)
    point["EWM Standard Deviation 99th Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.99), 3
    )
    point["EWM Standard Deviation 95th Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.95), 3
    )
    point["EWM Standard Deviation 90th Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.9), 3
    )
    point["EWM Standard Deviation 75th Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.75), 3
    )
    point["EWM Standard Deviation 25th Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.25), 3
    )
    point["EWM Standard Deviation 1st Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.01), 3
    )
    point["EWM Standard Deviation 0.1st Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.001), 3
    )
    point["EWM Standard Deviation 0.01st Percentile Absolute Deviation"] = round(
        ewm_std.agg(quantile_abs_dev, quantile=0.0001), 3
    )

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
    stats_file = str(main["File Path"].joinpath("{0}_statistics.txt".format(main["File Name"])))

    # print("Saving statistics to {0}...".format(stats_file))
    with open(str(stats_file), "w") as stat:
        stat.write("Number of frames: {}\n".format(len(main["index"])))
        for point in datapoints:
            for metric in metrics:
                stat.write("{} {} Score: {}\n".format(metric, point.upper(), main[point][metric]))
    # print("Done!")


def create_plot(main, datapoints, metrics, font_size):
    for point in datapoints:
        fig, ax = plt.subplots()

        [
            ax.axhline(
                int(i),
                color="grey",
                linewidth=0.4,
                antialiased=True,
                rasterized=True,
            )
            for i in np.linspace(start=0, stop=main[point]["Maximum"], num=100)
        ]
        [
            ax.axhline(
                int(i),
                color="black",
                linewidth=0.6,
                antialiased=True,
                rasterized=True,
            )
            for i in np.linspace(start=0, stop=main[point]["Maximum"], num=20)
        ]

        fig.dpi = 100
        plt.yticks(fontsize=font_size)
        plt.xticks(fontsize=font_size)

        label = "Frames: {0} | ".format(len(main["index"]))
        for metric in metrics:
            label += "{0}: {1} | ".format(metric, main[point][metric])

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

        plt.ylim(0, main[point]["Maximum"])
        plt.tight_layout()
        plt.margins(0)

        return fig, ax, label


def create_image(main, datapoints, res, fig, font_size, label):
    for point in datapoints:
        # Save plot to image file
        image_file = str(main["File Path"].joinpath("{0}_{1}_{2}.png".format(main["File Name"], point, res)))

        plt.plot(
            main[point]["dataset"],
            linewidth=0.7,
            antialiased=True,
            figure=fig,
            rasterized=True,
        )

        plt.ylabel(point.upper(), fontsize=font_size)
        plt.xlabel(label, fontsize=font_size)

        # print("Saving graph to {0}...".format(image_file))
        plt.savefig(image_file, dpi=100, transparent=True)
        # print("Done!")


def create_video(main, datapoints, res, fps, fig, ax):
    for point in datapoints:
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
            line.set_data(main["index"][:i], main[point]["dataset"][:i])
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

        anim_file = str(main["File Path"].joinpath("{0}_{1}_{2}.mov".format(main["File Name"], point, res)))

        # print("Saving animated graph to video file {}...".format(anim_file))
        # start = time()
        anim.save(
            anim_file,
            extra_args=["-c:v", "prores_ks"],
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


def get_name_model(name: str):
    name_new, model = name.split("_vmaf")
    model = "vmaf" + model.strip(".csv").strip(".json").strip(".xml")
    return name_new, model


def parse_arguments():
    main_help = "Plot VMAF to graph, save it as both a static image and as a transparent animated video file.\n"
    main_help += "All of the following arguments have default values within the config file.\n"
    main_help += "Arguments will override the values for the variables set in the config file when specified.\n"
    main_help += (
        "Settings that are not specified in the config file will use default values as deemed by the program.\n\n"
    )
    parser = argp.ArgumentParser(
        description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False, prog="VMAF Plotter"
    )

    vmaf_help = (
        "Directories containing subdirectories, which should contain the VMAF report files and distorted video files.\n"
    )
    vmaf_help += (
        'The program will scan for inside the provided directories for subdirectories ending with "_results".\n'
    )
    vmaf_help += 'The subdirectories are expected to contain reports in CSV, JSON, and XML format that end with "_statistics" and be alongside the distorted video files.\n\n'
    parser.add_argument("VMAF", type=str, nargs="*", help=vmaf_help)

    optional_args = parser.add_argument_group("Optional arguments")
    config_help = "Config file (default: config.ini).\n"
    optional_args.add_argument("-c", "--config", dest="config", type=str, help=config_help)

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
    misc_args.add_argument(
        "-h",
        "--help",
        action="help",
        default=argp.SUPPRESS,
        help="Show this help message and exit.\n",
    )
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


def main(args, original_location):
    metrics = [
        "Mean",
        "Median",
        "Standard Deviation",
        "Mean Absolute Deviation",
        "Median Absolute Deviation",
        "99th Percentile",
        "95th Percentile",
        "90th Percentile",
        "75th Percentile",
        "25th Percentile",
        "1st Percentile",
        "0.1st Percentile",
        "0.01st Percentile",
        "99th Percentile Absolute Deviation",
        "95th Percentile Absolute Deviation",
        "90th Percentile Absolute Deviation",
        "75th Percentile Absolute Deviation",
        "25th Percentile Absolute Deviation",
        "1st Percentile Absolute Deviation",
        "0.1st Percentile Absolute Deviation",
        "0.01st Percentile Absolute Deviation",
        "EWM Average Mean",
        "EWM Average Median",
        "EWM Average Standard Deviation",
        "EWM Average Mean Absolute Deviation",
        "EWM Average Median Absolute Deviation",
        "EWM Average 99th Percentile",
        "EWM Average 95th Percentile",
        "EWM Average 90th Percentile",
        "EWM Average 75th Percentile",
        "EWM Average 25th Percentile",
        "EWM Average 1st Percentile",
        "EWM Average 0.1st Percentile",
        "EWM Average 0.01st Percentile",
        "EWM Average 99th Percentile Absolute Deviation",
        "EWM Average 95th Percentile Absolute Deviation",
        "EWM Average 90th Percentile Absolute Deviation",
        "EWM Average 75th Percentile Absolute Deviation",
        "EWM Average 25th Percentile Absolute Deviation",
        "EWM Average 1st Percentile Absolute Deviation",
        "EWM Average 0.1st Percentile Absolute Deviation",
        "EWM Average 0.01st Percentile Absolute Deviation",
        "EWM Standard Deviation Mean",
        "EWM Standard Deviation Median",
        "EWM Standard Deviation Standard Deviation",
        "EWM Standard Deviation Mean Absolute Deviation",
        "EWM Standard Deviation Median Absolute Deviation",
        "EWM Standard Deviation 99th Percentile",
        "EWM Standard Deviation 95th Percentile",
        "EWM Standard Deviation 90th Percentile",
        "EWM Standard Deviation 75th Percentile",
        "EWM Standard Deviation 25th Percentile",
        "EWM Standard Deviation 1st Percentile",
        "EWM Standard Deviation 0.1st Percentile",
        "EWM Standard Deviation 0.01st Percentile",
        "EWM Standard Deviation 99th Percentile Absolute Deviation",
        "EWM Standard Deviation 95th Percentile Absolute Deviation",
        "EWM Standard Deviation 90th Percentile Absolute Deviation",
        "EWM Standard Deviation 75th Percentile Absolute Deviation",
        "EWM Standard Deviation 25th Percentile Absolute Deviation",
        "EWM Standard Deviation 1st Percentile Absolute Deviation",
        "EWM Standard Deviation 0.1st Percentile Absolute Deviation",
        "EWM Standard Deviation 0.01st Percentile Absolute Deviation",
    ]

    data = {}
    models = list(set(list([get_name_model(vmaf)[1] for vmaf in args.VMAF])))
    # configs = [args.config for i in range(len(args.VMAF))]
    print("Reading files for VMAF data...")

    had_exception = False

    pool_procs = cf.ProcessPoolExecutor()
    try:
        # ret = pool_threads.map(check_report, args.VMAF, configs)
        with tqdm(desc="Getting VMAF reports", total=len(args.VMAF), unit="reports", position=0, leave=True) as pbar:
            ret = []
            for vmaf in args.VMAF:
                ret.append(pool_procs.submit(check_report, vmaf, args.config, datapoints=args.datapoints))

            for task in cf.as_completed(ret):
                pbar.update()
                item = task.result()
                data[item[0]] = item[1]
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, working on shutting down pool...")
        had_exception = True
        pool_procs.shutdown(cancel_futures=True)
    except Exception:
        print_exc()
        had_exception = True
        pool_procs.shutdown(cancel_futures=True)
    pool_procs.shutdown()
    del pool_procs

    if had_exception:
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
                "animation.codec": "qtrle",
                # "agg.path.chunksize": 1000000,
                "path.simplify_threshold": 1,
            }
        )

        if args.res == "720":
            plt.rcParams.update({"font.size": 22})
        elif args.res == "1080":
            plt.rcParams.update({"font.size": 24})
            font_size = 19
        elif args.res == "1440":
            plt.rcParams.update({"font.size": 26})
            font_size = 22
        elif args.res == "4k":
            plt.rcParams.update({"font.size": 28})
            font_size = 25

    ret = {}
    main = {}
    pool_procs = cf.ProcessPoolExecutor(max_workers=1)
    try:
        for key, value in data.items():
            ret[
                pool_procs.submit(
                    get_stats, data=value, output=args.output[key], datapoints=args.datapoints, report=key
                )
            ] = {
                "task type": "get_stats",
                "key": key,
            }

        ret_len = len(ret)
        mbar = tqdm(desc="Creating metrics", total=ret_len, unit="metrics", position=0, leave=True)

        sbar = None
        if "stats" in args.output_types:
            sbar = tqdm(desc="Writing individual stats", total=ret_len, unit="stats", position=1, leave=True)

        pbar = None
        if any(item in args.output_types for item in ["image", "video"]):
            pbar = tqdm(desc="Creating data plots", total=ret_len, unit="plots", position=2, leave=True)

        ibar = None
        if "image" in args.output_types:
            ibar = tqdm(desc="Saving images", total=ret_len, unit="images", position=3, leave=True)

        vbar = None
        if "video" in args.output_types:
            vbar = tqdm(desc="Saving videos", total=ret_len, unit="videos", position=4, leave=True)

        for task in cf.as_completed(ret):
            if ret[task]["task type"] == "get_stats":
                mbar.update()
                main[ret[task]["key"]] = task.result()
                if "stats" in args.output_types:
                    ret[pool_procs.submit(write_stats, main[key], args.datapoints, metrics)] = {
                        "task type": "write_stats",
                        "key": ret[task]["key"],
                    }
                else:
                    ret[pool_procs.submit(time.sleep, 0.01)] = {"task type": "write_stats", "key": ret[task]["key"]}
            elif ret[task]["task type"] == "write_stats":
                sbar.update()
                if any(item in args.output_types for item in ["image", "video"]):
                    ret[pool_procs.submit(create_plot, main[key], args.datapoints, metrics, font_size)] = {
                        "task type": "plot",
                        "key": ret[task]["key"],
                    }
            elif ret[task]["task type"] == "plot":
                pbar.update()
                fig, ax, label = task.result()
                if "image" in args.output_types:
                    ret[pool_procs.submit(create_image, main[key], args.datapoints, fig, font_size, label)] = {
                        "task type": "image",
                        "key": ret[task]["key"],
                    }
                if "video" in args.output_types:
                    ret[pool_procs.submit(create_video, main[key], args.datapoints, args.res, args.fps, fig, ax)] = {
                        "task type": "video",
                        "key": ret[task]["key"],
                    }
            elif ret[task]["task type"] == "image":
                ibar.update()
            elif ret[task]["task type"] == "video":
                vbar.update()
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected, working on shutting down pool...")
        had_exception = True
        pool_procs.shutdown(cancel_futures=True)
    except Exception:
        print_exc()
        had_exception = True
    else:
        cf.wait(ret)
        pool_procs.shutdown()
        if mbar:
            mbar.close()

        if sbar:
            sbar.close()

        if pbar:
            pbar.close()

        if ibar:
            ibar.close()

        if vbar:
            vbar.close()

    del pool_procs

    if had_exception:
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

        # for model in df_scores.keys():
        #     for item in df_scores[model].keys():a
        #         df_scores[model][item] = pd.Series(df_scores[model][item], dtype="float64")

        df_scores_dist = pd.DataFrame(dict_scores_dist, dtype="float64")
        dict_scores_dist_rankings = {}

        print("Aggregating rankings for each metric...")
        # Rankings for distorted files on a per-model basis
        for model in sorted(df_scores.keys()):
            for point in args.datapoints:
                for metric in metrics:
                    item = "{} {}".format(point, metric)
                    item_rank = "{} RANK".format(item)
                    if metric in [
                        "Standard Deviation",
                        "Mean Absolute Deviation",
                        "Median Absolute Deviation",
                        "99th Percentile Absolute Deviation",
                        "95th Percentile Absolute Deviation",
                        "90th Percentile Absolute Deviation",
                        "75th Percentile Absolute Deviation",
                        "EWM Average Standard Deviation",
                        "EWM Average Mean Absolute Deviation",
                        "EWM Average Median Absolute Deviation",
                        "EWM Average 99th Percentile Absolute Deviation",
                        "EWM Average 95th Percentile Absolute Deviation",
                        "EWM Average 90th Percentile Absolute Deviation",
                        "EWM Average 75th Percentile Absolute Deviation",
                        "EWM Standard Deviation Standard Deviation",
                        "EWM Standard Deviation Mean Absolute Deviation",
                        "EWM Standard Deviation Median Absolute Deviation",
                        "EWM Standard Deviation 99th Percentile Absolute Deviation",
                        "EWM Standard Deviation 95th Percentile Absolute Deviation",
                        "EWM Standard Deviation 90th Percentile Absolute Deviation",
                        "EWM Standard Deviation 75th Percentile Absolute Deviation",
                        "File Size",
                    ]:
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
                    for metric in metrics:
                        model_item = "{} {} {}".format(model, point, metric)
                        model_item_rank = "{} RANK".format(model_item)
                        if metric in [
                            "Standard Deviation",
                            "Mean Absolute Deviation",
                            "Median Absolute Deviation",
                            "99th Percentile Absolute Deviation",
                            "95th Percentile Absolute Deviation",
                            "90th Percentile Absolute Deviation",
                            "75th Percentile Absolute Deviation",
                            "EWM Average Standard Deviation",
                            "EWM Average Mean Absolute Deviation",
                            "EWM Average Median Absolute Deviation",
                            "EWM Average 99th Percentile Absolute Deviation",
                            "EWM Average 95th Percentile Absolute Deviation",
                            "EWM Average 90th Percentile Absolute Deviation",
                            "EWM Average 75th Percentile Absolute Deviation",
                            "EWM Standard Deviation Standard Deviation",
                            "EWM Standard Deviation Mean Absolute Deviation",
                            "EWM Standard Deviation Median Absolute Deviation",
                            "EWM Standard Deviation 99th Percentile Absolute Deviation",
                            "EWM Standard Deviation 95th Percentile Absolute Deviation",
                            "EWM Standard Deviation 90th Percentile Absolute Deviation",
                            "EWM Standard Deviation 75th Percentile Absolute Deviation",
                        ]:
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
                for metric in metrics:
                    item = "{} {}".format(point, metric)
                    # print("model: {}".format(model))
                    # print("item: {}".format(item))
                    # print("df_scores[{}]:\n{}".format(model, df_scores[model]))
                    # print("\ndf_scores[{}].transpose():\n{}".format(model, df_scores[model].transpose()))
                    # print("\ndf_scores[{}].transpose()[{}]:\n{}".format(model, item, df_scores[model].transpose()[item]))
                    # exit()
                    if metric in [
                        "Standard Deviation",
                        "Mean Absolute Deviation",
                        "Median Absolute Deviation",
                        "99th Percentile Absolute Deviation",
                        "95th Percentile Absolute Deviation",
                        "90th Percentile Absolute Deviation",
                        "75th Percentile Absolute Deviation",
                        "EWM Average Standard Deviation",
                        "EWM Average Mean Absolute Deviation",
                        "EWM Average Median Absolute Deviation",
                        "EWM Average 99th Percentile Absolute Deviation",
                        "EWM Average 95th Percentile Absolute Deviation",
                        "EWM Average 90th Percentile Absolute Deviation",
                        "EWM Average 75th Percentile Absolute Deviation",
                        "EWM Standard Deviation Standard Deviation",
                        "EWM Standard Deviation Mean Absolute Deviation",
                        "EWM Standard Deviation Median Absolute Deviation",
                        "EWM Standard Deviation 99th Percentile Absolute Deviation",
                        "EWM Standard Deviation 95th Percentile Absolute Deviation",
                        "EWM Standard Deviation 90th Percentile Absolute Deviation",
                        "EWM Standard Deviation 75th Percentile Absolute Deviation",
                        "File Size",
                    ]:
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


if __name__ == "__main__":
    args, original_location = parse_arguments()
    main(args, original_location)
