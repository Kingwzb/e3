#!/usr/bin/env python3
"""Quick start script for the AI Chat Agent application."""

import os
import sys
import asyncio

def check_environment():
    """Check if environment is properly configured."""
    required_vars = []
    missing_vars = []
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. Please copy env.example to .env and configure it.")
        return False
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("❌ python-dotenv not installed. Please run: pip install -r requirements.txt")
        return False
    
    # Check required environment variables
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file configuration.")
        return False
    
    return True

def main():
    """Main function to start the application."""
    print("🚀 Starting AI Chat Agent...")
    
    # Check environment
    if not check_environment():
        print("\n📝 Setup instructions:")
        print("1. Copy env.example to .env: cp env.example .env")
        print("2. Edit .env file with your configuration")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run setup script: python scripts/setup_sample_data.py")
        print("5. Start the application: python start.py")
        sys.exit(1)
    
    # Import and run the application
    try:
        import uvicorn
        from app.core.config import settings
        
        print(f"✅ Configuration loaded successfully")
        print(f"🌐 Starting server on {settings.app_host}:{settings.app_port}")
        print(f"📚 API documentation will be available at http://{settings.app_host}:{settings.app_port}/docs")
        print(f"🔧 Debug mode: {settings.debug}")
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=settings.debug,
            log_level=settings.log_level.lower()
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 