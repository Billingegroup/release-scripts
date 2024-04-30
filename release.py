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
            "%prog <directory-to-release> <version-number> OPTIONS",
            "Release a particular version of a directory.",
        ]),
        epilog="Please report bugs on https://github.com/Billingegroup/release-scripts/issues."
    )
    
    vsn_group = optparse.OptionGroup(
        parser,
        "Version Control",
        "Update local version numbers, changelog information, and remote tag versions."
    )
    parser.add_option_group(vsn_group)
    
    vsn_group.add_option(
        "--version-bump",
    )
    
    vsn_group.add_option(
        "--changelog",
        action="store_true",
        dest="changelog",
        help="Combine all update files in the news directory into a single changelog file."
    )
    
    vsn_group.add_option(
        "--cl-file",
        metavar="FILENAME",
        dest="cl_file",
        help="Name of changelog file."
    )
    
    vsn_group.add_option(
        "--cl-news",
        metavar="NEWSDIR",
        dest="cl_news",
        help="Location of news directory."
    )
    
    vsn_group.add_option(
        "--cl-template",
        metavar="TEMPLATE",
        dest="cl_template",
        help="Name of template file. One will be auto-generated if one does not exist."
    )
    
    vsn_group.add_option(
        "--cl-categories",
        metavar="CATLIST",
        dest="cl_categories",
        help="List of categories to include in the changelog. Default \'Added, Changed, Deprecated, Removed, Fixed, Security\'."
    )
    
    vsn_group.add_option(
        "--cl-ignore",
        metavar="FILELIST",
        dest="cl_ignore",
        help="List of files in news to ignore. The template file is always ignored."
    )
    
    vsn_group.add_option(
        "--cl-access-point",
        metavar="APSTRING",
        dest="cl_access_point",
        help="All changes will be put in the change log after the access point. Default \'.. current developments\'."
    )
    
    vsn_group.add_option(
        "--tag",
        action="store_true",
        dest="tag",
        help="Create and push a version tag to GitHub."
    )
    
    rel_group = optparse.OptionGroup(
        parser,
        "Release Targets",
        "Make sure you have bumped the version, updated the changelog, and pushed the tag."
    )
    parser.add_option_group(rel_group)
    
    rel_group.add_option(
        "--github",
        action="store_true",
        dest="github",
        help="Initiate a release on GitHub."
    )
    
    rel_group.add_option(
        "--gh-title",
        metavar="TITLE",
        dest="gh_title",
        help="Title of GitHub release."
    )
    
    rel_group.add_option(
        "--gh-notes",
        metavar="NOTES",
        dest="gh_notes",
        help="Release notes to be posted for GitHub release."
    )
    
    rel_group.add_option(
        "--pypi",
        action="store_true",
        dest="pypi",
        help="Initiate a release on PyPi."
    )
    
    rel_group.add_option(
        "--conda-forge",
        action="store_true",
        dest="forge",
        help="Initiate a release on Conda-Forge."
    )
    
    return parser

# TODO: Implement automatic version bumping
def version_bump(opts, pargs):
    pass

