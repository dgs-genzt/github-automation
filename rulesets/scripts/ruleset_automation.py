import requests
import json
import os
import yaml
import sys

# GitHub personal access token (from the GitHub Action secret)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub API URL for creating/updating ruleset
API_URL = 'https://api.github.com/repos/{owner}/{repo}/rulesets'

# Headers for authentication and content type
headers = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json',
}

def load_yaml_mapping(yaml_file):
    """Load the YAML mapping file."""
    try:
        with open(yaml_file, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: The file {yaml_file} was not found.")
        return None
    except yaml.YAMLError:
        print(f"Error: The file {yaml_file} is not a valid YAML file.")
        return None

def load_ruleset_config(file_path):
    """Load the ruleset configuration from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
        return None

def delete_ruleset_if_not_in_yaml(owner, repo, existing_rulesets, yaml_ruleset_names):
    """Delete rulesets that exist in GitHub but are not listed in the YAML file."""
    for existing_ruleset in existing_rulesets:
        if existing_ruleset["name"].lower() not in yaml_ruleset_names:
            ruleset_id = existing_ruleset["id"]
            delete_url = API_URL.format(owner=owner, repo=repo) + f"/{ruleset_id}"

            # Send DELETE request to remove the ruleset from GitHub
            response = requests.delete(delete_url, headers=headers)

            if response.status_code == 204:
                print(f"Successfully deleted ruleset {existing_ruleset['name']} from {owner}/{repo}")
            else:
                print(f"Failed to delete ruleset {existing_ruleset['name']} from {owner}/{repo}: {response.status_code} - {response.text}")

def create_or_update_ruleset(owner, repo, config: dict):
    """Create or update a ruleset in the repository based on the name and ID."""
    if config is None:
        return

    # Construct the API URL with the provided owner and repo
    url = API_URL.format(owner=owner, repo=repo)

    # Check if ruleset exists
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        existing_rulesets = response.json()

        # If rulesets exist, check for a matching name and ID
        for existing_ruleset in existing_rulesets:
            if existing_ruleset["name"] == config.get("name"):
                print(f"Found matching ruleset for {owner}/{repo}\n")
                ruleset_id = existing_ruleset["id"]
                update_url = f"{url}/{ruleset_id}"
                response = requests.put(update_url, headers=headers, data=json.dumps(config))
                if response.status_code == 200:
                    print(f"Ruleset updated successfully for {owner}/{repo}\n")
                else:
                    print(f"Failed to update ruleset for {owner}/{repo}: {response.status_code} - {response.text}")
                return

        # No matching ruleset found, create a new one
        print(f"No matching ruleset found for {owner}/{repo}. Creating a new one...")
        response = requests.post(url, headers=headers, data=json.dumps(config))
        if response.status_code == 201:
            print(f"Ruleset created successfully for {owner}/{repo}")
        else:
            print(f"Failed to create ruleset for {owner}/{repo}: {response.status_code} - {response.text}")

    elif response.status_code == 404:
        # If no rulesets exist (404), create a new one
        print(f"No rulesets found for {owner}/{repo}. Creating a new one...")
        response = requests.post(url, headers=headers, data=json.dumps(config))
        if response.status_code == 201:
            print(f"Ruleset created successfully for {owner}/{repo}")
        else:
            print(f"Failed to create ruleset for {owner}/{repo}: {url} : {response.status_code} - {response.text}")

    else:
        print(f"Failed to fetch existing rulesets for {owner}/{repo}: {response.status_code} - {response.text}")

def process_yaml_mapping(yaml_file):
    """Process the YAML mapping and create/update rulesets for each repo."""
    yaml_mapping = load_yaml_mapping(yaml_file)

    if yaml_mapping:
        owner = os.path.basename(yaml_file).replace('.yaml', '')  # Extract owner name from the file name
        print(f"Processing for owner: {owner}")

        for repo, ruleset_files in yaml_mapping.items():
            # Get the list of ruleset names from the YAML file
            yaml_ruleset_names = [os.path.basename(ruleset_file).replace('.json', '') for ruleset_file in ruleset_files]

            # Fetch existing rulesets for the repo
            url = API_URL.format(owner=owner, repo=repo)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                existing_rulesets = response.json()

                # Delete rulesets that are not present in the YAML file
                delete_ruleset_if_not_in_yaml(owner, repo, existing_rulesets, yaml_ruleset_names)

            # Process each ruleset file listed in the YAML
            for ruleset_file in ruleset_files:
                ruleset_config = load_ruleset_config(ruleset_file)
                create_or_update_ruleset(owner, repo, ruleset_config)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <yaml_file_name>")
        sys.exit(1)

    yaml_file_name = sys.argv[1]  # Get the YAML file name from command-line argument
    # Ensure that the file exists in the current directory
    if not os.path.isfile(yaml_file_name):
        print(f"Error: The file {yaml_file_name} was not found in the current directory.")
        sys.exit(1)

    process_yaml_mapping(yaml_file_name)