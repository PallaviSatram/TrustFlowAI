
import json
import os

from dotenv import load_dotenv
from google import genai

from tools import list_failed_builds
from pydantic import ValidationError
from validation import RequestResult

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

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    return json.loads(response.text)


def handle_request(user_request):
    """Validate the AI result and run the appropriate Python tool."""
    result = understand_request(user_request)

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

    # Run our existing Python function
    failed_builds = list_failed_builds(service)

    if not failed_builds:
        print("\nNo failed builds found for that request.")
        return

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
