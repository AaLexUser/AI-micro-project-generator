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
└── cache/               # Response caching
```

## 🎓 About

This project was created as part of the **AI Product Hack track Yandex#6**. It demonstrates practical application of AI in educational technology, specifically for creating personalized learning experiences.
