# Health Research Assistant

Self-hosted web application for health researchers to produce:

1. **project.docx** — structured health data science project documentation via guided LLM conversation. This document also serves as the **specification for the analysis application** your team will build so end users can run the study's analyses.
2. **data_clean.py** — validated data cleaning script generated from schema metadata and researcher discussion

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy, LiteLLM
- **Frontend:** React + TypeScript (Vite)
- **Deployment:** Docker Compose

## Quick Start

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hra.local | admin12345 |
| Researcher | researcher@hra.local | research12345 |

## Features

### Project Document Wizard
Linear wizard: Basics → Guided Intake → Section Review → Quality Gate → Export

### Data Cleaning Wizard
Linear wizard: Select Dataset → Link Project → Schema Explore → Discussion → Script Draft → Validation → Export

### Admin
- Metadata catalog (datasets, tables, columns)
- App settings (`max_active_datasets`, institution name, LLM model)
- Audit log

## LLM Configuration

Default: Gemini via LiteLLM. Set in `.env`:

```
GEMINI_API_KEY=your-key
LLM_MODEL=gemini/gemini-2.0-flash
```

For local models (Ollama):

```
LOCAL_MODEL_ENABLED=true
OLLAMA_API_BASE=http://host.docker.internal:11434
LLM_MODEL_LOCAL=ollama/llama3
```

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Troubleshooting LLM / import

Check Gemini connectivity:

```bash
curl http://localhost:8000/api/llm/status
```

Run import debug script:

```bash
cd backend
set -a && source ../.env && set +a
PYTHONPATH=. python scripts/debug_import.py
```

**Free tier limit:** `gemini-flash-latest` allows ~20 requests/day. If import fails with rate limit, wait ~60 seconds or use **Skip — fill sections manually**.


- Change `SECRET_KEY` in production
- Use HTTPS (see `docs/DEPLOYMENT.md`)
- No row-level PHI in the app — only schema metadata
- Generated scripts require human review before production execution

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guidance.
