import requests
from config import GITHUB_TOKEN
from typing import Optional

def get_pr_diff(repo_url: str, pr_number: int, github_token: Optional[str] = None) -> str:

    api_base_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
    api_url = f"{api_base_url}/pulls/{pr_number}"
    
    token = github_token or GITHUB_TOKEN
    
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {token}" if token else ""
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PR diff: {e}")
        raise Exception(f"Failed to fetch PR diff for {repo_url} PR #{pr_number}")