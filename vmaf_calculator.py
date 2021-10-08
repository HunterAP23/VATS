import argparse as argp
import concurrent.futures as cf
import datetime as dt
import json
import subprocess as sp
import time
import traceback
from pathlib import Path

import ffmpy
from tqdm import tqdm

from vmaf_common import bytes2human, print_dict, search_handler


def parse_arguments() -> argp.Namespace:
    """Parse user given arguments for calculating VMAF."""
    main_help = "Multithreaded VMAF log file generator through FFmpeg.\n"
    main_help += 'The program expects a single "reference" file.\n'
    main_help += 'Specifying a single "distorted" file will only run a single VMAF calculation instance between it and the "reference" file.\n'
    main_help += 'Specifying a single "reference" file and multiple "distorted" files will compare the "reference" file against all the "disrotred" files.\n'
    main_help += 'Specifying a directory for the "distorted" argument will scan the diretory for any MP4 and MKV files to compare against the "reference" file.\n\n'
    parser = argp.ArgumentParser(
        description=main_help,
        formatter_class=argp.RawTextHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "-r",
        "--reference",
        dest="reference",
        type=str,
        required=True,
        help="reference video file().\n",
    )
    parser.add_argument(
        "-d",
        "--distorted",
        dest="distorted",
        nargs="*",
        type=str,
        required=True,
        help="distorted video file().\n\n",
    )

    optional_args = parser.add_argument_group("Optional arguments")
    ffmpeg_help = 'Specify the path to the FFmpeg executable (Default is "ffmpeg" which assumes that FFmpeg is part of your "Path" environment variable).\n'
    ffmpeg_help += 'The path must either point to the executable itself, or to the directory that contains the executable named "ffmpeg".\n\n'
    optional_args.add_argument("-f", "--ffmpeg", dest="ffmpeg", default="ffmpeg", help=ffmpeg_help)

    threads_help = 'Specify number of threads to be used for each process (Default is 0 for "autodetect").\n'
    threads_help += "Specifying more threads than there are available will clamp the value down to 1 thread for safety purposes.\n"
    threads_help += "A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.\n"
    threads_help += "The recommended value of threads to use per process is 4-6.\n\n"
    optional_args.add_argument("-t", "--threads", dest="threads", type=int, default=0, help=threads_help)

    proc_help = "Specify number of simultaneous VMAF calculation processes to run (Default is 1).\n"
    proc_help += "Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.\n\n"
    optional_args.add_argument("-p", "--processes", dest="processes", type=int, default=1, help=proc_help)

    # rem_threads_help = "Specify whether or not to use remaining threads that don't make a complete process to use for an process (Default is off).\n"
    # rem_threads_help += "For example, if your system has 16 threads, and you are running 5 processes with 3 threads each, then you will be using 4 * 3 threads, which is 12.\n"
    # rem_threads_help += "This means you will have 1 thread that will remain unused.\n"
    # rem_threads_help += "Using this option would run one more VMAF calculation process with only the single remaining thread.\n"
    # rem_threads_help += "This option is not recommended, as the unused threads will be used to keep the system responsive during the VMAF calculations.\n\n"
    # optional_args.add_argument(
    #     "-u",
    #     "--use-rem-threads",
    #     dest="use_remaining_threads",
    #     action="store_true",
    #     default=False,
    #     help=rem_threads_help,
    # )

    vmaf_version_help = "Specify the VMAF version to use (Default is 2).\n\n"
    optional_args.add_argument(
        "-v",
        "--vmaf-version",
        dest="vmaf_version",
        type=int,
        choices=[1, 2],
        default=2,
        help=vmaf_version_help,
    )

    psnr_help = "Enable calculating PSNR values (Default is off).\n\n"
    optional_args.add_argument("--psnr", dest="psnr", action="store_true", help=psnr_help)

    ssim_help = "Enable calculating SSIM values (Default is off).\n\n"
    optional_args.add_argument("--ssim", dest="ssim", action="store_true", help=ssim_help)

    ms_ssim_help = "Enable calculating MS-SSIM values (Default is off).\n\n"
    optional_args.add_argument("--ms-ssim", "--ms_ssim", dest="ms_ssim", action="store_true", help=ms_ssim_help)

    subsamples_help = "Specify the number of subsamples to use (default 1).\n"
    subsamples_help += "This value only samples the VMAF and related metrics' values once every N frames.\n"
    subsamples_help += "Higher values may improve calculation performance at the cost of less accurate results.\n\n"
    subsamples_help += 'This variable corresponds to VMAF\'s "n_subsample" variable.\n\n'
    optional_args.add_argument("--subsamples", dest="subsamples", help=subsamples_help)

    model_help = "Specify the VMAF model files to use. This argument expects a list of model files to use.\n"
    model_help += "The program will calculate the VMAF scores for every distorted file, for every model given.\n"
    model_help += "Note that VMAF version 1 requires PKL model files, while VMAF version 2 uses JSON model files.\n\n"
    optional_args.add_argument(
        "-m",
        "--model",
        dest="model",
        nargs="*",
        type=str,
        required=True,
        help=model_help,
    )

    log_format_help = 'Specify the VMAF log file format (Default is "xml").\n\n'
    optional_args.add_argument(
        "-l",
        "--log-format",
        dest="log_format",
        choices=["xml", "csv", "json"],
        default="xml",
        help=log_format_help,
    )

    hwaccel_help = "Enable FFmpeg to automatically attempt to use hardware acceleration for video decoding (default is off).\n"
    hwaccel_help += "Not specifying this option means FFmpeg will use only the CPU for video decoding.\n"
    hwaccel_help += "Enabling this option means FFmpeg will use attempt to use the GPU for video decoding instead.\n"
    hwaccel_help += "This could improve calculation speed, but your mileage may vary.\n\n"
    optional_args.add_argument("--hwaccel", dest="hwaccel", action="store_true", help=hwaccel_help)

    misc_args = parser.add_argument_group("Miscellaneous arguments")
    misc_args.add_argument(
        "-h",
        "--help",
        action="help",
        default=argp.SUPPRESS,
        help="Show this help message and exit.\n",
    )

    return parser.parse_args()


