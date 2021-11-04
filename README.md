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
Please look at the (TODO.md)[TODO.md] file for the current status of the
project and what tasks are left to be done.

## CONTRIBUTING
Please read the (CONTRIBUTING.md)[CONTRIBUTING.md] file to see how to set up
your development environment.

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

### Advanced Setup
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
usage: VMAF Calculator -r REFERENCE [-d [DISTORTED ...]] [-f FFMPEG] [-t THREADS] [-p PROCESSES] [-c] [--psnr]
                       [--ssim] [--ms-ssim] [--subsamples SUBSAMPLES] [-m [MODEL ...]] [-l {xml,csv,json}] [--hwaccel]
                       [-h] [-v]
```

### Options
```

Multithreaded VMAF log file generator through FFmpeg.

optional arguments:
  -r REFERENCE, --reference REFERENCE
                        Reference video file().
                        The program expects a single "reference" file.

  -d [DISTORTED ...], --distorted [DISTORTED ...]
                        Distorted video file().
                        Specifying a single "distorted" file will only run a single VMAF calculation instance between it and the "reference" file.
                        Specifying multiple "distorted" files will compare the "reference" file against all the "distorted" files.
                        Specifying a directory for the "distorted" argument will scan the diretory for any MP4 and MKV files to compare against the "reference" file.
                        You can provide any combination of files and directories.


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

  -c, --continue        Specify whether or not to look for a save state file for the given reference video file (Default is True).

  --psnr                Enable calculating PSNR values (Default is off).

  --ssim                Enable calculating SSIM values (Default is off).

  --ms-ssim, --ms_ssim  Enable calculating MS-SSIM values (Default is off).

  --subsamples SUBSAMPLES
                        Specify the number of subsamples to use (default 1).
                        This value only samples the VMAF and related metrics' values once every N frames.
                        Higher values may improve calculation performance at the cost of less accurate results.

                        This variable corresponds to VMAF's "n_subsample" variable.

  -m [MODEL ...], --model [MODEL ...]
                        Specify the VMAF model files to use. This argument expects a list of model files to use.
                        The program will calculate the VMAF scores for every distorted file, for every model given.
                        Note that VMAF models come in JSON format, and the program will only accept those models.

  -l {xml,csv,json}, --log-format {xml,csv,json}
                        Specify the VMAF log file format (Default is "xml").

  --hwaccel             Enable FFmpeg to automatically attempt to use hardware acceleration for video decoding (default is off).
                        Not specifying this option means FFmpeg will use only the CPU for video decoding.
                        Enabling this option means FFmpeg will use attempt to use the GPU for video decoding instead.
                        This could improve calculation speed, but your mileage may vary.


Miscellaneous arguments:
  -h, --help            Show this help message and exit.
  -v, --version         show program's version number and exit
```

## VMAF Plotter
This will generate a single image to show the VMAF values for the inputted VMAF
file overall, and generate a video file that is animated to move through the
graph, both at the same framerate (as reported by the source VMAF report) and
has a transparent background.
![](graph_examples/plot_720p_default.svg)

### Usage
```
usage: VMAF Plotter [-c CONFIG] [-o OUTPUT] [-t [{image,video,stats,agg,all} ...]]
                    [-dp [{vmaf,psnr,ssim,ms_ssim,all} ...]] [-r {720,1080,1440,4k}] [-f FPS] [-h] [-v]
                    [VMAF ...]
```

### Options
```
Plot VMAF to graph, save it as both a static image and as a transparent animated video file.
All of the following arguments have default values within the config file.
Arguments will override the values for the variables set in the config file when specified.
Settings that are not specified in the config file will use default values as deemed by the program.

positional arguments:
  VMAF                  Directories containing subdirectories, which should contain the VMAF report files and distorted video files.
                        The program will scan for inside the provided directories for subdirectories ending with "_results".
                        The subdirectories are expected to contain reports in CSV, JSON, and XML format that end with "_statistics" and be alongside the distorted video files.


Optional arguments:
  -c CONFIG, --config CONFIG
                        Config file (defualt: config.ini).
  -o OUTPUT, --output OUTPUT
                        Output files location, also defines the name of the output graph.
                        Not specifying an output directory will write the output data to the same directory as the inputs, for each input given.
                        Specifying a directory will save the output data of all inputs to that location.

  -t [{image,video,stats,agg,all} ...], --output_types [{image,video,stats,agg,all} ...], --output-types [{image,video,stats,agg,all} ...]
                        Choose whether to output a graph image, graph video, stats, or all three (Default: all).
                        The options are separated by a space if you want to specify only one or two of the choices.
                        - "image" will only output the image graph.
                        - "video" will only output the video graph.
                        - "stats" will only print out the statistics to the console and to a file.

                        - "all" will output the image and video graphs.
  -dp [{vmaf,psnr,ssim,ms_ssim,all} ...], --datapoints [{vmaf,psnr,ssim,ms_ssim,all} ...]
                        Choose which data points to show on the graphs and statistics outputs (Default: all).
                        The options are separated by a space if you want to specify only one or more.
                        - "vmaf" will only graph the VMAF scores.
                        - "psnr" will only graph the PSNR scores.
                        - "ssim" will only graph the SSIM scores.
                        - "ms_ssim" will only graph the MS-SSIM scores.
                        - "all" will graph the all of the above scores.

  -r {720,1080,1440,4k}, --resolution {720,1080,1440,4k}
                        Choose the resolution for the graph video (Default is 1080).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
                        This option is ignored when using option "-t" / "--output_types" with "none" value.

  -f FPS, --fps FPS     Specify the FPS for the video file (Default is 60).

Miscellaneous arguments:
  -h, --help            Show this help message and exit.
  -v, --version         show program's version number and exit
```


### Quality & Performance Considerations
The default resolution for the graph image and video is 1080p.
As expected, generating higher resolution images and videos will take much
longer.