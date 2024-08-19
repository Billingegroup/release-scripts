#!/usr/bin/env python

import re
import subprocess

import optparse
import sys
import shlex
from pathlib import Path

import warnings
import requests
from hashlib import sha256

gh_release_notes = None

def call(cmd, cwd, capture_output=False):
    cmd_list = shlex.split(cmd)
    return subprocess.run(cmd_list, cwd=cwd, capture_output=capture_output, text=True)

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
        metavar="VBREGEX",
        dest="vb_regex"
    )
    
    vsn_group.add_option(
        "--changelog",
        action="store_true",
        dest="changelog",
        help="Combine all update files in the news directory into a single changelog file."
    )
    
    vsn_group.add_option(
        "--cl-file",
        metavar="FILEPATH",
        dest="cl_file",
        help="Name (and path if not in root) of changelog file. Default \'CHANGELOG.rst\'"
    )
    
    vsn_group.add_option(
        "--cl-news",
        metavar="NEWSDIR",
        dest="cl_news",
        help="Location of news directory. Default is \'news\' in the root directory."
    )
    
    vsn_group.add_option(
        "--cl-template",
        metavar="TEMPLATE",
        dest="cl_template",
        help="Name of template file. One will be auto-generated if one does not exist. Default \'TEMPLATE.rst\'."
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
    
    vsn_group.add_option(
        "--upstream",
        action="store_true",
        dest="upstream",
        help="Push to upstream rather than origin."
    )
    
    rel_group = optparse.OptionGroup(
        parser,
        "Release Targets",
        "Make sure you have bumped the version, updated the changelog, and pushed the tag."
    )
    parser.add_option_group(rel_group)
    
    rel_group.add_option(
        "--release",
        action="store_true",
        dest="release",
        help="Update the changelog, push the tag, upload to Github, and upload to PyPi."
    )
    
    rel_group.add_option(
        "--pre-release",
        action="store_true",
        dest="pre_release",
        help="Push the tag, upload to Github, and upload to PyPi."
    )
    
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
        "--cf-hash",
        metavar="HASHFILE",
        dest="forge",
        help="Generate the SHA256 Hash for a conda-forge release in HASHFILE."
    )
    
    return parser

# TODO: Implement automatic version bumping
def version_bump(opts, pargs):
    pass

def update_changelog(opts, pargs):
    release_dir = pargs[0]
    version = pargs[1]
    
    # Get name of default branch
    remote = "origin"
    if opts.upstream:
        remote = "upstream"
    remote_listing = call(f"git remote show {remote}", release_dir, capture_output=True).stdout
    head_name = re.search("HEAD branch.*: (.+)", remote_listing).group(1)
    call(f"git checkout {head_name}", release_dir)
    
    # Categories of changes
    categories = ['Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security']
    if opts.cl_categories is not None:
        categories = list(map(str.strip, opts.cl_categories.split(',')))

    # Find news directory
    news = "news"
    if opts.cl_news is not None:
        news = opts.cl_news
    news = (release_dir / news).resolve()
    if not news.exists():
        call(f"mkdir {news.name}", release_dir)
    
    # Files to ignore
    ignore = []
    if opts.cl_ignore is not None:
        ignore = list(map(str.strip, opts.cl_ignore.split(',')))
    
    # Add template to ignore list
    template = "TEMPLATE.rst"
    if opts.cl_template is not None:
        template = opts.cl_template
    ignore.append(template)
    template = (news / template).resolve()
    
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
    changelog = (release_dir / changelog).resolve()
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
                rx = re.search(r"\*\*(.+):\*\*", row)
                if rx:
                    key = rx.group(1)
                    continue
                    
                # New entry
                if key is not None and "<news item>" not in row and row.strip() != "":
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
            if len(changes[key]) > 0:
                generated_update += f"\n**{key}:**\n"
                key_updates = "".join(changes[key])
                generated_update += f"\n{key_updates}"
        
        # Write update after access point
        line = cf.readline()
        ptr = cf.tell()
        while line:
            ptr = cf.tell()
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
        cf.seek(ptr)
        cf.write(f"\n{generated_update}{spc}")
        cf.write(f"{prev_updates}")
        
        # Set Github release notes
        global gh_release_notes
        gh_release_notes = generated_update[len(f"{version}\n{sep}\n"):]
            
    # Remove used files
    for change_file in news.iterdir():
        if change_file.name in ignore:
            continue
        change_file.unlink()
        
    # Push changes to GitHub
    call(f"git add {news} {changelog}", release_dir)
    call(f"git commit -m \"Update {changelog.name}\" --no-verify", release_dir)
    call(f"git push {remote} {head_name}", release_dir)

