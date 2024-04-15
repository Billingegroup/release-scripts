#!/usr/bin/env python

import re
import subprocess

import optparse
import sys
from pathlib import Path

def create_option_parser():
    prog_name_short = Path(sys.argv[0]).name  # Program name
    
    class Parser(optparse.OptionParser):
        def __init__(self, prog_name, *args, **kwargs):
            super(Parser, self).__init__(*args, **kwargs)
            self.prog_name = prog_name
            
    def detailed_error(self, msg):
        self.exit(2, f"{prog_name}: error: {msg}\n")
    
    parser = Parser(prog_name=prog_name_short,
        usage='\n'.join([
            "%prog <comma-separated-list-of-python-versions>",
            "For example, %prog \"3.10, 3.11, 3.12\""
        ]),
        epilog="Please report bugs on https://github.com/Billingegroup/release-scripts/issues."
    )
    parser.add_option(
        '-m',
        '--mamba',
        action="store_true",
        dest="mamba",
        help="Use mamba instead of conda. Without this option enabled, conda will be used."
    )
    parser.add_option(
        '-p',
        '--prefix',
        metavar="PREFIX",
        dest="prefix",
        help="""Set the environment name prefix. Environments will be named <prefix><version><suffix>.
The default prefix is \"py-\".""",
    )
    parser.add_option(
        '-s',
        '--suffix',
        metavar="SUFFIX",
        dest="suffix",
        help="""Set the environment name suffix. Environments will be named <prefix><version><suffix>.
The default suffix is \"-env\".""",
    )
    parser.add_option(
        '--vreqs',
        action="store_true",
        dest="vreqs",
        help="""Indicate that the requirements to be installed are version-specific.
This changes the behavior of the inputs for --requirements and --pip-requirements.
Each now takes in an expression of the form \"<prefix>[vsn]<suffix>\".
The program will replace \"[vsn]\" with a version number (e.g. 3.10).
For example, the input \"reqs/py-[vsn]-reqs.txt\" corresponds to files like \"reqs/py-3.10-reqs.txt\"."""
    )
    parser.add_option(
        '-r',
        '--requirements',
        metavar="REQFILE",
        dest="reqs",
        help="""A file containing requirements to install in each environment.
These requirements must be installable through conda/mamba.""",
    )
    parser.add_option(
        '--pip-requirements',
        metavar="PREQFILE",
        dest="pip_reqs",
        help="""A file containing requirements to install in each environment.
These requirements must be installable through pip.
It is recommended to install through conda/mamba unless the packages are available only on PyPi.""",
    )
    parser.add_option(
        '-d',
        '--dev-mode',
        action="store_true",
        dest="dev_mode",
        help="""Install the current directory in developer mode (pip install -e .).
This command will be run in each environment created.""",
    )

    return parser

if __name__ == "__main__":
    parser = create_option_parser()
    (opts, pargs) = parser.parse_args()
    if len(pargs) != 1:
        parser.error("Improper usage.")
    versions = list(map(str.strip, pargs[0].split(",")))
    
    # Switch environment manager to mamba if chosen
    env_manager = "conda"
    if opts.mamba:
        env_manager = "mamba"

    # Give user-specified names to environments
    prefix = "py-"
    suffix = "-env"
    if opts.prefix is not None:
        prefix = opts.prefix
    if opts.suffix is not None:
        suffix = opts.suffix
    def get_env_name(prefix, suffix, version):
        return prefix + version + suffix
    env_names = list(map(lambda v: get_env_name(prefix, suffix, v), versions))

    # Create environments
    for i, env_name in enumerate(env_names):
        vers_spec_req = opts.reqs
        if opts.vreqs and vers_spec_req is not None:
            vers_spec_req = opts.reqs.replace("[vsn]", versions[i])
        if vers_spec_req is not None:
            print(f"{env_manager} create -n {env_name} python={versions[i]} --file={vers_spec_req} --yes")
        else:
            print(f"{env_manager} create -n {env_name} python={versions[i]} --yes")

    # Install pip requirements into each environment
    if opts.pip_reqs is not None or opts.dev_mode:
        for i, env_name in enumerate(env_names):
            print(f"{env_manager} activate {env_name}")
            vers_spec_preq = opts.pip_reqs
            if opts.vreqs and vers_spec_preq is not None:
                vers_spec_preq = vers_spec_preq.replace("[vsn]", versions[i])
            if vers_spec_preq is not None:
                print(f"pip install -r {vers_spec_preq} --yes")
            if opts.dev_mode:
                print(f"pip install -e . --yes")
            print(f"{env_manager} deactivate")
