from tools import list_failed_builds
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