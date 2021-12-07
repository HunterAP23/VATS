# TODO
## General
- [ ] Convert config files to `toml` format. (Priority: High)
    - [x] Convert config file to `toml`.
    - [ ] Convert parsing to handle the new `toml` format.

## Calculator
- [x] Handle only running calculations that have not already completed. (Priority: High)
    - Solved by doing the following:
        - Adding a "status" key for every distorted video file + model key combo in the `io` variable. Statuses include:
            - "NOT STARTED": calculation has not been started.
            - "STARTED": calculation has started and would need to be forcibly exited to stop.
            - "DONE": calculation has been completed.
            - "MOVED": calculation for every model for the given distorted video file have all been completed, and the distorted video file has been moved.
                - Does this need to be done anymore?
            - "CANCELLED": calculation was cancelled and stopped successfully.
        - Saving that information to a JSON file named after and stored next to the reference video file.
        - On program launch, check for the existing JSON file and read in the status for each distorted video file + model combo.
        - The program would then only run calculations for distorted video file + model combos that were not listed explicitly as "DONE".
- [x] Handle closing out FFMPEG processes by force. (Priority: High)
    - Solved by doing the following:
        - After developing a method for the save state, changes were made to catch exceptions while waiting for tasks to complete.
        - On exception, the program will shutdown the ThreadPoolExecutor to prevent any more tasks from running.
        - Any tasks in "running" state are forcibly cancelled, and their respective FFMPEG subprocess.Popen is forcibly terminated.
        - The status of any incomplete calculations is set to "CANCELLED" and the state of the program is saved to the JSON file.
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Add checks for FFmpeg executable (Priority: Medium):
    - [ ] If FFmpeg executable is not given, make check to see if it is in the environment path variable.
    - [ ] Add check to see that VMAF version 2 is an available filter inside FFmpeg
- [ ] Take any important old code from `vmaf_calculator_old.py` and put it in `vmaf_calculator.py` or related files. (Priority: Medium)
    - Includes:
        - Checking if FFMPEG is working through ffmpy module
        - Reading/writing the config file.
- [ ] Create priority queue for calculations, prioritizing finishing all models for a single distorted file first before moving on to another distorted file. (Priority: Low)
    - Might not be necessary
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)

## Plotter
- [x] Grab all reports from folders ending in "_results" and use that as the
    name for the aggregate file.
    - Use this file to aggregate data by listing the metrics for each model
    used on the distorted file (IE: distortedname_model_vmaf_mean)
    (Priority: High)
    - RESULT: Actual implementation involved getting VMAF reports using any of
    the possible VMAF report extensions (csv, json, and xml), then removing the
    model name from the file name.
- [x] Aggregate data for each distorted file. Rank each metric for each model
      in one sheet, and rank the average score for each metric between all
      models in another sheet (Priority: Medium)
- [x] Add Mean Absolute Deviation (pandas.DataFrame.mad) (Priority: Medium)
    - Also added the following:
        - Median Absolute Deviation
        - 99th Percentile
        - 95th Percentile
        - 90th Percentile
        - 99th Quantile Absolute Deviation
        - 95th Quantile Absolute Deviation
        - 90th Quantile Absolute Deviation
        - 75th Quantile Absolute Deviation
        - 25th Quantile Absolute Deviation
        - 1st Quantile Absolute Deviation
        - 0.1st Quantile Absolute Deviation
        - 0.01st Quantile Absolute Deviation
- [x] Move from using `numpy` to only `pandas` if possible. (Priority: Medium)
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Move from using `matplotlib` to `pandas` for images. (Priority: Medium)
- [ ] Add functionality for graphing all the data points together on one
    graph using data normalization. (Priority: Medium)
    - 
- [ ] Add functionality for finding the distorted videos files in the existing
    file structure.
    - [ ] Use the distorted file's size to compare to the original file's size
    - [ ] Use the file size as a metric of quality compared to the file size,
        bitrate, and VMAF metrics
        - Divide the file size and bitrate by each individual metric's score,
        such as file size / median VMAF score or bitrate / mean PSNR score
        - There can be ties in the VMAF metric scores, and using the file can
        help determine a more clear winner
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)

## Encoder
- [x] Define if this is necessary - should the program take already encoded files, or should it encode AND calculate VMAF at the same time? (Priority: High)
    - The program will only encode files, not calculate VMAF for them. This is so we can measure the file size and encode times for comparison between all the files.
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Create an async encoder app for all combinations specified in a config (Priority: Low)
- [ ] Only encode videos that have no finished encoding (would require some form of state saving to know if a calculation was actually completed and NOT cancelled) (Priority: Low)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)