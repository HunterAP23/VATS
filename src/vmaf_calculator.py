import concurrent.futures as cf
import multiprocessing as mp
import os
import subprocess as sp
import sys
from argparse import RawTextHelpFormatter
from datetime import timedelta
from json import dump, load
from pathlib import Path
from time import time
from traceback import print_exc

import ffmpy
from gooey import Gooey, GooeyParser
from tqdm import tqdm

from vmaf_common import bytes2human, print_dict, search_handler


@Gooey(
    program_name="VMAF Suite Calculator",
    default_size=(1280, 720),
    advanced=True,
    use_cmd_args=True,
    # navigation="TABBED",
    # show_sidebar=True,
)
def parse_arguments(curdir):
    """Parse user given arguments for calculating VMAF scores.

    Raises:
        ValueError: User specified not to use an existing completions file and did not provide encoded video files and/or VMAF models.

    Returns:
        _type_: GooeyParser.parser() arguments
    """

    main_help = "Multithreaded VMAF log file generator through FFmpeg."
    parser = GooeyParser(description=main_help, formatter_class=RawTextHelpFormatter)

    main_args = parser.add_argument_group("Main arguments")
    file_args = parser.add_argument_group("Reference and Encoded file arguments")

    ffmpeg_args = parser.add_argument_group("FFmpeg arguments")
    threading_args = parser.add_argument_group("Multithreading arguments")

    vmaf_args = parser.add_argument_group("VMAF arguments")

    misc_args = parser.add_argument_group("Miscellaneous arguments")

    continue_help = "Whether or not to look for a save state file for the given reference video file."
    main_args.add_argument(
        "--Continue",
        action="store_false",
        help=continue_help,
        widget="CheckBox",
    )

    reference_help = "Reference video file(s).\n"
    reference_help += 'The program expects a single "reference" file.'
    file_args.add_argument(
        "-Reference",
        type=str,
        required=True,
        help=reference_help,
        widget="FileChooser",
        gooey_options={
            "wildcard": "".join(
                [
                    "MP4 files (*.mp4)|*.mp4|",
                    "MKV files (*.mkv)|*.mkv|",
                    "WEBM files (*.webm)|*.webm|",
                    "AVI files (*.avi)|*.avi|",
                    "All files (*.*)|*.*",
                ]
            ),
            "default_dir": str(curdir),
            "validator": {
                "test": "Path(r).exists() and Path(r).is_file() for r in user_input",
                "message": "Must include at least one existing file.",
            },
        },
    )

    encoded_help = "Encoded video file(s).\n"
    encoded_help += (
        'This should be a directory, which will be scanned for any video files to compare against the "reference" file.'
    )
    file_args.add_argument(
        "-Encoded",
        type=str,
        help=encoded_help,
        widget="DirChooser",
        gooey_options={
            "default_dir": str(curdir),
            "validator": {
                "test": "Path(d).exists() and Path(d).is_file() for r in user_input",
                "message": "Must include at least one existing directory.",
            },
        },
    )

    ffmpeg_help = "Specify the path to the FFmpeg executable.\n"
    ffmpeg_help = 'Default is "ffmpeg" which assumes that FFmpeg is part of your "Path" environment variable.\n'
    ffmpeg_help += 'The path must either point to the executable itself, or to the directory that contains the executable named "ffmpeg".'
    ffmpeg_args.add_argument(
        "--FFmpeg",
        type=str,
        default="ffmpeg",
        help=ffmpeg_help,
        widget="FileChooser",
        gooey_options={
            "default_dir": str(curdir),
            "wildcard": "EXE files (*.exe)|*.exe|" "All files (*.*)|*.*",
        },
    )

    hwaccel_help = "Enable FFmpeg to automatically attempt to use hardware acceleration for video decoding.\n"
    hwaccel_help += "Not specifying this option means FFmpeg will use only the CPU for video decoding.\n"
    hwaccel_help += (
        "Enabling this option means FFmpeg will use attempt to use the GPU for video decoding instead of the CPU.\n"
    )
    hwaccel_help += "This could improve calculation speed, but your mileage may vary."
    ffmpeg_args.add_argument(
        "--HWaccel",
        action="store_true",
        help=hwaccel_help,
    )

    threads_help = 'Specify number of threads to be used for each process (Default is 0 for "autodetect").\n'
    threads_help += "A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.\n"
    threads_help += "The recommended value of threads to use per process is 4-6."
    threading_args.add_argument(
        "--Threads",
        type=int,
        default=0,
        help=threads_help,
        widget="Slider",
        gooey_options={
            "min": 0,
            "max": mp.cpu_count(),
        },
    )

    proc_help = "Specify number of simultaneous VMAF calculation processes to run.\n"
    proc_help += "Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process."
    threading_args.add_argument(
        "--Processes",
        type=int,
        default=1,
        help=proc_help,
        widget="Slider",
        gooey_options={
            "min": 0,
            "max": mp.cpu_count(),
        },
    )

    # rem_threads_help = "Specify whether or not to use remaining threads that don't make a complete process to use for an process.\n"
    # rem_threads_help += "For example, if your system has 16 threads, and you are running 5 processes with 3 threads each, then you will be using 4 * 3 threads, which is 12.\n"
    # rem_threads_help += "This means you will have 1 thread that will remain unused.\n"
    # rem_threads_help += "Using this option would run one more VMAF calculation process with only the single remaining thread.\n"
    # rem_threads_help += "This option is not recommended, as the unused threads will be used to keep the system responsive during the VMAF calculations."
    # threading_args.add_argument("-u", "--use-rem-threads", dest="use_remaining_threads", action="store_true", default=False, help=rem_threads_help, widget="CheckBox",)

    ssim_help = "Enable calculating SSIM values."
    vmaf_args.add_argument(
        "--SSIM",
        action="store_false",
        help=ssim_help,
        widget="CheckBox",
    )

    ms_ssim_help = "Enable calculating MS-SSIM values."
    vmaf_args.add_argument(
        "--MS_SSIM",
        action="store_false",
        help=ms_ssim_help,
        widget="CheckBox",
    )

    psnr_help = "Enable calculating PSNR values."
    vmaf_args.add_argument(
        "--PSNR",
        action="store_false",
        help=psnr_help,
        widget="CheckBox",
    )

    subsamples_help = "Specify the number of subsamples to use.\n"
    subsamples_help += "This value only samples the VMAF and related metrics' values once every N frames.\n"
    subsamples_help += "Higher values may improve calculation performance at the cost of less accurate results.\n"
    subsamples_help += 'This variable corresponds to VMAF\'s "n_subsample" variable.'
    vmaf_args.add_argument(
        "--Subsamples",
        help=subsamples_help,
        widget="IntegerField",
        gooey_options={"min": 1, "max": 60},
    )

    # model_help = "Specify the VMAF model files to use. This argument expects a list of model files to use.\n"
    # model_help += "The program will calculate the VMAF scores for every encoded file, for every model given.\n"
    # model_help += "Note that VMAF models come in JSON format, and the program will only accept those models."
    # vmaf_args.add_argument(
    #     "--Model",
    #     nargs="*",
    #     default=["vmaf_v0.6.1", "vmaf_v0.6.1neg", "vmaf_4k_v0.6.1",],
    #     help=model_help,
    #     widget="MultiFileChooser",
    # )

    log_format_help = "Specify the VMAF log file format."
    vmaf_args.add_argument(
        "--Log_Format",
        choices=["xml", "csv", "json"],
        default="xml",
        help=log_format_help,
    )

    misc_args.add_argument(
        "-v",
        "--version",
        action="version",
        version="2021-12-06",
    )

    args = parser.parse_args()

    print("\n")
    for arg in dir(args):
        if "_" in arg:
            continue
        print("{}: {}".format(arg, getattr(args, arg)))
    print("\n")

    # if (not args.Model or not args.Encoded) and not args.Continue:
    #     raise ValueError(
    #         "User specified not to use an existing completions file and did not provide encoded video files directory."
    #     )

    return args


