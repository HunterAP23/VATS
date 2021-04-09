# VMAF-Over-Time
This script is a combination of forking
[master-of-zen/Plot_Vmaf](https://github.com/master-of-zen/Plot_Vmaf) and
combining it with the live motion graphing from my own repository
[HunterAP23/GameBench_Graph_Maker](https://github.com/HunterAP23/GameBench_Graph_Maker).

## Summary
There are two parts to this project:
1. Calculating VMAF through the use of the FFmpeg program with the ability to run
multiple instances at once to max out the speed of the calculations. VMAF scales
with threads up to a certain point, and this part of the script can help
2. Generate image and video graphs of the different VMAF related metrics. The
metrics include PSNR, SSIM, SSIM, and others that VMAF normally generates. The
video file is a live playback of the values to be used in situations like
benchmark videos.

## TODO
Please look at the (TODO.md)[https://github.com/HunterAP23/VMAF-Over-Time/blob/master/TODO.md] file for the current status of the
project and what tasks are left to be done.

## Requirements
Python 3.8 or newer<br>
FFmpeg

### Normal Setup
Install them with either of the following commands:
```
pip install -r requirements.txt
```
OR
```
python -m pip install -r requirements.txt
```

### Advanced Preferred Setup
If you instead want to keep your global python packages tidy, you can use the
`pipenv` python package.
1. Install `pipenv` with:
```
pip install pipenv
```
OR
```
python -m pip install pipenv
```
2. Create a virtual environment and install the required packages to it.
```
pipenv update
```
3. Before running any of the programs, you'll have to enter the pipenv
environment like so:
```
pipenv shell
```
Then you can run the commands for the programs in this project.

Alternatively, you can run the programs directly without entering the pipenv
environment. For example, if you wanted to get the help info for the VMAF
Calculator program, you can do so like this:
```
pipenv run python vmaf_calculator.py -h
```

# VMAF Calculator
Using FFmpeg, the script calculates the VMAF score as well as related metrics
like PSNR, SSIM, and MS_SSIM. It also attempts to utilize multithreading where
available, with the main focus being able to run multiple VMAF calculations
simultaneously to maximize the speed of all calculations.

### Usage
```
usage: vmaf_calculator.py [-f FFMPEG] [-t THREADS] [-p PROCESSES] [-u] [-v {1,2}] [--psnr] [--ssim] [--ms-ssim] [--subsamples SUBSAMPLES] [-m MODEL] [-l {xml,csv,json}] [-n LOG_PATH] [-c CONFIG] [-h] distorted reference

Multithreaded VMAF log file generator through FFmpeg.
```

### Options
```
The 1st required argument is the Distorted Video file.
The 2nd required argument is the Reference Video file that the Distorted Video is compared against.

positional arguments:
  distorted             distorted video file.
  reference             reference video file.

Optional arguments:
  -f FFMPEG, --ffmpeg FFMPEG
                        Specify the path to the FFmpeg executable (Default is "ffmpeg" which assumes that FFmpeg is part of your "Path" environment variable).
                        The path must either point to the executable itself, or to the directory that contains the executable named "ffmpeg".

  -t THREADS, --threads THREADS
                        Specify number of threads to be used for each process (Default is 0 for "autodetect").
                        Specifying more threads than there are available will clamp the value down to 1 thread for safety purposes.
                        A single VMAF process will effectively max out at 12 threads - any more will provide little to no performance increase.
                        The recommended value of threads to use per process is 4-6.

  -p PROCESSES, --processes PROCESSES
                        Specify number of simultaneous VMAF calculation processes to run (Default is 1).
                        Specifying more processes than there are available CPU threads will clamp the value down to the maximum number of threads on the system for a total of 1 thread per process.

  -u, --use-rem-threads
                        Specify whether or not to use remaining threads that don't make a complete process to use for an process (Default is off).
                        For example, if your system has 16 threads, and you are running 5 processes with 3 threads each, then you will be using 4 * 3 threads, which is 12.
                        This means you will have 1 thread that will remain unused.
                        Using this option would run one more VMAF calculation process with only the single remaining thread.
                        This option is not recommended, as the unused threads will be used to keep the system responsive during the VMAF calculations.

  -v {1,2}, --vmaf-version {1,2}
                        Specify the VMAF version to use (Default is 2).

  --psnr                Enable calculating PSNR values (Default is off).

  --ssim                Enable calculating SSIM values (Default is off).

  --ms-ssim             Enable calculating MS-SSIM values (Default is off).

  --subsamples SUBSAMPLES
                        Specify the number of subsamples to use (default 1).
                        This value only samples the VMAF and related metrics' values once every N frames.
                        Higher values may improve calculation performance at the cost of less accurate results.

                        This variable corresponds to VMAF's "n_subsample" variable.

  -m MODEL, --model MODEL
                        Specify the VMAF model file to use (Default is "vmaf_v0.6.1.pkl" for VMAF version 1 and "vmaf_v0.6.1.json" for VMAF version 2).
                        By default, this variable assumes the model file is located in the same location as this script.

  -l {xml,csv,json}, --log-format {xml,csv,json}
                        Specify the VMAF log file format (Default is "xml").

  -n LOG_PATH, --log-name LOG_PATH
                        Specify the VMAF log path and file name (Default is "vmaf").

  -c CONFIG, --config CONFIG
                        Specify a config file to import multiple settings with (Default is "config.ini" in the same folder as the script).
                        Values specified with the arguments above will override the settings in the config file.

Miscellaneous arguments:
  -h, --help            Show this help message and exit.
```

### Examples


## VMAF Plotter
This will generate a single image to show the VMAF values for the inputted VMAF
file overall, and generate a video file that is animated to move through the
graph, both at the same framerate (as reported by the source VMAF report) and
has a transparent background.
![](graph_examples/plot_720p_default.svg)

### Usage
```
usage: vmaf_plotter.py [-o OUTPUT] [-l {default,min,zero,custom}] [-c CUSTOM] [-r {720,1080,1440,4k}] [-d DPI] [-v {1,2}] [-f FPS] [-h] VMAF_FILE
```

### Example
This creates an image and video with 1440p resolution, 24fps, and the y-axis range is 0 to 100.
```bash
python plot_vmaf.py vmaf.xml -o plot.svg -r 1440p -f 24 -l zero
```

### Options
```
positional arguments:
  VMAF_FILE             VMAF report file.

Optional arguments:
  -o OUTPUT, --output OUTPUT
                        Output filename (Default: vmaf.png).
                        Also defines the name of the output graph (Default: vmaf.mov).
                        Specifying a path will save the output image and video to that location.
                        If no path is given, then the files are saved to this project folder.
  -l {default,min,zero,custom}, --lower-boundary {default,min,zero,custom}
                        Choose what the lowest value of the graph will be.
                        - "default" uses the lowest VMAF value minus 5 as the lowest point of the y-axis so the values are not so stretched vertically.
                        - "min" will use whatever the lowest VMAF value is as the lowest point of the y-axis. May make the data look a bit stretched vertically.
                        - "zero" will explicitly use 0 as the lowest point on the y-axis. May make the data look a bit compressed vertically.
                        - "custom" will use the value entered by the user in the "-c" / "--custom" option.
  -c CUSTOM, --custom CUSTOM
                        Enter custom minimum point for y-axis. Requires "-l" / "--lower-boundary" set to "custom" to work.
                        This option expects an integer value.
  -r {720,1080,1440,4k}, --resolution {720,1080,1440,4k}
                        Choose the resolution for the graph video (Default is 1080).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
  -d DPI, --dpi DPI     Choose the DPI for the graph image and video (Default is 100).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
                        This setting applies only to the video file, not the image file.
  -v {1,2}, --version {1,2}
                        Choose which VMAF version was used when generating the report file (Default is autodetect).
                        Note that the VMAF version can not be autodetected when using CSV files, so if you're using a CSV VMAF v1 report please specify this option as "1".
                        Also note that when using version 2, an FPS value should be specified for the video, the default FPS is 60.
  -f FPS, --fps FPS     Specify the FPS for the video file (Default is 60).
                        Note that for VMAF version 2 (which is the default) this value should be specified manually, otherwise the default value of 60fps will be used.

Miscellaneous arguments:
  -h, --help            Show this help message and exit.
```


### Quality & Performance Considerations
The default resolution for the graph image and video is 1080p.
For the image, resolution is the only factor in the file's quality. DPI has no effect on the image file.

For the video, resolution and DPI are multiplied to get the final output resolution of the video.
100 DPI is equivalent to a 1x scale on the resolution, and 200 DPI is a 2x scale.
This does not mean that picking a DPI for a 720p video will make it look the same as a 1080p video with 100 DPI.
The lines, axes, and graph labels will all be scaled differently depending on the resolution.


For example, using an AMD Ryzen 3700X, these were my encoding times for a 521
frame video with different resolutions and DPI values:
Resolution | DPI | Effective Video Resolution | Encode Time
720p | 100 | 1280x720 | 0H : 0M : 6.63S
720p | 300 | 3840x2160p | 0H : 0M : 36.16S
720p | 800 | 10240x5760 | 0H : 5M : 11.06S
1080p | 100 | 1920x1080 | 0H : 0M : 11.16S
1080p | 300 | 5760x3240 | 0H : 1M : 23.76S
1080p | 800 | 15360x8640 | 0H : 15M : 6.67S
