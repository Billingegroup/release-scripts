#!/bin/sh

# Inputs
# $1 -- Directory to release
# $2 -- Version number
# $3 -- Optional flag to use docker release, --docker or -d
# $4 -- The name of the package to release, required with --docker or -d

if [ -z "${1+x}" ] || [ -z "${2+x}" ] || { { [ "$3" = "--docker" ] || [ "$3" = "-d" ]; } && [ -z "${4+x}" ]; }
then
    if [ "$3" = "--docker" ] || [ "$3" = "-d" ]; then
        echo "Usage: $0 <package_directory> <package_version> [--docker|-d] [package_name]"
    else
        echo "Usage: $0 <package_directory> <package_version>"
    fi
    exit 1
fi

release_dir=$1
version=$2
docker_flag=$3
package_name=$4

cd "$release_dir" || exit 1

# Check configuration file for variables
config="release_config.sh"
if [ -x "./$config" ]; then
    . "./$config"
fi

# Generate news if requested
#if [ -z "${NEWS+x}" ]
#then
	# Run news script
#fi

# GH_RELEASE_* Variables from config file
if [ -z "${GH_RELEASE_NOTES+x}" ]; then
    gh_notes="--generate-notes"
else
    gh_notes="-n $GH_RELEASE_NOTES"
fi

if [ -z "${GH_RELEASE_TITLE+x}" ]; then
    gh_title="-t $version"
else
    gh_title="-t $GH_RELEASE_TITLE"
fi

if [ "$docker_flag" = "--docker" ] || [ "$docker_flag" = "-d" ]; then
    # Get all existing Docker images with package_name
    docker_images=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep "$package_name")
    if [ -z "$docker_images" ]; then
        printf "Error: No Docker images found for package %s\n" "$package_name" >&2
        exit 1
    fi

    # Create a temporary directory to store Docker images
    tmp_docker_dir="tmp_docker"
    mkdir "$tmp_docker_dir"

    # Save Docker images locally
    while IFS= read -r image; do
        image_name="${image//:/_}.tar"
        docker save "$image" -o "$tmp_docker_dir/$image_name"
    done <<< "$docker_images"

    # GitHub Release (tagging only)
    git tag "$version" "$(git rev-parse HEAD)"
    git push upstream "$version"
    gh release create "$version" "$gh_title" "$gh_notes"

    # Upload Docker images to PyPI
    python -m twine upload "$tmp_docker_dir"/*.tar || printf "Warning: Failed to upload Docker images to PyPI.\n" >&2

    # Remove temporary Docker images and directory
    rm -rf "$tmp_docker_dir"

    # Remove Docker images from the local system
    while IFS= read -r image; do
        docker rmi "$image"
    done <<< "$docker_images"

else
    # Build tar.gz for GitHub Release
    tmp_release_dir="tmp_release"
    mkdir "$tmp_release_dir"
    project_path="$(pwd)"
    project="${project_path##*/}"
    tgz_name="$project-$version.tar.gz"
    tar --exclude="./$tmp_release_dir" -zcf "./$tmp_release_dir/$tgz_name" .

    # GitHub Release
    git tag "$version" "$(git rev-parse HEAD)"
    git push upstream "$version"
    gh release create "$version" "./$tmp_release_dir/$tgz_name" "$gh_title" "$gh_notes"
    rm -rf "$tmp_release_dir"

    # PyPi Release
    python -m build
    twine upload "dist/*$version*.tar.gz" || printf "Warning: No new distribution build. Check for any untracked changes.\n" >&2
fi

exit 0
