import pytest
from tools import workflow_analysis


def test_latest_failed_workflow_is_analyzed(monkeypatch):
  # Arrange: simulate recent workflow runs.
    fake_runs = [
        {
            "run_id": 101,
            "name": "TrustFlow AI Tests",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "run_id": 102,
            "name": "TrustFlow AI Tests",
            "status": "completed",
            "conclusion": "failure",
        },
    ]

    fake_jobs = [
        {
            "name": "test",
            "status": "completed",
            "conclusion": "failure",
        }
    ]

    analyzed_job = {
        "job_name": "test",
        "needs_analysis": True,
        "failure_context": ["AssertionError: test failed"],
        "explanation": {
            "likely_cause": "An assertion failed",
            "evidence": "AssertionError",
            "suggested_fix": "Review the failing assertion",
            "confidence": "high",
        },
    }

    monkeypatch.setattr(
        workflow_analysis,
        "get_recent_workflow_runs",
        lambda: fake_runs,
    )

    requested_run_ids = []

    def fake_get_workflow_jobs(run_id):
        requested_run_ids.append(run_id)
        return fake_jobs

    monkeypatch.setattr(
        workflow_analysis,
        "get_workflow_jobs",
        fake_get_workflow_jobs,
    )

    analyzed_jobs = []

    def fake_analyze_job_logs(job):
        analyzed_jobs.append(job)
        return analyzed_job

    monkeypatch.setattr(
        workflow_analysis,
        "analyze_job_logs",
        fake_analyze_job_logs,
    )

    # Act
    result = workflow_analysis.analyze_latest_failed_workflow()

    # Assert
    assert result["workflow"]["run_id"] == 102
    assert requested_run_ids == [102]
    assert result["jobs"] == [analyzed_job]
    assert analyzed_jobs == fake_jobs
    assert result["message"] is None
    
def test_no_failed_workflow_returns_helpful_message(monkeypatch):
    monkeypatch.setattr(
        workflow_analysis,
        "get_recent_workflow_runs",
        lambda: [
            {
                "run_id": 201,
                "status": "completed",
                "conclusion": "success",
            },
            {
                "run_id": 202,
                "status": "in_progress",
                "conclusion": None,
            },
        ],
    )

    def unexpected_job_call(run_id):
        pytest.fail("Jobs should not be fetched when no failed workflow exists")

    monkeypatch.setattr(
        workflow_analysis,
        "get_workflow_jobs",
        unexpected_job_call,
    )

    result = workflow_analysis.analyze_latest_failed_workflow()

    assert result["workflow"] is None
    assert result["jobs"] == []
    assert result["message"] == "No completed failed workflow runs found."
    
def test_workflow_jobs_are_filtered_before_analysis(monkeypatch):
    monkeypatch.setattr(
        workflow_analysis,
        "get_recent_workflow_runs",
        lambda: [
            {
                "run_id": 303,
                "status": "completed",
                "conclusion": "failure",
            }
        ],
    )

    fake_jobs = [
        {
            "name": "failed-test",
            "status": "completed",
            "conclusion": "failure",
        },
        {
            "name": "successful-test",
            "status": "completed",
            "conclusion": "success",
        },
        {
            "name": "running-test",
            "status": "in_progress",
            "conclusion": None,
        },
    ]

    monkeypatch.setattr(
        workflow_analysis,
        "get_workflow_jobs",
        lambda run_id: fake_jobs,
    )

    analyzed_job_names = []

    def fake_analyze_job_logs(job):
        analyzed_job_names.append(job["name"])
        return {"job_name": job["name"]}

    monkeypatch.setattr(
        workflow_analysis,
        "analyze_job_logs",
        fake_analyze_job_logs,
    )

    result = workflow_analysis.analyze_latest_failed_workflow()

    assert analyzed_job_names == ["failed-test", "successful-test"]
    assert result["jobs"] == [
        {"job_name": "failed-test"},
        {"job_name": "successful-test"},
    ]

