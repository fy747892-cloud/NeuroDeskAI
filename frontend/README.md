# NeuroDeskAI Frontend

Next.js App Router frontend for the NeuroDeskAI monorepo.

## Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

The app runs on `http://localhost:3000` by default.

## Environment

`NEXT_PUBLIC_API_BASE_URL` should point to the backend API root, for example:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
