@echo off
REM Setup script for AI Chat Agent project (Windows)

echo 🚀 Setting up AI Chat Agent project...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%

REM Create virtual environment
set VENV_NAME=venv
if not exist "%VENV_NAME%" (
    echo 📦 Creating virtual environment...
    python -m venv %VENV_NAME%
    echo ✅ Virtual environment created in ./%VENV_NAME%
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env file from example...
    copy env.example .env
    echo ✅ .env file created. Please edit it with your configuration.
) else (
    echo ✅ .env file already exists
)

REM Create data directory
echo 📁 Creating data directories...
if not exist "data\faiss_index" mkdir data\faiss_index

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Activate the virtual environment: venv\Scripts\activate.bat
echo 2. Edit .env file with your configuration (OpenAI API key, database credentials)
echo 3. Setup sample data: python scripts\setup_sample_data.py
echo 4. Start the application: python start.py
echo.
echo To run tests: python scripts\run_tests.py
echo To deactivate virtual environment: deactivate

pause 