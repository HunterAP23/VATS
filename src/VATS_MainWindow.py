from pathlib import Path

# from vats_FFmpeg import ffmpeg
import ffmpeg
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

__Encoders: dict = {
    "generic": {
        "name": "generic",
        "test_statements": [
            "Error initializing output stream",
            "Error while opening encoder for output stream",
            "Unknown encoder",
        ],
    },
    "libx264 / AVC": {
        "name": "libx264",
        "test_statements": [],
    },
    "libx265 / HEVC": {
        "name": "libx265",
        "test_statements": [],
    },
    "AOM AV1": {
        "name": "libaom-av1",
        "test_statements": [],
    },
    "SVT AV1": {
        "name": "libsvtav1",
        "test_statements": [],
    },
    "Nvidia NVENC H.264": {
        "name": "h264_nvenc",
        "test_statements": [],
    },
    "Nvidia NVENC HEVC": {
        "name": "hevc_nvenc",
        "test_statements": [],
    },
    "Nvidia NVENC AV1": {
        "name": "av1_nvenc",
        "test_statements": [],
    },
    "AMD AMF/VCE H.264": {
        "name": "h264_amf",
        "test_statements": ["DLL amfrt64.dll failed to open"],
    },
    "AMD AMF/VCE HEVC": {
        "name": "hevc_amf",
        "test_statements": ["DLL amfrt64.dll failed to open"],
    },
    "AMD AMF/VCE AV1": {
        "name": "av1_amf",
        "test_statements": ["DLL amfrt64.dll failed to open"],
    },
    "Intel QuickSync H.264": {
        "name": "h264_qsv",
        "test_statements": ["Error creating a MFX session"],
    },
    "Intel QuickSync HEVC": {
        "name": "hevc_qsv",
        "test_statements": ["Error creating a MFX session"],
    },
    "Intel QuickSync AV1": {
        "name": "av1_qsv",
        "test_statements": ["Error creating a MFX session"],
    },
    "Apple VideoToolbox H.264": {
        "name": "h264_videotoolbox",
        "test_statements": [],
    },
    "Apple VideoToolbox HEVC": {
        "name": "hevc_videotoolbox",
        "test_statements": [],
    },
    "Apple ProRes": {
        "name": "prores",
        "test_statements": [],
    },
    "Apple ProRes (iCodec Pro)": {
        "name": "prores",
        "test_statements": [],
    },
}

__Decoders: dict = {
    "H.264 / AVC": "h264",
    "H.265 / HEVC": "hevc",
    "AOM AV1": "libaom-av1",
    "AOM AV1 alternative": "av1",
    "VideoLAN dav1d": "libdav1d",
    "Nvidia NVDEC/CUVID H.264": "h264_cuvid",
    "Nvidia NVDEC/CUVID HEVC": "hevc_cuvid",
    "Nvidia NVDEC/CUVID AV1": "av1_cuvid",
    "Intel QuickSync H.264": "h264_qsv",
    "Intel QuickSync HEVC": "hevc_qsv",
    "Intel QuickSync AV1": "av1_qsv",
    "Apple ProRes": "prores",
}

__HWAccels: dict = {
    "Nvidia CUDA": "cuda",
    "Intel QuickSync": "qsv",
    "DirectX 3D Acceleration 2 (DXVA2) - DX9": "dxva2",
    "DirectX 3D Acceleration 2 (DXVA2) - DX11": "d3d11va",
    "Open Compute Language (OpenCL)": "opencl",
    "Vulkan": "vulkan",
    "Video Acceleration API (VAAPI)": "vaapi",
}


