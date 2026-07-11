# NeuroDeskAI

NeuroDeskAI is an AI-powered workspace project for healthcare-oriented desk operations, including backend APIs, product and technical documentation, and a future web frontend.

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
│   └── README.md
├── .gitignore
└── README.md
```

## Documentation

The product, architecture, database, backend, AI, frontend, mobile, DevOps, security, QA, deployment, integration, and roadmap documentation lives in `docs/`.

Some backend-local documentation files differed from the top-level documentation copy during the monorepo consolidation. Those preserved variants use a `_backend` suffix.

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

## Frontend

The frontend application is not prepared yet. The `frontend/` directory is reserved for a future Next.js application.
