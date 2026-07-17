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

## Auth Flow

- `/kayit` creates an account and opens the protected dashboard.
- `/giris` signs in with an existing account.
- `/` is protected and redirects unauthenticated users to `/giris`.
- Sign out calls the backend logout endpoint and returns to `/giris`.

## Environment

`NEXT_PUBLIC_API_BASE_URL` should point to the backend API root, for example:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Sprint 1 Smoke Test

1. Run the backend API on `http://127.0.0.1:8000`.
2. Run the frontend with `npm run dev`.
3. Visit `/kayit` and create a user.
4. Confirm the dashboard loads and the backend status pill is visible.
5. Sign out and confirm `/` redirects to `/giris`.

## Implemented App Routes

- `/` dashboard
- `/ai-chat` AI chat, semantic search, voice command interpretation
- `/gorusmeler` conversations and calls
- `/gorevler` tasks
- `/takvim` appointments and calendar accounts
- `/oncelik` priority queue
- `/kisiler` contacts, `/kisiler/[id]` contact detail (Customer Memory)
- `/firsatlar` deals pipeline (kanban)
- `/dosyalar` files and document analysis actions
- `/mailler` email accounts, messages, sync
- `/bildirimler` notifications
- `/onay-merkezi` AI action approvals
- `/analitik` analytics overview
- `/ayarlar` account, subscription, usage

## Session Persistence

The refresh token is persisted to `localStorage` (`neurodesk-refresh-token`); the access token stays in memory only. On load, `SessionProvider` uses the stored refresh token to silently restore the session (calling `/auth/refresh` then `/users/me`) before `AuthGuard` decides whether to redirect to `/giris`, so a browser refresh no longer logs the user out. Access tokens are proactively refreshed ~60s before their 15-minute expiry (decoded from the JWT `exp` claim) and the rotated refresh token is re-persisted each time.
