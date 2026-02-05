import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_foursquare():
    token = os.getenv("FOURSQUARE_API_KEY")
    if not token:
        print("FOURSQUARE_API_KEY not found in .env")
        return

    url = "https://places-api.foursquare.com/places/search"
    headers = {
        "X-Places-Api-Version": "2025-06-17",
        "accept": "application/json",
        "authorization": f"Bearer {token}",
    }

    params = {
        "query": "restaurant",
        "near": "New York, NY",
        "limit": 1
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    print("HTTP Status Code:", r.status_code)

    try:
        data = r.json()
    except Exception:
        print("Non-JSON response:", r.text[:300])
        return

    if r.status_code != 200:
        print("Foursquare API Error:", data)
        return

    results = data.get("results", [])
    if not results:
        print("⚠️ No results returned:", data)
        return

    first = results[0]
    print("Test call successful!")
    print("Name:", first.get("name"))
    print("Address:", first.get("location", {}).get("formatted_address"))

if __name__ == "__main__":
    test_foursquare()
