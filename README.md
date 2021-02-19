# VMAF-Over-Time
This script is a combination of forking
[master-of-zen/Plot_Vmaf](https://github.com/master-of-zen/Plot_Vmaf) and
combining it with the live motion graphing from my own repository
[HunterAP23/GameBench_Graph_Maker](https://github.com/HunterAP23/GameBench_Graph_Maker).

Status (02/19/2021): INCOMPLETE - Does not currently work

There are two parts to this project:
1. Calculating VMAF through the use of the FFmpeg program with the ability to run
multiple instances at once to max out the speed of the calculations. VMAF scales
with threads up to a certain point, and this part of the script can help
2. Generate image and video graphs of the different VMAF related metrics. The
metrics include PSNR, SSIM, SSIM, and others that VMAF normally generates. The
video file is a live playback of the values to be used in situations like
benchmark videos.

# VMAF Calculator
Using FFmpeg, the script calculates the VMAF score as well as related metrics
like PSNR, SSIM, and MS_SSIM. It also attempts to utilize multithreading where
available, with the main focus being able to run multiple VMAF calculations
simultaneously to maximize the speed of all calculations.

## Usage

# VMAF Plotter
This will generate a single image to show the VMAF values for the inputted VMAF
file overall, and generate a video file that is animated to move through the
graph, both at the same framerate (as reported by the source VMAF report) and
has a transparent background.
![](graph_examples/plot_720p_default.svg)

## Usage
```bash
usage: vmaf_plotter.py [-o OUTPUT] [-l {default,min,zero,custom}] [-c CUSTOM] [-r {720,1080,1440,4k}] [-d DPI] [-v {1,2}] [-f FPS] [-h] VMAF_FILE
```

## Example
This creates an image and video with 1440p resolution, 24fps, and the y-axis range is 0 to 100.
```bash
python plot_vmaf.py vmaf.xml -o plot.svg -r 1440p -f 24 -l zero
```

## Options
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
                        - "default" uses the lowest VMAF value minus 5 as the lowest point of the y-axis so the values aren't so stretched vertically.
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

## Requirements
Python 3
Matplotlib
Numpy
FFMpeg

Install them with either of the following commands:
```
pip install -r requirements.txt
```
OR
```
python -m pip install -r requirements.txt
```


# Quality & Performance Considerations
The default resolution for the graph image and video is 1080p.
For the image, resolution is the only factor in the file's quality. DPI has no effect on the image file.

For the video, resolution and DPI are multiplied to get the final output resolution of the video.
100 DPI is equivalent to a 1x scale on the resolution, and 200 DPI is a 2x scale.
This does not mean that picking a DPI for a 720p video will make it look the same as a 1080p video with 100 DPI.
The lines, axes, and graph labels will all be scaled differently depending on the resolution.


For example, using an AMD Ryzen 3700X, these were my encoding times for a 521 frame some resolutions and DPI values:
Resolution | DPI | Effective Video Resolution | Encode Time
720p | 100 | 1280x720 | 0H : 0M : 6.63S
720p | 300 | 3840x2160p | 0H : 0M : 36.16S
720p | 800 | 10240x5760 | 0H : 5M : 11.06S
1080p | 100 | 1920x1080 | 0H : 0M : 11.16S
1080p | 300 | 5760x3240 | 0H : 1M : 23.76S
1080p | 800 | 15360x8640 | 0H : 15M : 6.67S
