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


def build_and_release(package_name, valid_versions, os_type, upload, package_path):
    if not os.path.exists(package_path):
        print(f"Error: The provided path '{package_path}' does not exist.")
        sys.exit(1)

    if os_type == 'macos':
        docker_container_name = "docker-osx"
        for version in valid_versions:
            print(f'Building {package_name} for Python {version} on macOS...')

            # Copy source code to Docker-OSX container
            subprocess.run([
                "docker", "cp", package_path, f"{docker_container_name}:/app"
            ], check=True)

            # Run build commands inside Docker-OSX container
            docker_exec_command = [
                "docker", "exec", "-it", docker_container_name,
                "bash", "-c", f"""
                cd /app &&
                pyenv install --skip-existing {version} &&
                pyenv local {version} &&
                python -m build
                """
            ]
            docker_upload_command = ["twine upload dist/* --username $TWINE_USERNAME --password $TWINE_PASSWORD"]
            subprocess.run(docker_exec_command, check=True)
            print("Build complete!")
            
            if upload:
                print(f'Uploading {package_name} for Python {version} on macOS...')
                subprocess.run(docker_upload_command, check=True)
                print("Upload complete!")
    else:
        dockerfile = f"Dockerfile.{os_type.lower()}"
        for version in valid_versions:
            print(f'Building {package_name} for Python {version} on {os_type}...')

            # Build Docker image
            docker_build_command = [
                "docker", "build", 
                "--build-arg", f"PYTHON_VERSION={version}", 
                "-t", f"{package_name}:{version}-{os_type.lower()}", 
                "-f", dockerfile, package_path
            ]
            subprocess.run(docker_build_command, check=True)
            
            # Run upload commands
            if upload:
                print(f'Uploading {package_name} for Python {version} on {os_type}...')
                docker_run_command = [
                    "docker", "run", "-it", "--rm", 
                    f"{package_name}:{version}-{os_type.lower()}", 
                    "/bin/bash" if os_type != 'Windows' else "powershell", 
                    "-c", "twine upload dist/* --username $TWINE_USERNAME --password $TWINE_PASSWORD"
                ]
                subprocess.run(docker_run_command, check=True)
                print("Upload complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Process package information for docker release.',
        usage='python docker_release.py [-u] <package_name> <min_version> <max_version> <path_to_package>'
    )
    parser.add_argument('-u', action='store_true', help='Upload the package')
    parser.add_argument('package_name', type=str, help='Name of the package')
    parser.add_argument('min_version', type=str, help='Minimum version')
    parser.add_argument('max_version', type=str, help='Maximum version')
    parser.add_argument('package_path', type=str, help='Path to the package directory')

    if len(sys.argv) < 5:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    # Validate versions
    if not is_valid_version(args.min_version) or not is_valid_version(args.max_version):
        print("Error: Invalid version format. Versions must be in the format 'X.Y'.")
        sys.exit(1)

    try:
        valid_versions = generate_versions(args.min_version, args.max_version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    for os_type in ['linux', 'windows', 'macos']:
        build_and_release(args.package_name, valid_versions, os_type, args.u, args.package_path)


if __name__ == "__main__":
    main()
