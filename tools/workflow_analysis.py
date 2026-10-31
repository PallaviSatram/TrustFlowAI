from .github_actions import get_recent_workflow_runs, get_workflow_jobs
from .log_analysis import analyze_job_logs

def analyze_latest_failed_workflow():
  """Analyze the most recent failed GitHub Actions workflow."""
  
  runs = get_recent_workflow_runs()
  
  failed_runs = [
    run for run in runs
    if run["status"] == "completed" and 
    run["conclusion"] == "failure"
  ]
  
  if not failed_runs:
    return {
      "workflow": None,
      "jobs": [],
      "message": "No completed failed workflow runs found."
    }
  
  # Runs are returned newest first by GitHub's API
  workflow = failed_runs[0]
  jobs = get_workflow_jobs(workflow["run_id"])
  
  analyzed_jobs = [
    analyze_job_logs(job)
    for job in jobs
    if (
      job["conclusion"] == "failure" or 
      job["status"] == "completed"
    )
  ]
  
  return {
    "workflow" : workflow,
    "jobs" : analyzed_jobs,
    "message": None,
  }