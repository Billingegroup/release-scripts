#!/bin/sh

# Inputs
# $1 -- Directory to release
# $2 -- Version number

if [ -z "${1+x}" ] && [ -z "${2+x}" ]
then
	echo "Usage: $0 <package_directory> <package_version>"
	exit 1
fi

release_dir=$1
version=$2
cd $release_dir

# Check configuration file for variables
config="release_config.sh"
if [ -x "./$config" ]
then
	. "./$config"
fi

# Generate news if requested
#if [ -z "${NEWS+x}" ]
#then
	# Run news script
#fi

# GH_RELEASE_* Variables from config file
if [ -z "${GH_RELEASE_NOTES+x}" ]
then
	gh_notes="--generate-notes"
else
	gh_notes="-n $GH_RELEASE_NOTES"
fi

if [ -z "${GH_RELEASE_TITLE+x}" ]
then
	gh_title="-t $version"
else
	gh_notes="-t $GH_RELEASE_TITLE"
fi

# Build tar.gz for GitHub Release
tmp_release_dir="tmp_release"
mkdir "$tmp_release_dir"
project_path="$(pwd)"
project="${project_path##*/}"
tgz_name="$project-$version.tar.gz"
tar --exclude="./$tmp_release_dir" -zcf "./$tmp_release_dir/$tgz_name" .

# GitHub Release
git tag $version $(git rev-parse HEAD)
git push upstream $version
gh release create "$version" "./$tmp_release_dir/$tgz_name" "$gh_title" "$gh_notes"
rm -rf $tmp_release_dir

# PyPi Release
python -m build
twine upload dist/*$version*.tar.gz || echo "Warning: No new distribution build. Check for any untracked changes."

exit 0
