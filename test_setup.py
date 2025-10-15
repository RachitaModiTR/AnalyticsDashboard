#!/usr/bin/env python3
"""
Test script to verify the Datadog Analytics Dashboard setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment setup"""
    print("🔍 Testing environment setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Check required variables
    client_token = os.getenv('DD_CLIENT_TOKEN')
    site = os.getenv('DD_SITE', 'datadoghq.com')
    
    print(f"✅ DD_CLIENT_TOKEN: {'Set' if client_token else '❌ Missing'}")
    print(f"✅ DD_SITE: {site}")
    
    if not client_token:
        print("\n❌ DD_CLIENT_TOKEN is required!")
        print("Please set it in your .env file:")
        print("DD_CLIENT_TOKEN=your_client_token_here")
        return False
    
    return True

def test_imports():
    """Test if all required packages can be imported"""
    print("\n🔍 Testing package imports...")
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import plotly
        print(f"✅ Plotly: {plotly.__version__}")
    except ImportError as e:
        print(f"❌ Plotly import failed: {e}")
        return False
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    try:
        from config import Config
        print("✅ Config module imported successfully")
        
        # Test validation
        try:
            Config.validate_config()
            print("✅ Configuration validation passed")
        except ValueError as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Datadog Analytics Dashboard - Setup Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Make sure your .env file has your DD_CLIENT_TOKEN")
        print("2. Run: python run.py")
        print("3. Open: http://localhost:5001")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
