"""Test event API endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_upcoming_events():
    print("Testing /events/upcoming...")
    response = requests.get(f"{BASE_URL}/events/upcoming", params={"days": 90})
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_timeline():
    print("Testing /events/timeline...")
    response = requests.get(f"{BASE_URL}/events/timeline", params={"days_back": 180})
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

if __name__ == "__main__":
    test_upcoming_events()
    test_timeline()
