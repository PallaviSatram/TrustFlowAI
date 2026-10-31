import os
import json
from dotenv import load_dotenv
from google import genai

# Load the API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None

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
    4. analyze_latest_failed_workflow
    Use this when the developer asks to:
    - Analyze the latest failed GitHub Actions workflow.
    - Explain why a workflow or CI run failed.
    - Identify failed job errors and suggest fixes.
    For this action, set service to null.

    For any supported action:
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
        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        return json.loads(response.text)

    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "Gemini returned an invalid JSON response."
        ) from error
