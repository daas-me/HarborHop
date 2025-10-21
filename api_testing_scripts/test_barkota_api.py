"""
Test script for Barkota API integration
Run this to verify the API connection works
"""
import requests

url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/voyages/search/bylocation"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://booking.barkota.com",
    "Referer": "https://booking.barkota.com/"
}

payload = {
    "origin": 93,
    "destination": 96,
    "departureDate": "2025-10-22",
    "passengerCount": 1,
    "shippingCompany": None,
    "cargoItemId": None,
    "withDriver": 1
}

print("Testing Barkota API...")
print(f"Payload: {payload}")
print("-" * 50)

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(response.json())
    print("-" * 50)
    print("✓ API test successful!")
    
except requests.exceptions.RequestException as e:
    print(f"✗ API test failed: {e}")