def push_tag(opts, pargs):
    release_dir = pargs[0]
    version = pargs[1]
    
    # Create and push tag to origin (must have origin release access)
    call(f"git tag {version}", release_dir)
    if opts.upstream is not None:
        call(f"git push upstream {version}", release_dir)
    else:
        call(f"git push origin {version}", release_dir)

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
    call(f"mkdir {tmp_dir}", release_dir)
    
    # Build tar
    project = Path(release_dir).name
    tgz_name = f"{project}-{version}.tar.gz"
    call(f"tar --exclude=\"./{tmp_dir}\" -zcf \"./{tmp_dir}/{tgz_name}\" . ", release_dir)
    
    # Set notes and title if user has not provided any
    gh_notes = "--generate-notes"
    if gh_release_notes is not None and gh_release_notes.strip() != "":
        gh_notes = f"-n {gh_release_notes}"
    if opts.gh_notes is not None:
        gh_notes = f"-n {opts.gh_notes}"
    gh_title = f"-t {version}"
    if opts.gh_title is not None:
        gh_title = f"-t {opts.gh_title}"
    
    # Release through gh
    call(f"gh release create \"{version}\" \"./{tmp_dir}/{tgz_name}\" \"{gh_title}\" \"{gh_notes}\"", release_dir)
    
    # Cleanup
    call(f"rm -rf {tmp_dir}", release_dir)
        
def pypi_release(opts, pargs):
    release_dir = pargs[0]
    version = pargs[1]

    # Build distribution (build will fail if there have been no changes since the previous version)
    call("python -m build", release_dir)
    
    # Upload using twine
    no_tar = True
    no_whl = True
    for file in list((release_dir / "dist").iterdir()):
        if re.search(f".*{version}.*.tar.gz", file.name):
            no_tar = False
        if re.search(f".*{version}.*.whl", file.name):
            no_whl = False
    if no_tar:
        call(f"echo \"Warning: No new distribution build. Check for any untracked changes.\"", release_dir)
    elif no_whl:
        call(f"echo \"Warning: No wheel found.\"", release_dir)
    else:
        call(f"twine upload dist/*{version}*.tar.gz dist/*{version}*.whl", release_dir)
    
# Generate SHA256 Hash for a Conda-Forge Release
def cf_hash(opts, pargs):
    version = pargs[1]

    # Get package name and convert to pep standard
    module_name = input("Name of package being released: ")
    pep_name = module_name.replace(".", "_").replace("-", "_").lower()

    # Decide what source to pull from
    sources = ["pypi", "github"]
    source_message = ""
    for i, source in enumerate(sources):
        source_message += f"[{i+1}] {source}\n"
    source_message += "Choose a distribution source (name or number): "
    dist_source = ""
    while dist_source.lower() not in sources and dist_source not in [str(i) for i in range(1, len(sources)+1)]:
        dist_source = input(source_message)

    # Get the download link for the .tar.gz
    source_url = ""
    if dist_source == "1" or dist_source == "pypi":
        source_url = f"https://pypi.io/packages/source/{pep_name[0]}/{pep_name}/{pep_name}-{version}.tar.gz"
        dist_source = "PyPi"
    if dist_source == "2" or dist_source == "github":
        github_org = input(f"What organization/user's version of {module_name} are you looking for: ")
        source_url = f"https://github.com/{github_org}/{module_name}/archive/{version}.tar.gz"
        dist_source = "GitHub"
    tar_gz_dist = requests.get(source_url)

    # Hash and ensure hash is not of an empty file
    sha256_hash = sha256(tar_gz_dist.content).hexdigest().strip()
    if (
            sha256_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            or sha256_hash == "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
            or sha256_hash == "d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed"
        ):
        warnings.warn("SHA256 Hash Returned Emtpy File Hash. "
            f"Make sure your .tar.gz is uploaded to {dist_source}!")

    # Print hash and source to a file
    with open(opts.forge, 'w') as hash_dump:
        hash_dump.write(f"Distribution downloaded from: {source_url}\nSHA256: {sha256_hash}\n")
    print(f"SHA256 Hash written to file: {opts.forge}")


if __name__ == "__main__":
    parser = create_option_parser()
    (opts, pargs) = parser.parse_args()
    
    if len(pargs) < 2:
        parser.error("Improper usage. Too few arguments!")
    if len(pargs) > 2:
        parser.error("Improper usage. Too many arguments!")
    
    # Set release directory to absolute path
    pargs[0] = Path(pargs[0]).resolve()
    
    # Actions
    if opts.release:
        opts.changelog = True
        opts.tag = True
        opts.github = True
        opts.pypi = True
    if opts.pre_release:
        opts.tag = True
        opts.github = True
        opts.pypi = True
    if opts.changelog:
        update_changelog(opts, pargs)
    if opts.tag:
        push_tag(opts, pargs)
    if opts.github:
        github_release(opts, pargs)
    if opts.pypi:
        pypi_release(opts, pargs)
    if opts.forge is not None:
        cf_hash(opts, pargs)