class MainWindow(QMainWindow):
    def __init__(self, args: dict, cur_os: str = "Windows"):
        """_summary_

        Args:
            args (dict): dictionary of command line arguments
            cur_os (str, optional): OS string descriptor. Defaults to "Windows".
        """
        super().__init__()

        self.args = args

        self.reference_dir_le = QLineEdit(args["Reference Directory"])
        self.config_file_le = QLineEdit(args["Config File"])
        self.ffmpeg_le = QLineEdit(args["FFmpeg"])
        self.psnr_cb = QCheckBox("PSNR")
        self.psnr_cb.setChecked(args["PSNR"])
        self.ssim_cb = QCheckBox("SSIM")
        self.ssim_cb.setChecked(args["SSIM"])
        self.ms_ssim_cb = QCheckBox("MS-SSIM")
        self.ms_ssim_cb.setChecked(args["MS-SSIM"])
        self.psnr_hvs_cb = QCheckBox("PSNR-HVS")
        self.psnr_hvs_cb.setChecked(args["PSNR-HVS"])
        self.subsamples_sb = QSpinBox()
        self.subsamples_sb.setRange(1, 60)
        self.subsamples_sb.setValue(args["Subsamples"])
        self.models_gb = QGroupBox()
        self.models_bg = QButtonGroup()
        self.models_bg.setParent(self.models_gb)
        self.models = args["Models"]
        for model in self.models:
            setattr(self, f"{model}_cb", QCheckBox(model))
            # getattr(self, f"{model}_cb")
            self.models_bg.addButton(getattr(self, f"{model}_cb"))
        self.log_format_cb = QComboBox()
        self.log_format_cb.addItems(["xml", "json", "csv"])
        self.log_format_cb.setCurrentText(args["Log Format"])
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.ensureCursorVisible()
        self.btn_run = QPushButton("Run")
        self.btn_clear = QPushButton("Clear")

        self.encoder_checkbox_groupbox = QGroupBox()
        self.encoder_checkbox_layout = QGridLayout()
        self.encoder_checkbox_libx264 = FFmpegCheckBox(
            "libx264 / AVC", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_libx264, 0, 0
        )
        self.encoder_checkbox_libx265 = FFmpegCheckBox(
            "libx265 / HEVC", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_libx265, 1, 0
        )

        self.encoder_checkbox_av1_aom = FFmpegCheckBox("AOM AV1", window=self)
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_av1_aom, 2, 0
        )
        self.encoder_checkbox_av1_svt = FFmpegCheckBox("SVT AV1", window=self)
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_av1_svt, 3, 0
        )
        col = 1
        row = 0
        if cur_os != "MacOS":
            self.encoder_checkbox_h264_nvenc = FFmpegCheckBox(
                "Nvidia NVENC H.264", window=self
            )
            self.encoder_checkbox_layout.addWidget(
                self.encoder_checkbox_h264_nvenc, row, col
            )
            row += 1
            self.encoder_checkbox_hevc_nvenc = FFmpegCheckBox(
                "Nvidia NVENC HEVC", window=self
            )
            self.encoder_checkbox_layout.addWidget(
                self.encoder_checkbox_hevc_nvenc, row, col
            )
            row += 1
            self.encoder_checkbox_av1_nvenc = FFmpegCheckBox(
                "Nvidia NVENC AV1", window=self
            )
            self.encoder_checkbox_layout.addWidget(
                self.encoder_checkbox_av1_nvenc, row, col
            )
            col += 1
            row = 0
        self.encoder_checkbox_h264_amf = FFmpegCheckBox(
            "AMD AMF/VCE H.264", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_h264_amf, row, col
        )
        row += 1
        self.encoder_checkbox_hevc_amf = FFmpegCheckBox(
            "AMD AMF/VCE HEVC", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_hevc_amf, row, col
        )
        row += 1
        self.encoder_checkbox_av1_amf = FFmpegCheckBox(
            "AMD AMF/VCE AV1", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_av1_amf, row, col
        )
        col += 1
        row = 0
        self.encoder_checkbox_h264_qsv = FFmpegCheckBox(
            "Intel QuickSync H.264", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_h264_qsv, row, col
        )
        row += 1
        self.encoder_checkbox_hevc_qsv = FFmpegCheckBox(
            "Intel QuickSync HEVC", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_hevc_qsv, row, col
        )
        row += 1
        self.encoder_checkbox_av1_qsv = FFmpegCheckBox(
            "Intel QuickSync AV1", window=self
        )
        self.encoder_checkbox_layout.addWidget(
            self.encoder_checkbox_av1_qsv, row, col
        )
        col += 1
        row = 0
        if cur_os == "MacOS":
            self.encoder_checkbox_h264_vt = FFmpegCheckBox(
                "Apple VideoToolbox H.264", window=self
            )
            self.encoder_checkbox_layout.addWidget(
                self.encoder_checkbox_h264_vt, row, col
            )
            row += 1
            self.encoder_checkbox_hevc_vt = FFmpegCheckBox(
                "Apple VideoToolbox HEVC", window=self
            )
            self.encoder_checkbox_layout.addWidget(
                self.encoder_checkbox_hevc_vt, row, col
            )
            col += 1
            row -= 1
        row += 1
        self.encoder_checkbox_groupbox.setLayout(self.encoder_checkbox_layout)

        for enc in range(self.encoder_checkbox_layout.count()):
            cur_box = self.encoder_checkbox_layout.itemAt(enc).widget()
            # print(f"cur_box is {cur_box.__name__}")
            cur_box.stateChanged.connect(cur_box.checked_action)

        ###############################################################

        self.decoder_checkbox_groupbox = QGroupBox()
        self.decoder_checkbox_layout = QGridLayout()
        self.decoder_checkbox_libx264 = FFmpegCheckBox(
            "H.264 / AVC", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_libx264, 0, 0
        )
        self.decoder_checkbox_libx265 = FFmpegCheckBox(
            "H.265 / HEVC", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_libx265, 1, 0
        )

        self.decoder_checkbox_av1_aom = FFmpegCheckBox(
            "AOM AV1", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_av1_aom, 2, 0
        )
        self.decoder_checkbox_av1_svt = FFmpegCheckBox(
            "AOM AV1 alternative", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_av1_svt, 3, 0
        )
        self.decoder_checkbox_av1_svt = FFmpegCheckBox(
            "VideoLAN dav1d", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_av1_svt, 4, 0
        )
        col = 1
        row = 0
        if cur_os != "MacOS":
            self.decoder_checkbox_h264_nvenc = FFmpegCheckBox(
                "Nvidia NVDEC/CUVID H.264", fftype="Decoder", window=self
            )
            self.decoder_checkbox_layout.addWidget(
                self.decoder_checkbox_h264_nvenc, row, col
            )
            row += 1
            self.decoder_checkbox_hevc_nvenc = FFmpegCheckBox(
                "Nvidia NVDEC/CUVID HEVC", fftype="Decoder", window=self
            )
            self.decoder_checkbox_layout.addWidget(
                self.decoder_checkbox_hevc_nvenc, row, col
            )
            row += 1
            self.decoder_checkbox_av1_nvenc = FFmpegCheckBox(
                "Nvidia NVDEC/CUVID AV1", fftype="Decoder", window=self
            )
            self.decoder_checkbox_layout.addWidget(
                self.decoder_checkbox_av1_nvenc, row, col
            )
            col += 1
            row = 0
        self.decoder_checkbox_h264_qsv = FFmpegCheckBox(
            "Intel QuickSync H.264", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_h264_qsv, row, col
        )
        row += 1
        self.decoder_checkbox_hevc_qsv = FFmpegCheckBox(
            "Intel QuickSync HEVC", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_hevc_qsv, row, col
        )
        row += 1
        self.decoder_checkbox_av1_qsv = FFmpegCheckBox(
            "Intel QuickSync AV1", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_av1_qsv, row, col
        )
        col += 1
        row = 0
        self.decoder_checkbox_apple_prores = FFmpegCheckBox(
            "Apple ProRes", fftype="Decoder", window=self
        )
        self.decoder_checkbox_layout.addWidget(
            self.decoder_checkbox_apple_prores, row, col
        )
        row += 1
        self.decoder_checkbox_groupbox.setLayout(self.decoder_checkbox_layout)

        for enc in range(self.decoder_checkbox_layout.count()):
            cur_box = self.decoder_checkbox_layout.itemAt(enc).widget()
            # print(f"cur_box is {cur_box.__name__}")
            cur_box.stateChanged.connect(cur_box.checked_action)

        ###############################################################

        reference_dir_layout = QHBoxLayout(self)
        reference_dir_layout.addWidget(QLabel("Reference Directory:"))
        reference_dir_layout.addWidget(self.reference_dir_le)
        config_file_layout = QHBoxLayout()
        config_file_layout.addWidget(QLabel("Config File:"))
        config_file_layout.addWidget(self.config_file_le)
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.addWidget(QLabel("FFmpeg Argument:"))
        ffmpeg_layout.addWidget(self.ffmpeg_le)
        psnr_layout = QHBoxLayout()
        psnr_layout.addWidget(self.psnr_cb)
        ssim_layout = QHBoxLayout()
        ssim_layout.addWidget(self.ssim_cb)
        ms_ssim_layout = QHBoxLayout()
        ms_ssim_layout.addWidget(self.ms_ssim_cb)
        psnr_hvs_layout = QHBoxLayout()
        psnr_hvs_layout.addWidget(self.psnr_hvs_cb)
        subsamples_layout = QHBoxLayout()
        subsamples_layout.addWidget(QLabel("Subsamples:"))
        subsamples_layout.addWidget(self.subsamples_sb)
        models_layout = QHBoxLayout()
        models_layout.addWidget(QLabel("Models:"))
        models_layout.addWidget(self.models_gb)
        log_format_layout = QHBoxLayout()
        log_format_layout.addWidget(QLabel("Log Format:"))
        log_format_layout.addWidget(self.log_format_cb)

        layout = QVBoxLayout()
        layout.addLayout(reference_dir_layout)
        layout.addLayout(config_file_layout)
        layout.addLayout(ffmpeg_layout)
        layout.addLayout(psnr_layout)
        layout.addLayout(ssim_layout)
        layout.addLayout(ms_ssim_layout)
        layout.addLayout(psnr_hvs_layout)
        layout.addLayout(subsamples_layout)
        layout.addLayout(models_layout)
        layout.addLayout(log_format_layout)
        layout.addWidget(self.encoder_checkbox_groupbox)
        layout.addWidget(self.decoder_checkbox_groupbox)
        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.output_box)

        self.btn_run.clicked.connect(self.print_args)
        self.btn_clear.clicked.connect(self.clear_output)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def print_args(self):
        """Do a thing"""
        for arg_name, arg_val in self.args.items():
            self.write_output(f"{arg_name}: {arg_val}")
        self.test_ffmpeg_feature(decoder="hevc_cuvid", hwaccel="cuda")

    def write_output(self, msg: str):
        """Write output to the log box

        Args:
            msg (str): Message to print to the log box
        """
        self.output_box.append(str(msg))
        print(msg)

    def clear_output(self):
        """Clear the output box"""
        self.output_box.clear()

    def action_on_check(self, receiver):
        print(receiver)
        print(type(receiver))


