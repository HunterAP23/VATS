#!/usr/bin/env python3

import argparse as argp
import concurrent.futures as cf
import sys
import time
import traceback
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from vmaf_common import search_handler

# from vmaf_config_handler import VMAF_Config_Handler
from vmaf_report_handler import VMAF_Report_Handler


def calc_progress(current, total, phrase="Saving frame"):
    percent = "{0:.2f}".format(current * 100 / total).zfill(5)
    sys.stdout.write("\r{0} {1} out of {2} : {3}%".format(phrase, current, total, percent))
    sys.stdout.flush()


def create_datapoint(data):
    point = {}
    point["list"] = data
    point["array"] = np.array(data)
    point["mean"] = round(np.mean(point["array"]), 3)
    point["median"] = round(np.median(point["array"]), 3)
    point["standard_deviation"] = round(np.std(point["array"]), 3)
    point["perc_1"] = round(np.percentile(point["array"], 1), 3)
    point["perc_01"] = round(np.percentile(point["array"], 0.1), 3)
    point["perc_001"] = round(np.percentile(point["array"], 0.01), 3)
    point["minimum"] = round(min(data), 3)

    return point


def plot_vmaf(data, fps, res, output, output_types, datapoints, report):
    main = {}

    # Create statistics for the selected datapoints
    dp = []
    if "all" in datapoints:
        dp = ["vmaf", "psnr", "ssim", "ms_ssim"]
    else:
        dp = [point for point in datapoints]

    for point in dp:
        main[point] = create_datapoint(data[point])
        if point in ["ssim", "ms_ssim"]:
            main[point]["maximum"] = 1
        else:
            main[point]["maximum"] = 100
    main["index"] = [x for x in range(len(data["vmaf"]))]

    main["file_path"] = Path(output)
    main["file_name"] = Path(report).stem

    # Only save statistics file
    if any(item in ["all", "stats"] for item in output_types):
        stats_file = str(main["file_path"].joinpath("{0}_statistics.txt".format(main["file_name"])))

        print("Saving statistics to {0}...".format(stats_file))
        # data["vmaf"]_df.to_csv(stats_file)
        with open(str(stats_file), "w") as stat:
            stat.write("Number of frames: {}\n".format(len(main["index"])))
            for point in dp:
                stat.write("Mean {} Score: {}\n".format(point.upper(), main[point]["mean"]))
                stat.write("Median {} Score: {}\n".format(point.upper(), main[point]["median"]))
                stat.write("standard_deviation {} Score: {}\n".format(point.upper(), main[point]["standard_deviation"]))
                stat.write("1% Lowest {} Score: {}\n".format(point.upper(), main[point]["perc_1"]))
                stat.write("0.1% Lowest {} Score: {}\n".format(point.upper(), main[point]["perc_01"]))
                stat.write("0.01% Lowest {} Score: {}\n\n".format(point.upper(), main[point]["perc_001"]))
        print("Done!")

    if any(item in ["all", "image", "video"] for item in output_types):
        for point in dp:
            [
                plt.axhline(
                    int(i),
                    color="grey",
                    linewidth=0.4,
                    antialiased=True,
                    rasterized=True,
                )
                for i in np.linspace(start=0, stop=main[point]["maximum"], num=100)
            ]
            [
                plt.axhline(
                    int(i),
                    color="black",
                    linewidth=0.6,
                    antialiased=True,
                    rasterized=True,
                )
                for i in np.linspace(start=0, stop=main[point]["maximum"], num=20)
            ]

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

            fig, ax = plt.subplots()

            font_size = 16
            fig.patch.set_alpha(0.0)
            if res == "720":
                fig.set_size_inches(12.8, 7.2)
                plt.rcParams.update({"font.size": 22})
            elif res == "1080":
                fig.set_size_inches(19.2, 10.8)
                plt.rcParams.update({"font.size": 24})
                font_size = 19
            elif res == "1440":
                fig.set_size_inches(25.6, 14.4)
                plt.rcParams.update({"font.size": 26})
                font_size = 22
            elif res == "4k":
                fig.set_size_inches(38.4, 21.6)
                plt.rcParams.update({"font.size": 28})
                font_size = 25
            fig.dpi = 100
            plt.yticks(fontsize=font_size)
            plt.xticks(fontsize=font_size)

            label = "Frames: {0}  |  Mean: {1}  |  standard_deviation: {2}  |  Median: {3}  |  1%: {4}  |  0.1%: {5}  |  0.01%: {6}".format(
                len(main["index"]),
                main[point]["mean"],
                main[point]["median"],
                main[point]["standard_deviation"],
                main[point]["perc_1"],
                main[point]["perc_01"],
                main[point]["perc_001"],
            )

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

            plt.ylim(0, main[point]["maximum"])
            plt.tight_layout()
            plt.margins(0)

            # Save plot to image file
            if any(item in ["all", "image"] for item in output_types):
                image_file = str(main["file_path"].joinpath("{0}_{1}_{2}.png".format(main["file_name"], point, res)))

                plt.plot(
                    main[point]["array"],
                    linewidth=0.7,
                    antialiased=True,
                    figure=fig,
                    rasterized=True,
                )

                plt.ylabel(point.upper(), fontsize=font_size)
                plt.xlabel(label, fontsize=font_size)

                print("Saving graph to {0}...".format(image_file))
                plt.savefig(image_file, dpi=100, transparent=True)
                print("Done!")
                exit()

            if any(item in ["all", "video"] for item in output_types):
                ax.set_ylim(0, main[point]["maximum"])
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

                (line,) = ax.plot(main["index"], main[point]["list"])
                anim = mpl.animation.FuncAnimation(
                    fig,
                    animate,
                    init_func=init,
                    frames=length,
                    interval=float(1000 / fps),
                    blit=True,
                    save_count=50,
                )

                anim_file = str(main["file_path"].joinpath("{0}_{1}_{2}.mov".format(main["file_name"], point, res)))

                print("Saving animated graph to video file {}...".format(anim_file))
                start = time.time()
                anim.save(
                    anim_file,
                    extra_args=["-c:v", "prores_ks"],
                    fps=fps,
                    dpi="figure",
                    savefig_kwargs={"transparent": True},
                    progress_callback=calc_progress,
                )
                calc_progress(length, length)
                print("")
                end = time.time()
                time_taken = end - start
                minutes = int(time_taken / 60)
                hours = int(minutes / 60)
                seconds = time_taken % 60
                print("Done! Video took took {0}H : {1}M : {2:0.2f}S to export.".format(hours, minutes, seconds))
            plt.close()

    if any(item in ["all", "agg"] for item in output_types):
        return main


