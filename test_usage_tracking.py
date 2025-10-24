"""
Test script for API usage tracking system
"""
import requests
import json
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE = 'http://localhost:8000'

print("=" * 80)
print("API Usage Tracking System Test")
print("=" * 80)

# Test 1: Get initial usage stats
print("\n1. Fetching initial usage stats...")
response = requests.get(f'{API_BASE}/api/usage')
if response.status_code == 200:
    usage_data = response.json()
    print(f"   ✓ Success! Date: {usage_data['date']}")
    print(f"   API Status Summary:")
    for api_name, api_data in usage_data['apis'].items():
        if api_data['limit']:
            print(f"     - {api_name}: {api_data['calls']}/{api_data['limit']} ({api_data['percent']}%) - {api_data['status']}")
        else:
            print(f"     - {api_name}: {api_data['calls']} calls (unlimited) - {api_data['status']}")
else:
    print(f"   ✗ Failed with status {response.status_code}")

# Test 2: Check cache stats
print("\n2. Fetching cache stats...")
response = requests.get(f'{API_BASE}/api/cache/stats')
if response.status_code == 200:
    cache_data = response.json()
    print(f"   ✓ Success!")
    print(f"     - Hit Rate: {cache_data.get('hit_rate_percent', 0)}%")
    print(f"     - Total Requests: {cache_data.get('total_requests', 0)}")
    print(f"     - Market Status: {cache_data.get('market_status', 'UNKNOWN')}")
else:
    print(f"   ✗ Failed with status {response.status_code}")

# Test 3: Trigger some API calls via portfolio endpoint
print("\n3. Triggering API calls via /api/portfolio...")
response = requests.get(f'{API_BASE}/api/portfolio')
if response.status_code == 200:
    portfolio = response.json()
    print(f"   ✓ Success!")
    print(f"     - Portfolio Value: ${portfolio['total_value']:.2f}")
    print(f"     - Positions: {len(portfolio['positions'])}")
else:
    print(f"   ✗ Failed with status {response.status_code}")

# Test 4: Check updated usage stats
print("\n4. Fetching updated usage stats...")
response = requests.get(f'{API_BASE}/api/usage')
if response.status_code == 200:
    usage_data = response.json()
    print(f"   ✓ Success!")
    print(f"   Updated API Status:")
    for api_name, api_data in usage_data['apis'].items():
        if api_data['calls'] > 0:  # Only show APIs that have been used
            if api_data['limit']:
                status_emoji = "🟢" if api_data['status'] == 'healthy' else "🟡" if api_data['status'] == 'warning' else "🔴"
                print(f"     {status_emoji} {api_name}: {api_data['calls']}/{api_data['limit']} ({api_data['percent']}%) - {api_data['status']}")
            else:
                print(f"     🔵 {api_name}: {api_data['calls']} calls (unlimited)")

    # Show cache stats
    if usage_data.get('cache'):
        cache = usage_data['cache']
        print(f"\n   Cache Performance:")
        print(f"     - Hit Rate: {cache.get('hit_rate', 0):.1f}%")
        print(f"     - Total Requests: {cache.get('total_requests', 0)}")
        print(f"     - Hits: {cache.get('hits', 0)} | Misses: {cache.get('misses', 0)}")
else:
    print(f"   ✗ Failed with status {response.status_code}")

# Test 5: Test warning/critical status detection
print("\n5. Simulating high usage for testing (modifying usage_tracker directly)...")
from api.usage_tracker import usage_tracker

# Simulate heavy alpha_vantage usage (warning threshold)
for _ in range(15):
    usage_tracker.increment("alpha_vantage")

# Simulate very heavy FMP usage (critical threshold)
for _ in range(210):
    usage_tracker.increment("fmp")

print("   ✓ Simulated usage:")
print(f"     - alpha_vantage: 15+ calls (should be WARNING at 60%+)")
print(f"     - fmp: 210+ calls (should be CRITICAL at 84%+)")

# Test 6: Verify warning/critical detection
print("\n6. Verifying warning/critical status detection...")
response = requests.get(f'{API_BASE}/api/usage')
if response.status_code == 200:
    usage_data = response.json()
    print(f"   ✓ Success!")

    warnings = []
    criticals = []

    for api_name, api_data in usage_data['apis'].items():
        if api_data['status'] == 'warning':
            warnings.append(f"{api_name}: {api_data['percent']}%")
        elif api_data['status'] == 'critical':
            criticals.append(f"{api_name}: {api_data['percent']}%")

    if warnings:
        print(f"   ⚠️  WARNING APIs detected:")
        for w in warnings:
            print(f"     - {w}")

    if criticals:
        print(f"   🚨 CRITICAL APIs detected:")
        for c in criticals:
            print(f"     - {c}")

    if not warnings and not criticals:
        print(f"   ℹ️  No warnings or critical status detected")
else:
    print(f"   ✗ Failed with status {response.status_code}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
print("\n📊 To view the dashboard, open: http://localhost:8000")
print("   Navigate to the 'System' tab to see the usage tracking UI")
print("=" * 80)
