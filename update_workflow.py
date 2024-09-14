#!/usr/bin/env python

import os
from pathlib import Path
import requests
import yaml
from yamlcore import CoreLoader, CoreDumper

""" This script fetches the latest workflows from the central repository 'release-scripts' and updates the local dummy workflows. Before running the script, install the required packages using the following command:

    conda install yaml requests
    pip install yamlcore

    This script assumes you are in the 'release-scripts' repository, and the package repository has the same parent directory as 'release-scripts'. You can change this by modifying the 'LOCAL_WORKFLOW_DIR' variable. 

    Sometimes there would be timeout errors while fetching the workflows from the central repository. In such cases, you can try running the script again.
"""

proj = input(f"Enter project name (default: {'PROJECT_NAME'}): ").strip() or 'PROJECT_NAME'

pwd = os.path.dirname(__file__)

CENTRAL_REPO_ORG = "Billingegroup"
CENTRAL_REPO_NAME = "release-scripts"
CENTRAL_WORKFLOW_DIR = ".github/workflows/templates"
LOCAL_WORKFLOW_DIR = Path(pwd + "/../"+proj+"/.github/workflows")

user_input_cache = {'project': proj}

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
    if user_value.lower() == 'false':
        value = False
    elif user_value.lower() == 'true':
        value = True
    elif user_value:
        value = user_value
    else:
        value = default

    user_input_cache[param_name] = value
    return value

def update_workflow_params(workflow):
    if 'jobs' in workflow:
        for _, job_content in workflow['jobs'].items():
            if isinstance(job_content, dict) and 'with' in job_content:
                for key, default_value in job_content['with'].items():
                    user_value = get_user_input(f"Enter value for '{key}'", default_value, key)
                    job_content['with'][key] = user_value
    return workflow

def update_local_workflows(central_workflows):
    local_workflows = set(f.name for f in LOCAL_WORKFLOW_DIR.glob("*.yml"))
    central_workflow_names = set(central_workflows.keys())

    for name, content in central_workflows.items():
        local_file = LOCAL_WORKFLOW_DIR / name
        central_yaml = yaml.load(content, Loader=CoreLoader)

        central_yaml = update_workflow_params(central_yaml)
        with open(local_file, 'w', encoding='utf-8') as file:
            yaml.dump(central_yaml, file, Dumper=CoreDumper, sort_keys=False)
        
        with open(local_file, 'r', encoding='utf-8') as file:
            content = file.read()
        parts = content.split('jobs', 1)
        parts[0] = parts[0].replace('-', '  -')
        content = 'jobs'.join(parts)
        with open(local_file, 'w', encoding='utf-8') as file:
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
