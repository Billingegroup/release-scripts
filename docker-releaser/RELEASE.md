# Docker Release Workflow
## Overview
Use docker to build (and optionally release) Python packages for PyPI. Windows and Linux
builds are handled via the dockerfiles, but Mac builds are done using the [Docker-OSX image](https://github.com/sickcodes/Docker-OSX).

## Usage
```
python docker_release.py [-u] <package_name> <min_version> <max_version> <path_to_package>
```
Where `-u` is an optional upload flag, `package_name` is the name of the Python package
as it is to be released, `min_version` is the minimum Python version (i.e. 3.10),
`max_version` is the maximum Python version (i.e. 3.12), and `path_to_packagee` is the
path to the package directory. If there is only one valid version, put the same number twice.

### Building Only
```
python docker_release.py diffpy.pdffit2 3.10 3.12 ~/Documents/dev/diffpy.pdffit2
```

Locate the build files in the build or dist directory within `<path_to_package>`.

### Build and Upload
In a command line environment on ubuntu or linux shell, set your twine info:
```
export TWINE_USERNAME="twine-username"
export TWINE_PASSWORD="twine-password"
```

Then, run the docker release script. This example command will both build and upload `diffpy.pdffit2`:
```
python docker_release.py -u diffpy.pdffit2 3.10 3.12 ~/Documents/dev/diffpy.pdffit2
```
