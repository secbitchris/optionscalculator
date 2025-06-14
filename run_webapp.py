#!/usr/bin/env python3
"""
Run the Options Analysis Web Application

Simple script to start the Flask web app with proper error handling.
"""

import os
import sys
import argparse
from app import app

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Options Analysis Web Application')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on (default: 5001)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    print("🚀 Starting Options Analysis Web Application")
    print("=" * 50)
    
    # Check if data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
        print("✅ Created data directory")
    
    # Check for .env file
    if os.path.exists('.env'):
        print("✅ Found .env file")
    else:
        print("⚠️  No .env file found - running in offline mode")
    
    print(f"\n🌐 Web application will be available at:")
    print(f"   http://localhost:{args.port}")
    print(f"   http://127.0.0.1:{args.port}")
    
    print(f"\n📋 Features available:")
    print(f"   • Live SPY/SPX options analysis")
    print(f"   • Real-time price fetching (if API key configured)")
    print(f"   • IV calculator")
    print(f"   • Price scenario analysis")
    print(f"   • Greeks comparison")
    print(f"   • Save/export results")
    
    print(f"\n🔧 To stop the server: Press Ctrl+C")
    print("=" * 50)
    
    try:
        # Run the Flask app
        app.run(debug=True, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print(f"\n\n👋 Web application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting web application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 