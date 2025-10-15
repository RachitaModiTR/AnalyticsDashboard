#!/usr/bin/env python3
"""
Test script to verify Datadog API keys
"""

import requests
from config import Config

def test_datadog_api():
    """Test if Datadog API keys are working"""
    
    print("🔑 Testing Datadog API Keys...")
    print(f"API Key: {Config.DD_API_KEY[:8]}...")
    print(f"Application Key: {Config.DD_APPLICATION_KEY[:8]}...")
    print(f"Site: {Config.DD_SITE}")
    
    # Test 1: Check if we can authenticate
    print("\n📡 Test 1: Authentication Test")
    url = f"https://api.{Config.DD_SITE}/api/v1/validate"
    headers = {
        'DD-API-KEY': Config.DD_API_KEY,
        'DD-APPLICATION-KEY': Config.DD_APPLICATION_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authentication successful!")
            data = response.json()
            print(f"Valid: {data.get('valid', 'Unknown')}")
        else:
            print(f"❌ Authentication failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Try to get available metrics
    print("\n📊 Test 2: Available Metrics Test")
    url = f"https://api.{Config.DD_SITE}/api/v1/metrics"
    params = {
        'from': 1640995200  # Jan 1, 2022
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', [])
            print(f"✅ Found {len(metrics)} metrics in your account")
            if metrics:
                print("Sample metrics:", metrics[:5])
            else:
                print("ℹ️  No metrics found - this is normal for new accounts")
        else:
            print(f"❌ Failed to get metrics: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Try to send a test metric
    print("\n📈 Test 3: Send Test Metric")
    url = f"https://api.{Config.DD_SITE}/api/v1/series"
    
    test_data = {
        "series": [
            {
                "metric": "test.dashboard.connection",
                "points": [[1640995200, 42]],
                "type": "gauge",
                "host": "test-host",
                "tags": ["test:true"]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 202:
            print("✅ Successfully sent test metric!")
        else:
            print(f"❌ Failed to send metric: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_datadog_api()


