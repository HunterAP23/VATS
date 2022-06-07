from argparse import RawTextHelpFormatter
from datetime import timedelta
from fractions import Fraction
from json import dump, load
from pathlib import Path
from subprocess import PIPE
from time import time
from traceback import print_exc

import ffmpy
import PySimpleGUIQt as sg

from vmaf_common import bytes2human, search_handler


def create_window(theme):
    # sg.ChangeLookAndFeel(theme)
    sg.theme(theme)

    main_frame = None

    should_continue = (
        True
        if sg.PopupYesNo("Do you have a progress JSON file you want to use to pick up where you left off?") == "Yes"
        else False
    )

    should_clean = None
    progress_file = None
    if should_continue:
        progress_file = sg.PopupGetFile(
            # button_text="Select progress JSON file.",
            message="Select progress JSON file.",
            file_types=(
                ("JSON Files", "*.json"),
                ("ALL Files", "*"),
            ),
            initial_folder=str(Path(__file__).parent.parent),
            size=(200, 30),
        )
        print("Progress File: {}".format(progress_file))
        main_frame = [
            [sg.InputText("Progress File: {}".format(progress_file), disabled=True, size=(200, 85))],
        ]
    else:
        should_clean = (
            True
            if sg.PopupYesNo(
                'Do you want to delete any existing encoded videos? This will only delete videos located in the "encoded" directory.'
            )
            == "Yes"
            else False
        )
        if should_clean:
            for item in Path(__file__).parent.parent.joinpath("encoded").iterdir():
                print("Deleting {}".format(item))
                item.unlink()
            print("Finished deleting old encoded files.")

    frame2 = [
        [sg.InputText("test", disabled=True, size=(200, 85))],
    ]

    frame3 = [
        [sg.Checkbox("Checkbox1", True), sg.Checkbox("Checkbox1")],
        [sg.Radio("Radio Button1", 1), sg.Radio("Radio Button2", 1, default=True), sg.Stretch()],
    ]

    frame4 = [
        [
            sg.Slider(range=(0, 100), orientation="v", size=(3, 30), default_value=40),
            sg.Dial(range=(0, 100), tick_interval=50, size=(150, 150), default_value=40),
            sg.Stretch(),
        ],
    ]
    matrix = [[str(x * y) for x in range(4)] for y in range(3)]

    main_layout = []
    if main_frame:
        main_layout.append(
            sg.Frame("Main Group", main_frame, title_color="red", size=(300, 60)),
        )
    main_layout.append(sg.Frame("Second Group", frame2, title_color="green", size=(300, 60)))
    layout = [
        main_layout,
        [
            # sg.Frame("Multiple Choice Group", frame2, title_color="green"),
            # sg.Frame("Binary Choice Group", frame3, title_color="purple"),
            # sg.Frame("Variable Choice Group", frame4, title_color="blue"),
            sg.Stretch(),
        ],
    ]

    window = (
        sg.Window(
            "Window Title",
            font=("Calibri", 16),
            default_button_element_size=(100, 30),
            auto_size_buttons=True,
            size=(1280, 720),
        )
        .Layout(layout)
        .Finalize()
    )
    i = 0
    while True:  # Event Loop
        event, values = window.Read(timeout=0)
        if event is None or event == "Exit":
            break
        if event == "Button":
            print(event, values)

    window.Close()
    return

    reference_help += 'The program expects a single "reference" directory (Default: "reference").'

    encoded_help = "Encoded video file(s).\n"
    encoded_help += (
        'This should be a directory, which will be scanned for any video files to compare against the "reference" file.'
    )

    ffmpeg_help = "Specify the path to the FFmpeg executable.\n"
    ffmpeg_help = 'Default is "ffmpeg" which assumes that FFmpeg is part of your "Path" environment variable.\n'
    ffmpeg_help += 'The path must either point to the executable itself, or to the directory that contains the executable named "ffmpeg".'

    resolutions_help = "Choose from a list of known resolutions to downscale the encoded videos."

    hwaccel_help = "Enable FFmpeg to automatically attempt to use hardware acceleration for video decoding.\n"
    hwaccel_help += "Not specifying this option means FFmpeg will use only the CPU for video decoding.\n"
    hwaccel_help += (
        "Enabling this option means FFmpeg will use attempt to use the GPU for video decoding instead of the CPU.\n"
    )


if __name__ == "__main__":
    # window = create_window(sg.theme())

    create_window("black")

    # # This is an Event Loop
    # while True:
    #     event, values = window.read(timeout=100)
    #     # keep an animation running so show things are happening
    #     window["-GIF-IMAGE-"].update_animation(sg.DEFAULT_BASE64_LOADING_GIF, time_between_frames=100)
    #     if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
    #         print("============ Event = ", event, " ==============")
    #         print("-------- Values Dictionary (key=value) --------")
    #         for key in values:
    #             print(key, " = ", values[key])
    #     if event in (None, "Exit"):
    #         print("[LOG] Clicked Exit!")
    #         break
    #     elif event == "About":
    #         print("[LOG] Clicked About!")
    #         sg.popup(
    #             "PySimpleGUI Demo All Elements",
    #             "Right click anywhere to see right click menu",
    #             "Visit each of the tabs to see available elements",
    #             "Output of event and values can be see in Output tab",
    #             "The event and values dictionary is printed after every event",
    #             keep_on_top=True,
    #         )
    #     elif event == "Popup":
    #         print("[LOG] Clicked Popup Button!")
    #         sg.popup("You pressed a button!", keep_on_top=True)
    #         print("[LOG] Dismissing Popup!")
    #     elif event == "Test Progress bar":
    #         print("[LOG] Clicked Test Progress Bar!")
    #         progress_bar = window["-PROGRESS BAR-"]
    #         for i in range(100):
    #             print("[LOG] Updating progress bar by 1 step (" + str(i) + ")")
    #             progress_bar.update(current_count=i + 1)
    #         print("[LOG] Progress bar complete!")
    #     elif event == "-GRAPH-":
    #         graph = window["-GRAPH-"]  # type: sg.Graph
    #         graph.draw_circle(values["-GRAPH-"], fill_color="yellow", radius=20)
    #         print("[LOG] Circle drawn at: " + str(values["-GRAPH-"]))
    #     elif event == "Open Folder":
    #         print("[LOG] Clicked Open Folder!")
    #         folder_or_file = sg.popup_get_folder("Choose your folder", keep_on_top=True)
    #         sg.popup("You chose: " + str(folder_or_file), keep_on_top=True)
    #         print("[LOG] User chose folder: " + str(folder_or_file))
    #     elif event == "Open File":
    #         print("[LOG] Clicked Open File!")
    #         folder_or_file = sg.popup_get_file("Choose your file", keep_on_top=True)
    #         sg.popup("You chose: " + str(folder_or_file), keep_on_top=True)
    #         print("[LOG] User chose file: " + str(folder_or_file))
    #     elif event == "Set Theme":
    #         print("[LOG] Clicked Set Theme!")
    #         theme_chosen = values["-THEME LISTBOX-"][0]
    #         print("[LOG] User Chose Theme: " + str(theme_chosen))
    #         window.close()
    #         window = make_window(theme_chosen)
    #     elif event == "Edit Me":
    #         sg.execute_editor(__file__)
    #     elif event == "Versions":
    #         sg.popup(sg.get_versions(), keep_on_top=True)

    # window.close()
    # exit(0)
