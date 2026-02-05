import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_google_places():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GOOGLE_API_KEY not found. Check your .env file.")
        return

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": "restaurants in New York",
        "key": api_key
    }

    response = requests.get(url, params=params, timeout=20)

    print("HTTP Status Code:", response.status_code)

    data = response.json()

    if "error_message" in data:
        print("Google API Error:", data["error_message"])
        return

    results = data.get("results", [])
    if not results:
        print("No results returned:", data)
        return

    first = results[0]
    print("Test call successful!")
    print("Name:", first.get("name"))
    print("Address:", first.get("formatted_address"))
    print("Rating:", first.get("rating"))

if __name__ == "__main__":
    test_google_places()
