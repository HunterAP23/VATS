import itertools

from VATS_Common import os_check, validate_input, write_message, write_state


def generate_encodings(settings, prompts):
    print("Generating encoding settings combinations...")
    encodings = {}
    for encoder in settings.keys():
        if prompts[encoder]:
            keys, values = zip(*settings[encoder].items())
            encodings[encoder] = dict()
            encodings[encoder]["Variations"] = [
                dict(zip(keys, v)) for v in itertools.product(*values)
            ]
            msg_success = ""
            msg_err = ""
            test = ""
            if encoder == "libx264":
                msg_success = "Software libx264 encoding supported."
                msg_err = "Software libx264 encoding is not supported on this system.\n\tThe FFmpeg build needs to have libx264 support built in."
                test = "-t 0.01 -pix_fmt nv12 -f null"
            elif encoder == "libx265":
                msg_success = "Software libx265 encoding supported."
                msg_err = "Software libx265 encoding is not supported on this system.\n\tThe FFmpeg build needs to have libx265 support built in."
                test = "-t 0.01 -pix_fmt nv12 -f null"
            elif encoder == "h264_nvenc":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = "Nvidia hardware H264 NVENC encoding supported."
                msg_err = "Nvidia H264 NVENC hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support h264_nvenc, or there was no Nvidia GPU's with H264 NVENC support detected."
            elif encoder == "hevc_nvenc":
                test = "-c:v hevc_nvenc -t 0.01 -pix_fmt nv12 -f null"
                msg_success = "Nvidia hardware HEVC NVENC encoding supported."
                msg_err = "Nvidia HEVC NVENC hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support hevc_nvenc, or there were no Nvidia GPU's with HEVC NVENC support detected."
            elif encoder == "h264_amf":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = "AMD hardware H264 AMF encoding supported."
                msg_err = "AMD H264 AMF hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support h264_amf, or there were no AMD GPU's with H264 AMF support detected."
            elif encoder == "hevc_amf":
                test = "-c:v hevc_amf -t 0.01 -pix_fmt nv12 -f null"
                msg_success = "AMD hardware HEVC AMF encoding supported."
                msg_err = "AMD HEVC AMF hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support hevc_amf, or there were no AMD GPU's with HEVC AMF support detected."
            elif encoder == "h264_qsv":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = (
                    "Intel hardware H264 QuickSync encoding supported."
                )
                msg_err = "Intel H264 QuickSync hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support h264_qsv, or there were no Intel GPU's with H264 QuickSync support detected."
            elif encoder == "hevc_qsv":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = (
                    "Intel hardware HEVC QuickSync encoding supported."
                )
                msg_err = "Intel HEVC QuickSync hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support hevc_qsv, or there were no Intel GPU's with HEVC QuickSync support detected."
            elif encoder == "h264_videotoolbox":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = (
                    "MacOS hardware H264 VideoToolbox encoding supported."
                )
                msg_err = "MacOS H264 VideoToolbox hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support h264_videotoolbox, or there were no MacOS GPU's or Media Engines with H264 VideoToolbox support detected."
            elif encoder == "hevc_videotoolbox":
                test = "-t 0.01 -pix_fmt nv12 -f null"
                msg_success = (
                    "MacOS hardware HEVC VideoToolbox encoding supported."
                )
                msg_err = "MacOS HEVC VideoToolbox hardware encoding is not supported on this system.\n\tEither the FFmpeg build you are using does not support hevc_videotoolbox, or there were no MacOS GPU's or Media Engines with HEVC VideoToolbox support detected."
            elif encoder == "libaom-av1":
                test = "-frame-parallel 1 -row-mt 1 -t 0.01 -pix_fmt yuv420p -f null"
                msg_success = "Software AOM AV1 encoding supported."
                msg_err = "Software AOM AV1 software encoding is not supported on this system.\n\tThe FFmpeg build needs to have libaom-av1 support built in."
            elif encoder == "libsvtav1":
                test = "-t 0.01 -pix_fmt yuv420p -f null"
                msg_success = "Software SVT AV1 encoding supported."
                msg_err = "Software SVT AV1 software encoding is not supported on this system.\n\tThe FFmpeg build needs to have libsvtav1 support built in."

            encodings[encoder]["Test"] = f"-c:v {encoder} {test}"
            encodings[encoder]["Success Message"] = msg_success
            encodings[encoder]["Error Message"] = msg_err

    for encoder, values in encodings.items():
        for k in values["Variations"]:
            if encoder in ["h264_nvenc", "hevc_nvenc"]:
                k["spatial_aq"] = k["Psycho-Visual Tuning"]
                k["temporal_aq"] = k["Psycho-Visual Tuning"]
                del k["Psycho-Visual Tuning"]

                if k["2pass"] == 0:
                    del k["multipass"]

            if encoder == "h264_qsv":
                if k["look_ahead"] == 0:
                    del k["look_ahead_depth"]
    print("Done.")
    return encodings


