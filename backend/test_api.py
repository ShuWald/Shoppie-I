import requests
import json

try:
    response = requests.get('http://localhost:8000/api/health')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    response2 = requests.get('http://localhost:8000/api/evaluate-trending-products')
    print(f"\nMain API Status Code: {response2.status_code}")
    print(f"Main API Response: {response2.text[:500]}...")
    
except Exception as e:
    print(f"Error: {e}")
