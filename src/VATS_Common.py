import json
import sys
from pathlib import Path
from typing import Any, Union

from VATS_MainWindow import MainWindow


def write_message(msg: str, window: Union[MainWindow, None] = None):
    """Handles writing messages to either the terminal
    in CLI mode or writing them to th output log box in GUI mode.

    Args:
        msg (str): String message to write out
        nogui (bool): Whether or not to run in CLI mode
        window (MainWindow): The GUI window
    """
    if window is None:
        print(msg)
    else:
        window.write_output(msg)


def os_check():
    """Check what OS is being used on this system"""
    cur_os = None
    if sys.platform == "linux":
        cur_os = "Linux"
    elif sys.platform == "win32":
        cur_os = "Windows"
    elif sys.platform == "darwin":
        cur_os = "MacOS"
    else:
        write_message("OS not supported, exiting...")
        sys.exit(1)
    return cur_os


def write_state(
    completions_file: Union[str, Path],
    completions: dict,
):
    with open(str(completions_file), "w") as writer:
        json.dump(
            completions,
            writer,
            indent=4,
            sort_keys=True,
        )


def validate_input(inp: Any):
    msg = input(inp)
    while msg == "":
        msg = input(inp)
    if msg.lower() in ("y", "yes"):
        return True
    return False
