import logging as lg
import subprocess as sp

# Variable typing
from typing import Optional, Union

import ffmpy

# from vmaf_file_handler import VMAF_File_Handler


class FFmpy_Handler_Exception(ffmpy.FFExecutableNotFoundError):
    pass


class FFmpy_Handler:
    def __init__(self, executable_ffmpeg: str, log: Optional[lg.RootLogger]):
        self._executable_ffmpeg = None
        self._libraries = []
        self._log = log
        # super.__init__(
        #     file=executable,
        #     file_type="config",
        #     ext="exe",
        #     os_name="Windows",
        #     program="Calculations"
        # )
        self._validate_ffmpeg(executable_ffmpeg)
        self._get_libs()

    def _validate_ffmpeg(self, executable: str) -> bool:
        self.run_command(executable, ff_globals="-h -hide_banner", ff_outputs={"-": "-f null"})
        self._executable_ffmpeg = executable

    def _get_libs(self):
        libs_out, libs_err = self.run_command(ff_globals="-buildconf")
        libs_out_str = libs_out.decode("utf-8")

        for line in libs_out_str.split("\n"):
            self._libraries.append(line.strip().replace("\r", ""))

    def run_command(
        self,
        executable: Optional[str] = None,
        ff_globals: Optional[str] = None,
        ff_inputs: Optional[dict] = None,
        ff_outputs: Optional[dict] = None,
        get_cmd: Optional[bool] = False,
    ) -> Union[str, tuple]:
        ff_exec = None

        try:
            if self._executable_ffmpeg is None:
                if executable is None:
                    msg = "No FFmpeg executable defined. The program will now exit."
                    raise FileNotFoundError(msg)
                else:
                    ff_exec = executable
            else:
                ff_exec = self._executable_ffmpeg
        except FileNotFoundError as fnfe:
            self._log.critical(fnfe)
            exit(1)

        try:
            ff = ffmpy.FFmpeg(
                executable=ff_exec,
                global_options=ff_globals,
                inputs=ff_inputs,
                outputs=ff_outputs,
            )

            if get_cmd:
                return ff.cmd
            else:
                return ff.run(stdout=sp.PIPE, stderr=sp.PIPE)
        except ffmpy.FFExecutableNotFoundError as ffenfe:
            self._log.critical(ffenfe)
            exit(1)

    def search_lib(self, lib: str) -> bool:
        if "--enable-" in lib:
            check = lib
        else:
            check = "--enable-{}".format(lib)

        if check in self._libraries:
            return True
        else:
            return False