def update_changelog(opts, pargs):
    release_dir = pargs[0]
    version = pargs[1]
    
    # Categories of changes
    categories = ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security']
    if opts.cl_categories is not None:
        categories = list(map(str.strip, opts.cl_categories.split(',')))
    
    # Find news directory
    news = "news"
    if opts.cl_news is not None:
        news = opts.cl_news
    news = release_dir / news
    if not news.exists():
        subprocess.run(f"mkdir {news.name}", shell=True, check=True)
    
    # Files to ignore
    ignore = []
    if opts.cl_ignore is not None:
        ignore = list(map(str.strip, opts.cl_ignore.split(',')))
    
    # Add template to ignore list
    template = "TEMPLATE.rst"
    if opts.cl_template is not None:
        template = opts.cl_template
    ignore.append(template)
    template = news / template
    
    # Generate template if one does not exist
    if not template.exists():
        with open(template, 'w') as tf:
            entries = [f"**{cat}:**\n\n* <news item>\n" for cat in categories]
            generated_template = "\n".join(entries)
            tf.write(f"{generated_template}\n")
    
    # Create a changelog if one does not exist
    changelog = "CHANGELOG.rst"
    if opts.cl_file is not None:
        changelog = opts.cl_file
    ignore.append(changelog)
    changelog = news / changelog
    if not changelog.exists():
        with open(changelog, 'w') as cf:
            generated_changelog = "=============\nRelease Notes\n=============\n\n.. current developments\n"
            cf.write(f"{generated_changelog}\n")
    
    # Compile all changes
    changes = {cat: [] for cat in categories}
    for change_file in news.iterdir():
        if change_file.name in ignore:
            continue
        key = None
        with open(change_file, 'r') as cf:
            for row in cf:
                # New key
                rx = re.search("\*\*(.+):\*\*", row)
                if rx:
                    key = rx.group(1)
                    continue
                    
                # New entry
                if key is not None and row.strip() != "":
                    changes[key].append(row) 
    
    # Write to changelog
    access_point = ".. current developments"
    if opts.cl_access_point is not None:
        access_point = opts.cl_access_point
    with open(changelog, 'r+') as cf:
        # Generate text based on changes
        sep = ""
        for i in range(len(str(version))):
            sep += "="
        generated_update = f"{version}\n{sep}\n"
        for key in changes.keys():
            generated_update += f"\n**{key}:**\n"
            key_updates = "".join(changes[key])
            generated_update += f"\n{key_updates}"
        
        # Write update after access point
        line = cf.readline()
        ptr = cf.tell()
        while line:
            ptr = cf.tell()
            print(ptr)
            if line.strip() == access_point:
                break
            line = cf.readline()
        
        # Spacing
        cf.seek(ptr)
        spc = ""
        prev_updates = cf.read()
        if prev_updates.strip() != "":
            cf.seek(ptr)
            spc = "\n\n"
            print("Has updates")
        cf.seek(ptr)
        cf.write(f"\n{generated_update}{spc}")
        cf.write(f"{prev_updates}")
            
    # Remove used files
    for change_file in news.iterdir():
        if change_file.name in ignore:
            continue
        change_file.unlink()

def push_tag(opts, pargs):
    version = pargs[1]
    
    # Create and push tag to upstream (must have upstream access)
    subprocess.run(f"git tag {version}", shell=True, check=True)
    subprocess.run(f"git push upstream {version}", shell=True, check=True)

# TODO: Implement environment and permissions checks
def check():
    pass

def github_release(opts, pargs):
    release_dir = pargs[0]
    version = pargs[1]

    # Create temporary release directory
    tmp_dir = "release_tmp"
    while (Path(release_dir) / tmp_dir).exists():
        tmp_dir += "_prime"
    subprocess.run(f"mkdir {tmp_dir}", shell=True, check=True)
    
    # Build tar
    project = Path(release_dir).name
    tgz_name = f"{project}-{version}.tar.gz"
    subprocess.run(f"tar --exclude=\"./{tmp_dir}\" -zcf \"./{tmp_dir}/{tgz_name}\" . ", shell=True, check=True)
    
    # Set notes and title if user has not provided any
    gh_notes = "generate_notes"
    if opts.gh_notes is not None:
        gh_notes = f"-n {opts.gh_notes}"
    gh_title = f"-t {version}"
    if opts.gh_title is not None:
        gh_title = f"-t {opts.gh_title}"
    
    # Release through gh
    subprocess.run(f"gh release create \"{version}\" \"./{tmp_dir}/{tgz_name}\" \"{gh_title}\" \"{gh_notes}\"", shell=True, check=True)
    
    # Cleanup
    subprocess.run(f"rm -rf {tmp_dir}", shell=True, check=True)
        
def pypi_release(opts, pargs):
    version = pargs[1]

    # Build distribution (build will fail if there have been no changes since the previous version)
    subprocess.run("python -m build", shell=True, check=True)
    
    # Upload using twine
    subprocess.run(f"twine upload dist/*{version}*.tar.gz || echo \"Warning: No new distribution build. Check for any untracked changes.\"", shell=True, check=True)

# TODO: Implement anaconda release (push to feedstock)
def conda_release(opts, pargs):
    pass

if __name__ == "__main__":
    parser = create_option_parser()
    (opts, pargs) = parser.parse_args()
    
    if len(pargs) < 2:
        parser.error("Improper usage. Too few arguments!")
    if len(pargs) > 2:
        parser.error("Improper usage. Too many arguments!")
    
    # Go to release directory
    pargs[0] = Path(pargs[0]).resolve()
    subprocess.run(f"cd {pargs[0]}", shell=True, check=True)
    
    # Actions
    if opts.changelog:
        update_changelog(opts, pargs)
    if opts.tag:
        push_tag(opts, pargs)
    if opts.github:
        github_release(opts, pargs)
    if opts.pypi:
        pypi_release(opts, pargs)
