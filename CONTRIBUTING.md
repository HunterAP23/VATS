### CONTRIBUTING
### Normal Setup
Install them with either of the following commands:
```
pip install -r requirements.txt
```
OR
```
python -m pip install -r requirements.txt
```

If you instead want to keep your global python packages tidy, you can use the
`pipenv` python package.
1. Install `pipenv` with:
```
pip install pipenv
```
OR
```
python -m pip install pipenv
```
2. Create a virtual environment and install the required packages to it.
```
pipenv update -d --pre
```
3. Before running any of the programs, you'll have to enter the pipenv
environment like so:
```
pipenv shell
```
Now your
4. Run commands through `pipenv` or enter into the `pipenv` virtual environment:
`pipenv run` / `python -m pipenv run` OR `pipenv shell` /
`python -m pipenv shell`