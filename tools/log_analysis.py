from .github_actions import get_workflow_job_logs

def extract_failure_context(logs, context_lines=3):
    """Extract lines around likely failure messages."""
    lines = logs.splitlines()
    matches = []
    keywords = (
        "error",
        "failed",
        "failure",
        "traceback",
        "exception",
        "assertionerror",
    )
    
    for index, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in keywords):
            start = max(0, index - context_lines)
            end = min(len(lines), index + context_lines + 1)
            
            matches.append((start, end))
    if not matches:
        return "No obvious failure messages found in the logs."
    
    # Merge overlapping ranges to avoid duplicate lines.
    merged = []
    
    for start, end in matches:
        if merged and start <= merged[-1][1]:
            merged[-1] = (
                merged[-1][0],
                max(merged[-1][1], end)
            )
        
        else:
            merged.append((start, end))
    
    relevant_lines = []
    
    for start, end in merged:
        relevant_lines.extend(lines[start: end])
        relevant_lines.append("...")
        
    return "\n".join(relevant_lines)


def should_analyze_job(job, logs):
    """Decide whether a job's logs need further analysis."""

    status = (job.get("status") or "").lower()
    conclusion = (job.get("conclusion") or "").lower()

    # Failed jobs should always be investigated.
    if status == "completed" and conclusion == "failure":
        return True

    # Only inspect log indicators for successfully completed jobs.
    if status == "completed" and conclusion == "success":
        error_keywords = (
            "error",
            "exception",
            "traceback",
            "assertionerror",
        )
        logs_lower = logs.lower()
        
        return any(
            keyword in logs_lower
            for keyword in error_keywords
        )

    # Skip jobs that are still running or have another conclusion.
    return False


def analyze_job_logs(job):
    """Retrieve and extract log context when a job needs analysis."""

    logs = get_workflow_job_logs(job["job_id"])

    if not should_analyze_job(job, logs):
        return {
            "job_id": job["job_id"],
            "job_name": job.get("name"),
            "status": job.get("status"),
            "conclusion": job.get("conclusion"),
            "needs_analysis": False,
            "context": None,
        }

    context = extract_failure_context(logs)

    return {
        "job_id": job["job_id"],
        "job_name": job.get("name"),
        "status": job.get("status"),
        "conclusion": job.get("conclusion"),
        "needs_analysis": True,
        "context": context,
    }