def read_completions(ref):
    """Read through completions JSON file to see what calculations were already complete.

    Args:
        ref (_type_): _description_

    Returns:
        _type_: _description_
    """
    ref_path = Path(ref)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    if completions_file.exists():
        with open(str(completions_file), "r") as reader:
            return load(reader)
    else:
        return {}


def write_state(
    ref,
    completions,
):
    ref_path = Path(ref)
    completions_file = Path(ref_path.parent.joinpath("{}_completions.json".format(ref_path.stem)))
    with open(str(completions_file), "w") as writer:
        dump(
            completions,
            writer,
            indent=4,
            sort_keys=True,
        )


def main():
    curdir = None
    if getattr(sys, "frozen", False):
        curdir = Path(sys.executable).parent
    elif __file__:
        curdir = Path(os.getcwd())

    # Parse command line arguments
    args = parse_arguments(curdir)
    models = {
        "vmaf_v0.6.1": "vmaf",
        "vmaf_v0.6.1neg": "vmaf_neg",
        "vmaf_4k_v0.6.1": "vmaf_4k",
    }

    # Create main input/output dictionary
    io = {}

    # Make sure the reference video file exists
    try:
        search_handler(args.Reference)
    except OSError as ose:
        print(ose)
        exit(1)

    # Load the completions file for the given reference video file, if it exists
    completions = {}
    if args.Continue:
        completions = read_completions(args.Reference)

    # Exit if we can't get any dis
    if len(completions) == 0 and args.Encoded is None:
        raise OSError(
            "Could not find any existing completions JSON files and no encoded files were provided. The program will now exit."
        )

    # Look for encoded video files in the provided locations
    enc_files = None
    if args.Encoded:
        try:
            # Check if given encoded files exist, and scan for video files inside
            # any given directories.
            enc_files = search_handler(args.Encoded, search_for="encoded")

            # Remove any duplicate encoded files
            enc_files = tuple(set(enc_files))
        except OSError as ose:
            print(ose)
            exit(1)

        # If no encoded files are found and no completions file exists, then
        # we exit
        if len(enc_files) == 0 and len(completions) == 0 and not args.Continue:
            msg = "Could not find any encoded files in the provided location {} and no completions save state file was provided."
            msg += "The program will now exit."
            raise OSError(msg.format(args.Encoded))

    # Validate VMAF model files

    for enc in enc_files:
        io[enc] = {}

    # If there were any encoded files in the completions file
    if len(completions) > 0:
        for enc in enc_files:
            # If the encoded file found from the provided args already
            # exists in the completions file, then we check for the status
            # of all the models it already ran through
            if enc in completions:
                # Check if the completions status for all models for the
                # encoded video files are some combination of DONE or MOVED
                check = completions[enc]["status"] in ["DONE", "MOVED"]
                if check:
                    # Move the encoded video file and change its' status to MOVED
                    Path(enc).replace(
                        Path(enc).parent.joinpath("{}_results".format(Path(enc).stem), Path(enc).name),
                    )
                    completions[enc]["status"] = "MOVED"

        # Move any enc-model pairs into the io dictionary
        for enc in completions.keys():
            if enc not in io:
                io[enc] = {}
                io[enc]["status"] = "NOT STARTED"
            else:
                io[enc]["status"] = completions[enc]["status"]

    del enc_files
    del completions

    for enc in io.keys():
        if "status" not in io[enc]:
            io[enc]["status"] = "NOT STARTED"

    write_state(args.Reference, io)
    aggregate = {}

    # Beginning of libvmaf filter
    for enc in io.keys():
        if io[enc]["status"] not in ["DONE", "MOVED"]:
            io[enc]["status"] = "NOT STARTED"
        # Start libvmaf filter and plug in vmaf model

        tmp_models = []
        for model, name in models.items():
            tmp_models.append("{}\\\\:name={}".format(model, name))
        tmp_models = "'{}'".format("|".join(tmp_models))
        tmp_filter = "libvmaf=model=version={}".format(tmp_models)

        # Add specified log format argument to libvmaf filter
        tmp_filter += ":log_fmt={}".format(args.Log_Format)

        # Get enc path for creating results folder next to it
        enc_path = Path(enc)
        enc_parent = enc_path.parent
        # Used for the final log location for each encoded file
        log_loc = None

        # Attempt to create a new directory for storing the log results
        try:
            # log_dir = enc_parent.joinpath("{}_results".format(enc_path.stem))
            log_dir = curdir.joinpath("logs")
            log_dir.mkdir(exist_ok=True)
            log_loc = "{}.{}".format(
                enc_path.stem,
                args.Log_Format,
            )
            log_loc = log_dir.joinpath(log_loc)

            if enc not in aggregate.keys():
                aggregate[enc] = {}
                aggregate_log = "{}_aggregate.txt".format(enc_path.stem)
                aggregate[enc]["log"] = log_dir.joinpath(aggregate_log)
                aggregate[enc]["file_size"] = Path(enc).stat().st_size
                aggregate[enc]["score"] = 0

        except OSError as ose:
            print(ose)
            exit(1)

        # Clean up the log path for windows systems
        io[enc]["log_path"] = str(log_loc).replace("\\", "/")  # .replace(":", "\\:")
        if io[enc]["status"] == "NOT STARTED":
            Path(io[enc]["log_path"]).unlink(missing_ok=True)
        # Save the libmvaf filter arguments and log path into the commands key
        io[enc]["commands"] = "{}:log_path={}".format(tmp_filter, io[enc]["log_path"])

    # 2nd part of the libvmaf filter
    tmp_filter = []
    # if args.psnr:
    #     tmp_filter += "name=psnr_hvs:"
    if args.SSIM:
        tmp_filter.append("name=float_ssim")
    if args.MS_SSIM:
        tmp_filter.append("name=float_ms_ssim")
    if args.Subsamples:
        tmp_filter.append("n_subsample={}".format(args.Subsamples))
    if args.Threads != 0:
        tmp_filter.append("n_threads={}".format(args.Threads))

    tmp_filter = ":feature={}".format("\\\\:".join(tmp_filter))

    # Combine all the filter arguments and save them for each enc-model dict
    for enc in io.keys():
        if io[enc]["status"] == "NOT STARTED":
            io[enc]["commands"] += tmp_filter
            # io[enc]["commands"] = repr(io[enc]["commands"])
            io[enc]["commands"] = (
                "-threads {0} -filter_threads {0} -filter_complex_threads {0} [0:v:0]setpts=PTS-STARTPTS[ref];[1:v:0]setpts=PTS-STARTPTS,colorspace=ispace=bt709:iprimaries=bt709:itrc=bt709:irange=tv:space=bt709:primaries=bt709:trc=bt709:range=tv:format=yuv444p12:dither=fsb[cmp];[ref][cmp]"
                + io[enc]["commands"]
                + " -f null"
            )

    # Create input arguments, are just related to decoding the reference and
    # encoded video files
    decode = "-threads {0}".format(args.Threads)
    if args.HWaccel:
        decode += " -hwaccel auto"

    # Holds the concurrent.futures.Future objects from the ThreadPoolExecutor's
    # submit calls as keys, with the encoded video file name and VMAF model
    # name as values
    my_ffs = {}

    # Used to count how many models have been processed for a given encoded
    # video file
    enc_finished = 0
    print_dict(io)

    # Semi-global check if the Futures were cancelled
    # If this is set to True at any point, then we stop writing any aggregate
    # score files and do not move the video files
    was_cancelled = False

    cf_handler = cf.ThreadPoolExecutor(max_workers=args.Processes)
    start = time()
    try:
        # For every encoded video file
        for enc, data in io.items():
            # For every model to test the encoded video with
            if io[enc]["status"] in ["DONE", "MOVED"]:
                continue
            # Submit an ffmpy task to the pool
            msg = "Submitting VMAF calculation:\n\tReference: {}\n\tEncoded: {}\n\tLog File: {}\n"
            print(
                msg.format(
                    args.Reference,
                    enc,
                    io[enc]["log_path"],
                )
            )

            # Create the ffmpy.FFmpeg class containing the inputs and output
            # commands
            ff_tmp = ffmpy.FFmpeg(
                executable=args.FFmpeg,
                global_options=[
                    "-hide_banner",
                ],
                inputs={enc: decode, str(args.Reference): decode},
                outputs={"-": str(data["commands"].format(args.Threads))},
            )

            print(ff_tmp.cmd + "\n")
            exit()

            # Submit the actual run Future as a key
            my_ffs[
                cf_handler.submit(
                    ff_tmp.run,
                    stdout=sp.PIPE,
                    stderr=sp.PIPE,
                )
            ] = {
                "ff": ff_tmp,
                "enc": enc,
            }
            io[enc]["status"] = "STARTED"

        # After submitting all tasks, have a tqdm progress bar measure the progress
        with tqdm(
            desc="Processing VMAF calculations",
            total=len(my_ffs),
            unit="reports",
            position=0,
            leave=True,
        ) as pbar:
            pbar.set_postfix({"Encoded videos finished": "0 : 0%"})
            # Wait and iterate over completed Futures
            for task in cf.as_completed(my_ffs):
                # Dict containing the "enc" and "model" keys
                out = my_ffs[task]
                enc = out["enc"]

                io[enc]["status"] = "DONE"

                # Contains the actual stdout and stderr of the ffmpy call
                # In our case we only need the stderr
                err = task.result()[1]

                # Prepare the output message for this enc-model combination
                # msg = "\tVMAF Model: {}\n".format(model)
                log_path = str(Path(io[enc]["log_path"]))
                msg = "\tLog Location: {}\n".format(log_path.replace("\\:", ":").replace('"', "/"))

                # Look for the average VMAF score given in the stderr
                for line in err.decode("utf-8").split("\n"):
                    if "VMAF score" in line:
                        vmaf_score = float(line.split("]")[1].split(": ")[1].strip())
                        # Set the score for this enc-model combination
                        io[enc]["score"] = vmaf_score
                        # Add this score to the overall score of the enc video
                        # file between all models
                        aggregate[enc]["score"] += vmaf_score
                        msg += "\tVMAF Score: {}\n\n".format(vmaf_score)
                        break

                # Save the enc-model output message for later
                io[enc]["msg"] = msg

                # Since we just finished using a model on this specific enc
                # video file, we increment the counter for the number of models
                # completed for this enc file
                # If we've finished testing all models against this enc, then
                # we can save the aggregate statistics and move the video file
                # to the log location
                enc_finished += 1
                pbar.set_postfix(
                    {"Encoded videos finished": str("{} : {}%".format(enc_finished, enc_finished / io.keys() * 100))}
                )
                # Move the enc video file to the log location
                enc_path = Path(enc)
                enc_path_new = aggregate[enc]["log"].parent.joinpath(enc_path.name)
                enc_path.replace(enc_path_new)

                # Get the average VMAF score between all model files
                aggregate[enc]["score"] /= len(io[enc].keys())

                # Save score to aggregate enc's output message
                tmp_msg = "Average VMAF Score between all tested VMAF models is {}\n"
                aggregate[enc]["msg"] = tmp_msg.format(aggregate[enc]["score"])

                # Open the aggregate statistics file for writing to
                with open(aggregate[enc]["log"], "w") as aggregate_file:
                    for model in models.keys():
                        # Write the average score for each model to the
                        # aggregate log file
                        tmp_msg = "{} Score: {}\n"
                        aggregate_file.write(tmp_msg.format(model, io[enc][model]["score"]))

                    # Write average VMAF score to aggregate log file
                    tmp_msg = "\nAverage Score: {}\n"
                    aggregate_file.write(tmp_msg.format(aggregate[enc]["score"]))

                    # Convert file size to a more human-readable format
                    size_converted = bytes2human(aggregate[enc]["file_size"])

                    # Write the size in bytes & the size in human-readable
                    # format to the aggregate log file
                    tmp_msg = "File Size: {}B = {}\n"
                    aggregate_file.write(tmp_msg.format(aggregate[enc]["file_size"], size_converted))

                for model in models.keys():
                    io[enc][model]["status"] = "MOVED"
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
                enc = info["enc"]
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
                        if io[enc][model]["status"] not in ["DONE", "MOVED"]:
                            time.sleep(0.5)
                            print("\tDeleting related log file:\n\t{}...".format(Path(io[enc][model]["log_path"])))
                            Path(io[enc][model]["log_path"]).unlink(missing_ok=True)
                        cancellations[task] = True
                    if io[enc][model]["status"] not in ["DONE", "MOVED"]:
                        io[enc][model]["status"] = "CANCELLED"
        del cancellations
        print("Pool has shutdown, exiting...")
    else:
        cf_handler.shutdown()

    write_state(args.Reference, io)
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
    print("Reference: {}".format(args.Reference))
    for enc, models in io.items():
        print("Encoded: {}".format(enc))
        print(aggregate[enc]["msg"])
        for model in models.keys():
            print(io[enc][model]["msg"])


if __name__ == "__main__":
    main()
