import os
import subprocess

def get_package_info():
    # Prompt the user for package information
    package_name = input('Enter the name of the package: ')
    min_version = input('Enter the minimum Python version (e.g., 3.10): ')
    max_version = input('Enter the maximum Python version (e.g., 3.12): ')
    return package_name, min_version, max_version

def generate_valid_python_versions(min_version, max_version):
    # Extracting major and minor version numbers
    min_major, min_minor = map(int, min_version.split('.'))
    max_major, max_minor = map(int, max_version.split('.'))

    # Generate valid versions list
    valid_versions = []
    for major in range(min_major, max_major + 1):
        minor_start = min_minor if major == min_major else 0
        minor_end = max_minor if major == max_major else 9
        valid_versions.extend([f'{major}.{minor}' for minor in range(minor_start, minor_end + 1)])

    return valid_versions

def build_and_release(package_name, valid_versions, os_type):
    if os_type == 'macos':
        docker_container_name = "docker-osx"
        for version in valid_versions:
            print(f'Building and releasing {package_name} for Python {version} on macOS...')

            # Copy source code to Docker-OSX container
            subprocess.run([
                "docker", "cp", ".", f"{docker_container_name}:/app"
            ], check=True)

            # Run build commands inside Docker-OSX container
            docker_exec_command = [
                "docker", "exec", "-it", docker_container_name,
                "bash", "-c", f"""
                cd /app &&
                pyenv install --skip-existing {version} &&
                pyenv local {version} &&
                python -m build &&
                twine upload dist/* --username $TWINE_USERNAME --password $TWINE_PASSWORD
                """
            ]
            subprocess.run(docker_exec_command, check=True)
    else:
        dockerfile = f"Dockerfile.{os_type.lower()}"
        for version in valid_versions:
            print(f'Building and releasing {package_name} for Python {version} on {os_type}...')

            # Build Docker image
            docker_build_command = [
                "docker", "build", 
                "--build-arg", f"PYTHON_VERSION={version}", 
                "-t", f"{package_name}:{version}-{os_type.lower()}", 
                "-f", dockerfile, "."
            ]
            subprocess.run(docker_build_command, check=True)

            # Run Docker container to upload package
            docker_run_command = [
                "docker", "run", "-it", "--rm", 
                f"{package_name}:{version}-{os_type.lower()}", 
                "/bin/bash" if os_type != 'Windows' else "powershell", 
                "-c", "twine upload dist/* --username $TWINE_USERNAME --password $TWINE_PASSWORD"
            ]
            subprocess.run(docker_run_command, check=True)

def main():
    package_name, min_version, max_version = get_package_info()
    valid_versions = generate_valid_python_versions(min_version, max_version)

    for os_type in ['linux', 'windows', 'macos']:
        build_and_release(package_name, valid_versions, os_type)

if __name__ == "__main__":
    main()