def encoder_selection():
    cur_os = os_check()
    encoder_settings = {
        "libx264": {
            "preset": (
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
            ),
            "rc-lookahead": (
                0,
                30,
                60,
                90,
                120,
            ),
            "trellis": (
                0,
                1,
            ),
        },
        "libx265": {
            "preset": (
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
            ),
            "x265-params rc-lookahead=": (
                30,
                60,
                90,
                120,
            ),
        },
        "h264_nvenc": {
            "preset": (
                "default",
                "slow",
                "medium",
                "fast",
                "hq",
                "p1",
                "p2",
                "p3",
                "p4",
                "p5",
                "p6",
                "p7",
            ),
            "rc-lookahead": (
                0,
                30,
                60,
                90,
                120,
            ),
            "tune": (
                "hq",
                "ll",
            ),
            "profile": ("high",),
            # OBS seems to have this on by default
            "b_adapt": (
                0,
                1,
            ),
            "Psycho-Visual Tuning": (
                0,
                1,
            ),
            "2pass": (
                0,
                1,
            ),
            "multipass": (
                "qres",
                "fullres",
            ),
        },
        "hevc_nvenc": {
            "preset": (
                "default",
                "slow",
                "medium",
                "fast",
                "hq",
                "p1",
                "p2",
                "p3",
                "p4",
                "p5",
                "p6",
                "p7",
            ),
            "rc-lookahead": (
                0,
                30,
                60,
                90,
                120,
            ),
            "tune": (
                "hq",
                "ll",
            ),
            "profile": ("main",),
            "Psycho-Visual Tuning": (
                0,
                1,
            ),
            "2pass": (
                0,
                1,
            ),
            "multipass": (
                "qres",
                "fullres",
            ),
        },
        "h264_amf": {
            "quality": (
                "speed",
                "quality",
                "balanced",
            ),
            # Seems look_ahead is always enabled unless look_ahead_depth = 0
            "rc": ("cbr",),
            # Same as OBS "Pre-Pass Mode"
            "preanalysis": (
                0,
                1,
            ),
            # Same as OBS "Filler Data"
            "filler_data": (
                0,
                1,
            ),
        },
        "hevc_amf": {
            "quality": (
                "speed",
                "quality",
                "balanced",
            ),
            # Only use CBR rate control
            "rc": ("cbr",),
            # Same as OBS "Pre-Pass Mode"
            "preanalysis": (
                0,
                1,
            ),
            # Same as OBS "Filler Data"
            "filler_data": (
                0,
                1,
            ),
        },
        "h264_qsv": {
            "preset": (
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
                "veryslow",
            ),
            # "maxrate" option by default makes this use the "CBR" rate control
            # if "maxrate" is defined and look_ahead = 0, then use "CBR" rate control
            # if "maxrate" is defined and look_ahead = 1, then use "LA_CBR" rate control
            "look_ahead": (0, 1),
            "look_ahead_depth": (
                0,
                30,
                60,
                90,
                100,
            ),  # how many look_ahead frames to use
        },
        "hevc_qsv": {
            "preset": (
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
                "veryslow",
            ),
            # Seems look_ahead is always enabled unless look_ahead_depth = 0
            "look_ahead_depth": (0, 30, 60, 90, 100),
            "bitrate_limit": (1,),
        },
        "h264_videotoolbox": {
            "allow_sw": (
                0,
                1,
            ),
            # Only use CBR rate control
            "require_sw": (
                0,
                1,
            ),
            "frames_before": (
                0,
                1,
            ),
            "frames_after": (
                0,
                1,
            ),
        },
        "hevc_videotoolbox": {
            "allow_sw": (
                0,
                1,
            ),
            # Only use CBR rate control
            "require_sw": (
                0,
                1,
            ),
            "frames_before": (
                0,
                1,
            ),
            "frames_after": (
                0,
                1,
            ),
        },
        "libaom-av1": {
            "cpu-used": (4, 6, 7, 8, 9, 10),
        },
        "libsvtav1": {
            "preset": (
                4,
                6,
                8,
                10,
                12,
            ),
        },
    }

    """
    Misc Encode Options
    """
    bitrates = (
        1000,
        2000,
        2500,
        3000,
        3500,
        4000,
        4500,
        5000,
        6000,
        8000,
        8500,
    )

    bframes = (
        0,
        1,
        2,
        3,
        4,
    )

    cqp = (
        0,
        4,
        8,
        12,
        14,
        16,
        18,
        20,
        22,
        24,
        26,
        28,
        30,
    )

    crf = (
        0,
        4,
        8,
        12,
        14,
        16,
        18,
        20,
        22,
        24,
        26,
        28,
        30,
    )

    encoder_prompts = {}
    encoder_prompts["libx264"] = validate_input(
        "Do you want to encode libx264? (Y/N): "
    )
    encoder_prompts["libx265"] = validate_input(
        "Do you want to encode libx265? (Y/N): "
    )
    encoder_prompts["h264_nvenc"] = False
    encoder_prompts["hevc_nvenc"] = False
    if cur_os != "MacOS":
        encoder_prompts["h264_nvenc"] = validate_input(
            "Do you want to encode h264_nvenc? (Y/N) (requires an NVENC-capable Nvidia GPU): "
        )
        encoder_prompts["hevc_nvenc"] = validate_input(
            "Do you want to encode hevc_nvenc? (Y/N) (requires an NVENC-capable Nvidia GPU): "
        )
    encoder_prompts["h264_amf"] = validate_input(
        "Do you want to encode h264_amf? (Y/N) (requires an AMF-capable AMD GPU): "
    )
    encoder_prompts["hevc_amf"] = validate_input(
        "Do you want to encode hevc_amf? (Y/N) (requires an AMF-capable AMD GPU): "
    )

    encoder_prompts["h264_qsv"] = validate_input(
        "Do you want to encode h264_qsv? (Y/N) (requires a QuickSync-capable Intel GPU): "
    )
    encoder_prompts["hevc_qsv"] = validate_input(
        "Do you want to encode hevc_qsv? (Y/N) (requires a QuickSync-capable Intel GPU): "
    )

    encoder_prompts["h264_videotoolbox"] = False
    encoder_prompts["hevc_videotoolbox"] = False
    if cur_os == "MacOS":
        encoder_prompts["h264_videotoolbox"] = validate_input(
            "Do you want to encode h264_videotoolbox? (Y/N): "
        )
        encoder_prompts["hevc_videotoolbox"] = validate_input(
            "Do you want to encode hevc_videotoolbox? (Y/N): "
        )

    encoder_prompts["libaom-av1"] = validate_input(
        "Do you want to encode libaom-av1? (Y/N): "
    )
    encoder_prompts["libsvtav1"] = validate_input(
        "Do you want to encode libsvtav1? (Y/N): "
    )
    encodings = generate_encodings(encoder_settings, encoder_prompts)


class Encoder:
    def __init__(
        self,
        name: str,
    ) -> None:
        self.name = name
        self.test_statements: list = []
        self.rc_modes: list = ["cbr", "vbr", "crf", "cqp"]
        self.presets: list = [
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ]

    # def parse_data(self) -> dict:
    #     stream = ffmpeg.input

    def get_rc_modes(self) -> list:
        return self.rc_modes

    def get_presets(self) -> list:
        return self.presets

    def get_profiles(self) -> list:
        ...
