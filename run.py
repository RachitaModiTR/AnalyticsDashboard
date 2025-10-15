#!/usr/bin/env python3
"""
Startup script for Datadog Analytics Dashboard (Application Key Version)
"""

import os
import sys
from config import Config

def main():
    """Main startup function"""
    try:
        # Validate configuration
        Config.validate_config()
        print("✅ Configuration validated successfully")
        
        # Import and run the app
        from app import app
        
        print("🚀 Starting Datadog Analytics Dashboard (Application Key)...")
        print(f"📊 Dashboard will be available at: http://localhost:5002")
        print(f"🔧 Environment: {Config.FLASK_ENV}")
        print(f"🐛 Debug mode: {Config.FLASK_DEBUG}")
        print(f"🔑 Using Application Key authentication")
        print(f"🌐 Datadog Site: {Config.DD_SITE}")
        print("\nPress Ctrl+C to stop the server")
        
        app.run(
            debug=Config.FLASK_DEBUG,
            host='0.0.0.0',
            port=5002  # Changed from 5001 to avoid port conflict
        )
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set:")
        print("- DD_API_KEY (required)")
        print("- DD_APPLICATION_KEY (required)")
        print("- DD_SITE (optional, defaults to datadoghq.com)")
        print("\nTo get your API and Application keys:")
        print("1. Go to your Datadog account")
        print("2. Navigate to Integrations > APIs")
        print("3. Create a new API Key and Application Key")
        sys.exit(1)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPlease install required dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
