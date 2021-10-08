# TODO
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
- [ ] Take any important old code from `vmaf_calculator_old.py` and put it in `vmaf_calculator.py` or related files. (Priority: Medium)
    - Includes:
        - Checking if FFMPEG is working through ffmpy module
        - Reading/writing the config file.
- [ ] Create priority queue for calculations, prioritizing finishing all models for a single distorted file first before moving on to another distorted file. (Priority: Low)
    - Might not be necessary
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)

## Plotter
- [ ] Grab all reports from folders ending in "_results" and use that as the name for the aggregate file.
    - Use this file to aggregate data by listing the (mean, median, std, % lows) for each model used on the distorted file (IE: distortedname_model_vmaf_mean) (Priority: High)
- [ ] Aggregate data for each distorted file. Rank each metric for each model in one sheet, and rank the average score for each metric between all models in another sheet (Priority: Medium)
- [ ] Add stats for (Priority: Medium):
    - [ ] Unbiased Variance (pandas.DataFrame.var)
    - [ ] Standard Error of Mean (pandas.DataFrame.sem)
    - [ ] Mean Absolute Deviation (pandas.DataFrame.mad)
    - [ ] Percent Change between data points (pandas.DataFrame.pct_change)
    - [ ] Exponential Weighted X (older values are less important as newer data is introduced) (pandas.DataFrame.ewm)
        - [ ] EW Mean
        - [ ] EW Median
        - [ ] EW Standard Deviation
        - [ ] EW Correlation
        - [ ] EW Covariance
    - [ ] Kurtosis (pandas.DataFrame.kurt)
- [ ] Move from using `numpy` to only `pandas` if possible. (Priority: Medium)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)

## Encoder
- [ ] Define if this is necessary - should the program take already encoded files, or should it encode AND calculate VMAF at the same time? (Priority: High)
- [ ] Create an async encoder app for all combinations specified in a config (Priority: Low)
- [ ] Only encode videos that have no finished encoding (would require some form of state saving to know if a calculation was actually completed and NOT cancelled) (Priority: Low)
- [ ] Utilize logging. (Priority: Medium)
- [ ] Utilize `amped` module. (Priority: Medium)