#!/bin/bash
# Setup script for AI Chat Agent project

set -e  # Exit on any error

echo "🚀 Setting up AI Chat Agent project..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
VENV_NAME="venv"
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv $VENV_NAME
    echo "✅ Virtual environment created in ./$VENV_NAME"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source $VENV_NAME/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
python3 setup_step_by_step.py

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from example..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists"
fi

# Create data directory
echo "📁 Creating data directories..."
mkdir -p data/faiss_index

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit .env file with your configuration (OpenAI API key, database credentials)"
echo "3. Setup sample data: python scripts/setup_sample_data.py"
echo "4. Start the application: python start.py"
echo ""
echo "To run tests: python scripts/run_tests.py"
echo "To deactivate virtual environment: deactivate" 