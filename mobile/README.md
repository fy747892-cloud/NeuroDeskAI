# NeuroDesk AI Mobile

Sprint 14 mobile MVP scaffold. The app consumes the same backend API as the web app and keeps auth tokens in platform secure storage.

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
- Secure token storage via `flutter_secure_storage`
- Protected dashboard shell
- Dashboard summary
- Task list with complete action
- Appointment list
