#!/usr/bin/env python

import argparse
import subprocess
import sys
import re
import os


def is_valid_version(version):
    """Check if a version string is a valid Python version."""
    return re.match(r'^\d+\.\d+$', version) is not None


def generate_versions(min_version, max_version):
    """Generate a list of versions between min_version and max_version."""
    min_major, min_minor = map(int, min_version.split('.'))
    max_major, max_minor = map(int, max_version.split('.'))
    
    if min_major != max_major:
        raise ValueError("Major versions must be the same for min_version and max_version")
    
    if min_minor > max_minor:
        raise ValueError("min_version cannot be greater than max_version")
    
    return list(range(min_minor, max_minor + 1))


def build_and_release(package_name, valid_versions, os_type, upload, package_path, version_number=None):
    if not os.path.exists(package_path):
        print(f"Error: The provided path '{package_path}' does not exist.")
        sys.exit(1)

    dockerfile = f"Dockerfile.{os_type.lower()}"
    for version in valid_versions:
        print(f'Building {package_name} for Python 3.{version} on {os_type}...')

        # Build Docker image
        docker_build_command = [
            "docker", "build", 
            "--build-arg", f"PYTHON_VERSION=3.{version}", 
            "-t", f"{package_name}:3.{version}-{os_type.lower()}", 
            "-f", dockerfile, package_path
        ]
        subprocess.run(docker_build_command, check=True)

    if upload:
        print(f'Uploading {package_name} for Python 3.{version} on {os_type}...')
        subprocess.run([
            "../basic_release.sh", package_path, version_number
        ], check=True)
        print("Upload complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Process package information for docker release.',
        usage='python docker_release.py <package_name> [-u] [version_number] <min_version> <max_version> <path_to_package>'
    )
    parser.add_argument('-u', action='store_true', help='Upload the package')
    parser.add_argument('package_name', type=str, help='Name of the package')
    parser.add_argument('min_version', type=str, help='Minimum version')
    parser.add_argument('max_version', type=str, help='Maximum version')
    parser.add_argument('package_path', type=str, help='Path to the package directory')
    parser.add_argument('version_number', nargs='?', type=str, help='Version number (required if -u is used)')

    if len(sys.argv) < 5:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    # Validate versions
    if not is_valid_version(args.min_version) or not is_valid_version(args.max_version):
        print("Error: Invalid version format. Versions must be in the format 'X.Y'.")
        sys.exit(1)

    # Ensure version_number is provided if -u is set
    if args.u and not args.version_number:
        print("Error: Version number is required when using the -u flag.")
        sys.exit(1)

    try:
        valid_versions = generate_versions(args.min_version, args.max_version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Strip trailing '/' from path if there
    package_path = args.package_path[:-1] if args.package_path.endswith('/') else args.package_path
    
    os_types = ['linux', 'windows', 'macos']
    for os_type in os_types:
        build_and_release(args.package_name, valid_versions, os_type, args.u, package_path, args.version_number)


if __name__ == "__main__":
    main()
