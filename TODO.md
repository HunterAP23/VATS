# TODO
## General
- [ ] Convert config files to `toml` format. (Priority: High)
    - [x] Convert config file to `toml`.
    - [ ] Convert parsing to handle the new `toml` format.
- [ ] Move from `pipenv` package manager to `poetry` (Priority: High)
    - Reasoning is that `poetry` supports setting a minimum Python version, while `pipenv` does not.
- [ ] Package app into single executable for each operating system
    - [ ] Create central app with GUI
        - [ ] Should contain three tabs:
            - [ ] Encoder
            - [ ] Calculator
            - [ ] Plotter
        - [ ] Provide same functionality as command line version
    - [ ] Compile code with Cython
    - [ ] Package code into single executable with Pyinstaller
    - [ ] Set up GitHub Actions for compile/build/release of application
    - [ ] Change file search functionality
        - Reference files should be stored in `reference` folder
        - Encoded files should be stored in `encoded` folder, where each `reference` file will have it's own subfolder
        - VMAF report files would be stored in `data` folder, which includes settings files
        - The `graphs` folder will hold any output graphs, which are separated into subfolders based on the original `reference` files' names
    - [ ] Add proper docstrings for all classes/functions
    - [ ] Update samples
        - [ ] Use new sample videos (includes source and encoded variants)
        - [ ] Create sample reports based on the new video samples
        - [ ] Create graphs based on generated sample reports
        - [ ] Display samples inside README


## Encoder
- [x] Define if this is necessary - should the program take already encoded files, or should it encode AND calculate VMAF at the same time? (Priority: High)
    - The program will only encode files, not calculate VMAF for them. This is so we can measure the file size and encode times for comparison between all the files.
- [ ] Create an async encoder app for all combinations specified in a config (Priority: High)
- [ ] Let user specify an encoder, and then dynamically generate GUI selectors for all the available options presented (Priority: Medium)
    - Requires running ffmpeg with options `-h encoder=X` and parsing that output BEFORE `gooey` initializes the display
    - Parsed options need to be split based on the option name, and the available values for each option
    - Parsed options need to have some for mof detecting whether their available settings are strings, integers, floats, or something else entirely
- [ ] Only encode videos that have no finished encoding (would require some form of state saving to know if a calculation was actually completed and NOT cancelled) (Priority: Low)
- [ ] Encoder should offer options for testing different combinations of options:
    - [ ] Scaled down videos. Would require upscaling the encoded videos back to the original resolution when doing VMAF calculations.
    - [ ] Different standard bitrates / quality settings. Twitch normally support up to 8 mbps, but the official documents state that the max rate is 6 mbps for video content. YouTube officially supports up to 51 mbps.
        - Streaming:
            - 51 mbps
            - 34 mbps
            - 20 mbps
            - 13 mbps
            - 8 mbps
            - 6 mbps
            - 4.5 mbps
            - 3 mbps
            - 2 mbps
        - Recording / Archiving:
            - h264 CRF / CQP 24
            - h264 CRF / CQP 22
            - h264 CRF / CQP 18
            - h264 CRF / CQP 14
            - h264 CRF / CQP 10
            - h265 CQP 24
            - h265 CQP 22
            - h265 CQP 18
            - h265 CQP 14
            - h265 CQP 10
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Lowest)

## Calculator
- [x] Handle only running calculations that have not already completed. (Priority: High)
    - Solved by doing the following:
        - Adding a "status" key for every encoded video file + model key combo in the `io` variable. Statuses include:
            - "NOT STARTED": calculation has not been started.
            - "STARTED": calculation has started and would need to be forcibly exited to stop.
            - "DONE": calculation has been completed.
            - "MOVED": calculation for every model for the given encoded video file have all been completed, and the encoded video file has been moved.
                - Does this need to be done anymore?
            - "CANCELLED": calculation was cancelled and stopped successfully.
        - Saving that information to a JSON file named after and stored next to the reference video file.
        - On program launch, check for the existing JSON file and read in the status for each encoded video file + model combo.
        - The program would then only run calculations for encoded video file + model combos that were not listed explicitly as "DONE".
- [x] Handle closing out FFMPEG processes by force. (Priority: High)
    - Solved by doing the following:
        - After developing a method for the save state, changes were made to catch exceptions while waiting for tasks to complete.
        - On exception, the program will shutdown the ThreadPoolExecutor to prevent any more tasks from running.
        - Any tasks in "running" state are forcibly cancelled, and their respective FFMPEG subprocess.Popen is forcibly terminated.
        - The status of any incomplete calculations is set to "CANCELLED" and the state of the program is saved to the JSON file.
- [ ] Add checks for FFmpeg executable (Priority: Medium):
    - [ ] If FFmpeg executable is not given, make check to see if it is in the environment path variable.
    - [ ] Add check to see that VMAF version 2 is an available filter inside FFmpeg
- [ ] Take any important old code from `vmaf_calculator_old.py` and put it in `vmaf_calculator.py` or related files. (Priority: Medium)
    - Includes:
        - Checking if FFMPEG is working through ffmpy module
        - Reading/writing the config file.
- [ ] Create priority queue for calculations, prioritizing finishing all models for a single encoded file first before moving on to another encoded file. (Priority: Low)
    - Might not be necessary
- [ ] Add metric for "how long does file take to get encoded" for each encoder.
    - Faster times mean less system load (be it CPU, GPU, RAM, VRAM, etc.)
    - Faster encoders attaining the same quality scores rank higher
- [ ] Add setting for not using file size as a comparison metric, such as when the encoding was targeting specific constant bit rates
- [ ] Scale/weigh score metrics
    - VMAF score
    - SSIM
    - MS-SSIM
    - Encode time
    - Output file size when not targeting specific bitrate)
- [ ] Convert encoded videos back to same color format / range / scale:
    - Convert [cmp] color to [ref] color.
    - Scale [cmp] size to [ref] size using bicubic scaling.
    - Fix up PTS to match between [cmp] and [ref].
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Lowest)

## Plotter
- [x] Grab all reports from folders ending in "_results" and use that as the
    name for the aggregate file.
    - Use this file to aggregate data by listing the metrics for each model
    used on the encoded file (IE: encodedname_model_vmaf_mean)
    (Priority: High)
    - RESULT: Actual implementation involved getting VMAF reports using any of
    the possible VMAF report extensions (csv, json, and xml), then removing the
    model name from the file name.
- [x] Aggregate data for each encoded file. Rank each metric for each model
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
- [ ] Add functionality for graphing all the data points together on one
    graph using data normalization. (Priority: Medium)
    - 
- [ ] Add functionality for finding the encoded videos files in the existing
    file structure.
    - [ ] Use the encoded file's size to compare to the original file's size
    - [ ] Use the file size as a metric of quality compared to the file size,
        bitrate, and VMAF metrics
        - Divide the file size and bitrate by each individual metric's score,
        such as file size / median VMAF score or bitrate / mean PSNR score
        - There can be ties in the VMAF metric scores, and using the file can
        help determine a more clear winner
- [ ] Migrate code from `argparse` to `gooey` (Priority: High)
- [ ] Move from using `matplotlib` to `pandas` for images. (Priority: Medium)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Lowest)