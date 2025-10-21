"""
Test script for Barkota Locations/Routes API
Correct endpoint: /ob/routes/passageenabled
"""
import requests
import json

url = "https://barkota-reseller-php-prod-4kl27j34za-uc.a.run.app/ob/routes/passageenabled"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://booking.barkota.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

payload = {
    "companyId": None
}

print("Testing Barkota Routes/Locations API...")
print(f"URL: {url}")
print(f"Method: POST")
print("-" * 50)

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ API test successful!")
        print(f"Total routes: {len(data) if isinstance(data, list) else 'N/A'}")
        
        # Extract unique locations
        unique_locations = set()
        if isinstance(data, list):
            for route in data:
                if 'origin' in route:
                    unique_locations.add(route['origin']['name'])
                if 'destinations' in route:
                    for dest in route['destinations']:
                        unique_locations.add(dest['name'])
        
        print(f"Total unique locations: {len(unique_locations)}")
        print(f"\nFirst 3 routes:")
        
        if isinstance(data, list):
            for i, route in enumerate(data[:3]):
                print(f"\n{i+1}. {json.dumps(route, indent=2)}")
        else:
            print(json.dumps(data, indent=2)[:500] + "...")
    else:
        print(f"✗ API returned status {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"✗ API test failed: {e}")
