#!/usr/bin/env python3
"""Script to verify that the setup is working correctly."""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    return True

def check_virtual_environment():
    """Check if running in virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Not running in virtual environment (recommended but not required)")
        return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'faiss',
        'langchain',
        'langgraph',
        'pydantic',
        'sqlalchemy',
        'asyncpg',
        'sentence_transformers',
        'pytest'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'faiss':
                __import__('faiss')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_environment_file():
    """Check if .env file exists."""
    if Path('.env').exists():
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found (copy from env.example)")
        return False

def check_project_structure():
    """Check if project structure is correct."""
    required_dirs = [
        'app',
        'app/api',
        'app/agents',
        'app/workflows',
        'app/tools',
        'app/models',
        'app/core',
        'tests',
        'data',
        'scripts'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - missing")
            all_exist = False
    
    return all_exist

def check_app_imports():
    """Check if app modules can be imported."""
    try:
        # Test basic imports
        from app.core.config import settings
        from app.models.chat import ChatRequest
        from app.tools.vector_store import vector_store
        print("✅ App modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ App import error: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🔍 Verifying AI Chat Agent setup...\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Environment File", check_environment_file),
        ("Project Structure", check_project_structure),
        ("App Imports", check_app_imports),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        if check_func():
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Setup verification completed successfully!")
        print("\nNext steps:")
        print("1. Configure .env file with your API keys and database credentials")
        print("2. Run: python scripts/setup_sample_data.py")
        print("3. Start the application: python start.py")
        return True
    else:
        print("❌ Setup verification failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 