def read_completions(ref):
    ref_path = Path(args.reference)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    if completions_file.exists():
        with open(str(completions_file), "r") as reader:
            return json.load(reader)
    else:
        return {}


def write_state(ref, completions):
    ref_path = Path(args.reference)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    with open(str(completions_file), "w") as reader:
        json.dump(completions, reader, indent=4, sort_keys=True)


if __name__ == "__main__":
    # Get start time of program

    # Parse command line arguments
    args = parse_arguments()

    # Create main input/output dictionary
    io = {}
    try:
        search_handler(args.reference)
    except OSError as ose:
        print(ose)
        exit(1)

    try:
        dist_files = []
        for dist in args.distorted:
            dist_files += search_handler(dist, search_for="distorted")

        dist_files = set(dist_files)
        if len(dist_files) == 0:
            raise OSError("ERROR: Could not find any distorted files. The program will now exit.")

        for dist in dist_files:
            io[dist] = {}
    except OSError as ose:
        print(ose)
        exit(1)

    # Validate VMAF model files
    try:
        tmp_models = []
        for model in args.model:
            tmp_models += search_handler(model, search_for="model", vmaf_version=args.vmaf_version)

        if len(tmp_models) == 0:
            raise OSError("ERROR: Could not find any VMAF model files. The program will now exit.")

        for dist in io.keys():
            for model in tmp_models:
                io[dist][model] = {}

    except OSError as ose:
        print(ose)
        exit(1)

    completions = read_completions(args.reference)
    if len(completions) > 0:
        for dist, models in completions.items():
            for model in models.keys():
                if dist in io:
                    if model in io[dist]:
                        io[dist][model]["status"] = completions[dist][model]["status"]
                    else:
                        io[dist][model] = {}
                        io[dist][model]["status"] = "NOT STARTED"
                else:
                    io[dist] = {}
                    io[dist][model] = {}
                    io[dist][model]["status"] = "NOT STARTED"
    del completions

    for dist, models in io.items():
        for model in models.keys():
            if "status" not in io[dist][model]:
                io[dist][model]["status"] = "NOT STARTED"

    write_state(args.reference, io)

    aggregate = {}

    # Beginning of libvmaf filter
    for dist, models in io.items():
        for model in models.keys():
            if io[dist][model]["status"] not in ["DONE", "MOVED"]:
                io[dist][model]["status"] = "NOT STARTED"
            # Start libvmaf filter and plug in vmaf model
            tmp_filter = "libvmaf=model_path={}".format(model).replace("\\", "/").replace(":", "\\:")
            # Add specified log format argument to libvmaf filter
            tmp_filter += ":log_fmt={}".format(args.log_format)

            # Get dist path for creating results folder next to it
            dist_path = Path(dist)
            dist_parent = dist_path.parent
            # Used for the final log location for each distorted file
            log_loc = None

            # Attempt to create a new directory for storing the log results
            try:
                log_dir = dist_parent.joinpath("{}_results".format(dist_path.stem))
                log_dir.mkdir(exist_ok=True)
                log_loc = "{}_{}.{}".format(dist_path.stem, Path(model).stem, args.log_format)
                log_loc = log_dir.joinpath(log_loc)

                if dist not in aggregate.keys():
                    aggregate[dist] = {}
                    aggregate_log = "{}_aggregate.txt".format(dist_path.stem)
                    aggregate[dist]["log"] = log_dir.joinpath(aggregate_log)
                    aggregate[dist]["file_size"] = Path(dist).stat().st_size
                    aggregate[dist]["score"] = 0

            except OSError as ose:
                print(ose)
                exit(1)

            # Clean up the log path for windows systems
            io[dist][model]["log_path"] = str(log_loc).replace("\\", "/").replace(":", "\\:")
            if io[dist][model]["status"] == "NOT STARTED":
                Path(io[dist][model]["log_path"]).unlink(missing_ok=True)
            # Save the libmvaf filter arguments and log path into the commands key
            io[dist][model]["commands"] = "{}:log_path={}".format(tmp_filter, io[dist][model]["log_path"])

    # 2nd part of the libvmaf filter
    tmp_filter = ""
    if args.psnr:
        tmp_filter += ":psnr=1"
    if args.ssim:
        tmp_filter += ":ssim=1"
    if args.ms_ssim:
        tmp_filter += ":ms_ssim=1"
    if args.subsamples:
        tmp_filter += ":n_subsample={}".format(args.subsamples)
    if args.threads != 0:
        tmp_filter += ":n_threads={}".format(args.threads)

    # Combine all the filter arguments and save them for each dist-model dict
    for dist, models in io.items():
        for model in models.keys():
            if io[dist][model]["status"] == "NOT STARTED":
                io[dist][model]["commands"] += tmp_filter
                io[dist][model]["commands"] = repr(io[dist][model]["commands"])
                io[dist][model]["commands"] = "-filter_complex " + io[dist][model]["commands"] + " -f null"

    # Create input arguments, are just related to decoding the reference and
    # distorted video files
    decode = "-threads 1"
    if args.hwaccel:
        # decode += " -c:v h264_cuvid -hwaccel auto"
        decode += " -hwaccel auto"
        # decode += " -c:v h264_cuvid "

    # Holds the concurrent.futures.Future objects from the ThreadPoolExectuor's
    # submit calls as keys, with the distorted video file name and VMAF model
    # name as values
    my_ffs = {}

    # Used to count how many models have been processed for a given distorted
    # video file
    num_models = {}
    for dist in io.keys():
        num_models[dist] = 0
    dist_finished = 0
    dists_total = len(io) * len(list(io.values())[0])

    # Semi-global check if the Futures were cancelled
    # If this is set to True at any oint, then we stop writing any aggregate
    # score files and do not move the video files
    was_cancelled = False

    cf_handler = cf.ThreadPoolExecutor(max_workers=args.processes)
    start = time.time()
    try:
        # For every ditorted video file
        for dist, models in io.items():
            # For every model to test the distorted video with
            for model, data in models.items():
                if io[dist][model]["status"] in ["DONE", "MOVED"]:
                    continue
                # Submit an ffmpy task to the pool
                msg = "Submitting VMAF calculation:\n\tReference: {}\n\tDistorted: {}\n\tModel: {}\n\tLog File: {}\n"
                print(msg.format(args.reference, dist, model, io[dist][model]["log_path"]))

                # Create the ffmpy.FFmpeg class containing the inputs and output
                # commands
                ff_tmp = ffmpy.FFmpeg(
                    executable=args.ffmpeg,
                    global_options=[
                        "-hide_banner",
                    ],
                    inputs={dist: decode, str(args.reference): decode},
                    outputs={"-": str(data["commands"])},
                )

                # Submit the actual run Future as a key
                my_ffs[cf_handler.submit(ff_tmp.run, stdout=sp.PIPE, stderr=sp.PIPE)] = {"ff": ff_tmp, "dist": dist, "model": model}
                io[dist][model]["status"] = "STARTED"

        # After submitting all tasks, have a tqdm progress bar measure the progress
        with tqdm(
            desc="Processing VMAF calculations",
            total=len(my_ffs),
            unit="reports",
            position=0,
            leave=True,
        ) as pbar:
            pbar.set_postfix({"Distorted videos finished": "0 : 0%"})
            # Wait and iterate over completed Futures
            for task in cf.as_completed(my_ffs):
                pbar.set_postfix({"Distorted videos finished": str("{} : {}%".format(dist_finished, dist_finished / dists_total))})
                # Dict containing the "dist" and "model" keys
                out = my_ffs[task]
                dist = out["dist"]
                model = out["model"]

                io[dist][model]["status"] = "DONE"

                # Contains the actual stdout and stderr of the ffmpy call
                # In our case we only need the stderr
                err = task.result()[1]

                # Prepare the output message for this dist-model combination
                msg = "\tVMAF Model: {}\n".format(model)
                log_path = str(Path(io[dist][model]["log_path"]))
                msg += "\tLog Location: {}\n".format(log_path.replace("\\:", ":").replace('"', "/"))

                # Look for the average VMAF score given in the stderr
                for line in err.decode("utf-8").split("\n"):
                    if "VMAF score" in line:
                        vmaf_score = float(line.split("]")[1].split(": ")[1].strip())
                        # Set the score for this dist-model combination
                        io[dist][model]["score"] = vmaf_score
                        # Add this score to the overall score of the dist video
                        # file between all models
                        aggregate[dist]["score"] += vmaf_score
                        msg += "\tVMAF Score: {}\n\n".format(vmaf_score)
                        break

                # Save the dist-model output message for later
                io[dist][model]["msg"] = msg

                # Since we just finished using a model on this specific dist
                # video file, we increment the counter for the number of models
                # completed for this dist file
                num_models[dist] += 1
                # If we've finished testing all models against this dist, then
                # we can save the aggregate statistics and move the video file
                # to the log location
                if num_models[dist] == len(io[dist].keys()):
                    dist_finished += 1
                    # Move the dist video file to the log location
                    dist_path = Path(dist)
                    dist_path_new = aggregate[dist]["log"].parent.joinpath(dist_path.name)
                    dist_path.replace(dist_path_new)

                    # Get the average VMAF score between all model files
                    aggregate[dist]["score"] /= len(io[dist].keys())

                    # Save score to aggregate dist's output message
                    tmp_msg = "Average VMAF Score between all tested VMAF models is {}\n"
                    aggregate[dist]["msg"] = tmp_msg.format(aggregate[dist]["score"])

                    # Open the aggregate statistics file for writing to
                    with open(aggregate[dist]["log"], "w") as aggregate_file:
                        for model in models.keys():
                            # Write the average score for each model to the
                            # aggregate log file
                            tmp_msg = "{} Score: {}\n"
                            aggregate_file.write(tmp_msg.format(model, io[dist][model]["score"]))

                        # Write average VMAF score to aggregate log file
                        tmp_msg = "\nAverage Score: {}\n"
                        aggregate_file.write(tmp_msg.format(aggregate[dist]["score"]))

                        # Convert file size to a more human-readable format
                        size_converted, size_unit = bytes2human(aggregate[dist]["file_size"])

                        # Write the size in bytes & the size in human-readable
                        # format to the aggregate log file
                        tmp_msg = "File Size: {}B = {}{}\n"
                        aggregate_file.write(tmp_msg.format(aggregate[dist]["file_size"], size_converted, size_unit))

                    for model in models.keys():
                        io[dist][model]["status"] = "MOVED"
                pbar.update()

    # All exceptions try to cancel the existing tasks in the pool and will exit
    # the program afterwards.
    except (KeyboardInterrupt, cf.CancelledError, ffmpy.FFRuntimeError, Exception) as e:
        if type(e) in [KeyboardInterrupt, cf.CancelledError]:
            print("KeyboardInterrupt detected, working on shutting down pool...")
        else:
            traceback.print_exc()
        was_cancelled = True
        cf_handler.shutdown(wait=False, cancel_futures=True)
        cancellations = {task: False for task in my_ffs.keys()}
        while not any([item for item in cancellations.values()]):
            for task, info in my_ffs.items():
                dist = info["dist"]
                model = info["model"]
                # If the task is still running, or if it finished but was cancelled,
                # or if it raised an exception, then we cancel the task
                if task.running() or (task.done() and task.cancelled()) or task.exception():
                    if info["ff"].process:
                        print("Shutting down {}...".format(info["ff"].process.pid))
                        info["ff"].process.terminate()
                        info["ff"].process.kill()
                        info["ff"].process.wait()
                        if io[dist][model]["status"] not in ["DONE", "MOVED"]:
                            print("\tDeleting related log file:\n\t{}...".format(Path(io[dist][model]["log_path"])))
                            Path(io[dist][model]["log_path"]).unlink(missing_ok=True)
                        cancellations[task] = True
                    if io[dist][model]["status"] not in ["DONE", "MOVED"]:
                        io[dist][model]["status"] = "CANCELLED"
        del cancellations
        print("Pool has shutdown, exiting...")
    else:
        cf_handler.shutdown()

    write_state(args.reference, io)
    # If an exception occurred, then this will finish exiting the program
    if was_cancelled:
        exit(1)

    end = time.time()
    total = end - start

    # Show how long it took to run this entire program
    print("Program took {}".format(dt.timedelta(seconds=total)))
    time_avg = dt.timedelta(seconds=total / len(my_ffs))
    print("All calculations took an average of {}\n".format(time_avg))

    # Print out all the releveant info to the user
    print("The scores are as follows:")
    print("Reference: {}".format(args.reference))
    for dist, models in io.items():
        print("Distorted: {}".format(dist))
        print(aggregate[dist]["msg"])
        for model in models.keys():
            print(io[dist][model]["msg"])
