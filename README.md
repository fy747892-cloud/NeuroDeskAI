# NeuroDeskAI

NeuroDeskAI is an AI-powered workspace for calls, conversations, email, files, tasks, appointments, CRM contacts, deals, semantic search and human-approved AI actions. This repository is a working monorepo with FastAPI backend, Next.js web app, Flutter mobile app and product/architecture documentation.

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
├── frontend/                  # Next.js web app
├── mobile/                    # Flutter app
├── scripts/
│   └── check-all.ps1          # Local release gate
├── .gitignore
└── README.md
```

## Release Gate

Run the local quality gate from the repository root:

```powershell
.\scripts\check-all.ps1
```

For the fuller mobile packaging check:

```powershell
.\scripts\check-all.ps1 -ReleaseMobile
```

Production readiness and external-service gates are tracked in `docs/PRODUCTION_READINESS.md`.

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

Open `http://localhost:3000`.

Auth routes:

- `http://localhost:3000/kayit`
- `http://localhost:3000/giris`
- `http://localhost:3000/` redirects unauthenticated users to login.

Sprint 1 smoke test:

1. Start backend dependencies and API.
2. Start the frontend dev server.
3. Register a user from `/kayit`.
4. Confirm the dashboard opens after auth.
5. Sign out and confirm `/` redirects to `/giris`.

MinIO note: `http://localhost:9000` is the S3 API endpoint. Use `http://localhost:9001` for the MinIO console.

## Mobile

The mobile app is a Flutter application in `mobile/`.

```powershell
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Use `http://10.0.2.2:8000` when Android Emulator talks to a backend running on the host machine.
