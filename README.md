# Cherry AI Micro‑Project Generator

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

Generate focused, bite‑sized learning projects from real error descriptions or topics. Perfect for turning mistakes into hands‑on micro‑projects with clear goals, success criteria, and reference solutions.

## ✨ Features

- **From issue → micro‑project**: Turn comments or struggles into structured tasks
- **Validation & auto‑fixing**: Validates projects and attempts automated bug fixes
- **Safe sandboxing**: Runs user code inside a Docker‑isolated Python sandbox
- **API + CLI + Frontend**: FastAPI backend, Typer CLI, React (Vite + Tailwind) UI
- **RAG powered**: Retrieves prior good projects and reuses them when relevant

---

## 🚀 Quickstart

### 1) 60‑second CLI

Prerequisites: Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
# Clone & install
git clone <your-repo-url>
cd ai-micro-project-generator
uv sync

# Configure LLM (OpenAI‑compatible via LiteLLM)
cp aipg/configs/default.yaml.example aipg/configs/default.yaml
export AIPG_LLM_API_KEY="<your_api_key>"
# Optionally customize model/base url
# export AIPG_LLM_MODEL="openai/gpt-4o"
# export AIPG_LLM_BASE_URL="https://api.openai.com/v1"  # or your compatible gateway

# Generate micro‑projects from comments/topics
uv run aipg "I keep mixing up list comprehensions with map/filter"
```

Pass multiple comments by adding more quoted arguments. You can override any config key inline:

```bash
uv run aipg -o llm.model_name=openai/gpt-4o -o rag.k_candidates=8 "Database connection times out"
```

### 2) API + Frontend (Docker Compose)

```bash
docker compose up -d --build
```

- Frontend: http://localhost
- API health: http://localhost/api/health

To stop: `docker compose down`.

### 3) Run locally (no Docker)

Backend API (FastAPI):

```bash
uv run api
# or: uv run python -m aipg.api
# API: http://localhost:8000
```

Frontend (Vite + React + Tailwind):

```bash
cd frontend
npm ci
npm run dev
# App: http://localhost:5173
# Point to a different API if needed:
VITE_API_BASE=http://localhost:8000 npm run dev
```

---

## 🧩 API Overview

Base URL when running locally without nginx: `http://localhost:8000`

- `GET /health` → `{ "status": "ok" }`
- `POST /projects` → Generate projects
  - Body: `{ "comments": string[], "overrides?": string[] }`
  - Returns: `Project[]`
- `POST /feedback` → Get feedback on a user solution
  - Body: `{ "project": Project, "user_solution": string, "overrides?": string[] }`
  - Returns: `{ "feedback": string, "execution_result?": { stdout, stderr, exit_code, timed_out } }`

Example request:

```bash
curl -X POST http://localhost:8000/projects \
  -H 'Content-Type: application/json' \
  -d '{"comments":["Struggling with async/await in Python"],"overrides":["llm.model_name=openai/gpt-4o"]}'
```

When using Docker Compose, the frontend proxies the API under `/api` (see `docker/nginx.conf`).

---

## ⚙️ Configuration

The app reads settings from `aipg/configs/default.yaml` (copy the example first):

```bash
cp aipg/configs/default.yaml.example aipg/configs/default.yaml
```

Key sections (env‑override friendly via OmegaConf):

- `llm.*`
  - `AIPG_LLM_MODEL` (default `openai/gpt-4o`)
  - `AIPG_LLM_BASE_URL` (OpenAI‑compatible endpoint if not default)
  - `AIPG_LLM_API_KEY` (required)
- `langfuse.*` (optional analytics)
  - `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- `rag.*`
  - `AIPG_RAG_SIMILARITY_THRESHOLD`, `AIPG_RAG_K_CANDIDATES`, `AIPG_RAG_COLLECTION_NAME`
  - Embeddings: `AIPG_RAG_EMBEDDING_MODEL`, `AIPG_RAG_EMBEDDING_BASE_URL`, `AIPG_RAG_EMBEDDING_API_KEY`
- `sandbox.*`
  - Uses Docker image `aipg-sandbox:latest` by default
  - Limits and timeouts configurable via env (see example file)

You can also override any key at runtime with `-o key=value` via the CLI or by passing `overrides` in API requests.

---

## 🛠️ Development

Install dev tools and run quality checks:

```bash
uv sync --group dev
make quality      # format + autofix
make lint         # check
make lint-fix     # autofix only
```

Pre‑commit hooks:

```bash
make pre-commit
```

Run tests:

```bash
uv run pytest -v
# or see: tests/README.md
```

---

## 🧪 Sandbox (optional but recommended)

The project ships a dedicated Python sandbox image with useful libraries preinstalled
(`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `requests`, `beautifulsoup4`, `lxml`, `torch` CPU).

Build it once if you are not using Docker Compose:

```bash
make docker-build-sandbox
# or
docker build -f docker/Dockerfile.sandbox -t aipg-sandbox:latest .
```

The backend will use the image specified in `sandbox.docker_image`.

---

## 🧭 Project Structure

```
aipg/
├── api.py                 # FastAPI app + routes
├── assistant.py           # Assistants orchestration (projects, feedback)
├── configs/               # AppConfig, loader, defaults (YAML)
├── domain.py              # Pydantic models and agent states
├── llm.py                 # LiteLLM client wrapper
├── prompting/             # Prompt templates and utils
├── rag/                   # RAG service + adapters
├── sandbox/               # Docker‑based Python sandbox
└── task_inference/        # Inference pipeline steps
```

Frontend lives in `frontend/` (Vite + React + Tailwind). Dockerfiles are in `docker/`.

---

## 🐳 Docker Cheat‑Sheet

```bash
# Build all images
make docker-build

# Build individually
make docker-build-api
make docker-build-frontend
make docker-build-sandbox

# Compose up/down
docker compose up -d --build
docker compose down
```

---

## ❓ Troubleshooting

- Missing LLM key → set `AIPG_LLM_API_KEY` (and `AIPG_LLM_BASE_URL` if not default)
- CORS from frontend dev → use `VITE_API_BASE=http://localhost:8000`
- Docker permissions → ensure your user can run `docker` without sudo
- Sandbox image not found → build it or update `sandbox.docker_image`

---

## 📜 License

Add your license here.

---

## 🙌 Acknowledgments

Created for the AI Product Hack (Yandex #6). Showcases practical AI for personalized learning.
