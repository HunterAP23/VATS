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
                    [-c CUSTOM] [-r {720p,1080p,1440p,4k}]
                    VMAF_FILE

Plot VMAF to graph, save it as both a static image and as a transparent animated video file.

positional arguments:
  VMAF_FILE             VMAF report file.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output filename (default: vmaf.png).
                        Also defines the name of the output graph (default: vmaf.mov).
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
                        Choose the resolution for the graph image and video. Note that higher values will mean drastically larger files.
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