class FFmpegCheckBox(QCheckBox):
    """Wrapper class for QCheckBox for FFmpeg encoders."""

    def __init__(
        self,
        name: str,
        fftype: str = "Encoder",
        window: MainWindow = None,
        test_statements: list[str] = None,
    ):
        self.name: str = name
        self.codec: str = str(globals()[f"__{fftype}s"][self.name])
        self.fftype: str = fftype
        self.test_statements: list = []
        if fftype == "Decoder":
            self.test_statements.append("Error while decoding stream".lower())
            if "intel" in self.name.lower():
                self.test_statements.append(
                    "Error creating a MFX session".lower()
                )
                self.test_statements.append(
                    "Error initializing an MFX session".lower()
                )
                self.test_statements.append("Error decoding header".lower())
        self.window: MainWindow = window
        # self.__pix_fmt: str = "nv12"
        # self.__extra_args: dict = {}
        # if "av1" in name.lower():
        #     self.__pix_fmt = "yuv420p"
        #     self.__extra_args = {"frame-parallel": 1, "row-mt": 1}
        self.__encode_success: bool = None
        super().__init__(name)

    def checked_action(self):
        """Callback for when the checkbox is checked or unchecked, handles FFmpeg tests."""
        if self.isChecked:
            if self.__encode_success is None:
                result = test_ffmpeg_feature(
                    **{
                        "window": self.window,
                        self.fftype: self.codec,
                        "test_statements": self.test_statements,
                    },
                )
                if result:
                    self.window.write_output(
                        f"{self.fftype} {self.__name__} failed to encode."
                    )
                    self.setCheckable(False)
                    self.setChecked(False)
                    self.setEnabled(False)
                else:
                    self.window.write_output(
                        f"Encoder {self.__name__} is available on this system."
                    )
                    self.__encode_success = True
            elif self.__encode_success:
                pass
            else:
                self.setCheckable(False)
                self.setChecked(False)
                self.setEnabled(False)


