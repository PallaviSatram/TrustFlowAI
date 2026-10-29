import app
import pytest


# unsupported requests are rejected before the build tool runs.
def test_unknown_action_does_not_execute_tool(monkeypatch, capsys):
  # simulate Gemini returning an unsupported request
  # monkeypatch - Think of it as temporarily changing a function for a test.
  # Pytest restores the patched attributes when the test finishes
  monkeypatch.setattr(
    app,
    "understand_request",
    lambda user_request: {
      "action" : "unknown",
      "service" : None,
    },
  )
  
  # If the tool is called, the test must fail
  def unexpected_tool_call(service=None):
    raise AssertionError("The tool should not have been executed!")

  monkeypatch.setitem(
    app.TOOL_REGISTRY,
    "list_failed_builds",
    unexpected_tool_call,
  )
  # Process the request.
  app.handle_request("Tell me a joke")
  # Check the message displayed by the application.
  output = capsys.readouterr().out
  assert "does not support that request yet" in output

# when Gemini returns malformed JSON, the JSON parsing error occurs before the build tool can execute.
def test_invalid_json_does_not_execute_tool(monkeypatch, capsys):
    import json

    class FakeResponse:
        text = "this is not valid JSON"

    monkeypatch.setattr(
        app.client.models,
        "generate_content",
        lambda **kwargs: FakeResponse(),
    )

    def unexpected_tool_call(service=None):
        raise AssertionError("The tool should not have been executed!")

    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "list_failed_builds",
        unexpected_tool_call,
    )

    app.handle_request("Show me failed builds")
    
    output = capsys.readouterr().out
    assert "Could not understand the AI response" in output

def test_gemini_api_failure_is_handled(monkeypatch, capsys):
  
    def simulate_api_failure(**kwargs):
        raise Exception("Simulated network failure")

    monkeypatch.setattr(
        app.client.models,
        "generate_content",
        simulate_api_failure,
    )

    def unexpected_tool_call(service=None):
        raise AssertionError("The tool should not have been executed!")

    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "list_failed_builds",
        unexpected_tool_call,
    )

    app.handle_request("Show me failed builds")

    output = capsys.readouterr().out
    assert "Could not get a response from Gemini" in output

def test_tool_execution_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(
        app,
        "understand_request",
        lambda user_request: {
            "action": "list_failed_builds",
            "service": "payment-service",
        },
    )

    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "list_failed_builds",
        lambda service=None: [
            {
                "build_id": 101,
                "service": "payment-service",
                "status": "failed",
                "error": "Database connection timeout",
            }
        ],
    )
    # caplog: captures log messages so the test can inspect them.
    # caplog.at_level("INFO"): captures informational logs and higher-severity messages.
    with caplog.at_level("INFO"):
        app.handle_request("Show failed payment builds")

    assert "Processing a developer request." in caplog.text
    assert "Executing tool: list_failed_builds" in caplog.text
    assert "Tool completed: found 1 failed build(s)." in caplog.text
    
def test_tool_error_is_handled_gracefully(monkeypatch, capsys):
    monkeypatch.setattr(
        app,
        "understand_request",
        lambda user_request: {
            "action": "list_failed_builds",
            "service": "payment-service",
        },
    )

    def simulate_tool_error(service=None):
        raise ValueError("Simulated tool failure")

    monkeypatch.setitem(
        app.TOOL_REGISTRY,
        "list_failed_builds",
        simulate_tool_error,
    )

    app.handle_request("Show failed payment builds")

    output = capsys.readouterr().out
    assert "Could not complete the request" in output

def test_unknown_action_does_not_select_a_tool():
    tool_function = app.TOOL_REGISTRY.get("unknown")

    assert tool_function is None
    
def test_deployment_status_is_displayed(monkeypatch, capsys):
    monkeypatch.setattr(
        app,
        "understand_request",
        lambda user_request : {
            "action": "get_deploy_status",
            "service": "payment-service",
        }
    )
    
    app.handle_request("show payment deployment status")
    
    output = capsys.readouterr().out
    
    assert "Deployment Status:" in output
    assert "payment-service" in output
    assert "deployed" in output
    assert "v1.4.2" in output


def test_deployment_status_requires_service(monkeypatch, capsys):
    # Simulate Gemini returning no service.
    monkeypatch.setattr(
        app,
        "understand_request",
        lambda user_request: {
            "action": "get_deploy_status",
            "service": None,
        },
    )

    app.handle_request("Show deployment status")

    output = capsys.readouterr().out

    assert "Please specify a service" in output

