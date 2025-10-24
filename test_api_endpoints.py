"""
Test API Endpoints - Quick verification script
Run this AFTER starting the API server
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, expected_status=200):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)

    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == expected_status:
            print("✅ SUCCESS")
            data = response.json()
            print("\nResponse:")
            print(json.dumps(data, indent=2, default=str))
            return True
        else:
            print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION FAILED - Is the server running?")
        print("\nStart the server with:")
        print("  python start_api.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 Project Tehama API - Endpoint Testing")
    print("="*60)

    # Check if server is running
    print("\nChecking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("✓ Server is running!")
    except:
        print("\n❌ Server is NOT running!")
        print("\nPlease start the server first:")
        print("  python start_api.py")
        print("\nOr:")
        print("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)

    # Test all endpoints
    results = []

    results.append(test_endpoint(
        "Health Check",
        f"{BASE_URL}/health"
    ))

    results.append(test_endpoint(
        "Portfolio Summary",
        f"{BASE_URL}/api/portfolio"
    ))

    results.append(test_endpoint(
        "AI Recommendations",
        f"{BASE_URL}/api/recommendations"
    ))

    results.append(test_endpoint(
        "Agent Status",
        f"{BASE_URL}/api/agents/status"
    ))

    results.append(test_endpoint(
        "Alerts",
        f"{BASE_URL}/api/alerts"
    ))

    results.append(test_endpoint(
        "Filtered Recommendations (pending)",
        f"{BASE_URL}/api/recommendations?status=pending"
    ))

    results.append(test_endpoint(
        "Limited Alerts (3)",
        f"{BASE_URL}/api/alerts?limit=3"
    ))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")

    print("\n" + "="*60)
    print("📖 Interactive Documentation")
    print("="*60)
    print(f"\nSwagger UI: {BASE_URL}/docs")
    print(f"ReDoc: {BASE_URL}/redoc")
    print()

if __name__ == "__main__":
    main()
