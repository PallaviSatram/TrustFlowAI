import os
from dotenv import load_dotenv
from google import genai

# Read the API key from the .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
  print("Error: Gemini API key not found")
else:
  try:
    # Connect to Gemini
    print("Connecting to Gemini")
    client = genai.Client(api_key=api_key)

    # Send a test message
    print("Sending a test message....")
    response = client.models.generate_content(
      model="gemini-flash-latest",
      contents="Introduce yourself as the AI assistant for TrustFlow AI in one sentence."
    )

    print("Gemini connection successful!")
    print("Gemini's response:")
    print(response.text)

  except Exception as error:
    print("Gemini connection failed")
    print("Error details:", error)
