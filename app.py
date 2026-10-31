import logging
import json
import os

from dotenv import load_dotenv
from google import genai

from tools import (
ALLOWED_SERVICES, 
list_failed_builds,
get_deploy_status,
get_recent_workflow_runs,
)

from pydantic import ValidationError
from validation import RequestResult

logging.basicConfig(
    level=logging.INFO, # records informational events and more serious warnings or errors
    format="%(asctime)s - %(levelname)s - %(message)s",
    # includes the timestamp, severity level, and message.
)

TOOL_REGISTRY = {
    "list_failed_builds": list_failed_builds,
    "get_deploy_status": get_deploy_status,
    "get_recent_workflow_runs": get_recent_workflow_runs,
}

logger = logging.getLogger(__name__)
# creates a logger associated with this python module

# Load the API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")



client = genai.Client(api_key=api_key) if api_key else None

def normalize_service(service):
    """Convert short service names into the names used by our data."""
    if not service:
        return None

    service = service.strip().lower().replace(" ", "-")

    aliases = {
        "payment": "payment-service",
        "payment-service": "payment-service",
        "user": "user-service",
        "user-service": "user-service",
    }

    return aliases.get(service, service)


def understand_request(user_request):
    """Ask Gemini to identify the intended action and service."""
    prompt = f"""
    You are the request-understanding assistant for TrustFlow AI.

    Read the developer's request and return a JSON object with:
    - action
    - service

    Supported actions:

    1. list_failed_builds
    Use this when the developer asks to list or show failed builds.
    2. get_deploy_status 
    Use this when the developer asks for the deployment status or deployment version of a service. 
    3. get_recent_workflow_runs
    Use this when the developer asks to:
    - Show recent GitHub Actions workflow runs.
    - List successful or failed workflow runs.
    - Check the status of recent CI runs.
    For this action, set service to null.

    For either supported action:
    - Set action to the appropriate action name.
    - Set service to "payment-service" or "user-service"
    if the service is mentioned.
    - Set service to null if no service is mentioned.

    For unrelated requests:
    - Set action to "unknown".
    - Set service to null.

    Return only the JSON object.

    Developer request: {user_request}
    """
    if client is None:
        raise RuntimeError(
        "Gemini API key is missing. Add GEMINI_API_KEY to your .env file."
        )
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
    except Exception as error:
        raise RuntimeError("Gemini API request failed.") from error
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini returned an invalid JSON response"
        ) from error


def handle_request(user_request):
    """Validate the AI result and run the appropriate Python tool."""
    
    logger.info("Processing a developer request.")
    try:
        result = understand_request(user_request)
    # represents a failed API Request
    except RuntimeError as error:
        print(f"\nCould not get a response from Gemini: {error}")
        return
    # represents an Invalid JSON response
    except ValueError as error:
        print(f"\nCould not understand the AI response: {error}")
        return

    try:
        validated_result = RequestResult.model_validate(result)
    except ValidationError as error:
        print("\nGemini returned an invalid response.")
        print(error)
        return

    action = validated_result.action
    service = validated_result.service
    
    tool_function = TOOL_REGISTRY.get(action)
    
    # Only allow actions our application supports
    if tool_function is None:
        print("\nSorry, TrustFlow AI does not support that request yet.")
        return

    if service is not None and service not in ALLOWED_SERVICES:
        print("\nUnknown service. Please specify payment-service or user-service.")
        return
    
    # A deployment-status request requires a specific service.
    if action == "get_deploy_status" and service is None:
        print("\nPlease specify a service: payment-service or user-service.")
        return

    # Execute the selected tool.
    try:
        logger.info("Executing tool: %s", action)
        tool_result = tool_function(service)
    except (ValueError, RuntimeError):
        logger.exception("Tool execution failed for action: %s", action)
        print("\nCould not complete the request. Please check the service or try again later.")
        return
    
    # Format the result according to the selected action.
    if action == "list_failed_builds":
        if not tool_result:
            logger.info("Tool completed: no failed builds found.")
            print("\nNo failed builds found for that request.")
            return
    
        logger.info("Tool completed: found %d failed build(s).", len(tool_result))
        print("\nFailed builds found:")

        for build in tool_result:
            print(f"\nBuild ID: {build['build_id']}")
            print(f"Service: {build['service']}")
            print(f"Error: {build['error']}")
            
    elif action == "get_deploy_status":
        if tool_result is None:
            logger.info("Tool completed: no deployment record found.")
            print("\nNo deployment information found for that service.")
            return

        logger.info(
            "Tool completed: deployment status retrieved for %s.",
            service,
        )

        print("\nDeployment Status:")
        print(f"Service: {tool_result['service']}")
        print(f"Status: {tool_result['status']}")
        print(f"Version: {tool_result['version']}")
    elif action == "get_recent_workflow_runs":
        if not tool_result:
            logger.info("No GitHub Actions workflow runs found.")
            print("\nNo GitHub Actions workflow runs found.")
            return

        logger.info(
            "Retrieved %d GitHub Actions workflow run(s).",
            len(tool_result),
        )

        print("\nRecent GitHub Actions Workflow Runs:")

        for run in tool_result:
            print(f"\nWorkflow: {run['name']}")
            print(f"Run ID: {run['run_id']}")
            print(f"Status: {run['status']}")
            print(f"Conclusion: {run['conclusion'] or 'Not completed'}")
            print(f"Branch: {run['branch']}")
            print(f"URL: {run['url']}")


if __name__ == "__main__":
    request = input("TrustFlow AI — Enter a developer request: ")
    try:
        handle_request(request)
    except Exception as error:
        print("\nSomething went wrong:", error)
