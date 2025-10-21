"""
Test the correct Barkota locations endpoint
Found via DevTools: /ob/routes/passageenabled
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

print("=" * 80)
print("Testing Barkota Routes/Locations API")
print("=" * 80)
print(f"URL: {url}")
print(f"Method: POST")
print(f"Payload: {json.dumps(payload)}")
print("-" * 80)

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API test successful!")
        print(f"Total items: {len(data) if isinstance(data, list) else 'N/A'}")
        
        if isinstance(data, list) and len(data) > 0:
            print(f"\nFirst 5 locations:")
            for i, location in enumerate(data[:5]):
                if isinstance(location, dict):
                    # Check if it's a route or location object
                    if 'origin' in location:
                        print(f"\n{i+1}. Route:")
                        print(f"   Origin: {location.get('origin', {}).get('name', 'N/A')}")
                        print(f"   Destination: {location.get('destination', {}).get('name', 'N/A')}")
                    else:
                        print(f"\n{i+1}. Location:")
                        print(f"   ID: {location.get('id')}")
                        print(f"   Code: {location.get('code')}")
                        print(f"   Name: {location.get('name')}")
                        print(f"   Province: {location.get('province')}")
            
            print(f"\n" + "-" * 80)
            print("Sample JSON structure:")
            print(json.dumps(data[0], indent=2))
        else:
            print(f"\nResponse: {json.dumps(data, indent=2)[:500]}...")
    else:
        print(f"✗ API returned status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"✗ API test failed: {e}")

print("\n" + "=" * 80)
