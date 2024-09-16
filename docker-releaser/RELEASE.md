# Docker Release Workflow
## Overview
Use docker to build (and optionally release) Python packages for PyPI. Windows and Linux
builds are handled via the dockerfiles, but Mac builds are done using the [Docker-OSX image](https://github.com/sickcodes/Docker-OSX).

## Requirements/Install
In order to run the docker releaser, you first need to install `docker` as normal. Then, navigate to
https://github.com/sickcodes/Docker-OSX and install the latest macos image `sickcodes/docker-osx:latest`.

Once this is done, clone the repo https://github.com/Billingegroup/release-scripts
`cd` into the `docker-releaser` directory and now you are ready to run the `docker_release.py` script as normal.

## Usage
```
python docker_release.py <package_name> [-u] [version_number] <min_version> <max_version> <path_to_package>
```
Where `-u` is an optional upload flag that requires `version_number` if it is set, `package_name` is the name 
of the Python package as it is to be released, `min_version` is the minimum Python version (i.e. 3.10),
`max_version` is the maximum Python version (i.e. 3.12), and `path_to_package` is the
path to the package directory. If there is only one valid version, put the same number twice.

### Building Only
If you just want to build the package, you can do as follows. Example for `diffpy.pdffit2`:

```
python docker_release.py diffpy.pdffit2 3.10 3.12 ~/Documents/dev/diffpy.pdffit2
```

The build files can be found by running `docker images`

### Build and Upload
Follow these first steps, from `basic_release.txt`:

#### Prerequisites
##### Python Build
`pip install build` or `mamba/conda install conda-forge::python-build`

##### GitHub
Must first login with GitHub-CLI:
First, install gh

```
mamba install gh --channel conda-forge
```

Then authenticate

```
gh auth login
```

Easy choices for login:

? What account do you want to log into? GitHub.com

? What is your preferred protocol for Git operations on this host? HTTPS

? How would you like to authenticate GitHub CLI? Login with a web browser

Then open the link https://github.com/login/device and enter the one-time code

##### PyPi
First install twine:

```
pip install twine
```

and then configure the pypirc file https://packaging.python.org/en/latest/specifications/pypirc/

#### Configuration Variables
You may put optional configuration variables in a release_config.sh file


#### Run

Once these steps are complete, run the docker releaser.

Add the `-u` flag and the associated `version_number`. This example command will both build and upload `diffpy.pdffit2` as
version `1.5.0`:

```
python docker_release.py -u 1.5.0 diffpy.pdffit2 3.10 3.12 ~/Documents/dev/diffpy.pdffit2
```
