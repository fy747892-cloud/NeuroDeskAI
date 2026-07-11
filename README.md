# NeuroDeskAI

NeuroDeskAI is an AI-powered workspace project for healthcare-oriented desk operations. This repository is organized as a monorepo with backend services, product and architecture documentation, and a reserved frontend workspace.

## Folder Structure

```text
NeuroDeskAI/
├── docs/
│   ├── CILT_1_PRD_NeuroDesk_AI.md
│   ├── CILT_2_SOFTWARE_ARCHITECTURE_NeuroDesk_AI.md
│   └── ...
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── bruno/
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── app/
│   ├── lib/
│   ├── package.json
│   └── README.md
├── .gitignore
└── README.md
```

## Documentation

The project documentation lives in `docs/`.

## Backend Setup

```powershell
cd backend
uv sync
Copy-Item .env.example .env
```

Update `backend/.env` with local values before running the API. The real `.env` file is intentionally ignored by Git.

## Run Backend

```powershell
cd backend
uv run uvicorn app.main:app --reload
```

The API runs on `http://127.0.0.1:8000` by default.

## Docker

```powershell
cd backend
docker compose up --build
```

The Docker Compose stack includes the API, PostgreSQL with pgvector, Redis, and MinIO.

## LLM Integration

The backend uses deterministic mock AI by default. Set `LLM_PROVIDER=openai` and configure `LLM_API_KEY` to enable the OpenAI-compatible provider.

## Frontend

The frontend is a Next.js App Router application in `frontend/`.

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```
