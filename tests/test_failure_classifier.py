from tools.failure_classifier import classify_failure

def test_classifies_dependency_failure():
  context = "ModuleNotFoundError: No module named 'requests'"
  
  result = classify_failure(context)
  
  assert result["earliest_detected_category"] == "Dependency"
  assert result["matched_indicators"]
  
def test_classifies_test_failure():
  context = "AssertionError: Expected 200 but received 500"
  
  result = classify_failure(context)
  
  assert result["earliest_detected_category"] == "Test Failure"
  
def test_classifies_syntax_failure():
  context = "SyntaxError: invalid syntax"

  result = classify_failure(context)

  assert result["earliest_detected_category"] == "Code / Syntax"
  
def test_classifies_permission_failure():
    context = "PermissionError: Permission denied"

    result = classify_failure(context)

    assert result["earliest_detected_category"] == "Permission"


def test_classifies_network_failure():
    context = "Connection timed out"

    result = classify_failure(context)

    assert result["earliest_detected_category"] == "Infrastructure / Network"


def test_classifies_configuration_failure():
    context = "Invalid configuration detected"

    result = classify_failure(context)

    assert result["earliest_detected_category"] == "Configuration"


def test_unknown_failure():
    context = "Something unexpected happened"

    result = classify_failure(context)

    assert result["earliest_detected_category"] == "Unknown"
    assert result["matched_indicators"] == []


def test_empty_context():
    result = classify_failure("")

    assert result["earliest_detected_category"] == "Unknown"
    assert result["matched_indicators"] == []
    assert result["secondary_categories"] == []
    
def test_identifies_multiple_failure_indicators():
    context = """
    ModuleNotFoundError: No module named 'requests'
    AssertionError: Expected 200 but received 500
    Connection timed out
    """

    result = classify_failure(context)

    assert result["earliest_detected_category"] == "Dependency"

    assert "ModuleNotFoundError" in result["matched_indicators"]
    assert "AssertionError" in result["matched_indicators"]
    assert "Connection timed out" in result["matched_indicators"]

    assert "Test Failure" in result["secondary_categories"]
    assert "Infrastructure / Network" in result["secondary_categories"]
