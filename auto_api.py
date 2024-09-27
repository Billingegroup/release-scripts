#!/usr/bin/env python

import optparse
import shlex
import subprocess
import sys
from pathlib import Path


def call(cmd, cwd, capture_output=False):
    cmd_list = shlex.split(cmd)
    return subprocess.run(cmd_list, cwd=cwd, capture_output=capture_output, text=True)


def create_option_parser():
    prog_name_short = Path(sys.argv[0]).name  # Program name

    class Parser(optparse.OptionParser):
        def __init__(self, prog_name, *args, **kwargs):
            super(Parser, self).__init__(*args, **kwargs)
            self.prog_name = prog_name

    parser = Parser(
        prog_name=prog_name_short,
        usage="\n".join(
            [
                "%prog <package_name> <path_to_package_proper> <path_to_api_directory>",
                "Automatically populate the API directory for a package.",
                "This only handles packages with single-depth submodules.",
            ]
        ),
        epilog="Please report bugs on https://github.com/Billingegroup/release-scripts/issues.",
    )

    return parser


def main(opts, pargs):
    base_package_name = pargs[0].replace('-', '_')
    base_package_dir = Path(pargs[1]).resolve()
    api_dir = Path(pargs[2]).resolve()

    # Clean out API directory
    for child in api_dir.iterdir():
        if child.is_file():
            child.unlink()
        else:
            # Leave directories
            pass

    # Populate API directory
    def gen_package_files(package_dir, package_name):
        """Generate package files.

        Parameters
        ----------

        package_dir: Path
            The package directory (e.g. /src/diffpy/pdfmorph).
        package_name: str
            The name of the package (e.g. diffpy.pdfmorph).
        """
        eq_spacing = "=" * len(f"{package_name} package")
        s = f""":tocdepth: -1

{package_name.replace('_', '-')} package
{eq_spacing}

.. automodule:: {package_name}
    :members:
    :undoc-members:
    :show-inheritance:
"""

        # Tag all subpackages
        sp_names = []
        sp_paths = []
        skip_dirs = ["tests", "__pycache__"]
        for child in package_dir.iterdir():
            if child.is_dir() and child.name not in skip_dirs:
                sp_names.append(f"{package_name}.{child.name}")
                sp_paths.append(child)
        if len(sp_names) > 0:
            s += """
Subpackages
-----------

.. toctree::
    :titlesonly:

"""
            for sp_name in sp_names:
                s += f"    {sp_name}\n"

        # Tag all submodules
        sm_names = []
        skip_files = ["__init__", "version"]
        for child in package_dir.iterdir():
            if (
                child.is_file()
                and child.suffix == ".py"
                and child.stem not in skip_files
            ):
                sm_names.append(f"{package_name}.{child.stem}")
        if len(sm_names) > 0:
            s += """
Submodules
----------
"""
        for sm_name in sm_names:
            dsh_spacing = "^" * len(f"{sm_name} module")
            s += f"""
{sm_name} module
{dsh_spacing}

.. automodule:: {sm_name}
    :members:
    :undoc-members:
    :show-inheritance:
"""

        s += "\n"
        package_file = api_dir / f"{package_name}.rst"
        with open(package_file, "w") as pfile:
            pfile.write(s)

        # Recurse on all subpackages
        for idx, path in enumerate(sp_paths):
            gen_package_files(path, sp_names[idx])

    gen_package_files(base_package_dir, base_package_name)


if __name__ == "__main__":
    parser = create_option_parser()
    (opts, pargs) = parser.parse_args()
    if len(pargs) != 3:
        parser.error("Incorrect number of arguments. See --help.")
    main(opts, pargs)
