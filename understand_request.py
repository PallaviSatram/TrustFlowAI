
import os
import json
from dotenv import load_dotenv
from google import genai

# Load the API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: Gemini API key not found.")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

# Get a request from the developer
user_request = input("Enter a developer request: ")

# Tell Gemini how to understand the request
prompt = f"""
You are the request-understanding assistant for TrustFlow AI.

Read the developer's request and identify:
1. The intended action.
2. The service name, if mentioned.

The only supported action is:
list_failed_builds

If the request asks to list failed builds:
- Set action to "list_failed_builds".
- Set service to the service name if mentioned.
- Otherwise, set service to null.

If the request is unrelated to listing failed builds:
- Set action to "unknown".
- Set service to null.

Return only a JSON object with these keys:
action, service

Developer request: {user_request}
"""

print("Sending one request to Gemini...", flush=True)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt,
    config={"response_mime_type": "application/json"}
)

# Convert Gemini's JSON response into Python data
result = json.loads(response.text)

# Normalize the service name to match our sample data
if result.get("service") == "payment":
    result["service"] = "payment-service"
elif result.get("service") == "user":
    result["service"] = "user-service"

print("\nGemini understood your request:")
print(json.dumps(result, indent=2))
