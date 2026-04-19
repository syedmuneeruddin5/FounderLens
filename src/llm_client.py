
# Sample LLM client for testing
import requests
import os
from dotenv import load_dotenv
import pprint

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

pprint.pprint(response.json(), indent=2)