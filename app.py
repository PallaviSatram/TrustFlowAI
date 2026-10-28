import logging
import json
import os

from dotenv import load_dotenv
from google import genai

from tools import list_failed_builds
from pydantic import ValidationError
from validation import RequestResult

logging.basicConfig(
    level=logging.INFO, # records informational events and more serious warnings or errors
    format="%(asctime)s - %(levelname)s - %(message)s",
    # includes the timestamp, severity level, and message.
)

logger = logging.getLogger(__name__)
# creates a logger associated with this python module

# Load the API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise SystemExit("Error: Gemini API key not found in .env")

client = genai.Client(api_key=api_key)

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

    Read the developer request and return a JSON object with:
    - action
    - service

    The only supported action is list_failed_builds.

    If the request asks to list failed builds:
    - action must be "list_failed_builds"
    - service must be the service name if mentioned, otherwise null

    For unrelated requests:
    - action must be "unknown"
    - service must be null

    Developer request: {user_request}
    """
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

    # Only allow actions our application supports
    if action != "list_failed_builds":
        print("\nSorry, TrustFlow AI does not support that request yet.")
        return

    # Only accept known service names
    allowed_services = {"payment-service", "user-service"}

    if service is not None and service not in allowed_services:
        print("\nUnknown service. Please specify payment-service or user-service.")
        return
    
    logger.info("Executing tool: list_failed_builds")
    # Run our existing Python function
    try:
        logger.info("Executing tool: list_failed_builds")
        failed_builds = list_failed_builds(service)
    except ValueError:
        logger.exception("Failed to retrieve failed builds")
        print("\nCould not retrieve failed builds. Please check the service and try again.")
        return

    if not failed_builds:
        logger.info("Tool completed: no failed builds found.")
        print("\nNo failed builds found for that request.")
        return
    
    logger.info("Tool completed: found %d failed build(s).", len(failed_builds))
    print("\nFailed builds found:")

    for build in failed_builds:
        print(f"\nBuild ID: {build['build_id']}")
        print(f"Service: {build['service']}")
        print(f"Error: {build['error']}")


if __name__ == "__main__":
    request = input("TrustFlow AI — Enter a developer request: ")
    try:
        handle_request(request)
    except Exception as error:
        print("\nSomething went wrong:", error)