def parse_arguments():
    main_help = "Plot VMAF to graph, save it as both a static image and as a transparent animated video file.\n"
    main_help += "All of the following arguments have default values within the config file.\n"
    main_help += "Arguments will override the values for the variables set in the config file when specified.\n"
    main_help += "Settings that are not specified in the config file will use default values as deemed by the program.\n\n"
    parser = argp.ArgumentParser(description=main_help, formatter_class=argp.RawTextHelpFormatter, add_help=False)

    vmaf_help = "Directory containing subdirectories, which should contain the VMAF report files and distorted video files.\n"
    vmaf_help += 'The program will scan for inside the provided directories for subdirectories ending with "_results".\n'
    vmaf_help += "The subdirectories are expected to contain reports in CSV, INI, JSON, and XML format alongisde the distorted video files.\n\n"
    parser.add_argument("VMAF", type=str, nargs="*", help=vmaf_help)

    optional_args = parser.add_argument_group("Optional arguments")
    config_help = "Config file (defualt: config.ini).\n"
    optional_args.add_argument("-c", "--config", dest="config", type=str, help=config_help)

    output_help = "Output files location, also defines the name of the output graph.\n"
    output_help += "Not specifying an output directory will write the output data to the same directory as the inputs, for each input given.\n"
    output_help += "Specifying a directory will save the output data of all inputs to that location.\n\n"
    optional_args.add_argument("-o", "--output", dest="output", type=str, help=output_help)

    out_types_help = "Choose whether to output a graph image, graph video, stats, or all three (Default: all).\n"
    out_types_help += "The options are separated by a space if you want to specifiy only one or two of the choices.\n"
    out_types_help += '- "image" will only output the image graph.\n'
    out_types_help += '- "video" will only output the video graph.\n'
    out_types_help += '- "stats" will only print out the statistics to the console and to a file.\n\n'
    out_types_help += '- "all" will output the image and video graphs.'
    optional_args.add_argument(
        "-ot",
        "--output_types",
        dest="output_types",
        nargs="*",
        type=str,
        default="all",
        choices=["image", "video", "stats", "agg", "all"],
        help=out_types_help,
    )

    data_help = "Choose which data points to show on the graphs and statistics outputs (Default: all).\n"
    data_help += "The options are separated by a space if you want to specifiy only one or more.\n"
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
    res_help += 'This option is ignored when using option "-ot" / "--output_types" with "none" value.\n\n'
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
    fps_help += "Note that for VMAF version 2 (which is the default) this value should be specified manually, otherwise the default value of 60fps will be used.\n\n"
    optional_args.add_argument("-f", "--fps", dest="fps", type=float, help=fps_help)

    misc_args = parser.add_argument_group("Miscellaneous arguments")
    misc_args.add_argument(
        "-h",
        "--help",
        action="help",
        default=argp.SUPPRESS,
        help="Show this help message and exit.\n",
    )

    args = parser.parse_args()

    print("Collecting list of files...")
    vmaf_files = []
    for VMAF in args.VMAF:
        vmaf_path = Path(VMAF)
        if vmaf_path.exists():
            if vmaf_path.is_dir():
                result_csv = []
                for i in vmaf_path.rglob("*.[cC][sS][vV]"):
                    print("Found file {}".format(i.name))
                    result_csv.append(str(i))

                result_ini = []
                for i in vmaf_path.rglob("*.[iI][nN][iI]"):
                    print("Found file {}".format(i.name))
                    result_ini.append(str(i))

                result_json = []
                for i in vmaf_path.rglob("*.[jJ][sS][oO][nN]"):
                    print("Found file {}".format(i.name))
                    result_json.append(str(i))

                result_xml = []
                for i in vmaf_path.rglob("*.[xX][mM][lL]"):
                    print("Found file {}".format(i.name))
                    result_xml.append(str(i))

                vmaf_files = result_csv + result_ini + result_json + result_xml
            elif vmaf_path.is_file():
                print("VMAF argument {} is supposed to be a directroy, but not a file.\n")
    args.VMAF = vmaf_files

    if args.fps <= 0:
        parser.exit(status=1, message="Can't use FPS value less than or equal to 0.")
    # elif not args.fps:
    #     if int(args.version) == 2:
    #         parser.error("WANRING: User did not specify an FPS value when using VMAF version 2. The default FPS value of 60 will be used when generating the video file.")

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

    if type(args.datapoints) == str:
        args.datapoints = [
            args.datapoints,
        ]

    return args


