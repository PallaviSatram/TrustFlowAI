import json
import os

from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv()


def validate_repository(repo):
    """Validate a GitHub Repo in owner/repo format."""
    if not isinstance(repo, str):
        raise ValueError("Repository must be in owner/repo format.")
    
    repo = repo.strip()
    parts = repo.split("/")
    if (
        len(parts) != 2 
        or not all(parts) 
        or any(
            part in {".", ".."} 
            or not all(char.isalnum() or char in "-_." for char in part)
            for part in parts
        )
    ):
        raise ValueError("Invalid repository format. Use owner/repo.")
    return repo


def get_github_headers():
    """Generate standardized GitHub API headers, injecting token if present."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "TrustFlowAI",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def handle_github_http_error(error, context_message="GitHub API request failed"):
    """Convert HTTP status codes into specific, actionable RuntimeError messages."""
    status = error.code
    if status == 401:
        raise RuntimeError(
            f"{context_message}: HTTP 401 Unauthorized. Check your GITHUB_TOKEN."
        ) from error
    elif status == 403:
        raise RuntimeError(
            f"{context_message}: HTTP 403 Forbidden. Rate limit exceeded or insufficient permissions."
        ) from error
    elif status == 404:
        raise RuntimeError(
            f"{context_message}: HTTP 404 Not Found. Repository or resource does not exist or is private."
        ) from error
    elif status == 429:
        raise RuntimeError(
            f"{context_message}: HTTP 429 Too Many Requests. API rate limit hit."
        ) from error
    else:
        raise RuntimeError(
            f"{context_message}: GitHub API returned HTTP {status}."
        ) from error


def get_recent_workflow_runs(repo, service=None):
    """Fetch recent workflow runs for a repository."""
    repo = validate_repository(repo)
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=10"
    request = Request(url, headers=get_github_headers())
    
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        handle_github_http_error(error, "Failed to fetch workflow runs")
    except URLError as error:
        raise RuntimeError("Could not connect to the GitHub API.") from error
        
    runs = []
    for run in data.get("workflow_runs", []):
        runs.append({
            "run_id": run["id"],
            "name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "branch": run["head_branch"],
            "url": run["html_url"],
        })
    return runs
        

def get_workflow_jobs(run_id, repo):
    """Fetch jobs for a specific GitHub Actions workflow run."""
    repo = validate_repository(repo)
    
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise ValueError("run_id must be a positive integer.")
    
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    request = Request(url, headers=get_github_headers())
    
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        handle_github_http_error(error, "Failed to fetch workflow jobs")
    except URLError as error:
        raise RuntimeError("Could not connect to GitHub API.") from error
    
    jobs = []
    for job in data.get("jobs", []):
        jobs.append({
            "job_id": job["id"],
            "name": job["name"],
            "status": job["status"],
            "conclusion": job["conclusion"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "url": job["html_url"],
        })
    return jobs


def get_workflow_job_logs(job_id, repo):
    """Retrieve plain-text logs for a GitHub Actions job."""
    repo = validate_repository(repo)
    
    if not isinstance(job_id, int) or isinstance(job_id, bool) or job_id <= 0:
        raise ValueError("job_id must be a positive integer.")
    
    url = f"https://api.github.com/repos/{repo}/actions/jobs/{job_id}/logs"
    request = Request(url, headers=get_github_headers())
    
    class NoRedirectHandler(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
        
    opener = build_opener(NoRedirectHandler)
    
    try:
        try:
            with opener.open(request, timeout=20) as response:
                logs = response.read().decode("utf-8", errors="replace")
        except HTTPError as error:
            if error.code != 302:
                raise
            downloaded_url = error.headers.get("Location")
            
            if not downloaded_url:
                raise RuntimeError("GitHub returned a redirect without a download URL.")
            
            # Request log download (unauthenticated or with basic token if needed)
            with urlopen(downloaded_url, timeout=20) as response:
                logs = response.read().decode("utf-8", errors="replace")
            
    except HTTPError as error:
        handle_github_http_error(error, "GitHub log request failed")
    except (URLError, TimeoutError) as error:
        raise RuntimeError("Could not retrieve GitHub Actions job logs.") from error

    if not logs.strip():
        return "No log content was returned for this job"
    
    return logs