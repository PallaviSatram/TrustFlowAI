from tools import list_failed_builds, get_deploy_status
import pytest

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