def check_report(report, config):
    print("Reading file {}...".format(Path(report).name))
    return (report, VMAF_Report_Handler(report, config).read_file())


def main(args):
    data = {}
    configs = [args.config for i in range(len(args.VMAF))]
    print("Reading files for VMAF data...")

    had_exception = False

    with cf.ThreadPoolExecutor() as pool_threads:
        try:
            ret = pool_threads.map(check_report, args.VMAF, configs)
            for item in ret:
                data[item[0]] = item[1]
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected, working on shutting down pool...")
            had_exception = True
            pool_threads.shutdown()
        except Exception:
            traceback.print_exc()
            had_exception = True

    if had_exception:
        exit(1)

    with cf.ThreadPoolExecutor() as pool_procs:
        try:
            ret = {}
            for key, value in data.items():
                ret[key] = pool_procs.submit(
                    plot_vmaf,
                    data=value,
                    fps=args.fps,
                    res=args.res,
                    output=args.output[key],
                    output_types=args.output_types,
                    datapoints=args.datapoints,
                    report=key,
                ).result()

            if any(item in ["all", "agg"] for item in args.output_types):
                print("Calculating aggregate statistics.")

                dp = []
                if "all" in args.datapoints:
                    dp = ["vmaf", "psnr", "ssim", "ms_ssim"]
                else:
                    dp = [point for point in args.datapoints]

                print("Aggregating initial data for all reports...")
                df_dict = {}
                for rep, main in ret.items():
                    df_dict[Path(rep).name] = {}
                    for point in dp:
                        for k, v in main[point].items():
                            if k in [
                                "mean",
                                "median",
                                "standard_deviation",
                                "perc_1",
                                "perc_01",
                                "perc_001",
                            ]:
                                df_dict[Path(rep).name]["{}_{}".format(point, k)] = v

                df = pd.DataFrame(df_dict)
                df = df.transpose()

                print("Aggregating rankings for each metric...")
                df2 = pd.DataFrame()
                for point in dp:
                    for k in [
                        "mean",
                        "median",
                        "standard_deviation",
                        "perc_1",
                        "perc_01",
                        "perc_001",
                    ]:
                        item = "{}_{}".format(point, k)
                        item_rank = "{}_RANK".format(item)
                        if k == "standard_deviation":
                            df2[item_rank] = df[item].rank()
                        else:
                            df2[item_rank] = df[item].rank(ascending=False)

                df2["OVERALL SCORE"] = df2.sum(axis=1)

                df = df.transpose()

                print("Adding rows for top scores to main table...")
                df["Top Score"] = pd.Series(dtype="float64")
                top_score = {}
                top_score_file = {}
                for rep, main in ret.items():
                    for point in dp:
                        for k in [
                            "mean",
                            "median",
                            "standard_deviation",
                            "perc_1",
                            "perc_01",
                            "perc_001",
                        ]:
                            item = "{}_{}".format(point, k)
                            if k == "standard_deviation":
                                top_score[item] = df.min(axis=1)[item]
                                top_score_file[item] = df.idxmin(axis=1)[item]
                            else:
                                top_score[item] = df.max(axis=1)[item]
                                top_score_file[item] = df.idxmax(axis=1)[item]

                df["Top Score"] = pd.Series(top_score)
                df["Top Score File"] = pd.Series(top_score_file)
                del top_score
                del top_score_file

                df = df.transpose()

                print("Aggregate data is {} bytes".format(df.memory_usage(deep=True).sum() + df2.memory_usage(deep=True).sum()))

                df_file = str(Path(list(args.output.values())[0]).joinpath("aggregate_stats.xlsx"))
                print("Saving aggregate statistics to file {}...".format(df_file))
                Path(df_file).unlink(missing_ok=True)
                with pd.ExcelWriter(df_file, mode="w") as writer:
                    df.to_excel(writer, sheet_name="Scores")
                    df2.to_excel(writer, sheet_name="Rankings")

        except KeyboardInterrupt:
            print("KeyboardInterrupt detected, working on shutting down pool...")
            had_exception = True
            pool_procs.shutdown()
        except Exception:
            traceback.print_exc()
            had_exception = True

    if had_exception:
        exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
