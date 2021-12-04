import argparse as argp
import concurrent.futures as cf
import multiprocessing as mp
import subprocess as sp
from datetime import timedelta
from json import dump, load
from pathlib import Path
from time import time
from traceback import print_exc

import ffmpy
from gooey import Gooey, GooeyParser
from tqdm import tqdm

from vmaf_common import bytes2human, search_handler


@Gooey(
    program_name="VMAF Calculator",
    default_size=(1280, 720),
    advanced=True,
    use_cmd_args=True,
    navigation="SIDEBAR",
    show_sidebar=True,
)
def parse_arguments() -> argp.Namespace:
    """Parse user given arguments for calculating VMAF."""
    main_help = "Multithreaded VMAF log file generator through FFmpeg."
    parser = GooeyParser(description=main_help, formatter_class=argp.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(help="commands", dest="command")

    main_parser = subparsers.add_parser("Files", help="Reference and Distorted file selection")
    main_args = main_parser.add_argument_group("Main Arguments")
    file_args = main_parser.add_argument_group("Reference and Distorted file arguments")

    ffmpeg_parser = subparsers.add_parser("FFmpeg", help="Options regarding to FFmpeg")
    ffmpeg_args = ffmpeg_parser.add_argument_group("FFmpeg arguments")
    threading_args = ffmpeg_parser.add_argument_group("Multithreading arguments")

    vmaf_parser = subparsers.add_parser("VMAF", help="Options regarding to VMAF")
    vmaf_args = vmaf_parser.add_argument_group("VMAF arguments")

    misc_parser = subparsers.add_parser("Miscellaneous", help="Miscellaneous Options")
    misc_args = misc_parser.add_argument_group("Miscellaneous arguments")

    continue_help = "Whether or not to look for a save state file for the given reference video file."
    main_args.add_argument(
        "-c", "--continue", dest="should_continue", action="store_false", help=continue_help, widget="CheckBox"
    )

    reference_help = "Reference video file(s).\n"
    reference_help += 'The program expects a single "reference" file.'
    file_args.add_argument(
        "-r",
        "--reference",
        dest="reference",
        type=str,
        required=True,
        help=reference_help,
        widget="FileChooser",
        gooey_options={
            "wildcard": "MP4 files (*.mp4)|*.mp4|"
            "MKV files (*.mkv)|*.mkv|"
            "WEBM files (*.webm)|*.webm|"
            "AVI files (*.avi)|*.avi|"
            "All files (*.*)|*.*",
            "default_dir": str(Path(__file__).parent),
        },
    )

    distorted_help = "Distorted video file(s).\n"
    distorted_help += (
        'This should be a directory, which will be scanned for any video files to compare against the "reference" file.'
    )
    file_args.add_argument(
        "-d",
        "--distorted",
        dest="distorted",
        type=str,
        help=distorted_help,
        widget="DirChooser",
        gooey_options={"default_dir": str(Path(__file__).parent)},
    )

    ffmpeg_help = "Specify the path to the FFmpeg executable.\n"
    ffmpeg_help = 'Default is "ffmpeg" which assumes that FFmpeg is part of your "Path" environment variable.\n'
    ffmpeg_help += 'The path must either point to the executable itself, or to the directory that contains the executable named "ffmpeg".'
    ffmpeg_args.add_argument(
        "-f",
        "--ffmpeg",
        dest="ffmpeg",
        type=str,
        default="ffmpeg",
        help=ffmpeg_help,
        widget="FileChooser",
        gooey_options={
            "default_dir": str(Path(__file__).parent),
            "wildcard": "EXE files (*.exe)|*.exe|" "All files (*.*)|*.*",
        },
    )

    hwaccel_help = "Enable FFmpeg to automatically attempt to use hardware acceleration for video decoding.\n"
    hwaccel_help += "Not specifying this option means FFmpeg will use only the CPU for video decoding.\n"
    hwaccel_help += (
        "Enabling this option means FFmpeg will use attempt to use the GPU for video decoding instead of the CPU.\n"
    )
    hwaccel_help += "This could improve calculation speed, but your mileage may vary."
    ffmpeg_args.add_argument("--hwaccel", dest="hwaccel", action="store_true", help=hwaccel_help)

    threads_help = 'Specify number of threads to be used for each process (Default is 0 for "autodetect").\n'
    threads_help += "A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.\n"
    threads_help += "The recommended value of threads to use per process is 4-6."
    threading_args.add_argument(
        "-t",
        "--threads",
        dest="threads",
        type=int,
        default=0,
        help=threads_help,
        widget="Slider",
        gooey_options={"min": 0, "max": mp.cpu_count()},
    )

    proc_help = "Specify number of simultaneous VMAF calculation processes to run.\n"
    proc_help += "Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process."
    threading_args.add_argument(
        "-p",
        "--processes",
        dest="processes",
        type=int,
        default=1,
        help=proc_help,
        widget="Slider",
        gooey_options={"min": 0, "max": mp.cpu_count()},
    )

    # rem_threads_help = "Specify whether or not to use remaining threads that don't make a complete process to use for an process.\n"
    # rem_threads_help += "For example, if your system has 16 threads, and you are running 5 processes with 3 threads each, then you will be using 4 * 3 threads, which is 12.\n"
    # rem_threads_help += "This means you will have 1 thread that will remain unused.\n"
    # rem_threads_help += "Using this option would run one more VMAF calculation process with only the single remaining thread.\n"
    # rem_threads_help += "This option is not recommended, as the unused threads will be used to keep the system responsive during the VMAF calculations."
    # threading_args.add_argument("-u", "--use-rem-threads", dest="use_remaining_threads", action="store_true", default=False, help=rem_threads_help, widget="CheckBox")

    psnr_help = "Enable calculating PSNR values."
    vmaf_args.add_argument("--psnr", dest="psnr", action="store_false", help=psnr_help, widget="CheckBox")

    ssim_help = "Enable calculating SSIM values."
    vmaf_args.add_argument("--ssim", dest="ssim", action="store_false", help=ssim_help, widget="CheckBox")

    ms_ssim_help = "Enable calculating MS-SSIM values."
    vmaf_args.add_argument(
        "--ms-ssim", "--ms_ssim", dest="ms_ssim", action="store_false", help=ms_ssim_help, widget="CheckBox"
    )

    subsamples_help = "Specify the number of subsamples to use.\n"
    subsamples_help += "This value only samples the VMAF and related metrics' values once every N frames.\n"
    subsamples_help += "Higher values may improve calculation performance at the cost of less accurate results.\n"
    subsamples_help += 'This variable corresponds to VMAF\'s "n_subsample" variable.'
    vmaf_args.add_argument(
        "--subsamples",
        dest="subsamples",
        help=subsamples_help,
        widget="IntegerField",
        gooey_options={"min": 1, "max": 60},
    )

    model_help = "Specify the VMAF model files to use. This argument expects a list of model files to use.\n"
    model_help += "The program will calculate the VMAF scores for every distorted file, for every model given.\n"
    model_help += "Note that VMAF models come in JSON format, and the program will only accept those models."
    vmaf_args.add_argument(
        "-m", "--model", dest="model", nargs="*", type=str, help=model_help, widget="MultiFileChooser"
    )

    log_format_help = "Specify the VMAF log file format."
    vmaf_args.add_argument(
        "-l",
        "--log-format",
        dest="log_format",
        choices=["xml", "csv", "json"],
        default="xml",
        help=log_format_help,
    )

    misc_args = misc_parser.add_argument_group("Miscellaneous arguments")
    misc_args.add_argument("-v", "--version", action="version", version="2021-12-03")

    args = parser.parse_args()

    if (not args.model or not args.distorted) and not args.should_continue:
        raise argp.ArgumentParser.error(
            "User specified not to use an existing completions file and did not provide distorted video files and/or VMAF models."
        )

    return args


def read_completions(ref):
    ref_path = Path(args.reference)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    if completions_file.exists():
        with open(str(completions_file), "r") as reader:
            return load(reader)
    else:
        return {}


def write_state(ref, completions):
    ref_path = Path(args.reference)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    with open(str(completions_file), "w") as reader:
        dump(completions, reader, indent=4, sort_keys=True)


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()

    # Create main input/output dictionary
    io = {}

    # Make sure the reference video file exists
    try:
        search_handler(args.reference)
    except OSError as ose:
        print(ose)
        exit(1)

    # Load the completions file for the given reference video file, if it exists
    completions = {}
    if args.should_continue:
        completions = read_completions(args.reference)

    # Exit if we can't get any dis
    if len(completions) == 0 and args.distorted is None:
        raise OSError(
            "Could not find any existing completions JSON files and no distorted files were provided. The program will now exit."
        )

    # Look for distorted video files in the provided locations
    dist_files = []
    if args.distorted:
        try:
            # Check if given distorted files exist, and scan for video files inside
            # any given directories.
            for dist in args.distorted:
                dist_files += search_handler(dist, search_for="distorted")

            # Remove any duplicate distorted files
            dist_files = list(set(dist_files))
        except OSError as ose:
            print(ose)
            exit(1)

        # If no distorted files are found and no completions file exists, then
        # we exit
        if len(dist_files) == 0 and len(completions) == 0 and not args.should_continue:
            msg = "Could not find any distorted files in the provided location {} and no completions save state file was provided."
            msg += "The program will now exit."
            raise OSError(msg.format(args.distorted))

    # Validate VMAF model files
    models = []
    if args.model:
        try:
            for model in args.model:
                models += search_handler(model, search_for="model")

            if len(models) == 0:
                raise OSError("Could not find any VMAF model files. The program will now exit.")

            for dist in dist_files:
                io[dist] = {}
                for model in models:
                    io[dist][model] = {}
        except OSError as ose:
            print(ose)
            exit(1)

    # If there were any distorted files in the completions file
    if len(completions) > 0:
        for dist in dist_files:
            # If the distorted file found from the provided args already
            # exists in the completions file, then we check for the status
            # of all the models it already ran through
            if dist in completions:
                # Check if the completions status for all models for the
                # distorted video files are some combination of DONE or MOVED
                check = [completions[dist][model]["status"] in ["DONE", "MOVED"] for model in completions[dist].keys()]
                if all(check):
                    # Move the distorted video file and change its' status to MOVED
                    Path(dist).replace(
                        Path(dist).parent.joinpath("{}_results".format(Path(dist).stem), Path(dist).name)
                    )
                    for model in completions[dist].keys():
                        completions[dist][model]["status"] = "MOVED"

        # Move any dist-model pairs into the io dictionary
        for dist, models in completions.items():
            if dist not in io:
                io[dist] = {}
            for model in models.keys():
                if model in io[dist]:
                    io[dist][model]["status"] = completions[dist][model]["status"]
                else:
                    io[dist][model] = {}
                    io[dist][model]["status"] = "NOT STARTED"
    del dist_files
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

    # Holds the concurrent.futures.Future objects from the ThreadPoolExecutor's
    # submit calls as keys, with the distorted video file name and VMAF model
    # name as values
    my_ffs = {}

    # Used to count how many models have been processed for a given distorted
    # video file
    num_models = {}
    for dist in io.keys():
        num_models[dist] = 0
    dist_finished = 0
    dists_total = len(io.keys()) * len(list(io.values())[0])

    # Semi-global check if the Futures were cancelled
    # If this is set to True at any point, then we stop writing any aggregate
    # score files and do not move the video files
    was_cancelled = False

    cf_handler = cf.ThreadPoolExecutor(max_workers=args.processes)
    start = time()
    try:
        # For every distorted video file
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
                my_ffs[cf_handler.submit(ff_tmp.run, stdout=sp.PIPE, stderr=sp.PIPE)] = {
                    "ff": ff_tmp,
                    "dist": dist,
                    "model": model,
                }
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
                    pbar.set_postfix(
                        {
                            "Distorted videos finished": str(
                                "{} : {}%".format(dist_finished, dist_finished / io.keys() * 100)
                            )
                        }
                    )
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
                        size_converted = bytes2human(aggregate[dist]["file_size"])

                        # Write the size in bytes & the size in human-readable
                        # format to the aggregate log file
                        tmp_msg = "File Size: {}B = {}\n"
                        aggregate_file.write(tmp_msg.format(aggregate[dist]["file_size"], size_converted))

                    for model in models.keys():
                        io[dist][model]["status"] = "MOVED"
                pbar.update()

    # All exceptions try to cancel the existing tasks in the pool and will exit
    # the program afterwards.
    except (KeyboardInterrupt, cf.CancelledError, ffmpy.FFRuntimeError, Exception) as e:
        if type(e) in [KeyboardInterrupt, cf.CancelledError]:
            print("KeyboardInterrupt detected, working on shutting down pool...")
        else:
            print_exc()
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
                        while info["ff"].process.poll() is None:
                            info["ff"].process.terminate()
                            info["ff"].process.kill()
                            info["ff"].process.wait()
                        if io[dist][model]["status"] not in ["DONE", "MOVED"]:
                            time.sleep(0.5)
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

    end = time()
    total = end - start

    # Show how long it took to run this entire program
    print("Program took {}".format(timedelta(seconds=total)))
    time_avg = timedelta(seconds=total / len(my_ffs))
    print("All calculations took an average of {}\n".format(time_avg))

    # Print out all the relevant info to the user
    print("The scores are as follows:")
    print("Reference: {}".format(args.reference))
    for dist, models in io.items():
        print("Distorted: {}".format(dist))
        print(aggregate[dist]["msg"])
        for model in models.keys():
            print(io[dist][model]["msg"])
