import tools.log_analysis as log_analysis

def test_extract_failure_context_finds_error():
  logs = (
    "Step 1: Setup\n"
    "Starting tests\n"
    "ERROR: Connection refused\n"
    "Step 3: Cleanup"
  )
  
  context = log_analysis.extract_failure_context(logs, context_lines=1)
  
  assert "ERROR: Connection refused" in context
  assert "Starting tests" in context
  
def test_extract_failure_context_when_no_error_exists():
  logs = "Build started\nBuild completed successfully"

  context = log_analysis.extract_failure_context(logs)

  assert context == "No obvious failure messages found in the logs."

def test_failed_job_need_analysis():
  job = {"status": "completed", "conclusion": "failure"}

  assert log_analysis.should_analyze_job(job, "Test failed") is True
def test_successful_job_with_warning_skips_analysis():
    job = {"status": "completed", "conclusion": "success"}
    logs = "WARNING: Deprecated configuration"

    assert log_analysis.should_analyze_job(job, logs) is False
    
def test_running_job_skips_analysis():
    job = {"status": "in_progress", "conclusion": None}

    assert log_analysis.should_analyze_job(job, "") is False
    
def test_successful_job_with_error_needs_analysis():
    job = {"status": "completed", "conclusion": "success"}
    logs = "ERROR: Something went wrong"

    assert log_analysis.should_analyze_job(job, logs) is True
    

def test_analyze_failed_job_returns_explanation(monkeypatch):
    monkeypatch.setattr(
        log_analysis,
        "get_workflow_job_logs",
        lambda job_id: "ERROR: Connection refused",
    )
    monkeypatch.setattr(
        log_analysis,
        "explain_job_issue",
        lambda job, context: {
            "likely_cause": "Database unavailable",
            "evidence": "ERROR: Connection refused",
            "suggested_fix": "Check the database service.",
            "confidence": "high",
        },
    )

    job = {
        "job_id": 123,
        "name": "integration-tests",
        "status": "completed",
        "conclusion": "failure",
    }

    result = log_analysis.analyze_job_logs(job)

    assert result["needs_analysis"] is True
    assert "ERROR: Connection refused" in result["context"]
    assert result["explanation"]["likely_cause"] == "Database unavailable"


def test_analyze_successful_warning_does_not_call_gemini(monkeypatch):
    monkeypatch.setattr(
        log_analysis,
        "get_workflow_job_logs",
        lambda job_id: "WARNING: Deprecated configuration",
    )

    def unexpected_gemini_call(job, context):
        raise AssertionError("Gemini should not be called for warnings")

    monkeypatch.setattr(
        log_analysis, "explain_job_issue", unexpected_gemini_call
    )

    job = {
        "job_id": 124,
        "name": "build",
        "status": "completed",
        "conclusion": "success",
    }

    result = log_analysis.analyze_job_logs(job)

    assert result["needs_analysis"] is False
    assert result["context"] is None
    assert result["explanation"] is None


def test_analyze_job_preserves_job_metadata(monkeypatch):
    monkeypatch.setattr(
        log_analysis,
        "get_workflow_job_logs",
        lambda job_id: "All checks passed",
    )

    job = {
        "job_id": 125,
        "name": "unit-tests",
        "status": "completed",
        "conclusion": "success",
    }

    result = log_analysis.analyze_job_logs(job)

    assert result["job_id"] == 125
    assert result["job_name"] == "unit-tests"
    assert result["status"] == "completed"
    assert result["conclusion"] == "success"
