# CONTRIBUTING
## Normal Setup
Install them with either of the following commands:<br>
`pip install -r requirements.txt`<br>
OR<br>
`python -m pip install -r requirements.txt`

## Advanced Setup
If you instead want to keep your global python packages tidy, you can use the
`pipenv` python package.
1. Install `pipenv` with:<br>
    * `pip install pipenv`OR
    * `python -m pip install pipenv`
2. Create a virtual environment and install the required packages to it:<br>
    * `pipenv update -d --pre`
3. Before running any of the programs, you'll have to enter the pipenv
environment like so:<br>
    * `pipenv shell`
You can now run any of the commands directly as though you went through the
setup as described in [Normal Setup](#normal-setup)

## TODO
Please look at the [TODO.md](TODO.md) file for the current status of the
project and what tasks are left to be done.

## Libraries And Their Uses
The program uses the following libraries for general runtime:
1. `defusedxml` for parsing XML files with security and safety
2. `toml` for parsing thr `toml` configuration files that the programs use
3. `ffmpy` for interacting with the `FFmpeg` exectuable
4. `gooey` for handling the creation of a Graphical User Interface (GUI) to
make running and using the programs easier for people who are not comnfortable
with the command line.
5. `tqdm` for presenting the user with progress bars
6. `numpy` and `pandas` for creating and manipulating arrays of data.
7. `matplotlib` for generating the different graphs

The program uses the following libraries for development:
1. `black` formatter library
2. `isort` library import sorter library
3. `flake8` styling and lint checker
4. `vermin` for detecting the minimum required version of the Python runtime
required to run this project
5. `pre-commit` for running checks on commits before they are pushed
6. `pyinstaller` for generating an executable file to more easily run the
program (NOTE: this is a planned feature for the future!)

## Guidelines
The best way to support this project is to look at the items in the
[TODO.md](TODO.md) file and see what's left to be done. There are also
[projects on the GitHub page](https://github.com/HunterAP23/VMAF-Suite/projects)
that you can take a look at to contribute to. You can even help on migrating
the stuff in the TODO.md file into projects on GitHub.

When contributing Python code specifically, the `pre-commit` library should
run these checks automatically when you try to push your commits.
1. Fork the branch from this repository that you want to work on.
2. Make your changes to the code.
3. Test your changes.
4. Commit the changes.
5. Push the changes to your forked repository.

The `pre-commit` program should automatically run the checks for the project.

If you want to run the `pre-commit` check before pushing your code, you can do
do by following these instructions after step #4 mentioned above:
1. Inside the command line, go to the project's directory.
2. Run the `pre-commit` program manually to run the checks for you
automatically:<br>
    * `pre-commit run -a`

Alternatively, you can run the individual checks manually with the following:
```
black src/
isort src/
flake8
```
* `black`<br>Formats the code with `black` as per the
[pyproject.toml](pyproject.toml) file dictates in the `[tool.black]` section.
* `isort`<br>Sorts the dependencies at the top of all the files. The style
for this project's dependency import sorting is described in
[Formatting and Styling](#formatting-and-styling).
* `flake8`<br>Scans the files and identify and other styling, linting, or
other general issues with the code. The rules used for `flake8` are
described in `[flake8]` section in the [setup.cfg](setup.cfg) file.

## Formatting and Styling
1. The line limit is 120 characters. The normal 80 character limit is a bit too
restricting.
2. When defining or calling functions:
    * If the function takes a singular argument, keep the definition on a
    single line like so: `def foo(my_argument)`
    * If the function has multipel arguments, then split each argument
    onto it's own line like so:
    ```python
    def foo(
        first_arg,
        second_arg,
    ):
    ```
3. Dependency imports should follow the following rules:
    * __Section 1__: Importing entire built-in libraries. These should be
    imported at the very top of the individual program files.
    * __Section 2__: Importing portions of built-in libraries.
    * __Section 3__: Importing entire 3rd-party libraries.
    * __Section 4__: Importing portions of 3rd-party libraries.
    * __Section 5__: Importing entire libraries from this project.
    * __Section 6__: Importing portions of libraries from this project.
    * Each section should be separated by a single blank line.
    * All imports for a section should be sorted alphabetically (this is
    normally handled by the `isort` library). For section 2 and 4, if mutiple
    modules are being imported from a single library, the library that is being
    imported from should be sorted first, and then sorted by the imported
    module. For example:
    ```python
    # This is incorrect, as Path should come before PurePath
    from pathlib import PurePath, Path
    # This is the correct version
    from pathlib import Path, PurePath
    
    # This is also incorrect, as csv should come before pathlib
    from pathlib import Path
    from csv import reader
    # This is the correct version
    from csv import reader
    from pathlib import Path
    ```
4. `flake8` should not report any issues. If `flake8` does report issues,
then the commit will not be accepted until the issues are fixed. These include
unused imports, undefined functions/variables, declared but unused variables,
etc.