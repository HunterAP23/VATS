# Plot_Vmaf
This script is a combination of forking
[master-of-zen/Plot_Vmaf](https://github.com/master-of-zen/Plot_Vmaf) and
combining it with the live motion graphing from my own repository
[HunterAP23/GameBench_Graph_Maker](https://github.com/HunterAP23/GameBench_Graph_Maker).

This will generate a single image to show the VMAF values for the inputted VMAF
file overall, and generate a video file that is animated to move through the
graph, both at the same framerate (as reported by the source VMAF report) and
has a transparent background.
![](plot.svg)

## Usage
```bash
python plot_vmaf.py [-h] [-o OUTPUT] vmaf_file
```

## Example
```bash
python plot_vmaf.py vmaf.xml -o plot.svg
```

## Options
```
usage: plot_vmaf.py [-h] [-o OUTPUT] [-l {default,min,zero,custom}]
                    [-c CUSTOM] [-r {720p,1080p,1440p,4k}] [-d DPI]
                    VMAF_FILE

Plot VMAF to graph, save it as both a static image and as a transparent animated video file.

positional arguments:
  VMAF_FILE             VMAF report file.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output filename (Default: vmaf.png).
                        Also defines the name of the output graph (Default: vmaf.mov).
  -l {default,min,zero,custom}, --lower-boundary {default,min,zero,custom}
                        Choose what the lowest value of the graph will be.
                        * "default" uses the lowest VMAF value minus 5  as the lowest point of the y-axis so the values aren't so stretched vertically.
                        * "min" will use whatever the lowest VMAF value is as the lowest point of the y-axis. Makes the data look a bit stretched vertically.
                        * "zero" will explicitly use 0 as the lowest point on the y-axis. Makes the data look a bit compressed vertically.
                        * "custom" will use the value entered by the user in the "-c" / "--custom" option.
  -c CUSTOM, --custom CUSTOM
                        Enter custom minimum point for y-axis. Requires "-l" / "--lower-boundary" set to "custom" to work.
                        This option expects an integer value.
  -r {720p,1080p,1440p,4k}, --resolution {720p,1080p,1440p,4k}
                        Choose the resolution for the graph video (Default is 1080p).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
  -d DPI, --dpi DPI     Choose the DPI for the graph image and video (Default is 100).
                        Note that higher values will mean drastically larger files and take substantially longer to encode.
                        This setting applies only to the video file, not the image file.
```

## Requirements
Python 3
Matplotlib
Numpy

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
Higher resolutions don't necessarily mean a higher quality image, it just makes it easier to scale to your photo or video editor's timeline resolution.
Higher resolutions don't really take any more time encode the photo or video graph for, and help prevent any quality loss from scaling in any form of photo or video editor.

The default DPI for the image is 800, which takes almost no time to render and save, and thus is not user-configurable at run-time.
The default DPI value for the video is 100, as going higher means that the video will take exponentially longer to encode.
In this case, video DPI is related to the bitrate that the video will have, leading to the axes and graph lines looking much better and less aliased.
For example, using an AMD Ryzen 3700X, these were my encoding times for a 521 frame some resolutions and DPI values:
Resolution | DPI | Encode Time
720p | 100 | 0H : 0M : 9.81S
720p | 300 | 0H : 1M : 21.53S
720p | 800 | 0H : 12M : 55.02S
1080p | 100 | 0H : 0M : 10.34S
1080p | 300 | 0H : 1M : 22.09S
1080p | 800 | 0H : 12M : 54.17S
1440p | 100 | 0H : 0M : 11.66S
1440p | 300 | 0H : 1M : 22.71S
1440p | 800 | 0H : 13M : 23.91S
