# Test script so AIs can validate functionality / sanity testing

import requests
import json

try:
    response = requests.get('http://localhost:8000/api/evaluate-trending-products?page=1&page_size=10')
    print(f"\nMain API Status Code: {response.status_code}")
    print(f"Main API Response: {response.text[:500]}...")
    
except Exception as e:
    print(f"Error: {e}")
