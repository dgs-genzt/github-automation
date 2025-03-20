import requests
import yaml
import sys
import os

# GitHub API base URL
GITHUB_API_URL = "https://api.github.com"

# GitHub personal access token (from the GitHub Action secret)
GITHUB_TOKEN = os.getenv('GH_TOKEN')

# Function to authenticate with GitHub API
def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

# Function to get the team ID from the team name
def get_team_id(team_name, org_name):
    url = f"{GITHUB_API_URL}/orgs/{org_name}/teams"
    response = requests.get(url, headers=get_github_headers())
    if response.status_code == 200:
        teams = response.json()
        for team in teams:
            if team["slug"] == team_name.lower():
                return team["id"]
    return None

# Function to get the repo's teams and their permissions
def get_repo_teams_permissions(repo_name, org_name):
    url = f"{GITHUB_API_URL}/repos/{org_name}/{repo_name}/teams"
    response = requests.get(url, headers=get_github_headers())
    if response.status_code == 200:
        return response.json()
    return []

# Function to add or update a team in a repository
def add_or_update_team_in_repo(repo_name, team_name, permission, org_name):
    team_id = get_team_id(team_name, org_name)
    if team_id is None:
        print(f"Team {team_name} not found.")
        return

    # Check if the team already exists with the desired permission
    existing_teams = get_repo_teams_permissions(repo_name, org_name)
    for team in existing_teams:
        if team["id"] == team_id:
            current_permission = team["permission"]
            if current_permission != permission:
                # Update permission
                team_slug = team_name.lower()
                print(f"team slug:{team_slug}")
                url = f"{GITHUB_API_URL}/orgs/{org_name}/teams/{team_slug}/repos/{org_name}/{repo_name}"
                data = {"permission": permission}
                response = requests.put(url, json=data, headers=get_github_headers())
                if response.status_code == 204:
                    print(f"Updated team {team_name} permission to {permission} in {repo_name}")
                else:
                    print(f"Failed to update permission for team {team_name} in {repo_name}")
            return
#https://api.github.com/orgs/ORG/teams/TEAM_SLUG/repos/OWNER/REPO
    # If the team doesn't exist, add the team with the specified permission
    team_slug = team_name.lower()
    print(f"team doesn't exist in repo || team slug:{team_slug}")
    url = f"{GITHUB_API_URL}/orgs/{org_name}/teams/{team_slug}/repos/{org_name}/{repo_name}"
    print(f"{GITHUB_API_URL}/orgs/{org_name}/teams/{team_slug}/repos/{org_name}/{repo_name}")
    data = {"permission": permission}
    response = requests.put(url, json=data, headers=get_github_headers())
    if response.status_code == 204:
        print(f"Added team {team_name} with {permission} permission in {repo_name}")
    else:
        print(f"Failed to add team {team_name} to {repo_name}")
        print(f"Response: {response.reason}")

# Function to remove a team from a repository
def remove_team_from_repo(repo_name, team_name, org_name):

            # Remove the team from the repository
            print(f"team doesn't exist in repo || team slug:{team_name}")
            url = f"{GITHUB_API_URL}/orgs/{org_name}/teams/{team_name}/repos/{org_name}/{repo_name}"
            response = requests.delete(url, headers=get_github_headers())
            if response.status_code == 204:
                print(f"Removed team {team_name} from {repo_name}")
            else:
                print(f"Failed to remove team {team_name} from {repo_name}")
            return

# Function to process the YAML file and update the teams accordingly
def process_yaml_file(yaml_file_path):
    # Extract the GitHub organization name from the file name (before .yml extension)
    org_name = os.path.basename(yaml_file_path).split('.')[0]

    with open(yaml_file_path, 'r') as file:
        repo_info = yaml.safe_load(file)

    for repo, teams in repo_info.items():
        repo_team_names = []
        for team_info in teams:
            for team_name, permission in team_info.items():
                # Add or update the team
                add_or_update_team_in_repo(repo, team_name, permission, org_name)
                repo_team_names.append(team_name)

        # Check for teams to remove (if a team should be removed based on the YAML file)
        existing_teams = get_repo_teams_permissions(repo, org_name)
        for team in existing_teams:
            # If the team doesn't exist in the YAML file, we remove it
            #if not any(team_name in str(team_info) for team_info in teams):
            if team["name"] not in repo_team_names:
                team_name = team["name"]
                remove_team_from_repo(repo, team["slug"], org_name)

# Main function to run the script
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_yaml_file>")
        sys.exit(1)

    yaml_file_path = sys.argv[1]  # Path to the YAML file passed as a command-line argument

    # Ensure the YAML file exists
    if not os.path.isfile(yaml_file_path):
        print(f"Error: The file '{yaml_file_path}' does not exist.")
        sys.exit(1)

    process_yaml_file(yaml_file_path)
