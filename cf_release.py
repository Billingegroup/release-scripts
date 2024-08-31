import sys
import requests
import subprocess
from os.path import join, exists, dirname
from click import prompt, confirm

"""
This script streamlines the process of updating Python package versions and
their corresponding SHA256 hash in a meta.yaml file, followed by creating a
PR into the GitHub feedstock repository.

Workflow:

- The user is prompted to enter the name of a PyPI package.
- Retrieves the feedstock directory and meta.yaml file paths
- Fetches the latest versions and SHA256 hashes from PyPI.
- Displays the latest PyPI versions, asking the user to choose the version.
- Fetches the user's GitHub username using the GitHub CLI for authentication
- Updates the meta.yaml file with the new version and SHA256
- Commits these changes, pushes them to GitHub, and creates a PR
"""

"""
Utility Functions
"""


def format_sha(sha):
    """Return a truncated version of the SHA256 hash."""
    return sha[:4] + "..." + sha[-4:]


def run_command(command, cwd=None):
    """Run a shell command in the specified directory."""
    subprocess.run(
        command,
        check=True,
        shell=True,
        text=True,
        cwd=cwd,
    )


"""
Core Functionalities - fetch info from PyPI, update meta.yaml and create PR
"""


def get_package_versions_SHA(package_name, count=5):
    """Fetch the latest versions of the package and their SHA256 from PyPI."""
    response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
    if response.status_code == 200:
        data = response.json()
        versions = sorted(data["releases"].keys(), reverse=True)[:count]
        version_info = {}
        for version in versions:
            files = data["releases"][version]
            for file in files:
                if file["packagetype"] == "sdist":
                    version_info[version] = file["digests"]["sha256"]
                    break
        return version_info
    else:
        error_message = (
            f"ERROR: No matching package has been found for {package_name}. "
            "Please double check the package name or visit "
            "https://pypi.org to check whether your package exists."
        )

        raise ValueError(error_message)


def get_feedstock_and_meta_file_path(package_name):
    release_scripts_dir_path = dirname(sys.argv[0])
    dev_dir_path = dirname(release_scripts_dir_path)
    feedstock_dir_path = join(dev_dir_path, f"{package_name}-feedstock")
    meta_file_path = join(feedstock_dir_path, "recipe", "meta.yaml")

    # Check if the meta file exists to ensure the path is correct
    if not exists(meta_file_path):
        error_message = (
            f"ERROR: meta.yaml file not found. Please re-run after checking whether {package_name}-feedstock "
            "exists in the dev folder Please also check the folder strucutre provided in the "
            "GitLab documentation: https://www.gitlab.com/learn/conda-forge#dev-folder-structure"
        )

        raise FileNotFoundError(error_message)

    return feedstock_dir_path, meta_file_path


def update_meta_yaml(meta_file_path, new_version, new_sha256):
    """
    Update the meta.yaml file with the new version and SHA256 hash
    before making a PR to the feedstock repository.
    """
    with open(meta_file_path, "r") as file:
        lines = file.readlines()

    with open(meta_file_path, "w") as file:
        for line in lines:
            if "{%- set version =" in line:
                line = f'{{%- set version = "{new_version}" -%}}\n'
            elif "sha256:" in line:
                line = f"  sha256: {new_sha256}\n"
            file.write(line)


def run_gh_shell_command(fd_stock_dir_path, meta_file_path, version, SHA256, username):
    """
    Create a PR from a branch name of <new_version>
    to the main branch of the feedstock repository.
    """
    try:
        # Check out main and pull the latest changes
        run_command("git checkout main", cwd=fd_stock_dir_path)
        run_command("git pull upstream main", cwd=fd_stock_dir_path)

        # Create and switch to a new branch named after the new version
        run_command(f"git checkout -b {version}", cwd=fd_stock_dir_path)

        # Update the meta.yaml file
        update_meta_yaml(meta_file_path, version, SHA256)

        # Add the updated meta.yaml file to the staging area
        run_command("git add recipe/meta.yaml", cwd=fd_stock_dir_path)

        # Commit the changes
        run_command(
            f'git commit -m "Update conda package to {version}"', cwd=fd_stock_dir_path
        )

        # Push the new branch to your origin repository
        run_command(f"git push origin {version}", cwd=fd_stock_dir_path)

        # Create a pull request using GitHub CLI
        pr_command = (
            f"gh pr create --base main --head {username}:{version} "
            f"--title 'Update meta.yaml to {version}' "
            f"--body 'Updated meta.yaml to version {version} with SHA value of {SHA256}'"
        )

        # Run the PR create command in the appropriate directory
        run_command(pr_command, cwd=fd_stock_dir_path)

    except subprocess.CalledProcessError as e:
        print(f"Failed to execute command: {e.cmd}")
        print(f"Error message: {e.stderr}")
        raise


"""
User Prompts
"""


def prompt_is_latest_version(pypi_version_info):
    latest_version = next(iter(pypi_version_info))
    use_latest_version = confirm(
        f"\nQ2. Would you like to proceed with the latest version {latest_version}?",
        default=True,
    )
    return use_latest_version


def print_latest_package_verison(package_name, pypi_version_info):
    print(f"\nThe latest versions of {package_name} are:")

    for i, (version, sha) in enumerate(pypi_version_info.items()):
        if i < 4:  # Display only the first 4 versions
            print(f" - Version: {version}, SHA256: {format_sha(sha)}")
        else:
            break


"""
GitHub Integration
"""


def get_github_username_via_gh():
    """Get the GitHub username using the GitHub CLI."""
    try:
        username = subprocess.check_output(
            ["gh", "api", "user", "--jq", ".login"], text=True
        ).strip()
        return username
    except subprocess.CalledProcessError:
        raise RuntimeError(
            "Could not retrieve GitHub username using GitHub CLI. "
            "Please make sure your local machine is authenticated with GitHub."
        )


"""
Main Entry Point
"""


def main():
    # Q1 Ask the package name from the user
    package_name = prompt("Q1. Please enter the PyPI package name Ex) numpy", type=str)

    try:
        # Get path to feedstock directory and meta.yaml file
        fd_stock_dir_path, meta_file_path = get_feedstock_and_meta_file_path(
            package_name
        )

        # Get the latest versions and SHA256 hashes from PyPI
        pypi_version_info = get_package_versions_SHA(package_name)

    except (FileNotFoundError, ValueError) as e:
        print(str(e))
        sys.exit(1)

    # Print the latest versions of the package
    print_latest_package_verison(package_name, pypi_version_info)

    # Q2. Ask the user if they want to proceed with the latest version
    if prompt_is_latest_version(pypi_version_info):
        # If the user confirms, proceed with the latest version
        new_version = next(iter(pypi_version_info))
        print(f"Using latest version: {new_version}")
    else:
        # Allow user to use a different version
        new_version = prompt("Please enter the version you would like to use", type=str)
        while new_version not in pypi_version_info:
            new_version = prompt(
                f"ERROR: {new_version} is not available in the list of versions. "
                "Please re-enter",
                type=str,
            )

    # Get the SHA256 hash for the selected version
    SHA256 = pypi_version_info[new_version]
    print(
        f"Great, you have selected version {new_version} with SHA256 "
        f"{format_sha(SHA256)} for {package_name}. "
        "We will now update the meta.yaml file and create a PR to the feedstock repository."
    )

    # Get the GitHub username using the GitHub CLI
    try:
        username = get_github_username_via_gh()
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)

    # Run the shell command to update the .yml file and create a PR
    run_gh_shell_command(
        fd_stock_dir_path, meta_file_path, new_version, SHA256, username
    )


if __name__ == "__main__":
    main()