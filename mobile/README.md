# NeuroDesk AI Mobile

Sprint 14 mobile MVP app. The app consumes the same backend API as the web app and keeps auth tokens in platform secure storage.

## Project root

Use this `mobile/` directory as the Flutter project root. The native platform folders (`android/`, `ios/`, `web/`, `windows/`, `macos/`, `linux/`) are aligned with the real MVP code in `lib/`.

`mobile/neurodeskai_mobile/` is the older generated Flutter template and is not the active app.

## Run

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

For Android emulator against a host backend, use:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

## Scope

- Login with `/api/v1/auth/login`
- Register with `/api/v1/auth/register`
- Refresh token retry with `/api/v1/auth/refresh`
- Secure token storage via `flutter_secure_storage`
- Remember-me login toggle
- Biometric unlock for saved sessions on supported devices
- Global API health banner and transient read retry
- Deep link route aliases for module/detail URLs
- Protected dashboard shell
- Dashboard summary
- Task list with complete action
- Appointment list
- Calls module with manual call transcript capture and AI analysis trigger
- AI approval list with approve/reject actions and approval materialization through `tasks/from-approval`, `appointments/from-approval`, or `deals/from-approval`
- Manual conversation transcript capture
- AI analysis request from conversations
- Notifications center with read action
- Notification source navigation to deep-linked module routes
- AI Chat sessions and messages
- Contacts/CRM list, detail, memory and notes
- Semantic search
- Deals pipeline
- Priority queue
- Analytics overview
- Files list/analyze/delete and native file picker upload
- Email accounts/messages/sync surface with native browser connect launch
- Settings profile/API/account screen

## Local smoke checklist

```bash
flutter analyze
flutter test
flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Backend must answer `GET http://localhost:8000/health`, and Android emulator builds must use `http://10.0.2.2:8000`.

Current MVP excludes offline outbox/cache, push notifications/FCM, production App/Universal Link association files, full OAuth app callback routing, crash reporting, product analytics events, store signing, tablet/foldable polish, production release automation, and large-file offline upload queueing.
