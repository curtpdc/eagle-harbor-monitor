"""
Test script to verify AI chat works in production
"""
import requests
import json
import time

API_BASE = "https://eagleharbor-api.azurewebsites.net"

def test_ai_chat(question):
    """Test AI chat endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing question: {question}")
    print(f"{'='*60}\n")
    
    url = f"{API_BASE}/api/chat"
    payload = {"question": question}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!\n")
            print(f"Answer: {data.get('answer', 'No answer')[:500]}...")
            print(f"\nSources: {len(data.get('sources', []))} sources")
            print(f"Confidence: {data.get('confidence', 0)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Waiting for backend to finish deploying...")
    time.sleep(30)  # Wait for deployment
    
    # Test questions
    questions = [
        "What happened at the Planning Board meeting on January 29, 2026?",
        "What is CR-98-2025?",
        "What are the environmental concerns about data centers in Prince George's County?",
        "Tell me about the AR zoning changes for data centers"
    ]
    
    for question in questions:
        test_ai_chat(question)
        time.sleep(2)  # Brief pause between tests
