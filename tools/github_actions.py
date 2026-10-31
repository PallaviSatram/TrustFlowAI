import json
import os

from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv

load_dotenv()

def get_recent_workflow_runs(service=None):
    """Fetch recent workflow runs for the TrustFlow AI GitHub repository."""
    
    url = (
        "https://api.github.com/repos/"
        "PallaviSatram/TrustFlowAI/actions/runs?per_page=5"
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
        
def get_workflow_jobs(run_id):
    """Fetch jobs for a specific GitHub Actions workflow run."""
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise ValueError("run_id must be a positive integer.")
    
    url = (
        "https://api.github.com/repos/"
        f"PallaviSatram/TrustFlowAI/actions/runs/{run_id}/jobs"
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

def get_workflow_job_logs(job_id):
    """Retrieve plain-text logs for a GitHub Actions job."""
    
    token = os.getenv("GITHUB_TOKEN")
    
    if(
        not isinstance(job_id, int) or
        isinstance(job_id, bool) or
        job_id <= 0
    ):
        raise ValueError("job_id must be a positive integer.")
    
    url = (
        "https://api.github.com/repos/"
        "PallaviSatram/TrustFlowAI/actions/jobs/"
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