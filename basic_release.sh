#!/bin/sh

# Inputs
# $1 -- Directory to release
# $2 -- Version number
release_dir=$1
version=$2
cd $release_dir

# Check configuration file for variables
config="release_config.sh"
if [ -x "./$config" ]
then
	. "./$config"
fi

# GH_RELEASE_NOTES variable from release_config.sh file
if [ -z "${GH_RELEASE_NOTES+x}" ]
then
	gh_notes="--generate-notes"
else
	gh_notes="-n $GH_RELEASE_NOTES"
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
gh release create "$version" "./$tmp_release_dir/$tgz_name" "$gh_notes"
rm -rf $tmp_release_dir

# PyPi Release
python -m build
twine upload -r testpypi dist/*.tar.gz
twine upload dist/*.tar.gz
