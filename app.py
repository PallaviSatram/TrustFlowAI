import logging

from understand_request import understand_request
from tools.workflow_analysis import analyze_latest_failed_workflow

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
    "analyze_latest_failed_workflow": analyze_latest_failed_workflow,
}

logger = logging.getLogger(__name__)
# creates a logger associated with this python module
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
        if action == "analyze_latest_failed_workflow":
            tool_result = tool_function()
        else:
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
            
    elif action == "analyze_latest_failed_workflow":
        if not tool_result["workflow"]:
            logger.info(tool_result["message"])
            print(f"\n{tool_result['message']}")
            return
        
        workflow = tool_result["workflow"]
        jobs = tool_result["jobs"]
        
        logger.info("Analyzed failed workflow run %s.", workflow["run_id"])
        
        print("\nTrustFlow AI — Workflow Analysis")
        print(f"\nWorkflow: {workflow['name']}")
        print(f"Run ID: {workflow['run_id']}")
        print(f"Status: {workflow['status']}")
        print(f"Conclusion: {workflow['conclusion']}")
        print(f"Branch: {workflow['branch']}")
        print(f"URL: {workflow['url']}")
        
        if not jobs:
            print("\nNo jobs were available to analyze.")
            return
        
        for job in jobs:
            print(f"\n{'=' * 50}")
            print(f"Job: {job['job_name']}")
            print(f"Status: {job['status']}")
            print(f"Conclusion: {job['conclusion'] or 'Not completed'}")

            if not job["needs_analysis"]:
                print("\nNo failure analysis needed for this job.")
                continue

            if job["context"]:
                print("\nFailure Context:")
                print(job["context"])

            explanation = job["explanation"]

            if explanation:
                print("\nLikely Cause:")
                print(explanation["likely_cause"])

                print("\nEvidence:")
                for item in explanation["evidence"]:
                    print(f"- {item}")

                print("\nSuggested Fix:")
                print(explanation["suggested_fix"])

                print(
                    f"\nConfidence: "
                    f"{explanation['confidence'].upper()}"
                )

        


if __name__ == "__main__":
    request = input("TrustFlow AI — Enter a developer request: ")
    try:
        handle_request(request)
    except Exception as error:
        print("\nSomething went wrong:", error)
