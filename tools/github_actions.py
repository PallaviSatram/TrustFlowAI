import json
import os

from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv()

def validate_repository(repo):
    """Validate a GitHub Repo in owe=ner/repo format."""
    
    if not isinstance(repo, str):
        raise ValueError("Repository must be in owner/repo format.")
    
    repo = repo.strip()
    parts = repo.split("/")
    if(len(parts) != 2 or not all(parts) or any(
        part in {".", ".."} or not all (
            char.isalnum() or char in "-_."
            for char in part
        )
        for part in parts
    )
    ):
        raise ValueError(
            "Invalid repository format. Use owner/repo."
        )
    return repo

def get_recent_workflow_runs(repo, service=None):
    """Fetch recent workflow runs for the TrustFlow AI GitHub repository."""
    
    repo = validate_repository(repo)
    
    url = (
        f"https://api.github.com/repos/{repo}"
        "/actions/runs?per_page=10"
    )
    
    request = Request(
        url,
        headers={
            "Accept":   "application/vnd.github+json",
            "User-Agent":   "TrustFlowAI",
        },
    )
    
    try:
        with urlopen(request, timeout=10) as response: # Contacts the GitHub API for your repository.
            
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(
            f"GitHub API returned HTTP {error.code}."
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to the GitHub API."
        ) from error
        
    runs = []
    # Extracts useful fields instead of returning the entire API response.
    for run in data.get("workflow_runs", []):
        runs.append({
            "run_id": run["id"],
            "name": run["name"],
            "status": run["status"],
            "conclusion": run["conclusion"],
            "branch": run["head_branch"],
            "url": run["html_url"]
        })
    
    return runs
        
def get_workflow_jobs(run_id, repo):
    """Fetch jobs for a specific GitHub Actions workflow run."""
    repo = validate_repository(repo)
    
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise ValueError("run_id must be a positive integer.")
    
    url = (
        f"https://api.github.com/repos/{repo}"
        f"/actions/runs/{run_id}/jobs"
        "?per_page=100"
    )
    
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "TrustFlowAI",
        },
    )
    
    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(
            f"GitHub API returned HTTP {error.code}."
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to GitHub API."
        ) from error
    
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
    
    token = os.getenv("GITHUB_TOKEN")
    
    if(
        not isinstance(job_id, int) or
        isinstance(job_id, bool) or
        job_id <= 0
    ):
        raise ValueError("job_id must be a positive integer.")
    
    url = (
        f"https://api.github.com/repos/{repo}"
        "/actions/jobs/"
        f"{job_id}/logs"
    )
    
    headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "TrustFlowAI",
    }
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    request = Request(
        url,
        headers = headers
    )
    
    class NoRedirectHandler(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
        
    opener = build_opener(NoRedirectHandler)
    
    try:
        try:
            with opener.open(request, timeout=20) as response:
                logs = response.read().decode("utf-8", errors="replace",)
        except HTTPError as error:
            if(error.code != 302):
                raise
            downloaded_url = error.headers.get("Location")
            
            if not downloaded_url:
                raise RuntimeError(
                    "GitHub returned a redirect without a download URL."
                )
            
            with urlopen(downloaded_url, timeout=20) as response:
                logs = response.read().decode(
                    "utf-8",
                    errors="replace"
                )
            
    except HTTPError as error:
        raise RuntimeError(
            f"GitHub log request failed with HTTP {error.code}."
        ) from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            "Could not retrieve GitHub Actions job logs."
        ) from error

        
    if not logs.strip():
        return "No log content was returned for this job"
    
    return logs