import subprocess as sp

# Variable typing
from typing import Optional

import ffmpy


class FFmpy_Handler:
    def __init__(self, executable):
        self.validate_ffmpeg(executable)

    def run_command(self, executable: Optional[str] = None, ff_globals: Optional[str] = None, ff_inputs: Optional[dict] = None, ff_outputs: Optional[dict] = None):
        ff_exec = None

        try:
            if self.executable is None:
                if executable is None:
                    msg = "No FFmpeg executable defined. The program will now exit."
                    raise FileNotFoundError(msg)
                else:
                    ff_exec = executable
            else:
                ff_exec = self.executable
        except FileNotFoundError as fnfe:
            print(fnfe)
            exit(1)

        try:
            ff = ffmpy.FFmpeg(
                executable=ff_exec,
                global_options=ff_globals,
                inputs=ff_inputs,
                outputs=ff_outputs
            )

            return ff.run(stdout=sp.PIPE, stderr=sp.PIPE)
        except ffmpy.FFExecutableNotFoundError as ffenfe:
            print(ffenfe)
            exit(1)

    def _validate_ffmpeg(self, executable) -> bool:
        self.run_command(executable, ff_globals="-h")
        self.executable = executable
        # ff_outputs={"-": "-f null"}

    def search_lib(self, lib: str) -> bool:
        return True
