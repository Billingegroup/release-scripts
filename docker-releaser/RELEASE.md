# Docker Release Workflow
## Idea:
- 3 dockerfiles, one for each OS
- No github action, just download the dockerfiles from a repo and run a series
of commands locally to release the package
- Python script to automate building each version
    - Answer questions
- Docker on macos: https://github.com/sickcodes/Docker-OSX


Do the following commands and answer the prompted questions:

```
export TWINE_USERNAME="twine-username"
export TWINE_PASSWORD="twine-password"

python release.py
```
