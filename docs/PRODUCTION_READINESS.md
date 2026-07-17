# NeuroDesk AI Production Readiness

This file is the release gate for the current monorepo. A build is considered product-ready only when the automated checks pass and the external-service checklist is completed for the target environment.

## Automated Gate

Run from the repository root:

```powershell
.\scripts\check-all.ps1 -ReleaseMobile
```

For faster local loops:

```powershell
.\scripts\check-all.ps1
.\scripts\check-all.ps1 -SkipMobile
.\scripts\check-all.ps1 -SkipBackend
```

The backend gate forces `LLM_PROVIDER=mock` so regression tests are deterministic and do not spend real provider quota. Test the real provider separately with a staging key and explicit smoke cases.

## Current Release Status

| Area | Status | Notes |
| --- | --- | --- |
| Backend API | Ready for staging | 161 backend tests pass with mock provider. Real provider requires quota/key verification. |
| Web frontend | Ready for staging | Typecheck and production build pass. Brand assets are wired through `frontend/public/brand/`. |
| Mobile Flutter app | Ready for staging | Analyze, widget/model tests, debug APK and release APK build pass locally. |
| Android/iOS app icons | Ready | Platform icons were regenerated from the NeuroDesk AI brand mark. |
| Email OAuth return | Ready for staging | Mobile callback route exists; real Google/Microsoft credentials must be configured per environment. |
| App/Universal Links | Code ready | Association files must be published and verified on the production domain. |
| Billing | Product skeleton | Plan/quota logic exists; real payment provider/webhook is not enabled. |
| Push notifications | Not enabled | FCM/APNs credentials and device-token flows are still a production integration task. |
| Crash/product analytics | Not enabled | Sentry/Firebase/Product analytics keys must be selected and configured. |

## Environment Gate

Backend required values:

- `ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `TOKEN_ENCRYPTION_KEY`
- `CORS_ORIGINS`
- `MINIO_ENDPOINT_URL`
- `MINIO_PUBLIC_ENDPOINT_URL`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET_NAME`
- `LLM_PROVIDER`
- `LLM_API_KEY` when `LLM_PROVIDER=openai`

Frontend required values:

- `NEXT_PUBLIC_API_BASE_URL`

Mobile build-time value:

- `API_BASE_URL` via `--dart-define`

Android release signing:

- `ANDROID_KEYSTORE_PATH`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

## External-Service Gate

Complete these before production:

1. Configure managed PostgreSQL with pgvector enabled and run Alembic migrations.
2. Configure managed Redis.
3. Configure private object storage and validate presigned upload/download from web and Android emulator/device.
4. Configure real LLM provider key and run a quota-safe smoke test for AI analysis, AI chat, search embeddings and voice.
5. Configure Google/Microsoft OAuth app IDs, callback URLs and allowed domains.
6. Publish `mobile/release/app-links/assetlinks.json` and `mobile/release/app-links/apple-app-site-association` on the production domain.
7. Verify Android SHA-256 certificate fingerprint and Apple Team/App ID in association files.
8. Configure Android release signing and archive the keystore outside git.
9. Configure iOS signing, bundle ID, Associated Domains and TestFlight/App Store metadata.
10. Choose and configure crash reporting and product analytics.
11. Decide whether billing remains manual or connect a payment provider before public launch.

## Final Smoke

Run these against staging before production approval:

1. Register and log in on web.
2. Register and log in on mobile.
3. Create a contact, task, appointment, deal and conversation.
4. Import a TXT call transcript and trigger AI analysis.
5. Approve one AI action and verify the materialized task/appointment/deal.
6. Upload a TXT/PDF/DOCX file and request analysis.
7. Connect Gmail/Outlook in staging OAuth mode and sync messages.
8. Run semantic search from web and mobile.
9. Verify app links open the correct mobile screen.
10. Confirm backend health, frontend build, mobile build and logs are clean.
