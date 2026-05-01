"""
Quick test script for chat API endpoint.
Tests that the backend returns proper hospital data with coordinates.
"""

import requests
import json
import sys

def test_chat_api():
    """Test the chat API endpoint for geospatial hospital data."""

    url = "http://localhost:8001/api/v1/chat"
    payload = {
        "message": "Find cardiac hospitals near Nagpur",
        "session_id": "test-session-001",
        "location": "Nagpur",
        "patient_profile": {
            "age": 45
        }
    }

    print("=" * 60)
    print("TESTING CHAT API ENDPOINT")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("-" * 60)

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"ERROR {response.status_code}: {response.text[:500]}")
        response.raise_for_status()

        data = response.json()

        print(f"Status: {response.status_code}")
        print("\nResponse Structure:")
        print(f"  - chat_response: {data.get('chat_response') is not None}")
        print(f"  - results_panel: {data.get('results_panel') is not None}")

        # Check geo_spatial data
        geo = data.get('results_panel', {}).get('geo_spatial')
        if geo:
            print(f"\n  ✓ geo_spatial: PRESENT")
            user_coords = geo.get('user_coords', {})
            print(f"    - User lat: {user_coords.get('lat')}")
            print(f"    - User lng: {user_coords.get('lng')}")
            print(f"    - City tier: {geo.get('city_tier')}")

            markers = geo.get('hospital_markers', [])
            print(f"    - Hospital markers: {len(markers)}")

            for i, marker in enumerate(markers[:3], 1):
                print(f"      {i}. {marker.get('name')} @ ({marker.get('lat')}, {marker.get('lng')}) - {marker.get('tier')}")
        else:
            print(f"\n  ✗ geo_spatial: MISSING")

        # Check hospitals in results_panel
        hospitals = data.get('results_panel', {}).get('hospitals', {}).get('hospitals', [])
        if hospitals:
            print(f"\n  ✓ hospitals: {len(hospitals)} found")
            for i, h in enumerate(hospitals[:3], 1):
                coords = h.get('coordinates', {})
                print(f"    {i}. {h.get('name')} @ ({coords.get('lat')}, {coords.get('lng')})")
        else:
            print(f"\n  ✗ hospitals: NONE")

        # Validation
        print("\n" + "=" * 60)
        print("VALIDATION")
        print("=" * 60)

        checks = []

        # Check 1: geo_spatial exists
        if geo:
            checks.append(("GeoSpatial data present", True))
        else:
            checks.append(("GeoSpatial data present", False))

        # Check 2: user coordinates valid
        if geo and user_coords.get('lat') and user_coords.get('lng'):
            lat = user_coords.get('lat')
            lng = user_coords.get('lng')
            valid = 20 < lat < 22 and 78 < lng < 80  # Nagpur range
            checks.append(("User coords in Nagpur range", valid))
        else:
            checks.append(("User coords in Nagpur range", False))

        # Check 3: hospital markers exist
        if geo and len(markers) > 0:
            checks.append(("Hospital markers generated", True))
        else:
            checks.append(("Hospital markers generated", False))

        # Check 4: hospitals have coordinates
        if hospitals and all(h.get('coordinates', {}).get('lat') for h in hospitals):
            checks.append(("All hospitals have coordinates", True))
        else:
            checks.append(("All hospitals have coordinates", False))

        for check, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: {check}")

        all_passed = all(p for _, p in checks)
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL CHECKS PASSED - Backend is ready for frontend!")
            return 0
        else:
            print("✗ SOME CHECKS FAILED - Review output above")
            return 1

    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend at localhost:8001")
        print("Make sure the backend server is running: python -m uvicorn main:app --host 0.0.0.0 --port 8001")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_chat_api())
