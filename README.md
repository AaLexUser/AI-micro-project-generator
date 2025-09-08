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

### API Server

Run the FastAPI server locally:

```bash
make serve
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

Generate via API:

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{
        "issue": "I keep mixing up Python list comprehensions with map/filter",
        "presets": null,
        "config_path": null,
        "config_overrides": ["llm.max_completion_tokens=256"]
      }'
```

### Frontend (Next.js)

Run the modern Next.js frontend:

```bash
# In one terminal: backend
make serve

# In another terminal: frontend
cd frontend
# choose one package manager
pnpm install   # or npm install, or yarn
pnpm dev       # or npm run dev, or yarn dev
```

Set the backend URL for the frontend (optional, defaults to http://127.0.0.1:8000):

```bash
cd frontend
echo "BACKEND_URL=http://127.0.0.1:8000" > .env.local
```

Open the app at `http://127.0.0.1:3000`.

Flow:
- Add code and review comments in the Chat page
- Select an issue from recent assistant messages
- Click Generate Project to call the backend `/generate`
- View projects at `Projects`, open a project to read Description and Goal, paste your solution, then reveal the Expert Solution

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
