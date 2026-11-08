from tools import list_failed_builds, get_deploy_status
import pytest
from tools.github_actions import get_github_headers, handle_github_http_error
from urllib.error import HTTPError
from unittest.mock import patch, MagicMock

def test_returns_only_failed_builds():
  result = list_failed_builds()
  
  assert len(result) == 2
  assert all(build["status"] == "failed" for build in result)

def test_filters_failed_builds_by_service():
  result = list_failed_builds("payment-service")
  
  assert len(result) == 2
  assert all(
    build["service"] == "payment-service"
    for build in result
  )
def test_returns_empty_list_for_service_without_failures():
  result = list_failed_builds("user-service")
  assert result == []
  
def test_rejects_unspported_service():
  with pytest.raises(ValueError, match="Unsupported service"):
    list_failed_builds("admin-service")

def test_returns_payment_deployment_status():
  result = get_deploy_status("payment-service")
  
  assert result["status"] == "deployed"
  assert result["version"] == "v1.4.2"
  
def test_returns_user_deployment_status():
    result = get_deploy_status("user-service")

    assert result["status"] == "in_progress"
    assert result["version"] == "v2.1.0"

def test_rejects_unsupported_service():
  with pytest.raises(ValueError, match="Unsupported service"):
    get_deploy_status("admin-service")
    
def test_get_github_headers_with_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake_test_token_123")
    headers = get_github_headers()
    assert headers["Authorization"] == "Bearer fake_test_token_123"
    assert headers["User-Agent"] == "TrustFlowAI"

def test_get_github_headers_without_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    headers = get_github_headers()
    assert "Authorization" not in headers

def test_handle_github_http_error_401():
    error = HTTPError(url="", code=401, msg="Unauthorized", hdrs={}, fp=None)
    with pytest.raises(RuntimeError, match="HTTP 401 Unauthorized"):
        handle_github_http_error(error)

def test_handle_github_http_error_404():
    error = HTTPError(url="", code=404, msg="Not Found", hdrs={}, fp=None)
    with pytest.raises(RuntimeError, match="HTTP 404 Not Found"):
        handle_github_http_error(error)