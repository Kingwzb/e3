#!/usr/bin/env python3
"""Step-by-step setup script with better error handling."""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def install_basic_packages():
    """Install basic packages first."""
    basic_packages = [
        "wheel",
        "setuptools",
        "pip",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
    ]
    
    for package in basic_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_core_packages():
    """Install core web framework packages."""
    core_packages = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "httpx>=0.25.0",
        "pydantic-settings>=2.1.0",
    ]
    
    for package in core_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_database_packages():
    """Install database packages."""
    db_packages = [
        "sqlalchemy>=2.0.20",
        "asyncpg>=0.29.0",
    ]
    
    for package in db_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def install_ai_packages():
    """Install AI and ML packages."""
    ai_packages = [
        "numpy>=1.24.0",
        "openai>=1.3.0",
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.0",
    ]
    
    for package in ai_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, trying alternative...")
            if package.startswith("faiss-cpu"):
                # Try alternative FAISS installation
                if not run_command("pip install faiss-cpu --no-cache-dir", "Installing faiss-cpu (no cache)"):
                    print("❌ Could not install FAISS. You may need to install it manually.")
                    return False
            else:
                return False
    return True

def install_langchain_packages():
    """Install LangChain packages last."""
    langchain_packages = [
        "langchain>=0.1.0",
        "langgraph>=0.0.40",
    ]
    
    for package in langchain_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            # Try with older versions if newer ones fail
            if package.startswith("langchain"):
                if not run_command("pip install 'langchain>=0.0.339'", "Installing langchain (older version)"):
                    return False
            elif package.startswith("langgraph"):
                if not run_command("pip install 'langgraph>=0.0.19'", "Installing langgraph (older version)"):
                    return False
            else:
                return False
    return True

def install_test_packages():
    """Install testing packages."""
    test_packages = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
    ]
    
    for package in test_packages:
        if not run_command(f"pip install '{package}'", f"Installing {package}"):
            return False
    return True

def main():
    """Main setup function."""
    print("🚀 Starting step-by-step AI Chat Agent setup...")
    
    # Check if we're in a virtual environment
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print("❌ Please activate a virtual environment first!")
        print("Run: python3 -m venv venv && source venv/bin/activate")
        return False
    
    # Update pip first
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Failed to upgrade pip, continuing anyway...")
    
    # Install packages in groups
    installation_steps = [
        ("Basic packages", install_basic_packages),
        ("Core web framework", install_core_packages),
        ("Database packages", install_database_packages),
        ("AI and ML packages", install_ai_packages),
        ("LangChain packages", install_langchain_packages),
        ("Testing packages", install_test_packages),
    ]
    
    failed_steps = []
    for step_name, step_func in installation_steps:
        print(f"\n📦 Installing {step_name}...")
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ Failed to install {step_name}")
        else:
            print(f"✅ {step_name} installed successfully")
    
    if failed_steps:
        print(f"\n⚠️  Some packages failed to install: {', '.join(failed_steps)}")
        print("You may need to install them manually or check for compatibility issues.")
        return False
    
    # Create necessary directories and files
    print("\n📁 Setting up project structure...")
    
    # Create .env file
    if not Path('.env').exists():
        if Path('env.example').exists():
            run_command("cp env.example .env", "Creating .env file")
        else:
            print("⚠️  env.example not found, please create .env manually")
    
    # Create data directory
    Path('data/faiss_index').mkdir(parents=True, exist_ok=True)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Run: python verify_setup.py")
    print("3. Run: python scripts/setup_sample_data.py")
    print("4. Start the application: python start.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 