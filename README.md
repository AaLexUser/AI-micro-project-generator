# Cherry AI Micro-Project Generator

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

An AI-powered tool that generates focused, bite-sized learning projects from issue descriptions. Perfect for creating targeted educational tasks that help students learn from their mistakes through practical, hands-on micro-projects.

## 🎯 What It Does

This tool transforms error descriptions or learning challenges into structured micro-projects with:

- **Task Description**: Clear, focused learning objectives
- **Success Criteria**: Measurable outcomes for completion
- **Expert Solution**: Reference implementation and guidance

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-micro-project-generator

# Install dependencies
uv sync

# Set up environment variables
cd aipg/configs
cp default.yaml.example default.yaml
# Edit default.yaml with your API keys
```

### Basic Usage

```bash
# Generate a micro-project from an issue description
uv run aipg "I keep mixing up Python list comprehensions with map/filter"

# Use custom configuration
uv run aipg --config-path custom.yaml "My function returns None instead of expected value"

# Override config values
uv run aipg -o llm.model_name="gpt-4" "Database connection fails with timeout"
```

## ⚙️ Configuration

The tool supports extensive configuration through YAML files and command-line overrides.

### Default Configuration

```yaml
task_timeout: 3600        # Task processing timeout (seconds)
time_limit: 14400         # Total time limit (seconds)
llm:
  model_name: "gemini/gemini-2.0-flash"
  max_completion_tokens: 500
  temperature: 0.5
  caching:
    enabled: true
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --group dev

# Run code quality checks
make quality

# Run linter
make lint

# Auto-fix linting issues
make lint-fix
```

### Run the API server

```bash
uv run python -m aipg.api
```

The FastAPI server runs at `http://localhost:8000` and exposes:

- `POST /projects` — body: `{ comments: string[] }` → returns `Project[]`
- `POST /feedback` — body: `{ project, user_solution }` → returns `{ feedback }`
- `GET /health`

### Frontend (React + Vite + Tailwind)

A React frontend is available in `frontend/` to interact with the API.

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` with CORS enabled on the API. To point to a different API URL:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

### Project Structure

```
aipg/
├── assistant.py          # Main assistant logic
├── llm.py               # LLM client wrapper
├── task.py              # Task and data models
├── prompting/           # Prompt generation
├── task_inference/      # AI inference pipeline
├── configs/             # Configuration management
├── sandbox/             # Safe Python sandbox (ports, service, docker adapter)
└── cache/               # Response caching
```

### Sandbox Quickstart

Run untrusted Python code inside Docker via the service:

```python
from aipg.sandbox.adapters import DockerPythonRunner
from aipg.sandbox.service import PythonSandboxService

service = PythonSandboxService(runner=DockerPythonRunner())
result = service.run_code("print('hello')")
print(result.stdout)
```

#### Preinstalled Libraries

The sandbox includes a custom Docker image with preinstalled Python libraries:

- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **torch** - Machine learning framework
- **scikit-learn** - Machine learning library
- **matplotlib** - Plotting library
- **requests** - HTTP library
- **beautifulsoup4** - HTML/XML parsing
- **lxml** - XML processing

To use the custom image with preinstalled libraries:

```python
from aipg.sandbox.builder import build_sandbox_service
from aipg.configs.app_config import AppConfig

# Load configuration (includes sandbox settings)
config = AppConfig()
service = build_sandbox_service(config)

# Now you can use preinstalled libraries
result = service.run_code("""
import pandas as pd
import numpy as np
import torch

df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print('DataFrame shape:', df.shape)

arr = np.array([1, 2, 3, 4, 5])
print('Array sum:', arr.sum())

tensor = torch.tensor([1.0, 2.0, 3.0])
print('Tensor mean:', tensor.mean().item())
""")
print(result.stdout)
```

#### Building Docker Images

The project includes several Docker images that can be built using make targets:

```bash
# Build all Docker images
make docker-build

# Build individual images
make docker-build-sandbox    # Custom Python sandbox with preinstalled libraries
make docker-build-api        # API server image
make docker-build-frontend   # Frontend React application image
```

Or build manually:

```bash
# Sandbox image with preinstalled libraries
docker build -f docker/Dockerfile.sandbox -t aipg-sandbox:latest .

# API server image
docker build -f docker/Dockerfile.api -t aipg-api:latest .

# Frontend image
docker build -f docker/Dockerfile.frontend -t aipg-frontend:latest .
```

#### Configuration

Sandbox settings can be configured in `aipg/configs/default.yaml`:

```yaml
sandbox:
  docker_image: "aipg-sandbox:latest"  # Custom image with preinstalled libraries
  memory_limit: "128m"
  cpu_quota: 0.5
  pids_limit: 128
  default_timeout_seconds: 5
```

Notes:
- Requires Docker to be installed and the current user able to run `docker`.
- The adapter runs with `--network none`, `--read-only`, memory/CPU limits, and non-root user.
- The custom image is based on `python:3.12-slim` for compatibility with all preinstalled libraries.

## 🐳 Docker Deployment

The project includes a complete Docker setup for production deployment:

### Using Docker Compose

```bash
# Build all images and start services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# Stop services
docker-compose down
```

This will start:
- **API server** on port 8000
- **Frontend** on port 80 (nginx)
- **Sandbox service** (internal)

### Individual Container Usage

```bash
# Run API server
docker run -p 8000:8000 aipg-api:latest

# Run frontend
docker run -p 80:80 aipg-frontend:latest

# Run sandbox (for testing)
docker run --rm aipg-sandbox:latest python -c "import pandas; print('pandas available')"
```

## 🎓 About

This project was created as part of the **AI Product Hack track Yandex#6**. It demonstrates practical application of AI in educational technology, specifically for creating personalized learning experiences.
