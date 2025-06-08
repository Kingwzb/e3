#!/usr/bin/env python3
"""Script to run tests with proper setup."""

import subprocess
import sys
import os

def run_tests():
    """Run the test suite."""
    
    # Change to the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    print("Running AI Chat Agent test suite...")
    print(f"Project root: {project_root}")
    
    # Set environment variables for testing
    test_env = os.environ.copy()
    test_env.update({
        "PYTHONPATH": project_root,
        "OPENAI_API_KEY": "test-key-not-real",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "DEBUG": "True"
    })
    
    try:
        # Run pytest with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--asyncio-mode=auto"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=test_env, check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            
        return result.returncode
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code) 