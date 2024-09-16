#!/usr/bin/env python

"""
This script fetches the latest workflows from the central repository 'release-scripts' 
and updates the local dummy workflows. Before running the script, install the required 
packages using the following command:

    conda install requests

This script assumes the package repository has the same parent directory as 'release-scripts'. 
You can change this by modifying the 'LOCAL_WORKFLOW_DIR' variable.

Sometimes there would be timeout errors while fetching the workflows from the central repository. 
In such cases, you can try running the script again.
"""

import os
import re
from pathlib import Path
import requests

proj = (
    input(f"Enter value for 'PROJECT' (default: {'PROJECT_NAME'}): ").strip()
    or "PROJECT_NAME"
)

pwd = os.path.dirname(__file__)

CENTRAL_REPO_ORG = "Billingegroup"
CENTRAL_REPO_NAME = "release-scripts"
CENTRAL_WORKFLOW_DIR = ".github/workflows/templates"
LOCAL_WORKFLOW_DIR = Path(pwd + "/../" + proj + "/.github/workflows")

user_input_cache = {"PROJECT": proj}

def get_central_workflows():
    base_url = f"https://api.github.com/repos/{CENTRAL_REPO_ORG}/{CENTRAL_REPO_NAME}/contents/{CENTRAL_WORKFLOW_DIR}"
    response = requests.get(base_url, timeout=5)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch central workflows: {response.status_code}")

    workflows = {}
    for file in response.json():
        if file['type'] == 'file' and file['name'].endswith('.yml'):
            content_response = requests.get(file['download_url'], timeout=5)
            if content_response.status_code == 200:
                workflows[file['name']] = content_response.text
    return workflows


def get_user_input(prompt, default, param_name):
    if param_name in user_input_cache:
        return user_input_cache[param_name]

    user_value = input(f"{prompt} (default: {default}): ").strip()
    if user_value.lower() == "false":
        value = False
    elif user_value.lower() == "true":
        value = True
    elif user_value:
        value = user_value
    else:
        value = default

    user_input_cache[param_name] = value
    return value


def update_workflow_params(content):

    def replace_match(match):
        key = match.group(1)
        default_value = match.group(2)
        if key not in user_input_cache:
            user_value = get_user_input(f"Enter value for '{key}'", default_value, key)
            user_input_cache[key] = user_value
        return str(user_input_cache[key])

    pattern = re.compile(r"\{\{\s*(\w+)\s*/\s*([^\s\}]+)\s*\}\}")
    return pattern.sub(replace_match, content)


def update_local_workflows(central_workflows):
    local_workflows = set(f.name for f in LOCAL_WORKFLOW_DIR.glob("*.yml"))
    central_workflow_names = set(central_workflows.keys())

    for name, content in central_workflows.items():
        local_file = LOCAL_WORKFLOW_DIR / name

        content = update_workflow_params(content)

        with open(local_file, "w", encoding="utf-8") as file:
            file.write(content)

    for name in local_workflows - central_workflow_names:
        (LOCAL_WORKFLOW_DIR / name).unlink()
        print(f"Removed workflow {name}")


def main():
    try:
        LOCAL_WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
        central_workflows = get_central_workflows()
        update_local_workflows(central_workflows)
        print("Workflow synchronization completed successfully")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
