# Makefile for AI Chat Agent project

# Variables
VENV_NAME = venv
PYTHON = $(VENV_NAME)/bin/python
PIP = $(VENV_NAME)/bin/pip
ACTIVATE = source $(VENV_NAME)/bin/activate

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  setup     - Create virtual environment and install dependencies"
	@echo "  setup-dev - Setup with development dependencies"
	@echo "  verify    - Verify installation and setup"
	@echo "  install   - Install/update dependencies"
	@echo "  run       - Start the application"
	@echo "  dev       - Start in development mode with auto-reload"
	@echo "  test      - Run tests"
	@echo "  data      - Setup sample data"
	@echo "  update-docs - Update RAG vector database with documentation changes"
	@echo "  rebuild-docs - Rebuild RAG vector database from scratch"
	@echo "  watch-docs - Watch documentation files for changes and auto-update"
	@echo "  docs-stats - Show RAG vector database statistics"
	@echo "  clean     - Clean up virtual environment and cache"
	@echo "  lint      - Run code linting (if flake8 is installed)"
	@echo "  format    - Format code with black and isort"
	@echo "  check     - Check environment status"

# Setup virtual environment
.PHONY: setup
setup:
	@echo "🚀 Setting up AI Chat Agent project..."
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@if [ ! -f .env ]; then cp env.example .env; echo "✅ .env file created"; fi
	@mkdir -p data/faiss_index
	@echo "🎉 Setup completed! Run 'make verify' to check installation."

# Setup with development dependencies
.PHONY: setup-dev
setup-dev:
	@echo "🚀 Setting up AI Chat Agent project (development mode)..."
	python3 -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	@if [ ! -f .env ]; then cp env.example .env; echo "✅ .env file created"; fi
	@mkdir -p data/faiss_index
	@echo "🎉 Development setup completed! Run 'make verify' to check installation."

# Verify installation
.PHONY: verify
verify:
	$(ACTIVATE) && $(PYTHON) verify_setup.py

# Install dependencies
.PHONY: install
install:
	$(PIP) install -r requirements.txt

# Run the application
.PHONY: run
run:
	$(ACTIVATE) && $(PYTHON) start.py

# Run in development mode
.PHONY: dev
dev:
	$(ACTIVATE) && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
.PHONY: test
test:
	$(ACTIVATE) && $(PYTHON) scripts/run_tests.py

# Setup sample data
.PHONY: data
data:
	$(ACTIVATE) && $(PYTHON) scripts/setup_sample_data.py

# Documentation and RAG vector database management
.PHONY: update-docs
update-docs:
	$(ACTIVATE) && $(PYTHON) scripts/update_vector_db.py

.PHONY: rebuild-docs
rebuild-docs:
	$(ACTIVATE) && $(PYTHON) scripts/update_vector_db.py --rebuild

.PHONY: watch-docs
watch-docs:
	$(ACTIVATE) && $(PYTHON) scripts/watch_docs.py

.PHONY: docs-stats
docs-stats:
	$(ACTIVATE) && $(PYTHON) scripts/update_vector_db.py --stats

# Clean up
.PHONY: clean
clean:
	rm -rf $(VENV_NAME)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf data/faiss_index/*

# Lint code (optional)
.PHONY: lint
lint:
	$(ACTIVATE) && flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503 || echo "flake8 not installed, skipping lint"

# Format code (optional)
.PHONY: format
format:
	$(ACTIVATE) && black app/ tests/ scripts/ || echo "black not installed, skipping format"
	$(ACTIVATE) && isort app/ tests/ scripts/ || echo "isort not installed, skipping import sort"

# Check environment
.PHONY: check
check:
	@echo "Checking environment..."
	@$(ACTIVATE) && $(PYTHON) -c "import sys; print(f'Python: {sys.version}')"
	@$(ACTIVATE) && $(PYTHON) -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
	@$(ACTIVATE) && $(PYTHON) -c "import openai; print(f'OpenAI: {openai.__version__}')" || echo "OpenAI not available"
	@echo "✅ Environment check completed" 