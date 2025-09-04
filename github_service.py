import requests
from config import GITHUB_TOKEN
from logger_config import setup_logger, log_function_start, log_function_end, log_step
from typing import Optional, Dict, Any, List

# Initialize logger
logger = setup_logger(__name__)


class GithubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass


def extract_repo_info_from_url(repo_url: str) -> Dict[str, str]:

    log_function_start(logger, "extract_repo_info_from_url", repo_url=repo_url)
    
    try:
        if not repo_url.startswith("https://github.com/"):
            raise GithubAPIError(f"Invalid GitHub URL format: {repo_url}")
            
        path = repo_url.replace("https://github.com/", "").strip("/")
        parts = path.split("/")
        
        if len(parts) < 2:
            raise GithubAPIError(f"Invalid GitHub URL format: {repo_url}")
            
        repo_info = {"owner": parts[0], "repo": parts[1]}
        log_function_end(logger, "extract_repo_info_from_url", owner=repo_info["owner"], repo=repo_info["repo"])
        return repo_info
        
    except Exception as e:
        logger.error(f"Failed to extract repo info from URL: {e}")
        log_function_end(logger, "extract_repo_info_from_url", success=False, error=str(e))
        raise


def create_api_headers(github_token: Optional[str] = None) -> Dict[str, str]:

    log_function_start(logger, "create_api_headers", has_token=bool(github_token))
    
    token = github_token or GITHUB_TOKEN
    
    if not token:
        error_msg = "GitHub token is required but was not provided"
        logger.error(error_msg)
        log_function_end(logger, "create_api_headers", success=False, error=error_msg)
        raise GithubAPIError(error_msg)

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    log_function_end(logger, "create_api_headers", headers_created=True)
    return headers


def fetch_pr_metadata(api_base_url: str, pr_number: int, headers: Dict[str, str]) -> Dict[str, str]:

    log_function_start(logger, "fetch_pr_metadata", pr_number=pr_number)
    
    try:
        pr_url = f"{api_base_url}/pulls/{pr_number}"
        log_step(logger, "Making API request", url=pr_url)
        
        pr_response = requests.get(pr_url, headers=headers)
        pr_response.raise_for_status()
        
        pr_data = pr_response.json()
        metadata = {
            'title': pr_data.get('title', ''),
            'description': pr_data.get('body', '')
        }
        
        log_step(logger, "Fetched PR metadata", 
                title_length=len(metadata['title']), 
                description_length=len(metadata['description']))
        
        log_function_end(logger, "fetch_pr_metadata", 
                        title_present=bool(metadata['title']),
                        description_present=bool(metadata['description']))
        
        return metadata
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch PR metadata: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" | Status: {e.response.status_code}"
        
        logger.error(error_msg)
        log_function_end(logger, "fetch_pr_metadata", success=False, error=error_msg)
        raise GithubAPIError(error_msg)


def fetch_pr_diff(api_base_url: str, pr_number: int, headers: Dict[str, str]) -> str:

    log_function_start(logger, "fetch_pr_diff", pr_number=pr_number)
    
    try:
        pr_url = f"{api_base_url}/pulls/{pr_number}"
        
        diff_headers = headers.copy()
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        log_step(logger, "Making diff API request", url=pr_url)
        
        diff_response = requests.get(pr_url, headers=diff_headers)
        diff_response.raise_for_status()
        
        diff_text = diff_response.text
        
        log_step(logger, "Fetched raw diff", diff_size=len(diff_text))
        log_function_end(logger, "fetch_pr_diff", diff_lines=len(diff_text.splitlines()))
        
        return diff_text
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch PR diff: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" | Status: {e.response.status_code}"
        
        logger.error(error_msg)
        log_function_end(logger, "fetch_pr_diff", success=False, error=error_msg)
        raise GithubAPIError(error_msg)


def fetch_file_content(content_url: str, token: str) -> str:
   
    try:
        headers = {"Authorization": f"token {token}"}
        content_response = requests.get(content_url, headers=headers)
        content_response.raise_for_status()
        return content_response.text
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch file content from {content_url}: {e}"
        logger.error(error_msg)
        raise GithubAPIError(error_msg)


def fetch_changed_files(api_base_url: str, pr_number: int, headers: Dict[str, str], token: str) -> List[Dict[str, str]]:

    log_function_start(logger, "fetch_changed_files", pr_number=pr_number)
    
    try:
        files_url = f"{api_base_url}/pulls/{pr_number}/files"
        
        log_step(logger, "Making files API request", url=files_url)
        
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        
        files_data = files_response.json()
        
        log_step(logger, "Retrieved files list", total_files=len(files_data))
        
        changed_files = []
        processed_files = 0
        
        for file_info in files_data:
            # Only process added or modified files
            if file_info['status'] in ['added', 'modified']:
                try:
                    content_url = file_info['raw_url']
                    filename = file_info['filename']
                    
                    log_step(logger, "Fetching file content", filename=filename)
                    
                    content = fetch_file_content(content_url, token)
                    
                    changed_files.append({
                        "filename": filename,
                        "content": content
                    })
                    
                    processed_files += 1
                    
                except GithubAPIError as e:
                    logger.warning(f"Failed to fetch content for file {file_info['filename']}: {e}")
                    continue
        
        log_step(logger, "Fetch list of changed files and their content", 
                processed_files=processed_files, 
                total_changed_files=len(changed_files))
        
        log_function_end(logger, "fetch_changed_files", 
                        files_processed=processed_files, 
                        files_retrieved=len(changed_files))
        
        return changed_files
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch changed files: {e}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f" | Status: {e.response.status_code}"
        
        logger.error(error_msg)
        log_function_end(logger, "fetch_changed_files", success=False, error=error_msg)
        raise GithubAPIError(error_msg)


def get_pr_context(repo_url: str, pr_number: int, github_token: Optional[str] = None) -> Dict[str, Any]:
    
    log_function_start(logger, "get_pr_context", repo_url=repo_url, pr_number=pr_number)
    
    try:
        
        repo_info = extract_repo_info_from_url(repo_url)
        api_base_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}"

        headers = create_api_headers(github_token)
        token = github_token or GITHUB_TOKEN

        pr_context = {}
 
        log_step(logger, "Starting PR metadata fetch")
        metadata = fetch_pr_metadata(api_base_url, pr_number, headers)
        pr_context.update(metadata)

        log_step(logger, "Starting PR diff fetch")
        pr_context['diff'] = fetch_pr_diff(api_base_url, pr_number, headers)

        log_step(logger, "Starting changed files fetch")
        pr_context['changed_files'] = fetch_changed_files(api_base_url, pr_number, headers, token)
        
        log_function_end(logger, "get_pr_context", 
                        files_count=len(pr_context['changed_files']),
                        has_title=bool(pr_context.get('title')),
                        has_diff=bool(pr_context.get('diff')))
        
        return pr_context
        
    except Exception as e:
        error_message = f"Failed to fetch PR context for {repo_url} PR #{pr_number}: {e}"
        logger.error(error_message)
        log_function_end(logger, "get_pr_context", success=False, error=error_message)
        raise GithubAPIError(error_message)