#  FIX QSV HEVC DECODE WHEN NO QSV DEVICE DETECTED
# Add check to see if the encoder is even listed in the output of ffmpeg -encoders
# Add different sample videos to use for different decoders
# Add checks to make sure input video is the correct format for the decoder
# Add checks to see what threading features are available for the encoder or decoder
# Add checks to see what supported hardware devices are available for the encoder or decoder
# Add checks to see what supported pixel formats are available for the encoder or decoder
def test_ffmpeg_feature(
    window: MainWindow,
    Encoder: str = None,
    Decoder: str = None,
    HWAccel: str = None,
    test_statements: str = None,
):
    """Test FFmpeg feature."""
    window.write_output(any([Encoder, Decoder, HWAccel]))
    if not any([Encoder, Decoder, HWAccel]):
        raise ValueError(
            "Must specify at least one of encoder, decoder, or hwaccel."
        )

    msg = []
    if Encoder is not None:
        msg.append(f"encoder {Encoder}")
    else:
        Encoder = "libx264"  # have to have an encoder when testing FFmpeg
        # msg.append(f"encoder {encoder}")
    if Decoder is not None:
        msg.append(f"decoder {Decoder}")
    if HWAccel is not None:
        msg.append(f"Testing hwaccel {HWAccel}")

    msg = ", ".join(msg)
    window.write_output(f"Testing {msg}...")

    kwargs_decode = {"hide_banner": None, "loglevel": "debug"}
    if HWAccel is not None:
        kwargs_decode["hwaccel"] = HWAccel
    if Decoder is not None:
        kwargs_decode["c:v"] = Decoder
    stream = ffmpeg.input(
        filename=str(Path("G:\\Shooters_HEVC_Preset-slow_QP_1.mp4")),
        **kwargs_decode,
    )

    kwargs_encode = {
        "c:v": Encoder,
        "filename": "-",
        "t": 0.01,
        "format": "null",
    }
    kwargs_encode["pix_fmt"] = "nv12"
    if "av1" in Encoder.lower():
        kwargs_encode["pix_fmt"] = "yuv420p"
    stream = ffmpeg.output(stream, **kwargs_encode)
    window.write_output(stream.get_args())
    proc = ffmpeg.run_async(stream, quiet=True)
    window.write_output("started...")
    res = []
    for line in iter(proc.stderr.readline, ""):
        res.append(line.decode())
        # if any([test in line.decode().lower() for test in test_statements]):
        #     msg = []
        #     if Encoder is not None:
        #         msg.append(f"encoder {Encoder}")
        #     if Decoder is not None:
        #         msg.append(f"decoder {Decoder}")
        #     if HWAccel is not None:
        #         msg.append(f"hwaccel {HWAccel}")
        #     msg = ",".join(msg)
        #     msg = "Test failed for " + msg
        #     window.write_output(msg)
        #     window.write_output("\n".join(res))
        #     return False, "", ""
    out, err = proc.communicate()
    return proc.poll(), out.decode(), err.decode()
